#!/usr/bin/env python3
"""Mede todas as faixas geradas e grava docs/medicoes.json (alimenta a pagina)."""
import json, math, os, subprocess, sys
import numpy as np
from scipy.signal import get_window

OUT = os.path.expanduser("~/projetos/output/musicas")
SR, HOP, FR = 22050, 256, 1024
FMIN, FMAX = 75.0, 750.0


def medir(src):
    wav = "/tmp/_medir.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src,
                    "-ac", "1", "-ar", str(SR), wav], check=True)
    import soundfile as sf
    x, sr = sf.read(wav)
    x = np.asarray(x, float)
    nfr = (len(x) - FR) // HOP
    win = get_window("hann", FR)
    freqs = np.fft.rfftfreq(FR, 1 / sr)
    rms = np.zeros(nfr); cen = np.zeros(nfr)
    f0 = np.zeros(nfr); conf = np.zeros(nfr)
    lo, hi = int(sr / FMAX), int(sr / FMIN)
    for i in range(nfr):
        seg0 = x[i * HOP:i * HOP + FR]
        fr = seg0 * win
        rms[i] = np.sqrt(np.mean(fr ** 2)) + 1e-12
        S = np.abs(np.fft.rfft(fr)) + 1e-12
        cen[i] = float(np.sum(freqs * S) / np.sum(S))
        d = seg0 - seg0.mean()
        if np.sqrt(np.mean(d ** 2)) < 1e-4:
            continue
        ac = np.correlate(d, d, "full")[FR - 1:]
        ac /= (ac[0] + 1e-12)
        seg = ac[lo:hi]
        if len(seg) < 4 or seg.max() < 0.30:
            continue
        cand = np.where(seg >= 0.85 * seg.max())[0]
        k = int(cand[0])
        for c in cand:
            if 0 < c < len(seg) - 1 and seg[c] >= seg[c - 1] and seg[c] >= seg[c + 1]:
                k = int(c); break
        f0[i] = sr / (lo + k); conf[i] = seg[k]

    voz = (f0 > 0) & (f0 < 0.95 * FMAX) & (conf > 0.55) & (rms > np.percentile(rms, 55))
    fv = f0[voz]
    db = 20 * np.log10(rms / rms.max())
    r = {"dur": round(len(x) / sr, 1),
         "dinamica_db": round(float(np.percentile(db, 95) - np.percentile(db, 5)), 1),
         "brilho_hz": int(np.median(cen[voz])) if voz.sum() else 0,
         "pct_voz": round(100.0 * voz.sum() / max(nfr, 1), 1)}
    if len(fv) > 50:
        r["f0_mediana"] = int(np.median(fv))
        faixas = [(0, 130), (130, 260), (260, 440), (440, 700)]
        r["registro"] = [round(float(((fv >= a) & (fv < b)).mean() * 100), 1) for a, b in faixas]
    else:
        r["f0_mediana"] = 0; r["registro"] = [0, 0, 0, 0]

    idx = np.where(voz)[0]
    runs = np.split(idx, np.where(np.diff(idx) > 2)[0] + 1) if len(idx) else []
    sust, vr, vd = [], [], []
    for run in runs:
        if len(run) < int(0.35 * sr / HOP):
            continue
        sust.append(len(run) * HOP / sr)
        cents = 1200 * np.log2(f0[run] / np.median(f0[run]))
        cents = cents - np.convolve(cents, np.ones(9) / 9, "same")
        if len(cents) < 16:
            continue
        sp = np.abs(np.fft.rfft(cents * get_window("hann", len(cents))))
        ff = np.fft.rfftfreq(len(cents), HOP / sr)
        band = (ff > 3.5) & (ff < 8.5)
        if band.sum() and sp[band].max() > 2 * (np.median(sp) + 1e-9):
            vr.append(float(ff[band][np.argmax(sp[band])]))
            vd.append(float(np.percentile(np.abs(cents), 90)))
    r["sustentadas"] = len(sust)
    r["sust_max"] = round(max(sust), 1) if sust else 0
    r["vibrato_hz"] = round(float(np.median(vr)), 1) if vr else 0
    r["vibrato_cents"] = int(np.median(vd)) if vd else 0

    # ---- FRASES, ESPACO ENTRE ELAS E TROCA DE VOZ
    # Uma "frase" e um trecho continuo de canto. O espaco entre frases e o
    # silencio vocal entre elas. Quando duas frases vizinhas tem alturas medias
    # bem diferentes (>5 semitons), tratamos como TROCA de voz/registro — e o
    # espaco nessa troca e o que diz se a resposta entra "colada" ou com respiro.
    fr_idx = np.where(voz)[0]
    frases = []
    if len(fr_idx):
        for run in np.split(fr_idx, np.where(np.diff(fr_idx) > 3)[0] + 1):
            if len(run) < int(0.12 * sr / HOP):
                continue
            frases.append((run[0] * HOP / sr, run[-1] * HOP / sr,
                           float(np.median(12 * np.log2(f0[run] / 440.0) + 69))))
    vaos, vaos_troca, trocas = [], [], 0
    for i in range(1, len(frases)):
        g = frases[i][0] - frases[i - 1][1]
        if g > 6.0:                      # buraco grande = instrumental, nao conta
            continue
        vaos.append(g)
        if abs(frases[i][2] - frases[i - 1][2]) > 5.0:
            trocas += 1
            vaos_troca.append(g)
    r["frases"] = len(frases)
    r["frase_media"] = round(float(np.median([b - a for a, b, _ in frases])), 2) if frases else 0
    r["vao_mediano"] = round(float(np.median(vaos)), 2) if vaos else 0
    r["vao_p10"] = round(float(np.percentile(vaos, 10)), 2) if vaos else 0
    r["trocas_voz"] = trocas
    r["vao_na_troca"] = round(float(np.median(vaos_troca)), 2) if vaos_troca else 0
    r["colagens"] = int(sum(1 for g in vaos_troca if g < 0.15))  # resposta "colada"
    # lista das frases (inicio, fim, altura media em MIDI) para desenhar o dialogo
    r["frases_lista"] = [[round(a, 2), round(b, 2), round(mm, 1)] for a, b, mm in frases[:160]]

    # ---- HISTOGRAMA DE NOTAS (quais graus a voz usa)
    if len(fv) > 50:
        midi = 12 * np.log2(fv / 440.0) + 69
        h = np.bincount(np.mod(np.round(midi).astype(int), 12), minlength=12)
        r["notas"] = [round(float(v * 100.0 / h.sum()), 1) for v in h]
    else:
        r["notas"] = [0] * 12

    # ---- MOVIMENTO: contorno de altura e envelope de volume ao longo do tempo
    N = 240
    passo = max(1, nfr // N)
    cont, ener = [], []
    for i in range(0, nfr - passo + 1, passo):
        j = slice(i, i + passo)
        f = f0[j][voz[j]]
        # nota MIDI mediana da janela (None quando nao ha canto)
        cont.append(round(float(np.median(12 * np.log2(f / 440.0) + 69)), 1) if len(f) else None)
        ener.append(round(float(np.median(db[j])), 1))
    r["contorno"] = cont[:N]
    r["energia"] = ener[:N]

    # ---- TOM: correlacao do perfil de croma com os perfis maior/menor
    FRc, HOPc = 4096, 2048
    fq = np.fft.rfftfreq(FRc, 1 / sr); fq[0] = 1
    pc = np.mod(np.round(12 * np.log2(fq / 440.0) + 69).astype(int), 12)
    banda = (fq > 80) & (fq < 2000)
    croma = np.zeros(12)
    wn = np.hanning(FRc)
    for i in range(0, len(x) - FRc, HOPc):
        S = np.abs(np.fft.rfft(x[i:i + FRc] * wn))
        for p in range(12):
            croma[p] += S[banda & (pc == p)].sum()
    croma = croma / (croma.sum() + 1e-9)
    MAJ = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])
    MEN = np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17])
    nomes = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
    melhor, tom = -9, "?"
    for i in range(12):
        for perfil, suf in ((MAJ, "maior"), (MEN, "menor")):
            v = np.corrcoef(np.roll(croma, -i), perfil)[0, 1]
            if v > melhor:
                melhor, tom = v, f"{nomes[i]} {suf}"
    r["tom"] = tom
    r["tom_conf"] = round(float(melhor), 2)
    return r


dados = {}
alvo = sys.argv[1:] or sorted(os.listdir(OUT))
for slug in alvo:
    d = os.path.join(OUT, slug)
    spec = os.path.join(d, "spec.json")
    if not os.path.isdir(d) or not os.path.exists(spec):
        continue
    s = json.load(open(spec))
    faixas = {}
    for i in (1, 2):
        f = os.path.join(d, f"faixa-{i}.mp3")
        if os.path.exists(f):
            print(f"medindo {slug}/faixa-{i}...", flush=True)
            faixas[f"faixa-{i}"] = medir(f)
    if not faixas:
        continue
    dados[slug] = {"titulo": s.get("title") or s.get("titulo_sugerido") or slug,
                   "style": s.get("style", ""), "negativos": s.get("negativeTags", ""),
                   "modo": s.get("modo"), "model": s.get("model"),
                   "voz": s.get("vocalGender", "-"),
                   "styleWeight": s.get("styleWeight"), "faixas": faixas}

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medicoes.json")
json.dump(dados, open(p, "w"), ensure_ascii=False, indent=1)
print("gravado:", p, "| musicas:", len(dados))
