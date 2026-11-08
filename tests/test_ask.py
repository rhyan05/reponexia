from reponexia.ask import build_context


def test_contexto_inclui_arquivos_simbolos_e_dependencias():
    graph = {
        "files": [{"path": "pkg/main.py"}],
        "languages": ["python"],
        "entry_points": [{"path": "pkg/main.py", "kind": "main", "evidence": "pkg/main.py:3"}],
        "metrics": [{"path": "pkg/main.py", "fan_in": 0, "fan_out": 1, "page_rank": 0.9}],
        "symbols": [
            {"name": "main", "file": "pkg/main.py", "kind": "function", "line": 3}
        ],
        "edges": [{"from": "pkg/main.py", "to": "pkg/util.py", "kind": "import", "line": 1}],
    }

    text = build_context(graph)

    assert "pkg/main.py" in text
    assert "main@pkg/main.py:3" in text
    assert "pkg/main.py -> pkg/util.py" in text
