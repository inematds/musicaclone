# 🎵 musicaclone

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

CLI to **clone** or **create** music from a link, using Suno through the Kie API.
Cloning and creating are different paths—the script handles them that way and blocks the things that commonly go wrong along the way.

## 📖 User guide

Complete guide (landing page + step-by-step instructions): **https://inematds.github.io/musicaclone/guia/en/**

## 🎵 Song catalog

All generated songs, with the style prompt, charted measurements, and player: **https://inematds.github.io/musicaclone/guia/en/musicas.html**

## 🎬 How we create the clips

**Where production stopped:** [docs/clipes/ESTADO.md](docs/clipes/ESTADO.md)

Complete pipeline (images with flux2-klein, keyframe animation in Agnes, assembly in ffmpeg with a scene plan), including the prompts used and the pitfalls resolved: **[docs/clipes](docs/clipes/)**

## Why it exists

Sending a music link to a generic agent produces bad results in three ways:
it transcribes instead of generating, generates from a 29 s excerpt thinking it's the
whole song, or generates with lyrics that the transcription cut off halfway through.
This CLI puts a gate at each of these points.

## Installation

```bash
git clone https://github.com/inematds/musicaclone.git && cd musicaclone
sudo apt install jq ffmpeg && pipx install yt-dlp

cat > .env <<'EOF'
KIE_API_KEY=sua-chave-de-kie.ai/api-key
GOOGLE_API_KEY=sua-chave-do-gemini
EOF
```

Keys are read at runtime and never committed (`.gitignore` covers `.env`).

## Usage

```bash
# CLONE — from a link
bash musica.sh prep "https://youtube.com/watch?v=..." minha-faixa  # download + analyze (free)
bash musica.sh spec minha-faixa                                    # the gate: review before proceeding
bash musica.sh clone minha-faixa --audio-weight 0.85               # generate (uses credits)

# CREATION — from scratch
bash musica.sh cria meu-tema --style "epic cinematic pop, female belt vocals, war drums, 118bpm" \
                             --title "Se Paga" --voz f --letra letra.txt
bash musica.sh regen meu-tema

# common commands
bash musica.sh status <slug|taskId>
bash musica.sh get <slug|taskId>     # downloads the tracks and measures the actual cost
bash musica.sh saldo                 # Kie credits
bash enviar.sh faixa-1.mp3 "legenda" # sends via Telegram (optional)
```

Output in `~/projetos/output/musicas/<slug>/` (change with `MUSICA_OUT`):
`ref.mp3`, `analise.json`, `spec.json`, `faixa-1.mp3`, `faixa-2.mp3`.

## The gates

| Gate | What it catches |
|---|---|
| **Is it music?** | Gemini classifies the audio. Interview, narration, noise → blocked, with an explanation of what it was. |
| **Complete lyrics?** | Sung vocals are often cut off in transcription. If they were truncated, it warns you before generating. Correct with `--letra arquivo.txt`. |
| **Short source?** | `spec` shows the duration. 29 s is a teaser, not the song. |
| **Cost** | Nothing is generated until you review the `spec` first. The `taskId` is saved before polling: if it fails, you can resume instead of paying again. |

## Settings

`--model` (V4 … V5_5) · `--style` · `--negative` · `--voz m|f` · `--style-weight` ·
`--audio-weight` (clone only: 0.9 sticks close to the original, 0.4 is inspiration only) · `--weirdness` ·
`--duration` (V5_5 only) · `--instrumental` · `--sem-referencia`.

Everything lives in `spec.json`, so `regen` regenerates with the updated settings without repeating the download or analysis.

## Writing lyrics (a real gotcha)

Structure and direction go in **square brackets**; Suno tends to **sing**
parentheses as ad-libs. In other words, `(Man, spoken, deep)` becomes vocals singing "man,
spoken, deep." The correct format:

```
[Intro] [Spoken Word] [Male Vocal]
Nobody tells you the price

[Chorus] [Female Vocal] [Belting]
And I'll go! Even if it hurts, even if it burns
(On the stone!)       <- this IS meant to be sung, so parentheses are correct
[Gang Vocals]
It's worth it, it's worth it
```

Useful tags: `[Verse]` `[Chorus]` `[Bridge]` `[Outro]` `[Male Vocal]`
`[Female Vocal]` `[Spoken Word]` `[Gang Vocals]` `[Belting]` `[Whisper]`.

## Cost (measured, 2026-08-05)

**12 credits per generation** (V5, custom mode, 2 tracks of ~3 min) ≈ US$ 0.06 —
about US$ 0.03 per usable track. The script measures this automatically and saves it in
`spec.json:creditos_gastos`.

Comparison: ElevenLabs Music charges by the minute (~US$ 0.30–0.40/min, or
~US$ 1.00–1.20 per 3-minute track) and doesn't clone from a reference. Udio charges
per generation but has no mature public API. Suno directly costs less per song with a
subscription, but has no official API.

## API used (verified 2026-08-05)

| What | Endpoint |
|---|---|
| create from scratch | `POST https://api.kie.ai/api/v1/generate` |
| clone with reference | `POST https://api.kie.ai/api/v1/generate/upload-cover` |
| status/result | `GET .../api/v1/generate/record-info?taskId=` |
| credits | `GET .../api/v1/chat/credit` |
| audio upload | `POST https://kieai.redpandaai.co/api/file-stream-upload` |

Reference: max 8 min. Uploaded file disappears after 24 h, generated track after 15 days—
so `get` downloads it right away. `callBackUrl` is required in practice (422 without it),
even though the docs mark it as optional; we send a placeholder and use polling.

## License

MIT.
