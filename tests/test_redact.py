import pytest

from reponexia.redact import PATTERNS, PLACEHOLDER, redact


# Um exemplo realista por padrão do DESIGN.
SEGREDOS = [
    ("aws", "AKIAIOSFODNN7EXAMPLE"),
    ("openai", "sk-abcdefghijklmnopqrstuvwx1234"),
    ("github", "ghp_" + "a" * 36),
    ("slack", "xoxb-1234567890-abcdefghij"),
    ("private_key", "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA\n-----END RSA PRIVATE KEY-----"),
    ("connection", "postgres://admin:s3nh4-secreta@db.internal:5432/app"),
]


# Cada padrão deve sumir do texto e virar o marcador.
@pytest.mark.parametrize("nome,segredo", SEGREDOS)
def test_redige_cada_padrao(nome, segredo):
    out = redact(f"valor = {segredo}")
    assert PLACEHOLDER in out
    assert segredo not in out
    # Nada detectável pode sobreviver no texto redigido.
    assert all(not p.search(out) for p in PATTERNS), nome


# Texto limpo não é alterado.
def test_texto_sem_segredo_nao_muda():
    texto = "def soma(a, b):\n    return a + b\n"
    assert redact(texto) == texto


# Rodar de novo no resultado não muda mais nada.
def test_idempotente():
    out = redact("AKIAIOSFODNN7EXAMPLE")
    assert redact(out) == out


# O corpo da chave privada (não só o header) fica escondido.
def test_chave_privada_redige_o_corpo():
    corpo = "-----BEGIN RSA PRIVATE KEY-----\nCONTEUDO_SECRETO\n-----END RSA PRIVATE KEY-----"
    assert "CONTEUDO_SECRETO" not in redact(corpo)
