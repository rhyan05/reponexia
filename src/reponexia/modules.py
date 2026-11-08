from __future__ import annotations

from collections import defaultdict
from pathlib import PurePosixPath


# Modulo = pai do arquivo, ou "(raiz)" se o arquivo estiver na raiz
def module_of(path: str) -> str:
    # Retorna o módulo pai do arquivo, ou "(raiz)" se o arquivo estiver na raiz
    parent = str(PurePosixPath(path).parent)
    return "(raiz)" if parent == "." else parent

# Agrupa os arquivos por módulo, retornando um dicionário {modulo: [arquivos]}
def group_files_by_module(files: list[dict]) -> dict[str,list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for file in files:
        groups[module_of(file["path"])].append(file)
    return {
        name: sorted(members, key=lambda f: f["path"])
        for name, members in groups.items()
    }
