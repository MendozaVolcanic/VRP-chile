# Analisis: cuanto sesgo queda con la pasada cruzada, C1, C2. Solo lectura.
import os, sys, pickle, math
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3"); V4 = os.path.abspath(HERE + "/../v4")
sys.path.insert(0, V3); sys.path.insert(0, V4); sys.path.insert(0, HERE)
from common3 import *  # noqa

D = pickle.load(open(HERE + "/cruz5.pkl", "rb"))
cross, own, nul = D["cross"], D["own"], D["null"]


def boot_D(s, Bn=2000, seed=144, col="d"):
    g = np.random.default_rng(seed)
    key = (s.vol + "|" + s.noche).values
    noches = {v: np.array(sorted(set(key[(s.vol == v).values]))) for v in s.vol.unique()}
    porn = {k: v[col].values for k, v in s.groupby(key)}
    out = []
    for _ in range(Bn):
        vals = []
        for v, ns in noches.items():
            sel = g.choice(ns, len(ns), True)
            vals.append(np.concatenate([porn[k] for k in sel]))
        out.append(float(np.mean(np.concatenate(vals))))
    return np.percentile(out, [2.5, 97.5])


def resumen(s, nombre, col="d"):
    s = s[s.estado == "ok"]
    if not len(s):
        print("  %-42s n=0" % nombre); return
    lo, hi = boot_D(s, col=col)
    print("  %-42s n=%4d noches=%3d  D=%+.4f  IC95 [%+.4f, %+.4f]  obs=%.3f ref=%.3f"
          % (nombre, len(s), (s.vol + s.noche).nunique(), s[col].mean(), lo, hi,
             s.e.mean() if col == "d" else np.nan, s.r.mean() if col == "d" else np.nan))
    return s


print("== 1. SESGO DE SELECCION: mismas pasadas fuera de la muestra del veredicto ==")
k_own = set(zip(own[own.estado == "ok"].vol, own[own.estado == "ok"].t))
k_cross = set(zip(cross[cross.estado == "ok"].vol, cross[cross.estado == "ok"].t))
inter = k_own & k_cross
print("  con imagen propia usable: %d   con imagen cruzada usable: %d   en las dos: %d"
      % (len(k_own), len(k_cross), len(inter)))

co = cross[cross.estado == "ok"].copy(); ow = own[own.estado == "ok"].copy()
co["k"] = list(zip(co.vol, co.t)); ow["k"] = list(zip(ow.vol, ow.t))
resumen(ow, "PROPIA, todas las que la tienen (C2 brazo A)")
resumen(ow[ow.k.isin(inter)], "PROPIA, interseccion")
resumen(co[co.k.isin(inter)], "CRUZADA, interseccion")
resumen(co, "CRUZADA, todas las que la tienen")

print("\n  -- por etiqueta (cruzada, todas) --")
print(co.groupby("lab").agg(n=("d", "size"), D=("d", "mean"), obs=("e", "mean"), ref=("r", "mean")).round(3).to_string())
print("\n  -- por volcan (cruzada, todas) --")
print(co.groupby("vol").agg(n=("d", "size"), D=("d", "mean"), obs=("e", "mean"), ref=("r", "mean")).round(3).to_string())

print("\n== 2. NULO con imagen cruzada (punto sorteado) ==")
nu = resumen(nul, "NULO cruzado")
print("\n  -- por volcan --")
print(nul[nul.estado == "ok"].groupby("vol").agg(n=("d", "size"), D=("d", "mean"),
      obs=("e", "mean"), ref=("r", "mean")).round(3).to_string())

print("\n== 3. C1 (intercambio de roles), sobre cada corrida ==")
for nom, s in [("cruzada fuera de muestra", co), ("propia fuera de muestra", ow), ("nulo cruzado", nul[nul.estado == "ok"])]:
    lo, hi = boot_D(s, col="c1")
    print("  %-30s n=%4d  C1=%+.4f  IC95 [%+.4f, %+.4f]   (|C1| <= 0,05 pasa)"
          % (nom, len(s), s.c1.mean(), lo, hi))

print("\n== 4. diagnosticos de ejecucion ==")
for nom, s in [("cruzada", co), ("nulo", nul[nul.estado == "ok"])]:
    print("  %-10s n_ref: %s   |dt| cruzada (min): mediana %.0f p10 %.0f p90 %.0f   sep refs (d): mediana %.1f"
          % (nom, s.n_ref.value_counts().to_dict(), s.dsep_min.abs().median(),
             s.dsep_min.abs().quantile(0.1), s.dsep_min.abs().quantile(0.9), s.sep_ref_d.median()))
print("  estados cruzada (universo completo):", cross.estado.value_counts().to_dict())
print("  estados nulo   (universo completo):", nul.estado.value_counts().to_dict())
