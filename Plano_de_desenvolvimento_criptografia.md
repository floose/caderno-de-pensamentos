# Desenvolvimento do cofre criptografado

**Branch:** `feature/vault-encryption`
**Estado:** protótipo CPV1 implementado em pacote separado da UI; não está pronto para dados reais.

Este documento acompanha tarefas, responsabilidades e validação. A especificação técnica única está em [`Decisao_de_arquitetura_cofre.md`](Decisao_de_arquitetura_cofre.md); não replique seus parâmetros aqui.

## Limites de trabalho

- Desenvolver em `src/caderno/vault/`; não importar Tkinter nem alterar `src/caderno/ui.py` antes da etapa explícita de integração.
- Usar `tests/fixtures/cofre_exemplo.json`, que contém dois textos sintéticos. Nunca incluir cofres reais, senhas, chaves ou plaintext pessoal no repositório.
- Não fazer commit, merge, rebase ou push sem autorização explícita.
- Registrar mudanças na arquitetura somente em `Decisao_de_arquitetura_cofre.md`.

## Agentes e revisão

### Desenvolvedor de criptografia

Tem autonomia para implementar a decisão CPV1, manter a API independente da UI, criar testes e corrigir problemas. Deve respeitar os limites da especificação, evitar primitivas próprias e registrar mudanças de formato antes de implementá-las.

### Agente cético

Revisa independentemente desenho, diff e testes; não altera arquivos durante a revisão. Prioriza autenticação completa, limites antes da KDF, truncamento/adulteração, vazamento de plaintext, gravação atômica, concorrência, schema/API e compatibilidade do `.app`. Registra achados com severidade, cenário e recomendação. Achados críticos/altos bloqueiam a conclusão até correção e nova revisão.

### Ciclo

1. Desenvolvedor propõe a decisão ou mudança; agente cético tenta refutá-la.
2. Desenvolvedor implementa e testa na branch desta feature.
3. Agente cético revisa o diff e os testes; desenvolvedor corrige e solicita nova revisão.
4. A coordenação relata limitações e evidências. Merge e commit dependem de autorização explícita.

## Estado e tarefas

- [x] Definir formato CPV1, API e limites iniciais; ver decisão arquitetural.
- [x] Implementar modelo, codec, persistência atômica e sessão em `src/caderno/vault/`.
- [x] Criar fixture sintética e testes do núcleo sem backend.
- [x] Fazer revisão cética inicial; não houve bloqueador para continuar como protótipo.
- [ ] Executar os testes integrados com PyNaCl/libsodium instalado; o teste criptográfico foi ignorado no último registro.
- [ ] Medir o perfil Argon2id no Mac arm64 e avaliar tempo/memória no hardware suportado.
- [ ] Ampliar testes de round-trip, senha errada, adulteração, truncamento, tags finais, salvamento, troca de senha e falhas de persistência.
- [ ] Validar inclusão e funcionamento do backend no `.app` arm64.
- [ ] Integrar a API do cofre à UI somente após as validações acima.

## Registro da última validação

- Último resultado registrado: `PYTHONPATH=src .venv/bin/python -m pytest -q` — 11 aprovados, 1 ignorado por falta do módulo `nacl`.
- `compileall` e `git diff --check` passaram naquele momento; repetir após alterações relevantes.
- O protótipo acumula plaintext em memória durante a autenticação, limitado pelos caps CPV1; não é leitura incremental.
- A medição sintética registrada foi de 28,3 MB em `tracemalloc`; não inclui buffers nativos nem memória total do runtime.
- PyNaCl real, benchmark Argon2id e build `.app` arm64 continuam sem validação. Não usar dados reais até fechar esses itens.

## Integração futura

A UI deve depender apenas da fachada pública `create_vault`, `open_vault` e dos métodos de `VaultSession` documentados no módulo. O pacote do cofre não apresenta diálogos nem conhece estado visual. A integração deve preservar mensagens seguras de erro e só indicar salvamento após persistência concluída.
