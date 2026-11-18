"""Formatação dos trechos da base de conhecimento para uso nos prompts."""


def formatar_conhecimento(trechos: list[dict]) -> str:
    """Transforma os trechos recuperados pelo RAG em texto para o prompt."""
    if not trechos:
        return "Nenhum trecho disponível."
    return "\n".join(f"- [{t['id']}] {t['titulo']}: {t['texto']}" for t in trechos)