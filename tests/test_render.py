from reponexia.render import render_markdown

GRAPH = {
    "schema_version": "1.0",
    "root": "/tmp/meu-repo",
    "repo_hash": "0123456789abcdef",
    "languages": ["python", "markdown"],
    "files": [
        {"path": "README.md", "language": "markdown", "loc": 2, "hash": "r", "parse_errors": []},
        {"path": "src/app/main.py", "language": "python", "loc": 10, "hash": "m", "parse_errors": []},
        {"path": "src/app/util.py", "language": "python", "loc": 5, "hash": "u", "parse_errors": []},
    ],
    "symbols": [
        {"id": "a", "file": "src/app/main.py", "name": "main", "kind": "function", "line": 1, "exported": True},
        {"id": "b", "file": "src/app/main.py", "name": "Helper", "kind": "class", "line": 5, "exported": False},
        {"id": "c", "file": "src/app/util.py", "name": "parse", "kind": "function", "line": 2, "exported": True},
    ],
    "edges": [
        {"from": "src/app/main.py", "to": "src/app/util.py", "kind": "import", "line": 3},
    ],
    "metrics": [
        {"path": "src/app/main.py", "fan_in": 0, "fan_out": 1, "page_rank": 0.7},
        {"path": "src/app/util.py", "fan_in": 1, "fan_out": 0, "page_rank": 0.2},
        {"path": "README.md", "fan_in": 0, "fan_out": 0, "page_rank": 0.1},
    ],
    "entry_points": [
        {"path": "src/app/main.py", "kind": "main", "evidence": "guard if __name__ == '__main__'"},
    ],
    "warnings": [
        {"path": "src/app/util.py", "message": "import nao resolvido"},
        {"message": "aviso global"},
    ],
}


def test_cabecalho_e_resumo():
    text = render_markdown(GRAPH)
    assert "# Onboarding: meu-repo" in text
    assert "repo_hash: 0123456789ab" in text
    assert "linguagens: python, markdown" in text


def test_entry_point_com_evidencia():
    text = render_markdown(GRAPH)
    assert "| `src/app/main.py` | main |" in text
    assert "guard if __name__" in text


def test_top_files_ordenados_por_page_rank():
    text = render_markdown(GRAPH)
    section = text.split("## Arquivos centrais")[1].split("## Módulos")[0]
    assert section.index("src/app/main.py") < section.index("src/app/util.py")
    assert section.index("src/app/util.py") < section.index("README.md")


def test_modulos_agrupados_por_diretorio():
    text = render_markdown(GRAPH)
    assert "### `src/app` (2 arquivos, 3 símbolos)" in text
    assert "### `(raiz)` (1 arquivo, 0 símbolos)" in text


def test_dependencias_e_avisos():
    text = render_markdown(GRAPH)
    assert "- linha 3 → `src/app/util.py`" in text
    assert "- `src/app/util.py`: import nao resolvido" in text
    assert "- aviso global" in text


def test_grafo_minimo_nao_quebra():
    minimal = {
        "schema_version": "1.0",
        "root": "/tmp/repo",
        "files": [
            {"path": "a.py", "language": "python", "loc": 1, "hash": "x", "parse_errors": []}
        ],
    }
    text = render_markdown(minimal)
    assert "# Onboarding: repo" in text
    assert "## Módulos" in text
    assert "## Entry points" not in text


def test_saida_deterministica():
    assert render_markdown(GRAPH) == render_markdown(GRAPH)
