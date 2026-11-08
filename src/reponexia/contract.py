from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

import jsonschema


class ContractError(ValueError):
    """O graph.json produzido pelo core viola o contrato."""


@lru_cache(maxsize=1)
def load_schema() -> dict:
    override = os.environ.get("REPONEXIA_CONTRACT")
    if override:
        path = Path(override)
    else:
        path = Path(__file__).with_name("graph.schema.json")

    if not path.exists():
        raise ContractError(f"schema do contrato nao encontrado em {path}")

    with path.open(encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError as err:
            raise ContractError(f"schema invalido em {path}: {err}") from err


def validate(graph: dict) -> None:
    schema = load_schema()

    try:
        jsonschema.validate(instance=graph, schema=schema)
    except jsonschema.ValidationError as err:
        raise ContractError(
            f"graph.json invalido em {err.json_path}: {err.message}"
        ) from err
    except jsonschema.SchemaError as err:
        raise ContractError(f"schema invalido: {err.message}") from err
