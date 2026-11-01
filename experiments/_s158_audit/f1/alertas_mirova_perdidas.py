# -*- coding: utf-8 -*-
"""F1 (S158): cada ALERTA_TERMICA de VIIRS 750 de la tabla de MIROVA, clasificada por lo que hizo nuestro detector.

Recorre desde el lado de MIROVA (no desde nuestros records), así cuenta también las pasadas en que no tenemos record.
Clases, en orden: sin_record (no hay record nuestro a <= 20 min), publicada (pub > 0 en el tablero, node),
cumbre_en_cero (hay píxel detectado dentro del inner y todos valen 0 MW por el fondo del anillo y el recorte),
solo_fuera_inner (hay píxeles pero ninguno dentro del inner), sin_deteccion (n_anomalous_pixels == 0), otra.
Instrumento 1: si el pareo no funcionara, todo caería en sin_record; si el predicado no corriera, nada en publicada.
Instrumento 2: las clases son exhaustivas y se imprime la suma contra el total.
Uso: python -B experiments/_s158_audit/f1/alertas_mirova_perdidas.py [desde]
"""
import io, json, math, os, sys
from collections import Counter, defaultdict
from datetime import timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pandas as pd, yaml, numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, RAIZ)
import scripts.calidad_referencia_mirova as calidad
DESDE = sys.argv[1] if len(sys.argv) > 1 else "2026-09-18"
HASTA = "2026-10-21"
VOLS = ["Isluga", "Lascar", "Lastarria", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Copahue",
        "Llaima", "Villarrica", "PuyehueCordonCaulle", "Chaiten"]
ALIAS = {"Planchon-Peteroa": "PlanchonPeteroa", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle",
         "Nevados de Chillan": "NevadosDeChillan"}
for a in calidad.avisos_de_ventana(DESDE, HASTA):
    print("AVISO referencia:", a[:160])
cfg = {x["name"]: x for x in yaml.safe_load(open(os.path.join(RAIZ, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}
pub = {(p["v"], p["t"], p["s"]): p for p in json.load(open(os.path.join(AQUI, "pub_v750.json"), encoding="utf-8"))}
ours = defaultdict(list)
for v in VOLS:
    for r in json.load(open(os.path.join(RAIZ, "data", "mirova_equivalent", v + ".json"), encoding="utf-8"))["records"]:
        if str(r.get("sensor", "")).endswith("_750") and r["datetime_utc"] >= DESDE:
            ours[v].append((pd.Timestamp(r["datetime_utc"]), r))
ref = pd.read_csv(os.path.join(RAIZ, "latest_consolidado.csv"))
ref = ref[(ref["Sensor"] == "VIIRS") & (ref["Tipo_Registro"] == "ALERTA_TERMICA")].copy()
ref["t"] = pd.to_datetime(ref["Fecha_Satelite_UTC"])
ref = ref[(ref["t"] >= DESDE)]
ref["vol"] = ref["Volcan"].map(lambda x: ALIAS.get(x, x))
ref = ref[ref["vol"].isin(VOLS)]
print("ALERTA_TERMICA VIIRS 750 de la tabla en ventana %s a %s: %d" % (DESDE, HASTA, len(ref)))
c = Counter(); porv = defaultdict(Counter); mw = defaultdict(list)
for _, f in ref.iterrows():
    v = f["vol"]; cf = cfg[v]
    vlat, vlon = cf.get("vent_lat", cf["lat"]), cf.get("vent_lon", cf["lon"])
    cand = [(abs(t - f["t"]), r) for t, r in ours[v]]
    cand = [x for x in cand if x[0] <= timedelta(minutes=20)]
    if not cand:
        k = "sin_record"
    else:
        r = min(cand, key=lambda x: x[0])[1]
        p = pub[(v, r["datetime_utc"], r["sensor"])]
        inner = [q for q in (r.get("anomaly_pixels") or [])
                 if math.hypot((q["lat"] - vlat) * 111.32, (q["lon"] - vlon) * 111.32 * math.cos(math.radians(vlat))) <= cf["inner_radius_km"]]
        if p["pub"] > 0:
            k = "publicada"
        elif inner and all((q.get("vrp_mw") or 0) == 0 for q in inner):
            k = "cumbre_en_cero"
        elif (r.get("n_anomalous_pixels") or 0) == 0:
            k = "sin_deteccion"
        elif not inner:
            k = "solo_fuera_inner"
        else:
            k = "otra"
    c[k] += 1; porv[v][k] += 1; mw[k].append(float(f["VRP_MW"]))
print("clases:", dict(c), " suma", sum(c.values()), "de", len(ref))
for k, x in mw.items():
    print(f"   {k:18s} VRP MIROVA mediana {np.median(x):.3f} MW, máx {max(x):.2f}, >= 1 MW: {sum(1 for y in x if y >= 1)}")
for v in VOLS:
    if porv[v]:
        print("  ", v, dict(porv[v]))
