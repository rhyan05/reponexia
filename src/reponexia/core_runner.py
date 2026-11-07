from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from .contract import validate


class CoreNotFound(RuntimeError):
    pass


def find_core() -> Path:
    override = os.environ.get("REPONEXIA_CORE")
    if override:
        return Path(override)

    exe = "reponexia-core.exe" if os.name == "nt" else "reponexia-core"

    on_path = shutil.which(exe)
    if on_path:
        return Path(on_path)

    root = Path(__file__).resolve().parents[2]
    for profile in ("release", "debug"):
        candidate = root / "core" / "target" / profile / exe
        if candidate.exists():
            return candidate

    raise CoreNotFound(
        "reponexia-core não encontrado. Rode `cargo build --release` em core/ "
        "ou defina a variável REPONEXIA_CORE."
    )

# Faz a indexação do path usando o core e retorna o grafo resultante
def index(path: str | Path) -> dict:
    core = find_core()
    proc = subprocess.run(
        [str(core), "index", str(path)],
        capture_output=True,
        check=True,
    )
    stdout = proc.stdout.decode("utf-8", errors="replace")
    graph = json.loads(stdout)

    # Valida o grafo retornado pelo core contra o contrato
    validate(graph)
    return graph
