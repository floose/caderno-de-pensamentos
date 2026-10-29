# Memória do projeto — Caderno de Pensamentos

Ponto curto de retomada para novas sessões. Antes de agir, confirme o estado real do Git e do código; esta memória pode ficar desatualizada.

## Produto e regras

Aplicativo offline para macOS Apple Silicon, em Python/Tkinter, planejado para distribuição como `.app`. Textos e imagens serão guardados num arquivo de cofre criptografado.

- Conversar em português. Não fazer commit, merge, rebase ou push sem autorização explícita.
- Preservar alterações locais e nunca versionar dados pessoais, senhas, chaves ou caminhos específicos da máquina.
- Manter `src/caderno/vault/` independente da UI. Usar apenas primitivas criptográficas de bibliotecas estabelecidas.
- Preferir nomes semânticos, valores visuais centralizados, funções curtas e testes para funcionalidades e regressões.
- Toda mudança de UI deve incluir um modo reproduzível de abrir e testar a janela.

## Documentos de referência

- [`Plano_do_projeto.md`](Plano_do_projeto.md): escopo, marcos e processo de desenvolvimento da UI.
- [`Decisao_de_arquitetura_cofre.md`](Decisao_de_arquitetura_cofre.md): especificação técnica vigente do formato CPV1.
- [`Plano_de_desenvolvimento_criptografia.md`](Plano_de_desenvolvimento_criptografia.md): cobertura, medições e pendências do núcleo criptográfico.
- [`AGENTS.md`](AGENTS.md): instruções obrigatórias para agentes neste repositório.

Cada documento deve manter os detalhes da sua área; evite copiá-los para esta memória.

## Retomada — 2026-10-29

- Branch atual: `feature/ui-vault-integration`, baseada em `feature/vault-encryption`; `main` permanece preservada. HEAD confirmado: `1faec56`.
- Há alterações locais sem commit em `src/caderno/ui.py`, `tests/test_ui.py`, `tests/test_ui_notes.py`, `tests/test_ui_layout.py`, `testar_ui.command`, `scripts/build_macos_app.command`, `scripts/packaged_entry.py`, `scripts/package_vault_smoke.py`, `Plano_do_projeto.md` e `MEMORIA_DO_PROJETO.md`.
- A UI cria, seleciona, abre e fecha bases; também lista, cria e edita notas com rascunho local e salvamento explícito. O editor oferece `⌘S`; o diálogo de alterações oferece salvar, descartar e cancelar por botão, com `⌘S`, `⌘⌫` e `Escape`.
- Execute `./testar_ui.command` (ou abra o arquivo pelo Finder) para rodar os testes focados e iniciar a janela com um perfil sintético isolado em `/private/tmp`. Não use arquivos pessoais nesse perfil.
- A UI agora permite criar coleções e associar coleção e hashtags às notas. Alterações nesses metadados participam do estado pendente e das escolhas salvar/descartar/cancelar; coleções e hashtags são persistidas no snapshot do cofre. O roteiro de janela real está em `testar_ui.command`.
- Validações da fatia: 61 testes focados aprovados (UI, notas, preferências, contraste e layout); `sh -n` nos scripts e `git diff --check` passaram. O ciclo de persistência da nota com metadados foi coberto com cofre sintético real. A build arm64 foi refeita e o smoke test CPV1 empacotado passou; o exercício completo de criar/editar/reabrir notas pela janela do `.app` ainda precisa ser feito.
- O cofre CPV1 tem backend real com PyNaCl/libsodium e fixtures sintéticas. O ciclo e os limites criptográficos estão descritos nos documentos de referência. Ainda falta validar dependências, desempenho e ciclo integrado no `.app` arm64 antes de usar dados pessoais.

## Próximos passos

1. Validar o ciclo completo de coleção/nota pela janela do `.app` empacotado.
2. Validar abertura do pacote após mover/extraí-lo e testar em macOS 14 e numa instalação limpa.
3. Avançar com busca, filtros e ordenação; depois Markdown, anexos, calendário e backup/restauração.

Não fazer commit até receber autorização explícita.
