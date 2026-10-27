# Decisão de arquitetura do cofre — CPV1

**Estado:** implementação inicial; sujeita a revisão do agente cético antes de ser considerada pronta.

## Decisão

Usar PyNaCl 1.6.2 sobre libsodium para derivar uma chave com Argon2id v1.3 e cifrar o arquivo com `crypto_secretstream_xchacha20poly1305`. O arquivo usa um envelope CPV1 pequeno e versionado, com manifesto JSON e anexos binários no mesmo fluxo criptografado.

OpenPGP v6 foi considerado por ser um padrão interoperável com Argon2 e AEAD em blocos. Não foi escolhido porque a aplicação precisaria integrar e empacotar uma implementação OpenPGP completa. PyNaCl oferece as APIs específicas necessárias e wheel macOS universal2; o `.app` arm64 ainda precisa de teste de empacotamento.

O módulo não implementa cifra, KDF, nonce ou MAC próprios. CPV1 define somente enquadramento, IDs, serialização e limites do formato da aplicação.

## JSON e cenário de capacidade avaliado

JSON é a serialização escolhida para o protótipo porque facilita validar o schema e separar os dados do código da interface. O JSON e os anexos ficam dentro do fluxo cifrado; JSON não é gravado em claro como arquivo de banco.

A pergunta sobre 5 milhões de palavras (estimativa de cerca de 40 MB de texto sintético) foi exploratória, não é um requisito do produto. A primitiva `secretstream` processa dados em blocos, mas **a implementação atual rejeita arquivos dessa dimensão**: os limites CPV1 abaixo são menores, o leitor acumula o conteúdo em memória e cada salvamento regrava o arquivo completo. Não aumentar os limites por causa desse cenário hipotético; se esse porte virar uma necessidade real, medir tamanho, tempo e pico de memória no Mac alvo antes de decidir.

## Perfil KDF

- Argon2id v1.3 (libsodium `ALG_ARGON2ID13`).
- `opslimit=3`, `memlimit=268435456` bytes, saída de 32 bytes e salt aleatório de 16 bytes.
- O libsodium MODERATE usa 256 MiB e 3 passagens. Seu wrapper Argon2id usa paralelismo `p=1`; essa propriedade é parte do perfil CPV1. Não se usa `ALG_DEFAULT`, pois o valor pode mudar entre versões da biblioteca.
- Medição inicial reproduzível no Mac arm64 disponível: `scripts/benchmark_argon2id.py --samples 5`, CPython 3.13.7/PyNaCl 1.6.2, mediana 2,1086 s (2,0965–2,1296 s). O RSS máximo do processo foi 289.931.264 bytes, com baseline de 21.233.664 bytes; a diferença (~256,2 MiB) aproxima o custo do perfil, mas `ru_maxrss` mede o processo inteiro, não a alocação isolada da KDF. Não altera o perfil nem prova adequação em Macs mais lentos; repetir no `.app` arm64 antes da distribuição. Os valores de KDF são lidos do cabeçalho, mas qualquer combinação fora da allowlist exata é rejeitada antes de derivar a chave.
- Senha: Unicode NFC, UTF-8, sem remover espaços, máximo de 1.024 bytes após normalização. O aplicativo não persiste senha nem chave.

## Envelope binário CPV1

Todos os inteiros são sem sinal e big-endian. O cabeçalho fixo tem 65 bytes:

| Offset | Tamanho | Campo | Valor/validação |
|---:|---:|---|---|
| 0 | 8 | Magic | ASCII `CPVAULT` seguido de `0x00` |
| 8 | 2 | Versão | `1` |
| 10 | 1 | KDF ID | `1` = Argon2id v1.3 |
| 11 | 1 | Stream ID | `1` = XChaCha20-Poly1305 secretstream |
| 12 | 1 | Flags | `0`; outros valores rejeitados |
| 13 | 4 | Opslimit | `3` |
| 17 | 8 | Memlimit em bytes | `268435456` |
| 25 | 16 | Salt | Novo ao criar/trocar senha |
| 41 | 24 | Secretstream header | Emitido por `init_push`; não é segredo |

O AAD de todas as mensagens é o cabeçalho CPV1 completo, exatamente nos bytes armazenados. Isso autentica formato, IDs, custo Argon2id, salt e stream header. Cabeçalho e comprimentos são validados antes da KDF; perfis não permitidos nunca controlam quantidade arbitrária de memória ou CPU.

Depois do cabeçalho, o arquivo contém uma sequência de frames:

```text
frame := ciphertext_length:u32be || secretstream_ciphertext
```

Cada mensagem carrega no máximo 65.536 bytes plaintext; o comprimento cifrado não pode exceder `65.536 + crypto_secretstream_xchacha20poly1305_ABYTES`. Todas as mensagens de dados usam `TAG_MESSAGE`. O escritor emite uma última mensagem vazia com `TAG_FINAL`. O leitor rejeita EOF antes de `TAG_FINAL`, qualquer tag diferente de `TAG_MESSAGE` antes do final, um segundo final, framing malformado e qualquer byte depois do frame final. A sequência secretstream autentica a ordem; trocar ou repetir frames causa falha de autenticação.

Limites provisórios de protótipo: arquivo cifrado até 14 MiB, plaintext até 10 MiB, manifesto até 8 MiB, até 256 anexos, cada anexo até 8 MiB e agregado até 8 MiB. São limites para testes e não requisitos finais de produto. O documento tem até 100 mil valores e profundidade 64. O parser só publica snapshot depois da tag final e EOF, mas acumula plaintext para autenticar antes de interpretar. Em um teste sintético de um milhão de palavras e duas imagens, `/usr/bin/time -l` mediu pico residente de 382.189.568 bytes (~364 MiB) e `peak memory footprint` de 369.525.480 bytes (~352 MiB), em macOS arm64 com Python 3.13.7. A medida inclui o processo de teste inteiro (Python, pytest, PyNaCl/libsodium e dados); não é uma medição isolada do app nem extrapola para outros arquivos/hardwares.

## Registros dentro do fluxo

O conteúdo plaintext do stream é uma sequência de registros binários. Não há plaintext temporário em disco.

1. Manifesto: `type:u8(0x01) || length:u32be || json_utf8`. O manifesto tem `schema_version: 1`, coleções, textos, datas UTC, hashtags e descritores de anexos. Cada texto referencia anexos por ID. Limite provisório de 8 MiB; conteúdo binário de imagens até 8 MiB agregado.
2. Um registro para cada anexo, na ordem do manifesto: `type:u8(0x02) || id_length:u16be || id:utf8 || data_length:u64be || image_bytes`.
3. O leitor exige um manifesto único primeiro, exatamente um registro por ID listado, comprimentos válidos e nenhum registro depois do último anexo.

O fluxo é cifrado em blocos de no máximo 64 KiB, então uma imagem não é transformada em Base64 nem precisa caber numa única mensagem AEAD. A camada devolve um snapshot somente após autenticar o stream final e validar todos os registros.

## Schema do documento v1

O objeto JSON do caderno usa chaves estritas; propriedades desconhecidas ou ausentes são rejeitadas para `schema_version: 1`. A raiz contém exatamente `schema_version`, `collections`, `attachments` e `entries`. Cada coleção tem exatamente `id` e `name`. Cada entrada tem `id`, `title`, `body_markdown`, `collection_id`, `tags`, `created_at`, `updated_at`, `published_at`, `favorite` e `attachments`. Cada descritor de anexo tem `id`, `entry_id`, `filename` e `media_type`.

IDs são textos não vazios de até 256 caracteres, sem caracteres de controle, únicos globalmente entre coleções, entradas e anexos. Nomes/títulos são textos não vazios de até 4.096 caracteres; corpo Markdown pode ser vazio e tem limite de 8 MiB. `tags` é lista de textos únicos não vazios, cada um até 256 caracteres. `favorite` precisa ser booleano, sem coerção de strings ou inteiros. `created_at` e `updated_at` são datas/hora ISO 8601 com fuso UTC (`Z` ou `+00:00`); `published_at` aceita a mesma forma ou `null` para rascunho.

`collection_id` referencia uma coleção existente. Cada ID em `entry.attachments` corresponde exatamente a um descritor cujo `entry_id` seja aquela entrada; não pode haver descritor ou referência extra. Cada descritor corresponde a um registro binário único, e `filename`/`media_type` coincidem com os metadados do objeto binário. O filename é simples, sem separadores de diretório; MIME type precisa ser `image/*`. O documento fica limitado a 100 mil valores e profundidade 64; há até 10 mil coleções, 100 mil entradas e 256 anexos, além dos limites de bytes CPV1.

As fixtures `cofre_exemplo.json` e `cofre_volume.json` são compatíveis sem migração: ambas usam schema v1, datas UTC e o conjunto de chaves definido acima. A fixture curta associa `pixel.png`; a de volume pode ter anexos adicionados pelo teste. `VaultSnapshot` pode ser construído em memória, mas criação/salvamento validam schema antes de persistir e leitura valida schema depois de autenticar o stream, antes de devolver qualquer snapshot. O construtor não converte `id`, `name` ou `media_type` para texto: esses campos precisam já ser `str`. `data` precisa ser `bytes`, `bytearray` ou `memoryview`; os dois últimos são copiados para bytes imutáveis. Tipos inválidos levantam `TypeError`.

O validador conta prospectivamente até 100 mil valores antes de enfileirar filhos de um objeto/lista e rejeita profundidade maior que 64. Assim, a própria fila de validação também permanece limitada; o limite não é aplicado depois de expandir uma lista larga.

## API de integração e snapshots

O pacote `caderno.vault` não importa Tkinter nem `caderno.ui`; não exibe diálogos nem guarda estado global da interface. A fachada expõe:

- `create_vault(path, password, snapshot) -> VaultSession`
- `open_vault(path, password) -> VaultSession`
- `session.snapshot -> VaultSnapshot`
- `session.save(snapshot) -> None`
- `session.change_password(new_password) -> None`
- `session.close() -> None`

`VaultSnapshot` é imutável: a fábrica serializa uma cópia do documento JSON e guarda anexos em tuple de objetos frozen, com bytes imutáveis. Alterar dicts/listas usados na criação não altera o snapshot; acessar o documento retorna uma cópia nova. O manifesto contém metadados dos anexos; `VaultAttachment` fornece ID, nome, MIME type e bytes binários.

`open_vault` pode levantar `AuthenticationError` para senha incorreta, falha de autenticação, truncamento ou dados depois do frame final. `InvalidVaultError` é usado para envelope/perfil inválido antes da KDF, limites estruturais excedidos e manifesto/registros inválidos encontrados depois da autenticação. Como esse segundo grupo pode ser detectado após o stream ter sido autenticado, callers não devem usar `InvalidVaultError` para inferir nem comunicar que a senha está correta. A UI deve apresentar uma mensagem genérica de falha ao abrir para qualquer erro de abertura e não publicar snapshot/sessão em nenhum desses casos.

Trocar senha cria salt, chave e stream header novos, e regrava o snapshot completo. A sessão troca sua chave somente depois de a substituição do arquivo ter ocorrido com sucesso.

## Salvamento, concorrência e durabilidade

- Cada sessão guarda SHA-256 do arquivo completo aberto ou salvo. Esse fingerprint é uma referência de concorrência, não uma proteção criptográfica adicional.
- Antes de salvar, adquirir um lock advisory por caminho e comparar o fingerprint atual com o esperado. Uma sessão/processo obsoleto recebe `ConcurrentModificationError` e não sobrescreve revisão mais recente.
- O lock fica num diretório privado por UID sob `tempfile.gettempdir()`, nomeado por hash do caminho normalizado (sem caminho em claro). O aplicativo valida dono/permissões e abre diretório e lock com `O_NOFOLLOW`/`dir_fd`; `flock` serializa escritores cooperantes no mesmo usuário/macOS.
- O aplicativo rejeita caminhos com symlink e diretórios pai graváveis por grupo/outros, exceto diretórios sticky como `/tmp`, onde só aceita uma base existente do usuário atual. Isso reduz troca de temporários por outros UIDs. Processos maliciosos do mesmo UID, filesystems de rede e escritores externos que ignoram o lock ficam fora da garantia; a comparação de fingerprint reduz, mas não elimina, corridas externas.
- Escrever o novo arquivo cifrado em temporário exclusivo no mesmo diretório, `flush` e `fsync` no arquivo, `os.replace`, e sincronizar o diretório quando suportado. Uma falha antes de `os.replace` preserva a base anterior.
- Se `fsync` do diretório falhar após `os.replace`, a nova base já está visível, mas a persistência após falta de energia é incerta. Atualizar o fingerprint ao que está visível e levantar/retornar erro de durabilidade específico; não relatar que a base antiga permaneceu ativa.
- O temporário contém somente bytes cifrados, com permissão `0600`. Nenhum plaintext é escrito em disco.

## Garantias e limites

CPV1 busca confidencialidade e integridade dos dados em repouso, incluindo anexos, e rejeita fluxo incompleto. Não impede exclusão, rollback para uma cópia antiga válida, malware ou acesso ao processo desbloqueado. Fechar a sessão remove referências internas à chave, mas Python não garante que todas as cópias na heap foram sobrescritas fisicamente.

Não suportar edição simultânea do mesmo cofre: escritores cooperantes são serializados e sessões stale recebem conflito. A aplicação deverá reabrir e, se necessário, reconciliar snapshots; o módulo não mescla textos.

## Fontes técnicas

- [libsodium secretstream — API de stream/arquivo](https://doc.libsodium.org/secret-key_cryptography/secretstream)
- [libsodium password hashing — Argon2id e perfil MODERATE](https://doc.libsodium.org/password_hashing/default_phf)
- [PyNaCl KDF Argon2id](https://pynacl.readthedocs.io/en/latest/api/pwhash/)
- [PyNaCl wheels e suporte macOS universal2/arm64](https://pypi.org/project/PyNaCl/)
- [Implementação de Argon2id no libsodium 1.0.20](https://github.com/jedisct1/libsodium/blob/1.0.20/src/libsodium/crypto_pwhash/argon2/pwhash_argon2id.c)
