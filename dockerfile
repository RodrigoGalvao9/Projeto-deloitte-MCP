FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FASTEMBED_CACHE_DIR=/app/.fastembed_cache \
    MCP_HOST=0.0.0.0

WORKDIR /app

# Dependências primeiro: esta camada só é refeita quando o requirements muda
COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt

# Código do RAG + download do modelo na build (evita baixar a cada reinício do serviço)
COPY src/rag ./src/rag
RUN python -c "from src.rag.embeddings import embed_esparso; embed_esparso(['x'])"

# Restante do que o servidor precisa
COPY src/dados ./src/dados
COPY src/mcp-server ./src/mcp-server

EXPOSE 8000
CMD ["python", "src/mcp-server/mcp_server.py"]