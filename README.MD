# Projeto Deloitte MCP

Aplicacao em Python que combina **LangGraph**, **FastMCP**, **Qdrant** e um provedor de LLM para simular a tomada de decisoes operacionais em uma frota maritima.

O operador escolhe um navio e faz uma pergunta em linguagem natural. O sistema:

1. consulta o estado do navio em um servidor MCP;
2. busca trechos relevantes em uma base de conhecimento maritima (RAG);
3. pede uma proposta ao agente Navegador;
4. faz o agente Revisor validar a proposta contra a base;
5. aplica uma alteracao de velocidade pela ferramenta MCP, quando aprovada;
6. informa o resultado ou solicita aprovacao humana em caso de escalamento.

> Os dados deste projeto sao **ficticios** e servem apenas para demonstracao. Nao use as respostas para navegacao real.

## Recursos principais

- Interface interativa no terminal.
- Grafo de decisao implementado com LangGraph.
- Servidor MCP com FastMCP na porta `8000`.
- Qdrant para busca vetorial na porta `6333`.
- Embeddings locais com FastEmbed; nao exige uma chave de API de embeddings.
- Suporte a Groq, OpenAI, Anthropic e Google Gemini.
- Controle de versao, idempotencia e conflitos no MCP.
- Fluxo humano de aprovacao em revisoes esgotadas.

## Arquitetura

```text
Operador
  |
  | pergunta no terminal
  v
src/app/main.py
  |
  v
LangGraph
  |-- ler_estado
  |-- consultar_conhecimento
  |-- navegador
  |-- revisor
  |-- validar
  |-- executar
  |-- confirmar/finalizar/escalar
  |
  +---- servidor MCP FastMCP (porta 8000)
              |-- get_fleet_state
              |-- buscar_conhecimento
              +-- set_speed
                       |
                       v
Qdrant (Docker, porta 6333)
  +-- colecao conhecimento_maritimo
```

Fluxos distintos:

- **Perguntas informativas:** Navegador usa `RESPONDER` e encerra sem alterar o navio.
- **Fora do escopo:** Navegador usa `RECUSAR` e encerra sem alterar o navio.
- **Acoes do navio:** Navegador usa `SET_SPEED` ou `NO_ACTION`, passara por revisao e, se aprovada, podera chamar o MCP.

## Tecnologias e portas

| Componente | Porta | Endpoint/comando |
|---|---:|---|
| FastMCP | `8000` | `http://127.0.0.1:8000/mcp` |
| Qdrant REST | `6333` | `http://127.0.0.1:6333` |
| Qdrant gRPC | `6334` | Uso interno/futuro |
| Aplicacao Python | - | `python -m src.app.main` |

## Estrutura do projeto

```text
Projeto-deloitte-MCP/
|-- docker-compose.yml
|-- requirements.txt
|-- README.MD
|-- grafo.png
|-- src/
|   |-- app/
|   |   `-- main.py
|   |-- dados/
|   |   `-- situacao_tempestade.json
|   |-- graph/
|   |   |-- builder.py
|   |   |-- routing.py
|   |   |-- state.py
|   |   |-- Node/
|   |   |   |-- ler_estado.py
|   |   |   |-- consultar_conhecimento.py
|   |   |   |-- navegador.py
|   |   |   |-- revisor.py
|   |   |   |-- validar.py
|   |   |   |-- executar.py
|   |   |   |-- confirmar.py
|   |   |   |-- escalar.py
|   |   |   |-- responder.py
|   |   |   `-- finalizar.py
|   |   `-- prompt/
|   |       |-- navegador_prompt.py
|   |       `-- revisor_prompt.py
|   |-- mcp-server/
|   |   `-- mcp_server.py
|   |-- rag/
|   |   |-- config.py
|   |   |-- embeddings.py
|   |   |-- ingest.py
|   |   `-- retriever.py
|   |-- scripts/
|   |   `-- testar_mcp.py
|   |-- utils/
|   |   |-- conhecimento.py
|   |   |-- llm_adapter.py
|   |   `-- mcp_client.py
|   `-- visualizador_grafo.py
`-- qdrant_storage/
```

`qdrant_storage/` e `venv/` nao devem ser enviados ao repositorio. O volume Docker persiste os dados do Qdrant nesse diretorio local.

## Pre-requisitos

- Windows.
- Docker Desktop com o engine ativo.
- Docker Compose disponivel como `docker compose`.
- Python 3.14 recomendado pelo ambiente atual.
- PowerShell.
- Uma chave de API do provedor escolhido.
- Acesso a Internet no primeiro uso do modelo de embeddings.

Com Docker Desktop instalado, verifique os comandos:

```powershell
docker --version
docker compose version
```

Verifique a sintaxe Docker sem subir containers:

```powershell
docker compose config
```

## Instalacao no Windows

Na raiz do projeto:

```powershell
cd C:\Users\USUARIO\Desktop\Codigo\Projeto-deloitte-MCP
```

### 1. Criar o ambiente virtual

```powershell
python -m venv venv
```

### 2. Ativar o ambiente

PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Se a execucao de scripts estiver bloqueada, use somente para a sessao atual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Prompt bem-sucedido:

```text
(venv) PS C:\...>
```

### 3. Instalar as dependencias

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configuracao do `.env`

Crie um arquivo `.env` na raiz do projeto. Um exemplo minimo com Groq:

```dotenv
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
GROQ_API_KEY=sua-chave-aqui

SIMULAR_CONFLITO=false

QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION=conhecimento_maritimo
```

Variaveis de ambiente:

| Variavel | Obrigatoria | Descricao |
|---|---:|---|
| `LLM_PROVIDER` | Sim | `groq`, `openai`, `anthropic` ou `google`. |
| `LLM_MODEL` | Sim | Modelo correspondente ao provedor. |
| `GROQ_API_KEY` | Groq | Chave da API Groq. |
| `OPENAI_API_KEY` | OpenAI | Chave da API OpenAI, caso essa integracao seja usada pela sua biblioteca. |
| `ANTHROPIC_API_KEY` | Anthropic | Chave da API Anthropic, caso essa integracao seja usada pela sua biblioteca. |
| `GOOGLE_API_KEY` | Google | Chave da API Google, caso essa integracao seja usada pela sua biblioteca. |
| `SIMULAR_CONFLITO` | Nao | `true` envia uma versao antiga uma vez para testar recuperacao de conflito. |
| `QDRANT_URL` | Nao | Endereco do Qdrant; padrao `http://localhost:6333`. |
| `QDRANT_API_KEY` | Nao | Chave do Qdrant hospedado/remoto; deixe vazia para o Docker local. |
| `QDRANT_COLLECTION` | Nao | Nome da colecao; padrao `conhecimento_maritimo`. |

Nao coloque chaves no terminal compartilhado nem commit o arquivo `.env`. Ele ja esta coberto pelo `.gitignore`.

## Criar e subir os containers

O arquivo `docker-compose.yml` inicia somente o Qdrant:

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./qdrant_storage:/qdrant/storage
    restart: unless-stopped
```

Com Docker Desktop aberto, execute na raiz:

```powershell
docker compose up -d
```

Verifique os containers:

```powershell
docker compose ps
docker ps
```

O resultado esperado mostra o container `qdrant` com o estado `Up/Running`.

Verifique a API diretamente:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:6333/collections" -Method Get
```

Os logs podem ser acompanhados com:

```powershell
docker compose logs -f qdrant
```

Para parar sem apagar os dados:

```powershell
docker compose stop
```

Para iniciar novamente:

```powershell
docker compose start
```

Para parar e remover o container; os dados permanecem em `qdrant_storage/`:

```powershell
docker compose down
```

Para remover tambem o volume persistido localmente, nao use apenas este guia: faca backup e exclua manualmente apenas a pasta `qdrant_storage/` depois de confirmar que nao contem dados necessarios.

## Indexar o RAG

Esta etapa e obrigatoria depois que o Qdrant foi criado pela primeira vez.

Com o ambiente virtual ativo e o container `qdrant` rodando:

```powershell
python -m src.rag.ingest
```

Saida esperada:

```text
10 documentos lidos de situacao_tempestade.json
10 pontos gravados na colecao 'conhecimento_maritimo' (http://localhost:6333)
```

O que o comando faz:

1. le `src/dados/situacao_tempestade.json`;
2. usa apenas os itens de `base_conhecimento`;
3. cria o texto de cada documento com `titulo + texto`;
4. gera vetores locais de 384 dimensoes com o modelo:
   `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`;
5. recria a colecao no Qdrant;
6. grava os documentos como pontos, junto de `doc_id`, `titulo` e `tags`.

A reindexacao apaga e recria a colecao. Execute-a sempre que alterar os documentos em `base_conhecimento`.

O download do modelo FastEmbed pode demorar na primeira execucao. Depois, ele costuma ficar em cache local.

### Testar a busca isoladamente

```powershell
python -m src.rag.retriever "Como leio a tabua de mares?"
python -m src.rag.retriever "Qual o limite de velocidade em tempestade na rota direta?"
```

Saida abreviada:

```text
Pergunta: ...
1. [0.xxx] KB-009 - Limites de velocidade em tempestade
...
```

Se aparecer `RAG_UNAVAILABLE` ou erro de conexao, confirme primeiro que o container esta rodando e que `QDRANT_URL` aponta para `http://localhost:6333`.

## Executar o servidor MCP

Abra o primeiro terminal na raiz do projeto e ative o ambiente virtual:

```powershell
.\venv\Scripts\Activate.ps1
python .\src\mcp-server\mcp_server.py
```

Saida esperada em uma versao FastMCP recente:

```text
Starting MCP server 'ocean' with transport 'http' on http://127.0.0.1:8000/mcp
```

Mantenha este terminal aberto.

Antes da primeira chamada MCP, o servidor:

- pre-carrega o modelo de embeddings;
- conecta ao Qdrant;
- expoe `get_fleet_state`, `buscar_conhecimento` e `set_speed`.

No MCP existem tres ferramentas:

| Ferramenta | Finalidade |
|---|---|
| `get_fleet_state` | Retorna navios e `state_version` atuais. |
| `buscar_conhecimento` | Faz busca vetorial no Qdrant e retorna trechos. |
| `set_speed` | Aplica velocidade com versao esperada e chave de idempotencia. |

## Executar a aplicacao

Abra um segundo terminal na raiz:

```powershell
.\venv\Scripts\Activate.ps1
python -m src.app.main
```

Escolha o navio:

```text
1. S1-FAROL
2. S2-MARE
3. S3-CORAL
```

Depois digite uma pergunta. No prompt:

- `Enter`: executa a avaliacao padrao da situacao;
- `trocar`: escolhe outro navio;
- `sair`: encerra o programa.

O `thread_id` muda em cada execucao, por isso o checkpointer em memoria nao mistura conversas anteriores.

## Exemplos de perguntas

Todas as perguntas abaixo podem ser inseridas no terminal da aplicacao.

### Fora da base maritima

```text
Qual a capital da Franca?
```

Resultado esperado: `RECUSAR`, pois a pergunta esta fora do escopo maritimo.

### Entrada em porto com calado alto

```text
Quando devo entrar no porto com calado alto?
```

Deve recuperar trechos sobre janela de mare e folga sob a quilha.

### Como ler uma tabua de mares

```text
Como leio a tabua de mares?
```

Deve recuperar `KB-006` e responder com preamar, baixa-mar, horario e altura.

### Velocidade em tempestade na rota direta

```text
Qual o limite de velocidade em tempestade na rota direta?
```

Deve recuperar `KB-009` e responder que o limite da simulacao e 12 nos.

### Avaliacao operacional

```text
Avalie a situacao do navio e decida a acao adequada.
```

Nesse fluxo o grafo pode propor `SET_SPEED` ou `NO_ACTION`, passar pelo revisor e aplicar a velocidade.

## Testar o MCP isoladamente

Com o servidor MCP ativo em outro terminal:

```powershell
python -m src.scripts.testar_mcp
```

O script verifica:

1. aplicacao da primeira velocidade;
2. repeticao da mesma chave com os mesmos parametros;
3. reutilizacao indevida da chave com parametros diferentes;
4. conflito de versao de estado.

Exemplo de resultados esperados:

```text
1 {'status': 'committed', 'state_version': 2, ...}
2 {..., 'duplicate': True}
3 {'error': {'code': 'IDEMPOTENCY_KEY_REUSED', ...}}
4 {'error': {'code': 'STATE_VERSION_CONFLICT', ...}}
```

A execucao altera o estado em memoria do servidor MCP. Reinicie o servidor para voltar os navios ao estado inicial do JSON.

## Controle de concorrencia e idempotencia

`set_speed` usa:

- `expected_state_version`: rejeita alteracoes sobre uma versao antiga;
- `idempotency_key`: impede execucao repetida da mesma operacao;
- hash dos parametros: rejeita reutilizacao da chave com valores diferentes.

Se o servidor retornar `STATE_VERSION_CONFLICT`, o LangGraph relera o estado e tentara novamente ate duas vezes.

Para exercitar esse fluxo automaticamente:

```dotenv
SIMULAR_CONFLITO=true
```

Na primeira tentativa, `executar.py` envia deliberadamente `state_version - 1`. Reinicie a aplicacao ou reinicie o servidor MCP apos os testes para evitar estado acumulado.

## Fluxo LangGraph

```text
START
  -> ler_estado
  -> consultar_conhecimento
  -> navegador

navegador
  -> RESPONDER ou RECUSAR
       -> responder -> END

navegador
  -> SET_SPEED ou NO_ACTION
       -> revisor

revisor
  -> aprovado
       -> validar
       -> executar
       -> confirmar
       -> finalizar -> END

revisor
  -> rejeitado
       -> tenta novamente por ate 2 rodadas
       -> esgotado
            -> escalar
            -> aprovacao humana
            -> finalizar -> END
```

Ao escalar, a aplicacao imprime os dados da proposta e pergunta:

```text
Deseja continuar? (s/n)
```

Se responder `s`, o operador pode informar um motivo de excecao.

## Gerar o grafo visual

Existem duas formas principais de gerar o diagrama.

### Opcao 1: gerar diretamente pelo terminal

Com o ambiente virtual ativo, na raiz do projeto:

```powershell
python -c "from src.graph.builder import graph; graph.get_graph().draw_mermaid_png(output_file_path='grafo.png')"
```

Para imprimir apenas o Mermaid:

```powershell
python -c "from src.graph.builder import graph; print(graph.get_graph().draw_mermaid())"
```

### Opcao 2: gerar pelo IPython ou Jupyter

Com o ambiente virtual ativo, abra o IPython:

```powershell
ipython
```

Dentro do IPython, execute o visualizador:

```python
%run src/visualizador_grafo.py
```

Depois gere o arquivo PNG na raiz do projeto:

```python
from src.graph.builder import graph

graph.get_graph().draw_mermaid_png(output_file_path="grafo.png")
```

O IPython tradicional pode mostrar apenas:

```text
<IPython.core.display.Image object>
```

Isso nao impede a geracao do arquivo. Se o objetivo for visualizar a imagem diretamente no VS Code, crie um notebook `grafo.ipynb` e execute uma celula com:

```python
from src.graph.builder import graph

grafo = graph.get_graph().draw_mermaid_png(output_file_path="grafo.png")
```

Em seguida, abra o arquivo `grafo.png` na raiz do projeto.

O projeto ja inclui `grafo.png`. Ele pode ser regenerado depois de alterar `src/graph/builder.py` ou `src/graph/routing.py`.

## Ordem completa de inicializacao

```powershell
# Terminal 0 - raiz do projeto
.\venv\Scripts\Activate.ps1
docker compose up -d
docker compose ps
python -m src.rag.ingest

# Terminal 1
.\venv\Scripts\Activate.ps1
python .\src\mcp-server\mcp_server.py

# Terminal 2
.\venv\Scripts\Activate.ps1
python -m src.app.main
```

## Solucao de problemas

### `docker` nao foi reconhecido

- Instale ou abra o Docker Desktop.
- Reinicie o PowerShell depois da instalacao.
- Confirme `docker --version` e `docker compose version`.

### Porta `6333` em uso

```powershell
docker compose ps
docker compose down
Get-NetTCPConnection -LocalPort 6333
```

Se outro processo usa a porta, encerre-o de forma controlada ou altere as duas configuracoes:

1. o mapeamento em `docker-compose.yml`, por exemplo `16333:6333`;
2. `QDRANT_URL=http://localhost:16333` no `.env`.

### Porta `8000` em uso

Confirme no terminal MCP qual processo inicia o servidor. Se houver outra instancia MCP, encerre-a antes de iniciar outra e tente novamente.

### `Collection not found`

Execute a ingestao:

```powershell
python -m src.rag.ingest
```

### Busca sem resultados ou resultados ruins

- confira se o JSON da base foi alterado e reexecute a ingestao;
- use termos presentes na base;
- teste a busca diretamente com `python -m src.rag.retriever "..."`
- verifique se o container Qdrant continua ativo.

### `LLM_PROVIDER nao foi definido`

Confira o `.env` na raiz e confirme:

```dotenv
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
GROQ_API_KEY=sua-chave
```

O adaptador em `src/utils/llm_adapter.py` reconhece somente os provedores `groq`, `openai`, `anthropic` e `google`.

### RAG indisponivel mas aplicacao continua

O codigo foi preparado para continuar sem o RAG:

- `consultar_conhecimento` registra a falha e entrega uma lista vazia;
- o navegador recebe uma mensagem informando que a base esta vazia;
- em caso de decisao de velocidade, o navegador deve usar `NO_ACTION`;
- em caso de pergunta informativa, deve responder que a informacao nao esta disponivel.
