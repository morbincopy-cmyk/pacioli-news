#!/bin/bash
# Pacioli News: ponto de entrada (chamado pelo launchd de hora em hora, ou à mão).
#
#   ./run.sh                  execução normal
#   ./run.sh --dry-run        testa sem publicar nem alterar o estado
#   ./run.sh --video <URL>    processa um vídeo específico
set -uo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd -P)"  # caminho real (a pasta na Área de Trabalho é um atalho)

# O launchd não carrega o ambiente do terminal: PATH, fuso e codificação explícitos.
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/Library/Python/3.9/bin:$HOME/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export TZ="America/Sao_Paulo"
export LANG="pt_BR.UTF-8" LC_ALL="pt_BR.UTF-8" PYTHONIOENCODING="utf-8" PYTHONUNBUFFERED=1
export HF_HUB_DISABLE_PROGRESS_BARS=1

PYTHON="$(/usr/bin/python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["paths"]["python"])' "$ROOT/config.json")"

LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/$(date +%Y-%m-%d_%H%M).log"
find "$LOG_DIR" -name '*.log' -mtime +30 -delete 2>/dev/null

notify() {
  /usr/bin/osascript -e "display notification \"$1\" with title \"Pacioli News\" sound name \"Basso\"" >/dev/null 2>&1 || true
}

# Lock: impede duas execuções ao mesmo tempo (uma transcrição longa pode passar de uma hora).
LOCK="$ROOT/state/run.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  OTHER="$(cat "$LOCK/pid" 2>/dev/null)"
  if [ -n "$OTHER" ] && kill -0 "$OTHER" 2>/dev/null; then
    echo "[$(date +%H:%M:%S)] Outra execução em andamento (pid $OTHER); saindo." >>"$LOG"
    exit 0
  fi
  rm -rf "$LOCK"   # lock antigo de uma execução que morreu
  mkdir "$LOCK" || { notify "Não consegui criar o lock em state/"; exit 1; }
fi
echo $$ >"$LOCK/pid"
trap 'rm -rf "$LOCK"' EXIT

cd "$ROOT"
echo "[$(date '+%d/%m/%Y %H:%M:%S')] Início ($*)" >>"$LOG"
if [ -t 1 ]; then
  "$PYTHON" "$ROOT/pipeline/main.py" "$@" 2>&1 | tee -a "$LOG"
  STATUS=${PIPESTATUS[0]}
else
  "$PYTHON" "$ROOT/pipeline/main.py" "$@" >>"$LOG" 2>&1
  STATUS=$?
fi

if [ "$STATUS" -ne 0 ]; then
  notify "A execução das $(date +%H:%M) falhou. Veja logs/$(basename "$LOG")"
fi
exit "$STATUS"
