# Plano de desenvolvimento do banco criptografado

**Branch:** `feature/vault-encryption`
**Estado:** protótipo CPV1 implementado; o backend real passou em round-trip com fixtures sintéticas, mas ainda não está pronto para dados pessoais.

Este é o roteiro de execução para o agente desenvolvedor e o agente cético. A especificação técnica única está em [`Decisao_de_arquitetura_cofre.md`](Decisao_de_arquitetura_cofre.md). O plano cobre o armazenamento local de textos e imagens e a função que protege o arquivo inteiro com senha.

## Resumo em linguagem simples

O programa já tem código que organiza textos e imagens num arquivo e tenta protegê-los com senha. A senha é usada para criar uma chave; uma biblioteca pronta cifra o conteúdo e também detecta alterações no arquivo. A interface ainda não usa esse recurso.

Isso ainda é um protótipo: PyNaCl 1.6.2 está instalado no ambiente do projeto e o fluxo real passou com textos e imagens sintéticos, inclusive uma amostra de um milhão de palavras. Não testamos um arquivo de 40 MB; esse foi apenas um cenário hipotético, não um requisito. O aplicativo Mac também não foi validado. Enquanto o caderno estiver aberto, o conteúdo e a chave precisam existir na memória do programa.

**Estado atual:** o núcleo e o benchmark inicial foram testados no runtime Python deste Mac. A revisão cética dos testes atuais não encontrou achados críticos/altos abertos. A UI pode começar a usar a fachada com fixtures sintéticas; dados pessoais e distribuição aguardam validação do `.app` arm64 e integração completa.

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

- [x] Disponibilizar PyNaCl 1.6.2/libsodium no ambiente e confirmar as APIs por meio dos testes criptográficos reais.
- [x] Executar round-trip real das fixtures: criar e abrir o arquivo e comparar documento e bytes das imagens.
- [x] Conferir ausência de títulos, corpos, nomes de imagens e prefixos de bytes das imagens no ciphertext.
- [x] Testar rejeição de senha errada.
- [x] Testar em cofre real alteração do salt autenticado e de byte de ciphertext, truncamento, remoção integral do frame final, bytes extras e perfil KDF desconhecido; falhas autenticadas/estruturais não constroem sessão nem publicam snapshot.
- [x] Medir o pico de memória do processo no cenário de um milhão de palavras em Mac arm64.
- [x] Medir tempo e memória do Argon2id no runtime Mac arm64 disponível com `scripts/benchmark_argon2id.py`.
- [ ] Repetir a medição com o `.app` empacotado e avaliar máquinas Mac mais lentas suportadas.

**Saída da etapa:** round-trip, pico do processo, testes reais de falhas e benchmark inicial do Argon2id concluídos com fixture/runtime atuais. Permanece pendente validar no `.app` e avaliar máquinas mais lentas.

### 2. Fechar o contrato dos dados

- [x] Usar as fixtures existentes para documentar e validar o schema v1: coleções, textos, tags, datas UTC, favoritos e anexos.
- [x] Validar campos obrigatórios, tipos, IDs únicos, referências entre texto/coleção/anexo, datas e limites antes de persistir ou publicar um snapshot lido.
- [x] Garantir compatibilidade com imagens binárias sem Base64 e validar nome, MIME type, tamanho por anexo e agregado.
- [x] Adicionar testes para schema válido, campos/tipos inválidos, referências quebradas, IDs duplicados, datas, metadados binários divergentes, versão futura, JSON duplicado, entrada bytes-like e lista larga adversarial.

**Saída da etapa:** a camada de persistência recebe e devolve um snapshot coerente; JSON malformado ou schema inválido nunca vira estado parcialmente carregado. As duas fixtures existentes passam pelo schema sem migração.

`VaultSnapshot` exige texto nos metadados dos anexos e bytes/bytearray/memoryview nos dados; não faz coerção silenciosa com `str()`/`bytes()` de tipos arbitrários. Dados mutáveis bytes-like são copiados. O teste de complexidade rejeita a cardinalidade prevista antes de enfileirar a lista larga.

### 3. Fechar criação, salvamento e troca de senha

- [x] Testar `create_vault` real sem sobrescrever arquivo existente e com modo `0600`.
- [x] Testar `save`/reabertura com backend real: editar texto e metadado de imagem, salvar, fechar e comparar texto e bytes da imagem após reabrir.
- [x] Testar troca de senha, senha antiga rejeitada e senha nova aceita.
- [x] Simular falha real de `os.replace` durante `session.save`: arquivo anterior e snapshot permanecem intactos, reabertura confirma o conteúdo original e `.cpvault-*` é removido.
- [x] Testar sessão fechada (incluindo ausência de KDF na troca de senha), conflito de duas sessões reais e falha de `fsync` do diretório após substituição.
- [x] Inspecionar `src/caderno/vault/` e interceptar o replace real durante `session.save`: procurar marcadores sintéticos selecionados (senha, chave, título, corpo, nome e prefixo binário) no temporário antes do replace real. A inspeção do pacote não encontrou logging de conteúdo/segredos nem escrita de preferências/keyring; o benchmark imprime apenas métricas resumidas.

**Saída da etapa:** operações persistentes têm comportamento previsível diante de falhas; salvamento só é reportado como concluído após a substituição.

### 4. Revisão independente e correções

- [x] O agente cético revisou os testes do núcleo, os deltas de schema, adulteração, persistência e benchmark; as correções foram reavaliadas.
- [x] Achados e limites remanescentes foram registrados abaixo; não há achado crítico/alto aberto na revisão do núcleo no runtime atual.
- [x] Revisar KDF e rejeição pré-derivação, autenticação de stream, marcadores de plaintext no temporário, schema e atomicidade. As verificações são testes de protótipo, não prova formal nem auditoria completa do aplicativo.
- [ ] Fazer revisão da integração UI + `.app`, dependências nativas e mensagens de erro após o empacotamento.

**Saída da etapa:** alcançada para o núcleo isolado no runtime Python testado; a revisão do pacote e da UI permanece pendente.

### 5. Preparar integração, sem acoplar o núcleo à UI

- [x] Manter importações do pacote independentes de Tkinter/UI; validar offline no `.app` ainda pendente.
- [ ] Manter docstrings nas APIs públicas e nas etapas criptográficas/de persistência críticas; explicitar propósito, contrato, falhas e garantias sem narrar cada linha.
- [ ] Confirmar que PyNaCl/libsodium entra corretamente no `.app` macOS arm64 e medir seu tempo/memória.
- [ ] Integrar criar/selecionar/desbloquear base e salvar snapshots pela API; manter formato CPV1 fora da UI e mostrar mensagem genérica em qualquer falha de abertura.
- [ ] Validar no `.app` os fluxos de criar, abrir, salvar, reabrir, trocar senha e recusar senha errada antes de considerar o ciclo de integração concluído.

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
- Execução completa incluindo inspeção do tempfile em `session.save`: `PYTHONPATH=src .venv/bin/python -m pytest -q -ra tests/test_vault.py` passou com **48 testes em 94,91 s, sem skips**. Os casos focais anteriores de persistência real passaram em 36,13 s; o novo teste do tempfile passou isoladamente em 2,06 s.
- Escopo dessa verificação de privacidade: o teste sintético inspeciona o arquivo temporário imediatamente antes de `os.replace`, delega ao replace real e procura marcadores selecionados: senha sintética, chave em memória, título, corpo, nome de arquivo e os primeiros 32 bytes da imagem. A busca estática cobre apenas `src/caderno/vault/` e o benchmark: não há logging de conteúdo/segredos nem gravação de preferências/keyring; o benchmark imprime somente métricas resumidas. A senha só passa para derivação, chave/salt/snapshot ficam em memória e o temporário é o stream cifrado. Não é uma auditoria da UI ou da aplicação inteira.
- A suíte anterior, com as duas imagens locais (133.863 bytes no total), passou com 14 testes em 15,36 s; teste focado de um milhão de palavras passou em 4,88 s. A bateria gera as 200 notas em memória, cifra e reabre com PyNaCl real e compara o documento e os anexos. Isso valida amostras sintéticas, não o cenário hipotético de 5 milhões de palavras.
- `compileall` e `git diff --check` passaram após as mudanças de schema.
- A leitura acumula plaintext em memória até autenticar o stream completo, sob limites provisórios CPV1.
- O teste de um milhão de palavras usa manifesto de até 8 MiB; os limites gerais permanecem 10 MiB para plaintext e 14 MiB para o arquivo, com até 8 MiB agregados de anexos. A medição foi feita com `/usr/bin/time -l env PYTHONPATH=src .venv/bin/python -m pytest -q -ra tests/test_vault.py::test_crypto_backend_roundtrips_one_million_words` em macOS arm64/Python 3.13.7: pico residente do processo de **382.189.568 bytes (~364 MiB)** e `peak memory footprint` de **369.525.480 bytes (~352 MiB)**. Inclui Python, pytest, PyNaCl/libsodium e os dados do teste; não é perfil isolado do `.app`. O cenário de 40 MB continua fora do escopo.
- O benchmark isolado está em `scripts/benchmark_argon2id.py`; no Mac arm64 atual, cinco amostras tiveram mediana 2,1086 s (2,0965–2,1296 s). RSS máximo do processo 289.931.264 B, baseline 21.233.664 B; o delta ~256,2 MiB é estimativa de alto nível e não uma alocação isolada da KDF. Ainda não há build `.app`.
- A revisão cética do núcleo encontrou lacunas médias ainda não cobertas ponta a ponta: abrir um stream criptograficamente válido cujo documento viola o schema; reordenação/duplicação de frames e TAG_FINAL não vazio; concorrência entre processos e crash/falha de energia real. Não invalidam o início da UI com fixtures, mas devem ser avaliadas antes de declarar o produto pronto para uso real.

## Pendências sinalizadas após o teste de um milhão

- [x] Medir o pico de memória durante a criação e a abertura do cofre de um milhão de palavras neste ambiente; repetir com o `.app` empacotado quando ele existir.
- [x] Testar salvamento real de alterações e reabertura do arquivo salvo; revisão cética sem achados bloqueadores.
- [x] Testar troca de senha real: senha nova abre o cofre, senha antiga é rejeitada e documento/anexos permanecem iguais.
- [x] Testar adulteração de ciphertext/salt autenticado, cabeçalho com perfil desconhecido, truncamento, ausência do marcador final e bytes extras em arquivo cifrado real.
- [x] Medir Argon2id no Mac arm64 atual com script reproduzível.
- [ ] Validar a medição no `.app` e em Macs mais lentos suportados.

### Observações da revisão cética dos testes criptográficos e benchmark

- Sem achados críticos/altos abertos no núcleo isolado. O teste com spy parametriza KDF, stream, flags, opslimit e memlimit inválidos, e confirma que `_derive` não é chamado antes da rejeição.
- `InvalidVaultError` também pode surgir durante a validação de plaintext já autenticado (schema/registros/limites), não apenas antes da KDF. Essa classe não é prova nem deve ser comunicada como senha válida. A UI deve exibir mensagem genérica de falha de abertura para `InvalidVaultError` e `AuthenticationError`; ambos impedem publicação do snapshot. `AuthenticationError` não diferencia senha errada, adulteração autenticada, truncamento ou bytes extras.
- A revisão do benchmark não encontrou bloqueadores; comparações entre Macs devem incluir aquecimento e contexto térmico/energia. O script usa `resource` e é voltado a Unix/macOS.

Não usar dados pessoais até essas pendências serem resolvidas e revisadas pelo agente cético.
