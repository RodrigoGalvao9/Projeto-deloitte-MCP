from pydantic import BaseModel
from src.graph.state import State
import json
from src.graph.prompt.revisor_prompt import REVISOR_PROMPT
from src.utils.llm_adapter import get_llm
from src.utils.conhecimento import formatar_conhecimento


class Revisao(BaseModel):
    aprovado: bool
    motivo: str


def revisor(state: State) -> State:

    navio = state["navio"]
    proposta = state["proposta"]

    proposta_para_revisao = {
        "acao": proposta["acao"],
        "velocidade_kn": proposta["velocidade_kn"]
    }

    navio_json = json.dumps(navio, ensure_ascii=False)
    proposta_json = json.dumps(proposta_para_revisao, ensure_ascii=False)
    conhecimento = formatar_conhecimento(state.get("conhecimento", []))

    mensagens = REVISOR_PROMPT.format_messages(
        navio=navio_json,
        proposta=proposta_json,
        conhecimento=conhecimento,
    )

    llm = get_llm().with_structured_output(Revisao)
    revisao = llm.invoke(mensagens)

    return {"revisao": revisao.model_dump()}