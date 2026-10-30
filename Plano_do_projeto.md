# Plano do projeto — Caderno de Pensamentos

## Objetivo

Construir um caderno de conhecimento offline para Macs Apple Silicon (`arm64`), distribuído como um aplicativo `.app` que aparece no Finder e pode ser aberto sem instalar Python ou dependências. Os textos e anexos ficam em um arquivo de base de dados criptografado, escolhido e aberto pelo aplicativo.

## Decisões já tomadas

- [x] Priorizar uma base criptografada em arquivo, em vez de depender do armazenamento do navegador.
- [x] Restringir a primeira versão do aplicativo ao macOS.
- [x] Entregar o programa como aplicativo `.app` visível no Finder, sem exigir instalação de Python.
- [x] Usar Python como linguagem principal do programa.
- [x] Usar Tkinter como toolkit da interface gráfica.
- [x] Definir Apple Silicon (`arm64`) como arquitetura da primeira versão; Intel fica fora do escopo inicial.
- [x] Definir macOS 14 Sonoma como versão mínima da primeira versão.
- [x] Não fazer commits sem autorização.

## Decisões pendentes

- [x] Escolher o toolkit da interface gráfica: Tkinter.
- [x] Selecionar o formato CPV1 e a biblioteca PyNaCl/libsodium; ver [`Decisao_de_arquitetura_cofre.md`](Decisao_de_arquitetura_cofre.md).
- [x] Medir Argon2id no runtime Python e no `.app` arm64 atual; avaliação em Macs mais lentos continua pendente.
- [x] Definir a distribuição inicial para uso próprio/testes; assinatura e notarização Apple ficam fora do escopo inicial.
- [x] Definir macOS 14 Sonoma como versão mínima do sistema.
- [x] Verificar que Tkinter, `_tkinter`, Tcl e Tk estão disponíveis no runtime Python.org usado pelo projeto.
- [x] Confirmar que o executável e as dependências nativas principais da build atual são `arm64`; validação em uma máquina limpa continua pendente.

## Etapas do projeto

### 1. Fechar requisitos e arquitetura

- [x] Ler o contexto inicial e inspecionar a versão pré-desenvolvida em `dist/`.
- [x] Escolher macOS e aplicativo `.app` como primeiro alvo.
- [x] Definir a versão mínima como macOS 14 Sonoma.
- [x] Produzir e validar a build atual do empacotamento `.app` `arm64` com probes sintéticos de backend e UI; interação física com a janela principal continua pendente.
- [x] Usar um runtime Python com Tcl/Tk 8.6 incluído; não depender do Tcl/Tk antigo fornecido pelo sistema.
- [x] Fazer um protótipo curto da interface Tkinter antes de migrar as funções.
- [x] Definir o fluxo de abertura e seleção de bases descrito abaixo.
- [x] Compactar e abrir uma prova do `.app` em outro local no Mac atual; repetir a extração após esta build atual continua pendente.

#### Fluxo de abertura e seleção de bases

- Ao iniciar, informar qual foi a última base acessada e tentar localizar o arquivo salvo como último caminho utilizado.
- Se o arquivo existir, pedir a senha e tentar desbloqueá-lo. Nunca guardar a senha nem a chave nas preferências ou no aplicativo.
- Guardar somente o caminho da última base nas preferências locais do usuário, fora do pacote do aplicativo e da base criptografada.
- Se a base não for encontrada (por exemplo, se foi movida ou está em um pendrive desconectado), informar que ela não foi localizada e permitir escolher uma base existente em uma janela de arquivos ou criar uma nova.
- Senha incorreta, arquivo inválido ou falha de integridade devem produzir mensagens claras sem substituir nem modificar a base.
- Para criar uma base, pedir nome, local do arquivo, senha e confirmação; atualizar o caminho da última base somente após criação bem-sucedida.
- Após abrir ou criar uma base com sucesso, atualizar o caminho da última base. A pessoa pode escolher outra base a qualquer momento pelo aplicativo.

### 2. Projetar o arquivo criptografado

- [x] Definir formato versionado, KDF, cifra autenticada, serialização e limites iniciais — ver [`Decisao_de_arquitetura_cofre.md`](Decisao_de_arquitetura_cofre.md).
- [x] Implementar um núcleo de cofre isolado da interface — protótipo em `src/caderno/vault/`.
- [x] Exercitar o backend PyNaCl real com fixtures sintéticas, inclusive um milhão de palavras e imagens.
- [x] Testar corrupção, salvamento/reabertura e troca de senha pelo backend criptográfico real com fixtures sintéticas; medir Argon2id no runtime Mac atual. Resultados e limites em [`Plano_de_desenvolvimento_criptografia.md`](Plano_de_desenvolvimento_criptografia.md).
- [x] Validar automaticamente o ciclo integrado de cofre pela UI Tk empacotada e medir Argon2id no runtime PyInstaller. O probe usa o modal de senha real e gera Enter no campo; o `.app` principal também iniciou em perfil sintético. Interação física com a janela principal e instalação limpa continuam pendentes antes de uso com dados pessoais.
- [x] Integrar o cofre com texto, coleções, hashtags, favoritos e exibição das datas da nota na UI; anexos e calendário seguem pendentes.
- [ ] Planejar backup e migração de versões do formato.
- [ ] Comunicar claramente que uma senha perdida não permite recuperar o conteúdo.

### 3. Implementar o núcleo do aplicativo

- [x] Criar a estrutura Python e separar interface, domínio, criptografia e persistência.
- [x] Implementar criar/abrir cofre e desbloquear com senha.
- [x] Implementar a lembrança do caminho da última base e os fluxos de base localizada, ausente, movida, inválida e criação de nova base; os probes empacotados atuais passaram nos caminhos sintéticos cobertos.
- [x] Implementar salvamento explícito no arquivo aberto, com rascunhos locais, proteção ao fechar/trocar e tratamento de falhas.
- [ ] Implementar exportação e restauração de cópia de segurança criptografada.
- [ ] Implementar alteração de senha sem expor o conteúdo em disco.

### 4. Migrar as funções do caderno

- [x] Implementar criação, leitura e edição de notas.
- [ ] Implementar exclusão segura de notas, com confirmação, tratamento de rascunhos pendentes e remoção de anexos associados.
- [x] Implementar rascunhos e organização por coleção e hashtag.
- [x] Implementar busca por título, conteúdo, coleção e hashtags; a consulta é temporária, combina todos os termos e preserva o rascunho enquanto filtra.
- [x] Implementar filtros temporários por coleção e hashtag, combináveis com a busca.
- [x] Implementar opções de ordenação por data de edição, criação e título, em ambos os sentidos.
- [x] Implementar favoritos persistentes no editor, protegidos por salvar/descartar/cancelar, e filtro combinável com coleção, hashtag e busca.
- [x] Implementar modo de foco que expande a escrita na janela atual e restaura a navegação sem perder o rascunho.
- [x] Aplicar margens laterais na cor do editor ao editor e à barra de rolagem, sem linha de contorno, no modo expandido; restaurar o contorno ao sair e dar suporte a Enter do teclado numérico. Testes unitários e probe Tk real cobrem os estados.
- [x] Exibir datas de criação e última modificação no editor e proteger botões contra compressão horizontal com largura mínima e quebra de nomes longos de coleção.
- [x] Adicionar ⌘N para criar nota na coleção selecionada, ⌃⌘E para alternar o modo de foco, o atalho no rótulo do botão, Enter no campo de senha e horário às datas do editor.
- [ ] Implementar editor e visualização Markdown, incluindo blocos de código e equações; preservar o corpo Markdown já armazenado sem alterar o schema nesta etapa.
- [ ] Implementar anexar imagens por arquivo e colagem da área de transferência.
- [ ] Implementar calendário baseado nas datas dos textos.
- [ ] Revisar acessibilidade, mensagens de erro e comportamento ao fechar o aplicativo.

### 5. Testar e proteger os dados

- [x] Criar testes automatizados do núcleo para criptografia, schema, persistência, senha e integridade do arquivo; resultados atuais e lacunas estão em [`Plano_de_desenvolvimento_criptografia.md`](Plano_de_desenvolvimento_criptografia.md).
- [x] Cobrir criação, edição, salvamento, reabertura e senha incorreta/correta pela `CadernoApp` em probe Tk empacotado; o probe gera Enter no campo real de senha.
- [ ] Cobrir anexos pela UI e interação física no bundle principal; os anexos estão cobertos no núcleo, não pela UI.
- [ ] Criar testes de regressão para operações de texto, imagens, backup e migração.
- [x] Testar no núcleo falha pré-replace, retry e erro simulado de `fsync` do diretório.
- [ ] Testar no `.app` falta de espaço, encerramento inesperado e recuperação após falha.
- [ ] Confirmar que nenhum texto ou imagem em claro é gravado fora do cofre.
- [ ] Testar backup e restauração em uma base de exemplo.
- [x] Testar troca de senha real no backend com fixture sintética.
- [ ] Testar inicialização com a última base presente, ausente ou movida, escolha manual e criação de base; confirmar que senha e chave não são persistidas.

### 6. Empacotar e validar no macOS

- [x] Gerar uma prova local do `.app` independente do Python instalado na máquina, com PyInstaller em modo `onedir` e `--windowed`; isso ainda não conclui a validação de distribuição.
- [x] Compactar a prova do `.app` em ZIP, extrair em outra pasta e abrir o executável sem instalador no Mac atual; repetir com a build atual continua pendente.
- [ ] Avaliar `--onefile --windowed` somente se um executável único for requisito literal após prototipagem; verificar o custo de extração e inicialização.
- [ ] Testar em uma instalação limpa do macOS dentro das versões suportadas.
- [x] Validar a prova inicial em Apple Silicon no Mac atual. macOS 14, versões antigas, instalação limpa e outros Macs ficam adiados para distribuição.
- [ ] Verificar abertura por duplo clique no Finder e acesso aos arquivos escolhidos.
- [x] Medir tamanho da prova inicial (~27 MB no `.app`, ~13 MB no ZIP) e corrigir problemas encontrados. Repetir com a build atual continua pendente.
- [ ] Decidir e, se necessário, configurar assinatura Developer ID e notarização Apple.
- [ ] Preparar instruções de uso, cópia de segurança e atualização do aplicativo.

#### Opções simples de empacotamento

1. **Recomendação inicial — `.app` PyInstaller `onedir` em ZIP:** coleta o runtime Python e as dependências no pacote `.app`; o ZIP facilita copiar o aplicativo sem instalador. O `.app` é internamente um pacote (diretório especial), embora apareça como um item no Finder. É a opção mais simples para inspecionar e depurar.
2. **`.app` em imagem de disco (`.dmg`):** entrega visual familiar no macOS, mas acrescenta criação e validação; não é necessária para uso próprio/testes.
3. **Executável único com `--onefile --windowed`:** produz um `.app` que extrai componentes temporários ao iniciar. PyInstaller considera essa combinação possível, mas não recomendada para macOS pelo custo de extração e limitações de assinatura com sandbox. Manter como alternativa somente se os testes mostrarem vantagem para uso em pendrive.

Produzir o pacote em um Mac arm64, validar as arquiteturas das dependências e testar a abertura após extrair o ZIP em outro local. A distribuição inicial é para uso próprio/testes, sem assinatura Developer ID ou notarização.

#### Resultado da prova inicial do `.app` arm64

- Build reproduzível em [`scripts/build_macos_app.command`](scripts/build_macos_app.command), com entry point em [`scripts/packaged_entry.py`](scripts/packaged_entry.py); artefatos ficam em `build/macos-arm64/`, ignorado pelo Git.
- PyInstaller não encontrou sozinho as importações tardias do cofre. A build precisa coletar `nacl` e `cffi`; sem isso, faltaram primeiro `_sodium.abi3.so` e depois `_cffi_backend`.
- Empacotar `src/caderno/__main__.py` como script isolado perdeu o contexto do pacote e falhou com `No module named 'ui'`. O entry point dedicado chama `caderno.__main__.main()`.
- No macOS 26.6.2 arm64, Python 3.13.7 e PyInstaller 6.22.3, o `.app` de prova foi gerado com cerca de 27 MB. O executável, `_sodium`, `_cffi_backend` e `_tkinter` são arm64; Tcl/Tk foi incluído. A janela inicial do app abriu pelo LaunchServices.
- [`scripts/package_vault_smoke.py`](scripts/package_vault_smoke.py), compilado como executável auxiliar com as mesmas coletas, criou, abriu, editou, salvou e reabriu um cofre sintético com backend real. Isso valida a coleta nativa e o ciclo CPV1 nesse runtime empacotado, mas ainda não exercita esse ciclo através da UI do próprio `.app`.
- [`scripts/package_ui_smoke.py`](scripts/package_ui_smoke.py) roda `CadernoApp` e widgets Tk reais em um app auxiliar PyInstaller: cria cofre sintético pelos callbacks da UI, salva nota/hashtags, rejeita duplicata, fecha e reabre para confirmar persistência. O build chama o probe via LaunchServices e falha se o marcador de sucesso não for gravado. A janela principal do `.app` foi aberta visível em perfil sintético; o probe automatiza callbacks no runtime empacotado, não cliques ou digitação física na janela principal.
- Um aceite separado da UI do código-fonte passou em janela Tk real com cofre CPV1 sintético: criação de coleção pelo callback, edição de nota, `⌘S` gerado no campo de hashtags, `Escape` com Cancelar e Descartar, e fechamento/reabertura com coleção e hashtags preservadas. A janela reportou estado normal e visível. O nome da coleção foi fornecido pelo harness ao diálogo; a interação física com o diálogo e o ciclo pelo bundle `.app` ainda não foram validados.
- O `.app` foi compactado em ZIP (~13 MB), extraído em outra pasta temporária e seu executável arm64 foi iniciado no Mac atual; a janela bloqueada ficou visível e normal. O executável declara `minos 11.0`, mas isso não valida essa versão nem macOS 14.
- A pedido do usuário, não faremos downgrade nem testaremos sistemas antigos nesta etapa; o alvo planejado macOS 14 permanece documentado, mas sua validação, instalação limpa, duplo clique no Finder e compatibilidade em outros Macs ficam adiados até a distribuição ser relevante. Ainda falta automatizar interação física com a janela principal e seus modais.
- A revisão cética reproduziu defeitos de UI que foram corrigidos com regressões: o seletor recebe `⌘S`/`Escape`; rótulos permanecem únicos mesmo com colisões entre sufixos gerados e nomes literais; tentativas de criar nomes duplicados mostram alerta e não persistem outra coleção.
- Alertas de erro/aviso/informação e a entrada de nome de coleção usam `Toplevel` próprios do app, com estilo compartilhado e confirmação/cancelamento por teclado. Senha e alterações pendentes também usam modais próprios. A suíte cobre tema, modalidade e atalhos; o usuário confirmou a aparência do alerta de duplicidade. O novo modal de texto deve ser conferido pela janela real via `testar_ui.command`.
- Os seletores de abrir/criar base e coleção agora são janelas do próprio app, sem `filedialog` ou `ttk`; a navegação permite filtrar `.cpv` e respeita a raiz do perfil sintético. As preferências selecionam o diretório convencional de cada plataforma, com override para testes.
- 142 testes completos passaram. A build arm64 atual e os probes empacotados passaram: fluxo de notas, senha errada/correta por Enter no campo real, troca de senha no backend, persistência, duplicidade e medição Argon2id (mediana 2,4367 s em 3 amostras; RSS de pico do processo 310.886.400 B, sem isolamento da KDF). O `.app` principal ficou ativo por três segundos em perfil sintético; assinatura válida, executável e dependências principais arm64, tamanho ~33 MB. A interação física no bundle principal, instalação limpa e compatibilidade entre versões do macOS continuam pendentes.

### Processo de desenvolvimento da UI e das funcionalidades

**Estratégia escolhida: fatias verticais por fluxo.** Cada entrega completa uma tarefa de ponta a ponta — interface, estado da aplicação e chamada ao cofre — para obter feedback de integração cedo. Foram consideradas duas alternativas: construir todas as telas com dados falsos antes de conectá-las, o que pode afastar o comportamento da API real; ou implementar o domínio de todas as funções antes da UI, o que atrasa o feedback de uso. Ambas podem servir a protótipos curtos, mas não serão o fluxo principal.

**Branch de trabalho:** `feature/ui-vault-integration`, criada a partir de `feature/vault-encryption`. A `main` permanece preservada durante a implementação. A integração com a `main` será feita em etapas revisáveis, após autorização explícita.

**Dados de desenvolvimento:** usar somente fixtures sintéticas versionadas, como `tests/fixtures/cofre_exemplo.json` e `tests/fixtures/pixel.png`. Não usar as imagens locais ignoradas de `tests/fixtures/imagens/` na UI, pois podem conter material privado. A interface chama a fachada `caderno.vault`; não importa o codec nem conhece detalhes internos do CPV1.

**Ordem das fatias:**

1. Criar, selecionar, abrir e fechar base; tratar base ausente, senha incorreta e arquivo inválido; guardar apenas o último caminho.
2. [x] Listar, criar e editar notas; salvar, fechar e reabrir sem perder conteúdo. Excluir notas ainda está pendente.
3. [x] Organizar notas em coleções e hashtags; suportar rascunhos, favoritos persistentes, modo de foco e exibição de datas e horários.
4. [x] Buscar, filtrar e ordenar notas; Markdown continua pendente.
5. Anexar e visualizar imagens; adicionar o calendário baseado nas datas das notas.
6. Completar backup/restauração, troca de senha na interface, acessibilidade e comportamento ao fechar o aplicativo.

**Sequência recomendada para retomada:** validar primeiro o ciclo do `.app` atual com dados sintéticos; depois implementar exclusão segura de notas e anexos associados; em seguida Markdown; depois anexos na UI; então backup/restauração e plano de migração; por fim calendário e revisão de acessibilidade. Compatibilidade com outras versões do macOS, instalação limpa, assinatura e distribuição continuam adiadas para quando forem necessárias.

### Ponto único para testar a UI (macOS)

Na raiz do projeto, dê duplo clique em [`testar_ui.command`](testar_ui.command). O script roda primeiro os testes automatizados focados em UI, preferências, contraste e medidas de tipografia/layout; se passarem, abre a janela real. Também pode ser iniciado com `./testar_ui.command` no terminal. Se falhar durante a preparação ou nos testes, o Terminal permanece aberto e mostra a mensagem.

O script usa o Python de `.venv` e mantém um perfil de teste sintético em `/private/tmp`, separado das preferências normais; ele cria e protege a própria subpasta do aplicativo com permissão `0700`, sem alterar a permissão da pasta indicada pelo ambiente. Define `CADERNO_CONFIG_DIR` para isolar preferências e `CADERNO_UI_TEST_PROFILE` para ativar a restrição de criar/abrir cofres dentro do perfil. O perfil persiste entre execuções para testar a lembrança da última base; os diálogos começam nessa pasta e a UI rejeita caminhos externos enquanto esse modo estiver ativo. Essa é uma proteção contra seleção acidental de arquivos reais, não uma sandbox contra hard links criados deliberadamente. Na primeira execução, escolha **Criar base**, salve `teste.cpv` na pasta sugerida e digite/confirme uma senha. Os botões principais devem ter texto escuro sobre verde-claro. Depois de abrir o cofre, **Fechar base** e **Escolher outra base** devem aparecer com texto escuro sobre um fundo neutro claro, inclusive ao passar o ponteiro. Confirme que os textos permanecem inteiros ao redimensionar a janela até o mínimo de 900 × 620; confira título, busca, navegação e botões. **Novo texto** deve estar legível e desativado sem cofre; depois de abrir, deve ficar ativo. Use `Tab` para percorrer os botões e conferir o indicador de foco.

Nos prompts de senha, confira o campo mascarado e os botões **Cancelar** e de ação (**Continuar**, **Confirmar** ou **Abrir base**), com o mesmo tema da janela principal. **Enter** confirma e **Escape** cancela.

Com uma base de teste aberta, use o **+** ao lado de **Coleções** para criar uma coleção. O campo de nome e os alertas devem seguir o tema do Caderno; **Enter/Criar** confirma e **Escape** cancela a entrada. Tente criar outra coleção com o mesmo nome, também variando maiúsculas/minúsculas: deve aparecer um alerta próprio com o nome existente, sem criar a coleção. Use **Novo texto**, preencha título e corpo, escolha a coleção no seletor e digite hashtags separadas por vírgula (por exemplo, `#ideia, #projeto`). Teste **⌘S** e **Escape** enquanto o seletor está focado. Salve pelo botão ou com **⌘S**. Altere o conteúdo ou os metadados e tente fechar a base: o diálogo oferece **Salvar**, **Descartar** e **Cancelar**; cancelar mantém o rascunho, descartar restaura a versão persistida e salvar grava a nota e seus metadados. Feche e reabra a base sintética e confirme que coleção e hashtags continuam na nota. O título é obrigatório; hashtags acima de 256 caracteres devem ser rejeitadas sem perder o rascunho.

Use **Fechar base**, tente abrir com uma senha incorreta e confirme que aparece um erro genérico e a base continua fechada. Repita com a senha correta. Feche o app e dê duplo clique no script outra vez: ele deve encontrar a última base e pedir a senha. Para um arquivo inválido, crie um arquivo de texto na pasta de teste e selecione-o pelo filtro **Todos os arquivos**; a mensagem de erro deve aparecer sem fechar a janela. O diretório usado é exibido no Terminal; não contém dados pessoais e pode ser removido pelo Finder após fechar o aplicativo.

Toda nova tela ou teste de UI deve ser conectado a este ponto único. Os callbacks Tkinter e o backend CPV1 real passaram por testes automatizados e por um aceite com janela Tk real. A tela bloqueada de uma prova do `.app` extraído abriu no Mac atual; a build atual passou pelos probes integrados sintéticos, mas ainda falta interação física com sua janela principal.

Uma prova mínima do `.app` arm64, com Tkinter e PyNaCl, avança em paralelo à primeira fatia para identificar cedo problemas de empacotamento. O `.app` integrado precisa passar o ciclo de criar, abrir, salvar, reabrir e trocar senha antes do uso com dados pessoais.

**Ciclo dos agentes por fatia:**

- O agente de design descreve o fluxo, estados vazios/carregando/erro, protótipo visual e critérios de aceite.
- O agente técnico de UI propõe os testes automatizados antes da implementação, cobrindo a regra ou fluxo e as falhas relevantes com fixtures sintéticas.
- O agente implementador conecta a tela à fachada pública e executa os testes da fatia.
- O agente cético tenta encontrar inconsistências e lacunas; a fatia só termina quando achados críticos/altos forem resolvidos e os critérios de aceite passarem.

**Gate de dados reais:** não usar dados pessoais até o `.app` arm64 e o fluxo integrado serem validados, erros de abertura serem genéricos, backup/restauração e falhas de persistência terem testes, e a UI não guardar senha/chave nem gravar conteúdo em claro fora do cofre.

## Gantt ASCII

Estimativa relativa em semanas de trabalho; não representa datas prometidas. Atualizar os marcadores conforme o progresso real.

```text
Etapa / Semana                         S1 S2 S3 S4 S5 S6 S7 S8 S9 S10
Requisitos e arquitetura               ██ ██ .. .. .. .. .. .. .. ..
Protótipo da interface Tkinter         .. ██ ██ .. .. .. .. .. .. ..
Formato do cofre e criptografia        .. ██ ██ .. .. .. .. .. .. ..
Núcleo Python e persistência           .. .. ██ ██ ██ .. .. .. .. ..
Interface e funções do caderno          .. .. .. ██ ██ ██ ██ .. .. ..
Testes automatizados e regressões       .. .. .. .. ██ ██ ██ ██ .. ..
Empacotamento do aplicativo macOS      .. .. .. .. .. .. ██ ██ .. ..
Validação limpa e ajustes finais        .. .. .. .. .. .. .. ██ ██ ..
Documentação e pacote de distribuição  .. .. .. .. .. .. .. .. ██ ██
Legenda: ██ trabalho previsto; .. sem atividade prevista.
```

## Acompanhamento

- **Estado atual:** primeira versão restrita a Apple Silicon (`arm64`), macOS 14 Sonoma ou posterior, Tkinter e distribuição inicial para uso próprio/testes.
- **Estado da UI:** criar, escolher, abrir e fechar base estão implementados. Notas podem ser listadas, criadas e editadas com rascunho local e salvamento explícito; ⌘N cria nota na coleção atual, ⌃⌘E alterna o modo de foco e Enter no teclado numérico cria uma quebra de linha no editor. Exclusão de notas, Markdown, anexos pela UI, calendário e backup/restauração permanecem pendentes. Coleção, hashtags e favoritos são editáveis e persistidos, e o fechamento protege alterações pendentes inclusive nos metadados. O modo de foco amplia a escrita com margens laterais na cor do editor, preserva o rascunho e retorna a campos inválidos quando a validação falha. O editor exibe data e hora de criação e última modificação, e mantém largura mínima para preservar os controles. Busca, filtros por coleção/hashtag/favoritos e ordenação por data de edição, criação ou título estão implementados. Alertas, entradas de texto, filtros, seletores de coleção, ordenação e navegação de bases usam modais próprios do app. Os 142 testes completos e a build arm64 anterior passaram. Nesta alteração, passaram 84 testes focados e o probe Tk real cobriu a cor e restauração das margens, KP_Enter, salvamento e rascunho; a janela visível deve ser conferida pelo roteiro em [`testar_ui.command`](testar_ui.command). Instalação limpa e compatibilidade entre versões continuam pendentes.
- **Estado do cofre:** protótipo CPV1 isolado, testado com backend PyNaCl e fixtures sintéticas. Resultados e pendências atuais estão em [`Plano_de_desenvolvimento_criptografia.md`](Plano_de_desenvolvimento_criptografia.md).
- **Próximo marco:** implementar exclusão segura de notas antes de Markdown. A validação automatizada da build arm64 atual passou com dados sintéticos; ainda falta interação física na janela do bundle principal, além de instalação limpa e compatibilidade de sistemas, que ficam adiadas para distribuição.
- **Atualizado em:** 2026-10-30.
