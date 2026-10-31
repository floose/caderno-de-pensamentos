#!/bin/sh

set -u

pause_before_exit() {
    if [ -t 0 ]; then
        printf 'Pressione Enter para fechar esta janela do Terminal. '
        read -r close_prompt
    fi
}

fail() {
    printf '%s\n' "$1"
    pause_before_exit
    exit 1
}

PROJECT_ROOT=$(CDPATH= cd "$(dirname "$0")" >/dev/null 2>&1 && pwd)
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"

if [ "$(uname -s)" != "Darwin" ]; then
    fail 'Este teste da interface requer macOS.'
fi

if [ ! -x "$PYTHON_BIN" ]; then
    fail 'Não encontrei o ambiente Python em .venv. Crie-o e instale requirements.txt antes de executar.'
fi

if ! "$PYTHON_BIN" -c 'import tkinter, nacl, pytest, PIL' >/dev/null 2>&1; then
    fail 'Faltam dependências no .venv (Tkinter, PyNaCl, Pillow ou pytest).'
fi

APP_UID=$(id -u)
TEST_DATA_DIR="/private/tmp/caderno-ui-test-$APP_UID"
if [ -L "$TEST_DATA_DIR" ]; then
    fail 'A pasta de teste é um symlink; não vou usá-la.'
fi

mkdir -p "$TEST_DATA_DIR" || fail 'Não consegui criar a pasta isolada de teste.'
DATA_OWNER=$(stat -f '%u' "$TEST_DATA_DIR") || fail 'Não consegui verificar a pasta de teste.'
if [ "$DATA_OWNER" != "$APP_UID" ]; then
    fail 'A pasta de teste existente não pertence a este usuário.'
fi
chmod 700 "$TEST_DATA_DIR" || fail 'Não consegui proteger a pasta de teste.'
PATH_PROBE_DIR=$(mktemp -d "$TEST_DATA_DIR/path-symlink-probe.XXXXXX") || fail 'Não consegui preparar o cenário sintético de symlink.'
mkdir -p "$PATH_PROBE_DIR/real-folder" || fail 'Não consegui preparar a pasta sintética de navegação.'
: > "$PATH_PROBE_DIR/real.cpv" || fail 'Não consegui preparar o arquivo sintético de symlink.'
ln -s "$PATH_PROBE_DIR/real.cpv" "$PATH_PROBE_DIR/alias.cpv" || fail 'Não consegui criar o symlink sintético de arquivo.'
ln -s "$PATH_PROBE_DIR/real-folder" "$PATH_PROBE_DIR/alias-folder" || fail 'Não consegui criar o symlink sintético de pasta.'

cd "$PROJECT_ROOT" || fail 'Não consegui entrar na pasta do projeto.'
export PYTHONPATH="$PROJECT_ROOT/src"
unset CADERNO_CONFIG_DIR 2>/dev/null || true
unset CADERNO_UI_TEST_PROFILE 2>/dev/null || true

printf 'Executando os testes automatizados da UI...\n'
"$PYTHON_BIN" -m pytest -q \
    tests/test_ui.py tests/test_ui_notes.py tests/test_preferences.py \
    tests/test_ui_contrast.py tests/test_ui_layout.py
TEST_STATUS=$?
if [ "$TEST_STATUS" -ne 0 ]; then
    printf 'Os testes da UI falharam; o aplicativo não será iniciado.\n'
    pause_before_exit
    exit "$TEST_STATUS"
fi

export CADERNO_CONFIG_DIR="$TEST_DATA_DIR"
export CADERNO_UI_TEST_PROFILE="$TEST_DATA_DIR"
printf '\nAbrindo o Caderno com perfil de teste em: %s\n' "$TEST_DATA_DIR"
printf 'Use somente cofres sintéticos neste perfil de teste.\n\n'
printf 'Na janela, crie uma coleção pelo +: a entrada do nome e os alertas devem usar diálogos do próprio Caderno, com cores e fontes do tema. Escape cancela a entrada; Enter ou Criar confirma.\n'
printf 'Associe a coleção a uma nota e informe hashtags como #ideia, #projeto. Tente criar outra coleção com o mesmo nome, inclusive mudando maiúsculas: o popup informa que ela já existe e não a cria.\n'
printf 'Os seletores de abrir/criar base e coleção devem usar janelas do Caderno. Abrir/criar deve começar na pasta da última base válida; se ela não estiver disponível, deve começar na sua pasta pessoal. No perfil sintético, deve permanecer na pasta indicada no Terminal. Teste navegar por pastas, filtrar bases .cpv e usar Cancelar/Escape; ao criar, informe um nome sem extensão e confirme que .cpv é acrescentado; informe também um nome .txt e confirme que o popup rejeita a extensão. Na pasta de prova impressa acima, tente abrir alias.cpv e entrar em alias-folder: ambos devem ser recusados com alerta, sem abrir nem navegar até o destino. A janela de coleção deve permitir escolher ou cancelar.\n'
printf 'Pasta de prova de symlinks: %s\n' "$PATH_PROBE_DIR"
printf 'Ao abrir uma base sintética, digite a senha no campo e pressione Enter: deve ter o mesmo efeito do botão Abrir base. Repita com senha incorreta: o alerta de falha deve aparecer; feche-o e tente abrir a base novamente.\n'
printf 'Na base aberta, busque termos de título, coleção, hashtag e conteúdo; a lista deve mostrar notas que contenham todos os termos. Escape limpa a busca; filtrar não deve apagar o rascunho aberto.\n'
printf 'No editor, clique no seletor de coleção: o modal deve mostrar os nomes das coleções, nunca IDs. Escolha outra coleção, confira o nome no botão, salve e reabra a base para confirmar a persistência da mudança.\n'
printf 'A janela não deve encolher abaixo da largura mínima. No editor, o botão da coleção deve permanecer legível (nomes longos podem quebrar em linhas) e Salvar/Descartar devem ficar inteiros. Ao abrir uma nota salva, confira no topo as datas e horários de criação e última modificação; nota nova só mostra esses dados depois de salvar.\n'
printf 'Abra Filtrar: escolha uma coleção e uma hashtag, aplique e confira que ambos restringem a lista junto com a busca. Use Todas as coleções/hashtags para limpar; Escape cancela sem alterar filtros. Fechar a base limpa os filtros.\n'
printf 'Abra Ordenar e experimente última edição, data de criação e título em ordem crescente/decrescente. A ordem escolhida deve mudar a lista e voltar ao padrão ao trocar de base.\n'
printf 'No editor, alterne ☆ Favoritar/★ Favorita, salve e feche/reabra a base: o estado deve persistir. Em Filtrar, marque Somente favoritas e confirme que notas não favoritas somem; desmarque para voltar à lista completa.\n'
printf 'No editor, confirme que o botão Expandir escrita indica ⌃⌘E. Use Control+Command+E ou clique nele: navegação, lista e metadados devem sumir e o texto ocupar a altura disponível. As margens laterais devem ter a mesma cor clara do editor, sem retângulo escuro nem linha de contorno ao redor do campo, e incluir a barra de rolagem. Pressione Enter no teclado numérico: deve iniciar uma nova linha, como o Enter principal. O botão deve indicar Voltar ao caderno com o mesmo atalho. Use-o, Escape ou o atalho para restaurar o editor; confirme que as margens e o contorno normal reaparecem e que rascunho e metadados continuam intactos. Teste Salvar expandido e, com título vazio ou hashtag acima de 256 caracteres, confirme que a validação retorna ao campo visível.\n'
printf 'Selecione uma nota de uma coleção diferente de Geral e use Command+N: o editor de nota nova deve manter essa coleção selecionada. Salve e confira que a nota aparece na coleção escolhida.\n'
printf 'No seletor de coleção, teste ⌘S para salvar e Escape para abrir as opções de alterações pendentes.\n'
printf 'Salve, feche e reabra a base: coleção e hashtags devem continuar na nota.\n\n'
"$PYTHON_BIN" -m caderno
APP_STATUS=$?

printf '\nO Caderno foi fechado (código %s).\n' "$APP_STATUS"
pause_before_exit
exit "$APP_STATUS"
