# RepoNexia — Guia de uso

## Instalação

Via PyPI (pacote publicado):
  pip install reponexia
  pip install "reponexia[llm]"        # para usar o LLM real

A partir do código-fonte (clone):
  python -m venv .venv
  .venv\Scripts\Activate.ps1          # Linux/macOS: source .venv/bin/activate

  # Opção A (após publicar): usa o wheel do core, sem Rust
  pip install -e .

  # Opção B (testar o core local): compila o Rust
  pip install ./core
  pip install -e ".[llm]"

O binário do motor é procurado nesta ordem:
  REPONEXIA_CORE -> Scripts do ambiente -> PATH -> core/target/{release,debug}

## Comandos

  reponexia guia [topico]               Este guia
  reponexia map <path>                  Estrutura do repo (JSON, sem LLM)
  reponexia graph <path> [--format]     Exporta o grafo (json|mermaid)
  reponexia explain <path> --dry-run    Onboarding estrutural, sem LLM
  reponexia explain <path> --model ...  Onboarding com LLM
  reponexia ask <path> "pergunta"       Pergunta sobre o índice

## Ver os dados do grafo

  reponexia map .                                 JSON no terminal
  reponexia graph . --out graph.json              salva JSON (UTF-8)
  reponexia graph . --format mermaid --out architecture.mmd
  reponexia explain . --dry-run                   gera .reponexia/{ONBOARDING.md,architecture.mmd,graph.json}
  reponexia graph . | jq '.edges'                 filtra com jq (se instalado)

Visualizar o Mermaid: https://mermaid.live ou extensão do VS Code.
Atenção (PowerShell 5.1): `>` grava UTF-16; prefira `--out`.
O graph.json contém só metadados (arquivos, símbolos, arestas, métricas), sem código.

## LLM

  reponexia explain . --model openai/gpt-4o-mini
  REPONEXIA_MODEL=... reponexia explain .
  --max-tokens N        teto de orçamento do run (estimativa)
  Cache em .reponexia/cache.json: rodar sem mudança = 0 chamadas.

Providers via litellm: OpenAI, Anthropic, Ollama, etc.
Configure a env do provider (ex.: OPENAI_API_KEY, ANTHROPIC_API_KEY).
Ollama local: --model ollama/qwen2.5-coder

## Configuração

  REPONEXIA_CORE      caminho do binário do motor
  REPONEXIA_MODEL     modelo padrão (usado quando --model não é passado)
  REPONEXIA_CONTRACT  caminho alternativo do graph.schema.json
  --out DIR           diretório de saída (padrão: <path>/.reponexia)

## Problemas comuns

  "reponexia-core não encontrado"
    -> pip install ./core  (ou cargo build --release em core/ e aponte REPONEXIA_CORE)

  "defina --model ou REPONEXIA_MODEL"
    -> passe --model ou use --dry-run

  "graph.json invalido ... schema"
    -> motor e orquestrador com versões diferentes; atualize os dois.

  Mermaid vazio
    -> não há dependências internas resolvidas; rode `reponexia map .` e veja `edges`.
