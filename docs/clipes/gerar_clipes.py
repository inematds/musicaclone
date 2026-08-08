#!/usr/bin/env python3
"""Anima cada foto-NN.png em clipe-NN.mp4 via Agnes, com tamanho configuravel.

Uso: gerar_clipes.py <pasta> [<pasta> ...]
Serial e resumivel (pula clipe que ja existe). Respeita o rate limit de 5 req/min.
O tamanho sai da propria foto, entao 9:16 funciona.
"""
import os, sys, time, json, urllib.request, urllib.error, struct

sys.path.insert(0, "/home/nmaldaner/projetos/videos-agnes")
import pipeline as P

MOVES = [
    "slow push in on the singer, warm bokeh breathing behind",
    "slow push in on the man singing, light shifting on his face",
    "the working layer fades in and out over the singing layer, slow drift",
    "macro slow pull back from the forearm, dust in the light",
    "the parents layer fades in and the singer layer fades out, gentle drift",
    "slow push in on the workshop, dust floating in the sunbeam",
    "slow push in on her face as she sings, hair moving",
    "slow tilt up from his face to the sunrise peaks",
    "the mountain layer swells and the singers fade through it",
    "slow tracking beside the climbers, clouds moving below",
    "slow push in on the hands meeting, backlight flaring",
    "slow crane up and back from the summit, clouds rolling",
    "slow orbit around the table, glasses raised, light flickering",
    "the summit layer fades over the family table and back again",
    "slow push in through the doorway, warm light growing",
    "slow pull back from the crowd singing, arms up, lights blooming",
]


def size_of(png):
    b = open(png, "rb").read(24)
    w, h = struct.unpack(">II", b[16:24])
    return w, h


def gerar(dest, kf_a, kf_b, prompt, frames, w, h, tentativas=8):
    body = {"model": "agnes-video-v2.0",
            "prompt": f"Smooth cinematic transition between the keyframes: {prompt}. "
                      f"Natural motion, consistent characters and style, cinematic camera.",
            "num_frames": frames, "frame_rate": P.FPS, "seed": P.SEED,
            "width": w, "height": h,
            "extra_body": {"image": [kf_a, kf_b], "mode": "keyframes"}}
    vid = None
    for t in range(1, tentativas + 1):
        try:
            d = P._post(P.VID_API, body, timeout=300)
            vid = d.get("video_id") or d.get("task_id") or d.get("id")
            break
        except urllib.error.HTTPError as e:
            print(f"    HTTP {e.code}", flush=True)
            time.sleep(min(300, 60 * t) if e.code == 429 else 6 * t)
        except Exception as e:
            print(f"    erro: {str(e)[:70]}", flush=True)
            time.sleep(6 * t)
    if not vid:
        return None
    t0 = time.time()
    while time.time() - t0 < 1800:
        try:
            d = P._get(P.VID_GET + vid)
            st = d.get("status")
            if st == "completed":
                u = d.get("url") or (d.get("data") or [{}])[0].get("url") or d.get("video_url")
                if not u:
                    return None
                open(dest, "wb").write(urllib.request.urlopen(u, timeout=300).read())
                return dest
            if st == "failed":
                return None
        except Exception:
            pass
        time.sleep(10)
    return None


for pasta in sys.argv[1:]:
    fotos = sorted(f for f in os.listdir(pasta) if f.startswith("foto-") and f.endswith(".png"))
    for f in fotos:
        n = f[5:7]
        dest = os.path.join(pasta, f"clipe-{n}.mp4")
        if os.path.exists(dest) and os.path.getsize(dest) > 10000:
            print("ja existe", dest, flush=True); continue
        src = os.path.join(pasta, f)
        w, h = size_of(src)
        kf = P.keyframe(src)
        # movs.json na pasta (lista de strings, 1 por cena) vence a lista fixa
        mvfile = os.path.join(pasta, "movs.json")
        movs = json.load(open(mvfile)) if os.path.exists(mvfile) else MOVES
        mv = movs[int(n) - 1] if int(n) <= len(movs) else "slow cinematic push in"
        t0 = time.time()
        out = gerar(dest, kf, kf, mv, P.frames_para(5), w, h)
        print(f"{'ok ' if out else 'FALHOU '}{dest} {time.time()-t0:.0f}s", flush=True)
        time.sleep(25)
open("/home/nmaldaner/projetos/output/musicas-video/.fila-ok","w").write("ok")
print("FIM", flush=True)
