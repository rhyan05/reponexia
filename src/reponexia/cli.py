from __future__ import annotations

import argparse
import json
import sys

from .contract import ContractError
from .core_runner import CoreNotFound, index


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(prog="reponexia")
    sub = parser.add_subparsers(dest="command", required=True)

    map_cmd = sub.add_parser("map", help="Mostra a estrutura do repositório (sem LLM)")
    map_cmd.add_argument("path")

    args = parser.parse_args(argv)

    if args.command == "map":
        try:
            graph = index(args.path)
        except (CoreNotFound, ContractError) as err:
            print(err, file=sys.stderr)
            return 1
        print(json.dumps(graph, indent=2))
        return 0

    return 1
