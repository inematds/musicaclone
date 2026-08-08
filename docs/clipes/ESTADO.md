# Estado da produção dos clipes

Atualizado: 2026-08-08

## Missão em aberto

Terminar os 12 clipes musicais (6 músicas × 2 faixas). Faltam duas coisas.

### 1. Animar os 2 clipes que faltam

Bancos animados: **130 de 132**.

| banco | música | animados |
|---|---|---|
| v2 | Se Paga (PT) | 22/22 |
| v3 | A Roda | 22/22 |
| v4 | Não Se Desiste | 22/22 |
| v5 | O Centro | 22/22 |
| **v6** | **Legado** | **20/22** — faltam `clipe-05` e `clipe-08` |
| v7 | It's Paid (EN) | 22/22 |

```bash
cd ~/projetos/output/musicas-video
python3 gerar_clipes.py clipe-v6      # serial, resumível, pula o que já existe
```

### 2. Remontar 10 dos 12 vídeos — legenda cortada

**Confirmado visualmente**, não por dedução: nos vídeos antigos a última letra
some. Exemplo real: uma cartela de 37 caracteres aparece truncada no penúltimo
caractere.

| clipe | legenda |
|---|---|
| `CLIPE-o-centro-f1` e `f2` | **corretos** (montados depois da correção) |
| os outros 10 | **precisam remontar** |

A correção já está no `montar_plano.py`: a cartela quebra em duas linhas
equilibradas e, se ainda não couber em 90% da largura, a fonte diminui até caber.
Basta rodar de novo.

```bash
cd ~/projetos/output/musicas-video
# exemplo para uma música/faixa
python3 receitas.py legado-pt ~/projetos/output/musicas/legado-pt/faixa-1.mp3 \
        finais/CLIPE-legado-pt-f1.mp4 /tmp/plano.json 1
python3 montar_plano.py /tmp/plano.json
```

Os slugs de receita são: `se-paga-pt`, `its-paid-en`, `legado-pt`,
`nao-se-desiste`, `o-centro`, `a-roda`. O último argumento é o número da faixa
(1 ou 2) — ele muda a montagem, não só a duração.

## Onde os arquivos ficam

- **Vídeos montados:** `~/projetos/output/musicas-video/finais/`
- **Destino de publicação:** a lives10 **reingere sozinha**. Copie para
  `~/projetos/yt-pub-lives10/imports/videos/` e o worker move para
  `lives/import_<AAAAMMDD>_videos/clips/`. **A pasta muda de nome conforme o dia**,
  então não guarde o caminho: procure com
  `find ~/projetos/yt-pub-lives10 -name 'CLIPE-*.mp4'`.
- **Áudios:** `~/projetos/output/musicas/<slug>/faixa-{1,2}.mp3`

## Pendência fora do escopo

O painel da lives10 não lista o lote porque a linha do import na tabela `lives`
(`data/lives.db`) está com `qtd_clips = 0` — o worker contou a pasta num momento
em que ela ainda estava incompleta, e depois os arquivos foram trocados por fora.
Os MP4 estão íntegros. A correção seria um `UPDATE` desse campo, mas o usuário
pediu para ignorar por ora.

## Como o pipeline funciona

Ver [README.md](README.md) nesta mesma pasta: etapas, prompts usados, os sete
modos de montagem e as armadilhas de ffmpeg já resolvidas (que voltam a morder
quem repetir o processo sem lê-las).
