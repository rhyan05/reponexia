from __future__ import annotations

from collections import defaultdict

from ..modules import group_files_by_module
from .base import ModuleContext, SymbolRef


# Monta o contexto resumido por módulo a partir do grafo.
# Por quê: o LLM recebe resumo estrutural (símbolos/imports), nunca o código inteiro.
def build_module_contexts(graph: dict) -> list[ModuleContext]:
    files_by_module = group_files_by_module(graph.get("files", []))

    # Mapa arquivo -> módulo, para atribuir símbolos e arestas ao módulo certo.
    module_of_file = {
        file["path"]: name
        for name, members in files_by_module.items()
        for file in members
    }

    # Um balde por módulo. Sets evitam import duplicado (A importa B 2x).
    symbols_by_module: dict[str, list[SymbolRef]] = defaultdict(list)
    out_by_module: dict[str, set[str]] = defaultdict(set)
    in_by_module: dict[str, set[str]] = defaultdict(set)

    for symbol in graph.get("symbols", []):
        module = module_of_file.get(symbol["file"])
        if module is None:
            continue
        symbols_by_module[module].append(
            SymbolRef(
                name=symbol["name"],
                kind=symbol["kind"],
                line=symbol["line"],
                file=symbol["file"],
            )
        )

    for edge in graph.get("edges", []):
        source = module_of_file.get(edge["from"])
        target = module_of_file.get(edge["to"])
        # Import dentro do mesmo módulo não é dependência entre módulos.
        if source is None or target is None or source == target:
            continue
        out_by_module[source].add(target)
        in_by_module[target].add(source)

    return [
        ModuleContext(
            name=name,
            files=tuple(file["path"] for file in members),
            symbols=tuple(symbols_by_module[name]),
            imports_out=tuple(sorted(out_by_module[name])),
            imports_in=tuple(sorted(in_by_module[name])),
        )
        for name, members in sorted(files_by_module.items())
    ]
