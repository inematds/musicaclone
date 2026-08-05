#!/usr/bin/env bash
# enviar.sh <arquivo.mp3> [legenda] — manda o audio no Telegram do bot.
set -euo pipefail
F="${1:?uso: enviar.sh <arquivo.mp3> [legenda]}"
CAP="${2:-}"
ENV="/home/nmaldaner/projetos/openpcbotv2/.env"
TOKEN=$(grep -E '^TELEGRAM_BOT_TOKEN=' "$ENV" | cut -d= -f2- | tr -d "\"'")
CHAT=$(grep -E '^ALLOWED_CHAT_ID=' "$ENV" | cut -d= -f2- | tr -d "\"'")
curl -sS -X POST "https://api.telegram.org/bot${TOKEN}/sendAudio" \
  -F chat_id="$CHAT" -F audio="@$F" -F caption="$CAP" | jq -r '.ok'
