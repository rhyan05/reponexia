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


# Testa se o grafo mínimo válido passa na validação
def test_grafo_minimo_valido():
    validate(VALID)


# Testa se o grafo com um campo obrigatório ausente levanta um ContractError
def test_campo_obrigatorio_ausente():
    graph = copy.deepcopy(VALID)
    del graph["root"]
    with pytest.raises(ContractError):
        validate(graph)


# Testa se uma versão major diferente falha na validação
def test_major_de_schema_errado():
    graph = copy.deepcopy(VALID)
    graph["schema_version"] = "2.0"
    with pytest.raises(ContractError):
        validate(graph)
