"""Ingestão: lê a base_conhecimento do JSON, gera embeddings e grava no Qdrant.

Execução (a partir da raiz do projeto):
    python -m src.rag.ingest
"""

import json

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from .config import (
    COLLECTION,
    DADOS_JSON,
    EMBEDDING_DIM,
    QDRANT_API_KEY,
    QDRANT_URL,
)
from .embeddings import embed


def carregar_documentos() -> list[dict]:
    dados = json.loads(DADOS_JSON.read_text(encoding="utf-8"))
    return dados["base_conhecimento"]


def main() -> None:
    docs = carregar_documentos()
    print(f"{len(docs)} documentos lidos de {DADOS_JSON.name}")

    # O texto que vira vetor: título + corpo. O título ajuda a busca a acertar o assunto.
    textos = [f"{d['titulo']}. {d['texto']}" for d in docs]
    vetores = embed(textos)
    assert len(vetores[0]) == EMBEDDING_DIM, (
        f"Dimensão {len(vetores[0])} difere de EMBEDDING_DIM={EMBEDDING_DIM}"
    )

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # Reindexação completa: simples e correta para uma base pequena.
    # Assim, documentos removidos do JSON também somem do banco.
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
    )

    pontos = [
        PointStruct(
            id=i,
            vector=vetor,
            payload={
                "doc_id": d["id"],
                "titulo": d["titulo"],
                "tags": d.get("tags", []),
                "texto": d["texto"],
            },
        )
        for i, (d, vetor) in enumerate(zip(docs, vetores))
    ]
    client.upsert(collection_name=COLLECTION, points=pontos)
    print(f"{len(pontos)} pontos gravados na coleção '{COLLECTION}' ({QDRANT_URL})")


if __name__ == "__main__":
    main()