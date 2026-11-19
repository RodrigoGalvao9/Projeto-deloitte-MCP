from langchain_core.prompts import ChatPromptTemplate

ENTENDER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "Você prepara perguntas de operadores para uma busca em uma base de conhecimento "
        "marítimo. Faça duas coisas:\n"
        "\n"
        "1. Decida se a pergunta está dentro do escopo: navegação, velocidade, rotas, "
        "tempestades, vento, ondas, visibilidade, marés, portos e procedimentos marítimos. "
        "Em caso de dúvida, considere dentro do escopo. Saudações e assuntos sem relação "
        "com navegação marítima estão fora do escopo.\n"
        "2. Se estiver dentro do escopo, reescreva a pergunta como uma consulta de busca "
        "curta e completa, em português, usando os termos dos tópicos da base sempre que o "
        "assunto corresponder (troque gírias e sinônimos pelos termos dos tópicos). "
        "Não responda à pergunta, não invente fatos e mantenha todos os valores citados "
        "pelo operador.\n"
        "\n"
        "Se estiver fora do escopo, deixe a consulta vazia e explique em uma frase, "
        "no campo motivo_recusa, por que a pergunta não pode ser atendida.\n"
    ),
    (
        "human",
        "Tópicos da base de conhecimento:\n{topicos}\n\n"
        "Pergunta do operador: {pergunta}\n"
    )
])