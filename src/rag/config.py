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

# --- Fonte dos documentos ---
DADOS_JSON = RAIZ / "src" / "dados" / "situacao_tempestade.json"