#!/bin/bash
# Envia o texto recebido no stdin ao Claude Code em modo headless, com o prompt
# do arquivo indicado, e escreve a resposta no stdout.
#
# Uso: summarize.sh <arquivo-de-prompt> < transcricao.txt > resumo.md
#
# Segurança: o resumo não precisa de ferramentas. Roda sem nenhuma (--tools ""),
# sem servidores MCP, com um turno só e sem salvar a sessão.
set -euo pipefail

PROMPT_FILE="${1:?uso: summarize.sh <arquivo-de-prompt>}"
CLAUDE="${CLAUDE_BIN:-$HOME/.local/bin/claude}"
PROMPT="$(cat "$PROMPT_FILE")"

# Roda fora do projeto para não carregar o CLAUDE.md dele como contexto.
cd "${TMPDIR:-/tmp}"

exec "$CLAUDE" -p \
  --tools "" \
  --strict-mcp-config \
  --no-session-persistence \
  --max-turns 1 \
  "$PROMPT"
