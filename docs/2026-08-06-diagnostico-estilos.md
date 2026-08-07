# Diagnóstico dos estilos e prompts — as 6 músicas

Data: 2026-08-06

Cada bloco traz: o **prompt de estilo enviado ao Suno**, o que foi **medido no
resultado**, o diagnóstico e a **produção de vídeo** que essa música recebe.
Medições feitas com `analisa_voz.py` (numpy/scipy).

---

## Quadro comparativo

| música | bpm | faixa dinâmica | notas sustentadas | vibrato | diagnóstico |
|---|---|---|---|---|---|
| Legado (variante) | 118 | — | — | — | mais contida que "Se Paga", serviu de rascunho |
| Se Paga (PT) | 118 | **16,4 dB** | **2** | 7 cents | achatada: intensidade constante |
| It's Paid (EN) | 118 | ~16 dB | poucas | — | mesmo defeito, cover da PT |
| Não Se Desiste | 76 | 18,1 dB | 13 | 45 cents | corrigida, contraste real |
| O Centro | 84 | 24,7 dB | **28** | 25 cents | melhor sustentação do lote |
| A Roda | 92 | **29,6 dB** | 12 | **57 cents** | melhor contraste do lote |

**A lição do lote:** as três primeiras pediam intensidade do início ao fim
(`screaming`, `desperate`, `raw aggressive` em tudo) e o resultado achatou — 2
notas sustentadas na música inteira, vibrato de 7 cents que é praticamente voz
reta. As três novas trocaram isso por `quiet intro` + `extreme dynamic contrast`
+ `no falsetto` e a faixa dinâmica quase dobrou.

---

## 1. Legado (variante) — `legado-pt`

**Prompt:** `epic cinematic pop, powerful female belt vocals, male spoken word
responses, gang vocal choir, brazilian portuguese, orchestral war drums, soaring
strings, anthemic, wide reverb, 118bpm, emotional build, huge chorus`
`styleWeight 0.85` · modo estilo · V5

**Diagnóstico:** é a versão mais contida das três primeiras — tem `emotional
build` no prompt, que ajuda, mas ainda pede `huge chorus` e `anthemic` sem
nenhuma marcação de trecho calmo. Serviu de rascunho do "Se Paga".

**Produção do vídeo:** banco escuro (v2), corte **lento**, quase toda a duração
na camada história, palco só em relance. Sem cartelas de texto além de duas.

---

## 2. Se Paga (PT) — `se-paga-pt`

**Prompt:** `epic cinematic anthem, screaming female belting, raspy desperate
female vocals, deep cavernous male baritone, viking folk duet, fast vocal call
and response, gang vocal choir, orchestral war drums, soaring strings, raw
aggressive vocals, 118bpm, huge chorus, brazilian portuguese`
`styleWeight 0.88` · modo estilo · V5 · sem negativeTags

**Medido:** 16,4 dB de faixa dinâmica · **2** notas sustentadas · vibrato 7 cents.

**Diagnóstico:** o prompt tem **seis** pedidos de intensidade e **zero** de
respiro. O Suno entregou o que foi pedido: tudo no talo. Sem `negativeTags`, nada
segurava. É a música mais "grande" do lote e a que menos emociona, porque nunca
sai do teto.

**Produção do vídeo:** banco escuro (v2), duas camadas (palco e história),
fusão em dupla exposição, cartelas nos picos. **Fogo removido** das cenas de
palco a pedido — agora é feixe branco e neblina.

---

## 3. It's Paid (EN) — `se-paga-en`

**Prompt:** igual ao de cima, trocando `brazilian portuguese` por
`english lyrics`. Diferença real: **modo `cover`** — usou a faixa PT como
referência de áudio, não só o estilo.

**Diagnóstico:** herda o mesmo achatamento. Por ser cover, também herda o
fraseado da PT, o que prende o inglês num desenho rítmico pensado pro português.

**Produção do vídeo:** mesmas imagens da PT, cartelas traduzidas, mas **corte
mais rápido** e ordem de cenas diferente pra não ficar clone da versão PT.

---

## 4. Não Se Desiste — `nao-se-desiste`

**Prompt:** `raw emotional male and female duet, gravelly baritone spoken
responses, driven chest mix, no falsetto, wide slow vibrato, laid back phrasing,
extreme dynamic contrast, quiet intimate verse, huge belted chorus, orchestral
build, live raw take, brazilian portuguese, 76bpm`
`negativeTags: muffled, lo-fi, constant screaming, flat dynamics, autotune, falsetto`

**Medido:** 18,1 dB · 13 notas sustentadas · vibrato 7,2 Hz / **45 cents**.

**Diagnóstico:** primeira do lote corrigido. O par `quiet intimate verse` +
`extreme dynamic contrast` funcionou, e `constant screaming` no negativo foi o
que impediu de repetir o erro do "Se Paga". 76bpm dá espaço pro fraseado
atrasado.

**Produção do vídeo:** banco **v4**, íntimo e documental — uma personagem só,
luz natural, sem palco grande, sem pirotecnia. Câmera na mão, corte médio,
progressão de quarto → sala de ensaio vazia → clube pequeno.

---

## 5. O Centro — `o-centro`

**Prompt:** `epic cinematic anthem, powerful female belt, deep male spoken word,
gang vocal choir, no falsetto, wide slow vibrato, quiet piano intro, massive
orchestral chorus, war drums, extreme dynamic contrast, brazilian portuguese,
84bpm` · mesmos negativeTags

**Medido:** 24,7 dB · **28** notas sustentadas (o melhor do lote) · vibrato 25 cents.

**Diagnóstico:** `quiet piano intro` é a instrução mais eficiente que testamos —
mais direta que "dynamic contrast", porque nomeia o instrumento e o trecho. É a
música com melhor sustentação de frase.

**Produção do vídeo:** banco **v5**, azul e âmbar, gráfico e simétrico, na linha
da imagem do manifesto. Texto é o recurso principal aqui (a música é um
manifesto), com cartelas no preto. Corte lento e planos longos.

---

## 6. A Roda — `a-roda`

**Prompt:** `soulful gospel rock, raspy male lead, female harmony, full choir,
hammond organ, handclaps, no falsetto, wide slow vibrato, quiet intro, explosive
final chorus, extreme dynamic contrast, brazilian portuguese, 92bpm`
· mesmos negativeTags · `vocalGender: m`

**Medido:** **29,6 dB** (melhor contraste do lote) · 12 sustentadas · vibrato
**57 cents** (o mais largo).

**Diagnóstico:** `quiet intro` + `explosive final chorus` marca começo E fim, e
foi o que rendeu o maior contraste de todos. `handclaps` e `hammond organ` deram
textura que nenhuma das outras tem. Melhor resultado técnico do lote.

**Produção do vídeo:** banco **v3**, moderno e alegre — coral jovem, palmas,
luz do dia, confete, mural pintado. Corte **rápido e ritmado nas palmas**, sem
cartela no preto, cores saturadas.

---

## Regras de produção que valem pra todas

1. **Close de quem canta no máximo ~4s.** O Agnes anima foto parada, não existe
   sincronia labial — segurar um rosto "cantando" por 12s denuncia na hora.
   Plano longo só em mão, plateia, paisagem ou objeto.
2. **Sem pirotecnia.** As referências de show serviram de ideia e layout, não de
   cenografia.
3. **Cada música tem banco, ritmo de corte e política de texto próprios** — o
   erro do primeiro lote foi rodar as 6 na mesma tabela de cenas.

## Receita de prompt que funciona (resumo)

```
<gênero>, <voz principal>, <voz de resposta>, no falsetto, wide slow vibrato,
quiet <instrumento> intro, extreme dynamic contrast, explosive final chorus,
<bpm>, <idioma>
negativeTags: constant screaming, flat dynamics, autotune, falsetto, lo-fi
```

O que mais pesa: **nomear o trecho calmo** (`quiet piano intro`) e **negativar
`constant screaming` e `flat dynamics`**.
