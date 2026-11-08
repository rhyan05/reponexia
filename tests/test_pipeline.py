from reponexia.cache import Cache
from reponexia.pipeline import build_narrative


class FakeSummarizer:
    model = "fake"

    def __init__(self):
        self.module_calls = []
        self.contexts = []

    def summarize_module(self, module):
        self.module_calls.append(module.name)
        self.contexts.append(module)
        return f"resumo de {module.name}"

    def summarize_repo(self, ctx):
        return "visao do repo"


def make_graph(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "a.py").write_text(
        "import os\nTOKEN = 'AKIAIOSFODNN7EXAMPLE'\n", encoding="utf-8"
    )
    return {
        "schema_version": "1.0",
        "root": str(tmp_path),
        "repo_hash": "h",
        "languages": ["python"],
        "files": [
            {"path": "pkg/a.py", "language": "python", "loc": 2, "hash": "aa", "parse_errors": []}
        ],
        "symbols": [
            {"id": "x", "file": "pkg/a.py", "name": "main", "kind": "function", "line": 2, "exported": True}
        ],
        "edges": [],
        "metrics": [],
        "entry_points": [],
        "warnings": [],
    }


def test_narrativa_hierarquica_e_redacao(tmp_path):
    graph = make_graph(tmp_path)
    fake = FakeSummarizer()

    narrative = build_narrative(graph, fake, cache=Cache(tmp_path / "cache.json"))

    assert narrative == {"repo": "visao do repo", "modules": {"pkg": "resumo de pkg"}}
    snippet = fake.contexts[0].snippets[0]
    assert "AKIA" not in snippet
    assert "[REDACTED]" in snippet


def test_cache_evita_segunda_chamada(tmp_path):
    graph = make_graph(tmp_path)
    cache = Cache(tmp_path / "cache.json")
    fake = FakeSummarizer()

    build_narrative(graph, fake, cache=cache)
    assert fake.module_calls == ["pkg"]

    build_narrative(graph, fake, cache=cache)
    assert fake.module_calls == ["pkg"]  # não chamou de novo
