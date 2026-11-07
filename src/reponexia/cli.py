from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .contract import ContractError
from .core_runner import CoreNotFound, index
from .render import render_markdown


def main(argv: list[str] | None = None) -> int:
    # Garante que o console aceite acentos e símbolos do markdown
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(prog="reponexia")
    sub = parser.add_subparsers(dest="command", required=True)

    # Subcomando map: só o core, sem LLM
    map_cmd = sub.add_parser("map", help="Mostra a estrutura do repositório (sem LLM)")
    map_cmd.add_argument("path")

    # Subcomando explain: gera o onboarding do repositório analisado
    explain_cmd = sub.add_parser(
        "explain", help="Gera o onboarding do repositório (--dry-run = sem LLM)"
    )
    explain_cmd.add_argument("path")
    explain_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Roda só o core e gera o esqueleto estrutural, sem LLM",
    )

    args = parser.parse_args(argv)

    if args.command == "map":
        # Indexa o repositório e imprime o grafo como JSON
        try:
            graph = index(args.path)
        except (CoreNotFound, ContractError) as err:
            print(err, file=sys.stderr)
            return 1
        print(json.dumps(graph, indent=2))
        return 0

    if args.command == "explain":
        # Por enquanto só o esqueleto sem LLM está disponível
        if not args.dry_run:
            print("pipeline completo ainda nao disponivel; use --dry-run", file=sys.stderr)
            return 1

        # Indexa o repositório usando o motor Rust
        try:
            graph = index(args.path)
        except (CoreNotFound, ContractError) as err:
            print(err, file=sys.stderr)
            return 1

        # Cria a pasta de saída dentro do repositório analisado
        out_dir = Path(args.path).resolve() / ".reponexia"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "ONBOARDING.md"

        # Renderiza o esqueleto e grava em UTF-8 com quebra de linha fixa
        with out_file.open("w", encoding="utf-8", newline="\n") as file:
            file.write(render_markdown(graph))

        print(f"onboarding gerado em {out_file}")
        return 0

    return 1
