import json
import os

from fastmcp.client import Client
from langchain.mcp import MCPAdapter


def _criar_cliente() -> Client:
    """Cria o cliente MCP. URL e token vêm do ambiente (.env).
    São lidos aqui, e não no import, porque o load_dotenv() roda depois dos imports."""
    url = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")
    token = os.getenv("MCP_AUTH_TOKEN")

    if token:
        return Client(url, auth=token)

    return Client(url)


async def get_tools_by_name():
    """
    Conecta ao servidor MCP e disponibiliza
    as ferramentas em um dicionário pelo nome.
    """

    async with MCPAdapter(_criar_cliente()) as adapter:
        tools = await adapter.list_tools()

    return {
        tool.name: tool
        for tool in tools
    }


def parse_result(raw):
    """
    Interpreta os resultados retornados pelas tools MCP.
    Converte blocos de texto JSON em dicionários Python.
    """

    # Já é um dicionário
    if isinstance(raw, dict):
        return raw

    # É uma string JSON
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    # É uma lista de blocos MCP
    if isinstance(raw, list):
        for bloco in raw:

            if isinstance(bloco, dict):
                texto = bloco.get("text")

            else:
                texto = getattr(bloco, "text", None)

            if texto:
                try:
                    return json.loads(texto)
                except json.JSONDecodeError:
                    return texto

        return raw

    # Resultado no formato ToolMessage
    content = getattr(raw, "content", None)

    if content is not None:
        return parse_result(content)

    # Alguns resultados estruturados ficam no artifact
    artifact = getattr(raw, "artifact", None)

    if artifact is not None:
        return artifact

    return raw