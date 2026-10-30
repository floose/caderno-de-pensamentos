#!/bin/sh

set -eu

fail() {
    printf '%s\n' "$1" >&2
    exit 1
}

PROJECT_ROOT=$(CDPATH= cd "$(dirname "$0")/.." >/dev/null 2>&1 && pwd)
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
BUILD_ROOT="$PROJECT_ROOT/build/macos-arm64"

if [ "$(uname -s)" != "Darwin" ] || [ "$(uname -m)" != "arm64" ]; then
    fail 'A prova inicial do aplicativo requer macOS em Apple Silicon (arm64).'
fi

if [ ! -x "$PYTHON_BIN" ]; then
    fail 'Não encontrei o ambiente Python em .venv. Instale requirements.txt antes de empacotar.'
fi

if ! "$PYTHON_BIN" -c 'import PyInstaller, cffi, nacl, tkinter' >/dev/null 2>&1; then
    fail 'Faltam PyInstaller, cffi, PyNaCl ou Tkinter no ambiente .venv.'
fi

mkdir -p "$BUILD_ROOT/pyinstaller-config"
export PYINSTALLER_CONFIG_DIR="$BUILD_ROOT/pyinstaller-config"

"$PYTHON_BIN" -m PyInstaller \
    --noconfirm --clean --onedir --windowed --name Caderno \
    --paths "$PROJECT_ROOT/src" \
    --collect-all nacl --collect-all cffi \
    --distpath "$BUILD_ROOT/dist" \
    --workpath "$BUILD_ROOT/work-app" \
    --specpath "$BUILD_ROOT/spec-app" \
    "$PROJECT_ROOT/scripts/packaged_entry.py"

"$PYTHON_BIN" -m PyInstaller \
    --noconfirm --clean --onedir --console --name CadernoVaultProbe \
    --paths "$PROJECT_ROOT/src" \
    --collect-all nacl --collect-all cffi \
    --distpath "$BUILD_ROOT/smoke-dist" \
    --workpath "$BUILD_ROOT/work-smoke" \
    --specpath "$BUILD_ROOT/spec-smoke" \
    "$PROJECT_ROOT/scripts/package_vault_smoke.py"

"$PYTHON_BIN" -m PyInstaller \
    --noconfirm --clean --onedir --console --name CadernoArgon2Probe \
    --paths "$PROJECT_ROOT/src" \
    --collect-all nacl --collect-all cffi \
    --distpath "$BUILD_ROOT/argon2-dist" \
    --workpath "$BUILD_ROOT/work-argon2" \
    --specpath "$BUILD_ROOT/spec-argon2" \
    "$PROJECT_ROOT/scripts/benchmark_argon2id.py"

UI_SMOKE_NAME="CadernoUISmoke$$"
"$PYTHON_BIN" -m PyInstaller \
    --noconfirm --clean --onedir --windowed --name "$UI_SMOKE_NAME" \
    --paths "$PROJECT_ROOT/src" \
    --collect-all nacl --collect-all cffi \
    --distpath "$BUILD_ROOT/ui-smoke-dist" \
    --workpath "$BUILD_ROOT/work-ui-smoke" \
    --specpath "$BUILD_ROOT/spec-ui-smoke" \
    "$PROJECT_ROOT/scripts/package_ui_smoke.py"

APP_BUNDLE="$BUILD_ROOT/dist/Caderno.app"
APP_EXECUTABLE="$APP_BUNDLE/Contents/MacOS/Caderno"
SODIUM_BINARY="$APP_BUNDLE/Contents/Frameworks/nacl/_sodium.abi3.so"
TKINTER_BINARY=$(find "$APP_BUNDLE/Contents/Frameworks" -name '_tkinter*.so' -print -quit)
set -- "$APP_BUNDLE/Contents/Frameworks"/_cffi_backend*.so
CFFI_BINARY=$1

if [ ! -f "$APP_EXECUTABLE" ] || [ ! -f "$SODIUM_BINARY" ] || \
    [ ! -f "$TKINTER_BINARY" ] || [ ! -f "$CFFI_BINARY" ]; then
    fail 'O bundle não contém todos os executáveis nativos esperados.'
fi

file "$APP_EXECUTABLE" | grep -q 'arm64' || fail 'O executável principal não é arm64.'
file "$SODIUM_BINARY" | grep -q 'arm64' || fail 'libsodium não foi empacotada para arm64.'
file "$CFFI_BINARY" | grep -q 'arm64' || fail 'cffi não foi empacotado para arm64.'
file "$TKINTER_BINARY" | grep -q 'arm64' || fail 'Tkinter não foi empacotado para arm64.'

"$BUILD_ROOT/smoke-dist/CadernoVaultProbe/CadernoVaultProbe"
printf '\nArgon2id no runtime empacotado (3 amostras):\n'
"$BUILD_ROOT/argon2-dist/CadernoArgon2Probe/CadernoArgon2Probe" --samples 3
UI_SMOKE_RESULT="$BUILD_ROOT/ui-smoke-result-$$.txt"
CADERNO_PACKAGE_UI_SMOKE_RESULT="$UI_SMOKE_RESULT" \
    open -n -W "$BUILD_ROOT/ui-smoke-dist/$UI_SMOKE_NAME.app"
[ -f "$UI_SMOKE_RESULT" ] || fail 'O smoke test da UI empacotada não gravou um resultado.'
grep -q '^PASS:' "$UI_SMOKE_RESULT" || {
    cat "$UI_SMOKE_RESULT" >&2
    fail 'O smoke test da UI empacotada falhou.'
}
cat "$UI_SMOKE_RESULT"
printf '\nApp de prova: %s\n' "$APP_BUNDLE"
