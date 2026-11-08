from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .ask import ask
from .cache import Cache
from .contract import ContractError
from .core_runner import CoreNotFound, index
from .guide import ORDER, render as render_guide
from .pipeline import build_narrative
from .render import render_markdown, render_mermaid
from .summarize.litellm_impl import (
    BudgetExceeded,
    LiteLLMSummarizer,
    SummarizerError,
)


def _model_from(args) -> str | None:
    # Sem hardcode de provider: flag ou variável de ambiente.
    return args.model or os.environ.get("REPONEXIA_MODEL")


def _write(path: Path, text: str) -> None:
    # UTF-8 + LF fixo para o artefato ser idêntico em qualquer SO.
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(text)


def _json(graph: dict) -> str:
    return json.dumps(graph, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(prog="reponexia")
    sub = parser.add_subparsers(dest="command", required=True)

    guia_cmd = sub.add_parser("guia", help="Guia de uso no terminal")
    guia_cmd.add_argument(
        "topico",
        nargs="?",
        help="instalacao | comandos | graph | llm | config | problemas",
    )
    guia_cmd.add_argument(
        "--markdown", action="store_true", help="emite markdown (para docs/USAGE.md)"
    )

    map_cmd = sub.add_parser("map", help="Mostra a estrutura do repositório (sem LLM)")
    map_cmd.add_argument("path")

    explain_cmd = sub.add_parser(
        "explain", help="Gera o onboarding do repositório (--dry-run = sem LLM)"
    )
    explain_cmd.add_argument("path")
    explain_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Roda só o core e gera o esqueleto estrutural, sem LLM",
    )
    explain_cmd.add_argument("--model", help="ex.: openai/gpt-4o-mini, ollama/qwen2.5-coder")
    explain_cmd.add_argument(
        "--max-tokens", type=int, default=1_000_000, help="orçamento de tokens do run"
    )
    explain_cmd.add_argument("--out", help="diretório de saída (padrão: <path>/.reponexia)")
    explain_cmd.add_argument("--verbose", action="store_true")

    graph_cmd = sub.add_parser("graph", help="Exporta o grafo do repositório")
    graph_cmd.add_argument("path")
    graph_cmd.add_argument("--format", choices=["json", "mermaid"], default="json")
    graph_cmd.add_argument("--out", help="arquivo de saída (padrão: stdout)")

    ask_cmd = sub.add_parser("ask", help="Pergunta sobre o índice do repositório")
    ask_cmd.add_argument("path")
    ask_cmd.add_argument("question")
    ask_cmd.add_argument("--model")
    ask_cmd.add_argument("--max-tokens", type=int, default=1_000_000)

    args = parser.parse_args(argv)

    # Guia não toca no core nem exige path: é o comando de quem está perdido.
    if args.command == "guia":
        try:
            print(render_guide(args.topico, markdown=args.markdown))
        except KeyError:
            print(f"topico desconhecido: {args.topico}", file=sys.stderr)
            print("disponiveis: " + ", ".join(ORDER), file=sys.stderr)
            return 1
        return 0

    if args.command == "map":
        try:
            graph = index(args.path)
        except (CoreNotFound, ContractError) as err:
            print(err, file=sys.stderr)
            return 1
        print(json.dumps(graph, indent=2, ensure_ascii=False))
        return 0

    if args.command == "graph":
        try:
            graph = index(args.path)
        except (CoreNotFound, ContractError) as err:
            print(err, file=sys.stderr)
            return 1
        text = _json(graph) if args.format == "json" else render_mermaid(graph)
        if args.out:
            _write(Path(args.out), text)
        else:
            sys.stdout.write(text)
        return 0

    if args.command == "ask":
        model = _model_from(args)
        if not model:
            print("defina --model ou REPONEXIA_MODEL", file=sys.stderr)
            return 1
        try:
            graph = index(args.path)
            print(ask(graph, args.question, model, max_tokens=args.max_tokens))
        except (CoreNotFound, ContractError, SummarizerError) as err:
            print(err, file=sys.stderr)
            return 1
        return 0

    if args.command == "explain":
        # No modo real exigimos modelo antes de tocar no core.
        model = None
        if not args.dry_run:
            model = _model_from(args)
            if not model:
                print("defina --model ou REPONEXIA_MODEL (ou use --dry-run)", file=sys.stderr)
                return 1

        try:
            graph = index(args.path)
        except (CoreNotFound, ContractError) as err:
            print(err, file=sys.stderr)
            return 1

        out_dir = Path(args.out) if args.out else Path(args.path).resolve() / ".reponexia"

        narrative = None
        if not args.dry_run:
            summarizer = LiteLLMSummarizer(model, max_tokens=args.max_tokens)
            cache = Cache(out_dir / "cache.json")
            try:
                narrative = build_narrative(
                    graph, summarizer, cache=cache, verbose=args.verbose
                )
            except (SummarizerError, BudgetExceeded) as err:
                print(err, file=sys.stderr)
                return 1
            cache.save()
            if args.verbose:
                print(
                    f"[verbose] ~{summarizer.spent} tokens gastos", file=sys.stderr
                )

        _write(out_dir / "graph.json", _json(graph))
        onboarding = out_dir / "ONBOARDING.md"
        _write(onboarding, render_markdown(graph, narrative))
        architecture = out_dir / "architecture.mmd"
        _write(architecture, render_mermaid(graph))

        print(f"onboarding gerado em {onboarding}")
        print(f"arquitetura gerada em {architecture}")
        print(f"grafo gerado em {out_dir / 'graph.json'}")
        return 0

    return 1
