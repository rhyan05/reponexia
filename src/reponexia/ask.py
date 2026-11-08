from __future__ import annotations

from .render import render_markdown, render_mermaid
from .summarize.litellm_impl import LiteLLMSummarizer


# Contexto compacto do grafo para responder perguntas sem mandar código bruto.
def build_context(graph: dict) -> str:
    lines = [f"Repositorio com {len(graph.get('files', []))} arquivos."]
    languages = ", ".join(graph.get("languages", [])) or "nenhuma"
    lines.append(f"Linguagens: {languages}")

    entries = graph.get("entry_points", [])
    if entries:
        lines.append("Entry points: " + ", ".join(e["path"] for e in entries))

    metrics = sorted(
        graph.get("metrics", []), key=lambda m: (-m["page_rank"], m["path"])
    )[:10]
    if metrics:
        lines.append(
            "Arquivos centrais: "
            + ", ".join(f"{m['path']} (rank {m['page_rank']})" for m in metrics)
        )

    symbols = graph.get("symbols", [])[:50]
    if symbols:
        lines.append(
            "Simbolos: "
            + ", ".join(f"{s['name']}@{s['file']}:{s['line']}" for s in symbols)
        )

    edges = graph.get("edges", [])[:50]
    if edges:
        lines.append(
            "Dependencias: "
            + "; ".join(f"{e['from']} -> {e['to']}" for e in edges)
        )

    return "\n".join(lines)


def ask(graph: dict, question: str, model: str, *, max_tokens: int = 1_000_000) -> str:
    summarizer = LiteLLMSummarizer(model, max_tokens=max_tokens)
    prompt = (
        f"Contexto do repositorio:\n{build_context(graph)}\n\n"
        f"Pergunta: {question}\n\n"
        "Responda citando arquivo quando possivel. Nao invente fatos."
    )
    return summarizer._complete(prompt)
