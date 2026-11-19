"""Embeddings: denso (Cloudflare) e esparso (BM25 local)."""

import unicodedata
from functools import lru_cache

import requests
from fastembed import SparseTextEmbedding

from .config import (
    CLOUDFLARE_API_TOKEN,
    CLOUDFLARE_EMBEDDING_URL,
    EMBEDDING_DIM,
    SPARSE_LANGUAGE,
    SPARSE_MODEL,
    FASTEMBED_CACHE_DIR,
)


@lru_cache(maxsize=1)
def _modelo_esparso() -> SparseTextEmbedding:
    try:
        return SparseTextEmbedding(
            model_name=SPARSE_MODEL,
            cache_dir=FASTEMBED_CACHE_DIR,
            language=SPARSE_LANGUAGE,
        )
    except (TypeError, ValueError) as e:
        print(
            f"AVISO: BM25 sem suporte a language='{SPARSE_LANGUAGE}': {e}. "
            "Usando idioma padrão."
        )
        return SparseTextEmbedding(
            model_name=SPARSE_MODEL,
            cache_dir=FASTEMBED_CACHE_DIR,
        )


def embed(textos: list[str]) -> list[list[float]]:
    """Gera embeddings densos remotamente pela Cloudflare."""

    if not textos:
        return []

    if not CLOUDFLARE_EMBEDDING_URL or not CLOUDFLARE_API_TOKEN:
        raise RuntimeError(
            "CLOUDFLARE_ACCOUNT_ID e CLOUDFLARE_API_TOKEN precisam estar configurados."
        )

    response = requests.post(
        CLOUDFLARE_EMBEDDING_URL,
        headers={
            "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "input": textos,
            "dimensions": EMBEDDING_DIM,
        },
        timeout=60,
    )

    response.raise_for_status()
    resultado = response.json()

    if "result" in resultado:
        resultado = resultado["result"]

    vetores = [
        item["embedding"]
        for item in resultado["data"]
    ]

    if len(vetores) != len(textos):
        raise RuntimeError(
            f"Cloudflare retornou {len(vetores)} vetores "
            f"para {len(textos)} textos."
        )

    if any(len(vetor) != EMBEDDING_DIM for vetor in vetores):
        raise RuntimeError(
            f"Dimensão retornada diferente de {EMBEDDING_DIM}."
        )

    return vetores


def _sem_acentos(texto: str) -> str:
    """Normaliza acentos para melhorar a correspondência do BM25."""
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(
        c for c in decomposto
        if unicodedata.category(c) != "Mn"
    )


def embed_esparso(textos: list[str]) -> list[tuple[list[int], list[float]]]:
    """Vetores esparsos (BM25) de documentos."""
    sem_acento = [_sem_acentos(t) for t in textos]

    return [
        (e.indices.tolist(), e.values.tolist())
        for e in _modelo_esparso().embed(sem_acento)
    ]


def embed_esparso_query(query: str) -> tuple[list[int], list[float]]:
    """Vetor esparso (BM25) de uma pergunta."""
    e = next(
        iter(_modelo_esparso().query_embed(_sem_acentos(query)))
    )

    return e.indices.tolist(), e.values.tolist()