# -*- coding: utf-8 -*-
"""S126 — helpers compartidos para leer los A/B. Escrito ANTES de que terminen (A16).

Concentra las decisiones metodologicas que se repiten en todos los veredictos y que,
cuando se re-escriben a mano en cada script, es donde aparecen los errores:

  · emparejar sobre la INTERSECCION de pasadas (datetime_utc + sensor), nunca sobre
    conteos de series sueltas;
  · un par por NOCHE, maximo de los dos lados — comparar cada pasada contra el maximo
    de MIROVA de la noche infla el objetivo cuando hay 2-3 pasadas (costo medido en
    S126: un deficit exagerado 2,5x);
  · ground truth CONS union OCR con el diccionario de alias COMPLETO (A11/A14), y del
    snapshot VIVO, no de la copia congelada (S126);
  · descartar las alertas DIURNAS de MIROVA — son artefacto de reflexion solar (A76) y
    el pipeline es night-only, asi que contarlas seria contar como fallo algo que
    hacemos bien;
  · pc.vrp_mw, NUNCA record.vrp_mw (A10);
  · desagregar POR VOLCAN antes de mirar cualquier agregado (leccion central de S126:
    la mediana agrupada invirtio el veredicto del brazo E).
"""
import csv
import json
import math
import os
import random
import statistics as st
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Coordenadas del crater (vent) por volcan — para el eje espacial (A61).
VENTS = {
    "Villarrica": (-39.420227, -71.939876),
    "PlanchonPeteroa": (-35.241099, -70.573345),
    "Lascar": (-23.362930, -67.731416),
    "PuyehueCordonCaulle": (-40.525499, -72.146137),
    "NevadosDeChillan": (-36.868000, -71.378000),
    "Copahue": (-37.856000, -71.183000),
    "Llaima": (-38.692000, -71.729000),
    "Lastarria": (-25.168000, -68.507000),
    "Isluga": (-19.150000, -68.833000),
    "Chaiten": (-42.833000, -72.646000),
    "Tupungatito": (-33.400000, -69.800000),
}

# A14: el scraper normaliza algunos nombres. Buscar con una sola variante pierde datos
# en silencio (S60 perdio 46 alertas de PP por buscar "Planchon-Peteroa").
ALIAS = {
    "Villarrica": {"Villarrica"},
    "PlanchonPeteroa": {"PlanchonPeteroa", "Planchon-Peteroa", "Planchon Peteroa"},
    "Lascar": {"Lascar", "Láscar"},
    "PuyehueCordonCaulle": {"PuyehueCordonCaulle", "Puyehue-Cordon Caulle",
                            "Puyehue Cordon Caulle", "Puyehue-Cordón Caulle"},
    "NevadosDeChillan": {"NevadosDeChillan", "Nevados de Chillan", "Nevados de Chillán"},
    "Copahue": {"Copahue"},
    "Llaima": {"Llaima"},
    "Lastarria": {"Lastarria"},
    "Isluga": {"Isluga"},
    "Chaiten": {"Chaiten", "Chaitén"},
    "Tupungatito": {"Tupungatito"},
}

SENSOR_MAP = {"VIIRS375": "v375", "VIIRS": "v750", "MODIS": "modis"}
BANDA = (0.7, 1.4)

# Canal OCR VIVO. La copia de data/mirova_reference/registro_vrp_ocr.csv quedo
# congelada el 2026-03-28 y nadie la refresca (ver el LEEME de ese directorio).
FUENTES_GT = ("latest_consolidado.csv",
              "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv")


def bucket(sensor):
    """Sensor del record -> bucket comparable con MIROVA.

    Convencion del proyecto (A48): VIIRS_SNPP / VIIRS_NOAA20 / VIIRS_NOAA21 SIN sufijo
    son I-band 375 m; el sufijo _750 marca M-band. Un regex ingenuo tipo `"375" in s`
    clasifica mal nuestros I-band y da conclusiones falsas.
    """
    s = (sensor or "").upper()
    if "MODIS" in s:
        return "modis"
    if "750" in s:
        return "v750"
    if "VIIRS" in s:
        return "v375"
    return None


def haversine(a, b):
    (la1, lo1), (la2, lo2) = a, b
    p = math.pi / 180.0
    h = (math.sin((la2 - la1) * p / 2) ** 2 +
         math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def resumen(xs, dec=3):
    if not xs:
        return None
    xs = sorted(xs)
    return {"n": len(xs), "mediana": round(st.median(xs), dec),
            "p25": round(xs[len(xs) // 4], dec), "p75": round(xs[3 * len(xs) // 4], dec),
            "min": round(xs[0], dec), "max": round(xs[-1], dec)}


def ic95(xs, n=4000, seed=20260829):
    """IC bootstrap de la mediana (T8). Determinista: misma semilla, mismo resultado."""
    if len(xs) < 3:
        return [None, None]
    rnd = random.Random(seed)
    meds = sorted(st.median([xs[rnd.randrange(len(xs))] for _ in range(len(xs))])
                  for _ in range(n))
    return [round(meds[int(0.025 * n)], 3), round(meds[int(0.975 * n)], 3)]


def cargar_mirova(ventana, solo_nocturnas=True):
    """{volcan: {(fecha, bucket): vrp_mw}} de las ALERTAS de MIROVA en la ventana."""
    out = defaultdict(dict)
    diurnas = 0
    for fname in FUENTES_GT:
        path = os.path.join(ROOT, fname)
        if not os.path.exists(path):
            continue
        for r in csv.DictReader(open(path, encoding="utf-8", errors="replace")):
            nom = (r.get("Volcan") or "").strip()
            vol = next((v for v, al in ALIAS.items() if nom in al), None)
            if vol is None or "ALERTA" not in (r.get("Tipo_Registro") or ""):
                continue
            b = SENSOR_MAP.get((r.get("Sensor") or "").strip().upper())
            fecha = (r.get("Fecha_Satelite_UTC") or "")
            if not b or not (ventana[0] <= fecha[:10] <= ventana[1]):
                continue
            try:
                v = float(r.get("VRP_MW") or 0)
            except ValueError:
                continue
            if v <= 0:
                continue
            if solo_nocturnas and not (3 <= int(fecha[11:13] or 12) <= 9):
                diurnas += 1        # A76: artefacto de reflexion solar
                continue
            k = (fecha[:10], b)
            out[vol][k] = max(out[vol].get(k, 0), v)
    return out, diurnas


def cargar_brazo(subdir, vol, ventana, solo_nocturnas=True):
    """{(datetime_utc, sensor): record} del brazo. None si el archivo no existe."""
    p = os.path.join(ROOT, "data", subdir, vol + ".json")
    if not os.path.exists(p):
        return None
    out = {}
    for r in json.load(open(p, encoding="utf-8"))["records"]:
        if bucket(r.get("sensor")) is None:
            continue
        if not (ventana[0] <= r["datetime_utc"][:10] <= ventana[1]):
            continue
        if solo_nocturnas:
            sz = r.get("solar_zenith_deg")
            if sz is not None and sz < 90:
                continue
        out[(r["datetime_utc"], r.get("sensor"))] = r
    return out


def interseccion(brazos_por_vol):
    """Pasadas presentes en TODOS los brazos. Sin esto, un brazo con mas pasadas
    parece 'detectar mas' cuando lo unico que pasa es que proceso mas granulos."""
    sets = [set(d) for d in brazos_por_vol if d is not None]
    return set.intersection(*sets) if sets else set()


def pares_por_noche(recs, pasadas, mirova_vol, buck="v375"):
    """[(fecha, vrp_nuestro, vrp_mirova)] — un par por noche, maximo de ambos lados."""
    mejor = {}
    for k in pasadas:
        if bucket(k[1]) != buck:
            continue
        v = (recs[k].get("primary_cluster") or {}).get("vrp_mw") or 0
        f = k[0][:10]
        if v > mejor.get(f, 0):
            mejor[f] = v
    out = []
    for (f, b), vm in (mirova_vol or {}).items():
        if b != buck or f not in mejor or not mejor[f]:
            continue
        out.append((f, mejor[f], vm))
    return sorted(out)


def en_banda(ratio):
    return ratio is not None and BANDA[0] <= ratio <= BANDA[1]


def marca(ok):
    return "CUMPLE" if ok else "NO CUMPLE"
