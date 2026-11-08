import reponexia.cli as cli
from reponexia.guide import ORDER, render


def test_guia_completo(capsys):
    assert cli.main(["guia"]) == 0
    out = capsys.readouterr().out
    assert "reponexia map" in out
    assert "pip install reponexia" in out


def test_guia_topico(capsys):
    assert cli.main(["guia", "graph"]) == 0
    assert "mermaid" in capsys.readouterr().out


def test_topico_desconhecido(capsys):
    assert cli.main(["guia", "naoexiste"]) == 1
    err = capsys.readouterr().err
    assert "desconhecido" in err
    assert "instalacao" in err


def test_todos_os_topicos_renderizam():
    for key in ORDER:
        assert render(key).strip()


def test_markdown_tem_titulo():
    assert render(markdown=True).startswith("# RepoNexia")
