# Comprobaciones sueltas: afirmaciones de hecho de la v4 y detalles de ejecucion.
import os, sys, json, pickle, math
from datetime import datetime, timezone
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3")
sys.path.insert(0, V3); sys.path.insert(0, HERE)
from common3 import *  # noqa
import base4 as B  # noqa
from analiza4 import arma, boot_D, zc, NUL  # noqa

df = B.df
geomP = B.geomP

print("== S1: banda de r(P) ==")
print("  frac en 1,5-3,5 km = %.4f   mediana = %.3f km   p99 = %.2f  max = %.2f"
      % (float(((geomP.rP >= 1.5) & (geomP.rP <= 3.5)).mean()), geomP.rP.median(),
         geomP.rP.quantile(0.99), geomP.rP.max()))

print("\n== S7 embudo (v4 dice 6.241 / 2.999 / 2.627 / 1.134 / 1.113 / 635 / 554) ==")
print("  records nocturnos V375:", len(df))
print("  con patron:", int(df.patron.sum()))
print("  con patron y publicados:", int((df.patron & df.pub).sum()))
sub = df[df.patron & df.pub]
print("  de esos neg_limpio:", int((sub.lab == 'neg_limpio').sum()),
      " fuera de Lastarria:", int(((sub.lab == 'neg_limpio') & (sub.vol != 'Lastarria')).sum()))

print("\n== S5 control H: pasadas con alerta, TIF pareado y ctx_cluster de 2+ px dentro del inner ==")
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/scripts")
import banco_paridad as bp
inner = bp.inner_desde_html()
pos = df[(df.lab == "pos") & df.tif.notna()].copy()
key = {(r.vol, pd.Timestamp(r.dt).strftime("%Y-%m-%d %H:%M")) for r in pos.itertuples()}
cnt = {}
for vol in VOLS:
    d = json.load(open(ROOT + f"/data/mirova_equivalent/{vol}.json", encoding="utf-8"))
    for r in d["records"]:
        k = (vol, (r.get("datetime_utc") or "")[:16])
        if k not in key:
            continue
        cc = r.get("ctx_cluster") or {}
        n = cc.get("n_pixels") or 0
        la, lo = cc.get("centroid_lat"), cc.get("centroid_lon")
        if n >= 2 and la is not None and lo is not None:
            if hav(la, lo, *vent(vol)) <= inner[vol]:
                cnt[vol] = cnt.get(vol, 0) + 1
print("  total:", sum(cnt.values()), " por volcan:", cnt)

print("\n== sensibilidad del percentil de zc_punto para el CONTROL TEMPORAL ==")
zz = B_zz = pickle.load(open(HERE + "/null4.pkl", "rb"))["zc"].dropna(subset=["z"])
for q in (0.85, 0.90, 0.95, 0.99):
    zq = zz.groupby("vol").z.quantile(q)
    rows = []
    for f in NUL:
        v = f["vol"]
        if v not in zq.index or f["zobs"] is None:
            continue
        zs, gaps = f["zs"], f["gaps"]
        ok = np.isfinite(zs) & (np.abs(gaps) > 3)
        idx = [i for i in np.argsort(np.abs(np.where(ok, gaps, 1e9)))[:5] if ok[i]]
        if len(idx) < 3:
            continue
        rows.append((v, 1.0 * (f["zobs"] >= zq[v]) - float(np.mean(zs[idx] >= zq[v]))))
    d = pd.DataFrame(rows, columns=["vol", "d"])
    print("  percentil %.2f:  D del nulo = %+.4f  (n=%d)" % (q, d.d.mean(), len(d)))

print("\n== asimetria temporal de las referencias (borde del archivo) ==")
rows = []
for f in NUL:
    zs, gaps = f["zs"], f["gaps"]
    ok = np.isfinite(zs) & (np.abs(gaps) > 3)
    idx = [i for i in np.argsort(np.abs(np.where(ok, gaps, 1e9)))[:5] if ok[i]]
    if len(idx) < 3:
        continue
    g = gaps[idx]
    rows.append(dict(vol=f["vol"], antes=int((g < 0).sum()), despues=int((g > 0).sum()),
                     dt=f["dt"], d=None))
Aa = pd.DataFrame(rows)
un = (Aa.antes == 0) | (Aa.despues == 0)
print("  pasadas con las 5 referencias de un solo lado: %d de %d (%.1f %%)"
      % (int(un.sum()), len(Aa), 100 * un.mean()))

print("\n== tramos de la muestra de M2 ==")
o = B.d3["o_neg"]
fin = o[(o.estado == "ok") & o.dl0_P & o.dl0_Pp].copy()
fin["noche"] = pd.to_datetime(fin.dt, utc=True).dt.strftime("%Y-%m-%d")
for t, g in fin.groupby("tramo"):
    tb = g.groupby("vol2").noche.nunique()
    print("  tramo %s: %d pasadas, %d noches, volcanes con >=20 noches: %d"
          % (t, len(g), g.groupby(['vol2', 'noche']).ngroups, int((tb >= 20).sum())))
