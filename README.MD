# Projeto Deloitte MCP

Projeto Python com LangGraph e FastMCP para simular a tomada de decisão operacional sobre a velocidade de navios em condições de tempestade.

O projeto utiliza dois agentes:

- **Navegador:** analisa os dados do navio e gera uma proposta de velocidade.
- **Revisor:** revisa a proposta com base nas regras de segurança.

O estado da frota é exposto por um servidor MCP, separado da aplicação principal.

## Arquitetura

```text
Terminal da aplicação
  -> src/app/main.py
  -> LangGraph
  -> Navegador e revisor via LLM
  -> Cliente MCP

Terminal do servidor MCP
  -> src/mcp-server/mcp_server.py
  -> FastMCP na porta 8000
  -> Estado da frota em memória
```

Quando o servidor MCP está ativo, o cliente encontra as ferramentas em:

```text
http://127.0.0.1:8000/mcp
```

## Pré-requisitos

- Windows
- Python 3.14 ou outra versão compatível
- PowerShell
- Conta e chave de API da Groq, caso o provedor escolhido seja Groq

Abra o PowerShell na raiz do projeto:

```powershell
cd C:\Users\USUARIO\Desktop\Codigo\Projeto-deloitte-MCP
```

## Criar o ambiente virtual

No Windows, o ambiente virtual pode ser criado por este comando:

```powershell
python -m venv venv
```

Esse diretório local será chamado de ambiente virtual ou "container virtual" neste guia, não sendo um container Docker.

### Ativar no PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

Quando estiver ativado, o terminal mostrará o prefixo:

```text
(venv)
```

Caso o PowerShell bloqueie a ativação, habilite temporariamente a execução de scripts neste processo:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Para desativar:

```powershell
deactivate
```

## Instalar as dependências

Com o ambiente virtual ativado:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

As principais dependências são LangGraph, LangChain, FastMCP, Pydantic, python-dotenv e os adaptadores dos provedores de LLM.

## Configurar o arquivo `.env`

Crie o arquivo `.env` na raiz do projeto.

Para usar Groq:

```dotenv
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
GROQ_API_KEY=sua-chave-da-groq
SIMULAR_CONFLITO=false
```

Descrição das variáveis:

| Variável | Obrigatória | Descrição |
|---|---|---|
| `LLM_PROVIDER` | Sim | Provedor escolhido: `groq`, `openai`, `anthropic` ou `google` |
| `LLM_MODEL` | Sim | Nome ou identificador do modelo |
| `GROQ_API_KEY` | Ao usar Groq | Chave da API Groq |
| `SIMULAR_CONFLITO` | Não | Usa `true` para testar conflito de versão; o padrão é `false` |

Para ativar o cenário de conflito de versão pela primeira tentativa:

```dotenv
SIMULAR_CONFLITO=true
```

Não compartilhe nem envie o arquivo `.env` para repositórios remotos. Verifique se `.env` está incluído no `.gitignore`.

## Executar o projeto

É necessário abrir **dois terminals** na raiz do projeto.

### Terminal 1: servidor MCP

Ative o ambiente virtual:

```powershell
.\venv\Scripts\Activate.ps1
```

Inicie o servidor:

```powershell
python .\src\mcp-server\mcp_server.py
```

O servidor ficará disponível em:

```text
http://127.0.0.1:8000/mcp
```

Mantenha esse terminal aberto.

### Terminal 2: aplicação principal

Em outro terminal, ativado na raiz do projeto:

```powershell
.\venv\Scripts\Activate.ps1
python -m src.app.main
```

Escolha um navio:

```text
1. S1-FAROL
2. S2-MARE
3. S3-CORAL
```

A aplicação executa o grafo LangGraph e consulta o servidor MCP.

## Testar o servidor MCP isoladamente

Com o servidor MCP ativo no Terminal 1, execute no Terminal 2:

```powershell
python -m src.scripts.testar_mcp
```

Esse script testa:

- Aplicação de velocidade.
- Idempotência da mesma operação.
- Rejeição de chave reutilizada com parâmetros diferentes.
- Conflito de versão de estado.

## Estrutura do projeto

```text
src/
├── app/
│   └── main.py
├── dados/
│   └── situacao_tempestade.json
├── graph/
│   ├── builder.py
│   ├── routing.py
│   ├── state.py
│   ├── Node/
│   │   ├── ler_estado.py
│   │   ├── navegador.py
│   │   ├── revisor.py
│   │   ├── validar.py
│   │   ├── executar.py
│   │   ├── confirmar.py
│   │   ├── escalar.py
│   │   └── finalizar.py
│   └── prompt/
│       ├── navegador_prompt.py
│       └── revisor_prompt.py
├── mcp-server/
│   └── mcp_server.py
├── scripts/
│   └── testar_mcp.py
├── utils/
│   ├── llm_adapter.py
│   └── mcp_client.py
└── visualizador_grafo.py
```

### `src/app`

Contém o ponto de entrada da aplicação.

- `main.py`: carrega o `.env`, solicita o navio, inicia o grafo e processa possíveis interrupções para aprovação humana.

### `src/dados`

Contém os dados fictícios da simulação.

- `situacao_tempestade.json`: navios, portos, zonas marítimas, previsões, marés, alertas e regras de conhecimento. O servidor MCP usa esse arquivo como base.

### `src/graph`

Implementa o fluxo LangGraph.

- `state.py`: define os campos compartilhados entre os nós.
- `builder.py`: registra os nós e compila o grafo.
- `routing.py`: decide o próximo nó após revisão, validação e execução.
- `prompt/`: prompts do navegador e do revisor.
- `Node/`: etapas individuais do processamento.

Os nós são:

| Nó | Objetivo |
|---|---|
| `ler_estado` | Consulta o estado atual da frota |
| `navegador` | Gera `SET_SPEED` ou `NO_ACTION` |
| `revisor` | Aprova ou rejeita a proposta |
| `validar` | Valida velocidade e formato da proposta |
| `executar` | Executa a alteração no servidor MCP |
| `confirmar` | Confirma o estado aplicado |
| `escalar` | Solicita aprovação humana |
| `finalizar` | Produz o resultado final |

### `src/mcp-server`

- `mcp_server.py`: cria o servidor FastMCP e expõe `get_fleet_state` e `set_speed`.

A ferramenta `set_speed` possui controle de:

- Versão esperada do estado.
- Idempotência.
- Reutilização incompatível de chave.
- Estado em conflito.

### `src/utils`

- `llm_adapter.py`: cria o cliente do provedor configurado em `LLM_PROVIDER`.
- `mcp_client.py`: conecta ao servidor MCP e converte as respostas em estruturas Python.

### `src/scripts`

- `testar_mcp.py`: testa diretamente as ferramentas MCP.

### `src/visualizador_grafo.py`

Contém o código auxiliar que gera uma representação visual do grafo LangGraph.

## Gerar o grafo visual

O arquivo [`src/visualizador_grafo.py`](C:/Users/Rodrigo/Desktop/Codigo/Projeto-deloitte-MCP/src/visualizador_grafo.py) está configurado para gerar o diagrama usando Mermaid.

Há três formas principais de utilizá-lo.

### Opção 1: criar o PNG diretamente

Com o ambiente virtual ativado, execute no terminal da raiz:

```powershell
python -c "from src.graph.builder import graph; graph.get_graph().draw_mermaid_png(output_file_path='grafo.png')"
```

O arquivo `grafo.png` será criado na raiz do projeto.

### Opção 2: visualizar como texto Mermaid

```powershell
python -c "from src.graph.builder import graph; print(graph.get_graph().draw_mermaid())"
```

Esse comando imprime a definição Mermaid no terminal. Ela pode ser usada em ferramentas que suportam Mermaid.

### Opção 3: usar Jupyter no VS Code

Instale o suporte Jupyter no VS Code, caso ainda não esteja instalado.

Crie um arquivo chamado `grafo.ipynb` na raiz do projeto e adicione uma célula com:

```python
from src.graph.builder import graph
from IPython.display import Image, display

png = graph.get_graph().draw_mermaid_png()
display(Image(png))
```

Execute a célula com `Shift+Enter`.

Também é possível salvar o resultado em PNG:

```python
from src.graph.builder import graph

graph.get_graph().draw_mermaid_png(output_file_path="grafo.png")
```

### Usar o terminal IPython

Abra o IPython:

```powershell
.\venv\Scripts\Activate.ps1
ipython
```

Execute o visualizador:

```python
%run src/visualizador_grafo.py
```

Esse modo pode imprimir apenas:

```text
<IPython.core.display.Image object>
```

Isso acontece porque o IPython tradicional não renderiza a imagem automaticamente no terminal. Nesse caso, use a opção que salva o PNG:

```python
from src.graph.builder import graph

graph.get_graph().draw_mermaid_png(output_file_path="grafo.png")
```

## Fluxo de execução

```text
Main
  -> ler_estado
  -> navegador
  -> revisor
  -> aprovado?
       -> não e ainda existem tentativas
          -> navegador novamente
       -> não e não existem tentativas
          -> escalar para operador
       -> sim
          -> validar
             -> executar via MCP
             -> confirmar
             -> finalizar
```

A aplicação também pode finalizar sem executar uma ação quando a proposta for `NO_ACTION` ou inválida.
