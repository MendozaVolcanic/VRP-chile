# Analisis del nulo: zc_punto, fracciones, diferencia pareada y bootstrap, con las reglas de la v3.
import os, sys, math, pickle, random
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common3 import *  # noqa

HERE = os.path.dirname(os.path.abspath(__file__))
D = pd.read_pickle(HERE + "/null3.pkl")
ok = D[D.estado == "ok"].copy()

# --- zc_punto por volcan: p95 del sorteo uniforme en la banda (regla v3)
zc = ok.groupby("vol").zu.quantile(0.95)
n_cal = ok.groupby("vol").zu.size()
print("== zc_punto por volcan (p95 del sorteo uniforme en la banda), pool nulo ==")
print(pd.DataFrame({"n_pasadas": n_cal, "zc_punto": zc.round(2)}).to_string())

ok["zc"] = ok.vol.map(zc)
# control de instrumento: el propio sorteo uniforme supera zc en ~5 % por construccion
print("\ncontrol: frac(zu >= zc) = %.3f   frac(reflejo del uniforme >= zc) = %.3f"
      % ((ok.zu >= ok.zc).mean(), (ok.zu_ref >= ok.zc).mean()))

# --- el nulo del control P': punto "como nuestro P" contra su reflejo
fp = (ok.zp >= ok.zc).mean()
fpp = (ok.zpp >= ok.zc).mean()
dif = ok.zp - ok.zpp
print("\n== NULO DEL CONTROL P' (pasadas RUTINA ajenas a la muestra de M2, n=%d) ==" % len(ok))
print("frac(Z(X) >= zc) = %.3f   frac(Z(X') >= zc) = %.3f   diferencia = %+.3f" % (fp, fpp, fp - fpp))
print("mediana de la diferencia pareada Z(X) - Z(X') = %+.4f" % dif.median())

rng = np.random.default_rng(144)
vols = ok.vol.values


def boot(sub, B=2000):
    """bootstrap estratificado por volcan de la mediana de la diferencia pareada."""
    out = []
    idx_por_vol = {v: np.where(sub.vol.values == v)[0] for v in sub.vol.unique()}
    dd = (sub.zp - sub.zpp).values
    for _ in range(B):
        sel = np.concatenate([rng.choice(ix, len(ix), replace=True) for ix in idx_por_vol.values()])
        out.append(np.median(dd[sel]))
    return np.percentile(out, [2.5, 97.5])


lo, hi = boot(ok)
print("IC 95 %% bootstrap estratificado de la mediana pareada: [%+.4f, %+.4f]" % (lo, hi))


def veredicto(fp, fpp, lo, hi):
    if (fp - fpp) >= 0.15 and lo > 0:
        return "cae sobre calor"
    if (fp - fpp) < 0.05 and lo <= 0 <= hi:
        return "no se distingue"
    return "INCONCLUSO"


print("VEREDICTO QUE DARIA LA REGLA DE LA v3 SOBRE EL NULO:", veredicto(fp, fpp, lo, hi))

print("\n-- por volcan --")
for v, g in ok.groupby("vol"):
    if len(g) < 10:
        continue
    f1 = (g.zp >= g.zc).mean(); f2 = (g.zpp >= g.zc).mean()
    print("  %-22s n=%3d  frac X=%.3f  frac X'=%.3f  dif=%+.3f  mediana pareada=%+.4f"
          % (v, len(g), f1, f2, f1 - f2, (g.zp - g.zpp).median()))

# --- submuestras del tamano del veredicto (n=30, 100, 554)
print("\n-- el mismo nulo con submuestras (500 repeticiones) --")
for n in (30, 100, 554):
    res = []
    for _ in range(500):
        s = ok.sample(n=min(n, len(ok)), replace=(n > len(ok)), random_state=rng.integers(1e9))
        f1 = (s.zp >= s.zc).mean(); f2 = (s.zpp >= s.zc).mean()
        res.append(f1 - f2)
    res = np.array(res)
    print("   n=%3d  dif de fracciones: mediana %+.3f  p5 %+.3f  p95 %+.3f   frac con dif>=0.15: %.3f   frac con dif<0.05: %.3f"
          % (n, np.median(res), np.percentile(res, 5), np.percentile(res, 95), (res >= 0.15).mean(), (res < 0.05).mean()))

# --- perfil acimutal a 2,8 km
print("\n== perfil acimutal de Z a 2,8 km del crater (mediana por sector), pool nulo ==")
cols = [c for c in ok.columns if c.startswith("z_")]
tab = ok.groupby("vol")[cols].median()
tab.columns = [c.split("_")[1] for c in cols]
print(tab.round(2).to_string())
print("\nmediana global por sector:")
print(ok[cols].median().round(3).to_string())

# diferencia entre sectores opuestos
print("\n== asimetria por par de sectores opuestos (mediana de Z(s) - Z(s+180)) ==")
for s in (0, 45, 90, 135):
    dd = ok[f"z_{s}"] - ok[f"z_{s+180}"]
    print("  %3d vs %3d : mediana %+.3f  (media %+.3f)" % (s, s + 180, dd.median(), dd.mean()))
