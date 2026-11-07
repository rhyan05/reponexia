from __future__ import annotations

from collections import defaultdict
from pathlib import PurePosixPath

TOP_FILES = 10


def render_markdown(graph: dict) -> str:
    sections = [
        _header(graph),
        _entry_points(graph),
        _top_files(graph),
        _modules(graph),
        _dependencies(graph),
        _warnings(graph),
    ]
    return "\n\n".join(section for section in sections if section) + "\n"


def _header(graph: dict) -> str:
    name = PurePosixPath(graph["root"]).name or graph["root"]
    languages = ", ".join(graph.get("languages", [])) or "nenhuma"

    lines = [f"# Onboarding: {name}", ""]
    lines.append(f"- schema: {graph['schema_version']}")
    if graph.get("repo_hash"):
        lines.append(f"- repo_hash: {graph['repo_hash'][:12]}")
    lines.append(f"- linguagens: {languages}")
    lines.append(f"- arquivos: {len(graph.get('files', []))}")
    lines.append(f"- símbolos: {len(graph.get('symbols', []))}")
    lines.append(f"- dependências internas: {len(graph.get('edges', []))}")
    lines.append(f"- entry points: {len(graph.get('entry_points', []))}")
    return "\n".join(lines)


def _entry_points(graph: dict) -> str:
    entries = graph.get("entry_points", [])
    if not entries:
        return ""

    lines = ["## Entry points", "", "| path | kind | evidência |", "|---|---|---|"]
    for entry in sorted(entries, key=lambda item: (item["path"], item["kind"])):
        lines.append(
            f"| `{entry['path']}` | {entry['kind']} | `{entry['evidence']}` |"
        )
    return "\n".join(lines)


def _top_files(graph: dict) -> str:
    metrics = graph.get("metrics", [])
    if not metrics:
        return ""

    top = sorted(metrics, key=lambda item: (-item["page_rank"], item["path"]))[:TOP_FILES]

    lines = [
        "## Arquivos centrais",
        "",
        "| path | fan_in | fan_out | page_rank |",
        "|---|---|---|---|",
    ]
    for metric in top:
        lines.append(
            f"| `{metric['path']}` | {metric['fan_in']} | {metric['fan_out']} | "
            f"{metric['page_rank']:.6f} |"
        )
    return "\n".join(lines)


def _modules(graph: dict) -> str:
    files = graph.get("files", [])
    if not files:
        return ""

    symbols_by_file: dict[str, int] = defaultdict(int)
    for symbol in graph.get("symbols", []):
        symbols_by_file[symbol["file"]] += 1

    groups: dict[str, list[dict]] = defaultdict(list)
    for file in files:
        parent = str(PurePosixPath(file["path"]).parent)
        groups["(raiz)" if parent == "." else parent].append(file)

    lines = ["## Módulos"]
    for module in sorted(groups):
        members = sorted(groups[module], key=lambda item: item["path"])
        total_symbols = sum(symbols_by_file[file["path"]] for file in members)
        lines.append("")
        lines.append(
            f"### `{module}` ({_count(len(members), 'arquivo', 'arquivos')}, "
            f"{_count(total_symbols, 'símbolo', 'símbolos')})"
        )
        for file in members:
            lines.append(f"- `{file['path']}` — {file['loc']} linhas")
    return "\n".join(lines)


def _count(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _dependencies(graph: dict) -> str:
    edges = graph.get("edges", [])
    if not edges:
        return ""

    by_source: dict[str, list[dict]] = defaultdict(list)
    for edge in edges:
        by_source[edge["from"]].append(edge)

    lines = ["## Dependências internas"]
    for source in sorted(by_source):
        lines.append("")
        lines.append(f"### `{source}`")
        for edge in sorted(by_source[source], key=lambda item: (item["to"], item["line"])):
            lines.append(f"- linha {edge['line']} → `{edge['to']}`")
    return "\n".join(lines)


def _warnings(graph: dict) -> str:
    warnings = graph.get("warnings", [])
    if not warnings:
        return ""

    lines = ["## Avisos"]
    for warning in warnings:
        path = warning.get("path")
        where = f"`{path}`: " if path else ""
        lines.append(f"- {where}{warning['message']}")
    return "\n".join(lines)
