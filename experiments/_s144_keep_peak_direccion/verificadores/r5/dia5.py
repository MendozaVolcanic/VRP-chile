# La "otra pasada de la misma noche" se define por FECHA UTC: puede caer una pasada DIURNA.
# Solo lectura.
import os, sys, pickle
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3"); V4 = os.path.abspath(HERE + "/../v4")
sys.path.insert(0, V3); sys.path.insert(0, V4); sys.path.insert(0, HERE)
from common3 import *  # noqa
from cruz5 import df, idx_v, zc, cruzada_de, MINGAP_S  # noqa

E = pickle.load(open(HERE + "/embudo5.pkl", "rb"))
F = E[(E.est == "ok")]
print("== |t_q - t_p| de la imagen cruzada elegida (muestra del veredicto, n=%d) ==" % len(F))
q = F.dsep_min
print("  minutos: min %.0f p25 %.0f mediana %.0f p75 %.0f p90 %.0f p99 %.0f max %.0f"
      % (q.min(), q.quantile(.25), q.median(), q.quantile(.75), q.quantile(.9), q.quantile(.99), q.max()))
for c in (120, 180, 240, 360, 600):
    print("   con |dt| > %3d min: %d (%.1f %%)" % (c, int((q > c).sum()), 100 * (q > c).mean()))

# hora UTC del raster elegido
print("\n== hora UTC de adquisicion del TIF cruzado elegido ==")
horas, casos = [], []
for vol, g in df[df.patron & df.pub & (df.lab == "neg_limpio") & (df.vol != "Lastarria")].groupby("vol"):
    if vol not in zc.index:
        continue
    ix = idx_v[vol]
    for _, r in g.iterrows():
        t_p = r["t"]
        dd = (ix.acquisition_utc - t_p).dt.total_seconds()
        m = (ix.acquisition_utc.dt.strftime("%Y-%m-%d") == t_p.strftime("%Y-%m-%d")) & (dd.abs() >= MINGAP_S)
        cand = ix[m]
        if not len(cand):
            continue
        dds = dd[m]
        orden = sorted(range(len(cand)), key=lambda i: (abs(dds.iloc[i]), dds.iloc[i]))
        for i in orden:
            rr = cand.iloc[i]
            Rq, why = usable({"own": bool(rr["own"]), "path": rr["path"]}, vol)
            if Rq is not None:
                horas.append(rr["acquisition_utc"].hour)
                casos.append((vol, t_p, rr["acquisition_utc"], float(dds.iloc[i] / 60), Rq["med"]))
                break
    raster.cache_clear()
H = pd.Series(horas)
print("  ", H.value_counts().sort_index().to_dict())
C = pd.DataFrame(casos, columns=["vol", "t_p", "t_q", "dt_min", "mediana_raster"])
dia = C[(C.t_q.dt.hour >= 14) & (C.t_q.dt.hour <= 22)]
print("  TIF cruzado con hora UTC 14-22 (pasada DIURNA en Chile): %d de %d" % (len(dia), len(C)))
if len(dia):
    print(dia.head(12).to_string())
print("\n  mediana del raster (W/m2 sr um) de los cruzados: min %.4f p50 %.4f p95 %.4f max %.4f"
      % (C.mediana_raster.min(), C.mediana_raster.median(), C.mediana_raster.quantile(.95), C.mediana_raster.max()))
