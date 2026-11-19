"""Configuração compartilhada pelo RAG (ingestão e busca).

Ingestão e busca PRECISAM usar o mesmo modelo de embeddings,
por isso o nome do modelo e a dimensão ficam centralizados aqui.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# src/rag/config.py -> parents[0]=rag, [1]=src, [2]=raiz do projeto
RAIZ = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ / ".env")

# --- Qdrant ---
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or None  # "" vira None (local não usa chave)
COLLECTION = os.getenv("QDRANT_COLLECTION", "conhecimento_maritimo")

# --- Embeddings (fastembed, roda em CPU, entende português) ---
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384

# --- Busca esparsa (BM25: casa palavras exatas, complementa a busca por sentido) ---
SPARSE_MODEL = "Qdrant/bm25"
SPARSE_LANGUAGE = "portuguese"

# Nomes dos vetores dentro de cada ponto do Qdrant
VETOR_DENSO = "dense"
VETOR_ESPARSO = "sparse"
# Pasta de cache do modelo. Na imagem Docker o modelo é baixado na build e fica aqui.
FASTEMBED_CACHE_DIR = os.getenv("FASTEMBED_CACHE_DIR") or None

# --- Fonte dos documentos ---
DADOS_JSON = RAIZ / "src" / "dados" / "situacao_tempestade.json"