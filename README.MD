# Ocean RAG MCP

Este repositório é o piloto da plataforma **Ocean**. Ele valida a integração entre RAG marítimo, LangGraph, FastMCP e a aplicação de ações operacionais sobre uma frota simulada.

> Os dados são fictícios e servem apenas para demonstração. Não use as respostas para navegação real.

## Plataforma Ocean

O piloto está sendo evoluído para uma plataforma composta por quatro repositórios:

| Repositório | Responsabilidade |
|---|---|
| [Ocean-MCP-Ingestor](https://github.com/RodrigoGalvao9/Ocean-MCP-Ingestor) | Ingestão e indexação do conteúdo marítimo |
| [ocean-agent-api](https://github.com/RodrigoGalvao9/ocean-agent-api) | API dos agentes e da lógica operacional |
| [ocean-frontend](https://github.com/RodrigoGalvao9/ocean-frontend) | Interface para operadores |
| [ocean-rag-mcp](https://github.com/RodrigoGalvao9/ocean-rag-mcp) | Piloto MCP/RAG; busca, estado da frota e execução de ações |

Este repositório demonstra o fluxo ponta a ponta em uma interface de terminal. A implementação da plataforma será distribuída entre os demais repositórios.

## O que este piloto faz

- Entende perguntas e instruções em linguagem natural.
- Consulta o estado de uma frota fictícia.
- Busca conhecimento marítimo no Qdrant usando busca híbrida densa + BM25.
- Usa LangGraph para navegar entre leitura, análise, revisão e execução.
- Expõe ferramentas MCP com FastMCP.
- Aplica mudanças de velocidade com controle de versão e idempotência.
- Solicita aprovação humana quando uma ação não é aprovada após as revisões.

## Arquitetura

```text
Operador
  |
  v
src/app/main.py
  |
  v
LangGraph
  |-- entender_pergunta
  |-- ler_estado
  |-- consultar_conhecimento
  |-- navegador
  |-- revisor
  |-- validar
  |-- executar
  `-- confirmar / escalar / finalizar
          |
          v
Servidor FastMCP
  |-- get_fleet_state
  |-- buscar_conhecimento
  |-- listar_topicos
  `-- set_speed
          |
          v
Qdrant
  `-- coleção conhecimento_maritimo
```

## Tecnologias

- Python
- LangGraph
- FastMCP
- Qdrant
- Cloudflare Workers AI para embeddings densos
- BM25 local via FastEmbed
- Docker Compose
- Groq, OpenAI, Anthropic ou Google Gemini como provedores de LLM

## Fluxos

- **Pergunta informativa:** responde sem alterar o navio.
- **Pergunta fora do escopo:** recusa a resposta.
- **Ação operacional:** passa por navegação, revisão e validação.
- **Ação aprovada:** chama `set_speed` no servidor MCP.
- **Conflito de estado:** relê o estado e tenta novamente.
- **Revisões esgotadas:** solicita aprovação humana antes de continuar.

## Estrutura

```text
ocean-rag-mcp/
|-- Dockerfile
|-- docker-compose.yml
|-- render.yaml
|-- requirements.txt
|-- requirements-server.txt
|-- src/
|   |-- app/
|   |-- dados/
|   |-- graph/
|   |-- mcp-server/
|   |-- rag/
|   |-- scripts/
|   `-- utils/
`-- qdrant_storage/
```

`qdrant_storage/`, ambientes virtuais e arquivos `.env` são locais e não devem ser versionados.

## Pré-requisitos

- Windows
- Python 3.12 ou superior
- Docker Desktop
- Docker Compose
- Conta e credenciais da Cloudflare para os embeddings densos
- Uma chave de API do provedor de LLM escolhido

## Configuração no Windows

Na raiz do projeto:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Se a política do PowerShell bloquear scripts nesta sessão:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Crie um arquivo `.env` a partir de `.env.example`:

```powershell
Copy-Item .env.example .env
```

Exemplo mínimo com Groq:

```dotenv
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
GROQ_API_KEY=sua-chave-aqui

CLOUDFLARE_ACCOUNT_ID=seu-account-id
CLOUDFLARE_API_TOKEN=seu-api-token

QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION=conhecimento_maritimo

MCP_SERVER_URL=http://127.0.0.1:8000/mcp
MCP_AUTH_TOKEN=
SIMULAR_CONFLITO=false
```

Não faça commit do `.env` ou das credenciais.

### Variáveis principais

| Variável | Uso |
|---|---|
| `LLM_PROVIDER` | `groq`, `openai`, `anthropic` ou `google` |
| `LLM_MODEL` | Modelo do provedor selecionado |
| `GROQ_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY` | Credencial do provedor correspondente |
| `CLOUDFLARE_ACCOUNT_ID` | Conta usada para gerar embeddings |
| `CLOUDFLARE_API_TOKEN` | Token autorizado a executar o modelo de embedding |
| `QDRANT_URL` | Endereço do Qdrant |
| `QDRANT_API_KEY` | Chave opcional para Qdrant remoto |
| `QDRANT_COLLECTION` | Nome da coleção; padrão `conhecimento_maritimo` |
| `MCP_SERVER_URL` | Endpoint HTTP usado pela aplicação |
| `MCP_AUTH_TOKEN` | Token Bearer opcional compartilhado entre cliente e servidor |
| `SIMULAR_CONFLITO` | `true` força uma versão antiga na primeira tentativa de ação |

## Subir o Qdrant

Na raiz do projeto:

```powershell
docker compose up -d
docker compose ps
```

Serviços locais:

| Componente | Endereço |
|---|---|
| Qdrant REST | `http://127.0.0.1:6333` |
| FastMCP HTTP | `http://127.0.0.1:8000/mcp` |
| Health check MCP | `http://127.0.0.1:8000/health` |

Verificação rápida:

```powershell
Invoke-RestMethod "http://127.0.0.1:6333/collections" -Method Get
```

Para interromper o Qdrant sem apagar os dados:

```powershell
docker compose stop
```

## Indexar o RAG

Depois que o Qdrant estiver ativo:

```powershell
python -m src.rag.ingest
```

O comando:

1. lê `src/dados/situacao_tempestade.json`;
2. cria vetores densos pela Cloudflare;
3. cria vetores esparsos BM25 localmente;
4. recria a coleção no Qdrant;
5. grava os documentos com payload de identificação e título.

A reindexação recria a coleção. Execute-a novamente após alterar a base.

Teste a busca isoladamente:

```powershell
python -m src.rag.retriever "Como leio a tábua de marés?"
python -m src.rag.retriever "Qual o limite de velocidade em tempestade na rota direta?" --modo hibrido
```

## Executar o piloto

Em um terminal, inicie o servidor MCP:

```powershell
.\venv\Scripts\Activate.ps1
python src/mcp-server/mcp_server.py
```

Em outro terminal, inicie a interface:

```powershell
.\venv\Scripts\Activate.ps1
python -m src.app.main
```

No terminal da aplicação:

- escolha um dos navios simulados;
- digite uma pergunta ou instrução;
- use `trocar` para selecionar outro navio;
- use `sair` para encerrar;
- pressione `Enter` para executar a avaliação padrão.

## Teste do MCP

Com o servidor ativo:

```powershell
python -m src.scripts.testar_mcp
```

O script verifica:

- aplicação de uma velocidade;
- repetição idempotente da operação;
- reutilização indevida da chave de idempotência;
- conflito de versão do estado.

Reinicie o servidor para restaurar o estado inicial da frota após os testes.

## Controle de concorrência

`set_speed` utiliza:

- `expected_state_version` para rejeitar alterações sobre estado antigo;
- `idempotency_key` para evitar execuções repetidas;
- hash dos parâmetros para impedir o uso da mesma chave com valores diferentes.

Ao receber `STATE_VERSION_CONFLICT`, o LangGraph relê o estado e tenta novamente.

Para testar esse comportamento:

```dotenv
SIMULAR_CONFLITO=true
```

## Ordem completa de execução

```powershell
# Terminal 1
docker compose up -d
python -m src.rag.ingest

# Terminal 2
.\venv\Scripts\Activate.ps1
python src/mcp-server/mcp_server.py

# Terminal 3
.\venv\Scripts\Activate.ps1
python -m src.app.main
```

## Deploy do servidor MCP

O `Dockerfile` gera uma imagem enxuta com o servidor MCP e suas dependências.

O `render.yaml` configura o serviço `ocean-rag-mcp` no Render e solicita:

- `QDRANT_URL`
- `QDRANT_API_KEY`
- `MCP_AUTH_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_API_TOKEN`

No Render, configure o `PORT` automaticamente; o servidor também aceita `MCP_HOST` e usa `0.0.0.0` por padrão.

## Solução de problemas

### Porta ocupada

```powershell
docker compose ps
docker compose down
Get-NetTCPConnection -LocalPort 6333
Get-NetTCPConnection -LocalPort 8000
```

### Coleção não encontrada

```powershell
python -m src.rag.ingest
```

### Embeddings indisponíveis

Confirme `CLOUDFLARE_ACCOUNT_ID` e `CLOUDFLARE_API_TOKEN` no `.env` e execute o ingest novamente.

### Servidor MCP sem autenticação

O servidor permite acesso local sem `MCP_AUTH_TOKEN`. Em ambientes remotos, configure o mesmo token no servidor e em `MCP_AUTH_TOKEN` da aplicação cliente.

## Segurança

- Nunca commit chaves ou tokens.
- Mantenha dados fictícios separados de dados reais.
- Não exponha o piloto sem autenticação em redes públicas.
- Valide propostas de ação antes de chamá-las em sistemas reais.
