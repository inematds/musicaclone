# Comparação vocal: referência x geração (2026-08-05)

Método: os dois áudios enviados juntos ao Gemini (`gemini-flash-latest`) num único
prompt, pedindo comparação crítica de potência, tessitura, desespero, gravidade
masculina e dinâmica de revezamento. Script: `docs/comparar.py`.

- **Referência**: "Viking Gods" / Bob Dominator — trecho de 29 s (teaser do Facebook).
- **Nossa**: "Se Paga" v2 — geração V5, custom mode, PT-BR.

## Placar

| Dimensão | Referência | Nossa | Gap |
|---|---|---|---|
| Feminina — potência | 9,5 | 7,5 | −2,0 |
| Feminina — desespero | 9,5 | 6,0 | −3,5 |
| Feminina — tessitura | agudo rasgado no limite | média-alta, limpa | — |
| Masculina — gravidade | 9,5 | 6,5 | −3,0 |

## Diagnóstico

**Feminina.** A referência usa drive e rasgo, cantando no limite da voz — visceral.
A nossa saiu "potente e dramática, porém muito polida e controlada (estilo power
pop / teatro musical), sem a aspereza e o desespero da referência".

**Masculina.** A referência é barítono cavernoso, operático, com ressonância. A
nossa é spoken-word macio, "sem peso ressonante ou agressividade".

**Interação — o gap que mais importa.** A referência é call and response *colado e
sobreposto*, frases curtas, sem tempo de respirar. A nossa virou estrofe alternada
tradicional: o masculino narra um bloco longo, depois a feminina assume a estrofe
inteira. E nos espaços do vocal masculino a feminina **não preenche** — sobra base
instrumental.

## Causa (é nossa, não do modelo)

A letra enviada tinha blocos longos por voz. O Suno respeita a estrutura do prompt,
então bloco longo produz revezamento lento. Duelo se escreve **linha a linha**, com
ad-lib da outra voz dentro dos vãos.

## Ajustes que entram na próxima geração

Estilo (tags):
```
screaming female belting, raspy desperate female vocals, deep cavernous male baritone,
viking folk metal duet, fast vocal call and response, raw aggressive vocals, dramatic epic chants
```

Letra:
- alternar `[Female High Screaming]` → `[Male Deep Response]` **linha a linha**, não em blocos;
- técnica antes das frases dela: `[High Belt]`, `[Desperate Scream]`, `[Raspy Peak]`;
- ad-lib feminino dentro dos espaços do homem: `[High Echo Scream]`;
- parênteses só para o que deve mesmo ser cantado (o Suno canta parêntese).

Parâmetros: `--style-weight 0.85+` e `--weirdness` mais alto, para fugir do polido.

## O que isso vira no projeto

O `analisa.py` já classifica e transcreve; esta comparação é o passo seguinte
(referência x resultado) e vale como **checagem de qualidade depois de gerar**, não
só antes. Candidato a virar subcomando `musica.sh compara <slug>`.
