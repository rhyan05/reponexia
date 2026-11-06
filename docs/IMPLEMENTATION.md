# RepoNexia — Plano de Implementação

Trilha de execução por commits. O design canônico está em
[`DESIGN.md`](./DESIGN.md); este documento define **em que ordem** construir.

> **Regra de ouro:** cada commit abaixo deve deixar o repositório em estado
> executável. Não comece o próximo passo antes do anterior rodar com um comando
> real.

## Bloco A — Fronteira viva (P0)

1. `chore: init repo, README esqueleto, .gitignore`
2. `feat(core): clap + comando index que só lista arquivos (sem parse)`
3. `feat(contract): graph.schema.json v1.0 (mínimo: files, warnings)`
4. `feat(py): core_runner chama o binário e imprime JSON cru`
5. ✅ Checkpoint: `reponexia map <path>` mostra a lista de arquivos do repo alvo.

## Bloco B — Parse de uma linguagem (início do P1)

6. `feat(core): tree-sitter-python; extrai símbolos (função/classe)`
7. `feat(core): extrai imports de python`
8. `feat(contract): adiciona symbols[] e edges[] ao schema` (bump minor)
9. ✅ Checkpoint: `reponexia map` mostra símbolos de um arquivo Python real.

## Bloco C — Grafo e métricas (fim do P1)

10. `feat(core): resolve imports internos e monta edges reais`
11. `feat(core): fan-in/fan-out + page_rank (petgraph)`
12. `feat(core): entry_points heurísticos (main, __main__, console_scripts)`
13. `feat(test): teste automatizado de determinismo (2x → diff vazio)`
14. ✅ Checkpoint: `graph.json` determinístico (rodar 2x, diff = vazio).

## Bloco D — Skeleton doc sem LLM (P2)

15. `feat(py): valida graph.json contra o schema (jsonschema)`
16. `feat(py): render/ markdown com estrutura do repo e módulos`
17. `feat(py): comando explain --dry-run gera .reponexia/ONBOARDING.md`
18. ✅ Checkpoint: doc estrutural gerado sem nenhuma chamada LLM.

## Bloco E — LLM com responsabilidade (P3)

19. `feat(py): Summarizer Protocol + LiteLLMSummarizer (só módulo a módulo)`
20. `feat(py): sumarização hierárquica (módulos → repo)`
21. `feat(py): redact.py + aplicação antes do LLM`
22. `feat(py): skeleton.py para arquivos > MAX_LINES_FOR_LLM`
23. `feat(py): --max-tokens e retry com backoff`
24. ✅ Checkpoint: `explain` gera ONBOARDING.md com citações reais.

## Bloco F — Polimento (P4)

25. `feat(py): cache por hash de graph.json + repo_hash`
26. `feat(py): incremental por módulo`
27. `feat(core): --jobs + rayon (parse paralelo)`
28. ✅ Checkpoint: 2ª execução sem mudanças = zero chamadas LLM.

## Bloco G — Extensão (P5)

29. `feat(core): grammars javascript/typescript`
30. `feat(py): filtro do Mermaid (top N por PageRank)`
31. `feat(py): comando ask` (fase 2)
32. `docs: examples/ com ONBOARDING.md de um repo OSS famoso`
