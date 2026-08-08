# 🎵 musicaclone

CLI para **clonar** ou **criar** música a partir de um link, usando Suno pela API do Kie.
Clonar e criar são caminhos diferentes — o script trata assim, e trava o que costuma dar errado no meio.

## 📖 Guia de uso

Guia completo (landing + passo a passo): **https://inematds.github.io/musicaclone/guia/**

## 🎵 Catálogo das músicas

Todas as músicas geradas, com o prompt de estilo, as medições em gráfico e o player: **https://inematds.github.io/musicaclone/guia/musicas.html**

## 🎬 Como criamos os clipes

Pipeline completo (imagens no flux2-klein, animação por keyframe na Agnes, montagem em ffmpeg com plano de cenas), com os prompts usados e as armadilhas resolvidas: **[docs/clipes](docs/clipes/)**

## Por que existe

Mandar um link de música pra um agente genérico dá resultado ruim de três jeitos:
ele transcreve em vez de gerar, gera em cima de um trecho de 29 s achando que é a
música inteira, ou gera com uma letra que a transcrição cortou pela metade.
Este CLI põe um portão em cada um desses pontos.

## Instalação

```bash
git clone https://github.com/inematds/musicaclone.git && cd musicaclone
sudo apt install jq ffmpeg && pipx install yt-dlp

cat > .env <<'EOF'
KIE_API_KEY=sua-chave-de-kie.ai/api-key
GOOGLE_API_KEY=sua-chave-do-gemini
EOF
```

As chaves são lidas em runtime e nunca versionadas (o `.gitignore` cobre `.env`).

## Uso

```bash
# CLONE — a partir de um link
bash musica.sh prep "https://youtube.com/watch?v=..." minha-faixa  # baixa + analisa (grátis)
bash musica.sh spec minha-faixa                                    # o portão: confira antes
bash musica.sh clone minha-faixa --audio-weight 0.85               # gera (gasta crédito)

# CRIAÇÃO — do zero
bash musica.sh cria meu-tema --style "epic cinematic pop, female belt vocals, war drums, 118bpm" \
                             --title "Se Paga" --voz f --letra letra.txt
bash musica.sh regen meu-tema

# comuns
bash musica.sh status <slug|taskId>
bash musica.sh get <slug|taskId>     # baixa as faixas e mede o custo real
bash musica.sh saldo                 # créditos no Kie
bash enviar.sh faixa-1.mp3 "legenda" # manda no Telegram (opcional)
```

Saída em `~/projetos/output/musicas/<slug>/` (mude com `MUSICA_OUT`):
`ref.mp3`, `analise.json`, `spec.json`, `faixa-1.mp3`, `faixa-2.mp3`.

## Os portões

| Portão | O que pega |
|---|---|
| **É música?** | Gemini classifica o áudio. Entrevista, narração, ruído → bloqueia e diz o que era. |
| **Letra completa?** | Voz cantada corta fácil na transcrição. Se veio truncada, avisa antes de gerar. Corrige com `--letra arquivo.txt`. |
| **Fonte curta?** | O `spec` mostra a duração. 29 s é teaser, não é a música. |
| **Custo** | Nada gera sem você olhar o `spec` primeiro. O `taskId` é gravado antes do poll: se cair, você retoma em vez de pagar de novo. |

## Ajustes

`--model` (V4 … V5_5) · `--style` · `--negative` · `--voz m|f` · `--style-weight` ·
`--audio-weight` (só clone: 0.9 cola no original, 0.4 só inspira) · `--weirdness` ·
`--duration` (só V5_5) · `--instrumental` · `--sem-referencia`.

Tudo vive no `spec.json`, então `regen` refaz com o ajuste sem repetir download nem análise.

## Escrevendo a letra (pegadinha real)

Estrutura e direção vão em **colchetes**; parênteses o Suno costuma **cantar**
como ad-lib. Ou seja, `(Homem, falado, grave)` vira vocal cantando "homem,
falado, grave". O certo:

```
[Intro] [Spoken Word] [Male Vocal]
Ninguém te conta o preço

[Chorus] [Female Vocal] [Belting]
E eu vou! Mesmo que doa, mesmo que arda
(Na pedra!)          <- isto SIM é pra ser cantado, então parêntese está certo
[Gang Vocals]
Vale a pena, vale a pena
```

Tags úteis: `[Verse]` `[Chorus]` `[Bridge]` `[Outro]` `[Male Vocal]`
`[Female Vocal]` `[Spoken Word]` `[Gang Vocals]` `[Belting]` `[Whisper]`.

## Custo (medido, 2026-08-05)

**12 créditos por geração** (V5, custom mode, 2 faixas de ~3 min) ≈ US$ 0,06 —
uns US$ 0,03 por faixa utilizável. O script mede sozinho e grava em
`spec.json:creditos_gastos`.

Comparativo: ElevenLabs Music cobra por minuto (~US$ 0,30–0,40/min, ou seja
~US$ 1,00–1,20 por faixa de 3 min) e não faz clone de referência. Udio é crédito
por geração mas sem API pública madura. Suno direto sai mais barato por música na
assinatura, só que sem API oficial.

## API usada (verificada em 2026-08-05)

| O quê | Endpoint |
|---|---|
| criar do zero | `POST https://api.kie.ai/api/v1/generate` |
| clone com referência | `POST https://api.kie.ai/api/v1/generate/upload-cover` |
| status/resultado | `GET .../api/v1/generate/record-info?taskId=` |
| créditos | `GET .../api/v1/chat/credit` |
| upload do áudio | `POST https://kieai.redpandaai.co/api/file-stream-upload` |

Referência: máx 8 min. Arquivo enviado some em 24 h, faixa gerada em 15 dias —
por isso `get` baixa na hora. `callBackUrl` é obrigatório na prática (422 sem ele),
mesmo o doc marcando como opcional; mandamos um placeholder e usamos poll.

## Licença

MIT.
