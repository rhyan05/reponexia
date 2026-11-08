import os

import reponexia.core_runner as cr


def _exe_name() -> str:
    return "reponexia-core.exe" if os.name == "nt" else "reponexia-core"


def test_override_por_variavel_de_ambiente(monkeypatch, tmp_path):
    exe = tmp_path / _exe_name()
    exe.write_text("", encoding="utf-8")
    monkeypatch.setenv("REPONEXIA_CORE", str(exe))

    assert cr.find_core() == exe


def test_acha_binario_junto_do_python(monkeypatch, tmp_path):
    python = tmp_path / ("python.exe" if os.name == "nt" else "python")
    python.write_text("", encoding="utf-8")
    exe = tmp_path / _exe_name()
    exe.write_text("", encoding="utf-8")

    monkeypatch.delenv("REPONEXIA_CORE", raising=False)
    monkeypatch.setattr(cr.sys, "executable", str(python))

    assert cr.find_core() == exe
