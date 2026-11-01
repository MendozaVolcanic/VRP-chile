# -*- coding: utf-8 -*-
"""ubicar.py <pdf> <regex>: paginas (idx 1) y lineas donde aparece el patron, solo para elegir que renderizar."""
import sys, re, io, fitz
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
doc = fitz.open(sys.argv[1]); pat = re.compile(sys.argv[2], re.I)
for i, p in enumerate(doc, 1):
    for ln in p.get_text().splitlines():
        if pat.search(ln):
            print(f"p{i}: {ln.strip()[:160]}")
