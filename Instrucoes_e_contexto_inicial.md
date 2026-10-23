## O que estamos construindo

Quero criar uma ferramenta que atue como um blog offline para servir como um repositório de conhecimento, através de textos e ensaios que escrevo sobre as coisas que eu pesquiso. Algo como um "caderno de conhecimento" online.

## Regras para o agente de IA

* Nunca faça commits automáticos ao menos que seja autorizado. No entanto, sugira ao devo commitar para manter o rastreo do código sem realizar commits quebrados.
* No prompt, nunca realize código a menos que seja solicitado. Eu dou o comando, e você executa.
* Sempre apresenta as sugestões de desenvolvimento como próximos passos. Eu analiso e dou a autorização sempre.
* Certificar de nunca deixar no código informações privadas sobre mim, sobre a minha máquina, sobre a minha localização, ou quaisquer informações que, quando commitadas, possam vazar conteúdo pessoal.
* As funções não devem conter mais que 50 linhas cada. Caso seja necessário, deve-se partir as funções de forma lógica e ordenada.
* O código deve ser comentado só o suficiente para que um agente de IA possa entender e seguir o desenvolvimento.
* Simplicidade primeiro: Forneça o código mínimo que resolva um problema e evite abstrações especulativas.
* Crie casos de testes automatizados para automatizar a busca de bugs durante o desenvolvimento do software e de novas features. Estes testes devem fazer parte de um conjunto de testes automatizados a serem executados.
* Toda fez que você corrigir um bug, crie um teste de regressão.

## Requisitos do programa

* Precisa ser executável no macOS (arm64), de forma offline.
* Precisa ser um programa consistindo em um único arquivo para ser acessado no computador, ou num pendrive, e mais um arquivo correspondente à uma ou mais base de dados.
* Precisa ser um programa que não requer instalação.

## Funções do Caderno de Pensamentos

* Precisa ser capaz de salvar os textos, com opção de classificar os textos por coleção e hashtag e controle de data e hora de publicação de cada texto
* Precisa conter uma ferramenta de busca dos textos, através da busca por palavras no título, ou pelas hashtags
* Os textos usam metodologia markdown para escrita
* Os textos também devem possuir a capacidade de identificar o que é código do que é texto. Como a feature do Markdown com o uso das aspas
* Nos textos, deve-se ser capaz de colar imagens da área de transferência
* Os textos devem ser capazes também de fazer upload de uma imagem contida no computador
* Todos os textos escritos devem estar armazenados em uma base de dados comum, armazenada offline no computador na forma de um único arquivo, e criptografada por uma senha. A cada novo texto, ou a cada edição de texto dentro do programa, a base de dados deve ser atualizada automaticamente.
* O programa deve permitir editar a senha da base de dados somente acessando a base de dados pelo programa. Quaisquer outras tentativas de entrar na base de dados, a criptografia deve ser capaz de atuar e não permitir a visualização dos textos sem o uso desse próprio programa e da senha.
* O programa deve ser capaz de criar novas bases de dados, caso necessário, exigindo uma senha e um nome da base de dados.
* Ao abrir o programa, ele deve enviar uma notificação noticiando a última base de dados acessada, e procurar acessá-la mediante o uso da senha. Se o programa não conseguir encontrar uma base de dados, ele deve notificar que não conseguiu encontrar nenhuma base de dados, e esperar que o usuário possa carregar uma base de dados ao procurar pela mesma em uma janela nos arquivos do computador.
* O programa deve conter um modal no formato de um calendário, que sinalize os dias em que houveram textos publicados.
