# Analisis de c6.pkl: R con la regla literal de la v6, N1, bandas, heterogeneidad. Solo lectura.
import os, sys, pickle
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(HERE + "/../v3"))

D = pickle.load(open(HERE + "/c6.pkl", "rb"))
R_ = D["R"]; N1a = D["N1a"]


def boot(s, Bn=2000, seed=144, col="d"):
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
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def res(s, nom):
    s = s[s.estado == "ok"]
    if len(s) < 5:
        print("  %-46s n=%d" % (nom, len(s))); return None
    lo, hi = boot(s)
    print("  %-46s n=%4d noches=%3d vols=%2d  D=%+.4f IC95 [%+.4f, %+.4f] ancho %.4f obs=%.3f ref=%.3f"
          % (nom, len(s), (s.vol + s.noche).nunique(), s.vol.nunique(), s.d.mean(), lo, hi, hi - lo,
             s.e.mean(), s.r.mean()))
    return (s.d.mean(), lo, hi)


print("== R: estrato hermano con la regla LITERAL de la v6 (45-120 min, cruzada nocturna) ==")
r_all = res(R_, "R, ventana [45,120]")
ro = R_[R_.estado == "ok"].copy(); ro["gap"] = ro.dsep_min.abs()
res(ro[(ro.gap >= 45) & (ro.gap < 60)], "R, banda [45,60)")
res(ro[(ro.gap >= 60) & (ro.gap <= 120)], "R, banda [60,120]")
print("\n  -- R por volcan --")
print(ro.groupby("vol").agg(n=("d", "size"), noches=("noche", "nunique"), D=("d", "mean"),
                            obs=("e", "mean"), ref=("r", "mean")).round(3).to_string())
print("\n  -- R por etiqueta --")
print(ro.groupby("lab").agg(n=("d", "size"), D=("d", "mean")).round(4).to_string())
print("  |dt| (min): mediana %.0f p10 %.0f p90 %.0f" % (ro.gap.median(), ro.gap.quantile(.1), ro.gap.quantile(.9)))
print("  estados R:", R_.estado.value_counts().to_dict())

print("\n== N1 (lectura A: TODAS las pasadas sin patron), regla v6 ==")
n_all = res(N1a, "N1a, todas sin patron")
na = N1a[N1a.estado == "ok"].copy(); na["gap"] = na.dsep_min.abs()
res(na[na.vol != "Lastarria"], "N1b, sin patron fuera de Lastarria")
res(na[(na.vol != "Lastarria") & (na.lab == "neg_limpio")], "N1c, lectura de la v5 (neg_limpio, fuera Last.)")
res(na[na.lab.isin(["far_ref", "sin_info"])], "N1d, sin patron en el estrato hermano")
print("\n  -- N1a por volcan --")
print(na.groupby("vol").agg(n=("d", "size"), noches=("noche", "nunique"), D=("d", "mean"),
                            obs=("e", "mean"), ref=("r", "mean")).round(3).to_string())
print("\n  -- N1a por etiqueta --")
print(na.groupby("lab").agg(n=("d", "size"), D=("d", "mean"), obs=("e", "mean")).round(4).to_string())
print("  |dt| (min): mediana %.0f p10 %.0f p90 %.0f" % (na.gap.median(), na.gap.quantile(.1), na.gap.quantile(.9)))

