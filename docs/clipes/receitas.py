#!/usr/bin/env python3
"""Receita de producao POR MUSICA. Cada uma tem banco, ritmo de corte,
politica de texto e gramatica propria. Nada de tabela unica pra todas.

Uso: receitas.py <slug-da-receita> <audio.mp3> <saida.mp4> <plano.json>
"""
import json, subprocess, sys, os

# Cenas que sao close de quem canta. O Agnes anima foto parada, entao NAO ha
# sincronia labial: segurar essas por muito tempo denuncia. Teto de 4s.
CANTANDO = {
    "clipe-v2": {2, 7, 8, 16, 18, 22},
    "clipe-v3": {2, 3, 8, 16, 17, 20},
    "clipe-v4": {2, 7, 9, 15, 16, 20, 21},
    "clipe-v5": {13},
}
TETO_CANTO = 4.0
TETO_GERAL = 11.0   # nenhum plano passa disso, mesmo sem canto

# (cena, peso, modo, sobre, texto)
R = {}

# --- SE PAGA (PT): duas camadas, palco x historia, fusao. Corte medio.
R["se-paga-pt"] = dict(banco="clipe-v2", xfade=0.8, texto_no_preto=True, cenas=[
 (1,9,"cheio",None,"NINGUÉM TE CONTA O PREÇO"), (2,4,"cheio",None,None),
 (3,11,"cheio",None,"ANTES DO SOL"), (4,11,"janela",2,None),
 (5,9,"fusao",2,"CHAMARAM DE SORTE. ERA FÉ."), (6,10,"cheio",None,None),
 (7,4,"cheio",None,"NINGUÉM FALA DA SUBIDA"), (0,0.5,"preto",None,None),
 (8,4,"cheio",None,"E EU VOU"), (9,10,"janela",8,"MESMO QUE DOA"),
 (10,9,"cheio",None,"NA PEDRA"), (11,11,"cheio",None,"PRO MEU FILHO ANDAR DE CABEÇA ERGUIDA"),
 (12,11,"cheio",None,"PERDI A FESTA"), (13,11,"cheio",None,"CADA NÃO VIROU CHÃO"),
 (14,10,"cheio",None,None), (15,9,"fusao",2,"QUEM ME VIU CAIR NÃO ME VIU LEVANTAR"),
 (16,4,"cheio",None,"SUCESSO NÃO É O BRILHO"), (17,11,"cheio",None,"É O QUE SOBRA QUANDO AS LUZES APAGAM"),
 (0,1.0,"preto",None,"É O QUE FICA"), (18,4,"cheio",None,None),
 (19,11,"janela",18,"QUE MEUS NETOS DIGAM O MEU NOME"), (20,12,"cheio",None,"VALE A PENA"),
 (21,9,"fusao",2,"O LEGADO NÃO SE COMPRA"), (22,4,"cheio",None,None),
 (0,1.2,"preto",None,"SE PAGA")])

# --- IT'S PAID (EN): mesmas imagens, ordem embaralhada e corte MAIS RAPIDO,
#     pra nao virar clone da versao PT. Sem janela, so fusao.
R["its-paid-en"] = dict(banco="clipe-v2", xfade=0.5, texto_no_preto=True, cenas=[
 (2,4,"cheio",None,None), (1,7,"cheio",None,"NOBODY TELLS YOU THE PRICE"),
 (4,8,"cheio",None,"BEFORE THE SUN"), (3,7,"cheio",None,None),
 (6,7,"cheio",None,None), (5,7,"fusao",2,"THEY CALLED IT LUCK. IT WAS FAITH."),
 (13,7,"cheio",None,"NOBODY TALKS ABOUT THE CLIMB"), (0,0.4,"preto",None,None),
 (8,4,"cheio",None,"AND I GO"), (10,6,"cheio",None,"INTO THE STONE"),
 (9,7,"cheio",None,"EVEN IF IT HURTS"), (11,8,"cheio",None,"SO MY SON CAN WALK WITH HIS HEAD HELD HIGH"),
 (14,7,"cheio",None,None), (12,7,"cheio",None,"MISSED THE PARTY"),
 (15,7,"fusao",2,"WHO SAW ME FALL NEVER SAW ME RISE"), (16,4,"cheio",None,"SUCCESS IS NOT THE SHINING"),
 (17,8,"cheio",None,"IT'S WHAT REMAINS WHEN THE LIGHTS GO OUT"),
 (0,0.9,"preto",None,"IT'S WHAT REMAINS"), (18,4,"cheio",None,None),
 (20,8,"cheio",None,"IT'S WORTH THE PAIN"), (19,8,"cheio",None,"LET MY GRANDCHILDREN SPEAK MY NAME"),
 (21,7,"fusao",2,"A LEGACY IS NOT BOUGHT"), (22,4,"cheio",None,None),
 (0,1.1,"preto",None,"IT'S PAID")])

# --- LEGADO (variante): quase tudo historia, palco so em relance.
#     Corte LENTO, so duas cartelas, sem preto.
R["legado-pt"] = dict(banco="clipe-v2", xfade=1.4, texto_no_preto=False, cenas=[
 (3,14,"cheio",None,None), (4,14,"cheio",None,"ANTES DO SOL"),
 (6,13,"cheio",None,None), (2,4,"cheio",None,None),
 (12,14,"cheio",None,None), (13,13,"cheio",None,None),
 (14,14,"cheio",None,None), (15,10,"fusao",2,None),
 (9,13,"cheio",None,None), (10,12,"cheio",None,None),
 (17,13,"cheio",None,None), (11,13,"cheio",None,None),
 (19,14,"cheio",None,None), (20,15,"cheio",None,"VALE A PENA"),
 (22,4,"cheio",None,None)])

# --- NAO SE DESISTE: banco intimo, uma personagem, luz natural.
#     Narrativa continua e cronologica, corte medio, texto discreto.
R["nao-se-desiste"] = dict(banco="clipe-v4", xfade=1.0, texto_no_preto=False, cenas=[
 (1,11,"cheio",None,None), (2,4,"cheio",None,"TODO MUNDO DESISTE UMA VEZ"),
 (3,11,"cheio",None,None), (4,11,"cheio",None,None),
 (5,11,"cheio",None,None), (6,10,"cheio",None,"NÃO FOI TALENTO"),
 (7,4,"cheio",None,None), (8,11,"cheio",None,"FOI VOLTAR NO DIA SEGUINTE"),
 (9,4,"cheio",None,None), (10,11,"cheio",None,None),
 (13,11,"cheio",None,None), (14,10,"cheio",None,"COM A MÃO TREMENDO"),
 (11,11,"cheio",None,None), (12,9,"fusao",9,None),
 (15,11,"cheio",None,None), (16,4,"cheio",None,None),
 (17,11,"cheio",None,None), (18,9,"fusao",9,None),
 (20,4,"cheio",None,None), (21,4,"cheio",None,"E VÃO ME VER CHEGAR"),
 (19,11,"cheio",None,None), (22,13,"cheio",None,"NÃO SE DESISTE")])

# --- O CENTRO: grafico, azul e ambar. Planos LONGOS, texto e o recurso
#     principal (a musica e um manifesto), cartelas no preto.
R["o-centro"] = dict(banco="clipe-v5", xfade=1.2, texto_no_preto=True, cenas=[
 (1,14,"cheio",None,None), (2,10,"cheio",None,"ELA JÁ PASSOU"),
 (3,13,"cheio",None,None), (6,12,"cheio",None,None),
 (5,13,"cheio",None,"ELA NUNCA TEVE MEDO ÀS TRÊS DA MANHÃ"),
 (0,0.9,"preto",None,"NÃO É A RESPOSTA"), (4,12,"cheio",None,None),
 (10,13,"cheio",None,"ELA AMPLIA O QUE EU JÁ SOU"),
 (16,11,"cheio",None,"SE EU CHEGO VAZIO, ELA AMPLIA O VAZIO"),
 (9,12,"cheio",None,None), (8,11,"cheio",None,None),
 (7,12,"cheio",None,None), (13,4,"cheio",None,None),
 (14,12,"cheio",None,None), (0,1.1,"preto",None,"NÃO É A MESMA COISA"),
 (11,11,"fusao",12,None), (17,12,"cheio",None,None),
 (19,11,"cheio",None,None), (12,13,"cheio",None,"QUEM DECIDE O QUE IMPORTA SOU EU"),
 (18,12,"cheio",None,None), (15,13,"cheio",None,None),
 (21,11,"fusao",12,None), (20,14,"cheio",None,None),
 (0,1.4,"preto",None,"O CENTRO CONTINUA SENDO O SER HUMANO"), (22,12,"cheio",None,None)])

# --- A RODA: moderno e alegre. Corte RAPIDO e ritmado, sem preto,
#     sem cartela solta, cores saturadas.
R["a-roda"] = dict(banco="clipe-v3", xfade=0.35, texto_no_preto=False, cenas=[
 (10,7,"cheio",None,None), (2,4,"cheio",None,None),
 (0,5,"rajada",[9,2,7,10,4,13],None),
 (6,7,"cheio",None,"EU NÃO INVENTEI A RODA"), (9,5,"cheio",None,None),
 (7,6,"cheio",None,None), (12,7,"cheio",None,None),
 (3,4,"cheio",None,None), (1,7,"cheio",None,"FAZ GIRAR"),
 (4,6,"cheio",None,None), (9,4,"cheio",None,None),
 (14,6,"cheio",None,None), (17,4,"cheio",None,None),
 (0,6,"split",[6,9,16],None),
 (11,7,"cheio",None,None), (5,6,"fusao",2,None),
 (13,6,"cheio",None,None), (19,7,"cheio",None,"NINGUÉM EVOLUI SOZINHO"),
 (16,4,"cheio",None,None), (6,5,"cheio",None,None),
 (0,5,"rajada",[18,12,13,10,4,20],None),
 (18,7,"cheio",None,None), (15,6,"fusao",3,None),
 (20,4,"cheio",None,None), (21,6,"cheio",None,None),
 (8,4,"cheio",None,None), (22,8,"cheio",None,"É ASSIM QUE EVOLUÍMOS")])


def variar(T, faixa):
    """Faixa 2 ganha montagem propria: nao basta mudar duracao, o corte tem de
    ser outro. Gira a ordem, troca os modos e redistribui o texto."""
    if faixa != 2:
        return T
    corpo = [x for x in T if x[2] != "preto"]
    pretos = [(i, x) for i, x in enumerate(T) if x[2] == "preto"]
    k = max(1, len(corpo) // 3)
    corpo = corpo[k:] + corpo[:k]                 # comeca de outro ponto da historia
    novo = []
    for i, (c, w, modo, sobre, txt) in enumerate(corpo):
        # inverte a gramatica: o que era plano cheio vira janela/fusao e vice-versa
        if modo == "cheio" and i % 5 == 2:
            modo, sobre = ("fusao", 2) if i % 2 else ("janela", 2)
        elif modo in ("fusao", "janela"):
            modo, sobre = "cheio", None
        # metade das cartelas sai, para nao repetir a mesma leitura
        if txt and i % 2:
            txt = None
        novo.append((c, w, modo, sobre, txt))
    for i, x in pretos:                            # devolve os pretos espalhados
        novo.insert(min(len(novo), i), x)
    return novo


def main():
    slug, audio, saida, dest = sys.argv[1:5]
    faixa = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    r = R[slug]
    banco = r["banco"]
    canta = CANTANDO.get(banco, set())
    AD = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                               "format=duration", "-of", "csv=p=0", audio],
                              capture_output=True, text=True).stdout.strip())
    XF = r["xfade"] * (1.6 if faixa == 2 else 1.0)   # corte com respiro diferente
    T = variar(r["cenas"], faixa)
    n = len(T)
    alvo = AD + XF * (n - 1)

    # cenas de canto entram com duracao FIXA e curta; o resto divide o que sobra
    fixas = sum(min(TETO_CANTO, w) for (c, w, m, s, t) in T if m != "preto" and c in canta)
    fixas += sum(w for (c, w, m, s, t) in T if m in ("preto", "rajada", "split"))
    peso = sum(w for (c, w, m, s, t) in T if m not in ("preto", "rajada", "split") and c not in canta)
    k = (alvo - fixas) / peso if peso else 1.0

    cenas = []
    for (c, w, modo, sobre, txt) in T:
        if modo == "preto":
            d = w
        elif modo in ("rajada", "split"):
            d = w
        elif c in canta:
            d = min(TETO_CANTO, w)
        else:
            d = min(TETO_GERAL, round(w * k, 2))   # nenhum plano se arrasta
        item = {"dur": round(d, 2), "modo": modo}
        if modo not in ("preto", "rajada", "split"):
            item["n"] = c
        if isinstance(sobre, list):
            item["cenas"] = sobre
        elif sobre:
            item["sobre"] = sobre
        if txt:
            item["texto"] = txt
        cenas.append(item)

    # Se o teto geral encurtou demais, completa reciclando as cenas longas do
    # proprio banco (sem texto, pra nao repetir cartela) em vez de esticar uma.
    def total(cs):
        return sum(x["dur"] for x in cs) - XF * (len(cs) - 1)

    pool = [c for (c, w, m, s, t) in T if m != "preto" and c not in canta]
    i = 0
    while pool and total(cenas) < AD:
        c = pool[i % len(pool)]
        i += 1
        falta = AD - total(cenas)
        cenas.insert(min(len(cenas) - 1, 3 + i * 3),
                     {"dur": round(min(TETO_GERAL, max(4.0, falta + XF)), 2),
                      "modo": "cheio", "n": c})

    plano = {"banco": banco, "audio": audio, "saida": saida,
             "w": 1280, "h": 704, "xfade": XF,
             "fonte": os.path.expanduser("~/.local/share/fonts/Montserrat-ExtraBold.ttf"),
             "cenas": cenas}
    json.dump(plano, open(dest, "w"), ensure_ascii=False, indent=1)
    mx = max(c["dur"] for c in cenas)
    print(f"{slug:16s} f{faixa} banco={banco} xfade={XF} cenas={n} audio={AD:.0f}s "
          f"maior_plano={mx:.1f}s canto<={TETO_CANTO}s")


if __name__ == "__main__":
    main()
