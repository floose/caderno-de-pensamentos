# Instruções para agentes deste repositório

Antes de alterar o projeto, leia [`MEMORIA_DO_PROJETO.md`](MEMORIA_DO_PROJETO.md) e as instruções da tarefa. A memória aponta os documentos de referência e o estado atual; confirme sempre o estado real do Git e do código, pois a memória pode ficar desatualizada.

## Regras de colaboração

- Responda em português, salvo pedido diferente.
- Não faça commit, merge, rebase ou push sem autorização explícita.
- Não implemente código sem solicitação explícita; quando solicitado, conclua a tarefa e informe arquivos alterados e validações feitas.
- Preserve a privacidade: não adicione caminhos pessoais, nomes, localização, segredos, dados reais ou informações da máquina ao código, testes e documentação versionada.
- Prefira soluções pequenas e claras. Mantenha funções com até 50 linhas; divida-as quando necessário.
- Documente APIs públicas e funções sensíveis com docstrings que expliquem finalidade, entradas/saídas, erros e garantias relevantes. Comente invariantes criptográficas ou de persistência não óbvias; evite comentários linha a linha que apenas repetem o código.
- Crie testes automatizados para funcionalidades e regressões de bugs.
- Toda mudança de UI deve incluir um modo reproduzível de experimentá-la pela janela real, com instruções curtas e resultados esperados; testes unitários isolados não substituem esse roteiro manual. Atualize o script raiz `testar_ui.command`, que roda os testes focados da UI e inicia o app num perfil de teste que rejeita cofres fora da pasta sintética.
- Não altere a interface durante o trabalho do cofre criptográfico, salvo solicitação explícita de integração.

## Segurança do cofre

- Não invente primitivas criptográficas. Siga a decisão vigente em [`Decisao_de_arquitetura_cofre.md`](Decisao_de_arquitetura_cofre.md) e o plano/revisão em [`Plano_de_desenvolvimento_criptografia.md`](Plano_de_desenvolvimento_criptografia.md).
- Fixtures devem ser sintéticas. Nunca grave senha, chave, plaintext de usuário ou cofre real no repositório.
- Preserve a separação entre `src/caderno/vault/` e UI: o pacote do cofre não depende de Tkinter nem de `caderno.ui`.
- Trate claims de segurança e testes ignorados como limitações explícitas; não declare criptografia validada sem executar os testes com o backend real.
