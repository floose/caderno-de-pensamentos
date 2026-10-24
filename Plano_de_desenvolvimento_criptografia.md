# Plano de desenvolvimento do banco criptografado

**Branch:** `feature/vault-encryption`
**Estado:** protótipo CPV1 implementado; o backend criptográfico real ainda não foi validado.

Este é o roteiro de execução para o agente desenvolvedor e o agente cético. A especificação técnica única está em [`Decisao_de_arquitetura_cofre.md`](Decisao_de_arquitetura_cofre.md). O plano cobre o armazenamento local de textos e imagens e a função que protege o arquivo inteiro com senha.

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
- O schema ilustrativo está em `tests/fixtures/cofre_exemplo.json` e contém duas notas sintéticas; `tests/fixtures/pixel.png` é uma imagem sintética.
- O codec e a persistência existem, mas o último registro é **11 testes aprovados e 1 ignorado** porque PyNaCl não estava instalado. `compileall` e `git diff --check` passaram naquele registro; repetir após mudanças.
- A leitura acumula plaintext em memória até autenticar o stream completo, sob limites provisórios CPV1. A medição anterior de 28,3 MB em `tracemalloc` não inclui memória nativa ou o runtime.
- Ainda não há validação do backend criptográfico real, benchmark Argon2id no Mac arm64, nem build `.app`. Não usar dados reais antes de concluir os marcos 1–4.
