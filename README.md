# RepoNexia

CLI que explica um repositório desconhecido: mapeia arquitetura, entry points e
dependências críticas, e gera um onboarding doc.

Motor em Rust (`reponexia-core`) faz o scan/parse e monta o grafo; o orquestrador
em Python chama o LLM e renderiza a documentação. A fronteira é um JSON
versionado (`src/reponexia/graph.schema.json`).

## Build e instalação

**Via PyPI** (após o release):
```bash
pip install reponexia
pip install "reponexia[llm]"      # LLM real (litellm)
```

**A partir do código-fonte** (clone):
```bash
python -m venv .venv
# .venv\Scripts\Activate.ps1  (Windows) | source .venv/bin/activate (Unix)

pip install -e .                  # usa o wheel publicado do core (sem Rust)
# ou, para compilar/testar o core local:
pip install ./core
pip install -e ".[llm]"
```

O Python descobre o binário nesta ordem: `REPONEXIA_CORE` → `Scripts/bin` do
ambiente → `PATH` → `core/target/{release,debug}`.

## Uso

```bash
reponexia guia                           # guia de uso no terminal
reponexia map <path>                     # só o core; imprime o graph.json
reponexia graph <path> --format mermaid  # exporta o grafo (json|mermaid)
reponexia explain <path> --dry-run       # esqueleto estrutural, sem LLM
reponexia explain <path> --model openai/gpt-4o-mini
reponexia ask <path> "onde fica a autenticação?"
```

O mesmo guia está em [`docs/USAGE.md`](docs/USAGE.md) (gerado por
`reponexia guia --markdown`).

No modo real o modelo vem de `--model` ou `REPONEXIA_MODEL`. `--max-tokens`
limita o orçamento; sem mudança no repo, o cache evita novas chamadas LLM.

Saída padrão em `<path>/.reponexia/`: `graph.json`, `ONBOARDING.md` e
`architecture.mmd` (`--out` sobrescreve o diretório).

Exemplo de saída: [`examples/ONBOARDING.md`](examples/ONBOARDING.md).

## Segurança

Antes de qualquer chamada LLM, snippets passam por `redact.py` (AWS, OpenAI,
GitHub, Slack, chave privada e connection strings). O scan ignora `.gitignore`,
dotfiles e `.reponexia`.

## Testes

```bash
cargo test --manifest-path core/Cargo.toml
pytest
```
