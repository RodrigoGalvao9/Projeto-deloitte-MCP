"""Embeddings: denso (modelo neural do fastembed) e esparso (BM25)."""

import unicodedata
from functools import lru_cache

from fastembed import SparseTextEmbedding, TextEmbedding

from .config import (
    EMBEDDING_MODEL,
    FASTEMBED_CACHE_DIR,
    SPARSE_LANGUAGE,
    SPARSE_MODEL,
)


@lru_cache(maxsize=1)
def _modelo() -> TextEmbedding:
    # Na primeira vez baixa o modelo (algumas centenas de MB) e guarda em cache local.
    return TextEmbedding(model_name=EMBEDDING_MODEL, cache_dir=FASTEMBED_CACHE_DIR)


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
            f"AVISO: BM25 sem suporte a language='{SPARSE_LANGUAGE}' nesta versão "
            f"do fastembed ({e}). Usando o idioma padrão."
        )
        return SparseTextEmbedding(model_name=SPARSE_MODEL, cache_dir=FASTEMBED_CACHE_DIR)


def _sem_acentos(texto: str) -> str:
    """BM25 compara palavras exatas, então 'tábua' e 'tabua' precisam virar o mesmo termo.
    Aplicado igualmente aos documentos e às perguntas."""
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def embed(textos: list[str]) -> list[list[float]]:
    """Vetores densos (384 dimensões) para uma lista de textos."""
    return [vetor.tolist() for vetor in _modelo().embed(textos)]


def embed_esparso(textos: list[str]) -> list[tuple[list[int], list[float]]]:
    """Vetores esparsos (BM25) de documentos: lista de (índices, valores)."""
    sem_acento = [_sem_acentos(t) for t in textos]
    return [(e.indices.tolist(), e.values.tolist()) for e in _modelo_esparso().embed(sem_acento)]


def embed_esparso_query(query: str) -> tuple[list[int], list[float]]:
    """Vetor esparso (BM25) de uma pergunta: (índices, valores)."""
    e = next(iter(_modelo_esparso().query_embed(_sem_acentos(query))))
    return e.indices.tolist(), e.values.tolist()