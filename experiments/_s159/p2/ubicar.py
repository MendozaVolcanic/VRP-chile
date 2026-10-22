"""Ubica (NO cita) pasajes por palabra clave en la capa de texto de los PDF.
La capa de texto corrompe simbolos (A95): sirve solo para saber que pagina renderizar.
Uso: python ubicar.py <pdf> <regex> [contexto_chars]"""
import sys, re, fitz
pdf, pat = sys.argv[1], sys.argv[2]
ctx = int(sys.argv[3]) if len(sys.argv) > 3 else 160
d = fitz.open(pdf)
rx = re.compile(pat, re.I)
for i, p in enumerate(d):
    t = p.get_text().replace('\n', ' ')
    for m in rx.finditer(t):
        a, b = max(0, m.start()-ctx), min(len(t), m.end()+ctx)
        print(f"[p_idx {i+1}] ...{t[a:b]}...")
