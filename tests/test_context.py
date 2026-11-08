from reponexia.summarize.context import build_module_contexts

# Grafo com dois módulos com dependência entre eles e um import intra-módulo
# (que deve ser ignorado) + um arquivo na raiz.
GRAPH = {
    "files": [
        {"path": "README.md", "language": "markdown", "loc": 2},
        {"path": "src/app/main.py", "language": "python", "loc": 10},
        {"path": "src/app/util.py", "language": "python", "loc": 5},
        {"path": "src/core/db.py", "language": "python", "loc": 8},
    ],
    "symbols": [
        {"file": "src/app/main.py", "name": "main", "kind": "function", "line": 10},
        {"file": "src/app/util.py", "name": "soma", "kind": "function", "line": 1},
        {"file": "src/app/util.py", "name": "sub", "kind": "function", "line": 5},
    ],
    "edges": [
        {"from": "src/app/main.py", "to": "src/app/util.py", "kind": "import", "line": 3},
        {"from": "src/app/main.py", "to": "src/core/db.py", "kind": "import", "line": 4},
        {"from": "src/app/util.py", "to": "src/app/main.py", "kind": "import", "line": 2},
    ],
}


def context(contexts, name):
    return next(c for c in contexts if c.name == name)


def test_um_contexto_por_modulo_em_ordem():
    contexts = build_module_contexts(GRAPH)
    assert [c.name for c in contexts] == ["(raiz)", "src/app", "src/core"]


def test_arquivos_e_simbolos_do_modulo():
    app = context(build_module_contexts(GRAPH), "src/app")
    assert app.files == ("src/app/main.py", "src/app/util.py")
    assert [(s.name, s.line) for s in app.symbols] == [("main", 10), ("soma", 1), ("sub", 5)]


def test_imports_entre_modulos_e_self_import_ignorado():
    contexts = build_module_contexts(GRAPH)
    app = context(contexts, "src/app")
    core = context(contexts, "src/core")

    # main -> core.db é o único import entre módulos diferentes.
    assert app.imports_out == ("src/core",)
    assert core.imports_in == ("src/app",)
    # main <- util é intra-módulo e não deve contar.
    assert app.imports_in == ()


def test_modulo_sem_simbolos_nao_quebra():
    raiz = context(build_module_contexts(GRAPH), "(raiz)")
    assert raiz.files == ("README.md",)
    assert raiz.symbols == ()
