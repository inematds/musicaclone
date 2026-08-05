#!/usr/bin/env bash
# musica.sh — clonar OU criar musica via Kie (Suno). Ver SKILL.md.
# Estado por faixa em $OUT/<slug>/spec.json. Nada gera sem passar pelo portao.
#
# CLONAR (a partir de um link):
#   musica.sh prep <url> [slug]      resolve + baixa + analisa -> spec.json
#   musica.sh spec <slug>            resumo pro portao de confirmacao
#   musica.sh clone <slug> [flags]   gera usando o audio original como referencia
#
# CRIAR (do zero, sem referencia):
#   musica.sh cria <slug> --style "..." --title "..." [--letra arq|--instrumental]
#
# COMUNS:
#   musica.sh status <slug|taskId>
#   musica.sh get <slug|taskId>      baixa as faixas (URL do Suno expira)
#   musica.sh regen <slug> [flags]   gera de novo com ajustes, sem reanalisar
#
# Flags de ajuste (clone/cria/regen):
#   --model V4|V4_5|V4_5PLUS|V4_5ALL|V5|V5_5   (default V5)
#   --style "tags"    --title "..."   --negative "tags"
#   --voz m|f         --instrumental
#   --style-weight 0-1     adesao ao estilo descrito
#   --audio-weight 0-1     (so clone) quanto puxa a referencia. 0.9 = mais colado
#   --weirdness 0-1        desvio criativo
#   --duration N           so no model V5_5
#   --sem-referencia       clone vira recriacao so por estilo
set -euo pipefail

SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${MUSICA_OUT:-$HOME/projetos/output/musicas}"
KIE="https://api.kie.ai/api/v1"
KIE_UPLOAD="https://kieai.redpandaai.co/api/file-stream-upload"

# Chaves lidas em runtime, nunca versionadas. Ordem: .env local do projeto,
# depois os .env pessoais. Precisa de KIE_API_KEY e GOOGLE_API_KEY.
set -a
for f in "$SELF/.env" "$HOME/projetos/wifi/.env" "$HOME/projetos/openpcbotv2/.env"; do
  [ -f "$f" ] && . "$f"
done
set +a
: "${KIE_API_KEY:?KIE_API_KEY nao encontrada (ponha num .env: kie.ai/api-key)}"

jqf() { jq -r "${1}" "$2" 2>/dev/null; }
put() { # put <spec.json> <jq-expr> [--arg ...]
  local f="$1"; shift; local e="$1"; shift
  jq "$@" "$e" "$f" > "$f.t" && mv "$f.t" "$f"
}
dir_of() { # slug ou taskId -> diretorio. Vazio nunca: erra alto.
  [ -d "$OUT/$1" ] && { echo "$OUT/$1"; return; }
  local d; d=$(dir_try "$1")
  [ -n "$d" ] || { echo "slug/taskId nao encontrado: $1 (veja $OUT)" >&2; exit 1; }
  echo "$d"
}
dir_try() { # igual, mas devolve vazio em vez de falhar (status/get aceitam taskId solto)
  [ -d "$OUT/$1" ] && { echo "$OUT/$1"; return; }
  grep -rl "\"taskId\": *\"$1\"" "$OUT"/*/spec.json 2>/dev/null | head -1 | xargs -r dirname
}

# --------------------------------------------------------------- CLONAR: prep
cmd_prep() {
  local url="$1" slug="${2:-}"
  echo "[1/4] resolvendo link..." >&2
  local meta title dur uploader page
  meta=$(yt-dlp --no-warnings -J "$url")
  title=$(jq -r '.title // "sem titulo"' <<<"$meta")
  dur=$(jq -r '.duration // 0' <<<"$meta")
  uploader=$(jq -r '.uploader // ""' <<<"$meta")
  page=$(jq -r '.webpage_url // ""' <<<"$meta")
  [ -n "$slug" ] || slug=$(echo "${uploader}-${title}" | tr '[:upper:]' '[:lower:]' \
    | sed 's/[^a-z0-9]\+/-/g; s/^-//; s/-$//' | cut -c1-50)
  local d="$OUT/$slug" s
  mkdir -p "$d"; s="$d/spec.json"

  jq -n --arg s "$slug" --arg t "$title" --arg u "$uploader" --arg p "$page" \
        --arg o "$url" --argjson dur "$dur" \
    '{slug:$s, tipo:"clone", titulo_fonte:$t, artista:$u, url_original:$o,
      url_resolvida:$p, duracao_s:$dur, model:"V5", criado_em:(now|todate)}' > "$s"

  echo "[2/4] baixando audio..." >&2
  yt-dlp --no-warnings -x --audio-format mp3 -o "$d/ref.%(ext)s" "$url" >&2
  [ -f "$d/ref.mp3" ] || { echo "falhou baixar o audio"; exit 1; }

  echo "[3/4] analisando (Gemini)..." >&2
  python3 "$SELF/analisa.py" "$d/ref.mp3" "$dur" > "$d/analise.json"

  local a="$d/analise.json"
  if [ "$(jqf .e_musica "$a")" != "true" ]; then
    jq -s '.[0] * {analise:.[1], bloqueado:"nao e musica"}' "$s" "$a" > "$s.t" && mv "$s.t" "$s"
    cmd_spec "$slug"; return 3
  fi

  echo "[4/4] montando spec..." >&2
  jq -s '.[0] * {
      analise: .[1],
      style:        (.[1].tags_suno // [] | join(", ")),
      title:        (.[1].titulo_sugerido // .[0].titulo_fonte)[0:70],
      negativeTags: (.[1].negative_tags // [] | join(", ")),
      vocalGender:  (.[1].voz.genero // "m"),
      letra:        .[1].letra,
      letra_completa: (.[1].letra_completa // false),
      instrumental: ((.[1].tem_vocal // true) | not),
      audioWeight: 0.65, styleWeight: 0.7,
      modo: (if .[0].duracao_s > 480 then "estilo" else "cover" end)
    }' "$s" "$a" > "$s.t" && mv "$s.t" "$s"
  cmd_spec "$slug"
}

# --------------------------------------------------------------- CRIAR do zero
cmd_cria() {
  local slug="$1"; shift
  local d="$OUT/$slug"; mkdir -p "$d"
  jq -n --arg s "$slug" '{slug:$s, tipo:"criacao", model:"V5", modo:"estilo",
                          instrumental:false, styleWeight:0.7, criado_em:(now|todate)}' > "$d/spec.json"
  parse_flags "$d/spec.json" "$@"
  cmd_spec "$slug"
  echo
  echo "spec criado. Rode: musica.sh regen $slug   (depois do ok do usuario)"
}

parse_flags() { # parse_flags <spec.json> [flags...]
  local s="$1"; shift
  while [ $# -gt 0 ]; do
    case "$1" in
      --model)        put "$s" '.model=$v'        --arg v "$2"; shift 2;;
      --style)        put "$s" '.style=$v'        --arg v "$2"; shift 2;;
      --title)        put "$s" '.title=$v'        --arg v "$2"; shift 2;;
      --negative)     put "$s" '.negativeTags=$v' --arg v "$2"; shift 2;;
      --voz)          put "$s" '.vocalGender=$v'  --arg v "$2"; shift 2;;
      # letra vinda de arquivo = letra oficial: mata o alerta de truncamento
      --letra)        put "$s" '.letra=$v | .letra_completa=true | del(.analise._palavras_letra)' \
                          --arg v "$(cat "$2")"; shift 2;;
      --style-weight) put "$s" '.styleWeight=($v|tonumber)' --arg v "$2"; shift 2;;
      --audio-weight) put "$s" '.audioWeight=($v|tonumber)' --arg v "$2"; shift 2;;
      --weirdness)    put "$s" '.weirdnessConstraint=($v|tonumber)' --arg v "$2"; shift 2;;
      --duration)     put "$s" '.duration=($v|tonumber)' --arg v "$2"; shift 2;;
      --instrumental) put "$s" '.instrumental=true'; shift;;
      --sem-referencia) put "$s" '.modo="estilo"'; shift;;
      # usa um ref.mp3 ja colocado na pasta como referencia (ex.: refazer a
      # mesma musica em outro idioma mantendo a melodia)
      --cover)        put "$s" '.modo="cover"'; shift;;
      *) echo "flag desconhecida: $1" >&2; shift;;
    esac
  done
}

# ------------------------------------------------------------------ portao
cmd_spec() {
  local d s; d=$(dir_of "$1"); s="$d/spec.json"
  echo "--- $(jqf .slug "$s")  [$(jqf .tipo "$s")] ---"
  if [ "$(jqf .tipo "$s")" = "clone" ]; then
    echo "fonte:    $(jqf .titulo_fonte "$s")"
    echo "artista:  $(jqf .artista "$s")   duracao: $(jqf .duracao_s "$s")s"
    echo "url:      $(jqf .url_resolvida "$s")"
  fi
  if [ "$(jqf .bloqueado "$s")" != "null" ]; then
    echo "BLOQUEADO: $(jqf .bloqueado "$s") — $(jqf .analise.motivo "$s")"
    return
  fi
  echo "modo:     $(jqf .modo "$s")  (cover = usa o audio original como referencia)"
  echo "model:    $(jqf .model "$s")   voz: $(jqf .vocalGender "$s")   instrumental: $(jqf .instrumental "$s")"
  echo "style:    $(jqf .style "$s")"
  echo "evitar:   $(jqf .negativeTags "$s")"
  echo "pesos:    style=$(jqf .styleWeight "$s") audio=$(jqf .audioWeight "$s") weirdness=$(jqf .weirdnessConstraint "$s")"
  if [ "$(jqf .instrumental "$s")" != "true" ]; then
    local pal; pal=$(jqf .analise._palavras_letra "$s")
    echo "letra completa? $(jqf .letra_completa "$s")$([ "$pal" != "null" ] && echo "  ($pal palavras)")"
    echo "letra (inicio):"; jqf .letra "$s" | head -6 | sed 's/^/  /'
  fi
  echo "custo:    ver SKILL.md (creditos Kie/Suno) — confirmar consumo real na 1a geracao."
  [ "$(jqf .modo "$s")" = "cover" ] && \
    echo "AVISO: no modo cover o audio de referencia e publicado no Kie (apagado em 24h)."
  return 0
}

# ---------------------------------------------------------------- geracao
gerar() { # gerar <slug> ; le tudo do spec
  local d s; d=$(dir_of "$1"); s="$d/spec.json"
  [ "$(jqf .bloqueado "$s")" = "null" ] || { echo "spec bloqueado, nao gero."; exit 1; }
  local modo model url body
  modo=$(jqf .modo "$s"); model=$(jqf .model "$s"); url="$KIE/generate"

  # callBackUrl e obrigatorio na pratica (422 sem ele), mesmo o doc marcando
  # como opcional. Nao temos endpoint publico: mandamos um placeholder e usamos poll.
  body=$(jq --arg cb "${MUSICA_CALLBACK:-https://example.com/kie-callback}" \
            '{prompt: (.letra // ""), style, title, negativeTags, model,
              callBackUrl: $cb,
              customMode: true, instrumental: (.instrumental // false)}
             + (if .vocalGender=="m" or .vocalGender=="f" then {vocalGender} else {} end)
             + (if .styleWeight then {styleWeight} else {} end)
             + (if .weirdnessConstraint then {weirdnessConstraint} else {} end)
             + (if .duration and .model=="V5_5" then {duration} else {} end)' "$s")

  if [ "$modo" = "cover" ] && [ -f "$d/ref.mp3" ]; then
    echo "[upload] subindo ref.mp3 pro Kie..." >&2
    local up furl
    up=$(curl -sS -X POST "$KIE_UPLOAD" -H "Authorization: Bearer $KIE_API_KEY" \
      -F "file=@$d/ref.mp3" -F "uploadPath=audio" -F "fileName=$(jqf .slug "$s").mp3")
    furl=$(jq -r '.data.downloadUrl // .data.fileUrl // empty' <<<"$up")
    if [ -z "$furl" ]; then
      echo "upload falhou ($(jq -r '.msg? // "?"' <<<"$up")) — caindo pro modo estilo." >&2
      modo="estilo"
    else
      put "$s" '.uploadUrl=$v' --arg v "$furl"
      url="$KIE/generate/upload-cover"
      body=$(jq --arg u "$furl" --argjson aw "$(jqf .audioWeight "$s")" \
                '. + {uploadUrl:$u, audioWeight:$aw}' <<<"$body")
    fi
  fi

  # saldo nunca pode derrubar a gravacao do taskId depois do POST: default 0.
  local antes; antes=$(saldo || true); antes=${antes:-0}
  case "$antes" in ''|*[!0-9.]*) antes=0;; esac
  echo "[gen] POST $url  ($modo / $model)  saldo antes: $antes" >&2
  local resp task
  resp=$(curl -sS -X POST "$url" -H "Authorization: Bearer $KIE_API_KEY" \
    -H "Content-Type: application/json" -d "$body")
  task=$(jq -r '.data.taskId // empty' <<<"$resp")
  [ -n "$task" ] || { echo "erro do Kie: $resp"; exit 1; }
  # grava o taskId ANTES de qualquer poll: se o poll morrer, o dinheiro ja foi.
  jq --arg t "$task" --arg m "$modo" --argjson b "$body" --argjson c "$antes" \
     '. + {taskId:$t, modo_usado:$m, request:$b, creditos_antes:$c,
           historico: ((.historico // []) + [{taskId:$t, em:(now|todate)}])}' \
     "$s" > "$s.t" && mv "$s.t" "$s"
  echo "taskId: $task"
}

saldo() { curl -sS "$KIE/chat/credit" -H "Authorization: Bearer $KIE_API_KEY" | jq -r '.data // 0'; }
cmd_saldo() { echo "creditos Kie: $(saldo)"; }

cmd_clone() { local slug="$1"; shift; parse_flags "$(dir_of "$slug")/spec.json" "$@"; gerar "$slug"; }
cmd_regen() { cmd_clone "$@"; }

cmd_status() {
  local d task; d=$(dir_try "$1"); task="$1"
  [ -n "$d" ] && task=$(jqf .taskId "$d/spec.json")
  curl -sS "$KIE/generate/record-info?taskId=$task" -H "Authorization: Bearer $KIE_API_KEY" \
    | jq -r '.data | "\(.status)  \(.errorMessage // "")  faixas: \((.response.sunoData // []) | length)"'
}

cmd_get() {
  local d task r st i=1
  d=$(dir_try "$1"); task="$1"
  if [ -n "$d" ]; then task=$(jqf .taskId "$d/spec.json"); else d="$OUT/$1"; mkdir -p "$d"; fi
  r=$(curl -sS "$KIE/generate/record-info?taskId=$task" -H "Authorization: Bearer $KIE_API_KEY")
  st=$(jq -r '.data.status' <<<"$r")
  [ "$st" = "SUCCESS" ] || { echo "ainda nao: $st $(jq -r '.data.errorMessage // ""' <<<"$r")"; exit 2; }
  echo "$r" > "$d/resultado.json"
  # custo real = saldo antes - saldo agora (medido, nao estimado)
  local antes agora
  antes=$(jqf .creditos_antes "$d/spec.json"); agora=$(saldo || true)
  case "$antes" in ''|null|*[!0-9.]*) antes=0;; esac
  case "$agora" in ''|null|*[!0-9.]*) agora=0;; esac
  if [ "$antes" != "0" ] && [ "$agora" != "0" ]; then
    put "$d/spec.json" '.creditos_gastos=($a|tonumber)-($b|tonumber)' --arg a "$antes" --arg b "$agora"
    echo "creditos gastos: $(jqf .creditos_gastos "$d/spec.json")"
  fi
  while read -r au; do
    curl -sSL "$au" -o "$d/faixa-$i.mp3" && echo "$d/faixa-$i.mp3"
    i=$((i+1))
  done < <(jq -r '.data.response.sunoData[].audioUrl' <<<"$r")
}

case "${1:-}" in
  prep)   shift; cmd_prep "$@";;
  spec)   shift; cmd_spec "$@";;
  clone)  shift; cmd_clone "$@";;
  cria)   shift; cmd_cria "$@";;
  regen)  shift; cmd_regen "$@";;
  status) shift; cmd_status "$@";;
  saldo)  shift; cmd_saldo "$@";;
  get)    shift; cmd_get "$@";;
  *) sed -n '2,30p' "$0"; exit 1;;
esac
