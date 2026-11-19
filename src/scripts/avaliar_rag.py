"""Mede a qualidade da busca: para cada pergunta, em que posição aparece o documento esperado.

Execução (a partir da raiz do projeto, com o Qdrant no ar e a base ingerida):
    python -m src.scripts.avaliar_rag               # compara denso, esparso e híbrido
    python -m src.scripts.avaliar_rag --reescrita   # inclui a reescrita de pergunta (usa o LLM)

Dois grupos de perguntas:
- vocabulário da base: reaproveitam palavras dos documentos (favorece a busca por palavras, BM25)
- paráfrases: dizem a mesma coisa com outras palavras (favorece a busca por sentido, densa)

O que importa para o agente é o documento certo estar entre os k trechos entregues ao LLM,
então olhe principalmente hit@3, além de hit@1 e MRR.

Cuidado: se você ajustar o prompt de reescrita olhando estes mesmos casos, o resultado deixa
de ser uma medida honesta. Prefira acrescentar perguntas novas a cada ajuste.
"""

import argparse
import asyncio

from src.rag.retriever import buscar, listar_topicos

GRUPOS = {
    "vocabulário da base": [
        ("Como leio a tábua de marés?", "KB-006"),
        ("como ler a tabua de mares", "KB-006"),
        ("Qual o limite de velocidade em tempestade na rota direta?", "KB-009"),
        ("Até quantos nós posso ir com tempestade na rota protegida?", "KB-009"),
        ("O que fazer quando recebo aviso de tempestade?", "KB-007"),
        ("Quanto devo reduzir a velocidade na primeira proposta?", "KB-010"),
        ("Quando devo entrar no porto com calado alto?", "KB-005"),
        ("O que é folga sob a quilha?", "KB-004"),
        ("Qual a diferença entre rota direta e protegida?", "KB-003"),
        ("Vento de 30 nós ainda é seguro para navegar?", "KB-001"),
        ("O que fazer com ondas de 6 metros?", "KB-002"),
        ("Posso manter velocidade plena com neblina?", "KB-008"),
    ],
    "paráfrases": [
        ("Meu navio está com o fundo quase tocando o leito no porto, o que verifico?", "KB-004"),
        ("Qual o melhor horário para chegar ao terminal com um navio muito pesado?", "KB-005"),
        ("Como sei quando a água estará mais alta ou mais baixa ao longo do dia?", "KB-006"),
        ("Uma ventania muito forte me obriga a mudar o plano de viagem?", "KB-001"),
        ("Em quanto devo diminuir o ritmo da embarcação logo de início num temporal?", "KB-010"),
        ("Enxergar pouco à frente por causa da bruma exige alguma cautela?", "KB-008"),
        ("Compensa ir colado à costa ou pelo alto-mar numa tormenta?", "KB-003"),
        ("Qual o teto de nós para um navio no meio do temporal, indo em linha reta?", "KB-009"),
        ("O mar está enorme, com ondas gigantes; devo procurar um porto abrigado?", "KB-002"),
    ],
}

# Perguntas que o classificador de escopo deve recusar.
FORA_DO_ESCOPO = [
    "Qual a capital da França?",
    "Me conta uma piada.",
    "Como faço um bolo de chocolate?",
    "Quem ganhou a última Copa do Mundo?",
]

MODOS = ["denso", "esparso", "hibrido"]


def posicao(consulta: str, esperado: str, modo: str) -> int | None:
    ids = [r["id"] for r in buscar(consulta, k=10, modo=modo)]
    return ids.index(esperado) + 1 if esperado in ids else None


def avaliar_grupo(nome: str, casos: list[tuple[str, str]], entendimentos: dict | None) -> None:
    colunas = MODOS + (["reescrita"] if entendimentos else [])
    resultados: dict[str, list[int | None]] = {c: [] for c in colunas}
    recusas_indevidas = 0
    reescritas: list[tuple[str, str]] = []

    print(f"\n=== {nome} ===")
    print(f"{'pergunta':<60}" + "".join(f"{c:>10}" for c in colunas) + "   esperado")
    for pergunta, esperado in casos:
        linha = f"{pergunta[:58]:<60}"

        for modo in MODOS:
            pos = posicao(pergunta, esperado, modo)
            resultados[modo].append(pos)
            linha += f"{(str(pos) if pos else '-'):>10}"

        if entendimentos:
            e = entendimentos[pergunta]
            if not e.dentro_do_escopo:
                recusas_indevidas += 1
                pos = None
            else:
                consulta = e.consulta.strip() or pergunta
                reescritas.append((pergunta, consulta))
                # A reescrita é avaliada com a busca híbrida, o padrão do sistema.
                pos = posicao(consulta, esperado, "hibrido")
            resultados["reescrita"].append(pos)
            linha += f"{(str(pos) if pos else '-'):>10}"

        print(linha + f"   {esperado}")

    total = len(casos)
    print(f"\nResumo de '{nome}' ({total} perguntas; '-' = fora do top 10)")
    print(f"{'modo':<11}{'hit@1':>8}{'hit@3':>8}{'MRR':>8}")
    for coluna in colunas:
        pos = resultados[coluna]
        hit1 = sum(1 for p in pos if p == 1) / total
        hit3 = sum(1 for p in pos if p and p <= 3) / total
        mrr = sum(1 / p for p in pos if p) / total
        print(f"{coluna:<11}{hit1:>8.2f}{hit3:>8.2f}{mrr:>8.2f}")

    if entendimentos:
        print(f"Recusas indevidas pelo classificador de escopo: {recusas_indevidas}")
        print("\nComo cada pergunta foi reescrita:")
        for original, consulta in reescritas:
            print(f"  {original[:55]}\n    -> {consulta}")


def avaliar_escopo(entendimentos: dict) -> None:
    print("\n=== classificador de escopo (todas devem ser recusadas) ===")
    recusadas = 0
    for pergunta in FORA_DO_ESCOPO:
        recusou = not entendimentos[pergunta].dentro_do_escopo
        recusadas += recusou
        print(f"  {'recusada' if recusou else 'ACEITA (erro)'}: {pergunta}")
    print(f"Recusadas corretamente: {recusadas} de {len(FORA_DO_ESCOPO)}")


async def _entender_lote(perguntas: list[str]) -> dict:
    # Import tardio: só quem usa --reescrita precisa do LLM e do restante do grafo.
    from src.graph.Node.entender_pergunta import entender, formatar_topicos

    topicos = formatar_topicos(listar_topicos())
    resultados = {}
    for pergunta in perguntas:  # em sequência, para não estourar limite de requisições do provedor
        resultados[pergunta] = await entender(pergunta, topicos)
    return resultados


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--reescrita", action="store_true",
        help="avalia também a reescrita de pergunta e o classificador de escopo (usa o LLM)",
    )
    args = ap.parse_args()

    entendimentos = None
    if args.reescrita:
        from dotenv import load_dotenv

        load_dotenv()
        todas = [p for casos in GRUPOS.values() for p, _ in casos] + FORA_DO_ESCOPO
        entendimentos = asyncio.run(_entender_lote(todas))

    for nome, casos in GRUPOS.items():
        avaliar_grupo(nome, casos, entendimentos)

    if entendimentos:
        avaliar_escopo(entendimentos)


if __name__ == "__main__":
    main()