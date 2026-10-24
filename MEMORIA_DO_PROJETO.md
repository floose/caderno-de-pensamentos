# Memória do projeto — Caderno de Pensamentos

Este é o ponto de retomada para novas sessões e agentes. Atualize-o quando uma decisão, estado de implementação ou próximo marco mudar. Não o trate como substituto da inspeção do repositório: confirme branch, diff, código e resultados de testes antes de agir.

## O que estamos construindo

Um caderno de conhecimento local e offline para macOS Apple Silicon, distribuído como `.app` sem exigir instalação de Python. O conteúdo — textos Markdown e imagens — ficará em um arquivo de dados criptografado. A interface inicial usa Python e Tkinter.

## Preferências permanentes da pessoa responsável

- Conversar em português.
- Não criar commits automaticamente; pedir autorização explícita antes de commit, merge, rebase ou push.
- Não começar implementação sem solicitação explícita. Ao receber autorização, executar o trabalho pedido sem pedir confirmações redundantes.
- Manter o projeto simples, modular e fácil de retomar por outros agentes.
- Funções devem ter até 50 linhas; comentários devem explicar decisões não óbvias.
- Adicionar testes automatizados para funcionalidade nova e regressões de bugs.
- Não versionar dados reais, senhas, chaves, caminhos pessoais, localização ou informações específicas da máquina.

## Mapa da memória

1. [`Plano_do_projeto.md`](Plano_do_projeto.md): requisitos, interface, empacotamento e marcos gerais.
2. [`Decisao_de_arquitetura_cofre.md`](Decisao_de_arquitetura_cofre.md): fonte única da arquitetura e formato CPV1.
3. [`Plano_de_desenvolvimento_criptografia.md`](Plano_de_desenvolvimento_criptografia.md): tarefas, responsabilidades dos agentes, revisão e estado da implementação.

Se documentos discordarem, confirme o código e o Git; registre cada decisão criptográfica apenas em `Decisao_de_arquitetura_cofre.md` e atualize o plano de desenvolvimento quando o estado das tarefas mudar.

## Estado conhecido na última atualização

- Branch de trabalho criptográfico: `feature/vault-encryption`.
- A camada isolada está em `src/caderno/vault/`; ela deve continuar sem dependência da UI Tkinter.
- CPV1 usa PyNaCl/libsodium, Argon2id e `crypto_secretstream_xchacha20poly1305`; detalhes, limites, formato e garantias estão na decisão arquitetural.
- A fixture `tests/fixtures/cofre_exemplo.json` tem conteúdo sintético. Não é uma base de produção.
- No último registro, PyNaCl não estava instalado no ambiente. Os testes não criptográficos passaram e um teste integrado foi ignorado; portanto, o backend real, o benchmark do perfil Argon2id e o `.app` arm64 ainda precisam ser validados antes de uso com dados reais.
- A última revisão cética não apontou bloqueador para continuar como protótipo, mas manteve essas validações como pré-requisitos para uso real.
- Não há autorização permanente para commit ou integração. A branch deve poder ser integrada futuramente pela API desacoplada, sem substituir a UI.

**Nota de atualidade:** este estado é um registro de retomada, não uma afirmação sobre o estado atual. Confira `git status`, `git branch --show-current`, dependências, testes e os documentos antes de relatar progresso.

## Como retomar uma tarefa

1. Leia estas instruções e o documento indicado no mapa para a área da tarefa.
2. Inspecione `git status` e a branch; preserve alterações existentes e não assuma que o último resumo ainda vale.
3. Siga os limites e as decisões registrados. Se encontrar contradições ou riscos, esclareça-os na documentação antes de ampliar o escopo.
4. Execute somente as validações relevantes e reporte exatamente o que foi ou não executado, incluindo testes ignorados e dependências indisponíveis.
5. Atualize esta memória quando a próxima sessão depender de uma decisão ou estado que mudou.
