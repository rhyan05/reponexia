# Onboarding: ProjetoNet

- schema: 1.0
- repo_hash: 98098d2dc96a
- linguagens: python, rust, unknown
- arquivos: 46
- símbolos: 102
- dependências internas: 37
- entry points: 2

## Entry points

| path | kind | evidência |
|---|---|---|
| `src/reponexia/__main__.py` | package_main | `src/reponexia/__main__.py:1` |
| `src/reponexia/cli.py` | console_script | `pyproject.toml:13` |

## Arquivos centrais

| path | fan_in | fan_out | page_rank |
|---|---|---|---|
| `src/reponexia/summarize/base.py` | 5 | 0 | 0.086075 |
| `src/reponexia/render/__init__.py` | 4 | 2 | 0.056759 |
| `src/reponexia/contract.py` | 3 | 0 | 0.052473 |
| `src/reponexia/cache.py` | 4 | 0 | 0.040833 |
| `src/reponexia/render/markdown.py` | 1 | 0 | 0.039803 |
| `src/reponexia/render/mermaid.py` | 1 | 0 | 0.039803 |
| `src/reponexia/summarize/litellm_impl.py` | 3 | 1 | 0.037919 |
| `src/reponexia/cli.py` | 2 | 7 | 0.032254 |
| `src/reponexia/redact.py` | 2 | 0 | 0.030392 |
| `src/reponexia/summarize/context.py` | 2 | 2 | 0.030392 |

## Módulos

### `(raiz)` (2 arquivos, 0 símbolos)
- `README.md` — 14 linhas
- `pyproject.toml` — 20 linhas

### `contract` (1 arquivo, 0 símbolos)
- `contract/graph.schema.json` — 119 linhas

### `core` (2 arquivos, 0 símbolos)
- `core/Cargo.lock` — 642 linhas
- `core/Cargo.toml` — 21 linhas

### `core/src` (7 arquivos, 0 símbolos)
- `core/src/analyze.rs` — 128 linhas
- `core/src/entrypoints.rs` — 229 linhas
- `core/src/main.rs` — 300 linhas
- `core/src/models.rs` — 67 linhas
- `core/src/parse.rs` — 297 linhas
- `core/src/resolve.rs` — 321 linhas
- `core/src/scan.rs` — 20 linhas

### `core/tests` (1 arquivo, 0 símbolos)
- `core/tests/determinism.rs` — 44 linhas

### `core/tests/fixtures/broken` (2 arquivos, 0 símbolos)
- `core/tests/fixtures/broken/a_bad.py` — 2 linhas
- `core/tests/fixtures/broken/z_bad.py` — 2 linhas

### `docs` (2 arquivos, 0 símbolos)
- `docs/DESIGN.md` — 374 linhas
- `docs/IMPLEMENTATION.md` — 64 linhas

### `src/reponexia` (10 arquivos, 27 símbolos)
- `src/reponexia/__init__.py` — 2 linhas
- `src/reponexia/__main__.py` — 6 linhas
- `src/reponexia/ask.py` — 51 linhas
- `src/reponexia/cache.py` — 41 linhas
- `src/reponexia/cli.py` — 155 linhas
- `src/reponexia/contract.py` — 44 linhas
- `src/reponexia/core_runner.py` — 52 linhas
- `src/reponexia/modules.py` — 22 linhas
- `src/reponexia/pipeline.py` — 102 linhas
- `src/reponexia/redact.py` — 29 linhas

### `src/reponexia/render` (3 arquivos, 10 símbolos)
- `src/reponexia/render/__init__.py` — 5 linhas
- `src/reponexia/render/markdown.py` — 144 linhas
- `src/reponexia/render/mermaid.py` — 45 linhas

### `src/reponexia/summarize` (5 arquivos, 19 símbolos)
- `src/reponexia/summarize/__init__.py` — 4 linhas
- `src/reponexia/summarize/base.py` — 40 linhas
- `src/reponexia/summarize/context.py` — 58 linhas
- `src/reponexia/summarize/litellm_impl.py` — 113 linhas
- `src/reponexia/summarize/skeleton.py` — 29 linhas

### `tests` (11 arquivos, 46 símbolos)
- `tests/test_ask.py` — 21 linhas
- `tests/test_cache.py` — 27 linhas
- `tests/test_cli.py` — 74 linhas
- `tests/test_context.py` — 56 linhas
- `tests/test_contract.py` — 41 linhas
- `tests/test_litellm.py` — 90 linhas
- `tests/test_mermaid.py` — 68 linhas
- `tests/test_pipeline.py` — 66 linhas
- `tests/test_redact.py` — 43 linhas
- `tests/test_render.py` — 85 linhas
- `tests/test_skeleton.py` — 22 linhas

## Dependências internas

### `src/reponexia/__main__.py`
- linha 3 → `src/reponexia/cli.py`

### `src/reponexia/ask.py`
- linha 3 → `src/reponexia/render/__init__.py`
- linha 4 → `src/reponexia/summarize/litellm_impl.py`

### `src/reponexia/cli.py`
- linha 9 → `src/reponexia/ask.py`
- linha 10 → `src/reponexia/cache.py`
- linha 11 → `src/reponexia/contract.py`
- linha 12 → `src/reponexia/core_runner.py`
- linha 13 → `src/reponexia/pipeline.py`
- linha 14 → `src/reponexia/render/__init__.py`
- linha 15 → `src/reponexia/summarize/litellm_impl.py`
- linha 16 → `src/reponexia/summarize/litellm_impl.py`

### `src/reponexia/core_runner.py`
- linha 9 → `src/reponexia/contract.py`

### `src/reponexia/pipeline.py`
- linha 6 → `src/reponexia/cache.py`
- linha 7 → `src/reponexia/redact.py`
- linha 8 → `src/reponexia/summarize/base.py`
- linha 9 → `src/reponexia/summarize/context.py`
- linha 10 → `src/reponexia/summarize/skeleton.py`

### `src/reponexia/render/__init__.py`
- linha 1 → `src/reponexia/render/markdown.py`
- linha 2 → `src/reponexia/render/mermaid.py`

### `src/reponexia/summarize/__init__.py`
- linha 1 → `src/reponexia/summarize/base.py`

### `src/reponexia/summarize/context.py`
- linha 5 → `src/reponexia/modules.py`
- linha 6 → `src/reponexia/summarize/base.py`

### `src/reponexia/summarize/litellm_impl.py`
- linha 6 → `src/reponexia/summarize/base.py`

### `tests/test_ask.py`
- linha 1 → `src/reponexia/ask.py`

### `tests/test_cache.py`
- linha 1 → `src/reponexia/cache.py`

### `tests/test_cli.py`
- linha 1 → `src/reponexia/cli.py`
- linha 2 → `src/reponexia/core_runner.py`

### `tests/test_context.py`
- linha 1 → `src/reponexia/summarize/context.py`

### `tests/test_contract.py`
- linha 5 → `src/reponexia/contract.py`

### `tests/test_litellm.py`
- linha 3 → `src/reponexia/summarize/base.py`
- linha 4 → `src/reponexia/summarize/litellm_impl.py`

### `tests/test_mermaid.py`
- linha 1 → `src/reponexia/render/__init__.py`

### `tests/test_pipeline.py`
- linha 1 → `src/reponexia/cache.py`
- linha 2 → `src/reponexia/pipeline.py`

### `tests/test_redact.py`
- linha 3 → `src/reponexia/redact.py`

### `tests/test_render.py`
- linha 1 → `src/reponexia/render/__init__.py`

### `tests/test_skeleton.py`
- linha 1 → `src/reponexia/summarize/skeleton.py`

## Avisos
- `core/tests/fixtures/broken/a_bad.py`: erro de sintaxe no arquivo
- `core/tests/fixtures/broken/z_bad.py`: erro de sintaxe no arquivo
