# 🎵 musicaclone

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

CLI para **clonar** o **crear** música a partir de un enlace, usando Suno mediante la API de Kie.
Clonar y crear son procesos diferentes: el script los trata por separado y bloquea lo que suele salir mal durante el proceso.

## 📖 Guía de uso

Guía completa (landing + paso a paso): **https://inematds.github.io/musicaclone/guia/es/**

## 🎵 Catálogo de canciones

Todas las canciones generadas, con el prompt de estilo, las mediciones en gráficos y el reproductor: **https://inematds.github.io/musicaclone/guia/es/musicas.html**

## 🎬 Cómo creamos los clips

**Dónde se detuvo la producción:** [docs/clipes/ESTADO.md](docs/clipes/ESTADO.md)

Pipeline completo (imágenes con flux2-klein, animación por keyframe en Agnes, montaje en ffmpeg con plan de escenas), con los prompts usados y las dificultades resueltas: **[docs/clipes](docs/clipes/)**

## Por qué existe

Enviar el enlace de una canción a un agente genérico da malos resultados de tres maneras:
la transcribe en vez de generarla, genera a partir de un fragmento de 29 s creyendo que es
la canción completa, o genera con una letra que la transcripción cortó a la mitad.
Esta CLI pone una barrera en cada uno de esos puntos.

## Instalación

```bash
git clone https://github.com/inematds/musicaclone.git && cd musicaclone
sudo apt install jq ffmpeg && pipx install yt-dlp

cat > .env <<'EOF'
KIE_API_KEY=sua-chave-de-kie.ai/api-key
GOOGLE_API_KEY=sua-chave-do-gemini
EOF
```

Las claves se leen en tiempo de ejecución y nunca se versionan (el `.gitignore` cubre `.env`).

## Uso

```bash
# CLONAR — a partir de un enlace
bash musica.sh prep "https://youtube.com/watch?v=..." minha-faixa  # descarga + analiza (gratis)
bash musica.sh spec minha-faixa                                    # la barrera: comprueba antes
bash musica.sh clone minha-faixa --audio-weight 0.85               # genera (consume créditos)

# CREACIÓN — desde cero
bash musica.sh cria meu-tema --style "epic cinematic pop, female belt vocals, war drums, 118bpm" \
                             --title "Se Paga" --voz f --letra letra.txt
bash musica.sh regen meu-tema

# comunes
bash musica.sh status <slug|taskId>
bash musica.sh get <slug|taskId>     # descarga las pistas y mide el costo real
bash musica.sh saldo                 # créditos en Kie
bash enviar.sh faixa-1.mp3 "legenda" # envía por Telegram (opcional)
```

Salida en `~/projetos/output/musicas/<slug>/` (cambia con `MUSICA_OUT`):
`ref.mp3`, `analise.json`, `spec.json`, `faixa-1.mp3`, `faixa-2.mp3`.

## Las barreras

| Barrera | Qué detecta |
|---|---|
| **¿Es música?** | Gemini clasifica el audio. Entrevista, narración, ruido → bloquea e indica qué era. |
| **¿Letra completa?** | La voz cantada se corta fácilmente en la transcripción. Si llegó truncada, avisa antes de generar. Corrige con `--letra arquivo.txt`. |
| **¿Fuente corta?** | `spec` muestra la duración. 29 s es un teaser, no la canción. |
| **Costo** | No se genera nada sin que primero revises `spec`. El `taskId` se guarda antes del poll: si falla, retomas en vez de pagar otra vez. |

## Ajustes

`--model` (V4 … V5_5) · `--style` · `--negative` · `--voz m|f` · `--style-weight` ·
`--audio-weight` (solo clone: 0.9 se apega al original, 0.4 solo sirve de inspiración) · `--weirdness` ·
`--duration` (solo V5_5) · `--instrumental` · `--sem-referencia`.

Todo vive en `spec.json`, así que `regen` vuelve a generar con el ajuste sin repetir la descarga ni el análisis.

## Cómo escribir la letra (truco real)

La estructura y las indicaciones van entre **corchetes**; Suno suele **cantar**
los paréntesis como ad-libs. Es decir, `(Homem, falado, grave)` se convierte en una voz cantando «hombre,
hablado, grave». Lo correcto:

```
[Intro] [Spoken Word] [Male Vocal]
Nadie te cuenta el precio

[Chorus] [Female Vocal] [Belting]
¡Y yo voy! Aunque duela, aunque arda
(¡En la piedra!)          <- esto SÍ se debe cantar, así que los paréntesis están bien
[Gang Vocals]
Vale la pena, vale la pena
```

Etiquetas útiles: `[Verse]` `[Chorus]` `[Bridge]` `[Outro]` `[Male Vocal]`
`[Female Vocal]` `[Spoken Word]` `[Gang Vocals]` `[Belting]` `[Whisper]`.

## Costo (medido, 2026-08-05)

**12 créditos por generación** (V5, modo personalizado, 2 pistas de ~3 min) ≈ US$ 0,06 —
unos US$ 0,03 por pista utilizable. El script mide por sí solo y lo guarda en
`spec.json:creditos_gastos`.

Comparación: ElevenLabs Music cobra por minuto (~US$ 0,30–0,40/min, es decir,
~US$ 1,00–1,20 por pista de 3 min) y no clona referencias. Udio cobra créditos
por generación, pero no tiene una API pública madura. Suno directamente cuesta menos por canción con
la suscripción, pero no tiene una API oficial.

## API usada (verificada en 2026-08-05)

| Qué | Endpoint |
|---|---|
| crear desde cero | `POST https://api.kie.ai/api/v1/generate` |
| clonar con referencia | `POST https://api.kie.ai/api/v1/generate/upload-cover` |
| estado/resultado | `GET .../api/v1/generate/record-info?taskId=` |
| créditos | `GET .../api/v1/chat/credit` |
| subir el audio | `POST https://kieai.redpandaai.co/api/file-stream-upload` |

Referencia: máx. 8 min. El archivo enviado desaparece en 24 h y la pista generada en 15 días;
por eso `get` la descarga de inmediato. `callBackUrl` es obligatorio en la práctica (422 sin él),
aunque la documentación lo marque como opcional; enviamos un placeholder y usamos poll.

## Licencia

MIT.
