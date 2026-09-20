# Embudo de la muestra del veredicto con la regla LITERAL de la v6 (45-120 min, cruzada nocturna).
# SOLO CONTEO: no evaluo Z en el P de ninguna pasada de la muestra del veredicto.
import os, sys, pickle, time
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (os.path.abspath(HERE + "/../v3"), os.path.abspath(HERE + "/../v4"), HERE):
    sys.path.insert(0, p)
from common3 import *  # noqa
from c6 import df, zc, refs_de, cruzada_v6, MINREF, raster  # noqa

M2 = df[df.patron & df.pub & (df.lab == "neg_limpio") & (df.vol != "Lastarria")].copy()
print("== muestra del veredicto (patron+pub+neg_limpio, fuera de Lastarria): %d ==" % len(M2))

rows = []
t0 = time.time()
for vol, g in M2.groupby("vol"):
    for _, r in g.sort_values("t").iterrows():
        R = refs_de(vol, r["t"], r["noche"], r["P"])
        est = "sin_zc"
        dsep = None
        if vol in zc.index:
            cr, why = cruzada_v6(vol, r["t"])
            est = "ok" if cr is not None else why
            if cr is not None:
                dsep = abs(cr[1]) / 60.0
        rows.append(dict(vol=vol, t=r["t"], noche=r["noche"], tramo=r["tramo"],
                         n_ref=len(R), est=est, dsep_min=dsep))
    raster.cache_clear()
E = pd.DataFrame(rows)
pickle.dump(E, open(HERE + "/e6.pkl", "wb"))
print("estados:", E.est.value_counts().to_dict(), " (%.0fs)" % (time.time() - t0))
print("n_ref:", E.n_ref.value_counts().sort_index().to_dict(), " con menos de 3:", int((E.n_ref < MINREF).sum()))

F = E[(E.est == "ok") & (E.n_ref >= MINREF)].copy()
print("\n== MUESTRA FINAL v6: %d pasadas (de %d) ==" % (len(F), len(E)))
tb = F.groupby("vol").agg(pasadas=("t", "size"), noches=("noche", "nunique")).sort_values("noches", ascending=False)
print(tb.to_string())
print("  noches de volcan totales:", F.groupby(["vol", "noche"]).ngroups)
print("  volcanes con >=20 noches:", int((tb.noches >= 20).sum()), "de", len(tb),
      "->", [v for v in tb.index if tb.noches[v] >= 20])
print("  |dt| (min): mediana %.0f p10 %.0f p90 %.0f" % (F.dsep_min.median(), F.dsep_min.quantile(.1), F.dsep_min.quantile(.9)))
for t, g in F.groupby("tramo"):
    tb2 = g.groupby("vol").noche.nunique()
    print("   tramo %-4s: %d pasadas, %d noches, volcanes >=20 noches: %d %s"
          % (t, len(g), g.groupby(["vol", "noche"]).ngroups, int((tb2 >= 20).sum()),
             [v for v in tb2.index if tb2[v] >= 20]))

# comparacion de composicion con R (estrato hermano)
D = pickle.load(open(HERE + "/c6.pkl", "rb"))
ro = D["R"]; ro = ro[ro.estado == "ok"]
cA = F.groupby("vol").noche.nunique(); cA = cA / cA.sum()
cB = ro.groupby("vol").noche.nunique(); cB = cB / cB.sum()
comp = pd.DataFrame({"veredicto": cA, "R_hermano": cB}).fillna(0).round(3)
print("\n== composicion por volcan (fraccion de noches) ==")
print(comp.to_string())
print("  distancia L1 entre las dos composiciones: %.3f" % float((comp.veredicto - comp.R_hermano).abs().sum()))

# R re-ponderado a la composicion del veredicto
Dv = ro.groupby("vol").d.mean()
w = cA.reindex(Dv.index).fillna(0)
w = w / w.sum()
print("  R agrupado tal cual                 : %+.4f" % ro.d.mean())
print("  R re-ponderado al mix del veredicto : %+.4f" % float((Dv * w).sum()))

# nulo N1 re-ponderado
na = D["N1a"]; na = na[na.estado == "ok"]
Dn = na.groupby("vol").d.mean()
wn = cA.reindex(Dn.index).fillna(0); wn = wn / wn.sum()
print("  N1a agrupado tal cual               : %+.4f" % na.d.mean())
print("  N1a re-ponderado al mix del veredicto: %+.4f" % float((Dn * wn).sum()))
