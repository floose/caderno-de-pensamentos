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

## Retomada — 2026-10-28

- Branch atual: `feature/ui-vault-integration`, baseada em `feature/vault-encryption`; `main` permanece preservada.
- Commit recente: `beb4f20` estabiliza a restauração inicial e o diálogo de senha. As alterações atuais da primeira fatia de notas estão locais e sem commit.
- A UI cria, seleciona, abre e fecha bases; também lista, cria e edita notas com rascunho local e salvamento explícito. O editor oferece `⌘S`; o diálogo de alterações oferece salvar, descartar e cancelar por botão, com `⌘S`, `⌘⌫` e `Escape`.
- Execute `./testar_ui.command` (ou abra o arquivo pelo Finder) para rodar os testes focados e iniciar a janela com um perfil sintético isolado em `/private/tmp`. Não use arquivos pessoais nesse perfil.
- Validações desta fatia: suíte focada de UI, notas, preferências, contraste e layout: 53 aprovados; mais 5 testes centrais de persistência, senha, falha pré-replace, durabilidade e conflito aprovados. Inclui ciclo real com PyNaCl, PNG sintético preservado, acesso com senha correta/incorreta e conflito entre sessões; `sh -n testar_ui.command` e `git diff --check` aprovados. A revisão cética não encontrou bloqueadores após corrigir o fechamento com widgets descartados. O launcher abriu a janela real no perfil sintético; ainda falta conferir manualmente os atalhos e o tamanho mínimo.
- O cofre CPV1 tem backend real com PyNaCl/libsodium e fixtures sintéticas. O ciclo e os limites criptográficos estão descritos nos documentos de referência. Ainda falta validar dependências, desempenho e ciclo integrado no `.app` arm64 antes de usar dados pessoais.

## Próximos passos

1. Conferir na janela real o fluxo de notas, os atalhos e as decisões salvar/descartar/cancelar, inclusive em 900 × 620.
2. Continuar com organização por coleções e hashtags, mantendo fixtures sintéticas e a fachada `caderno.vault`.
3. Preparar e validar uma prova `.app` arm64 antes de avançar para backup, integração completa e o gate de dados pessoais.

Não fazer commit até receber autorização explícita.
