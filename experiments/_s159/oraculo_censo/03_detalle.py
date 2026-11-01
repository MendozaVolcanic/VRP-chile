# -*- coding: utf-8 -*-
"""S159, censo del oráculo, paso 3 (descriptivo, post hoc, no pre-registrado): en los negativos limpios, cuántos tienen
píxeles del oráculo y por qué el predicado del tablero no publica los que no publica; y los negativos publicados por
O-sens que el lote de N no había visto. Lee tabla_por_pasada.csv y negativos_publicados.csv (salidas de 02_analizar.py).
Pregunta 1: si el predicado no actuara, detectados = publicados; la diferencia es lo que filtra. Pregunta 2: un oráculo
muerto daría 0 detectados también en las alertas (control 4 de 02: 193 y 241 detectadas).
Ventana: VIIRS 750 nocturno 2026-04-01 a 2026-10-21 sin 10-18 y 10-19; sólo pasadas ok (sin fuera ni SIN DATO).
"""
import collections
import csv
import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
t = list(csv.DictReader(open(AQUI / "tabla_por_pasada.csv", encoding="utf-8")))
neg = [r for r in t if r["lab"] == "neg_limpio" and r["estado"] == "ok"]
print("negativos ok:", len(neg))
for c in ("Odef", "Osens"):
    det = [r for r in neg if r[f"{c}_npix"] not in ("", "0")]
    pub = [r for r in det if r[f"pub_{c}"] == "1"]
    print(f"{c}: con pixeles {len(det)}, publicados {len(pub)}, detectados sin publicar {len(det) - len(pub)}")
    print("   detectados por volcan:", dict(collections.Counter(r["volcan"] for r in det)))
    print("   vrp de los detectados sin publicar:", sorted(round(float(r[f"{c}_vrp"]), 3) for r in det if r[f"pub_{c}"] != "1")[:40])
p = list(csv.DictReader(open(AQUI / "negativos_publicados.csv", encoding="utf-8")))
nuevos = [r for r in p if r["caja"] == "O-sens" and r["pub_O"] == "1" and r["en_n"] == "False"]
print("O-sens publica y N no los habia medido:", [(r["volcan"], r["hora_utc"], r["O_npix"], round(float(r["O_vrp"]), 3),
                                                     r["O_dist"], round(float(r["O_tmax"]), 1), r["z"]) for r in nuevos])
amb = [r for r in p if r["pub_O"] == "1" and r["O_banda"] and json.loads(r["O_banda"])[0] <= 0]
print("publicados con banda de triangulacion que toca 0:", [(r["caja"], r["volcan"], r["hora_utc"], r["O_banda"]) for r in amb])
