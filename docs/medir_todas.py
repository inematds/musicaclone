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
