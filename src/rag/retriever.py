"""Busca: embedding da pergunta + similaridade no Qdrant.

Teste rápido (a partir da raiz do projeto):
    python -m src.rag.retriever "o que fazer com ondas de 4 metros?"
"""

import sys
from functools import lru_cache

from qdrant_client import QdrantClient

from .config import COLLECTION, QDRANT_API_KEY, QDRANT_URL
from .embeddings import embed


@lru_cache(maxsize=1)
def _client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)


def buscar(query: str, k: int = 4) -> list[dict]:
    """Retorna os k trechos mais parecidos com a pergunta, do mais ao menos relevante."""
    vetor = embed([query])[0]
    resposta = _client().query_points(
        collection_name=COLLECTION,
        query=vetor,
        limit=k,
        with_payload=True,
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


if __name__ == "__main__":
    pergunta = " ".join(sys.argv[1:]) or "o que fazer com ondas de 4 metros?"
    print(f"Pergunta: {pergunta}\n")
    # k=10: mostra o ranking completo da base, útil para diagnosticar a busca
    for posicao, r in enumerate(buscar(pergunta, k=10), start=1):
        print(f"{posicao:>2}. [{r['score']}] {r['id']} - {r['titulo']}")