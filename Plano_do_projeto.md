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
- [ ] Medir Argon2id isoladamente no Mac alvo e validar o perfil no `.app` arm64.
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
- [ ] Testar corrupção e salvamento/troca de senha no fluxo criptográfico real; medir Argon2id isoladamente e validar o `.app` arm64 antes de usar dados reais.
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

- [ ] Criar testes automatizados para criptografia, persistência, senha e integridade do arquivo.
- [ ] Criar testes de regressão para operações de texto, imagens, backup e migração.
- [ ] Testar falhas durante gravação, falta de espaço e encerramento inesperado.
- [ ] Confirmar que nenhum texto ou imagem em claro é gravado fora do cofre.
- [ ] Testar recuperação de cópia e troca de senha em uma base de exemplo.
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
- **Estado do protótipo:** a primeira janela visual Tkinter está implementada em `src/caderno/ui.py`; os controles ainda são apenas visuais.
- **Estado do cofre:** CPV1 está implementado como protótipo isolado; o backend real passou com fixtures sintéticas. Testes de estados de falha/persistência e validação do `.app` continuam pendentes. Consulte [`Plano_de_desenvolvimento_criptografia.md`](Plano_de_desenvolvimento_criptografia.md).
- **Próximo marco:** completar testes reais de adulteração, salvamento e troca de senha; medir Argon2id isoladamente e validar o `.app` arm64 antes da integração visual.
- **Atualizado em:** 2026-10-24.
