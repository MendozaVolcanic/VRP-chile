# -*- coding: utf-8 -*-
"""VA, hallazgo 4: la caida de la razon de magnitud con el cenit, quien la mueve (nuestro conteo o el Npix de MIROVA).

Camino propio: pareo hecho aqui desde el CSV del OSF v2.5 (no pares_osf.csv de RA2) contra data/mirova_equivalent.
Pregunta 1: si el conteo nuestro no cayera con el cenit, la Spearman n_ours-cenit daria ~0; si el Npix de MIROVA
subiera o bajara, su Spearman lo mostraria. Pregunta 2 (instrumento muerto): control de pareo, Spearman entre el
SatZen del OSF y el sensor_zenith_deg nuestro, tiene que dar ~1; y se imprime n de cada estrato.
Ventana: 2025 (cobertura OSF), noche (Dayflag 0), |dt| <= 10 min, misma familia (Resolution 375/750/1000).
Ademas, sin pareo: Npix del OSF contra SatZen en TODAS las filas nocturnas chilenas 2001-2025 (MIROVA sola).
"""
import glob, json, sys
from collections import defaultdict
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.stdout.reconfigure(encoding="utf-8")
OSF = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv"
d = pd.read_csv(OSF, encoding="utf-8")
print("filas OSF:", len(d), "sin timeUTC (descartadas):", int(d.timeUTC.isna().sum()))
d = d[d.timeUTC.notna()].copy()
# formato de fecha: comprobar si el primer campo pasa de 12 (dia) o el segundo (mes)
a = d.timeUTC.str.slice(0, 2).astype(int).max(); b = d.timeUTC.str.slice(3, 5).astype(int).max()
print("max primer campo", a, "max segundo campo", b)
fmt = "%d/%m/%Y %H:%M" if a > 12 else "%m/%d/%Y %H:%M"
d["t"] = pd.to_datetime(d.timeUTC, format=fmt)
NOMB = {"Lascar": "Láscar", "Chaiten": "Chaitén", "PuyehueCordonCaulle": "Puyehue-Cordón Caulle",
        "NevadosDeChillan": "Chillán, Nevados de", "PlanchonPeteroa": "Planchón-Peteroa"}
nuestros = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Copahue",
            "Llaima", "Villarrica", "PuyehueCordonCaulle", "Chaiten"]
osfn = {NOMB.get(v, v): v for v in nuestros}
print("nombres OSF encontrados:", sorted(set(d.Volc_Name) & set(osfn)))
cl = d[d.Volc_Name.isin(osfn) & (d.Dayflag == 0)].copy()
cl["vol"] = cl.Volc_Name.map(osfn)
print("filas OSF nocturnas chilenas:", len(cl), cl.Resolution.value_counts().to_dict(), "anios", cl.t.dt.year.min(), cl.t.dt.year.max())
print("\nMIROVA sola (todas las filas nocturnas chilenas): Spearman Npix-SatZen y mediana Npix por tramo")
for res, g in cl.groupby("Resolution"):
    rho = spearmanr(g.SatZen, g.Npix).correlation
    tr = pd.cut(g.SatZen, [0, 20, 30, 40, 50, 60, 75])
    print("  res %4d n=%6d rho=%+.3f  medianas %s  medias %s" % (res, len(g), rho,
          g.groupby(tr, observed=True).Npix.median().round(1).to_dict(), g.groupby(tr, observed=True).Npix.mean().round(2).to_dict()))

fam = {375: lambda s: not s.endswith("_750") and s.startswith("VIIRS"), 750: lambda s: s.endswith("_750"),
       1000: lambda s: s.startswith("MODIS")}
our = defaultdict(list)
for f in glob.glob("data/mirova_equivalent/*.json"):
    j = json.load(open(f, encoding="utf-8"))
    if j["volcano"] not in nuestros:
        continue
    for r in j["records"]:
        if r["datetime_utc"][:4] != "2025":
            continue
        our[j["volcano"]].append(r)
c25 = cl[cl.t.dt.year == 2025]
rows = []
for _, o in c25.iterrows():
    cands = [r for r in our[o.vol] if fam[o.Resolution](r["sensor"])
             and abs((datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M") - o.t.to_pydatetime()).total_seconds()) <= 600]
    if len(cands) != 1:
        continue
    r = cands[0]
    rows.append(dict(res=o.Resolution, vol=o.vol, npix=o.Npix, zosf=o.SatZen, z=r.get("sensor_zenith_deg"),
                     n=r.get("n_anomalous_pixels") or 0, pcn=(r.get("primary_cluster") or {}).get("n_pixels") or 0))
p = pd.DataFrame(rows)
print("\npares 2025 nocturnos con un unico record nuestro a <=10 min:", len(p), p.res.value_counts().to_dict())
for res, g in p.groupby("res"):
    g = g.dropna(subset=["z"])
    ctrl = spearmanr(g.zosf, g.z).correlation
    det = g[g.n > 0]
    print("  res %4d n=%d (con deteccion nuestra %d) | CONTROL rho(SatZen_OSF, zen nuestro)=%.3f" % (res, len(g), len(det), ctrl))
    print("     rho(Npix MIROVA, cenit)=%+.3f  rho(n_anom nuestro, cenit)=%+.3f  rho(pc_n, cenit)=%+.3f  rho(n_anom/Npix, cenit)=%+.3f  [sobre pares con deteccion]" % (
        spearmanr(det.z, det.npix).correlation, spearmanr(det.z, det.n).correlation,
        spearmanr(det.z, det.pcn).correlation, spearmanr(det.z, det.n / det.npix).correlation))
    print("     rho(Npix, cenit) sobre TODOS los pares (incluye sin deteccion nuestra)=%+.3f ; fraccion sin deteccion z<30: %.3f z>=50: %.3f" % (
        spearmanr(g.z, g.npix).correlation, (g[g.z < 30].n == 0).mean(), (g[g.z >= 50].n == 0).mean() if (g.z >= 50).any() else float("nan")))
    tr = pd.cut(det.z, [0, 30, 50, 75])
    print("     por tramo (con deteccion): Npix media", det.groupby(tr, observed=True).npix.mean().round(2).to_dict(),
          " n_anom media", det.groupby(tr, observed=True).n.mean().round(2).to_dict(), " n por tramo", det.groupby(tr, observed=True).size().to_dict())
