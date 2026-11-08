from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path


def cache_key(*parts: str) -> str:
    hasher = sha256()
    for part in parts:
        hasher.update(part.encode("utf-8"))
        hasher.update(b"\x00")  # separador evita colisão entre campos
    return hasher.hexdigest()


# Cache local em JSON: map de chave -> resumo.
# Chave inclui repo/conteúdo do módulo + modelo, então rodar sem mudança = 0 chamadas.
class Cache:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._data = self._load()

    def _load(self) -> dict[str, str]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def get(self, key: str) -> str | None:
        return self._data.get(key)

    def set(self, key: str, value: str) -> None:
        self._data[key] = value

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._data, indent=2, sort_keys=True, ensure_ascii=False),
            encoding="utf-8",
        )
