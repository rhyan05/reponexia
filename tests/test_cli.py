import reponexia.cli as cli
from reponexia.core_runner import CoreNotFound

# Grafo mínimo usado nos testes, sem depender do core Rust
GRAPH = {
    "schema_version": "1.0",
    "root": "/tmp/repo",
    "files": [
        {
            "path": "main.py",
            "language": "python",
            "loc": 3,
            "hash": "x",
            "parse_errors": [],
        }
    ],
}


# Testa se o dry-run cria o ONBOARDING.md dentro do repositório analisado
def test_explain_dry_run_grava_onboarding(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "index", lambda path: GRAPH)
    target = tmp_path / "repo"
    target.mkdir()

    code = cli.main(["explain", str(target), "--dry-run"])

    assert code == 0
    out = target / ".reponexia" / "ONBOARDING.md"
    assert out.exists()
    assert out.read_text(encoding="utf-8").startswith("# Onboarding: repo")
    assert b"\r\n" not in out.read_bytes()


# Testa se o comando sem --dry-run falha sem tocar no core nem criar a pasta
def test_explain_sem_dry_run_falha(tmp_path, monkeypatch):
    chamou = False

    def fake_index(path):
        nonlocal chamou
        chamou = True
        return GRAPH

    monkeypatch.setattr(cli, "index", fake_index)
    target = tmp_path / "repo"
    target.mkdir()

    code = cli.main(["explain", str(target)])

    assert code == 1
    assert chamou is False
    assert not (target / ".reponexia").exists()


# Testa se um erro do core vira exit code 1, sem traceback
def test_explain_core_ausente(tmp_path, monkeypatch):
    def fake_index(path):
        raise CoreNotFound("core nao encontrado")

    monkeypatch.setattr(cli, "index", fake_index)
    target = tmp_path / "repo"
    target.mkdir()

    code = cli.main(["explain", str(target), "--dry-run"])

    assert code == 1
    assert not (target / ".reponexia").exists()
