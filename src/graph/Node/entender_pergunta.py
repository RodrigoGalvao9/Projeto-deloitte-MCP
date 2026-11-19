from pydantic import BaseModel

from src.graph.prompt.entender_prompt import ENTENDER_PROMPT
from src.graph.state import State, PERGUNTA_PADRAO
from src.utils.llm_adapter import get_llm
from src.utils.mcp_client import get_tools_by_name, parse_result


class Entendimento(BaseModel):
    """Resultado da análise da pergunta do operador"""
    dentro_do_escopo: bool
    consulta: str = ""
    motivo_recusa: str = ""


def formatar_topicos(topicos: list[dict]) -> str:
    """Lista de títulos da base, usada para a reescrita falar a língua dos documentos."""
    if not topicos:
        return "(indisponível)"
    return "\n".join(f"- {t['titulo']}" for t in topicos)


async def entender(pergunta: str, topicos: str) -> Entendimento:
    """Classifica o escopo e reescreve a pergunta como consulta de busca."""
    mensagens = ENTENDER_PROMPT.format_messages(pergunta=pergunta, topicos=topicos)
    llm = get_llm().with_structured_output(Entendimento)
    return await llm.ainvoke(mensagens)


async def _obter_topicos() -> str:
    try:
        tools = await get_tools_by_name()
        resultado = parse_result(await tools["listar_topicos"].ainvoke({}))

        if not isinstance(resultado, dict) or "error" in resultado:
            raise RuntimeError(resultado)

        return formatar_topicos(resultado["topicos"])

    except Exception as e:
        print(f"\nEntendimento: tópicos indisponíveis ({e}). Reescrevendo sem eles.\n")
        return formatar_topicos([])


async def entender_pergunta(state: State) -> State:
    """Interpreta a pergunta antes de qualquer busca: recusa o que está fora do escopo
    e reescreve o restante com o vocabulário da base."""
    pergunta = state.get("pergunta") or PERGUNTA_PADRAO

    # Avaliação padrão: não há o que interpretar, e não gasta chamada de LLM.
    if pergunta == PERGUNTA_PADRAO:
        return {"consulta": ""}

    try:
        entendimento = await entender(pergunta, await _obter_topicos())
    except Exception as e:
        # Se a análise falhar, o fluxo segue com a pergunta original.
        print(f"\nEntendimento: falhou ({e}). Seguindo com a pergunta original.\n")
        return {"consulta": ""}

    if not entendimento.dentro_do_escopo:
        motivo = (
            entendimento.motivo_recusa
            or "A pergunta está fora do escopo da navegação marítima."
        )
        print(f"\nEntendimento: fora do escopo | {motivo}\n")
        return {
            "consulta": "",
            "proposta": {"acao": "RECUSAR", "velocidade_kn": None, "motivo": motivo},
        }

    consulta = entendimento.consulta.strip()
    print(f"\nEntendimento: dentro do escopo | consulta: {consulta!r}\n")
    return {"consulta": consulta}