# -*- coding: utf-8 -*-
"""VA, hallazgo 5: fondo del anillo de produccion (VIIRS 375) contra el fondo medio por pixel de MIROVA (OSF 2025).

Camino propio: pareo desde el CSV del OSF; fondo nuestro = diag_L_bg_w_m2_sr_um del record (el que se resta), con
control de coherencia contra Planck(t_bg_k, 3,74 um) recalculado aqui. Fondo MIROVA = Tot_Lmir_bk / Npix.
Pregunta 1: si el fondo nuestro fuera igual al de MIROVA la razon daria 1; control positivo: la razon en
temperatura equivalente se imprime junto (un 15 % de radiancia a 3,74 um son pocos K, y eso tiene que verse).
Pregunta 2: n por volcan impreso; volcan sin pares sale n=0.
Ventana: 2025, noche, |dt| <= 10 min, pares con deteccion nuestra y fondo de anillo (diag_L_bg_local nulo).
"""
import glob, json, math, sys
from collections import defaultdict
from datetime import datetime
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from pipeline.process_viirs import C1, C2  # noqa: E402

LAM = 3.74
planck = lambda T: C1 / (LAM ** 5 * (math.exp(C2 / (LAM * T)) - 1))
inv = lambda L: C2 / (LAM * math.log(C1 / (LAM ** 5 * L) + 1))
OSF = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv"
d = pd.read_csv(OSF, encoding="utf-8")
d = d[d.timeUTC.notna() & (d.Dayflag == 0) & (d.Resolution == 375)].copy()
d["t"] = pd.to_datetime(d.timeUTC, format="%d/%m/%Y %H:%M")
d = d[d.t.dt.year == 2025]
NOMB = {"Láscar": "Lascar", "Chaitén": "Chaiten", "Puyehue-Cordón Caulle": "PuyehueCordonCaulle",
        "Chillán, Nevados de": "NevadosDeChillan", "Planchón-Peteroa": "PlanchonPeteroa"}
d["vol"] = d.Volc_Name.map(lambda x: NOMB.get(x, x))
our = defaultdict(list)
for f in glob.glob("data/mirova_equivalent/*.json"):
    j = json.load(open(f, encoding="utf-8"))
    for r in j["records"]:
        if r["datetime_utc"][:4] == "2025" and r["sensor"].startswith("VIIRS") and not r["sensor"].endswith("_750"):
            our[j["volcano"]].append(r)
res = defaultdict(list)
coh = []
for _, o in d.iterrows():
    c = [r for r in our.get(o.vol, []) if abs((datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M") - o.t.to_pydatetime()).total_seconds()) <= 600]
    if len(c) != 1:
        continue
    r = c[0]
    if not r.get("n_anomalous_pixels") or r.get("diag_L_bg_w_m2_sr_um") is None:
        continue
    fuente = "local" if r.get("diag_L_bg_local_w_m2_sr_um") is not None else "anillo"
    Lo = r["diag_L_bg_w_m2_sr_um"]
    coh.append(Lo / planck(r["t_bg_k"]))
    if fuente == "local":  # el que se resta es el local; el del anillo se informa aparte
        res[(o.vol, "anillo(no se resta)")].append((Lo / (o.Tot_Lmir_bk / o.Npix), inv(Lo) - inv(o.Tot_Lmir_bk / o.Npix)))
        Lo = r["diag_L_bg_local_w_m2_sr_um"]
    bkM = o.Tot_Lmir_bk / o.Npix
    res[(o.vol, fuente)].append((Lo / bkM, inv(Lo) - inv(bkM)))
print("coherencia diag_L_bg / Planck(t_bg): n=%d mediana=%.4f min=%.4f max=%.4f" % (len(coh), np.median(coh), min(coh), max(coh)))
print("volcan, fuente del fondo: n, mediana razon L_bg_nuestro/bk_MIROVA (p25, p75), mediana dif. en K equivalente")
for k in sorted(res):
    v = np.array(res[k])
    print("  %-22s %-6s n=%4d  razon %.3f (%.3f, %.3f)  dT %.2f K" % (k[0], k[1], len(v), np.median(v[:, 0]),
          np.percentile(v[:, 0], 25), np.percentile(v[:, 0], 75), np.median(v[:, 1])))
