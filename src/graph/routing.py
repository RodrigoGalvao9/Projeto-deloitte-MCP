from src.graph.state import State


def route_after_navegador(state: State) -> str:
    """Ações que alteram (ou mantêm) o navio passam pelo revisor.
    Perguntas informativas ou fora do escopo são respondidas direto."""
    if state["proposta"]["acao"] in ("RESPONDER", "RECUSAR"):
        return "responder"

    return "revisor"


def router_after_review(state: State) -> str:
    revisao = state["revisao"]

    if revisao["aprovado"]:
        return "aprovado"

    if state["rodada"] < 2:
        return "tentar_de_novo"

    return "esgotado"


def route_after_validate(state: State) -> str:
    if state["resultado"] == "validado":
        return "executar"

    return "finalizar"


def route_after_execute(state: State) -> str:
    erro = state.get("erro", {})

    if erro.get("code") == "STATE_VERSION_CONFLICT":
        if state.get("tentativas", 0) < 2:
            return "reler_estado"

        return "falha"

    if erro:
        return "falha"

    return "confirmar"