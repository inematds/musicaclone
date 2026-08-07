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

TPL = open(os.path.join(R, "docs", "musicas_tpl.html")).read()
out = TPL.replace("{{TABELA}}", "".join(linhas)).replace("{{CARDS}}", "".join(cards))
p = os.path.join(R, "guia", "musicas.html")
open(p, "w").write(out)
print("gerado:", p, f"({len(out)//1024} KB, {len(cards)} musicas)")
