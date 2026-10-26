# -*- coding: utf-8 -*-
"""Verificador V750-B (VB): sobre las 510 grillas de N mide dos cosas que el pre-registro no mide.

(a) ANCLA. analizar_v750b.record_cumulo clasifica summit/far por la distancia del centroide del cumulo al CENTRO de la
    grilla (C, C); produccion (process_viirs_mod, get_detection_anchor) mide desde el crater de volcanoes.yaml. Cuento,
    por brazo y volcan, los cumulos publicables (npix > 0) cuya clase cambia segun el ancla: far desde el centro pero
    summit desde el crater (el brazo pierde una publicacion por el ancla, no por la ROI) y al reves.
(b) B0e. El pre-registro dice «medido: 0 de 510» para la matriz de ejemplo tal cual (anillo 21 x 19) y el script que lo
    midio ya no existe (se retiro el brazo). Lo re-mido: mascara de B0 contra la de la caja 21 x 19 (filas 22-42,
    columnas 24-42, probe_granulos.caja_mirova docstring).

Pregunta 1: si el ancla no importara, (a) daria 0 en todos; si B0e importara, (b) daria > 0. Control positivo de (a):
un cumulo sintetico a 6 km al NW del centro de Tupungatito (inner 7) tiene que dar summit por el centro y far por el
crater... no: tiene que dar DISTINTA clase si y solo si cruza el inner por un lado. Se imprime un caso construido.
Pregunta 2: si las grillas no cargaran, `pasadas` seria 0 y el script aborta.
Uso: python ancla_centro_vs_crater_510.py --arbol <arbol de origin/main con _s162_v750b> --insumos <n/> --grillas D:/...
"""
from __future__ import annotations
import argparse, collections, json, sys
from pathlib import Path
import numpy as np, yaml

ap = argparse.ArgumentParser()
ap.add_argument("--arbol", required=True); ap.add_argument("--insumos", required=True, type=Path)
ap.add_argument("--grillas", required=True, type=Path)
a = ap.parse_args()
A = Path(a.arbol)
sys.path.insert(0, str(A / "experiments/_s162_v750b")); sys.path.insert(0, str(A / "scripts"))
import probe_v750b as PV, objetivos_v750b as OV, banco_paridad as B, analizar_v750b as AN  # noqa: E402
RUNS = ("run_39682867040", "run_39693661527", "run_39680724047")
C = PV.C

res = {}
for f in sorted((a.insumos / "n").rglob("resultados_*.json")):
    for r in json.loads(f.read_text(encoding="utf-8")):
        if r.get("estado") == "ok" or r["id"] not in res:
            res[r["id"]] = r
objs = []
for nom in ("objetivos_n.json", "objetivos_censo.json"):
    objs += json.loads((a.insumos / "n" / nom).read_text(encoding="utf-8"))
vy = {v["name"]: v for v in yaml.safe_load((A / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
inner = B.inner_desde_html()
OV.completar(objs, vy, inner)

def caja_21x19():
    b = np.zeros((67, 67)); b[22:43, 24:43] = 1; b[30:37, 30:37] = 2
    return b

def clase(cu, ancla, ik):
    fr, fc = np.mean([p[0] for p in cu]), np.mean([p[1] for p in cu])
    d = float(np.hypot(fr - ancla[0], fc - ancla[1]) * 0.75)
    return ("summit" if d <= ik else "far"), d

cnt = collections.Counter(); ejemplos = collections.defaultdict(list); pasadas = 0; b0e_dist = 0
for o in objs:
    r = res.get(o["id"])
    if not r or r.get("estado") != "ok" or r.get("dayflag") != 0 or not r.get("oraculo"):
        continue
    gp = next((p for run in RUNS for p in sorted((a.grillas / run).glob(f"*/grilla_{o['id']:03d}.npz"))), None)
    if gp is None:
        continue
    z = np.load(gp); pasadas += 1
    cj = PV.cajas(tuple(o["celda_crater"]), o["inner_km"])
    s = {n: PV.oraculo_caja(z["m13"], z["m15"], 0, r["sunglint"], box, semillas=0) for n, box in cj.items()}
    e = PV.oraculo_caja(z["m13"], z["m15"], 0, r["sunglint"], caja_21x19(), semillas=0)
    if sorted((p[0], p[1]) for p in e["pixeles"]) != sorted((p[0], p[1]) for p in s["B0"]["pixeles"]):
        b0e_dist += 1
    for nom, x in s.items():
        if not x["npix"]:
            continue
        cu = AN.cumulo_del_mas_radiante(x["pixeles"])
        c_cen, d_cen = clase(cu, (C, C), o["inner_km"])
        c_cra, d_cra = clase(cu, tuple(o["celda_crater"]), o["inner_km"])
        cnt[(nom, o["volcan"], "cumulos")] += 1
        if c_cen != c_cra:
            cnt[(nom, o["volcan"], f"centro={c_cen}/crater={c_cra}")] += 1
            if len(ejemplos[(nom, o["volcan"])]) < 3:
                ejemplos[(nom, o["volcan"])].append((o["hora_utc"], o["lab"], round(d_cen, 2), round(d_cra, 2), len(cu)))
assert pasadas, "sin grillas: SIN DATO"
print(f"pasadas con grilla: {pasadas} (ventana de N: objetivos_n + objetivos_censo, 2026-04-01 a 2026-10-21)")
print(f"(b) B0e (21 x 19) con mascara distinta de B0: {b0e_dist} de {pasadas}")
print("(a) cumulos cuya clase cambia segun el ancla (centro de grilla vs crater del yaml), por brazo y volcan:")
for k in sorted(cnt):
    if k[2] != "cumulos":
        print(f"   {k[0]} {k[1]:22s} {k[2]:28s} {cnt[k]:3d} de {cnt[(k[0], k[1], 'cumulos')]} cumulos")
print("   ejemplos (hora, lab, d_centro, d_crater, n_pix):")
for k, v in sorted(ejemplos.items()):
    print(f"   {k}: {v}")
# control positivo construido: Tupungatito inner 7, crater (27, 30). Cumulo en (24, 27): a 12,7 celdas = 9,5 km del centro
# (far) y a 4,2 celdas = 3,2 km del crater (summit). La funcion tiene que distinguirlos.
cu = [(24, 27)]
print("control positivo construido Tupungatito (24,27):", clase(cu, (C, C), 7.0), clase(cu, (27, 30), 7.0))
assert clase(cu, (C, C), 7.0)[0] == "far" and clase(cu, (27, 30), 7.0)[0] == "summit"
