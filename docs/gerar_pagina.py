#!/usr/bin/env python3
"""Gera guia/musicas.html a partir de docs/medicoes.json + specs.

Regeneravel: mexeu nas medicoes, roda de novo.
"""
import html, json, os

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(R, "docs", "medicoes.json")))

# descricao editorial de cada musica (o que ela e, e o veredito)
INFO = {
 "legado-pt": ("Legado (variante)", "O primeiro rascunho do tema: preco do sucesso e heranca. "
   "Versao mais contida, com 'emotional build' no prompt.", "rascunho"),
 "se-paga-pt": ("Se Paga (PT)", "O tema em forma de hino: ninguem conta o preco, so mostram o trofeu. "
   "Duo feminino/masculino em call and response rapido.", "achatada"),
 "se-paga-en": ("It's Paid (EN)", "Versao inglesa, feita em modo cover a partir da faixa PT — "
   "herda o fraseado pensado para o portugues.", "achatada"),
 "nao-se-desiste": ("Nao Se Desiste", "Perseveranca: quem fica de pe nao e quem nao caiu, "
   "e quem voltou no dia seguinte. Primeira do lote corrigido.", "corrigida"),
 "o-centro": ("O Centro", "O talento humano diante da superinteligencia. A maquina amplia o que "
   "ja existe na pessoa; quem chega vazio amplia o vazio.", "corrigida"),
 "a-roda": ("A Roda", "Ninguem cresce sozinho: reconhecer quem veio antes e ajudar a roda a girar. "
   "Gospel rock com orgao e palmas.", "corrigida"),
 "luz-de-volta": ("Luz de Volta", "Rock emocional no estilo da referencia tears-v3a: troca de vozes "
   "sem respiro, voz a frente da banda e poucos dobros.", "nova"),
}
SEL = ["legado-pt", "se-paga-pt", "se-paga-en", "nao-se-desiste", "o-centro", "a-roda", "luz-de-volta"]
BADGE = {"rascunho": ("#94a3b8", "rascunho"), "achatada": ("#f87171", "intensidade constante"),
         "corrigida": ("#4ade80", "contraste corrigido"), "nova": ("#38bdf8", "nova")}
REG = ["grave", "medio-grave", "medio-agudo", "belt"]


def vib(m):
    """Vibrato acima de ~200 cents e falha de deteccao, nao medicao. Nao exibe."""
    c = m.get("vibrato_cents", 0)
    return f"{c} cents" if 0 < c <= 200 else "—"


def barras(reg):
    """SVG de barras da distribuicao de registro."""
    W, H, g = 300, 92, 10
    bw = (W - g * 3) / 4
    cores = ["#475569", "#64748b", "#E2A23B", "#f59e0b"]
    mx = max(reg + [1])
    s = [f'<svg viewBox="0 0 {W} {H+22}" class="chart" role="img" aria-label="distribuicao de registro">']
    for i, v in enumerate(reg):
        h = max(2, (v / mx) * H)
        x = i * (bw + g)
        s.append(f'<rect x="{x:.0f}" y="{H-h:.0f}" width="{bw:.0f}" height="{h:.0f}" rx="3" fill="{cores[i]}"/>')
        s.append(f'<text x="{x+bw/2:.0f}" y="{H-h-4:.0f}" class="cval">{v:.0f}%</text>')
        s.append(f'<text x="{x+bw/2:.0f}" y="{H+16:.0f}" class="clab">{REG[i]}</text>')
    s.append("</svg>")
    return "".join(s)


def metrica(rot, val, dica=""):
    t = f' title="{html.escape(dica)}"' if dica else ""
    return f'<div class="met"{t}><b>{val}</b><span>{rot}</span></div>'


cards = []
for slug in SEL:
    if slug not in D:
        continue
    d = D[slug]
    titulo, desc, tag = INFO[slug]
    cor, rot = BADGE[tag]
    fx = []
    for nome, m in sorted(d["faixas"].items()):
        n = nome.split("-")[1]
        mm, ss = divmod(int(m["dur"]), 60)
        audio = f"audio/{slug}-{nome}.mp3"
        fx.append(f'''
      <div class="faixa">
        <div class="fhead"><b>Faixa {n}</b><span>{mm}:{ss:02d}</span></div>
        <audio controls preload="none" src="{audio}"></audio>
        <div class="mets">
          {metrica("dinamica", f"{m['dinamica_db']} dB", "diferenca entre o trecho mais baixo e o mais alto — quanto maior, mais a musica respira")}
          {metrica("sustentadas", m["sustentadas"], "notas seguradas por mais de 0,35s")}
          {metrica("vibrato", vib(m), "profundidade do vibrato; acima de 200 cents e falha de deteccao")}
          {metrica("brilho", f"{m['brilho_hz']} Hz", "centroide espectral cantando — mais alto soa mais rasgado")}
        </div>
        {barras(m["registro"])}
      </div>''')
    cards.append(f'''
  <article class="song" id="{slug}">
    <header class="shead">
      <div>
        <h3>{html.escape(titulo)}</h3>
        <p class="sdesc">{html.escape(desc)}</p>
      </div>
      <span class="badge" style="--bc:{cor}">{rot}</span>
    </header>
    <div class="prompt">
      <div class="plab">prompt de estilo enviado ao Suno</div>
      <code>{html.escape(d["style"])}</code>
      {f'<div class="plab neg">negativos</div><code>{html.escape(d["negativos"])}</code>' if d.get("negativos") else ''}
      <div class="pmeta">modelo {d.get("model","-")} · modo {d.get("modo","-")} · voz {d.get("voz","-")} · styleWeight {d.get("styleWeight","-")}</div>
    </div>
    <div class="faixas">{''.join(fx)}</div>
    <div class="video"><span>video:</span> <em>ainda nao publicado — entra aqui quando subir na lives10</em></div>
  </article>''')

# tabela resumo
linhas = []
for slug in SEL:
    if slug not in D:
        continue
    d = D[slug]; titulo, desc, tag = INFO[slug]
    cor, rot = BADGE[tag]
    f1 = d["faixas"].get("faixa-1") or list(d["faixas"].values())[0]
    bpm = ""
    for t in d["style"].split(","):
        if "bpm" in t:
            bpm = t.strip()
    linhas.append(f'''<tr>
      <td><a href="#{slug}">{html.escape(titulo)}</a></td>
      <td class="num">{bpm or "—"}</td>
      <td class="num">{f1["dinamica_db"]} dB</td>
      <td class="num">{f1["sustentadas"]}</td>
      <td class="num">{vib(f1)}</td>
      <td><span class="badge sm" style="--bc:{cor}">{rot}</span></td>
    </tr>''')

# ---------------------------------------------------------------- referencias
# So MEDICOES. Audio de referencia nao vai pro site: parte e gravacao de
# terceiros (as duas do YouTube), e nao e nosso para publicar.
RP = os.path.join(R, "docs", "medicoes-refs.json")
REFS = json.load(open(RP)) if os.path.exists(RP) else {}
RNOME = {
 "tears-v3a": ("tears-v3a", "a referencia do rock emocional: respira, sobe sem morar no grito, voz reta e tensa"),
 "tears-v3b": ("tears-v3b", "irma da anterior, mais tempo em belt e sustentacoes mais longas"),
 "wewerehere-v2a": ("wewerehere-v2a", "a mais 'segurada' de todo o acervo gerado: 44 notas sustentadas"),
 "wewerehere-v2b": ("wewerehere-v2b", "mesma familia, mais aguda"),
 "fire-v1a": ("fire-v1a", "mais grave e espalhada pelos registros"),
 "fire-v1b": ("fire-v1b", "idem, com menos sustentacao"),
 "suno-horizons-v1-chops": ("suno-horizons-v1", "89% do tempo em belt: quase nao sai do teto"),
 "suno-horizons-v2-chops": ("suno-horizons-v2", "boa dinamica, sustentacao curta"),
 "suno-digital-sky-v1": ("suno-digital-sky-v1", "mora no agudo, dinamica media"),
 "suno-digital-sky-v2": ("suno-digital-sky-v2", "dinamica baixa"),
 "suno-builders-v1-vocal": ("suno-builders-v1", "dinamica baixa e quase nenhuma sustentacao"),
 "suno-builders-v2-vocal": ("suno-builders-v2", "ZERO notas sustentadas: a voz nunca para"),
 "suno-cover-isolado-v1": ("suno-cover-isolado-v1", "ZERO sustentadas, 78% em belt"),
 "suno-cover-isolado-v2": ("suno-cover-isolado-v2", "a menor dinamica do acervo"),
 "suno-cover-reel-v1": ("suno-cover-reel-v1", "dinamica alta, sustentacao quase nula"),
 "suno-cover-reel-v2": ("suno-cover-reel-v2", "vibrato largo, pouca dinamica"),
 "yt-agt-video2-standby": ("humano ao vivo (AGT)", "VOZ HUMANA REAL: 182 sustentadas e 41 dB — nenhuma gerada chega perto"),
 "yt-agt-video1": ("humano, captacao suja (AGT)", "mesma origem, gravacao contaminada por banda e plateia"),
}
rlin = []
for k in ["tears-v3a", "tears-v3b", "wewerehere-v2a", "wewerehere-v2b", "fire-v1a", "fire-v1b",
          "suno-horizons-v1-chops", "suno-horizons-v2-chops", "suno-digital-sky-v1",
          "suno-digital-sky-v2", "suno-builders-v1-vocal", "suno-builders-v2-vocal",
          "suno-cover-isolado-v1", "suno-cover-isolado-v2", "suno-cover-reel-v1",
          "suno-cover-reel-v2", "yt-agt-video2-standby", "yt-agt-video1"]:
    if k not in REFS:
        continue
    m = REFS[k]; nome, obs = RNOME[k]
    hum = "hum" if k.startswith("yt-") else ""
    rlin.append(f'''<tr class="{hum}">
      <td><b>{html.escape(nome)}</b><div class="robs">{html.escape(obs)}</div></td>
      <td class="num">{m["f0_mediana"]} Hz</td>
      <td class="num">{m["dinamica_db"]} dB</td>
      <td class="num">{m["sustentadas"]}</td>
      <td class="num">{m["sust_max"]}s</td>
      <td class="num">{vib(m)}</td>
      <td class="num">{m["registro"][3]:.0f}%</td>
    </tr>''')

# --------------------------------------------------- grafico de dispersao
pts = []
for slug in SEL:
    if slug in D:
        m = D[slug]["faixas"].get("faixa-1") or list(D[slug]["faixas"].values())[0]
        pts.append((m["dinamica_db"], m["sustentadas"], INFO[slug][0], "g"))
for k, m in REFS.items():
    if k in RNOME:
        pts.append((m["dinamica_db"], m["sustentadas"], RNOME[k][0], "h" if k.startswith("yt-") else "r"))

W, H, pad = 640, 340, 46
mxx = max(p[0] for p in pts) * 1.08
mxy = max(p[1] for p in pts) * 1.12
COR = {"g": "#E2A23B", "r": "#64748b", "h": "#38bdf8"}
sc = [f'<svg viewBox="0 0 {W} {H}" class="scatter" role="img" aria-label="dinamica versus notas sustentadas">']
for i in range(5):
    y = pad + (H - pad * 2) * i / 4
    sc.append(f'<line x1="{pad}" y1="{y:.0f}" x2="{W-14}" y2="{y:.0f}" class="grid"/>')
    sc.append(f'<text x="{pad-8}" y="{y+4:.0f}" class="ax" text-anchor="end">{mxy*(1-i/4):.0f}</text>')
for i in range(5):
    x = pad + (W - pad - 14) * i / 4
    sc.append(f'<text x="{x:.0f}" y="{H-10}" class="ax" text-anchor="middle">{mxx*i/4:.0f} dB</text>')
for dx, sy, nome, tipo in pts:
    X = pad + (W - pad - 14) * (dx / mxx)
    Y = pad + (H - pad * 2) * (1 - sy / mxy)
    rr = 8 if tipo == "h" else 5
    sc.append(f'<circle cx="{X:.0f}" cy="{Y:.0f}" r="{rr}" fill="{COR[tipo]}" opacity=".9"><title>{html.escape(nome)}: {dx} dB, {sy} sustentadas</title></circle>')
    if tipo == "h" or nome in ("tears-v3a", "Luz de Volta", "A Roda", "Se Paga (PT)", "wewerehere-v2a"):
        sc.append(f'<text x="{X+11:.0f}" y="{Y+4:.0f}" class="pt">{html.escape(nome)}</text>')
sc.append(f'<text x="{pad}" y="22" class="ax">notas sustentadas (eixo vertical) x dinamica (eixo horizontal)</text>')
sc.append("</svg>")

TPL = open(os.path.join(R, "docs", "musicas_tpl.html")).read()
out = (TPL.replace("{{TABELA}}", "".join(linhas))
          .replace("{{CARDS}}", "".join(cards))
          .replace("{{REFS}}", "".join(rlin))
          .replace("{{SCATTER}}", "".join(sc)))
p = os.path.join(R, "guia", "musicas.html")
open(p, "w").write(out)
print("gerado:", p, f"({len(out)//1024} KB, {len(cards)} musicas)")
