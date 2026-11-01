# -*- coding: utf-8 -*-
"""F1 (S158): los records de VIIRS 750 que nuestro detector vio en la cumbre y el tablero esconde porque el fondo del
anillo deja todos sus píxeles en 0 MW, cruzados con la tabla de MIROVA (latest_consolidado.csv, Sensor == 'VIIRS').

Ventana: 2026-09-18 (datos con K) al último record. Calidad de la referencia (A119): la etiqueta que decide desde
2026-03 es la de la tabla; acá se usa SOLO la tabla (Tipo_Registro), sin OCR. Pareo: misma pasada si
|Fecha_Satelite_UTC - datetime_utc| <= 20 min (los VIIRS de un mismo volcán están separados por ~50 min o más).

Instrumento 1: si MIROVA no hubiera mirado esas pasadas, el pareo daría 'sin fila' y se cuenta aparte (SIN DATO).
Instrumento 2 (control positivo): los publicados por nosotros deben parear en su mayoría con filas de la tabla.
También: razón publicado / VRP de MIROVA en pares ALERTA_TERMICA de VIIRS 750 (lo neto de todas las diferencias).
Uso: python -B experiments/_s158_audit/f1/cruce_referencia.py
"""
import io, json, math, os, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np, pandas as pd, yaml

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, RAIZ)
import scripts.calidad_referencia_mirova as calidad
VOLS = ["Isluga", "Lascar", "Lastarria", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Copahue",
        "Llaima", "Villarrica", "PuyehueCordonCaulle", "Chaiten"]
ALIAS = {"PlanchonPeteroa": ["PlanchonPeteroa", "Planchon-Peteroa"], "PuyehueCordonCaulle": ["Puyehue-Cordon Caulle", "PuyehueCordonCaulle"],
         "NevadosDeChillan": ["Nevados de Chillan", "NevadosDeChillan"]}
DESDE = sys.argv[1] if len(sys.argv) > 1 else "2026-09-18"
for a in calidad.avisos_de_ventana(DESDE, "2026-10-21"):
    print("AVISO referencia:", a)
C1, C2 = 1.191042e8, 14388.0
planck = lambda T: C1 / (4.05 ** 5 * (math.exp(C2 / (4.05 * T)) - 1))
cfg = {x["name"]: x for x in yaml.safe_load(open(os.path.join(RAIZ, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}
pub = {(p["v"], p["t"], p["s"]): p for p in json.load(open(os.path.join(AQUI, "pub_v750.json"), encoding="utf-8"))}

ref = pd.read_csv(os.path.join(RAIZ, "latest_consolidado.csv"))
ref = ref[ref["Sensor"] == "VIIRS"].copy()
ref["t"] = pd.to_datetime(ref["Fecha_Satelite_UTC"])
ref = ref[ref["t"] >= DESDE]
nombre_ref = {}
for v in VOLS:
    for a in ALIAS.get(v, [v]):
        nombre_ref[a] = v
ref["vol"] = ref["Volcan"].map(nombre_ref)
print("filas de la tabla VIIRS 750 en ventana:", len(ref), " sin volcán mapeado:", int(ref["vol"].isna().sum()),
      " tipos:", dict(ref["Tipo_Registro"].value_counts()))
porvol = {v: g.sort_values("t") for v, g in ref.groupby("vol")}


def parear(v, t):
    g = porvol.get(v)
    if g is None or g.empty:
        return None
    dt = (g["t"] - t).abs()
    i = dt.idxmin()
    return g.loc[i] if dt.loc[i] <= timedelta(minutes=20) else None


c = Counter(); detalle = []; pares = []; cpub = Counter(); porv = defaultdict(Counter)
for v in VOLS:
    d = json.load(open(os.path.join(RAIZ, "data", "mirova_equivalent", v + ".json"), encoding="utf-8"))
    cf = cfg[v]; vlat, vlon = cf.get("vent_lat", cf["lat"]), cf.get("vent_lon", cf["lon"])
    for r in d["records"]:
        if not str(r.get("sensor", "")).endswith("_750") or r["datetime_utc"] < DESDE:
            continue
        p = pub[(v, r["datetime_utc"], r["sensor"])]
        t = pd.Timestamp(r["datetime_utc"])
        fila = parear(v, t)
        tipo = None if fila is None else fila["Tipo_Registro"]
        if p["pub"] > 0:
            cpub[tipo] += 1
            if tipo == "ALERTA_TERMICA" and float(fila["VRP_MW"]) > 0:
                pares.append((v, p["pub"], float(fila["VRP_MW"])))
        inner = [q for q in (r.get("anomaly_pixels") or [])
                 if math.hypot((q["lat"] - vlat) * 111.32, (q["lon"] - vlon) * 111.32 * math.cos(math.radians(vlat))) <= cf["inner_radius_km"]]
        if inner and all((q.get("vrp_mw") or 0) == 0 for q in inner) and p["pub"] <= 0:
            c[tipo] += 1; porv[v][tipo] += 1
            detalle.append((v, r["datetime_utc"], r["sensor"], r["t_bg_k"], [q["bt_k"] for q in inner],
                            tipo, None if fila is None else float(fila["VRP_MW"]),
                            None if fila is None else fila["Distancia_km"]))
        if tipo == "ALERTA_TERMICA" and p["pub"] <= 0:
            porv[v]["MIROVA_alerta_y_nosotros_no"] += 1
            porv[v]["MIROVA_alerta_y_nosotros_no__con_px_inner_todo_0"] += bool(inner and all((q.get("vrp_mw") or 0) == 0 for q in inner))
            porv[v]["MIROVA_alerta_y_nosotros_no__sin_px_inner"] += (not inner)
        if tipo == "ALERTA_TERMICA":
            porv[v]["MIROVA_alerta"] += 1
print("\nCONTROL positivo: nuestros publicados según el tipo de la fila pareada de MIROVA:", dict(cpub))
print("\nDetectados en la cumbre con TODOS sus píxeles en 0 MW por el fondo del anillo, NO publicados, por tipo MIROVA:", dict(c))
for x in detalle:
    print("  ", x[0], x[1], x[2], "t_bg", x[3], "BT píxeles inner", x[4], "| MIROVA:", x[5], x[6], "MW", x[7], "km")
print("\nPor volcán:")
for v in VOLS:
    if porv[v]:
        print("  ", v, dict(porv[v]))
if pares:
    rz = np.array([a / b for _, a, b in pares])
    print(f"\nRazón publicado / VRP MIROVA en pasadas ALERTA_TERMICA de VIIRS 750 que ambos publican: n={len(rz)}, "
          f"percentiles 10/50/90 = {np.round(np.percentile(rz, [10, 50, 90]), 3)}")
    for v in VOLS:
        x = [a / b for vv, a, b in pares if vv == v]
        if x:
            print(f"   {v:20s} n={len(x):3d} mediana {np.median(x):.3f}")
