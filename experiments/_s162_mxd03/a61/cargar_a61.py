# -*- coding: utf-8 -*-
"""Cargador comun de la auditoria A61 (S162, MxD03): artefactos de las tres tandas, poblacion sellada, referencia
congelada de MIROVA (con comprobacion de sha256 contra el MANIFIESTO) y la tabla VIIRS de la vara.

No importa el evaluador del autor: lee los jsonl y los CSV por su cuenta (A48, A110).
"""
import csv
import glob
import hashlib
import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
EXP = RAIZ / "experiments" / "_s162_mxd03"
ART = Path(r"D:\vrp-trabajo\temporales\s162_mxd03\tandas")
REF = Path(r"D:\vrp-trabajo\temporales\s162_mxd03\ref")
NULOS = ["R%02d" % k for k in range(20)]
TOL_S = 120
ALIAS = {"Nevados de Chillan": "NevadosDeChillan", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle",
         "Planchon-Peteroa": "PlanchonPeteroa", "PlanchonPeteroa": "PlanchonPeteroa", "Lascar": "Lascar",
         "Villarrica": "Villarrica", "Chaiten": "Chaiten", "Lastarria": "Lastarria", "Isluga": "Isluga",
         "Tupungatito": "Tupungatito", "Llaima": "Llaima", "Copahue": "Copahue"}


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def rumbo(lat1, lon1, lat2, lon2):
    """Acimut geografico (grados desde el norte, hacia el este) de 1 a 2."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return math.degrees(math.atan2(y, x)) % 360.0


def ne_km(lat0, lon0, lat, lon):
    """(norte, este) en km de (lat, lon) respecto de (lat0, lon0); misma formula plana del arnes."""
    return (lat - lat0) * 111.32, (lon - lon0) * 111.32 * math.cos(math.radians((lat + lat0) / 2))


def punto_cardinal(az):
    return ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int(((az + 22.5) % 360) // 45)]


def sha256_lf(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def cargar_artefactos(art=ART):
    """Records `ok` de los jsonl de las tres tandas; devuelve (records, cabeceras, pies)."""
    ok, cab, pies = [], [], []
    for p in sorted(glob.glob(str(Path(art) / "**" / "ab_parte*.jsonl"), recursive=True)):
        for l in open(p, encoding="utf-8"):
            r = json.loads(l)
            t = r.get("tipo")
            if t == "cabecera":
                cab.append(r)
            elif t == "pie":
                pies.append(r)
            elif t == "record":
                if r.get("estado") == "ok":
                    ok.append(r)
                else:
                    raise RuntimeError("record no ok: %s %s %s" % (r.get("vol"), r.get("dt"), r.get("estado")))
    return ok, cab, pies


def cargar_poblacion():
    pob = json.load(open(EXP / "poblacion.json", encoding="utf-8"))
    filas = {(f["vol"], f["dt"]): f for g in pob["granulos"] for f in g["records"]}
    return pob, filas


def cargar_referencia(pob):
    """Filas MODIS de la referencia congelada (consolidado + OCR), con comprobacion de sha256 contra la poblacion."""
    man = pob["referencia"]
    filas = []
    for nombre, src in (("registro_vrp_consolidado.csv", "CONS"), ("registro_vrp_ocr.csv", "OCR")):
        p = REF / nombre
        h = sha256_lf(p)
        if h != man[nombre]["sha256_lf"]:
            sys.exit("%s: sha256 %s distinto del sellado %s" % (nombre, h, man[nombre]["sha256_lf"]))
        with open(p, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                if r.get("Sensor") != "MODIS":
                    continue
                vol = ALIAS.get(r["Volcan"])
                if vol is None:
                    continue
                try:
                    dt = datetime.strptime(r["Fecha_Satelite_UTC"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
                def _f(v):
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        return None
                filas.append({"vol": vol, "dt": dt, "tipo": r.get("Tipo_Registro", ""), "vrp": _f(r.get("VRP_MW")),
                              "dist": _f(r.get("Distancia_km")), "clase": r.get("Clasificacion Mirova"), "src": src,
                              "sha": h[:8]})
    filas.sort(key=lambda f: f["dt"])
    return filas


def parear(filas, vol, dt_str, tol=TOL_S):
    t = datetime.strptime(dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return [f for f in filas if f["vol"] == vol and abs((f["dt"] - t).total_seconds()) <= tol]


def cargar_vara():
    v = json.load(open(EXP / "vara_viirs_mxd03.json", encoding="utf-8"))
    return v["granulos"], v["meta"]
