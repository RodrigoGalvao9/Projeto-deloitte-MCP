from src.graph.state import State, PERGUNTA_PADRAO
from src.utils.mcp_client import get_tools_by_name, parse_result


def _montar_query_contexto(navio: dict) -> str:
    """Pergunta de busca montada a partir dos dados do navio (sem usar LLM).
    Garante que as regras de velocidade cheguem ao navegador e ao revisor."""
    situacao = "em tempestade" if navio.get("em_tempestade") else "sem tempestade"
    rota = navio.get("rota", "")
    return (
        f"regras de velocidade e ação esperada para navio {situacao} "
        f"na rota {rota}, limites e procedimento"
    )


async def _buscar(ferramenta, query: str, k: int) -> list[dict]:
    resultado = parse_result(await ferramenta.ainvoke({"query": query, "k": k}))

    if not isinstance(resultado, dict) or "error" in resultado:
        raise RuntimeError(resultado)

    return resultado["resultados"]


async def consultar_conhecimento(state: State) -> State:
    """Busca na base de conhecimento (RAG, via MCP) os trechos relevantes.

    - Pergunta digitada: busca pela consulta reescrita (entender_pergunta) ou, se ela
      não existir, pelo texto original da pergunta. É isso que testa o RAG.
    - Sempre: busca por contexto do navio, para trazer as regras de velocidade.
    Os resultados são unidos, sem repetir trechos.

    Dois desfechos distintos para o resto do grafo:
    - busca funcionou (mesmo sem trechos): erro_rag = "" ("a base não contém");
    - busca falhou: conhecimento = [] e erro_rag preenchido ("base indisponível").
    erro_rag é sempre escrito, para limpar um erro de uma passagem anterior (o grafo
    volta a este nó após STATE_VERSION_CONFLICT).
    """
    pergunta = state.get("pergunta") or PERGUNTA_PADRAO
    consulta = (state.get("consulta") or "").strip()

    consultas = []
    if pergunta != PERGUNTA_PADRAO:
        if consulta:
            consultas.append(("pergunta reescrita", consulta, 4))
        else:
            consultas.append(("pergunta", pergunta, 4))
    consultas.append(("contexto do navio", _montar_query_contexto(state["navio"]), 3))

    try:
        tools = await get_tools_by_name()
        ferramenta = tools["buscar_conhecimento"]

        trechos_por_id: dict[str, dict] = {}
        for rotulo, query, k in consultas:
            trechos = await _buscar(ferramenta, query, k)
            print(f"\nConhecimento ({rotulo}): {[(t['id'], t['score']) for t in trechos]}")
            for t in trechos:
                trechos_por_id.setdefault(t["id"], t)

    except Exception as e:
        # Falha na busca (não é o mesmo que "a base não contém"): o navegador encerra
        # o fluxo avisando que a base está indisponível, sem propor nenhuma ação.
        print(f"\nConhecimento: busca indisponível ({e}).\n")
        return {"conhecimento": [], "erro_rag": f"{type(e).__name__}: {e}"[:300]}

    print()
    return {"conhecimento": list(trechos_por_id.values()), "erro_rag": ""}