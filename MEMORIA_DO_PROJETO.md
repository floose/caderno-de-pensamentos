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
- PyNaCl 1.6.2 está instalado no `.venv` do projeto. A suíte `PYTHONPATH=src .venv/bin/python -m pytest -q -ra tests/test_vault.py` passou com **14 testes aprovados e nenhum ignorado**.
- O teste de escala gera em memória 200 notas sintéticas de 5.000 palavras cada, cifra e reabre o cofre com PyNaCl real e inclui as imagens locais de teste. O teste focado passou em 4,88 s; a suíte completa passou com 14 testes em 15,36 s. A fixture de um milhão de palavras não é salva no repositório.
- O limite CPV1 de manifesto foi aumentado de 1 MiB para 8 MiB para permitir esse cenário experimental. Os limites gerais permanecem: plaintext 10 MiB, arquivo 14 MiB, anexos 8 MiB agregados e 8 MiB por anexo.
- Um milhão de palavras é apenas um cenário de teste, não requisito de produto. A hipótese de 5 milhões/40 MB não foi testada e excede os limites atuais. No teste de um milhão em macOS arm64/Python 3.13.7, `/usr/bin/time -l` mediu pico residente do processo de 382.189.568 bytes (~364 MiB) e peak memory footprint de 369.525.480 bytes (~352 MiB); inclui o processo de teste todo, não só o app.
- As imagens locais em `tests/fixtures/imagens/` são ignoradas pelo Git; não as force para um commit. A execução registrada usou duas imagens locais, mas nomes e conteúdo não são registrados nesta memória.
- O teste real de salvamento/reabertura foi adicionado: altera texto e metadado de uma imagem, salva, fecha e reabre o arquivo, comparando documento e bytes da imagem. O teste focado passou e a revisão cética não encontrou bloqueadores; ela observou que adulterar os bytes do PNG deixaria a fixture inválida, então o teste preserva os bytes originais da imagem. Pendências explícitas: troca de senha e adulteração/truncamento/cabeçalho/final de stream em arquivo real; validar o `.app` antes de uso real/distribuição. Repetir a medição de memória com o `.app` empacotado quando ele existir.
- Não há autorização permanente para commit ou integração. A branch deve poder ser integrada futuramente pela API desacoplada, sem substituir a UI.

**Estado do Git:** a bateria de um milhão de palavras foi registrada em `2eefba0`; a medição de memória e sua documentação, em `be94bd9`. Confirme `git status` e a branch antes de agir.

**Nota de atualidade:** este estado é um registro de retomada, não uma afirmação sobre o estado atual. Confira `git status`, `git branch --show-current`, dependências, testes e os documentos antes de relatar progresso.

## Como retomar uma tarefa

1. Leia estas instruções e o documento indicado no mapa para a área da tarefa.
2. Inspecione `git status` e a branch; preserve alterações existentes e não assuma que o último resumo ainda vale.
3. Siga os limites e as decisões registrados. Se encontrar contradições ou riscos, esclareça-os na documentação antes de ampliar o escopo.
4. Execute somente as validações relevantes e reporte exatamente o que foi ou não executado, incluindo testes ignorados e dependências indisponíveis.
5. Atualize esta memória quando a próxima sessão depender de uma decisão ou estado que mudou.
