# Como criamos os clipes

> Onde a produção parou e o que falta: **[ESTADO.md](ESTADO.md)**

Pipeline completo que transforma uma música gerada num clipe musical, sem
gerador de vídeo caro: imagem local, animação por keyframe e montagem em ffmpeg
seguindo um plano de cenas escrito à mão.

```
letra da música
   ↓  escrever as cenas (uma por trecho da letra)
cenas.json  ──►  flux2-klein (local)   ──►  foto-NN.png     22 imagens
   ↓  escrever o movimento de câmera de cada cena
movs.json   ──►  Agnes (keyframes)     ──►  clipe-NN.mp4    22 clipes de 5s
   ↓  receita da música (ordem, ritmo, texto)
receitas.py ──►  plano.json
   ↓
montar_plano.py ──► ffmpeg ──► CLIPE-<musica>-f<N>.mp4
```

## 1. As imagens (`gerar_fotos.py`)

Lê `cenas.json` da pasta do banco: uma lista de `{n, prompt}`. Cada prompt
descreve **uma cena da letra**, e recebe por cima um sufixo de acabamento fixo,
igual para todas as imagens do projeto:

**Sufixo de acabamento (LOOK), o mesmo em todas:**

```
raw documentary photograph, live-action cinema still, anamorphic 35mm,
natural skin texture and pores, film grain, practical light,
shallow depth of field, muted teal and amber grade
```

**Negativo, o mesmo em todas:**

```
cartoon, 3d render, cgi, pixar, anime, illustration, painting, plastic skin,
doll face, oversaturated, text, watermark, extra fingers, deformed
```

Modelo `flux2-klein` no inemaimg local (`localhost:8000`), 1312x736 para 16:9,
seed fixo por cena (`1000 + n`) para a imagem ser reproduzível.

**Consistência de personagem** sai de repetir a descrição física inteira em toda
cena onde a pessoa aparece ("a 28-year-old woman with dirty-blonde hair falling
past her shoulders and freckles across her nose"). Não existe truque melhor: se
a descrição encurta, o rosto muda.

Os prompts de cena de cada banco estão em [`bancos/`](bancos/).

## 2. A animação (`gerar_clipes.py`)

Cada foto vira um clipe de 5s na Agnes (`agnes-video-v2.0`, modo keyframes,
mesma imagem nos dois keyframes). O movimento de câmera vem de `movs.json`, uma
frase por cena — é o que diferencia um clipe do outro:

```
"slow push in on her face as she sits up, the blue window light shifting"
"macro slow push in on the hand scratching the name, raindrops striking"
"fast crane around the guitarist as he leans back, light streaks sweeping past"
```

O prompt enviado é sempre o mesmo molde, com essa frase no meio:

```
Smooth cinematic transition between the keyframes: <movimento>.
Natural motion, consistent characters and style, cinematic camera.
```

Serial e resumível: pula clipe que já existe. A Agnes tem **cota diária** e
devolve HTTP 429 com `Retry-After` quando estoura — o script faz backoff
progressivo até 8 tentativas.

## 3. A receita da música (`receitas.py`)

Aqui é onde cada música ganha identidade. **Não existe tabela única**: cada uma
declara seu banco, seu ritmo de corte e sua política de texto.

```python
R["a-roda"] = dict(banco="clipe-v3", xfade=0.35, cenas=[
 (10, 7, "cheio",  None,     None),
 (0,  5, "rajada", [9,2,7,10,4,13], None),
 (6,  7, "cheio",  None,     "EU NÃO INVENTEI A RODA"),
 ...])
```

Cada cena é `(número, peso de duração, modo, sobreposta, texto)`.

**Modos disponíveis:**

| modo | o que faz |
|---|---|
| `cheio` | o plano ocupa a tela toda |
| `fusao` | dupla exposição: outra cena dissolvida por cima (55% de opacidade) |
| `janela` | a cena principal cheia e outra numa janela no canto |
| `split` | duas ou três imagens dividindo a tela ao mesmo tempo |
| `rajada` | várias imagens em 0,28s cada, corte seco com zoom alternado |
| `preto` | tela preta com cartela de texto, usada como respiro antes do refrão |
| `insertos` | flashes de 0,22s de outra imagem por cima, sem cortar o plano |

**Duas regras que vieram de erro real:**

1. **Close de quem canta no máximo 4s.** A Agnes anima foto parada, então não há
   sincronia labial — segurar um rosto "cantando" por 12s denuncia na hora.
   As cenas de canto de cada banco estão listadas em `CANTANDO`.
2. **Nenhum plano passa de 11s.** Quando o teto encurta demais e sobra música,
   o script recicla cenas do próprio banco em vez de esticar uma só.

**Faixa 1 e faixa 2 têm montagem diferente.** O Suno devolve duas faixas por
geração; se as duas usassem a mesma ordem, os dois clipes ficariam iguais. A
faixa 2 gira o ponto de partida, inverte a gramática (cheio vira janela ou fusão
e vice-versa), corta metade das cartelas e usa crossfade 60% mais longo.

## 4. A montagem (`montar_plano.py`)

Monta cada cena na duração exata, encadeia por crossfade, corta no tempo do
áudio e queima a trilha por cima com fade.

**Armadilhas de ffmpeg que custaram caro aqui, todas resolvidas:**

- `xfade` entrega **yuv444p**. Sem forçar `format=yuv420p` e `-pix_fmt yuv420p`,
  o arquivo sai em perfil `High 4:4:4 Predictive` e **não toca** em celular, TV
  nem Telegram.
- `zoompan` gera `d=` quadros **por quadro de entrada**. Com `-loop 1 -t 7` a
  entrada tem 168 quadros e o clipe sai com 29.400 (1225s). A entrada precisa
  ser **uma imagem só**: `-loop 1 -framerate 1 -t 1`.
- `hstack` de 3 colunas em 1280px dá 1278px (1280÷3=426, ×3=1278). O `xfade`
  exige dimensões idênticas — daí `scale` e `setsar=1` em todo segmento.
- **ffmpeg consome o stdin** de quem o chama. Num laço `while read ... done <<<`
  no shell, o primeiro ffmpeg engole a lista e o laço morre depois de um item.
  Resolvido com `stdin=DEVNULL`.
- Texto com acento quebra dentro do filtro: usar `textfile=` e nunca `text=`.
  Fonte: Montserrat-ExtraBold.

## 5. Rodar

```bash
cd ~/projetos/output/musicas-video

# 1. imagens do banco (precisa do inemaimg em localhost:8000)
python3 gerar_fotos.py clipe-v3

# 2. animar (Agnes; serial, resumível, respeita cota)
python3 gerar_clipes.py clipe-v3

# 3. plano da música + montagem
python3 receitas.py a-roda ~/projetos/output/musicas/a-roda/faixa-1.mp3 \
        finais/CLIPE-a-roda-f1.mp4 /tmp/plano.json 1
python3 montar_plano.py /tmp/plano.json
```

## Os quatro bancos visuais

| banco | estética | usado por |
|---|---|---|
| **v2** | arena escura, feixe branco e neblina, história paralela | Se Paga, It's Paid, Legado |
| **v3** | moderno e alegre, luz do dia, coral, confete, cores saturadas | A Roda |
| **v4** | íntimo e documental, uma personagem, luz natural, sem palco | Não Se Desiste |
| **v5** | gráfico, azul e âmbar, simétrico, quase abstrato | O Centro |

Sem pirotecnia em nenhum: as referências de show serviram de gramática de
câmera (plano aberto de arena, macro no microfone, dupla exposição, reverso para
a plateia), não de cenografia.
