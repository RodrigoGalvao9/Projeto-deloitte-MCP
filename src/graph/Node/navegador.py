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


MOTIVO_BASE_INDISPONIVEL = (
    "Não consegui consultar a base de conhecimento agora, então não vou propor "
    "nenhuma ação. Nenhuma alteração foi feita no navio. Tente novamente em instantes."
)


def navegador(state: State) -> State:
    """Função que representa o nó do navegador no grafo de estados"""

    # Busca falhou (RAG/MCP fora do ar): sem as regras da base não há decisão a tomar.
    # Encerra via RESPONDER, sem chamar o LLM e sem passar por revisor/escalar.
    # Diferente de "a base não contém", em que a busca funcionou e o LLM decide.
    erro_rag = state.get("erro_rag")
    if erro_rag:
        print(f"\nNavegador: base indisponível ({erro_rag}). Encerrando sem chamar o LLM.\n")
        proposta = Proposta(acao="RESPONDER", motivo=MOTIVO_BASE_INDISPONIVEL)
        return {"rodada": state["rodada"] + 1, "proposta": proposta.model_dump()}

    feedback = ""
    aprovado = state["revisao"].get("aprovado")
    if aprovado is False:
        print("\nNavegador: Revisão não aprovada, gerando nova proposta...\n")
        feedback = state["revisao"]["motivo"]
    navio = state["navio"]
    navio_json = json.dumps(navio, ensure_ascii=False)

    pergunta = state.get("pergunta") or PERGUNTA_PADRAO

    # Lista vazia aqui significa que a busca funcionou e não achou nada
    # (falha de busca é tratada acima, via erro_rag); o prompt trata esse caso.
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