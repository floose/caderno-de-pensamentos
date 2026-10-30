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

## Retomada — 2026-10-30

- Branch atual: `feature/ui-vault-integration`, baseada em `feature/vault-encryption`; `main` permanece preservada. O commit mais recente, `1e603eb`, foi enviado para `origin/feature/ui-vault-integration`; antes dele estão `1884f71` (layout e datas) e `ae48dbf` (foco em campos inválidos).
- A UI cria, seleciona, abre e fecha bases; também lista, cria e edita notas com rascunho local e salvamento explícito. Excluir nota ainda não está implementado. O campo de senha aceita Enter; o editor oferece `⌘S`; o diálogo de alterações oferece salvar, descartar e cancelar por botão, com `⌘S`, `⌘⌫` e `Escape`.
- Execute `./testar_ui.command` (ou abra o arquivo pelo Finder) para rodar os testes focados e iniciar a janela com um perfil sintético isolado em `/private/tmp`. Não use arquivos pessoais nesse perfil.
- A UI agora permite criar coleções e associar coleção e hashtags às notas. Alterações nesses metadados participam do estado pendente e das escolhas salvar/descartar/cancelar; coleções e hashtags são persistidas no snapshot do cofre. O roteiro de janela real está em `testar_ui.command`.
- Aceite da UI em janela Tk real passou com cofre CPV1 sintético: janela normal e visível; coleção criada pelo callback; nota associada e salva com `⌘S` gerado no campo de hashtags; `Escape` com Cancelar preservou o rascunho e com Descartar restaurou o salvo; fechar e reabrir preservou coleção e hashtags. O campo de nome foi fornecido ao diálogo por harness temporário; entrada física no diálogo não foi exercitada. Esse teste usou a UI do código-fonte, não o bundle `.app`.
- Etapa 2, no Mac atual: o `.app` arm64 foi compactado em ZIP (~13 MB), extraído em outra pasta temporária e aberto diretamente pelo executável extraído; a janela bloqueada ficou visível e normal. O bundle declara `minos 11.0`, mas isso não comprova funcionamento em macOS 11 ou 14. Por ora não vamos fazer downgrade nem validar versões antigas; o alvo planejado macOS 14 fica sem teste até a distribuição ser relevante.
- Os achados céticos foram corrigidos: `⌘S`/`Escape` também estão ligados ao seletor; os rótulos de coleção são únicos mesmo com colisões entre sufixos gerados e nomes literais; nomes duplicados por diferença de caixa mostram alerta e não são salvos. Há regressões para os três comportamentos.
- Alertas, entrada de texto, navegação para abrir/criar base, seleção de coleção, filtros, ordenação e senha usam diálogos próprios do app, com estilo compartilhado e ações por teclado. Reauditado em 2026-10-30: não há imports/chamadas a `messagebox`, `simpledialog`, `filedialog`, `ttk`, `NSAlert` ou `osascript` no código de produção; os modais usam `tk.Toplevel`. O Tk ainda entrega a moldura da janela e eventos ao gerenciador de janelas do sistema. O seletor de arquivos permite navegar pastas, filtrar `.cpv` e restringir o perfil sintético; Enter envia a senha a partir do campo mascarado.
- Preferências usam os diretórios convencionais por plataforma (Application Support no macOS, APPDATA no Windows e XDG no Linux); `CADERNO_CONFIG_DIR` continua permitindo isolamento.
- A busca combina todos os termos digitados, sem diferenciar maiúsculas/minúsculas, sobre título, conteúdo, coleção e hashtags. Filtros temporários por coleção, hashtag e favoritas se combinam com a busca. A ordenação oferece edição, criação ou título em ordem ascendente/descendente; o padrão é edição mais recente primeiro. Busca, filtros e ordenação são temporários, reiniciam ao fechar/trocar de base e atualizam somente a lista para preservar o rascunho. O favorito é um metadado persistente da nota e suas alterações participam do estado pendente.
- O modo **Expandir escrita** oculta temporariamente a navegação, lista, título e metadados, mantendo o mesmo widget de texto. Salvar preserva o modo expandido; Escape ou Voltar restauram o editor sem descartar o rascunho. Fechar a base sai do modo de foco. Se validação de título ou hashtag falhar no modo expandido, o app o encerra antes de focar o campo inválido.
- O editor mantém largura mínima de 1000 px para preservar botões e colunas; o seletor de coleção quebra nomes extensos em linhas. Notas existentes mostram data e hora de criação e última modificação no topo; notas novas passam a mostrar esses dados após o primeiro salvamento. ⌘N cria uma nota na coleção atualmente selecionada; ⌃⌘E alterna o modo Expandir escrita, e o botão mostra esse atalho nos dois estados.
- Validações: 94 testes focados aprovados (UI, notas, preferências, contraste e layout). A prova arm64 e os probes UI/Tk + CPV1 de uma versão anterior passaram; a build atual ainda precisa ser refeita e validada com o ciclo integrado. O smoke de código-fonte confirma largura mínima, atalhos de foco e nova nota, coleção herdada, datas após salvar e o fluxo de favoritos/foco. O roteiro manual está em [`testar_ui.command`](testar_ui.command).
- O cofre CPV1 tem backend real com PyNaCl/libsodium e fixtures sintéticas. O ciclo e os limites criptográficos estão descritos nos documentos de referência. Ainda falta validar dependências, desempenho e ciclo integrado no `.app` arm64 antes de usar dados pessoais.

## Próximos passos

1. **Validar a build atual do `.app` com dados sintéticos.** Recompilar a versão após os commits recentes e exercitar criar/abrir, senha correta e incorreta, Enter no campo de senha, salvar, fechar e reabrir; conferir duplicidade, atalhos e persistência. Repetir a troca de senha e medir Argon2id no runtime empacotado. Isso valida o pacote neste Mac, não compatibilidade com outras versões do macOS.
2. **Implementar exclusão segura de notas.** Incluir confirmação no modal próprio do app, respeitar rascunhos pendentes e remover do snapshot também os anexos associados, com testes de persistência e regressão.
3. **Implementar editor e visualização Markdown**, preservando o texto atual do corpo e sem alterar o schema do cofre.
4. **Implementar anexos na UI**, com validação dos limites já definidos no schema e persistência exclusivamente dentro do cofre.
5. **Planejar backup/restauração e migração** antes de futuras mudanças de formato; cobrir falhas e recuperação com fixtures sintéticas.
6. **Definir o calendário** a partir das datas disponíveis e revisar acessibilidade e comportamento ao fechar o aplicativo.

Distribuição, instalação limpa, assinatura/notarização e validação em outras versões de macOS continuam adiadas enquanto o uso for particular. O mínimo de versão do sistema também não é uma validação concluída.

Não fazer commit até receber autorização explícita.
