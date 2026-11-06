# RepoNexia

CLI que explica um repositório desconhecido: mapeia arquitetura, entry points e
dependências críticas, e gera um onboarding doc.

Motor em Rust (`reponexia-core`) faz o parse e monta o grafo; orquestrador em
Python chama o LLM e renderiza a documentação.

```
reponexia explain <path>
```

Status: design concluído, fase P0 (esqueleto do core).
