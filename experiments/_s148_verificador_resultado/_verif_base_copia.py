# -*- coding: utf-8 -*-
"""Verificador S148, modulo base INDEPENDIENTE: no importa nada del repo.

Carga los dos brazos, la referencia congelada, etiqueta por pasada y decide "publica" con un
port propio a Python del predicado de frontend/index.html (se contrasta aparte contra node, v2).
"""
import csv
import json
import math
import collections
from datetime import datetime
from pathlib import Path

VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
# inner_radius_km de la tabla S14 del CLAUDE.md del proyecto, NO leido del html
INNER = {"Lastarria": 3, "PlanchonPeteroa": 3, "Copahue": 4, "Tupungatito": 7,
         "PuyehueCordonCaulle": 20, "Lascar": 5, "Isluga": 5, "NevadosDeChillan": 5,
         "Llaima": 5, "Villarrica": 5, "Chaiten": 5}
NOMBRES = {"puyehue-cordon caulle": "PuyehueCordonCaulle", "nevados de chillan": "NevadosDeChillan",
           "planchonpeteroa": "PlanchonPeteroa", "planchon-peteroa": "PlanchonPeteroa"}
B, F = "_s146_ab_sin_test1", "_s147_ab_sin_test1_max"


def cubo(s):
    s = s or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None


def hav(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(x))


# ---- port propio del predicado del tablero (index.html l.1043-1240 y 1466-1487), USE_F5_CORE=true
def eq_vrp(r, inner):
    pc = r.get("primary_cluster")
    if not pc:
        v = r.get("vrp_mw")
        if v is None:
            v = r.get("vrp_mir_mw")
        v = v or 0
        return 0 if v > 50000 else v
    dc = r.get("distance_class")
    if dc and dc != "summit":
        return 0
    d = pc.get("centroid_dist_km")
    if d is not None and d > inner:
        return 0
    v = pc.get("vrp_mw") or 0
    return 0 if v > 50000 else v


def eq_core(r, inner):
    base = eq_vrp(r, inner)
    if base <= 0:
        return base
    s = (r.get("sensor") or "").upper()
    if not (s.startswith("VIIRS") and not s.endswith("_750")):
        return base
    core = r.get("f5_core_vrp_mw")
    if not isinstance(core, (int, float)):
        core = None  # el respaldo JS por pixeles no se porta; v1 cuenta cuantos records caen aca
    if core is None or core <= 0:
        return base
    return 0 if core > 50000 else core


def publica(r, inner):
    pc = r.get("primary_cluster")
    if pc:
        valid = (pc.get("vrp_mw") or 0) > 0
    else:
        valid = (r.get("vrp_mw") or 0) > 0 or r.get("triggered_test1") is True
    if (r.get("vrp_mw") or 0) == 0 and r.get("discarded_reason") and not r.get("triggered_test1"):
        summit = False
    elif r.get("distance_class") == "summit":
        summit = True
    elif r.get("distance_class") == "far":
        summit = False
    else:
        summit = (r.get("vrp_vent_mw") or 0) > 0
    tmax = r.get("t_max_k")
    e = eq_vrp(r, inner)
    cirrus = tmax is not None and tmax < 273.15 and e > 10
    npx = (pc or {}).get("n_pixels") or 0
    dif = bool(pc) and tmax is not None and tmax < 278.15 and npx >= 100 and e >= 50 and e / npx < 1.0
    disp = eq_core(r, inner)
    return int(bool(summit and valid and not (cirrus or dif) and disp > 0)), disp


def cargar_brazo(d):
    out = {}
    dup = 0
    for v in VOLS:
        p = Path(d) / (v + ".json")
        if not p.exists():
            continue
        for r in json.loads(p.read_text(encoding="utf-8"))["records"]:
            b = cubo(r.get("sensor"))
            if not b:
                continue
            k = (v, b, r["datetime_utc"])
            if k in out:
                dup += 1
            r["_pub"], r["_disp"] = publica(r, INNER[v])
            out[k] = r
    return out, dup


def cargar_ref(dirc):
    filas = []
    for nombre, src in (("registro_vrp_consolidado.csv", "CONS"), ("registro_vrp_ocr.csv", "OCR")):
        with open(Path(dirc) / nombre, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                vol = (r["Volcan"] or "").strip()
                vol = NOMBRES.get(vol.lower(), vol)
                if vol not in VOLS:
                    continue
                s = r["Sensor"].upper()
                b = "MODIS" if "MODIS" in s else ("VIIRS375" if "375" in s else "VIIRS750")
                try:
                    dt = datetime.strptime(r["Fecha_Satelite_UTC"][:19], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
                try:
                    vrp = float(r["VRP_MW"])
                except ValueError:
                    vrp = None
                filas.append({"vol": vol, "b": b, "dt": dt, "tipo": r["Tipo_Registro"].strip(),
                              "src": src, "vrp": vrp})
    return filas


def etiquetar(recs, filas, ini, fin, solo_nocturnas=True):
    """pos / far_ref / neg / sin_info por pasada. Regla del spec escrita de nuevo."""
    por = collections.defaultdict(list)
    noche = collections.defaultdict(set)
    for f in filas:
        if not (ini <= f["dt"].strftime("%Y-%m-%d") <= fin):
            continue
        # criterio propio y tosco de nocturna para VIIRS: hora UTC 00 a 10 (noche local en Chile)
        if solo_nocturnas and f["b"] != "MODIS" and not (0 <= f["dt"].hour <= 10):
            continue
        por[(f["vol"], f["b"])].append(f)
        t = "A" if f["tipo"].startswith("ALERTA") else ("P" if f["tipo"].startswith("FALSO_POSITIVO") else None)
        if t:
            noche[(f["vol"], f["b"], f["dt"].strftime("%Y-%m-%d"))].add(t)
    lab = {}
    for k, r in recs.items():
        v, b, d = k
        if not (ini <= d[:10] <= fin):
            continue
        sz = r.get("solar_zenith_deg")
        if sz is None or sz <= 90:
            continue  # solo pasadas nocturnas, con el dato del propio record
        t = datetime.strptime(d, "%Y-%m-%d %H:%M")
        fs = [f for f in por.get((v, b), []) if abs((f["dt"] - t).total_seconds()) <= 120]
        if any(f["tipo"].startswith("ALERTA") for f in fs):
            lab[k] = "pos"
        elif any(f["tipo"].startswith("FALSO_POSITIVO") for f in fs):
            lab[k] = "far_ref"
        elif (any(f["tipo"] == "RUTINA" and f["src"] == "CONS" and (f["vrp"] or 0) == 0 for f in fs)
              and not noche.get((v, b, d[:10]))):
            lab[k] = "neg"
        else:
            lab[k] = "sin_info"
    return lab, por


def zona(z):
    return "nadir" if z < 36 else ("medio" if z < 52 else "borde")
