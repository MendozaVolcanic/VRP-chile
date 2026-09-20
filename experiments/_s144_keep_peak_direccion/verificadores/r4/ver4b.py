# Alcanzabilidad por tramo, que condicion manda, y senal concentrada en pocos volcanes.
import os, sys, math, pickle
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3")
sys.path.insert(0, V3); sys.path.insert(0, HERE)
from common3 import *  # noqa
import base4 as B  # noqa
from analiza4 import arma, boot_D, zc, NUL  # noqa

u = arma(NUL, gap_d=3.0); u = u[u.usada]
o = B.d3["o_neg"]
fin = o[(o.estado == "ok") & o.dl0_P & o.dl0_Pp].copy()
fin["noche"] = pd.to_datetime(fin.dt, utc=True).dt.strftime("%Y-%m-%d")


def sim(nv_noches, rep=150, delta=0.0, delta_vols=None, seed=3, cond2_vacio=False):
    g = np.random.default_rng(seed)
    out = []
    for _ in range(rep):
        partes = []
        for v, nn in nv_noches.items():
            pool = u[u.vol == v]
            if len(pool) < 5:
                pool = u
            s = pool.sample(n=nn, replace=True, random_state=int(g.integers(1e9))).copy()
            s["vol"] = v
            dl = delta if (delta_vols is None or v in delta_vols) else 0.0
            if dl > 0:
                s.loc[g.random(len(s)) < dl, "e"] = 1.0
            s["d"] = s.e - s.r
            s["noche"] = [f"{v}{i}" for i in range(len(s))]
            partes.append(s)
        S = pd.concat(partes, ignore_index=True)
        (lo, hi), _ = boot_D(S, Bn=400, seed=int(g.integers(1e9)))
        Dv = S.groupby("vol").d.mean(); nn2 = S.groupby("vol").size()
        elig = Dv[nn2 >= 20]
        if len(elig) == 0:
            c2 = cond2_vacio
        else:
            c2 = (elig > 0).sum() >= math.ceil(2 / 3 * len(elig))
        ver = ("cae sobre calor" if (lo > 0.05 and c2)
               else "no se distingue" if (lo >= -0.05 and hi <= 0.05) else "INCONCLUSO")
        out.append((ver, S.d.mean(), lo, hi, lo > 0.05, c2))
    return pd.DataFrame(out, columns=["ver", "D", "lo", "hi", "c1", "c2"])


# --- por tramo, con las NOCHES reales de cada tramo
for t in ("pre", "post"):
    g = fin[fin.tramo == t]
    nv = g.groupby("vol2").noche.nunique().to_dict()
    for cv in (True, False):
        r = sim(nv, rep=120, seed=5, cond2_vacio=cv)
        print("tramo %-4s (%d noches, %d volcanes, elegibles>=20 noches: %d) cond2 vacia=%s -> %s  ancho IC medio %.3f"
              % (t, sum(nv.values()), len(nv), sum(1 for x in nv.values() if x >= 20), cv,
                 r.ver.value_counts().to_dict(), (r.hi - r.lo).mean()))
        if t == "pre":
            break

# --- global: que condicion manda cuando hay senal
nvg = fin.groupby("vol2").noche.nunique().to_dict()
print("\n== que condicion manda (global, %d noches) ==" % sum(nvg.values()))
for delta in (0.05, 0.08, 0.10, 0.12, 0.15):
    r = sim(nvg, rep=120, delta=delta, seed=9)
    print("  delta=%.2f D=%+.3f -> %-42s  IC por encima de 0,05: %3d%%   dos tercios: %3d%%"
          % (delta, r.D.mean(), str(r.ver.value_counts().to_dict()), int(100 * r.c1.mean()), int(100 * r.c2.mean())))

# --- senal concentrada en 2 volcanes (Villarrica y Chaiten, los cat-b de A54)
print("\n== senal FUERTE concentrada en 2 volcanes (el resto sin senal) ==")
for delta in (0.20, 0.40, 0.60):
    r = sim(nvg, rep=120, delta=delta, delta_vols={"Villarrica", "Chaiten"}, seed=13)
    print("  delta=%.2f en Villarrica y Chaiten  D=%+.3f -> %s"
          % (delta, r.D.mean(), r.ver.value_counts().to_dict()))
