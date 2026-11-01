"""V2 / F2-H1: Npix de MIROVA (OSF v2.5) contra nuestros conteos, misma pasada.

Pregunta 1: si nuestro conteo y el de MIROVA midieran lo mismo (píxeles), la razón
nuestro/MIROVA en la misma pasada estaría cerca de 1; si MIROVA contara cúmulos, la razón
sería >>1 incluso comparando n_hotspots_clustered (nuestros cúmulos) contra Npix.
Pregunta 2: si el pareo no encontrara nada, n_pares = 0 y se imprime: SIN DATO, no OK.
Control positivo: el pareo por tiempo debe dar |dt| chico (se imprime la mediana).
Denominador: filas OSF de 2025 de los 11 Tier A con VIIRS (375/750), pareadas a nuestro
record del mismo satélite y resolución con |dt| <= 10 min. Ventana: lo que solapen OSF
(hasta 2025-12-31) y data/mirova_equivalent/ (desde 2025-02).
"""
import sys, io, json, unicodedata
from pathlib import Path
import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
OSF = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv"

def norm(s):
    return "".join(c for c in unicodedata.normalize("NFKD", str(s)) if c.isalnum()).lower()

df = pd.read_csv(OSF, encoding="latin-1")
df["t"] = pd.to_datetime(df.timeUTC, dayfirst=True)
df = df[(df.t >= "2025-01-01") & df.Satellite.isin([3, 4])]
df["vn"] = df.Volc_Name.map(norm)

sat = {3: "SNPP", 4: "NOAA20"}
filas = []
for f in sorted((ROOT / "data/mirova_equivalent").glob("*.json")):
    if f.stat().st_size < 2_000_000:
        continue
    vn = norm(f.stem)
    o = df[df.vn.str[:6] == vn[:6]]
    if o.empty:
        print("sin OSF:", f.stem); continue
    recs = json.load(open(f, encoding="utf-8"))["records"]
    R = pd.DataFrame([{ "t": r["datetime_utc"], "sensor": r["sensor"],
                        "npx": r.get("n_anomalous_pixels"), "ncl": r.get("n_hotspots_clustered"),
                        "pcn": (r.get("primary_cluster") or {}).get("n_pixels")} for r in recs])
    R["t"] = pd.to_datetime(R.t, utc=True).dt.tz_localize(None)
    for _, row in o.iterrows():
        s = f"VIIRS_{sat[row.Satellite]}" + ("_750" if row.Resolution == 750 else "")
        c = R[R.sensor == s]
        if c.empty: continue
        dt = (c.t - row.t).abs()
        i = dt.idxmin()
        if dt[i] <= pd.Timedelta(minutes=10):
            filas.append(dict(volc=f.stem, res=row.Resolution, npix_mirova=row.Npix,
                              npx=c.npx[i], ncl=c.ncl[i], pcn=c.pcn[i], dt_min=dt[i].total_seconds()/60))
P = pd.DataFrame(filas)
print("n_pares:", len(P))
if len(P):
    print("mediana |dt| min:", P.dt_min.median())
    for res, g in P.groupby("res"):
        g = g[g.npx.fillna(0) > 0]
        print(f"\n== Resolution {res}: pares con npx>0 = {len(g)} ==")
        print("Npix MIROVA mediana:", g.npix_mirova.median(), " p90:", g.npix_mirova.quantile(.9))
        print("n_anomalous_pixels nuestro mediana:", g.npx.median(), " p90:", g.npx.quantile(.9))
        print("n_hotspots_clustered nuestro mediana:", g.ncl.median())
        print("primary_cluster.n_pixels mediana:", g.pcn.median())
        print("razón npx/Npix mediana:", (g.npx / g.npix_mirova).median())
        print("razón ncl/Npix mediana:", (g.ncl / g.npix_mirova).median())
        print(g.groupby("volc").agg(n=("npx", "size"), npixM=("npix_mirova", "median"), npx=("npx", "median"), ncl=("ncl", "median")).to_string())
