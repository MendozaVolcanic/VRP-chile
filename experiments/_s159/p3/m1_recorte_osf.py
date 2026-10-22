# M1. ¿MIROVA recorta ΔL a cero? Lectura del OSF v2.5 (MODIS y los demás sensores).
# Pregunta 1 del instrumento: si MIROVA NO recortara, ¿lo veríamos? Sólo si el archivo conserva
#   filas con ΔL <= 0. El OSF está filtrado (A105: DBSCAN + umbral de VRP por sensor), así que
#   un umbral de VRP > 0 borra justo esas filas: si el mínimo de VRP es > 0, la medición es CIEGA.
# Pregunta 2: si el instrumento estuviera muerto (columnas mal leídas), la identidad
#   VRP = k * A * (Tot_hot - Tot_bk) no se cumpliría: control positivo.
# Denominador: todas las filas del CSV; ventana: la del archivo (se imprime).
import sys, io, pandas as pd, numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
F = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv"
d = pd.read_csv(F)
d["t"] = pd.to_datetime(d["timeUTC"], format="%d/%m/%Y %H:%M", errors="coerce")
print("filas", len(d), "ventana", d.t.min(), "->", d.t.max())
K = {1000: 18.9e6 * 1.0, 750: 1.97e7 * 0.5625, 375: 18.0 * 140625}
for res, g in d.groupby("Resolution"):
    dl = g.Tot_Lmir_hot - g.Tot_Lmir_bk
    pred = dl * K.get(res, np.nan)
    ok = np.isclose(pred, g.VRP, rtol=1e-3)
    print(f"\nResolution {res}: n={len(g)}  identidad VRP=k*A*dL cumple {ok.sum()} ({100*ok.mean():.2f} %)")
    print(f"  VRP min {g.VRP.min():.4g} W   filas VRP<=0: {(g.VRP<=0).sum()}   filas dL<=0: {(dl<=0).sum()}")
    for nightflag in (0, 1):
        h = g[g.Dayflag == nightflag]
        if len(h):
            print(f"  Dayflag={nightflag}: n={len(h)}  VRP min {h.VRP.min():.4g}  p0.1 {h.VRP.quantile(0.001):.4g}  Npix=1: {(h.Npix==1).sum()}")
    one = g[g.Npix == 1]
    print(f"  Npix=1: n={len(one)}  dL min {(one.Tot_Lmir_hot-one.Tot_Lmir_bk).min():.4g}  dL<=0: {((one.Tot_Lmir_hot-one.Tot_Lmir_bk)<=0).sum()}")
