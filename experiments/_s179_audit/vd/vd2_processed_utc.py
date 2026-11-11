# -*- coding: utf-8 -*-
"""VD2 (verificador frente D, S179). Afirmación 553: menor processed_utc de los records de la vía en los trozos D2 y D4
de la retrospectiva, por familia, leído directo de los artefactos (no de la unión del auditor).
Pregunta 1: si el encendido de la regla (§4.1, menor processed_utc con via true) no se moviera con el reemplazo, ¿lo
vería? Sí: si el menor processed_utc de los trozos fuera posterior a cualquier encendido real, el reemplazo no lo mueve.
Pregunta 2 (instrumento muerto): imprimo cuántos records leí por familia y cuántos traen processed_utc; un cero es SIN DATO.
Uso: python vd2_processed_utc.py <D2> <D4>
"""
import sys, io, json, re, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
PAT = re.compile(r"^trozo-(?P<v>[A-Za-z]+)-(?P<i>\d+)-(?P<a>\d{4}-\d\d-\d\d)_(?P<b>\d{4}-\d\d-\d\d)-intento-(?P<n>\d+)$")
def fam(s):
    s = str(s or "")
    return "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else "VIIRS375")
for nombre, carpeta in zip(("D2", "D4"), sys.argv[1:3]):
    n, conp, mn, mx, marca = collections.Counter(), collections.Counter(), {}, {}, collections.Counter()
    for p in Path(carpeta).iterdir():
        m = PAT.match(p.name)
        if not m:
            continue
        for r in json.loads((p / (m["v"] + ".json")).read_text(encoding="utf-8"))["records"]:
            f = fam(r.get("sensor")); n[f] += 1
            marca[(f, str(r.get("via_codigo_mirova")))] += 1
            t = r.get("processed_utc")
            if t:
                conp[f] += 1
                mn[f] = min(mn.get(f, t), t); mx[f] = max(mx.get(f, t), t)
    for f in sorted(n):
        print(f"{nombre} {f}: records {n[f]} (todos los intentos), con processed_utc {conp[f]}, menor {mn.get(f)}, mayor {mx.get(f)}")
    print(f"{nombre} marcas:", dict(marca))
