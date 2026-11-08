from __future__ import annotations

# Evita espaguete: só os N arquivos mais centrais (PageRank) + entry points.
DEFAULT_TOP_N = 50


# Renderiza as dependências internas como um grafo Mermaid.
def render_mermaid(graph: dict, top_n: int = DEFAULT_TOP_N) -> str:
    edges = graph.get("edges", [])
    entry_points = {entry["path"] for entry in graph.get("entry_points", [])}

    # Nós = arquivos ligados por arestas + entry points.
    paths = {edge["from"] for edge in edges} | {edge["to"] for edge in edges}
    paths |= entry_points
    if not paths:
        return "graph LR\n    %% nenhuma dependencia interna detectada\n"

    # Filtro top-N por PageRank; entry points sempre ficam.
    metrics = graph.get("metrics", [])
    if metrics and top_n > 0:
        ranked = sorted(metrics, key=lambda m: (-m["page_rank"], m["path"]))
        keep = {m["path"] for m in ranked[:top_n]} | entry_points
        paths &= keep
        edges = [e for e in edges if e["from"] in paths and e["to"] in paths]
        if not paths:
            return "graph LR\n    %% nenhuma dependencia interna detectada\n"

    # IDs determinísticos: ordem alfabética, sem depender do path no nó.
    node_id = {path: f"n{index}" for index, path in enumerate(sorted(paths))}

    lines = ["graph LR"]
    for path in sorted(paths):
        # Entry points ganham formato de estádio para se destacarem.
        if path in entry_points:
            lines.append(f'    {node_id[path]}(["{path}"])')
        else:
            lines.append(f'    {node_id[path]}["{path}"]')

    # Uma seta por par origem/destino, em ordem estável.
    pairs = {(edge["from"], edge["to"]) for edge in edges}
    for source, target in sorted(pairs):
        lines.append(f"    {node_id[source]} --> {node_id[target]}")

    return "\n".join(lines) + "\n"
