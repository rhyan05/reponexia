from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SymbolRef:
    name: str
    kind: str
    line: int
    file: str


@dataclass(frozen=True)
class ModuleContext:
    name: str
    files: tuple[str, ...]
    symbols: tuple[SymbolRef, ...]
    imports_out: tuple[str, ...]
    imports_in: tuple[str, ...]
    # Snippets já redigidos/esqueletizados; vazio no modo estrutural.
    snippets: tuple[str, ...] = ()


# Resumo do repositório é montado a partir dos resumos de módulo (hierárquico),
# por isso carrega os textos e não o código bruto.
@dataclass(frozen=True)
class RepoContext:
    name: str
    languages: tuple[str, ...]
    file_count: int
    module_summaries: tuple[str, ...]


class Summarizer(Protocol):
    def summarize_module(self, module: ModuleContext) -> str: ...

    def summarize_repo(self, ctx: RepoContext) -> str: ...
