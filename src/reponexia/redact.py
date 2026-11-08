from __future__ import annotations

import re

PLACEHOLDER = "[REDACTED]"

# Regex de padrões comuns de segredo. Configuráveis via o parâmetro `patterns`,
# para quando existir um arquivo de config (por ora o default cobre os casos do DESIGN).
PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"AKIA[0-9A-Z]{16}"),                    # AWS access key
    re.compile(r"sk-[A-Za-z0-9]{20,}"),                 # chave estilo OpenAI
    re.compile(r"ghp_[A-Za-z0-9]{36}"),                 # GitHub token
    re.compile(r"xox[baprs]-[A-Za-z0-9-]+"),            # Slack token
    re.compile(                                         # bloco de chave privada
        r"-----BEGIN[^-]*PRIVATE KEY-----.*?-----END[^-]*PRIVATE KEY-----",
        re.DOTALL,                                      # o corpo tem quebras de linha
    ),
    re.compile(                                         # connection string com senha
        r"\b(?:postgres(?:ql)?|mysql|mongodb|redis)://[^:\s]+:[^@\s]+@[^\s]+"
    ),
)


# Substitui todo segredo detectado por um marcador fixo.
def redact(text: str, patterns: tuple[re.Pattern[str], ...] = PATTERNS) -> str:
    for pattern in patterns:
        text = pattern.sub(PLACEHOLDER, text)
    return text
