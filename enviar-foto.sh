#!/usr/bin/env bash
# enviar-foto.sh <arquivo.png|jpg|mp4> [legenda] — manda foto ou video no Telegram.
set -euo pipefail
F="${1:?uso: enviar-foto.sh <arquivo> [legenda]}"
CAP="${2:-}"
ENV="/home/nmaldaner/projetos/openpcbotv2/.env"
TOKEN=$(grep -E '^TELEGRAM_BOT_TOKEN=' "$ENV" | cut -d= -f2- | tr -d "\"'")
CHAT=$(grep -E '^ALLOWED_CHAT_ID=' "$ENV" | cut -d= -f2- | tr -d "\"'")
case "${F,,}" in
  *.mp4|*.mov) METHOD=sendVideo; FIELD=video;;
  *)           METHOD=sendPhoto; FIELD=photo;;
esac
curl -sS -X POST "https://api.telegram.org/bot${TOKEN}/${METHOD}" \
  -F chat_id="$CHAT" -F "${FIELD}=@$F" -F caption="$CAP" | jq -r '.ok'
