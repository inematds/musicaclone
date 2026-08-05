#!/usr/bin/env python3
"""Analisa um audio de referencia com o Gemini: e musica? estilo? letra?

Uso: analisa.py <ref.mp3> <duracao_segundos> > analise.json

Saida (JSON):
  e_musica, tem_vocal, idioma, motivo, genero, subgenero, bpm, tonalidade,
  instrumentacao[], voz{genero,timbre}, mood, era, tags_suno[], negative_tags[],
  titulo_sugerido, letra (com [Verse]/[Chorus]), letra_completa (bool)
"""
import base64
import json
import mimetypes
import os
import sys
import urllib.request

# gemini-2.5-flash foi descontinuado para contas novas (404 em 2026-08).
MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
API = "https://generativelanguage.googleapis.com"

PROMPT = """Voce recebe um audio. Responda SO com JSON valido, sem markdown.

Campos:
- e_musica (bool): o audio e uma musica (com instrumental/melodia)? Fala, podcast,
  entrevista, narracao ou ruido => false.
- tem_vocal (bool), idioma (ISO ex "en", "pt"), motivo (string curta em pt-BR).
- Se e_musica for false, preencha SO os campos acima e pare.
- genero, subgenero, bpm (int aprox), tonalidade, instrumentacao (lista),
  voz {genero: "m"|"f"|"none", timbre}, mood, era (ex "2020s").
- tags_suno: 6 a 12 tags curtas em ingles descrevendo o som para um gerador de
  musica (genero, instrumentos, producao, tipo de vocal, andamento).
- negative_tags: 0 a 4 tags do que evitar.
- titulo_sugerido: max 70 caracteres.
- letra: transcricao COMPLETA do que e cantado, no idioma original, estruturada
  com marcadores [Verse], [Chorus], [Bridge], [Outro]. Nao invente versos: se
  algum trecho for ininteligivel, escreva a linha como "..." .
- letra_completa (bool): true so se voce transcreveu a musica inteira do inicio
  ao fim sem cortes.
"""


def main() -> int:
    path, dur = sys.argv[1], float(sys.argv[2] or 0)
    key = os.environ.get("GOOGLE_API_KEY")
    if not key:
        print(json.dumps({"erro": "GOOGLE_API_KEY ausente"}))
        return 1

    data = open(path, "rb").read()
    mime = mimetypes.guess_type(path)[0] or "audio/mpeg"
    if len(data) > 18 * 1024 * 1024:
        print(json.dumps({"erro": "audio > 18MB: corte antes de analisar"}))
        return 1

    body = {
        "contents": [{"parts": [
            {"text": PROMPT},
            {"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode()}},
        ]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
    }
    req = urllib.request.Request(
        f"{API}/v1beta/models/{MODEL}:generateContent?key={key}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        raw = json.load(r)["candidates"][0]["content"]["parts"][0]["text"]

    out = json.loads(raw)

    # Checagem de completude da letra: Whisper/Gemini cortam vocal cantado.
    # ~0.9 palavra/segundo e um piso conservador para musica com vocal.
    letra = (out.get("letra") or "").strip()
    palavras = len([w for w in letra.split() if not w.startswith("[")])
    esperado = int(dur * 0.9)
    truncada = letra.endswith(("of", "the", "a", "and", "e", "de", "que")) or (
        letra and letra[-1].isalnum() and not letra.endswith((".", "!", "?", "]"))
    )
    if out.get("tem_vocal") and (palavras < esperado * 0.35 or truncada):
        out["letra_completa"] = False
    out["_palavras_letra"] = palavras
    out["_palavras_esperadas_min"] = int(esperado * 0.35)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
