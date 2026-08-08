#!/usr/bin/env python3
"""Monta o clipe seguindo um PLANO DE CENAS explicito (nao sorteia ordem).

Uso: montar_plano.py <plano.json>

plano.json:
{
  "banco": "clipe-v2",          # pasta com clipe-NN.mp4 e foto-NN.png
  "audio": "...mp3",
  "saida": "...mp4",
  "w": 1280, "h": 704,
  "fonte": "/caminho/Montserrat-ExtraBold.ttf",
  "cenas": [
    {"n": 1, "dur": 10, "modo": "cheio",  "texto": "NINGUEM TE CONTA O PRECO"},
    {"n": 5, "dur": 10, "modo": "fusao",  "sobre": 2},   # cena 5 com a 2 por cima
    {"n": 9, "dur": 10, "modo": "janela", "sobre": 8},   # historia cheia + canto na janela
    {"modo": "preto", "dur": 0.4, "texto": "SE PAGA"}
  ]
}

modo: cheio | fusao | janela | preto
Cada cena e construida no tempo exato pedido; o encadeamento e por crossfade.
"""
import json, os, subprocess, sys, math

P = json.load(open(sys.argv[1]))
BANCO = P["banco"]
W, H = P.get("w", 1280), P.get("h", 704)
FPS = 24
XF = P.get("xfade", 0.8)
FONTE = P.get("fonte", os.path.expanduser("~/.local/share/fonts/Montserrat-ExtraBold.ttf"))
TMP = os.path.join(BANCO, ".plano")
os.makedirs(TMP, exist_ok=True)


def sh(args):
    # stdin=DEVNULL: sem isso o ffmpeg engole o stdin de quem chamou, e um laco
    # `while read ... done <<< "$JOBS"` no shell morre depois do primeiro job.
    subprocess.run(args, check=True, stdin=subprocess.DEVNULL)


def dur_de(f):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip()
    return float(out)


def fonte_cena(c):
    """Devolve o caminho do clipe/foto da cena."""
    n = c["n"]
    cl = os.path.join(BANCO, f"clipe-{n:02d}.mp4")
    ft = os.path.join(BANCO, f"foto-{n:02d}.png")
    return cl if os.path.exists(cl) else ft



def rajada(c, i):
    """RAJADA: varias imagens em tempos minimos, corte seco na batida.
    c["cenas"] = lista de numeros; c["tiro"] = duracao de cada (default 0.28s)."""
    out = os.path.join(TMP, f"r{i:03d}.mp4")
    d = c["dur"]
    tiro = c.get("tiro", 0.28)
    ns = c["cenas"]
    partes = []
    k = 0
    while sum(p[1] for p in partes) < d:
        n = ns[k % len(ns)]
        partes.append((n, tiro)); k += 1
    ins, filt, lbl = [], "", []
    for j, (n, t) in enumerate(partes):
        src = fonte_cena({"n": n})
        if src.endswith(".png"):
            ins += ["-loop", "1", "-framerate", str(FPS), "-t", str(t), "-i", src]
        else:
            ins += ["-i", src]
        # leve zoom alternado para o corte nao parecer slideshow
        z = 1.0 + 0.06 * (j % 3)
        filt += (f"[{j}:v]scale={int(W*z)}:{int(H*z)},crop={W}:{H},fps={FPS},"
                 f"trim=0:{t},setpts=PTS-STARTPTS,format=yuv420p[p{j}];")
        lbl.append(f"[p{j}]")
    filt += "".join(lbl) + f"concat=n={len(partes)}:v=1:a=0,scale={W}:{H},setsar=1,trim=0:{d},setpts=PTS-STARTPTS[v]"
    sh(["ffmpeg", "-y", "-loglevel", "error"] + ins + ["-filter_complex", filt,
        "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", out])
    return out


def split(c, i):
    """SPLIT: 2 ou 3 imagens ao mesmo tempo na tela, dividindo o quadro."""
    out = os.path.join(TMP, f"s{i:03d}.mp4")
    d = c["dur"]
    ns = c["cenas"][:3]
    n = len(ns)
    lw = W // n
    ins, filt, lbl = [], "", []
    for j, num in enumerate(ns):
        src = fonte_cena({"n": num})
        if src.endswith(".png"):
            ins += ["-loop", "1", "-framerate", str(FPS), "-t", str(d), "-i", src]
        else:
            ins += ["-stream_loop", "-1", "-i", src]
        filt += (f"[{j}:v]scale={int(lw*1.6)}:{H}:force_original_aspect_ratio=increase,"
                 f"crop={lw}:{H},fps={FPS},trim=0:{d},setpts=PTS-STARTPTS[c{j}];")
        lbl.append(f"[c{j}]")
    filt += "".join(lbl) + f"hstack=inputs={n},scale={W}:{H},setsar=1,format=yuv420p[v]"
    sh(["ffmpeg", "-y", "-loglevel", "error"] + ins + ["-filter_complex", filt,
        "-map", "[v]", "-an", "-t", str(d), "-c:v", "libx264", "-crf", "18",
        "-preset", "veryfast", out])
    return out


def insertos(c, i, b):
    """INSERTO: flashes de outra imagem por cima do plano, sem cortar o fluxo."""
    ns = c.get("insertos") or []
    if not ns:
        return b
    out = os.path.join(TMP, f"x{i:03d}.mp4")
    d = c["dur"]
    passo = d / (len(ns) + 1)
    ins = ["-i", b]
    for n in ns:
        src = fonte_cena({"n": n})
        if src.endswith(".png"):
            ins += ["-loop", "1", "-framerate", str(FPS), "-t", "0.22", "-i", src]
        else:
            ins += ["-i", src]
    # monta em cadeia: cada inserto sobrepoe por 0.22s
    parts, cur = [], "[0:v]"
    for j, n in enumerate(ns):
        t0 = round(passo * (j + 1), 2)
        parts.append(f"[{j+1}:v]scale={W}:{H},fps={FPS},trim=0:0.22,setpts=PTS-STARTPTS[i{j}];"
                     f"{cur}[i{j}]overlay=0:0:enable='between(t,{t0},{t0+0.22})'[o{j}];")
        cur = f"[o{j}]"
    filt = "".join(parts) + f"{cur}format=yuv420p[v]"
    sh(["ffmpeg", "-y", "-loglevel", "error"] + ins + ["-filter_complex", filt,
        "-map", "[v]", "-an", "-t", str(d), "-c:v", "libx264", "-crf", "18",
        "-preset", "veryfast", out])
    return out


def base(c, i):
    """Constroi o video base da cena na duracao exata, sem texto."""
    out = os.path.join(TMP, f"b{i:03d}.mp4")
    d = c["dur"]
    if c["modo"] == "rajada":
        return rajada(c, i)
    if c["modo"] == "split":
        return split(c, i)
    if c["modo"] == "preto":
        sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
            "-i", f"color=c=black:s={W}x{H}:r={FPS}:d={d}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out])
        return out
    src = fonte_cena(c)
    if src.endswith(".png"):
        # foto -> Ken Burns. UMA imagem de entrada (senao zoompan explode).
        fr = int(d * FPS)
        z = ["zoom+0.0012", "if(eq(on,1),1.35,zoom-0.0010)", "1.22", "1.22"][i % 4]
        x = ["iw/2-(iw/zoom/2)", "iw/2-(iw/zoom/2)", f"(iw-iw/zoom)*on/{fr}",
             f"(iw-iw/zoom)*(1-on/{fr})"][i % 4]
        sh(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "1",
            "-t", "1", "-i", src, "-filter_complex",
            f"[0:v]scale={W*4}:{H*4},zoompan=z='{z}':x='{x}':y='ih/2-(ih/zoom/2)'"
            f":d={fr}:s={W}x{H}:fps={FPS},setsar=1,format=yuv420p",
            "-an", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", out])
        return out
    # clipe do Agnes: ping-pong e slow leve ate cobrir d, depois corta em d
    sd = dur_de(src)
    slow = c.get("slow", 1.25)
    ciclo = sd * 2 * slow                      # ping-pong ja esticado
    voltas = max(1, math.ceil(d / ciclo))
    sh(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", str(voltas - 1), "-i", src,
        "-filter_complex",
        f"[0:v]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0,"
        f"setpts={slow}*PTS,scale={W}:{H},setsar=1,fps={FPS},trim=0:{d},setpts=PTS-STARTPTS,format=yuv420p",
        "-an", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", out])
    return out


def compor(c, i, b):
    """Aplica fusao (dupla exposicao) ou janela (canto por cima da historia)."""
    if c["modo"] not in ("fusao", "janela") or not c.get("sobre"):
        return b
    src = fonte_cena({"n": c["sobre"]})
    out = os.path.join(TMP, f"c{i:03d}.mp4")
    d = c["dur"]
    if src.endswith(".png"):
        top = ["-loop", "1", "-framerate", str(FPS), "-t", str(d), "-i", src]
    else:
        sd = dur_de(src)
        top = ["-stream_loop", str(max(0, math.ceil(d / sd) - 1)), "-i", src]
    if c["modo"] == "fusao":
        # dupla exposicao: o de cima entra e sai por rampa de opacidade
        f = (f"[1:v]scale={W}:{H},fps={FPS},trim=0:{d},setpts=PTS-STARTPTS,"
             f"format=yuva420p,colorchannelmixer=aa=0.55[t];"
             f"[0:v][t]overlay=0:0:format=auto,format=yuv420p[v]")
    else:
        # janela: canto no canto inferior direito, com borda
        ww, hh = int(W * 0.34), int(H * 0.34)
        f = (f"[1:v]scale={ww}:{hh},fps={FPS},trim=0:{d},setpts=PTS-STARTPTS,"
             f"pad={ww+6}:{hh+6}:3:3:white@0.85[t];"
             f"[0:v][t]overlay=W-w-{int(W*0.04)}:H-h-{int(H*0.06)},format=yuv420p[v]")
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", b] + top +
       ["-filter_complex", f, "-map", "[v]", "-an", "-c:v", "libx264",
        "-crf", "18", "-preset", "veryfast", "-t", str(d), out])
    return out


def texto(c, i, b):
    """Queima o texto. textfile= porque acento quebra dentro do filtro."""
    if not c.get("texto"):
        return b
    tf = os.path.join(TMP, f"t{i:03d}.txt")
    open(tf, "w", encoding="utf-8").write(c["texto"])
    out = os.path.join(TMP, f"d{i:03d}.mp4")
    d = c["dur"]
    fs = int(H * (0.085 if c["modo"] == "preto" else 0.062))
    y = f"(h-text_h)/2" if c["modo"] == "preto" else f"h-text_h-{int(H*0.11)}"
    ap, fim = 0.35, max(0.4, d - 0.35)
    dt = (f"drawtext=fontfile='{FONTE}':textfile='{tf}':fontcolor=white:fontsize={fs}"
          f":x=(w-text_w)/2:y={y}:box=0:shadowcolor=black@0.85:shadowx=0:shadowy=3"
          f":alpha='if(lt(t,{ap}),t/{ap},if(lt(t,{fim}),1,max(0,({d}-t)/0.35)))'")
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", b, "-vf", f"{dt},format=yuv420p",
        "-an", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", out])
    return out


segs = []
for i, c in enumerate(P["cenas"]):
    c.setdefault("modo", "cheio")
    b = base(c, i)
    b = compor(c, i, b)
    b = insertos(c, i, b)
    b = texto(c, i, b)
    segs.append(b)
    print(f"cena {i+1:02d}/{len(P['cenas'])} {c['modo']:6s} {c['dur']:5.1f}s "
          f"{'texto' if c.get('texto') else ''}", flush=True)

# encadeia por crossfade
ins = []
for s in segs:
    ins += ["-i", s]
acc = P["cenas"][0]["dur"] - XF
filt = f"[0:v][1:v]xfade=transition=fade:duration={XF}:offset={acc:.3f}[v1]"
for k in range(2, len(segs)):
    acc += P["cenas"][k - 1]["dur"] - XF
    filt += f";[v{k-1}][{k}:v]xfade=transition=fade:duration={XF}:offset={acc:.3f}[v{k}]"
filt += f";[v{len(segs)-1}]format=yuv420p[vout]"
seq = os.path.join(TMP, "seq.mp4")
sh(["ffmpeg", "-y", "-loglevel", "error"] + ins + ["-filter_complex", filt,
    "-map", "[vout]", "-r", str(FPS), "-c:v", "libx264", "-profile:v", "high",
    "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "veryfast", "-an", seq])

AD = dur_de(P["audio"])
sh(["ffmpeg", "-y", "-loglevel", "error", "-i", seq, "-i", P["audio"],
    "-filter_complex",
    f"[0:v]fade=t=in:st=0:d=1.2,fade=t=out:st={AD-2:.2f}:d=2,format=yuv420p[v];"
    f"[1:a]afade=t=out:st={AD-3:.2f}:d=3[a]",
    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-profile:v", "high",
    "-pix_fmt", "yuv420p", "-crf", "21", "-preset", "medium",
    "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", "-shortest", P["saida"]])
print("pronto:", P["saida"], f"{os.path.getsize(P['saida'])//1048576} MB")
