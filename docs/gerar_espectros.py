#!/usr/bin/env python3
"""Gera ESPECTROGRAMA + FORMA DE ONDA (PNG) e PIANO ROLL (dados) por faixa.

Espectrograma: eixo X tempo, eixo Y frequencia em escala musical (semitons),
cor = volume. E onde se ve o harmonico da voz, o vibrato e a afinacao.
Forma de onda: so o volume ao longo do tempo.
Piano roll: a nota cantada quantizada em semitom, virando blocos.

Uso: gerar_espectros.py            (todas)
     gerar_espectros.py <arquivo>  (uma)
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(R, "guia", "espectro")
os.makedirs(DEST, exist_ok=True)
SR = 22050
FR, HOP = 2048, 512
W, H = 900, 300          # espectrograma
WW, WH = 900, 90         # forma de onda

# escala de cor: escuro -> ambar -> claro (combina com a pagina)
def paleta():
    p = np.zeros((256, 3), np.uint8)
    for i in range(256):
        t = i / 255.0
        if t < 0.5:
            u = t / 0.5
            p[i] = (int(12 + 30 * u), int(12 + 18 * u), int(20 + 40 * u))
        else:
            u = (t - 0.5) / 0.5
            p[i] = (int(42 + 213 * u), int(30 + 175 * u), int(60 + 60 * u))
    return p
PAL = paleta()


def carrega(src):
    wav = "/tmp/_spec.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src,
                    "-ac", "1", "-ar", str(SR), wav], check=True)
    import soundfile as sf
    x, sr = sf.read(wav)
    return np.asarray(x, float), sr


def espectrograma(x, sr, out):
    n = (len(x) - FR) // HOP
    if n < 10:
        return None
    win = np.hanning(FR)
    freqs = np.fft.rfftfreq(FR, 1 / sr)
    # bins musicais: de C2 (~65Hz) a C7 (~2093Hz), 1 linha por meio-semitom
    lo_m, hi_m = 36, 96
    nb = (hi_m - lo_m) * 2
    bordas = 440.0 * 2 ** ((np.linspace(lo_m, hi_m, nb + 1) - 69) / 12.0)
    idx = [np.where((freqs >= bordas[i]) & (freqs < bordas[i + 1]))[0] for i in range(nb)]
    passo = max(1, n // W)
    cols = []
    for i in range(0, n - passo + 1, passo):
        S = np.zeros(len(freqs))
        for k in range(passo):
            S += np.abs(np.fft.rfft(x[(i + k) * HOP:(i + k) * HOP + FR] * win))
        S /= passo
        col = np.array([S[j].max() if len(j) else 0.0 for j in idx])
        cols.append(col)
    M = np.array(cols).T                      # (nb, tempo)
    M = 20 * np.log10(M + 1e-9)
    lo = np.percentile(M, 55)                 # corta o ruido de fundo
    hi = np.percentile(M, 99.7)
    M = np.clip((M - lo) / max(hi - lo, 1e-9), 0, 1)
    img = Image.fromarray((M[::-1] * 255).astype(np.uint8), "L").resize((W, H), Image.BILINEAR)
    rgb = PAL[np.array(img)]
    Image.fromarray(rgb, "RGB").save(out, optimize=True)
    return (lo_m, hi_m)


def forma_onda(x, out):
    passo = max(1, len(x) // WW)
    img = np.full((WH, WW, 3), (20, 20, 27), np.uint8)
    meio = WH // 2
    for i in range(WW):
        seg = x[i * passo:(i + 1) * passo]
        if not len(seg):
            continue
        a = int(min(meio - 1, abs(seg).max() * (meio - 2)))
        img[meio - a:meio + a + 1, i] = (226, 162, 59)
    Image.fromarray(img, "RGB").save(out, optimize=True)


def piano_roll(m):
    """Blocos de nota a partir do contorno ja medido (quantizado em semitom)."""
    cont = m.get("contorno") or []
    notas, atual = [], None
    for i, c in enumerate(cont):
        q = None if c is None else int(round(c))
        if q != atual:
            if atual is not None and notas and notas[-1][2] is not None:
                notas[-1][1] = i
            if q is not None:
                notas.append([i, i + 1, q])
            atual = q
        elif q is not None and notas:
            notas[-1][1] = i + 1
    return [n for n in notas if n[1] - n[0] >= 1][:400]


if __name__ == "__main__":
    med = json.load(open(os.path.join(R, "docs", "medicoes.json")))
    refs = json.load(open(os.path.join(R, "docs", "medicoes-refs.json")))
    OUTM = os.path.expanduser("~/projetos/output/musicas")
    REFD = [os.path.expanduser("~/projetos/musical/musicas"),
            os.path.join(OUTM, "_referencias")]

    tarefas = []
    for slug, d in med.items():
        for fn in d["faixas"]:
            tarefas.append((f"{slug}-{fn}", os.path.join(OUTM, slug, f"{fn}.mp3"), d["faixas"][fn]))
    for nome, m in refs.items():
        for base in REFD:
            p = os.path.join(base, nome + ".mp3")
            if os.path.exists(p):
                tarefas.append((nome, p, m)); break

    roll = {}
    for nome, src, m in tarefas:
        sp = os.path.join(DEST, f"{nome}-spec.png")
        wf = os.path.join(DEST, f"{nome}-wave.png")
        roll[nome] = piano_roll(m)
        if os.path.exists(sp) and os.path.exists(wf):
            print("ja existe", nome); continue
        try:
            x, sr = carrega(src)
            espectrograma(x, sr, sp)
            forma_onda(x, wf)
            print(f"{nome}  {os.path.getsize(sp)//1024}KB")
        except Exception as e:
            print(f"{nome}  ERRO {str(e)[:60]}")
    json.dump(roll, open(os.path.join(R, "docs", "pianoroll.json"), "w"))
    print("faixas:", len(tarefas))
