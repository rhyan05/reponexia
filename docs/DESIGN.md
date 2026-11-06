# RepoNexia — Design

## 1. Visão geral

`reponexia explain <path>` analisa um repositório desconhecido e gera material de
onboarding: arquitetura, entry points, dependências críticas e um documento
narrativo explicando como o projeto funciona.

**Público:** quem entra num codebase legado, auditoria técnica, due diligence,
revisão de projetos de terceiros.

**Não-objetivos:** não é IDE, não roda o código analisado, não substitui code
review, não indexa em tempo real.

**Princípio central:** o motor estrutural (Rust) nunca chama LLM. O orquestrador
(Python) nunca parseia código. A fronteira é um JSON versionado.

> A ordem de implementação (commits e checkpoints) vive em
> [`IMPLEMENTATION.md`](./IMPLEMENTATION.md). Este documento define o **quê** e o
> **por quê**.

## 2. Arquitetura em dois processos

```
reponexia explain <path>
        │
        ▼
┌───────────────────────────────┐
│ Cérebro — Python (reponexia)  │
│ • CLI / config                │
│ • chama o core via subprocess │
│ • lê graph.json               │
│ • sumariza (LiteLLM+Strategy) │
│ • renderiza artefatos         │
└──────────────┬────────────────┘
               │ subprocess + JSON
               ▼
┌───────────────────────────────┐
│ Motor — Rust (reponexia-core) │
│ • scan + .gitignore           │
│ • parse tree-sitter (paralelo)│
│ • grafo de dependências       │
│ • métricas / entry points     │
│ • emite graph.json            │
└───────────────────────────────┘
```

### Por que processo separado e não FFI/PyO3

- Contrato explícito e testável isoladamente (schema JSON).
- O core é reutilizável por qualquer linguagem/consumidor.
- Sem `maturin`/PyO3 no MVP: menos build, menos acoplamento de versões.
- O JSON é cacheável e diffável; a análise estrutural vira artefato.

Custo aceito: um `subprocess` por execução. Irrelevante para um comando rodado
manualmente. Se um dia virar servidor/long-running, PyO3 pode substituir o
`subprocess` sem mudar o contrato.

## 3. Contrato `graph.json`

Arquivo versionado, formato estável. Campo `schema_version` no topo. O Python
recusa rodar com major diferente do esperado.

```jsonc
{
  "schema_version": "1.0",
  "root": "/abs/path",
  "generated_at": "2026-11-06T12:00:00Z",
  "repo_hash": "sha256:...",           // hash do hash de todos os arquivos
  "languages": ["python", "typescript"],
  "files": [
    {
      "path": "src/app/main.py",
      "language": "python",
      "loc": 120,
      "hash": "sha256:...",
      "parse_errors": []
    }
  ],
  "symbols": [
    {
      "id": "src/app/main.py::main",
      "file": "src/app/main.py",
      "name": "main",
      "kind": "function",        // function | class | method | const | module
      "line": 42,
      "exported": true
    }
  ],
  "edges": [
    {
      "from": "src/app/main.py",
      "to": "src/app/service.py",
      "kind": "import",          // import | call | extends | implements
      "symbol": "Service",       // opcional
      "line": 3
    }
  ],
  "metrics": [
    {
      "path": "src/app/service.py",
      "fan_in": 7,
      "fan_out": 3,
      "page_rank": 0.081
    }
  ],
  "entry_points": [
    {
      "path": "src/app/main.py",
      "kind": "console_script",  // main | bin | console_script | package_main
      "evidence": "pyproject.toml:18"
    }
  ],
  "modules": [
    {
      "name": "app",
      "root": "src/app",
      "files": ["src/app/main.py", "src/app/service.py"]
    }
  ],
  "warnings": [
    { "path": "vendor/x.js", "message": "no grammar for .jsx, skipped" }
  ]
}
```

Regras do contrato:

- **Determinístico:** ordenação estável de `files`, `symbols`, `edges`,
  `modules` para permitir diff e cache por hash.
- **Sem código-fonte:** só metadados estruturais. Snippets são lidos pelo Python
  diretamente do disco, somente quando necessário.
- **Tolerante a falha:** arquivo que não parseia entra em `warnings`, não
  aborta o run.
- `schema_version` segue semver; mudança de major quebra o Python de propósito.
- **`repo_hash` no topo:** hash do hash de todos os arquivos. Permite ao Python
  decidir em O(1) se precisa re-sumarizar o repositório inteiro.
- Paths normalizados para `/` antes de serializar, inclusive no Windows.

## 4. Motor Rust (`reponexia-core`)

### Responsabilidades

| Etapa       | O que faz                                                      |
|-------------|----------------------------------------------------------------|
| scan        | walk respeitando `.gitignore`, ignora binários e dirs de build |
| detect      | detecta linguagem por extensão                                 |
| parse       | tree-sitter por linguagem, extrai símbolos e imports           |
| graph       | monta nós/arestas, resolve imports para arquivos do repo       |
| analyze     | fan-in/out, PageRank, detecção de ciclos, clustering de módulos|
| entrypoints | detecta `main`, `__main__`, `bin`/`main` de manifests          |
| emit        | serializa `graph.json` (stdout ou `--out`)                     |

### Dependências previstas

- `tree-sitter` + grammars por **feature** do Cargo (`python`, `javascript`,
  `typescript`, `rust`, `go`, `java`) — só compila o que for habilitado.
- `ignore` — walk com semântica de gitignore.
- `rayon` — parse paralelo por arquivo.
- `serde`, `serde_json` — contrato.
- `clap` — CLI do binário.
- `petgraph` — grafo e PageRank.

### CLI do core

```
reponexia-core index <path> [--out graph.json] [--lang python,typescript] [--jobs N]
reponexia-core graph <path> [--format json|mermaid]
```

- Saída JSON em stdout quando `--out` não é dado.
- Métrica de performance no stderr (files/s, tempo por etapa) com `--verbose`.
- Exit codes: `0` ok, `1` erro de I/O, `2` path inválido, `3` erro interno.

### Performance e determinismo

Ordem de grandeza alvo: milhares de arquivos em poucos segundos; parse domina.
Paralelo por arquivo com `rayon`; merge determinístico no fim. Toda saída que
possa variar (paths, ordenação) é normalizada antes de serializar.

## 5. Cérebro Python (`reponexia`)

### Responsabilidades

- Localizar/executar o `reponexia-core` (ver §10).
- Ler e validar `graph.json`.
- Sumarizar hierarquicamente: arquivo → módulo → repositório.
- Renderizar `ONBOARDING.md`, `architecture.mmd` e copiar/referenciar `graph.json`.

### LLM: Strategy + LiteLLM

```python
class Summarizer(Protocol):
    def summarize_module(self, module: ModuleContext) -> str: ...
    def summarize_repo(self, ctx: RepoContext) -> str: ...
```

- Implementação única `LiteLLMSummarizer` sobre **litellm**, que já abstrai
  OpenAI, Anthropic, Ollama, etc. O Strategy existe para permitir implementação
  alternativa (mock em teste, sumarizador offline, provider exótico) — não para
  duplicar o roteamento que o litellm já faz.
- Provider/modelo por config: `--model openai/gpt-4o-mini`,
  `anthropic/claude-...`, `ollama/qwen2.5-coder`. Sem hardcode.
- `--dry-run`: roda só o core e gera o esqueleto estrutural do doc, **sem LLM**.
- `--max-tokens`: teto de orçamento; aborta/avisa antes de estourar.
- Retry com backoff; fallback de modelo opcional.

### Economia de contexto e anti-alucinação

- O LLM **nunca** recebe o repositório inteiro.
- Entrada = resumo estrutural do módulo (símbolos, imports, métricas) + poucos
  snippets selecionados (entry points, arquivos centrais por PageRank).
- Toda afirmação do onboarding deve citar `arquivo:linha` real, derivado do
  grafo — não inventado.
- Sumarização hierárquica: módulos primeiro, depois um resumo do todo a partir
  dos resumos (não do código bruto).

### Tratamento de arquivos grandes (context window)

- Arquivos acima de `MAX_LINES_FOR_LLM` (padrão 1500 linhas) não vão inteiros
  para o LLM. Antes, são "esqueletizados" pelo Python a partir do `graph.json`:
  mantém assinaturas de funções/classes e imports, omite corpos.
- Se ainda assim estourar, o arquivo é fatiado por intervalo de linhas e
  sumarizado em partes, depois concatenado.
- O `--verbose` mostra quantos arquivos foram esqueletizados/fatiados.

### Cache

Cache local por hash de conteúdo (do `graph.json` e da config do modelo). O
`repo_hash` permite decidir em O(1) se o repositório inteiro precisa ser
re-sumarizado. Rodar de novo sem mudança = zero chamadas LLM. Incremental por
módulo.

## 6. Segurança

- O scan do core ignora `.env`, chaves, credenciais, binários e dirs de build.
- Antes de qualquer chamada LLM: redaction (no Python, sobre os snippets lidos do
  disco) de padrões sensíveis, com regex configuráveis:
  - `AKIA[0-9A-Z]{16}` (AWS access key)
  - `sk-[A-Za-z0-9]{20,}` (chaves estilo OpenAI)
  - `ghp_[A-Za-z0-9]{36}` (GitHub token)
  - `xox[baprs]-...` (Slack)
  - `-----BEGIN .* PRIVATE KEY-----`
  - connection strings (`postgres://user:pass@...`)
- Nenhum segredo em log; `--verbose` nunca imprime conteúdo de `.env`.
- O core é read-only sobre o repo analisado.

## 7. Prior art

Não reinventar o que já existe:

- **aider repo-map** — tree-sitter + PageRank para ranking de arquivos; referência
  direta para o `analyze`.
- **universal-ctags** — extração de símbolos madura; útil como fallback/validação.
- **code2prompt / repomix** — empacotamento de contexto para LLM; referência para
  orçamento de tokens.
- **tree-sitter** grammars oficiais — base do parse.

Reusar conceitos e, onde fizer sentido, código/grammars; construir do zero só o
que é específico do RepoNexia (contrato JSON, sumarização hierárquica, render).

## 8. Superfície de CLI

Core (Rust):

```
reponexia-core index <path> [--out FILE] [--lang LIST] [--jobs N] [--verbose]
reponexia-core graph <path> [--format json|mermaid]
```

Python:

```
reponexia explain <path>      # pipeline completo → ONBOARDING.md + architecture.mmd + graph.json
reponexia map <path>          # só core, sem LLM; imprime/gera a estrutura
reponexia graph <path>        # delega ao core, exporta grafo
reponexia ask "<pergunta>"    # fase 2: Q&A sobre o índice
```

Flags comuns: `--out`, `--model`, `--max-tokens`, `--dry-run`, `--lang`,
`--include/--exclude`, `--verbose`.

## 9. Layout do repositório

Os artefatos vão para uma pasta de saída dedicada (padrão `.reponexia/`), para
não sujar a raiz do repositório analisado. `--out` sobrescreve.

```
ProjetoNet/
├── core/                      # workspace Rust
│   ├── Cargo.toml             # bin reponexia-core
│   └── src/
│       ├── main.rs            # clap + orquestração
│       ├── scan.rs            # walk + gitignore
│       ├── parse/             # tree-sitter por linguagem
│       ├── graph.rs           # nós/arestas + resolução de imports
│       ├── analyze.rs         # fan-in/PageRank/ciclos/módulos
│       └── model.rs           # tipos do contrato (serde)
├── src/reponexia/             # pacote Python
│   ├── cli.py                 # entry point
│   ├── core_runner.py         # encontra e chama o binário Rust
│   ├── contract.py            # carrega/valida graph.json
│   ├── summarize/             # Strategy + LiteLLM
│   │   ├── base.py            # Summarizer (Protocol)
│   │   ├── litellm_impl.py    # LiteLLMSummarizer
│   │   └── skeleton.py        # esqueletização de arquivos grandes
│   ├── redact.py              # redaction de segredos antes do LLM
│   ├── render/                # markdown + mermaid
│   └── cache.py
├── contract/graph.schema.json # schema do contrato
├── docs/
│   ├── DESIGN.md              # este documento
│   ├── IMPLEMENTATION.md      # trilha de commits/checkpoints
│   └── *_historico.md         # versões anteriores (arquivo)
├── examples/                  # ONBOARDING.md de exemplo p/ README
├── tests/                     # golden files do JSON + demo()
└── pyproject.toml
```

Saída padrão:

```
<repo>/
└── .reponexia/
    ├── graph.json
    ├── ONBOARDING.md
    └── architecture.mmd
```

## 10. Distribuição e descoberta do binário

MVP (build a partir do código):

1. `cargo build --release`
2. Python localiza o core nesta ordem: env `REPONEXIA_CORE` → `PATH` →
   `core/target/release/reponexia-core` (e `reponexia-core.exe` no Windows).
3. Erro claro se não encontrar, com instrução de build.

Notas de portabilidade (Windows):

- Sempre invocar `subprocess.run` com lista de argumentos, nunca `shell=True`.
- Capturar `stdout`/`stderr` como `bytes` e decodificar explicitamente com
  `utf-8` (`errors="replace"`), evitando problemas de encoding do console.
- Normalizar paths no JSON para `/` antes de serializar no Rust.

Depois: empacotar o binário por plataforma dentro do wheel (build via CI). Não
faz parte do MVP.

## 11. Roadmap

| Fase | Entrega |
|------|---------|
| **P0** | `contract/graph.schema.json` definido + esqueleto do workspace Rust + CLI `index` emitindo JSON mínimo |
| **P1** | scan + parse tree-sitter (Python/JS/TS) + grafo + análise + `graph.json` completo |
| **P2** | CLI Python: `core_runner`, validação do contrato, `explain --dry-run` |
| **P3** | `LiteLLMSummarizer` + sumarização hierárquica + render `ONBOARDING.md`/`architecture.mmd` |
| **P4** | cache por hash (`repo_hash`), incremental por módulo, controles de custo |
| **P5** | grammars extras (Rust/Go/Java), filtro top-N do Mermaid por PageRank, wheel com binário embutido, `ask` |

Detalhamento em commits: [`IMPLEMENTATION.md`](./IMPLEMENTATION.md).

## 12. Critérios de aceite

- `reponexia explain <repo OSS conhecido>` gera `.reponexia/ONBOARDING.md`,
  `.reponexia/architecture.mmd` e `.reponexia/graph.json`.
- `graph.json` valida contra `contract/graph.schema.json`.
- Toda referência `arquivo:linha` no onboarding existe no repositório.
- `reponexia explain --dry-run` produz o esqueleto sem uma única chamada LLM.
- O core é determinístico: rodar duas vezes no mesmo commit produz JSON
  idêntico — coberto por teste automatizado, não só por checkpoint manual.
- Um `test_*.py`/`demo()` cobre a montagem do grafo e a validação do contrato.
- Nenhum snippet enviado ao LLM contém padrão de segredo detectável pela
  `redact.py` (teste unitário cobrindo os regex).
