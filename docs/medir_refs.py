#!/usr/bin/env python3
"""Mede as REFERENCIAS (musical/musicas/*.mp3) e grava docs/medicoes-refs.json."""
import importlib.util, json, os, sys

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("mt", os.path.join(here, "medir_todas.py"))
# medir_todas roda ao importar; isolamos so a funcao copiando o modulo em modo seguro
src = open(os.path.join(here, "medir_todas.py")).read()
src = src.split("dados = {}")[0]          # corta a parte que executa
ns = {"__name__": "mt"}
exec(compile(src, "medir_todas.py", "exec"), ns)
medir = ns["medir"]

REF = os.path.expanduser("~/projetos/musical/musicas")
EXTRA = os.path.expanduser("~/projetos/output/musicas/_referencias")
PULA = ("musicgen-local-instrumental", "reel-fb-instrumental")

out = {}
alvo = sorted(f for f in os.listdir(REF) if f.endswith(".mp3")
              and not any(p in f for p in PULA))
alvo = [(REF, f) for f in alvo]
if os.path.isdir(EXTRA):
    alvo += [(EXTRA, f) for f in sorted(os.listdir(EXTRA)) if f.endswith(".mp3")]
for base, f in alvo:
    p = os.path.join(base, f)
    if os.path.getsize(p) < 60_000:
        print("pula (curto demais):", f, flush=True); continue
    print("medindo", f, flush=True)
    try:
        out[f[:-4]] = medir(p)
    except Exception as e:
        print("  erro:", str(e)[:60], flush=True)

d = os.path.join(here, "medicoes-refs.json")
json.dump(out, open(d, "w"), ensure_ascii=False, indent=1)
print("gravado:", d, "|", len(out), "referencias")
