from reponexia.render import render_mermaid

# Grafo de exemplo com entry point e import repetido
GRAPH = {
    "schema_version": "1.0",
    "root": "/tmp/repo",
    "files": [],
    "edges": [
        {"from": "src/app/main.py", "to": "src/app/util.py", "kind": "import", "line": 3},
        {"from": "src/app/main.py", "to": "src/app/util.py", "kind": "import", "line": 5},
    ],
    "entry_points": [
        {"path": "src/app/main.py", "kind": "main", "evidence": "main.py:1"},
    ],
}


# Testa a estrutura básica: direção, entry point em estádio e nó comum
def test_estrutura_do_grafo():
    text = render_mermaid(GRAPH)
    assert text.startswith("graph LR\n")
    assert 'n0(["src/app/main.py"])' in text
    assert 'n1["src/app/util.py"]' in text
    assert "n0 --> n1" in text


# Testa se arestas repetidas entre o mesmo par viram uma única seta
def test_arestas_deduplicadas():
    text = render_mermaid(GRAPH)
    assert text.count("-->") == 1


# Testa se um grafo sem arestas nem entry points gera um Mermaid válido e vazio
def test_grafo_vazio():
    text = render_mermaid({"schema_version": "1.0", "root": "/tmp/r", "files": []})
    assert text.startswith("graph LR\n")
    assert "nenhuma dependencia interna" in text


# Testa se a saída é determinística
def test_saida_deterministica():
    assert render_mermaid(GRAPH) == render_mermaid(GRAPH)

def test_top_n_por_page_rank_preserva_entry_points():
    graph = {
        "files": [],
        "edges": [
            {"from": "a.py", "to": "b.py", "kind": "import", "line": 1},
            {"from": "c.py", "to": "b.py", "kind": "import", "line": 1},
            {"from": "b.py", "to": "d.py", "kind": "import", "line": 1},
        ],
        "entry_points": [
            {"path": "d.py", "kind": "main", "evidence": "d.py:1"},
        ],
        "metrics": [
            {"path": "a.py", "fan_in": 0, "fan_out": 1, "page_rank": 0.1},
            {"path": "b.py", "fan_in": 2, "fan_out": 1, "page_rank": 0.5},
            {"path": "c.py", "fan_in": 0, "fan_out": 1, "page_rank": 0.2},
            {"path": "d.py", "fan_in": 1, "fan_out": 0, "page_rank": 0.2},
        ],
    }

    text = render_mermaid(graph, top_n=1)

    assert "b.py" in text and "d.py" in text
    assert "a.py" not in text
    assert "c.py" not in text
