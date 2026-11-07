import copy

import pytest

from reponexia.contract import ContractError, validate

VALID = {
    "schema_version": "1.0",
    "root": "/tmp/repo",
    "files": [
        {
            "path": "a.py",
            "language": "python",
            "loc": 3,
            "hash": "abc",
            "parse_errors": [],
        }
    ],
}


def test_grafo_minimo_valido():
    validate(VALID)


def test_campo_obrigatorio_ausente():
    graph = copy.deepcopy(VALID)
    del graph["root"]
    with pytest.raises(ContractError):
        validate(graph)


def test_major_de_schema_errado():
    graph = copy.deepcopy(VALID)
    graph["schema_version"] = "2.0"
    with pytest.raises(ContractError):
        validate(graph)
