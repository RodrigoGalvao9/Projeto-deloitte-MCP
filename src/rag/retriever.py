"""Busca no Qdrant, em três modos:

- denso:   similaridade de sentido (modelo neural)
- esparso: palavras exatas (BM25)
- hibrido: os dois em paralelo, unidos por RRF (padrão)

Teste rápido (a partir da raiz do projeto):
    python -m src.rag.retriever "Como leio a tábua de marés?"
    python -m src.rag.retriever "Como leio a tábua de marés?" --modo denso
"""

import argparse
from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.models import Fusion, FusionQuery, Prefetch, SparseVector

from .config import COLLECTION, QDRANT_API_KEY, QDRANT_URL, VETOR_DENSO, VETOR_ESPARSO
from .embeddings import embed, embed_esparso_query

MODOS = ("denso", "esparso", "hibrido")
PREFETCH = 20  # candidatos que cada busca entrega para a fusão


@lru_cache(maxsize=1)
def _client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)


def buscar(query: str, k: int = 4, modo: str = "hibrido") -> list[dict]:
    """Retorna os k trechos mais relevantes, do mais ao menos relevante.

    Atenção: no modo híbrido o 'score' vem da fusão RRF (baseado em posições),
    então não é comparável com o score de similaridade do modo denso.
    """
    if modo not in MODOS:
        raise ValueError(f"modo inválido: {modo!r} (use um de {MODOS})")

    denso = embed([query])[0] if modo in ("denso", "hibrido") else None
    indices, valores = embed_esparso_query(query) if modo in ("esparso", "hibrido") else ([], [])
    esparso = SparseVector(indices=indices, values=valores)
    client = _client()

    if modo == "esparso":
        if not indices:  # pergunta sem nenhum termo útil para o BM25
            return []
        resposta = client.query_points(
            collection_name=COLLECTION, query=esparso, using=VETOR_ESPARSO,
            limit=k, with_payload=True,
        )
    elif modo == "denso" or not indices:
        # Híbrido sem termos úteis para o BM25 cai para a busca densa.
        resposta = client.query_points(
            collection_name=COLLECTION, query=denso, using=VETOR_DENSO,
            limit=k, with_payload=True,
        )
    else:
        resposta = client.query_points(
            collection_name=COLLECTION,
            prefetch=[
                Prefetch(query=denso, using=VETOR_DENSO, limit=PREFETCH),
                Prefetch(query=esparso, using=VETOR_ESPARSO, limit=PREFETCH),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=k, with_payload=True,
        )

    return [
        {
            "id": p.payload["doc_id"],
            "titulo": p.payload["titulo"],
            "texto": p.payload["texto"],
            "score": round(p.score, 3),
        }
        for p in resposta.points
    ]


def listar_topicos() -> list[dict]:
    """Lista id e título de todos os documentos da base (orienta a reescrita de perguntas).
    Limite de 100 documentos por chamada: suficiente para esta base pequena."""
    pontos, _ = _client().scroll(
        collection_name=COLLECTION, limit=100, with_payload=True, with_vectors=False,
    )
    topicos = [{"id": p.payload["doc_id"], "titulo": p.payload["titulo"]} for p in pontos]
    return sorted(topicos, key=lambda t: t["id"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pergunta", nargs="*")
    ap.add_argument("--modo", choices=MODOS, default="hibrido")
    args = ap.parse_args()

    pergunta = " ".join(args.pergunta) or "o que fazer com ondas de 4 metros?"
    print(f"Pergunta: {pergunta}  (modo: {args.modo})\n")
    # k=10: mostra o ranking completo da base, útil para diagnosticar a busca
    for posicao, r in enumerate(buscar(pergunta, k=10, modo=args.modo), start=1):
        print(f"{posicao:>2}. [{r['score']}] {r['id']} - {r['titulo']}")