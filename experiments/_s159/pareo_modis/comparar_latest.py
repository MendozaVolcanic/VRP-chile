# -*- coding: utf-8 -*-
"""Diferencias hoja a hoja entre dos latest.json (sin generated_utc). Uso: comparar_latest.py A B"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
def hojas(x, p=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from hojas(v, f"{p}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from hojas(v, f"{p}[{i}]")
    else:
        yield p, x
A = dict(hojas(json.load(open(sys.argv[1], encoding="utf-8"))))
B = dict(hojas(json.load(open(sys.argv[2], encoding="utf-8"))))
dif = [(k, A.get(k, "<falta>"), B.get(k, "<falta>")) for k in sorted(set(A) | set(B))
       if A.get(k, "<falta>") != B.get(k, "<falta>") and "generated_utc" not in k]
print(f"{len(A)} hojas A, {len(B)} hojas B, {len(dif)} distintas")
for k, a, b in dif:
    print(f"  {k}: {a} -> {b}")
