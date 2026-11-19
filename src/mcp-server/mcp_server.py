import json
import os
import sys
import hashlib
import threading
from pathlib import Path

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

# Coloca src/ no path para importar o pacote rag
# (a pasta mcp-server tem hífen e o arquivo roda como script).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rag.embeddings import embed_esparso  # noqa: E402
from rag.retriever import buscar, listar_topicos as _listar_topicos  # noqa: E402

DADOS = Path(__file__).resolve().parent.parent / "dados" / "situacao_tempestade.json"


def _criar_auth():
    """Autenticação por token (Bearer). Sem MCP_AUTH_TOKEN, o servidor fica aberto (uso local)."""
    token = (os.getenv("MCP_AUTH_TOKEN") or "").strip()

    if not token:
        print("AVISO: MCP_AUTH_TOKEN não definido; servidor SEM autenticação.")
        return None

    try:
        from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
    except ImportError:  # caminho de importação em versões mais novas do FastMCP
        from fastmcp.server.auth.verifiers import StaticTokenVerifier

    return StaticTokenVerifier(
        tokens={token: {"client_id": "agente-langgraph", "scopes": []}}
    )


mcp = FastMCP("ocean", auth=_criar_auth())

FROTA = {
    n["id"]: n
    for n in json.loads(DADOS.read_text(encoding="utf-8"))["navios"]
}

RESPOSTAS: dict[str, dict] = {}
LOCK = threading.RLock()


def _erro(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def _memoria_mb() -> int | None:
    """Memória residente do processo em MB (só Linux; no Windows retorna None)."""
    try:
        with open("/proc/self/status", encoding="utf-8") as f:
            for linha in f:
                if linha.startswith("VmRSS:"):
                    return round(int(linha.split()[1]) / 1024)
    except OSError:
        pass
    return None


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    """Verificação de saúde (pública, sem dados sensíveis)."""
    return JSONResponse({"status": "ok", "memoria_mb": _memoria_mb()})


@mcp.tool
def get_fleet_state() -> dict:
    """Snapshot dos navios, incluindo state_version."""
    with LOCK:
        return {"navios": [dict(n) for n in FROTA.values()]}


@mcp.tool
def buscar_conhecimento(query: str, k: int = 4) -> dict:
    """Busca trechos na base de conhecimento marítimo: limites de vento e ondas,
    rotas, marés e procedimentos de tempestade."""
    k = max(1, min(k, 8))
    try:
        return {"resultados": buscar(query, k)}
    except Exception as e:
        return _erro("RAG_UNAVAILABLE", f"Falha na busca: {e}")


@mcp.tool
def listar_topicos() -> dict:
    """Lista os tópicos (id e título) da base de conhecimento marítimo."""
    try:
        return {"topicos": _listar_topicos()}
    except Exception as e:
        return _erro("RAG_UNAVAILABLE", f"Falha ao listar tópicos: {e}")


@mcp.tool
def set_speed(
    ship_id: str,
    speed_kn: float,
    expected_state_version: int,
    idempotency_key: str,
) -> dict:
    """Aplica uma velocidade-alvo.
    Garante controle de versão e idempotência.
    Regras de negócio devem ser validadas antes da chamada.
    """

    request = {
        "ship_id": ship_id,
        "speed_kn": speed_kn,
        "expected_state_version": expected_state_version,
    }

    request_hash = hashlib.sha256(
        json.dumps(request, sort_keys=True).encode("utf-8")
    ).hexdigest()

    with LOCK:

        # 1. Idempotência
        if idempotency_key in RESPOSTAS:
            registro = RESPOSTAS[idempotency_key]

            if registro["request_hash"] != request_hash:
                return _erro(
                    "IDEMPOTENCY_KEY_REUSED",
                    "Chave reutilizada com parâmetros diferentes",
                )

            return {
                **registro["response"],
                "duplicate": True,
            }

        # 2. Existência do recurso
        navio = FROTA.get(ship_id)

        if navio is None:
            return _erro("SHIP_NOT_FOUND", "Navio inexistente")

        # 3. Concorrência otimista
        if navio["state_version"] != expected_state_version:
            return _erro(
                "STATE_VERSION_CONFLICT",
                f"esperado {expected_state_version}, "
                f"atual {navio['state_version']}",
            )

        # 4. Aplicação da alteração
        antes = navio["velocidade_alvo_kn"]

        navio["velocidade_alvo_kn"] = speed_kn
        navio["state_version"] += 1

        resposta = {
            "status": "committed",
            "ship_id": ship_id,
            "before": antes,
            "after": speed_kn,
            "state_version": navio["state_version"],
            "duplicate": False,
        }

        # 5. Registro idempotente
        RESPOSTAS[idempotency_key] = {
            "request_hash": request_hash,
            "response": resposta,
        }

        return resposta


if __name__ == "__main__":
    # Apenas o BM25 é carregado localmente.
    # Embeddings densos são gerados sob demanda pela Cloudflare.
    embed_esparso(["aquecimento"])

    mcp.run(
        transport="http",
        host=os.getenv("MCP_HOST", "0.0.0.0"),  # no Docker: 0.0.0.0
        port=int(os.getenv("PORT", "8000")),       # o Render define PORT
    )