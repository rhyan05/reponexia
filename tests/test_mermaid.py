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
