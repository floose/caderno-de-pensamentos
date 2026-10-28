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
- [x] Medir Argon2id isoladamente no runtime Mac arm64 atual; perfil medido, com validação no `.app` ainda pendente.
- [x] Definir a distribuição inicial para uso próprio/testes; assinatura e notarização Apple ficam fora do escopo inicial.
- [x] Definir macOS 14 Sonoma como versão mínima do sistema.
- [x] Verificar que Tkinter, `_tkinter`, Tcl e Tk estão disponíveis no runtime Python.org usado pelo projeto.
- [ ] Confirmar as arquiteturas das dependências no `.app` `arm64` final.

## Etapas do projeto

### 1. Fechar requisitos e arquitetura

- [x] Ler o contexto inicial e inspecionar a versão pré-desenvolvida em `dist/`.
- [x] Escolher macOS e aplicativo `.app` como primeiro alvo.
- [x] Definir a versão mínima como macOS 14 Sonoma.
- [ ] Definir e validar o empacotamento de um `.app` `arm64`.
- [x] Usar um runtime Python com Tcl/Tk 8.6 incluído; não depender do Tcl/Tk antigo fornecido pelo sistema.
- [x] Fazer um protótipo curto da interface Tkinter antes de migrar as funções.
- [x] Definir o fluxo de abertura e seleção de bases descrito abaixo.
- [ ] Validar o empacotamento portátil do aplicativo `.app` para uso próprio em computador ou pendrive.

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
- [ ] Validar PyNaCl/libsodium, ciclo de cofre e perfil Argon2id no `.app` arm64 antes de usar dados pessoais.
- [ ] Integrar o cofre com textos, coleções, hashtags, datas, favoritos e imagens.
- [ ] Planejar backup e migração de versões do formato.
- [ ] Comunicar claramente que uma senha perdida não permite recuperar o conteúdo.

### 3. Implementar o núcleo do aplicativo

- [ ] Criar a estrutura Python e separar interface, domínio, criptografia e persistência.
- [ ] Implementar criar/abrir cofre e desbloquear com senha.
- [ ] Implementar a lembrança do caminho da última base e os fluxos de base localizada, ausente, movida, inválida e criação de nova base.
- [ ] Implementar salvamento automático no arquivo aberto, com tratamento de falhas.
- [ ] Implementar exportação e restauração de cópia de segurança criptografada.
- [ ] Implementar alteração de senha sem expor o conteúdo em disco.

### 4. Migrar as funções do caderno

- [ ] Implementar criação, leitura, edição e exclusão de textos.
- [ ] Implementar rascunhos e organização por coleção e hashtag.
- [ ] Implementar busca, filtros, favoritos e ordenação.
- [ ] Implementar editor e visualização Markdown, incluindo blocos de código e equações.
- [ ] Implementar anexar imagens por arquivo e colagem da área de transferência.
- [ ] Implementar calendário baseado nas datas dos textos.
- [ ] Revisar acessibilidade, mensagens de erro e comportamento ao fechar o aplicativo.

### 5. Testar e proteger os dados

- [x] Criar testes automatizados do núcleo para criptografia, schema, persistência, senha e integridade do arquivo; 48 testes passaram no runtime Python testado.
- [ ] Criar testes de integração da UI e regressão para operações de texto/imagem no `.app`.
- [ ] Criar testes de regressão para operações de texto, imagens, backup e migração.
- [x] Testar no núcleo falha pré-replace, retry e erro simulado de `fsync` do diretório.
- [ ] Testar no `.app` falta de espaço, encerramento inesperado e recuperação após falha.
- [ ] Confirmar que nenhum texto ou imagem em claro é gravado fora do cofre.
- [ ] Testar backup e restauração em uma base de exemplo.
- [x] Testar troca de senha real no backend com fixture sintética.
- [ ] Testar inicialização com a última base presente, ausente ou movida, escolha manual e criação de base; confirmar que senha e chave não são persistidas.

### 6. Empacotar e validar no macOS

- [ ] Gerar um `.app` independente do Python instalado na máquina, preferencialmente com PyInstaller em modo `onedir` e `--windowed`.
- [ ] Compactar o `.app` em ZIP para entrega e cópia para computador ou pendrive; validar extração e abertura sem instalador.
- [ ] Avaliar `--onefile --windowed` somente se um executável único for requisito literal após prototipagem; verificar o custo de extração e inicialização.
- [ ] Testar em uma instalação limpa do macOS dentro das versões suportadas.
- [ ] Validar em Apple Silicon, incluindo macOS 14 Sonoma e uma versão atual do macOS.
- [ ] Verificar abertura por duplo clique no Finder e acesso aos arquivos escolhidos.
- [ ] Medir tamanho e tempo de abertura; corrigir problemas de empacotamento.
- [ ] Decidir e, se necessário, configurar assinatura Developer ID e notarização Apple.
- [ ] Preparar instruções de uso, cópia de segurança e atualização do aplicativo.

#### Opções simples de empacotamento

1. **Recomendação inicial — `.app` PyInstaller `onedir` em ZIP:** coleta o runtime Python e as dependências no pacote `.app`; o ZIP facilita copiar o aplicativo sem instalador. O `.app` é internamente um pacote (diretório especial), embora apareça como um item no Finder. É a opção mais simples para inspecionar e depurar.
2. **`.app` em imagem de disco (`.dmg`):** entrega visual familiar no macOS, mas acrescenta criação e validação; não é necessária para uso próprio/testes.
3. **Executável único com `--onefile --windowed`:** produz um `.app` que extrai componentes temporários ao iniciar. PyInstaller considera essa combinação possível, mas não recomendada para macOS pelo custo de extração e limitações de assinatura com sandbox. Manter como alternativa somente se os testes mostrarem vantagem para uso em pendrive.

Produzir o pacote em um Mac arm64, validar as arquiteturas das dependências e testar a abertura após extrair o ZIP em outro local. A distribuição inicial é para uso próprio/testes, sem assinatura Developer ID ou notarização.

### Processo de desenvolvimento da UI e das funcionalidades

**Estratégia escolhida: fatias verticais por fluxo.** Cada entrega completa uma tarefa de ponta a ponta — interface, estado da aplicação e chamada ao cofre — para obter feedback de integração cedo. Foram consideradas duas alternativas: construir todas as telas com dados falsos antes de conectá-las, o que pode afastar o comportamento da API real; ou implementar o domínio de todas as funções antes da UI, o que atrasa o feedback de uso. Ambas podem servir a protótipos curtos, mas não serão o fluxo principal.

**Branch de trabalho:** `feature/ui-vault-integration`, criada a partir de `feature/vault-encryption`. A `main` permanece preservada durante a implementação. A integração com a `main` será feita em etapas revisáveis, após autorização explícita.

**Dados de desenvolvimento:** usar somente fixtures sintéticas versionadas, como `tests/fixtures/cofre_exemplo.json` e `tests/fixtures/pixel.png`. Não usar as imagens locais ignoradas de `tests/fixtures/imagens/` na UI, pois podem conter material privado. A interface chama a fachada `caderno.vault`; não importa o codec nem conhece detalhes internos do CPV1.

**Ordem das fatias:**

1. Criar, selecionar, abrir e fechar base; tratar base ausente, senha incorreta e arquivo inválido; guardar apenas o último caminho.
2. Listar, criar, editar e excluir uma nota; salvar, fechar e reabrir sem perder conteúdo.
3. Organizar notas em coleções e hashtags; suportar rascunhos, favoritos e datas.
4. Buscar, filtrar e ordenar notas; editar e visualizar Markdown.
5. Anexar e visualizar imagens; adicionar o calendário baseado nas datas das notas.
6. Completar backup/restauração, troca de senha na interface, acessibilidade e comportamento ao fechar o aplicativo.

### Ponto único para testar a UI (macOS)

Na raiz do projeto, dê duplo clique em [`testar_ui.command`](testar_ui.command). O script roda primeiro os testes automatizados focados em UI, preferências e contraste; se passarem, abre a janela real. Também pode ser iniciado com `./testar_ui.command` no terminal. Se falhar durante a preparação ou nos testes, o Terminal permanece aberto e mostra a mensagem.

O script usa o Python de `.venv` e mantém um perfil de teste sintético em `/private/tmp`, separado das preferências normais; ele cria e protege a própria subpasta do aplicativo com permissão `0700`, sem alterar a permissão da pasta indicada pelo ambiente. Define `CADERNO_CONFIG_DIR` para isolar preferências e `CADERNO_UI_TEST_PROFILE` para ativar a restrição de criar/abrir cofres dentro do perfil. O perfil persiste entre execuções para testar a lembrança da última base; os diálogos começam nessa pasta e a UI rejeita caminhos externos enquanto esse modo estiver ativo. Essa é uma proteção contra seleção acidental de arquivos reais, não uma sandbox contra hard links criados deliberadamente. Na primeira execução, escolha **Criar base**, salve `teste.cpv` na pasta sugerida e digite/confirme uma senha. Confira os textos brancos sobre verde escuro nos botões principais. Depois de abrir o cofre, **Fechar base** e **Escolher outra base** devem aparecer com fundo verde-claro e texto escuro, inclusive ao passar o ponteiro. O texto do botão desativado **Novo texto** deve continuar legível. Use `Tab` para percorrer os botões e conferir o indicador de foco.

Use **Fechar base**, tente abrir com uma senha incorreta e confirme que aparece um erro genérico e a base continua fechada. Repita com a senha correta. Feche o app e dê duplo clique no script outra vez: ele deve encontrar a última base e pedir a senha. Para um arquivo inválido, crie um arquivo de texto na pasta de teste e selecione-o pelo filtro **Todos os arquivos**; a mensagem de erro deve aparecer sem fechar a janela. O diretório usado é exibido no Terminal; não contém dados pessoais e pode ser removido pelo Finder após fechar o aplicativo.

Toda nova tela ou teste de UI deve ser conectado a este ponto único. Os callbacks Tkinter e o backend CPV1 real já passaram por um smoke test automatizado; a validação visual do `.app` empacotado continua pendente.

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
- **Estado da UI:** a janela Tkinter já permite criar, escolher, abrir e fechar uma base pela fachada `caderno.vault`. O aplicativo lembra somente o caminho em preferências locais; senha e chave permanecem fora delas. Há testes unitários de UI e preferências locais; a edição de notas e a validação da janela real no `.app` ainda não foram implementadas.
- **Estado do cofre:** CPV1 é um protótipo isolado; 48 testes do núcleo passaram com PyNaCl real e fixtures sintéticas, e o agente cético revisou a cobertura sem achar bloqueadores críticos/altos. A validação do `.app` e a integração com a UI continuam pendentes. Consulte [`Plano_de_desenvolvimento_criptografia.md`](Plano_de_desenvolvimento_criptografia.md).
- **Próximo marco:** conectar a criação e edição da primeira nota com persistência no cofre; em paralelo, preparar a prova `.app` arm64. O ciclo de abrir/criar/fechar tem testes unitários, mas ainda precisa de validação manual na janela empacotada. O processo e a sequência estão documentados em “Processo de desenvolvimento da UI e das funcionalidades”.
- **Atualizado em:** 2026-10-27.
