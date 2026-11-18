from typing import Literal
from pydantic import BaseModel
from src.graph.state import State, PERGUNTA_PADRAO
import json
from src.graph.prompt.navegador_prompt import NAVEGADOR_PROMPT
from src.utils.llm_adapter import get_llm
from src.utils.conhecimento import formatar_conhecimento


class Proposta(BaseModel):
    """Proposta de ação do navegador"""
    acao: Literal["SET_SPEED", "NO_ACTION", "RESPONDER", "RECUSAR"]
    velocidade_kn: float | None = None
    motivo: str


def navegador(state: State) -> State:
    """Função que representa o nó do navegador no grafo de estados"""

    feedback = ""
    aprovado = state["revisao"].get("aprovado")
    if aprovado is False:
        print("\nNavegador: Revisão não aprovada, gerando nova proposta...\n")
        feedback = state["revisao"]["motivo"]
    navio = state["navio"]
    navio_json = json.dumps(navio, ensure_ascii=False)

    pergunta = state.get("pergunta") or PERGUNTA_PADRAO

    # Se o RAG estiver fora do ar, o nó anterior deixa a lista vazia e o prompt trata isso.
    conhecimento = formatar_conhecimento(state.get("conhecimento", []))

    mensagens = NAVEGADOR_PROMPT.format_messages(
        pergunta=pergunta,
        navio=navio_json,
        feedback=feedback,
        conhecimento=conhecimento,
    )
    llm = get_llm().with_structured_output(Proposta)
    proposta = llm.invoke(mensagens)

    print(
        f"\nNavegador: {proposta.acao} | velocidade={proposta.velocidade_kn} | "
        f"{proposta.motivo}\n"
    )

    return {"rodada": state["rodada"] + 1, "proposta": proposta.model_dump()}