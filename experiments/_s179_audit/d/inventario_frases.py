# -*- coding: utf-8 -*-
"""Inventario de frases de Nicolas en la bitacora S172 a S178 (tasks/LOOP_OBJETIVOS.md de loop 0472cd95e, lineas 570 a
1689, copiadas a bitacora_s172_s178.md). Lista cada entrada (titulo ###) que cita una frase entre comillas angulares
cerca de la palabra Nicolas, Frase o Decision. Uso: python inventario_frases.py <bitacora> <salida.txt>"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
txt = open(sys.argv[1], encoding="utf-8").read().splitlines()
pat = re.compile(r"(Nicol[aá]s|[Ff]rase|[Dd]ecisi[oó]n(?:es)?)[^«\n]{0,90}«([^»]{2,220})»")
titulo, out = None, []
for i, l in enumerate(txt, 1):
    if l.startswith("### "):
        titulo = l[4:]
    for m in pat.finditer(l):
        out.append((i, titulo, m.group(2)))
with open(sys.argv[2], "w", encoding="utf-8") as fh:
    for i, t, f in out:
        fh.write(f"{i}\t{t[:110]}\t«{f}»\n")
print(len(out), "frases en", len({t for _, t, _ in out}), "entradas")
for i, t, f in out:
    print(f"{i:5d} | {t[:70]:70s} | «{f[:110]}»")
