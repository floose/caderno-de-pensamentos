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
- Commits recentes: `78cabfa` centraliza o tema e ajusta layout; `b6760f2` corrige contraste e adiciona o launcher; `1678e5d` inicia os testes de fluxos do cofre.
- Há alterações locais não commitadas em `MEMORIA_DO_PROJETO.md`, `Plano_do_projeto.md`, `src/caderno/ui.py`, `testar_ui.command`, `tests/test_ui.py` e `tests/test_ui_layout.py`. Preservá-las.
- A UI já cria, seleciona, abre e fecha bases. Tema, tipografia e diálogo de senha estão sendo ajustados; o diálogo usa campo mascarado, ações tematizadas, Enter para confirmar e Escape para cancelar.
- Execute `./testar_ui.command` (ou abra o arquivo pelo Finder) para rodar os testes focados e iniciar a janela com um perfil sintético isolado em `/private/tmp`. Não use arquivos pessoais nesse perfil.
- Validações: suíte completa, 77 testes aprovados; suíte focada de UI, 30 aprovados após a correção da inicialização; `git diff --check` aprovado. A janela real voltou a abrir e responder no launcher, confirmado manualmente. Resta conferir o diálogo de senha e o encaixe visual no tamanho mínimo.
- O cofre CPV1 tem backend real com PyNaCl/libsodium e fixtures sintéticas. O ciclo e os limites criptográficos estão descritos nos documentos de referência. Ainda falta validar dependências, desempenho e ciclo integrado no `.app` arm64 antes de usar dados pessoais.

## Próximos passos

1. Conferir visualmente o diálogo de senha, foco, cores e encaixe na janela mínima pelo launcher.
2. Desenvolver a primeira fatia de notas: listar, criar, editar, salvar, fechar e reabrir usando a fachada `caderno.vault` e fixtures sintéticas.
3. Preparar e validar uma prova `.app` arm64; só depois avançar para backup, integração completa e o gate de dados pessoais.

Não fazer commit até receber autorização explícita.
