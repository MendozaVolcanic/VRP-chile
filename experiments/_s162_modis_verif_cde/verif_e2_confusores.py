# -*- coding: utf-8 -*-
"""Verificador CDE, E2: la razón port/MIROVA sube con el cenit. ¿Por qué camino? Mismos insumos que razon_por_cenit.py
(lote 39712862945, objetivos_portes.json, alertas MODIS que el port publica, n 89), con tres preguntas que el auditor no
hizo:
 (a) ¿sube el NUMERADOR (VRP del port) o baja el DENOMINADOR (VRP de MIROVA) con el cenit? Spearman de cada uno con z.
 (b) ¿es tiempo disfrazado de cenit? Spearman de la razón con la fecha, y del cenit con la fecha, dentro de Láscar.
 (c) ¿depende de la clase (protegida / bajo 1 MW) o de la plataforma (Terra / Aqua)?
Las dos preguntas del instrumento: (1) si la tendencia fuera del denominador, (a) lo vería; (2) control: la correlación
razón-cenit tiene que reproducir el rho 0,291 (n 89) del auditor con scipy, por otro código.
Denominador: 89 alertas MODIS (2026-03-01 a 2026-10-21 sin el 17 al 20 de octubre) en que el port publica.
Uso: python -I verif_e2_confusores.py --art <run_39712862945> --objetivos <objetivos_portes.json>
"""
import argparse
import glob
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--art", required=True)
ap.add_argument("--objetivos", required=True)
a = ap.parse_args()
obj = {o["id"]: o for o in json.load(open(a.objetivos, encoding="utf-8"))}
res = []
for p in sorted(glob.glob(str(Path(a.art) / "s159-portes-MODIS-*" / "resultados_MODIS_*.json"))):
    res += json.load(open(p, encoding="utf-8"))
filas = []
for r in res:
    if r.get("estado") != "ok":
        continue
    o = obj[r["id"]]
    f = r["port"]["fisica"]
    if o["lab"] == "pos" and o.get("mirova_vrp") and f.get("npix", 0) > 0 and f.get("vrp_mw"):
        z = (r.get("geometria_centro") or {}).get("sensor_zenith", o["z"])
        filas.append({"vol": o["volcan"], "z": z, "zo": o["z"], "port": f["vrp_mw"], "mir": o["mirova_vrp"],
                      "razon": f["vrp_mw"] / o["mirova_vrp"], "t": datetime.strptime(o["hora_utc"], "%Y-%m-%d %H:%M").timestamp(),
                      "prot": bool(o["protegida"]), "sensor": o["sensor"], "npix": f["npix"],
                      "k": (o["pc_vrp"] / o["mirova_vrp"]) if o.get("pub_prod") and o.get("pc_vrp") else None,
                      "n_mirova": len(o["mirova"]), "h": o["hora_utc"]})
print("n:", len(filas), "(auditor: 89)")
z = np.array([f["z"] for f in filas]); zo = np.array([f["zo"] for f in filas])
print(f"cenit de geometria_centro contra o['z'] de la poblacion: max |dif| {np.abs(z - zo).max():.2f} grados")
razon = np.array([f["razon"] for f in filas]); port = np.array([f["port"] for f in filas]); mir = np.array([f["mir"] for f in filas])
t = np.array([f["t"] for f in filas])


def sp(x, y, nombre):
    r, p = stats.spearmanr(x, y)
    print(f"  {nombre:<42} rho {r:+.3f}  p {p:.4f}  n {len(x)}")
    return r


print("\n== control: Spearman razón-cenit con scipy (auditor: rho 0,291, p 0,0054)")
sp(z, razon, "razón port/MIROVA ~ cenit")
print("\n== (a) numerador o denominador")
sp(z, port, "VRP del port ~ cenit")
sp(z, mir, "VRP de MIROVA ~ cenit")
sp(z, np.log(port) - np.log(mir), "log razón ~ cenit (control)")
print("\n== (b) tiempo")
sp(t, razon, "razón ~ fecha")
sp(t, z, "cenit ~ fecha")
sp(t, mir, "VRP MIROVA ~ fecha")
print("\n== (c) estratos")
for nombre, sel in (("Láscar", np.array([f["vol"] == "Lascar" for f in filas])),
                    ("Láscar protegidas", np.array([f["vol"] == "Lascar" and f["prot"] for f in filas])),
                    ("Láscar bajo 1 MW", np.array([f["vol"] == "Lascar" and not f["prot"] for f in filas])),
                    ("Terra", np.array([f["sensor"] == "MODIS_TERRA" for f in filas])),
                    ("Aqua", np.array([f["sensor"] == "MODIS_AQUA" for f in filas]))):
    if sel.sum() >= 6:
        print(f" {nombre} (n {sel.sum()}):")
        sp(z[sel], razon[sel], "   razón ~ cenit")
        sp(z[sel], port[sel], "   VRP port ~ cenit")
        sp(z[sel], mir[sel], "   VRP MIROVA ~ cenit")
        sp(t[sel], razon[sel], "   razón ~ fecha")
        sp(t[sel], z[sel], "   cenit ~ fecha")
# parcial: razón ~ cenit controlando fecha (rangos, regresión lineal de rangos), Láscar
sel = np.array([f["vol"] == "Lascar" for f in filas])
rz, rr, rt = (stats.rankdata(v[sel]) for v in (z, razon, t))
def resid(y, x):
    b = np.polyfit(x, y, 1); return y - np.polyval(b, x)
r_par = stats.pearsonr(resid(rz, rt), resid(rr, rt))
print(f"\n== Spearman parcial razón ~ cenit | fecha, Láscar: rho {r_par[0]:+.3f} p {r_par[1]:.4f} (n {sel.sum()})")
print("\n== pseudorreplicación: pasadas con más de una fila de MIROVA pareada:",
      sum(f["n_mirova"] > 1 for f in filas), "de", len(filas))
print("== npix del port por tramo de cenit (mediana): ",
      {tr: float(np.median([f["npix"] for f in filas if lo <= f["z"] < hi])) for tr, (lo, hi) in
       (("0-25", (0, 25)), ("25-40", (25, 40)), ("40-50", (40, 50)), ("50-90", (50, 90)))})
print("== VRP MIROVA mediana por tramo: ",
      {tr: round(float(np.median([f["mir"] for f in filas if lo <= f["z"] < hi])), 3) for tr, (lo, hi) in
       (("0-25", (0, 25)), ("25-40", (25, 40)), ("40-50", (40, 50)), ("50-90", (50, 90)))})
print("== VRP port mediana por tramo: ",
      {tr: round(float(np.median([f["port"] for f in filas if lo <= f["z"] < hi])), 3) for tr, (lo, hi) in
       (("0-25", (0, 25)), ("25-40", (25, 40)), ("40-50", (40, 50)), ("50-90", (50, 90)))})
