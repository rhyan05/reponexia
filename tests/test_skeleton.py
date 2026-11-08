from reponexia.summarize.skeleton import MAX_LINES_FOR_LLM, skeletonize


def test_arquivo_pequeno_passa_intacto():
    texto = "import os\n\ndef soma(a, b):\n    return a + b\n"
    assert skeletonize(texto, [{"line": 3}]) == texto


def test_arquivo_grande_omite_corpos_e_mantem_imports_e_assinaturas():
    linhas = ["import os"] + [f"x{i} = {i}" for i in range(MAX_LINES_FOR_LLM + 10)]
    linhas[5] = "def alvo(a, b):"
    linhas[6] = "    return a + b"
    texto = "\n".join(linhas)

    out = skeletonize(texto, [{"line": 6}])

    assert "import os" in out
    assert "def alvo(a, b):" in out
    assert "return a + b" not in out
    assert "x0 = 0" not in out
    assert out.count("\n") == 1  # só import + assinatura
