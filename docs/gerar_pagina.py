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


NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def nota(midi):
    i = int(round(midi))
    return f"{NOTAS[i % 12]}{i // 12 - 1}"


def movimento(m):
    """Contorno de altura da voz + envelope de volume ao longo do tempo."""
    cont = m.get("contorno") or []
    ener = m.get("energia") or []
    vals = [c for c in cont if c is not None]
    if len(vals) < 8:
        return '<div class="semmov">sem canto continuo suficiente para tracar o movimento</div>'
    W, H, top, bot = 300, 96, 8, 20
    lo, hi = min(vals), max(vals)
    if hi - lo < 4:
        lo, hi = lo - 2, hi + 2
    n = len(cont)
    px = lambda i: i * W / max(n - 1, 1)
    py = lambda v: top + (H - top - bot) * (1 - (v - lo) / (hi - lo))

    s = [f'<svg viewBox="0 0 {W} {H}" class="mov" role="img" aria-label="movimento da voz">']
    # envelope de volume ao fundo
    if ener:
        emin, emax = min(ener), max(ener)
        rng = (emax - emin) or 1
        pts = " ".join(f"{px(i):.1f},{top + (H-top-bot) * (1 - (e-emin)/rng):.1f}"
                       for i, e in enumerate(ener[:n]))
        s.append(f'<polyline points="{pts}" class="env"/>')
    # contorno da voz, quebrando onde nao ha canto
    seg = []
    for i, c in enumerate(cont):
        if c is None:
            if len(seg) > 1:
                s.append(f'<polyline points="{" ".join(seg)}" class="line"/>')
            seg = []
        else:
            seg.append(f"{px(i):.1f},{py(c):.1f}")
    if len(seg) > 1:
        s.append(f'<polyline points="{" ".join(seg)}" class="line"/>')
    s.append(f'<text x="2" y="{top+6}" class="nlab">{nota(hi)}</text>')
    s.append(f'<text x="2" y="{H-bot:.0f}" class="nlab">{nota(lo)}</text>')
    s.append(f'<text x="{W-2}" y="{H-4}" class="nlab" text-anchor="end">tempo &rarr;</text>')
    s.append(f'<text x="2" y="{H-4}" class="nlab">extensao {hi-lo:.0f} semitons</text>')
    s.append(f'<line class="ph" x1="0" y1="{top}" x2="0" y2="{H-bot}" style="display:none"/>')
    s.append("</svg>")
    return "".join(s)




def notas_hist(m):
    """Quais notas a voz usa — mostra o tom de forma concreta."""
    nt = m.get("notas") or []
    if not nt or sum(nt) == 0:
        return ""
    W, H, g = 300, 66, 3
    bw = (W - g * 11) / 12
    mx = max(nt)
    tom = (m.get("tom") or "").split(" ")[0]
    s = [f'<svg viewBox="0 0 {W} {H+16}" class="hist" role="img" aria-label="notas usadas">']
    for i, v in enumerate(nt):
        h = max(1.5, (v / mx) * H)
        x = i * (bw + g)
        cor = "#E2A23B" if NOTAS[i] == tom else "#475569"
        s.append(f'<rect x="{x:.1f}" y="{H-h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="2" fill="{cor}"><title>{NOTAS[i]}: {v}%</title></rect>')
        s.append(f'<text x="{x+bw/2:.1f}" y="{H+12}" class="hlab">{NOTAS[i]}</text>')
    s.append("</svg>")
    return "".join(s)


def dialogo(m):
    """Cada frase cantada vira um bloco. Altura = registro, vao = silencio entre
    as vozes. E aqui que se ve se a resposta entra colada ou com respiro."""
    fl = m.get("frases_lista") or []
    if len(fl) < 4:
        return ""
    W, H = 300, 60
    t0 = fl[0][0]
    t1 = max(f[1] for f in fl)
    span = (t1 - t0) or 1
    alt = [f[2] for f in fl]
    lo, hi = min(alt), max(alt)
    if hi - lo < 3:
        lo, hi = lo - 1.5, hi + 1.5
    s = [f'<svg viewBox="0 0 {W} {H}" class="dlg" role="img" aria-label="dialogo entre as vozes">']
    ant = None
    for a, b, mm in fl:
        x = (a - t0) / span * W
        w = max(1.2, (b - a) / span * W)
        y = 6 + (H - 18) * (1 - (mm - lo) / (hi - lo))
        troca = ant is not None and abs(mm - ant) > 5.0
        cor = "#38bdf8" if troca else "#E2A23B"
        s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="5" rx="2.5" fill="{cor}"><title>{a:.1f}s  {nota(mm)}</title></rect>')
        ant = mm
    s.append(f'<text x="2" y="{H-2}" class="hlab">vao mediano {m.get("vao_mediano",0)}s · na troca {m.get("vao_na_troca",0)}s · {m.get("trocas_voz",0)} trocas</text>')
    s.append("</svg>")
    return "".join(s)



ROLL = json.load(open(os.path.join(R, "docs", "pianoroll.json"))) if os.path.exists(
    os.path.join(R, "docs", "pianoroll.json")) else {}


def piano(chave):
    """Piano roll: cada nota cantada vira um bloco na altura da tecla."""
    ns = ROLL.get(chave) or []
    if len(ns) < 4:
        return ""
    W, H = 300, 110
    lo = min(n[2] for n in ns); hi = max(n[2] for n in ns)
    if hi - lo < 6:
        lo, hi = lo - 3, hi + 3
    t1 = max(n[1] for n in ns) or 1
    alt = (H - 14) / (hi - lo + 1)
    s = [f'<svg viewBox="0 0 {W} {H}" class="roll" role="img" aria-label="piano roll">']
    # faixas das teclas pretas, para dar a leitura de teclado
    for m in range(lo, hi + 1):
        if m % 12 in (1, 3, 6, 8, 10):
            y = 6 + (hi - m) * alt
            s.append(f'<rect x="0" y="{y:.1f}" width="{W}" height="{alt:.1f}" fill="currentColor" opacity=".06"/>')
    for a, b, m in ns:
        x = a / t1 * W
        w = max(1.4, (b - a) / t1 * W)
        y = 6 + (hi - m) * alt
        s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{max(2,alt-1):.1f}" rx="1.5" fill="#E2A23B"><title>{nota(m)}</title></rect>')
    s.append(f'<text x="2" y="{H-2}" class="hlab">{nota(lo)} a {nota(hi)} · {len(ns)} notas</text>')
    s.append("</svg>")
    return "".join(s)


def espectro(chave):
    sp = f"espectro/{chave}-spec.png"
    wf = f"espectro/{chave}-wave.png"
    if not os.path.exists(os.path.join(R, "guia", sp)):
        return ""
    return (f'<div class="mlab">espectrograma <span>(grave embaixo, agudo em cima; cor = volume)</span></div>'
            f'<img class="spec" src="{sp}" alt="espectrograma" loading="lazy">'
            f'<div class="mlab">forma de onda <span>(so o volume)</span></div>'
            f'<img class="wave" src="{wf}" alt="forma de onda" loading="lazy">')


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
        <div class="mlab">movimento da voz <b>· tom {m.get("tom","?")}</b> <span>(confianca {m.get("tom_conf",0)})</span></div>
        {movimento(m)}
        {espectro(f"{slug}-{nome}")}
        <div class="mlab">piano roll <span>(cada bloco = uma nota cantada)</span></div>
        {piano(f"{slug}-{nome}")}
        <div class="mlab">dialogo entre as vozes <span>(azul = troca de registro)</span></div>
        {dialogo(m)}
        <div class="mlab">notas usadas <span>(ambar = tonica)</span></div>
        {notas_hist(m)}
        <div class="mlab">onde a voz passa o tempo</div>
        {barras(m["registro"])}
      </div>''')
    cards.append(f'''
  <article class="song" id="{slug}">
    <header class="shead">
      <img class="capa" src="capas/{slug}.png" alt="" loading="lazy">
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
      <td class="num">{f1.get("tom","?")}</td>
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
 "tiktok-audio": ("audio de TikTok", "baixado de fora, usado so como referencia de estilo"),
 "viking-gods-ref": ("viking-gods (ref)", "trecho baixado de link; a geracao nunca chegou a rodar"),
}
rlin = []
for k in ["yt-agt-video2-standby", "yt-agt-video1", "tiktok-audio", "viking-gods-ref"]:
    if k not in REFS:
        continue
    m = REFS[k]; nome, obs = RNOME[k]
    hum = "hum" if k.startswith("yt-") else ""
    rlin.append(f'''<tr class="{hum}">
      <td><b>{html.escape(nome)}</b><div class="robs">{html.escape(obs)}</div></td>
      <td class="num">{m.get("tom","?")}</td>
      <td class="num">{m["f0_mediana"]} Hz</td>
      <td class="num">{m["dinamica_db"]} dB</td>
      <td class="num">{m["sustentadas"]}</td>
      <td class="num">{m["sust_max"]}s</td>
      <td class="num">{vib(m)}</td>
      <td class="num">{m["registro"][3]:.0f}%</td>
    </tr>''')


# ------------------------------------------------------------------ acervo
# Faixas nossas geradas antes (pares a/b = duas faixas por geracao do Suno).
# Nao temos o spec destas, entao entram sem prompt, mas com audio e medicoes.
AC = json.load(open(os.path.join(R, "docs", "acervo.json")))
acards = []
for slug, a in AC.items():
    fx = []
    for fn in a["faixas"]:
        m = REFS.get(fn)
        if not m:
            continue
        mm, ss = divmod(int(m["dur"]), 60)
        fx.append(f'''
      <div class="faixa">
        <div class="fhead"><b>{html.escape(fn)}</b><span>{mm}:{ss:02d}</span></div>
        <audio controls preload="none" src="audio/{fn}.mp3"></audio>
        <div class="mets">
          {metrica("dinamica", f"{m['dinamica_db']} dB")}
          {metrica("sustentadas", m["sustentadas"])}
          {metrica("vibrato", vib(m))}
          {metrica("brilho", f"{m['brilho_hz']} Hz")}
        </div>
        <div class="mlab">movimento da voz <b>· tom {m.get("tom","?")}</b> <span>(confianca {m.get("tom_conf",0)})</span></div>
        {movimento(m)}
        {espectro(fn)}
        <div class="mlab">piano roll <span>(cada bloco = uma nota cantada)</span></div>
        {piano(fn)}
        <div class="mlab">dialogo entre as vozes <span>(azul = troca de registro)</span></div>
        {dialogo(m)}
        <div class="mlab">notas usadas <span>(ambar = tonica)</span></div>
        {notas_hist(m)}
        <div class="mlab">onde a voz passa o tempo</div>
        {barras(m["registro"])}
      </div>''')
    if not fx:
        continue
    acards.append(f'''
  <article class="song" id="{slug}">
    <header class="shead">
      <img class="capa" src="capas/{a["capa"]}.png" alt="" loading="lazy">
      <div>
        <h3>{html.escape(a["titulo"])}</h3>
        <p class="sdesc">{html.escape(a["desc"])}</p>
      </div>
      <span class="badge" style="--bc:#94a3b8">acervo</span>
    </header>
    <div class="faixas">{"".join(fx)}</div>
  </article>''')

# ------------------------------------------------------------------ menu
menu = []
for slug in SEL:
    if slug in D:
        menu.append(f'<a class="mi" href="#{slug}"><img src="capas/{slug}.png" alt="" loading="lazy"><span>{html.escape(INFO[slug][0])}</span></a>')
for slug, a in AC.items():
    if any(f in REFS for f in a["faixas"]):
        menu.append(f'<a class="mi" href="#{slug}"><img src="capas/{a["capa"]}.png" alt="" loading="lazy"><span>{html.escape(a["titulo"])}</span></a>')


# acervo tambem na tabela do topo
for slug, a in AC.items():
    m = None
    for fn in a["faixas"]:
        if fn in REFS:
            m = REFS[fn]; break
    if not m:
        continue
    linhas.append(f'''<tr>
      <td><a href="#{slug}">{html.escape(a["titulo"])}</a></td>
      <td class="num">—</td>
      <td class="num">{m.get("tom","?")}</td>
      <td class="num">{m["dinamica_db"]} dB</td>
      <td class="num">{m["sustentadas"]}</td>
      <td class="num">{vib(m)}</td>
      <td><span class="badge sm" style="--bc:#94a3b8">acervo</span></td>
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
          .replace("{{SCATTER}}", "".join(sc))
          .replace("{{ACERVO}}", "".join(acards))
          .replace("{{MENU}}", "".join(menu)))
p = os.path.join(R, "guia", "musicas.html")
open(p, "w").write(out)
print("gerado:", p, f"({len(out)//1024} KB, {len(cards)} musicas)")
