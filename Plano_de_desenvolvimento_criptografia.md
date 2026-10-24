# Plano de desenvolvimento do banco criptografado

**Branch:** `feature/vault-encryption`
**Estado:** protótipo CPV1 implementado; o backend criptográfico real ainda não foi validado.

Este é o roteiro de execução para o agente desenvolvedor e o agente cético. A especificação técnica única está em [`Decisao_de_arquitetura_cofre.md`](Decisao_de_arquitetura_cofre.md). O plano cobre o armazenamento local de textos e imagens e a função que protege o arquivo inteiro com senha.

## Resumo em linguagem simples

O programa já tem código que organiza textos e imagens num arquivo e tenta protegê-los com senha. A senha é usada para criar uma chave; uma biblioteca pronta cifra o conteúdo e também detecta alterações no arquivo. A interface ainda não usa esse recurso.

Isso ainda é um protótipo: PyNaCl 1.6.2 está instalado no ambiente do projeto e o fluxo real passou com textos e imagens sintéticos, inclusive uma amostra de um milhão de palavras. Não testamos um arquivo de 40 MB; esse foi apenas um cenário hipotético, não um requisito. O aplicativo Mac também não foi validado. Enquanto o caderno estiver aberto, o conteúdo e a chave precisam existir na memória do programa.

**O que falta agora:** continuar os testes com dados sintéticos, medir o desempenho e a memória em volumes relevantes para o uso esperado e conferir a biblioteca no aplicativo Mac. O agente desenvolvedor implementa esses passos e o agente cético procura falhas.

## Objetivo da primeira entrega

Comprovar, antes de integrar a interface, que a fixture sintética de dois textos e uma imagem pode ser criada, aberta, editada, salva e reaberta como um único arquivo criptografado. Senha errada, adulteração, truncamento e falha de gravação devem falhar sem entregar conteúdo parcial nem destruir uma versão válida.

## Limites de trabalho

- Trabalhar em `feature/vault-encryption`, dentro de `src/caderno/vault/` e dos testes relacionados. Não alterar `src/caderno/ui.py` nesta etapa.
- Manter a API independente da interface: `create_vault`, `open_vault` e `VaultSession`.
- Usar apenas conteúdo sintético de `tests/fixtures/`; nunca adicionar dados pessoais, senha, chave, plaintext de usuário ou cofre descriptografado ao repositório.
- Não implementar primitivas criptográficas próprias; mudanças de formato ou parâmetros devem ser registradas e criticadas antes de codificar.
- Não fazer commit, merge, rebase ou push sem autorização explícita.

## Etapas de desenvolvimento

### 1. Validar o caminho criptográfico real

- [ ] Disponibilizar PyNaCl 1.6.2/libsodium no ambiente autorizado e confirmar que Argon2id e `secretstream` usados pelo código estão presentes.
- [ ] Executar um round-trip real da fixture: criar arquivo, fechar sessão, abrir e comparar documento e bytes da imagem.
- [ ] Confirmar que o arquivo cifrado não contém título, texto, nome de imagem nem sequência Base64 da fixture.
- [ ] Testar senha errada, alteração de ciphertext, truncamento, remoção de frame final e bytes extras após o final.
- [ ] Medir tempo e pico de memória do perfil Argon2id CPV1 no Mac arm64 alvo; registrar hardware/versão de runtime sem incluir identificadores pessoais da máquina.

**Saída da etapa:** teste criptográfico deixa de ser ignorado; perfil tem medição repetível. Se PyNaCl exigir instalação fora das permissões disponíveis, parar apenas essa etapa e pedir autorização, sem contornar a restrição.

### 2. Fechar o contrato dos dados

- [ ] Usar a fixture existente para documentar e validar o schema v1: coleções, textos, hashtags, datas, favoritos e referências a anexos.
- [ ] Validar campos obrigatórios, tipos, IDs únicos, referências entre texto/coleção/anexo, datas e limites antes de publicar um `VaultSnapshot`.
- [ ] Garantir compatibilidade com imagens binárias sem Base64 e validar nome, MIME type, tamanho por anexo e agregado.
- [ ] Adicionar testes para schema válido, campos/tipos inválidos, referências quebradas, IDs duplicados, limites e versão futura desconhecida.

**Saída da etapa:** a camada de persistência recebe e devolve um snapshot coerente; JSON malformado ou schema inválido nunca vira estado parcialmente carregado.

### 3. Fechar criação, salvamento e troca de senha

- [ ] Testar `create_vault` sem sobrescrever arquivo existente e com permissões restritas.
- [ ] Testar `save`/reabertura, troca de senha, senha antiga rejeitada e senha nova aceita.
- [ ] Simular falhas antes da substituição atômica e confirmar que o arquivo anterior e o snapshot da sessão permanecem coerentes.
- [ ] Testar sessão fechada, conflito de sessão obsoleta e falha de `fsync` do diretório após substituição.
- [ ] Confirmar que senha, chave e plaintext não aparecem em arquivo temporário, logs ou preferências.

**Saída da etapa:** operações persistentes têm comportamento previsível diante de falhas; salvamento só é reportado como concluído após a substituição.

### 4. Revisão independente e correções

- [ ] O agente cético revisa a decisão, o diff completo e os testes após cada marco.
- [ ] Registrar cada achado com severidade, cenário, arquivo/local e correção sugerida.
- [ ] O desenvolvedor corrige achados críticos/altos e solicita nova revisão; não declarar pronto enquanto houver algum aberto.
- [ ] Revisar em particular KDF e limites antes da derivação, autenticação do stream final, vazamento de plaintext, schema, atomicidade, dependência nativa e afirmações de segurança.

**Saída da etapa:** revisão sem achados críticos/altos abertos, acompanhada dos testes executados e limitações restantes.

### 5. Preparar integração, sem acoplar o núcleo à UI

- [ ] Validar importação e execução offline do pacote `caderno.vault`.
- [ ] Manter docstrings nas APIs públicas e nas etapas criptográficas/de persistência críticas; explicitar propósito, contrato, falhas e garantias sem narrar cada linha.
- [ ] Confirmar que a dependência PyNaCl/libsodium entra corretamente no `.app` macOS arm64.
- [ ] Planejar integração posterior para criar/selecionar/desbloquear base e salvar snapshots; a UI traduz erros de domínio em mensagens, sem conhecer o formato CPV1.
- [ ] Só integrar depois que o round-trip real, os testes de persistência, o benchmark e a revisão cética forem concluídos.

## Papéis dos agentes

**Desenvolvedor:** tem autonomia para implementar, reorganizar módulos e adicionar testes dentro dos limites acima. Pode escolher detalhes internos sem pedir aprovação, mas deve registrar qualquer alteração à especificação CPV1 antes de implementá-la.

**Cético:** trabalha na mesma branch, mas não edita arquivos durante a revisão. Tenta refutar as garantias, testa cenários de falha e aponta lacunas mesmo quando a suíte passa.

**Ciclo:** desenvolvedor implementa um marco → cético revisa → desenvolvedor corrige → cético confirma. A coordenação relata o resultado; commit e integração continuam sob autorização da pessoa responsável.

## Estado de partida

- A fachada em `src/caderno/vault/` já oferece `create_vault(path, password, snapshot)`, `open_vault(path, password)` e `VaultSession` com `snapshot`, `save`, `change_password` e `close`.
- `tests/fixtures/cofre_exemplo.json` contém duas notas sintéticas para testes rápidos; `tests/fixtures/cofre_volume.json` contém cinco textos sintéticos de 5.000 palavras cada para teste de volume. A pasta `tests/fixtures/imagens/` recebe imagens de teste fornecidas pela pessoa responsável.
- `tests/fixtures/pixel.png` continua sendo uma imagem sintética pequena para os testes automatizados existentes.
- O cenário hipotético de 40 MB excede os limites implementados; não é requisito atual nem capacidade validada. Um milhão de palavras é coberto como cenário experimental, sem compromisso de capacidade de produto.
- O teste de volume cifra e reabre os cinco textos (25.000 palavras) e as imagens encontradas em `tests/fixtures/imagens/`; quando a pasta está vazia, usa `pixel.png` como fallback sintético. As imagens colocadas nessa pasta são ignoradas pelo Git para evitar versionar arquivos possivelmente pessoais.
- Última execução com as duas imagens locais (133.863 bytes no total): o teste de um milhão de palavras passou em **4,77 s**; suíte `PYTHONPATH=src .venv/bin/python -m pytest -q -ra tests/test_vault.py` — **14 aprovados, nenhum ignorado, em 15,36 s**. A bateria gera as 200 notas em memória, cifra e reabre com PyNaCl real e compara o documento e os anexos. Isso valida essa amostra sintética, não o cenário hipotético de 5 milhões de palavras.
- `compileall` passou em execução anterior; repetir após mudanças relevantes. `git diff --check` também deve ser repetido antes do commit.
- A leitura acumula plaintext em memória até autenticar o stream completo, sob limites provisórios CPV1. A medição anterior de 28,3 MB em `tracemalloc` não inclui memória nativa ou o runtime.
- O teste de um milhão de palavras usa manifesto de até 8 MiB; os limites gerais permanecem 10 MiB para plaintext e 14 MiB para o arquivo, com até 8 MiB agregados de anexos. A medição passou com as duas imagens locais atuais, mas não mede pico de memória nem desempenho no Mac arm64. O cenário de 40 MB continua fora do escopo.
- Ainda não há benchmark Argon2id no Mac arm64 nem build `.app`.

## Pendências sinalizadas após o teste de um milhão

- [ ] Medir o pico de memória durante a criação e a abertura do cofre de um milhão de palavras.
- [ ] Testar salvamento real de alterações e reabertura do arquivo salvo.
- [ ] Testar troca de senha real: senha nova abre o cofre e senha antiga é rejeitada.
- [ ] Testar adulteração de ciphertext/cabeçalho, truncamento, ausência do marcador final e bytes extras em arquivos cifrados reais.
- [ ] Validar o benchmark Argon2id e o `.app` no Mac arm64.

Não usar dados pessoais até essas pendências serem resolvidas e revisadas pelo agente cético.
