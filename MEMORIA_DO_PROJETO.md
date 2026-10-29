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

- Branch atual: `feature/ui-vault-integration`, baseada em `feature/vault-encryption`; `main` permanece preservada. Últimos commits: `557cec7` (aceite Tk documentado), `d12cc9a` (atalhos no campo de hashtags) e `4655768` (coleções, hashtags e prova do app).
- A UI cria, seleciona, abre e fecha bases; também lista, cria e edita notas com rascunho local e salvamento explícito. O editor oferece `⌘S`; o diálogo de alterações oferece salvar, descartar e cancelar por botão, com `⌘S`, `⌘⌫` e `Escape`.
- Execute `./testar_ui.command` (ou abra o arquivo pelo Finder) para rodar os testes focados e iniciar a janela com um perfil sintético isolado em `/private/tmp`. Não use arquivos pessoais nesse perfil.
- A UI agora permite criar coleções e associar coleção e hashtags às notas. Alterações nesses metadados participam do estado pendente e das escolhas salvar/descartar/cancelar; coleções e hashtags são persistidas no snapshot do cofre. O roteiro de janela real está em `testar_ui.command`.
- Aceite da UI em janela Tk real passou com cofre CPV1 sintético: janela normal e visível; coleção criada pelo callback; nota associada e salva com `⌘S` gerado no campo de hashtags; `Escape` com Cancelar preservou o rascunho e com Descartar restaurou o salvo; fechar e reabrir preservou coleção e hashtags. O campo de nome foi fornecido ao diálogo por harness temporário; entrada física no diálogo não foi exercitada. Esse teste usou a UI do código-fonte, não o bundle `.app`.
- Etapa 2, no Mac atual: o `.app` arm64 foi compactado em ZIP (~13 MB), extraído em outra pasta temporária e aberto diretamente pelo executável extraído; a janela bloqueada ficou visível e normal. O bundle declara `minos 11.0`, mas isso não comprova funcionamento em macOS 11 ou 14. Por ora não vamos fazer downgrade nem validar versões antigas; o alvo planejado macOS 14 fica sem teste até a distribuição ser relevante.
- Os achados céticos foram corrigidos: `⌘S`/`Escape` também estão ligados ao seletor; os rótulos de coleção são únicos mesmo com colisões entre sufixos gerados e nomes literais; nomes duplicados por diferença de caixa mostram alerta e não são salvos. Há regressões para os três comportamentos.
- Alertas de erro/aviso/informação e a entrada de nome de coleção agora usam modais próprios do app, com estilo compartilhado, ações por teclado e sem `messagebox`/`simpledialog` nativos. Senha e alterações pendentes já usavam diálogos próprios; seletores de arquivo seguem a API multiplataforma `filedialog` do Tk. O usuário confirmou a aparência do alerta de duplicidade; o novo modal de texto ainda precisa de conferência pela janela real.
- Validações após a migração dos diálogos: 63 testes focados aprovados (UI, notas, preferências, contraste e layout); `sh -n` no roteiro e `git diff --check` passaram. Testes cobrem tema, modalidade, confirmação/cancelamento por teclado e fluxos de falha sem persistência indevida. A build arm64 foi refeita e o smoke test CPV1 empacotado passou; a nova versão da UI ainda precisa ser testada no bundle `.app`.
- O cofre CPV1 tem backend real com PyNaCl/libsodium e fixtures sintéticas. O ciclo e os limites criptográficos estão descritos nos documentos de referência. Ainda falta validar dependências, desempenho e ciclo integrado no `.app` arm64 antes de usar dados pessoais.

## Próximos passos

1. Repetir na janela do `.app` extraído os testes de coleção duplicada, atalhos no seletor e persistência.
2. Testar duplo clique no Finder se necessário; deixar compatibilidade com macOS 11/14, instalação limpa e distribuição para uma etapa posterior.
3. Avançar com busca, filtros e ordenação; depois Markdown, anexos, calendário e backup/restauração.

Não fazer commit até receber autorização explícita.
