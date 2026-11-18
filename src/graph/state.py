from typing import TypedDict

# Pergunta usada quando o operador não digita nada.
PERGUNTA_PADRAO = "Avalie a situação do navio e decida a ação adequada."


class State(TypedDict, total=False):
    ship_id: str
    pergunta: str
    navio: dict
    conhecimento: list[dict]
    proposta: dict
    revisao: dict

    rodada: int
    tentativas: int

    resultado: str
    resultado_execucao: dict

    aprovado_operador: bool
    motivo_excecao: str

    erro: dict
    idempotency_key: str


ESTADO_INICIAL: State = {
    "ship_id": "",
    "pergunta": "",
    "navio": {},
    "conhecimento": [],
    "proposta": {},
    "revisao": {},
    "rodada": 0,
    "tentativas": 0,
    "resultado": "",
    "resultado_execucao": {},
    "aprovado_operador": False,
    "motivo_excecao": "",
    "erro": {},
    "idempotency_key": "",
}