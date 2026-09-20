# Simulacion de la regla de veredicto de la v4 S7 sobre el nulo, potencia, y el proxy de seleccion.
import os, sys, math, pickle
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3")
sys.path.insert(0, V3); sys.path.insert(0, HERE)
from common3 import *  # noqa
import base4 as B  # noqa
from analiza4 import arma, boot_D, zc, NUL, PROX  # noqa

df = B.df
u = arma(NUL, gap_d=3.0)
u = u[u.usada]

# ---------- A. n real de M2 por volcan y noches
o = B.d3["o_neg"]
fin = o[(o.estado == "ok") & o.dl0_P & o.dl0_Pp].copy()
fin["noche"] = pd.to_datetime(fin.dt, utc=True).dt.strftime("%Y-%m-%d")
print("== muestra real de M2 (554): pasadas y noches por volcan ==")
tb = fin.groupby("vol2").agg(pasadas=("dt", "size"), noches=("noche", "nunique")).sort_values("pasadas", ascending=False)
print(tb.to_string())
print("total noches:", fin.groupby(["vol2", "noche"]).ngroups,
      " volcanes con >=20 noches:", int((tb.noches >= 20).sum()), "de", len(tb))
print(" tramos:", fin.tramo.value_counts().to_dict())

# ---------- B. la regla de veredicto sobre el nulo, al n real
NV = dict(zip(tb.index, tb.pasadas))


def simula(rep=200, delta=0.0, seed=7):
    g = np.random.default_rng(seed)
    res = []
    for _ in range(rep):
        partes = []
        for v, n in NV.items():
            pool = u[u.vol == v]
            if len(pool) == 0:
                pool = u
            s = pool.sample(n=n, replace=True, random_state=int(g.integers(1e9))).copy()
            s["vol"] = v
            if delta > 0:
                flip = g.random(len(s)) < delta
                s.loc[flip, "e"] = 1.0
                s["d"] = s.e - s.r
            # noches ficticias para el remuestreo (una por pasada resampleada)
            s["noche"] = [f"{i}" for i in range(len(s))]
            partes.append(s)
        S = pd.concat(partes, ignore_index=True)
        (lo, hi), _ = boot_D(S, Bn=400, seed=int(g.integers(1e9)))
        Dv = S.groupby("vol").d.mean()
        nn = S.groupby("vol").size()
        elig = Dv[nn >= 20]
        cond2 = (elig > 0).sum() >= math.ceil(2 / 3 * len(elig)) if len(elig) else False
        if lo > 0.05 and cond2:
            ver = "cae sobre calor"
        elif lo >= -0.05 and hi <= 0.05:
            ver = "no se distingue"
        else:
            ver = "INCONCLUSO"
        res.append((ver, S.d.mean(), lo, hi, int((elig > 0).sum()), len(elig)))
    r = pd.DataFrame(res, columns=["ver", "D", "lo", "hi", "pos", "elig"])
    return r


print("\n== la regla de la v4 S7 sobre el NULO, al n real (200 repeticiones) ==")
r0 = simula()
print(r0.ver.value_counts().to_dict())
print("  D medio %+.4f  ancho medio del IC %.4f  volcanes con D_v>0: mediana %d de %d"
      % (r0.D.mean(), (r0.hi - r0.lo).mean(), r0.pos.median(), r0.elig.median()))

print("\n== potencia: cuanta senal hace falta para 'cae sobre calor' ==")
for delta in (0.02, 0.05, 0.08, 0.10, 0.15, 0.20):
    r = simula(rep=100, delta=delta, seed=11)
    vc = r.ver.value_counts()
    print("  delta=%.2f  D=%+.3f  cae sobre calor: %3d%%   no se distingue: %3d%%   INCONCLUSO: %3d%%"
          % (delta, r.D.mean(), vc.get("cae sobre calor", 0), vc.get("no se distingue", 0),
             vc.get("INCONCLUSO", 0)))

# ---------- C. condicion de los dos tercios, aislada
print("\n== condicion 'D_v>0 en 2/3 de los volcanes con >=20 noches' ==")
print("  volcanes con >=20 NOCHES en la muestra real:", list(tb[tb.noches >= 20].index))
for k in (4, 6, 8, 10):
    p = sum(1 for _ in range(20000) if np.random.binomial(k, 0.5) >= math.ceil(2 / 3 * k)) / 20000
    print("   con %2d volcanes elegibles, un campo sin senal la cumple el %.1f %% de las veces" % (k, 100 * p))

# ---------- D. proxy de seleccion: nuestro propio P, en pasadas con patron NO publicadas
p = arma(PROX, gap_d=3.0)
p = p[p.usada]
print("\n== PROXY DE CONTAMINACION: Z en NUESTRO P, pasadas neg_limpio con patron NO publicadas ==")
print("  n=%d  D=%+.4f  tasa obs=%.3f  tasa ref=%.3f" % (len(p), p.d.mean(), p.e.mean(), p.r.mean()))
if len(p):
    (lo, hi), _ = boot_D(p.assign(noche=p.dt.map(lambda x: pd.Timestamp(x).strftime('%Y-%m-%d'))))
    print("  IC95 [%+.4f, %+.4f]" % (lo, hi))
    print(p.groupby("vol").agg(n=("d", "size"), D=("d", "mean"), obs=("e", "mean"), ref=("r", "mean")).round(3).to_string())
