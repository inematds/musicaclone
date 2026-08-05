#!/usr/bin/env python3
"""Compara duas faixas no Gemini: referencia original x nossa geracao."""
import base64, json, mimetypes, os, sys, urllib.request

REF, NOSSA = sys.argv[1], sys.argv[2]
KEY = os.environ["GOOGLE_API_KEY"]
MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")

PROMPT = """Voce recebe DOIS audios.
AUDIO 1 = referencia original (trecho curto).
AUDIO 2 = uma faixa gerada por IA que tenta o mesmo tipo de energia, em portugues.

Compare os VOCAIS com ouvido critico. Responda SO JSON, em pt-BR, campos:

- voz_feminina: {ref: {potencia_0a10, altura_tessitura, desespero_0a10, descricao},
                 nossa: {potencia_0a10, altura_tessitura, desespero_0a10, descricao},
                 veredito: "quem esta mais forte e por que, em 1-2 frases"}
- voz_masculina: {ref: {gravidade_0a10, descricao}, nossa: {gravidade_0a10, descricao},
                  veredito}
- interacao: {ref: "como as vozes se revezam: colado? com espaco? call and response?",
              nossa: "idem",
              espacos: "na NOSSA faixa, o que acontece nos espacos entre as frases? a voz feminina preenche com forca ou fica vazio?",
              veredito}
- o_que_falta: lista de 3 a 6 ajustes CONCRETOS para a nossa faixa ficar com vocal
  feminino mais forte/agudo/desesperado, masculino mais grave, e interacao mais
  dinamica e colada. Cada item deve dizer o que mudar em TAGS DE ESTILO ou em
  MARCACAO DE LETRA (ex: [Belting], [Whisper], vocalGender, tags de producao),
  porque so isso da pra controlar via API do Suno.
- tags_sugeridas: lista de tags de estilo em ingles para a proxima geracao.
"""


def part(path):
    data = open(path, "rb").read()
    mime = mimetypes.guess_type(path)[0] or "audio/mpeg"
    return {"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode()}}


body = {
    "contents": [{"parts": [
        {"text": PROMPT},
        {"text": "AUDIO 1 (referencia original):"}, part(REF),
        {"text": "AUDIO 2 (nossa geracao):"}, part(NOSSA),
    ]}],
    "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
}
req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}",
    data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=900) as r:
    print(json.dumps(json.loads(json.load(r)["candidates"][0]["content"]["parts"][0]["text"]),
                     ensure_ascii=False, indent=2))
