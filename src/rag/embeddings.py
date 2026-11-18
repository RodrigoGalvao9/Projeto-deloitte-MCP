"""Geração de embeddings com fastembed (local, sem chave de API)."""

from functools import lru_cache

from fastembed import TextEmbedding

from .config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def _modelo() -> TextEmbedding:
    # Na primeira vez baixa o modelo (algumas centenas de MB) e guarda em cache local.
    return TextEmbedding(model_name=EMBEDDING_MODEL)


def embed(textos: list[str]) -> list[list[float]]:
    """Converte uma lista de textos em uma lista de vetores."""
    return [vetor.tolist() for vetor in _modelo().embed(textos)]