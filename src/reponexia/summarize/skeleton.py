from __future__ import annotations

# Acima disso o arquivo não vai inteiro para o LLM: vira esqueleto.
MAX_LINES_FOR_LLM = 1500


# Reduz um arquivo grande às suas "costuras": imports + linhas de declaração de
# símbolos (que o grafo já conhece), omitindo corpos.
# Por quê: mandar 5k linhas estoura a context window e encarece a chamada.
def skeletonize(text: str, symbols: list[dict]) -> str:
    lines = text.splitlines()
    if len(lines) <= MAX_LINES_FOR_LLM:
        return text

    kept: dict[int, str] = {}
    for number, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        # Imports dão o "de onde vem" sem custo de corpo.
        if stripped.startswith(("import ", "from ")):
            kept[number] = line

    # Assinaturas vêm do grafo (line já é 1-based).
    for symbol in symbols:
        number = symbol.get("line", 0)
        if 1 <= number <= len(lines):
            kept[number] = lines[number - 1]

    return "\n".join(kept[number] for number in sorted(kept))
