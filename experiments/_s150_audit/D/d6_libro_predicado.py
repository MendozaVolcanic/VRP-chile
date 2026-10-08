# -*- coding: utf-8 -*-
"""S150 auditor D, sonda 6: el libro de cuentas (scripts/libro_de_cuentas.py) dice medir el recall VIIRS 750
"del DASHBOARD" con isValidDetection e isSummitDetection reescritos en Python. Esta sonda compara esa
reescritura con el predicado real del tablero ejecutado con node, sobre los mismos records y las mismas
noches de alerta (las de _s126_lib.cargar_mirova), y cuenta cuantas alertas MODIS nocturnas tira el filtro
horario de _s126_lib (hora UTC entre 3 y 9) contra el filtro por elevacion solar del pipeline.

PREGUNTAS DEL INSTRUMENTO
 1. Si la reescritura del libro hubiera derivado del tablero, esta sonda lo veria? Si: cuenta records donde
    las dos versiones discrepan, por sensor, y recalcula la cifra del libro con cada una.
 2. Si la sonda estuviera muerta, se veria distinto? Control positivo: la cifra con la reescritura tiene que
    ser la misma que devuelve libro_de_cuentas.r_recall_v750_dash() (lo importo y lo llamo).

Uso: python d6_libro_predicado.py
"""
import collections, io, json, os, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts")); sys.path.insert(0, str(RAIZ / "experiments"))
import banco_paridad as bp
from _s126_lib import VENTS, bucket, cargar_mirova

inner = bp.inner_desde_html()
mir, _ = cargar_mirova(("2026-01-01", "2026-12-31"))


def libro_valida_summit(r):
    v = r.get("vrp_mw") or 0
    if not (v > 0 or r.get("triggered_test1") is True):
        return False
    if v == 0 and r.get("discarded_reason") and not r.get("triggered_test1"):
        return False
    dc = r.get("distance_class")
    if dc == "far":
        return False
    if dc != "summit" and not ((r.get("vrp_vent_mw") or 0) > 0):
        return False
    return True


recs, casos = [], []
for vol in VENTS:
    for r in json.load(open(RAIZ / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]:
        b = bucket(r.get("sensor"))
        if b is None or not ("2026-01-01" <= r.get("datetime_utc", "")[:10] <= "2026-12-31"):
            continue
        recs.append((vol, b, r["datetime_utc"][:10], libro_valida_summit(r)))
        casos.append([{k: r.get(k) for k in bp.CAMPOS_JS}, inner[vol]])
pred = bp.correr_node(casos)
disc = collections.Counter()
for (vol, b, d, lib), p in zip(recs, pred):
    disc[(b, "libro" if lib else "-", "tablero" if p[4] else "-")] += 1
print("records 2026, cruce libro x tablero(node):")
for k, v in sorted(disc.items()):
    print("  ", k, v)

for b in ("v750", "v375", "modis"):
    nl, nt = set(), set()
    for (vol, bb, d, lib), p in zip(recs, pred):
        if bb != b:
            continue
        if lib:
            nl.add((vol, d))
        if p[4]:
            nt.add((vol, d))
    tot = [(vol, d) for vol in VENTS for (d, bb) in (mir.get(vol) or {}) if bb == b]
    print("%-5s noches alerta %4d | recall con la reescritura del libro %.2f %% | con el tablero real %.2f %%" % (
        b, len(tot), 100 * sum(1 for x in tot if x in nl) / len(tot), 100 * sum(1 for x in tot if x in nt) / len(tot)))

import importlib.util
spec = importlib.util.spec_from_file_location("libro_parcial", str(RAIZ / "scripts" / "libro_de_cuentas.py"))
src = open(RAIZ / "scripts" / "libro_de_cuentas.py", encoding="utf-8").read()
corte = src.index("# ══ EL REGISTRO")
ns = {"__file__": str(RAIZ / "scripts" / "libro_de_cuentas.py"), "__name__": "libro_parcial"}
exec(compile(src[:corte].replace("sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=\"utf-8\")", ""), "libro", "exec"), ns)
print("CONTROL POSITIVO: libro_de_cuentas.r_recall_v750_dash() =", ns["r_recall_v750_dash"]())

# filtro horario de _s126_lib contra el de elevacion solar
from auto_audit_weekly import _coords_por_volcan
from referencia_mirova_unificada import cargar_referencia_unificada
coords = _coords_por_volcan()
por_vb, _, _, _ = bp.indexar_referencia(cargar_referencia_unificada(), coords, ("2026-01-01", "2026-12-31"))
c = collections.Counter()
for (vol, b), lista in por_vb.items():
    for dt, f in lista:
        if bp.es_alerta(f["tipo"]) and (f["vrp_mw"] or 0) > 0:
            c[(b, "la tira el filtro 3-9 h" if not (3 <= dt.hour <= 9) else "la conserva")] += 1
print("ALERTAS nocturnas (elevacion solar <= 0) por sensor, frente al filtro horario de _s126_lib:", sorted(c.items()))
