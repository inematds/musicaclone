# Análise de VOZ — referência de performance ao vivo

Data: 2026-08-06
Fonte: `https://www.youtube.com/watch?v=LnuxV1WO36c` (Michael Bennett, AGT) — 578s
Analisado **só o áudio**. Nada de vídeo.
Método: medição acústica própria (`analisa_voz.py`, numpy/scipy) + leitura
qualitativa do Gemini sobre o trecho 470-570s (o pico de canto).

---

## 1. O que foi MEDIDO (números, não impressão)

| Métrica | Valor |
|---|---|
| Apoio central (mediana f0) | 282 Hz — C#4 |
| Base útil (p05) | 115 Hz — A#2 |
| Topo útil (p99) | 695 Hz — F5 |
| Extensão útil | ~31 semitons (2,6 oitavas) |
| Vibrato — taxa | **7,0 Hz** |
| Vibrato — profundidade | **~46 cents** |
| Nota sustentada mediana | 0,42s (mais longa 0,9s) |
| Saltos > 200 cents | 175 |
| Faixa dinâmica útil | 14,9 dB (crest factor 17 dB) |
| Brilho (centroide cantando) | mediana 2349 Hz, p90 3072 Hz |
| Ruidosidade (flatness) | 0,335 |

**Distribuição de registro:** médio-grave 40%, agudo/belt 29%, médio-agudo 22%,
grave 7%. Ou seja: a voz **mora no médio-grave e sobe pro belt**, não fica no
agudo o tempo todo.

**Arco da performance:** os primeiros ~360s têm pouca voz (apresentação, plateia).
O canto denso vai de 390s ao fim — e é lá que a densidade sobe pra 55-67% e o
volume sobe ~4 dB. A performance **cresce até o fim**, não abre no pico.

### CORREÇÃO (2026-08-06, mesma sessão)

Os números da tabela acima são do **vídeo 1** e **não devem ser usados como
referência vocal**. Ao comparar com o segundo link
(`https://www.youtube.com/watch?v=-johaHxpk4I`, 529s) ficou claro que:

- o vídeo 1 tem só **12% de quadros com voz** depois do filtro — baixo demais
  para uma apresentação cantada;
- no mesmo tipo de trecho, a **ruidosidade (flatness)** do vídeo 1 é 0,292
  contra **0,060** do vídeo 2, e o vídeo 1 rende 3 notas sustentadas contra 43.

Ou seja, o vídeo 1 é captação suja / material misturado, e as médias do arquivo
inteiro estavam contaminadas por banda e plateia. **A referência boa é o vídeo 2.**
Eu havia afirmado que era "a mesma voz, sem dúvida" a partir das médias
agregadas — estava errado; a comparação por trecho não sustenta isso.

### Medição do VÍDEO 2 (a que vale)

| Métrica | Valor |
|---|---|
| Apoio central (mediana f0) | 294 Hz — D4 |
| Base útil (p05) | 124 Hz — B2 |
| Topo útil (p99) | 697 Hz — F5 |
| Extensão útil | ~30 semitons |
| Vibrato | **7,2 Hz / ~53 cents** |
| Notas sustentadas >0,35s | **182** (mais longa 3,1s, mediana 0,61s) |
| Saltos > 200 cents | 418 |
| Faixa dinâmica útil | **41,1 dB** (crest 19,3 dB) |
| Brilho (centroide) | 1748 Hz (p90 2196) |

Registro: médio-agudo 47%, médio-grave 26%, agudo/belt 18%, grave 8%.

O que mais importa aqui: **41 dB de faixa dinâmica** contra 15 dB do vídeo 1, e
182 notas sustentadas contra 31. É uma performance de contraste real, que
sustenta frase e depois abre — exatamente o oposto de intensidade constante.

### Ressalva honesta sobre a medição
São dois valores em que não confio e não devem virar regra:
- O **topo (F5)** provavelmente inclui instrumento da banda vazando na detecção.
  É gravação ao vivo com banda e plateia, não voz isolada.
- Tive que **jogar fora dois passos** antes de chegar nesses números: a primeira
  medição deu vibrato de 559 cents (impossível) por erro de oitava da
  autocorrelação, e a segunda ainda empilhava tudo no teto do detector.
  Confiáveis mesmo: vibrato, distribuição de registro, dinâmica e o arco.

## 2. O que a ESCUTA qualitativa diz

- **Timbre:** grave, escuro, encorpado — barítono/tenor dramático. Textura
  rasgada e saturada; alterna aveludado com ar nos trechos baixos e drive áspero
  sob pressão.
- **Registro:** apoio forte de peito no grave e médio. **Não usa falsete.**
  Sobe de peito puro para um *mix* comprimido e impulsionado. A tensão no agudo
  é intencional, no limite da sobrecarga controlada.
- **Jogo da voz:** ataques arrastados por baixo (*scoop*) nas partes calmas;
  ataques diretos e percussivos nos picos. Muito glissando e curva de blues,
  **sem melisma rápido** — prefere nota reta que abre em vibrato largo e lento
  no fim da sustentação. Canta **atrasado** (*layback*), jogando contra a
  bateria. Termina frase deixando o ar escapar ou com descompressão gutural.
- **Dinâmica:** contraste extremo, sem meio-termo. Entra contido no grave,
  explode direto em belt rasgado, recolhe abruptamente para sussurro.
- **Emoção:** de mágoa contida para catarse de raiva. A distorção é veículo de
  esforço físico, não enfeite.

Os dois métodos batem: vibrato de 7 Hz e 46 cents **é** o "vibrato largo e lento
no fim da sustentação"; 175 saltos grandes **é** o glissando; 14,9 dB de faixa
dinâmica **é** o contraste extremo.

## 3. Como pedir isso ao Suno

Tags sugeridas (a partir do comportamento medido, não do gênero):

```
raspy male vocals, soulful grit, gravelly baritone, driven chest mix,
intense distorted belt, no falsetto, wide slow vibrato, scooped attacks,
bluesy glissando, laid back phrasing, extreme dynamic contrast, live raw take
```

**Comparação com o que já usamos em "Se Paga"** (`epic cinematic anthem,
screaming female belting, raspy desperate female vocals, deep cavernous male
baritone...`): o que falta lá e esta referência entrega é o **contraste
dinâmico** e o **fraseado atrasado**. Hoje nosso prompt pede intensidade o tempo
todo, e intensidade constante achata. A referência prova o contrário: ela vale
porque tem de onde subir.

## 4. Como isso muda o clipe

O arco medido (contido → catarse, crescendo até o fim) é exatamente o arco do
plano de cenas: a bridge recolhe, o último refrão explode. Vale sincronizar o
corte com a **dinâmica** e não só com a batida — cortar curto onde o dB sobe e
segurar o plano onde a voz recolhe.

Referência cruzada: [plano de cenas](2026-08-05-plano-de-cenas-clipe.md).
