from __future__ import annotations

import time
from collections.abc import Callable

from .base import ModuleContext, RepoContext


class SummarizerError(RuntimeError):
    """Falha ao obter resumo do LLM (após os retries)."""


class BudgetExceeded(SummarizerError):
    """O orçamento de tokens configurado seria estourado."""


def _estimate_tokens(text: str) -> int:
    # ponytail: estimativa chars/4; trocar por tokenizer real se o custo precisar ser exato
    return max(1, len(text) // 4)


# Implementação única sobre o litellm, que já abstrai OpenAI/Anthropic/Ollama.
# O Protocol Summarizer existe só para permitir mock/offline nos testes.
class LiteLLMSummarizer:
    def __init__(
        self,
        model: str,
        *,
        max_tokens: int = 1_000_000,
        retries: int = 3,
        call: Callable[[str], str] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.retries = retries
        self.spent = 0
        self._call = call or self._litellm_call
        self._sleep = sleep

    # Chamada real; o import fica lazy para testar sem o litellm instalado.
    def _litellm_call(self, prompt: str) -> str:
        import litellm

        response = litellm.completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""

    # Executa com retry/backoff e contabiliza o orçamento antes de devolver.
    def _complete(self, prompt: str) -> str:
        for attempt in range(self.retries + 1):
            try:
                text = self._call(prompt)
            except Exception as err:  # noqa: BLE001 - qualquer falha de provider
                if attempt == self.retries:
                    raise SummarizerError(
                        f"LLM falhou apos {self.retries + 1} tentativas: {err}"
                    ) from err
                self._sleep(2**attempt)
                continue

            self.spent += _estimate_tokens(prompt) + _estimate_tokens(text)
            if self.spent > self.max_tokens:
                raise BudgetExceeded(
                    f"orcamento de {self.max_tokens} tokens estourado "
                    f"(~{self.spent} usados)"
                )
            return text

        raise AssertionError("inalcancavel")

    def _module_prompt(self, module: ModuleContext) -> str:
        parts = [f"Modulo: {module.name}"]
        parts.append("Arquivos:\n" + "\n".join(f"- {path}" for path in module.files))
        if module.symbols:
            parts.append(
                "Simbolos:\n"
                + "\n".join(
                    f"- {symbol.name} ({symbol.kind}) em {symbol.file}:{symbol.line}"
                    for symbol in module.symbols
                )
            )
        if module.imports_out:
            parts.append("Depende de: " + ", ".join(module.imports_out))
        if module.imports_in:
            parts.append("E usado por: " + ", ".join(module.imports_in))
        if module.snippets:
            parts.append("Snippets (redigidos):\n" + "\n\n".join(module.snippets))
        parts.append(
            "Explique o proposito deste modulo em 3 a 6 frases. "
            "Cite arquivo:linha ao afirmar algo sobre o codigo."
        )
        return "\n\n".join(parts)

    def summarize_module(self, module: ModuleContext) -> str:
        return self._complete(self._module_prompt(module))

    def _repo_prompt(self, ctx: RepoContext) -> str:
        parts = [f"Repositorio: {ctx.name}"]
        parts.append(f"Arquivos: {ctx.file_count}. Linguagens: {', '.join(ctx.languages)}.")
        parts.append("Resumos por modulo:\n\n" + "\n\n".join(ctx.module_summaries))
        parts.append(
            "Com base apenas nos resumos acima, escreva uma visao geral da arquitetura "
            "em 2 a 4 paragrafos. Nao invente fatos nem arquivos."
        )
        return "\n\n".join(parts)

    def summarize_repo(self, ctx: RepoContext) -> str:
        return self._complete(self._repo_prompt(ctx))
