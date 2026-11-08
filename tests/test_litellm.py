import pytest

from reponexia.summarize.base import ModuleContext, RepoContext, SymbolRef
from reponexia.summarize.litellm_impl import (
    BudgetExceeded,
    LiteLLMSummarizer,
    SummarizerError,
)


def module():
    return ModuleContext(
        name="app",
        files=("app/main.py",),
        symbols=(SymbolRef("main", "function", 10, "app/main.py"),),
        imports_out=("app/util",),
        imports_in=(),
        snippets=("valor = 1",),
    )


def test_prompt_cita_arquivo_e_linha():
    prompts = []

    def fake(prompt):
        prompts.append(prompt)
        return "resumo"

    out = LiteLLMSummarizer("x", call=fake).summarize_module(module())

    assert out == "resumo"
    assert "app/main.py:10" in prompts[0]
    assert "app/util" in prompts[0]


def test_retry_com_backoff_ate_ter_sucesso():
    calls = []

    def flaky(prompt):
        calls.append(prompt)
        if len(calls) < 3:
            raise RuntimeError("provider fora")
        return "ok"

    summarizer = LiteLLMSummarizer(
        "x", retries=3, call=flaky, sleep=lambda _seconds: None
    )

    assert summarizer.summarize_module(module()) == "ok"
    assert len(calls) == 3


def test_erro_apos_esgotar_retries():
    def sempre_falha(prompt):
        raise RuntimeError("fora")

    summarizer = LiteLLMSummarizer(
        "x", retries=1, call=sempre_falha, sleep=lambda _seconds: None
    )

    with pytest.raises(SummarizerError):
        summarizer.summarize_module(module())


def test_estoura_orcamento():
    summarizer = LiteLLMSummarizer(
        "x", max_tokens=1, call=lambda _prompt: "a" * 4000
    )

    with pytest.raises(BudgetExceeded):
        summarizer.summarize_module(module())


def test_resumo_do_repo_usa_resumos_dos_modulos():
    prompts = []

    def fake(prompt):
        prompts.append(prompt)
        return "visao"

    ctx = RepoContext(
        name="repo",
        languages=("python",),
        file_count=3,
        module_summaries=("## app\nresumo do app",),
    )

    assert LiteLLMSummarizer("x", call=fake).summarize_repo(ctx) == "visao"
    assert "resumo do app" in prompts[0]
