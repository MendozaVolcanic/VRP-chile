# -*- coding: utf-8 -*-
"""Verificador: potencia del control de reproduccion por pixel (223 de 223) y el factor lambda de MODIS."""
import io, json, math, os, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
W = Path("D:/vrp-trabajo/worktrees/s157-magnitud-chillan")
sys.path.insert(0, str(W)); sys.path.insert(0, str(W / "experiments/_s131_audit/magnitud"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from pipeline.constants import C1_PLANCK, C2_PLANCK
from importlib import import_module
fm = import_module("02_correccion_area_por_angulo").f_modelo
d = json.loads((W / "experiments/_s157_magnitud_chillan/a_pasadas_salida.json").read_text(encoding="utf-8"))
recs = {(r["sensor"], r["datetime_utc"]): r for r in json.loads((W / "data/mirova_equivalent/NevadosDeChillan.json").read_text(encoding="utf-8"))["records"]}
def pl(t, lam):
    return C1_PLANCK / (lam ** 5 * (math.exp(C2_PLANCK / (lam * t)) - 1.0))
SEN = {"VIIRS375": (3.74, 18.0, 140625.0), "VIIRS750": (4.05, 19.7, 562500.0), "MODIS": (3.929, 18.9, 1e6)}
from pipeline import process_viirs as pv, process_viirs_mod as pm
print("constantes pipeline: I04", pv.I04_LAMBDA, pv.WOOSTER_COEFF, pv.NADIR_PIXEL_AREA_M2, "| M13", pm.M13_LAMBDA, pm.WOOSTER_COEFF, pm.NADIR_PIXEL_AREA_M2)
SEN["VIIRS375"] = (pv.I04_LAMBDA, pv.WOOSTER_COEFF, pv.NADIR_PIXEL_AREA_M2)
SEN["VIIRS750"] = (pm.M13_LAMBDA, pm.WOOSTER_COEFF, pm.NADIR_PIXEL_AREA_M2)
def vrp(b, bt, tbg, lam=None):
    l, k, A = SEN[b]; l = lam or l
    return k * A * max(pl(bt, l) - pl(tbg, l), 0) / 1e6
stats = {"ok": 0, "n": 0, "maxrel": 0, "modis_n": 0, "modis_ok_b22": 0, "modis_ok_b21": 0, "abs_tol_dominante": 0}
lam_fac = []
for p in d["pasadas"]:
    r = recs[(p["sensor"], p["pasada"])]
    tbg = r["t_bg_k"]
    px = [x for x in r["anomaly_pixels"] if x["dist_km"] is not None and x["dist_km"] <= 5]
    for x in px:
        v = vrp(p["b"], x["bt_k"], tbg)
        tol = max(0.002, 0.005 * x["vrp_mw"])
        stats["n"] += 1; stats["ok"] += abs(v - x["vrp_mw"]) <= tol
        if x["vrp_mw"] > 0:
            stats["maxrel"] = max(stats["maxrel"], abs(v - x["vrp_mw"]) / x["vrp_mw"])
        if 0.002 > 0.005 * x["vrp_mw"]:
            stats["abs_tol_dominante"] += 1
        if p["b"] == "MODIS":
            stats["modis_n"] += 1
            v22 = vrp("MODIS", x["bt_k"], tbg, lam=3.959)
            stats["modis_ok_b22"] += abs(v22 - x["vrp_mw"]) <= tol
            stats["modis_ok_b21"] += abs(v - x["vrp_mw"]) <= tol
    if p["b"] == "MODIS":
        s21 = sum(vrp("MODIS", x["bt_k"], tbg) for x in px)
        s22 = sum(vrp("MODIS", x["bt_k"], tbg, lam=3.959) for x in px)
        lam_fac.append((p["pasada"], round(s22 / s21, 4) if s21 else None, p["f_lambda_modis"], max(x["bt_k"] for x in px)))
print(stats)
print("MODIS factor lambda B22/B21 (mio, fondo y pixel con B22) vs el del script, t_max:")
for row in lam_fac:
    print("  ", row)
# Control de potencia: ¿el control falla si se usa la longitud de onda de B22? ya arriba. ¿y si el area de 750 fuera la de 375?
bad = sum(1 for p in d["pasadas"] if p["b"] == "VIIRS750" for x in recs[(p["sensor"], p["pasada"])]["anomaly_pixels"]
          if x["vrp_mw"] > 0 and abs(pv.WOOSTER_COEFF * pv.NADIR_PIXEL_AREA_M2 * max(pl(x["bt_k"], pm.M13_LAMBDA) - pl(recs[(p["sensor"], p["pasada"])]["t_bg_k"], pm.M13_LAMBDA), 0) / 1e6 - x["vrp_mw"]) <= max(0.002, 0.005 * x["vrp_mw"]))
print("750 con k*A de 375: pixeles que igual pasarian el control:", bad)
# f_modelo en las pasadas sin geometria
for z, G in ((50.52, 0.97), (50.53, 0.81), (62.37, 0.47), (62.38, 0.36), (10.5, 0.88), (37.63, 0.83), (27.79, 0.55), (20.48, 0.64)):
    print("  sin_geometria cenital %.2f f %.2f G %.2f G_area %.2f" % (z, fm(z), G, G * fm(z)))
