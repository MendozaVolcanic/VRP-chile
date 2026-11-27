# -*- coding: utf-8 -*-
"""S201: frecuencia real del mecanismo R5C-101 (cierre de la ronda 5 de Codex) en el barrido del piso.
POR QUÉ: al bajar el piso, un foco débil junto a un hueco de datos puede quedar alertado sin vecinos para el fondo y la
vía guarda la escena como no medida (diag_codigo_mirova.motivo_vacio); el evaluador la saca del denominador sólo en ese
brazo y puede elegir otro piso con los controles en verde. Codex lo mostró con escenas sintéticas y dejó la frecuencia
real SIN DATO. Aquí se cuenta, sobre la unión real (unir_tandas.py) hasta la última tanda del manifiesto, cuántas
escenas son inválidas en un brazo y válidas en el control (y al revés), por brazo, motivo, sensor y volcán, de noche y de día.
Control del instrumento: también cuenta las inválidas comunes a todos los brazos (tiene que ser > 0: hay escenas que la
vía no mide en ningún brazo, por ejemplo por la mitad de la grilla sin dato).
Uso: python medir_invalidas_por_brazo.py <carpeta de la unión>"""
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
U = Path(sys.argv[1])
BRAZOS = ["_s196_lab_sinzona", "_s196_lab_control", "_s196_lab_p300", "_s196_lab_p275", "_s196_lab_p250",
          "_s196_lab_p225", "_s196_lab_p200", "_s196_lab_p175", "_s196_lab_p150"]


def motivo(r):
    return (r.get("diag_codigo_mirova") or {}).get("motivo_vacio")


inval = {b: {} for b in BRAZOS}
total = Counter()
for b in BRAZOS:
    for f in sorted((U / b).glob("*.json")):
        for r in json.loads(f.read_text(encoding="utf-8"))["records"]:
            k = (f.stem, r.get("sensor"), r["datetime_utc"])
            total[b] += 1
            m = motivo(r)
            if m:
                inval[b][k] = m
ctrl = inval["_s196_lab_control"]
comunes = set.intersection(*(set(inval[b]) for b in BRAZOS))
print("records por brazo:", dict(total))
print("inválidas por brazo:", {b: len(inval[b]) for b in BRAZOS})
print("inválidas comunes a los 9 brazos (control del instrumento):", len(comunes),
      Counter(inval["_s196_lab_control"][k] for k in comunes).most_common())
print()
for b in BRAZOS:
    solo_b = {k: inval[b][k] for k in inval[b] if k not in ctrl}
    solo_c = {k: ctrl[k] for k in ctrl if k not in inval[b]}
    print(f"{b}: inválidas en el brazo y válidas en el control = {len(solo_b)}; al revés = {len(solo_c)}")
    if solo_b:
        print("   por motivo:", Counter(solo_b.values()).most_common())
        print("   por volcán:", Counter(k[0] for k in solo_b).most_common())
        print("   por sensor:", Counter(k[1] for k in solo_b).most_common())
        for k in sorted(solo_b)[:8]:
            print("     ", k, solo_b[k])
