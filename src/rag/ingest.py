"""Ingestão: lê a base_conhecimento do JSON, gera embeddings (denso + BM25) e grava no Qdrant.

Execução (a partir da raiz do projeto):
    python -m src.rag.ingest
"""

import json

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    Modifier,
    PointStruct,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from .config import (
    COLLECTION,
    DADOS_JSON,
    EMBEDDING_DIM,
    QDRANT_API_KEY,
    QDRANT_URL,
    VETOR_DENSO,
    VETOR_ESPARSO,
)
from .embeddings import embed, embed_esparso


def carregar_documentos() -> list[dict]:
    dados = json.loads(DADOS_JSON.read_text(encoding="utf-8"))
    return dados["base_conhecimento"]


def main() -> None:
    docs = carregar_documentos()
    print(f"{len(docs)} documentos lidos de {DADOS_JSON.name}")

    # O texto que vira vetor: título + corpo. O título ajuda a busca a acertar o assunto.
    textos = [f"{d['titulo']}. {d['texto']}" for d in docs]
    densos = embed(textos)
    esparsos = embed_esparso(textos)
    assert len(densos[0]) == EMBEDDING_DIM, (
        f"Dimensão {len(densos[0])} difere de EMBEDDING_DIM={EMBEDDING_DIM}"
    )

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # Reindexação completa: simples e correta para uma base pequena.
    # Assim, documentos removidos do JSON também somem do banco.
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)

    client.create_collection(
        collection_name=COLLECTION,
        vectors_config={
            VETOR_DENSO: VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        },
        sparse_vectors_config={
            # IDF: palavras raras pesam mais que palavras comuns (metade do cálculo do BM25)
            VETOR_ESPARSO: SparseVectorParams(modifier=Modifier.IDF),
        },
    )

    pontos = [
        PointStruct(
            id=i,
            vector={
                VETOR_DENSO: denso,
                VETOR_ESPARSO: SparseVector(indices=indices, values=valores),
            },
            payload={
                "doc_id": d["id"],
                "titulo": d["titulo"],
                "tags": d.get("tags", []),
                "texto": d["texto"],
            },
        )
        for i, (d, denso, (indices, valores)) in enumerate(zip(docs, densos, esparsos))
    ]
    client.upsert(collection_name=COLLECTION, points=pontos)
    print(f"{len(pontos)} pontos gravados na coleção '{COLLECTION}' ({QDRANT_URL})")


if __name__ == "__main__":
    main()