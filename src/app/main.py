import asyncio
import uuid

from dotenv import load_dotenv
from langgraph.types import Command

from src.graph.state import State, PERGUNTA_PADRAO
from src.graph.builder import graph

NAVIOS = {"1": "S1-FAROL", "2": "S2-MARE", "3": "S3-CORAL"}


def escolher_navio() -> str:
    while True:
        escolha = input(
            "\nEscolha um navio para a simulação:\n"
            "1. S1-FAROL\n"
            "2. S2-MARE\n"
            "3. S3-CORAL\n"
            "Escolha (1-3): "
        ).strip()

        if escolha in NAVIOS:
            return NAVIOS[escolha]

        print("Opção inválida. Tente novamente.")


async def executar_simulacao(ship_id: str, pergunta: str) -> None:
    estado_inicial: State = {
        "ship_id": ship_id,
        "pergunta": pergunta,
        "rodada": 0,
        "tentativas": 0,
    }

    # thread_id novo a cada execução: o checkpointer não reaproveita
    # estado de simulações anteriores.
    config = {
        "configurable": {
            "thread_id": f"frota-{uuid.uuid4().hex[:8]}"
        }
    }

    resposta = await graph.ainvoke(
        estado_inicial,
        config=config
    )

    pausas = resposta.get("__interrupt__", [])

    if pausas:
        print(pausas[0].value)

        retorno = input(
            "\nDeseja continuar? (s/n): "
        ).strip().lower()

        while retorno not in ["s", "n"]:
            retorno = input(
                "\nOpção inválida. Deseja continuar? (s/n): "
            ).strip().lower()

        motivo = ""

        if retorno == "s":
            motivo = input(
                "\nDigite o motivo da exceção: "
            ).strip()

        resposta = await graph.ainvoke(
            Command(
                resume=retorno == "s",
                update={"motivo_excecao": motivo},
            ),
            config=config
        )

    print(f"\n{resposta['resultado']}")


async def main():
    load_dotenv()

    ship_id = escolher_navio()

    while True:
        pergunta = input(
            f"\n[{ship_id}] Digite uma pergunta ou instrução "
            "(Enter = avaliação padrão, 'trocar' = outro navio, 'sair' = encerrar): "
        ).strip()

        if pergunta.lower() == "sair":
            break

        if pergunta.lower() == "trocar":
            ship_id = escolher_navio()
            continue

        await executar_simulacao(ship_id, pergunta or PERGUNTA_PADRAO)


if __name__ == "__main__":
    asyncio.run(main())