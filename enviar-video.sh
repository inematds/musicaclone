#!/usr/bin/env bash
# enviar-video.sh <arquivo.mp4> [legenda] — manda o video no Telegram do bot.
# Se passar de 48MB, recomprime antes (limite do Telegram e 50MB).
set -euo pipefail
F="${1:?uso: enviar-video.sh <arquivo.mp4> [legenda]}"
CAP="${2:-}"
ENV="/home/nmaldaner/projetos/openpcbotv2/.env"
TOKEN=$(grep -E '^TELEGRAM_BOT_TOKEN=' "$ENV" | cut -d= -f2- | tr -d "\"'")
CHAT=$(grep -E '^ALLOWED_CHAT_ID=' "$ENV" | cut -d= -f2- | tr -d "\"'")

LIM=$((48 * 1024 * 1024))
SZ=$(stat -c%s "$F")
ENVIAR="$F"
if [ "$SZ" -gt "$LIM" ]; then
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$F")
  # bitrate de video que cabe no limite, descontando 192k de audio
  BR=$(python3 -c "print(max(500, int(($LIM*8/$DUR)/1000) - 200))")
  ENVIAR="/tmp/tg-$(basename "$F")"
  echo "[comprime] $((SZ/1048576))MB -> alvo 48MB (${BR}k)" >&2
  ffmpeg -y -loglevel error -i "$F" -c:v libx264 -profile:v high -pix_fmt yuv420p \
    -b:v "${BR}k" -maxrate "${BR}k" -bufsize "$((BR*2))k" -preset medium \
    -movflags +faststart -c:a aac -b:a 128k "$ENVIAR"
fi

W=$(ffprobe -v error -select_streams v -show_entries stream=width -of csv=p=0 "$ENVIAR")
H=$(ffprobe -v error -select_streams v -show_entries stream=height -of csv=p=0 "$ENVIAR")
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$ENVIAR" | cut -d. -f1)

curl -sS --max-time 900 -X POST "https://api.telegram.org/bot${TOKEN}/sendVideo" \
  -F chat_id="$CHAT" -F video="@$ENVIAR" -F caption="$CAP" \
  -F supports_streaming=true -F width="$W" -F height="$H" -F duration="$D" \
  | jq -r 'if .ok then "enviado: '"$(basename "$F")"'" else "FALHOU: \(.description)" end'
