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

    - Pergunta digitada: busca pelo texto da pergunta (é isso que testa o RAG).
    - Sempre: busca por contexto do navio, para trazer as regras de velocidade.
    Os resultados são unidos, sem repetir trechos.
    """
    pergunta = state.get("pergunta") or PERGUNTA_PADRAO

    consultas = []
    if pergunta != PERGUNTA_PADRAO:
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
        # Sem RAG o fluxo continua; os prompts tratam a lista vazia.
        print(f"\nConhecimento: busca indisponível ({e}). Seguindo sem base.\n")
        return {"conhecimento": []}

    print()
    return {"conhecimento": list(trechos_por_id.values())}