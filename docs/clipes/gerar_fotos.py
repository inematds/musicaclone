#!/usr/bin/env python3
"""Gera a sequencia de fotos 16:9 no inemaimg (flux2-klein).

Uso: gerar_fotos.py <pasta-destino> [indice-inicial]
Le as cenas de cenas.json na pasta (lista de {n, prompt}).
"""
import base64, json, os, sys, time, urllib.request

DEST = sys.argv[1]
START = int(sys.argv[2]) if len(sys.argv) > 2 else 1
API = "http://localhost:8000/generate"

LOOK = ("raw documentary photograph, live-action cinema still, anamorphic 35mm, "
        "natural skin texture and pores, film grain, practical light, shallow depth of field, "
        "muted teal and amber grade")
NEG = ("cartoon, 3d render, cgi, pixar, anime, illustration, painting, plastic skin, "
       "doll face, oversaturated, text, watermark, extra fingers, deformed")

cenas = json.load(open(os.path.join(DEST, "cenas.json")))
for c in cenas:
    if c["n"] < START:
        continue
    out = os.path.join(DEST, f"foto-{c['n']:02d}.png")
    if os.path.exists(out):
        print("ja existe:", out); continue
    body = json.dumps({
        "model": "flux2-klein",
        "prompt": f"{c['prompt']}. {LOOK}",
        "negative_prompt": NEG,
        "width": int(os.environ.get("W", 1312)), "height": int(os.environ.get("H", 736)),
        "seed": 1000 + c["n"],
    }).encode()
    t = time.time()
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        d = json.load(r)
    b64 = d.get("image") or d.get("images", [None])[0] or d.get("image_base64")
    if not b64:
        print("resposta sem imagem:", list(d)[:6]); sys.exit(1)
    open(out, "wb").write(base64.b64decode(b64.split(",")[-1]))
    print(f"{out}  {time.time()-t:.0f}s")
