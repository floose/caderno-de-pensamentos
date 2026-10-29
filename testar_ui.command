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
printf 'No seletor de coleção, teste ⌘S para salvar e Escape para abrir as opções de alterações pendentes.\n'
printf 'Salve, feche e reabra a base: coleção e hashtags devem continuar na nota.\n\n'
"$PYTHON_BIN" -m caderno
APP_STATUS=$?

printf '\nO Caderno foi fechado (código %s).\n' "$APP_STATUS"
pause_before_exit
exit "$APP_STATUS"
