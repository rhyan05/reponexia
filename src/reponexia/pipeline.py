from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .cache import cache_key
from .redact import redact
from .summarize.base import ModuleContext, RepoContext, Summarizer
from .summarize.context import build_module_contexts
from .summarize.skeleton import MAX_LINES_FOR_LLM, skeletonize

# Teto de linhas de um snippet enviado ao LLM (mesmo abaixo do limite de esqueleto).
MAX_SNIPPET_LINES = 200


def _symbols_by_file(graph: dict) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for symbol in graph.get("symbols", []):
        result.setdefault(symbol["file"], []).append(symbol)
    return result


# Lê o arquivo do disco, esqueletiza se for grande, fatia e redige segredos.
# O LLM nunca vê o repositório inteiro.
def _snippet(root: Path, path: str, symbols: list[dict]) -> str | None:
    try:
        text = (root / path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    if text.count("\n") + 1 > MAX_LINES_FOR_LLM:
        text = skeletonize(text, symbols)

    lines = text.splitlines()[:MAX_SNIPPET_LINES]
    return redact("\n".join(lines))


def attach_snippets(contexts: list[ModuleContext], graph: dict) -> list[ModuleContext]:
    root = Path(graph["root"])
    by_file = _symbols_by_file(graph)

    attached = []
    for ctx in contexts:
        snippets = []
        for path in ctx.files:
            snippet = _snippet(root, path, by_file.get(path, []))
            if snippet:
                snippets.append(f"# {path}\n{snippet}")
        attached.append(replace(ctx, snippets=tuple(snippets)))
    return attached


def _module_hash(graph: dict, files: tuple[str, ...]) -> str:
    hashes = {file["path"]: file.get("hash", "") for file in graph.get("files", [])}
    return cache_key(*[hashes.get(path, "") for path in files])


# Pipeline hierárquico: sumariza módulo a módulo e depois o repo a partir desses
# resumos. Cache por hash de módulo evita re-chamar o LLM sem mudança.
def build_narrative(
    graph: dict,
    summarizer: Summarizer,
    *,
    cache=None,
    verbose: bool = False,
) -> dict:
    contexts = attach_snippets(build_module_contexts(graph), graph)
    model = getattr(summarizer, "model", "")

    modules: dict[str, str] = {}
    for ctx in contexts:
        key = cache_key("module", model, _module_hash(graph, ctx.files))
        cached = cache.get(key) if cache else None
        if cached is not None:
            if verbose:
                print(f"[cache] modulo {ctx.name}")
            modules[ctx.name] = cached
            continue

        text = summarizer.summarize_module(ctx)
        modules[ctx.name] = text
        if cache is not None:
            cache.set(key, text)

    repo_context = RepoContext(
        name=Path(graph["root"]).name or graph["root"],
        languages=tuple(graph.get("languages", [])),
        file_count=len(graph.get("files", [])),
        module_summaries=tuple(
            f"## {name}\n{text}" for name, text in modules.items()
        ),
    )

    repo_key = cache_key("repo", model, graph.get("repo_hash", ""))
    cached_repo = cache.get(repo_key) if cache else None
    if cached_repo is None:
        cached_repo = summarizer.summarize_repo(repo_context)
        if cache is not None:
            cache.set(repo_key, cached_repo)

    return {"repo": cached_repo, "modules": modules}
