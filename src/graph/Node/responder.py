from src.graph.state import State


def responder(state: State) -> State:
    """Encerra o fluxo quando a pergunta é informativa (RESPONDER) ou está fora do escopo (RECUSAR).
    Nenhuma alteração é feita no navio."""
    proposta = state["proposta"]
    rotulo = "Recusado" if proposta["acao"] == "RECUSAR" else "Resposta"
    return {"resultado": f"{rotulo}: {proposta['motivo']}"}