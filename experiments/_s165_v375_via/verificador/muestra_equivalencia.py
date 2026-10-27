# -*- coding: utf-8 -*-
"""Verificador S165 (contexto limpio): re-corre equivalencia_v375e.py sobre una MUESTRA elegida por el verificador y
agrega comprobaciones propias que el script del autor no hace.

Muestra: las 8 pasadas de publicación distinta y las 40 de VRP fuera de tolerancia (leídas del JSON del autor, sólo
como lista de ids), todas las protegidas, y 60 al azar (semilla 165) del resto. Comprobaciones propias por pasada:
  (a) rec["vrp_mw"] del record de la vía (procesar_grilla, lo que corre en producción) == round(VRP del bloque suelto, 3);
  (b) la máscara de rec["anomaly_pixels"] == la máscara del bloque suelto (detectar_mirova);
  (c) rec["n_anomalous_pixels"] == len(máscara).
Al final compara fila por fila (dvrp, misma_mascara, pub_via, pub_port) con el JSON del autor para los mismos ids.

Uso: python -I muestra_equivalencia.py
"""
from __future__ import annotations

import io
import json
import random
import sys
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
CARPETA = AQUI.parent
sys.path.insert(0, str(CARPETA))
import equivalencia_v375e as EQ  # noqa: E402  (inserta RAIZ, scripts y _s162_v375 en el path)

autor = json.loads((CARPETA / "equivalencia_v375e.json").read_text(encoding="utf-8"))
filas_autor = {f["i"]: f for f in autor["filas"]}
ids_pub = {d[0] for d in autor["publicacion"]["cercano"]["distintas"]}
ids_vrp = {f["i"] for f in autor["filas"] if f["dvrp"] is not None and f["dvrp"] > EQ.TOL_VRP_MW}
ids_prot = {f["i"] for f in autor["filas"] if f["prot"]}
resto = sorted(set(filas_autor) - ids_pub - ids_vrp - ids_prot)
random.seed(165)
ids_azar = set(random.sample(resto, 60))
MUESTRA = ids_pub | ids_vrp | ids_prot | ids_azar
print("muestra:", len(MUESTRA), "| pub:", len(ids_pub), "vrp:", len(ids_vrp), "prot:", len(ids_prot),
      "azar:", len(ids_azar), flush=True)

_obj_orig = EQ.objetivos


def objetivos_muestra():
    o = _obj_orig()
    return {i: v for i, v in o.items() if i in MUESTRA}


EQ.objetivos = objetivos_muestra

propias = {"a_vrp": 0, "b_mascara": 0, "c_n": 0, "n": 0, "fallas": []}
_rec_orig = EQ.record_de_la_via


def record_de_la_via_vigilado(o, g, mir, tir, r, v):
    rec, mascara, vrp = _rec_orig(o, g, mir, tir, r, v)
    propias["n"] += 1
    m_rec = sorted((q["fila"], q["col"]) for q in rec["anomaly_pixels"])
    m_sue = sorted(zip(*[x.tolist() for x in np.nonzero(mascara)]))
    if rec["vrp_mw"] == (round(float(vrp["VRP_MW"]), 3) if len(m_sue) else 0.0):
        propias["a_vrp"] += 1
    else:
        propias["fallas"].append(("a", o["id"], rec["vrp_mw"], float(vrp["VRP_MW"])))
    if m_rec == m_sue:
        propias["b_mascara"] += 1
    else:
        propias["fallas"].append(("b", o["id"], len(m_rec), len(m_sue)))
    if rec["n_anomalous_pixels"] == len(m_sue):
        propias["c_n"] += 1
    else:
        propias["fallas"].append(("c", o["id"], rec["n_anomalous_pixels"], len(m_sue)))
    return rec, mascara, vrp


EQ.record_de_la_via = record_de_la_via_vigilado

salida = AQUI / "muestra_equivalencia_salida_eq.txt"
js = AQUI / "muestra_equivalencia.json"
EQ.main(["--salida", str(salida), "--json", str(js)])

print("\n== comprobaciones propias del verificador (record de procesar_grilla contra los bloques sueltos)")
print(f"   (a) vrp_mw del record == round(VRP suelto, 3): {propias['a_vrp']} de {propias['n']}")
print(f"   (b) anomaly_pixels del record == máscara suelta: {propias['b_mascara']} de {propias['n']}")
print(f"   (c) n_anomalous_pixels == len(máscara): {propias['c_n']} de {propias['n']}")
print("   fallas:", propias["fallas"][:20])

print("\n== comparación fila por fila con el JSON del autor (mismos ids)")
mio = json.loads(js.read_text(encoding="utf-8"))
dif = []
for f in mio["filas"]:
    a = filas_autor[f["i"]]
    for k in ("npix_p", "npix_v", "misma_mascara", "fuente", "pub_via", "prot"):
        if f[k] != a[k]:
            dif.append((f["i"], k, f[k], a[k]))
    if f["pub_port"] != a["pub_port"]:
        dif.append((f["i"], "pub_port", f["pub_port"], a["pub_port"]))
    for k in ("vrp_vara", "vrp_via", "dvrp", "dvrp_regla"):
        x, y = f[k], a[k]
        if (x is None) != (y is None) or (x is not None and abs(x - y) > 1e-9):
            dif.append((f["i"], k, x, y))
print(f"   filas comparadas: {len(mio['filas'])}; diferencias con el autor: {len(dif)}")
for d in dif[:30]:
    print("    ", d)
print("   veredicto de la muestra:", mio["veredicto"])
