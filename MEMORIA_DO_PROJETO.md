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
- Branch atual para integração da UI: `feature/ui-vault-integration`, criada a partir do commit `dd3c523` da branch criptográfica; a `main` permanece sem alterações.
- Estratégia acordada para UI: fatias verticais com fixtures sintéticas, usando a fachada `caderno.vault`; prova do `.app` arm64 em paralelo. Sequência de features e processo design → testes técnicos → implementação → revisão cética constam no `Plano_do_projeto.md`.
- Estado da UI: `src/caderno/ui.py` implementa criar, escolher, abrir e fechar base. `src/caderno/preferences.py` guarda apenas o caminho da última base em Application Support com permissões restritas; senha/chave não são persistidas. Busca, ordenação e criação de nota continuam desativadas até suas fatias.
- Ponto único de UI: `testar_ui.command` na raiz roda os testes focados e inicia o aplicativo com perfil sintético em `/private/tmp/caderno-ui-test-<uid>`, separado das preferências usuais. Esse local evita o symlink `/var` que o núcleo rejeita. `CADERNO_CONFIG_DIR` isola preferências; a variável específica `CADERNO_UI_TEST_PROFILE` restringe criação/abertura a esse perfil e direciona os diálogos. Preferências ficam numa subpasta própria do app e não alteram permissões da raiz. A restrição evita seleção acidental de cofres fora do perfil, não hard links deliberados. O perfil persiste entre execuções para cobrir reabertura. Atualizar script/testes ao acrescentar funcionalidades de interface.
- Revisão cética inicial não encontrou bloqueadores; apontou troca de base, controles visuais sem ação, caminho inacessível, falha de durabilidade e contadores que exibiam zero. A implementação foi ajustada nesses pontos.
- Testes unitários mockam os diálogos/API do cofre e cobrem preferências sem senha/chave, permissões `0600`/`0700`, restrição do perfil de teste e contraste. A suíte completa passou com **65 testes em 61,87 s**. O launcher executou os 17 testes focados e inicializou a janela; ainda falta inspeção visual manual e o `.app` não foi empacotado.
- Auditoria de contraste encontrou texto secundário entre 2,3:1 e 3,2:1; o conjunto foi escurecido. Texto secundário agora fica acima de 4,6:1, texto branco no botão principal tem 7,57:1, controles recebem borda/foco legíveis e a navegação selecionada tem marcador lateral verde. O cético não encontrou outros pares textuais baixos e confirmou a correção do foco. `tests/test_ui_contrast.py`: testes de contraste passaram; construção de janela Tk real confirmou estilos/estados dos botões e do campo. Guia manual inclui inspeção de foco/leitura.
- Verificação adicional com widgets Tkinter reais, callbacks da UI e backend CPV1 real passou por criação, fechamento, senha incorreta, arquivo inválido, reabertura correta e restauração do último caminho. O teste usou pasta temporária sob `/private/tmp`; o arquivo permaneceu inalterado após senha errada e as preferências continham só o caminho. A automação de cliques via AppleScript foi bloqueada pela permissão de Acessibilidade do macOS, portanto o aspecto visual e os diálogos nativos ainda precisam de inspeção manual.
- A camada isolada está em `src/caderno/vault/`; ela deve continuar sem dependência da UI Tkinter.
- CPV1 usa PyNaCl/libsodium, Argon2id e `crypto_secretstream_xchacha20poly1305`; detalhes, limites, formato e garantias estão na decisão arquitetural.
- PyNaCl 1.6.2 está instalado no `.venv` do projeto. Suíte completa mais recente: **65 passed em 61,87 s**. Inclui schema e tipos estritos, adulteração real, troca de senha, spy pré-KDF, falha real pré-replace com retry/limpeza, sessão fechada sem KDF, conflito entre duas sessões, criação modo `0600`, busca de marcadores plaintext selecionados no temporário e testes de UI/preferências/contraste locais.
- O teste de escala gera em memória 200 notas sintéticas de 5.000 palavras cada, cifra e reabre o cofre com PyNaCl real e inclui as imagens locais de teste. O teste focado passou em 4,88 s; a suíte completa passou com 14 testes em 15,36 s. A fixture de um milhão de palavras não é salva no repositório.
- O limite CPV1 de manifesto foi aumentado de 1 MiB para 8 MiB para permitir esse cenário experimental. Os limites gerais permanecem: plaintext 10 MiB, arquivo 14 MiB, anexos 8 MiB agregados e 8 MiB por anexo.
- Um milhão de palavras é apenas um cenário de teste, não requisito de produto. A hipótese de 5 milhões/40 MB não foi testada e excede os limites atuais. No teste de um milhão em macOS arm64/Python 3.13.7, `/usr/bin/time -l` mediu pico residente do processo de 382.189.568 bytes (~364 MiB) e peak memory footprint de 369.525.480 bytes (~352 MiB); inclui o processo de teste todo, não só o app.
- As imagens locais em `tests/fixtures/imagens/` são ignoradas pelo Git; não as force para um commit. A execução registrada usou duas imagens locais, mas nomes e conteúdo não são registrados nesta memória.
- O teste real de salvamento/reabertura altera texto e metadado de imagem, preservando os bytes originais do PNG. Testes reais de adulteração e troca de senha também cobrem integridade sem publicar sessão parcial. Validar o `.app` antes de uso real/distribuição e repetir nele a medição de memória.
- O schema v1 foi documentado e validado antes de persistir ou devolver snapshots; ambas as fixtures passam sem migração. Inclui rejeição de campos/tipos/IDs/referências/datas inválidos, filename traversal (`.`/`..` incluídos), chaves JSON duplicadas e lista larga adversarial antes de expandir a fila. `VaultSnapshot` rejeita metadados com tipo inválido e só aceita bytes/bytearray/memoryview, copiando dados mutáveis. A cobertura de adulteração, troca de senha, falha pré-replace com retry, encerramento de sessão e conflito sequencial entre sessões reais está concluída. A revisão cética do núcleo não encontrou achados críticos/altos; apontou lacunas médias de parser autenticado, variações de framing e concorrência/crash entre processos, registradas no plano. O teste do temporário busca marcadores sintéticos selecionados; a inspeção cobre apenas o pacote vault, não UI/app. O benchmark Argon2id foi revisado sem bloqueadores; comparações futuras devem incluir aquecimento/contexto térmico e o script é Unix/macOS. A validação do `.app` e Macs lentos ainda falta.
- Não há autorização permanente para commit ou integração. A branch deve poder ser integrada futuramente pela API desacoplada, sem substituir a UI.

**Estado do Git:** a bateria de um milhão de palavras foi registrada em `2eefba0`; a medição de memória e sua documentação, em `be94bd9`. A implementação atual da UI está sem commit. Confirme `git status` e a branch antes de agir.

**Nota de atualidade:** este estado é um registro de retomada, não uma afirmação sobre o estado atual. Confira `git status`, `git branch --show-current`, dependências, testes e os documentos antes de relatar progresso.

## Como retomar uma tarefa

1. Leia estas instruções e o documento indicado no mapa para a área da tarefa.
2. Inspecione `git status` e a branch; preserve alterações existentes e não assuma que o último resumo ainda vale.
3. Siga os limites e as decisões registrados. Se encontrar contradições ou riscos, esclareça-os na documentação antes de ampliar o escopo.
4. Execute somente as validações relevantes e reporte exatamente o que foi ou não executado, incluindo testes ignorados e dependências indisponíveis.
5. Atualize esta memória quando a próxima sessão depender de uma decisão ou estado que mudou.
