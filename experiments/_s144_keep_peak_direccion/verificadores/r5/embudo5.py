# Embudo de la muestra del veredicto: cuantas pasadas pierden la imagen cruzada y cuantas no
# consiguen 3 sitios de referencia. SOLO CONTEO: no evaluo Z en el P de ninguna de ellas.
import os, sys, math, pickle, time
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3"); V4 = os.path.abspath(HERE + "/../v4")
sys.path.insert(0, V3); sys.path.insert(0, V4); sys.path.insert(0, HERE)
from common3 import *  # noqa
from cruz5 import df, idx_v, zc, refs_de, cruzada_de, MINREF, POOL  # noqa

M2 = df[df.patron & df.pub & (df.lab == "neg_limpio") & (df.vol != "Lastarria")].copy()
print("== muestra del veredicto: patron + publicado + neg_limpio, fuera de Lastarria: %d ==" % len(M2))
print("  ", M2.vol.value_counts().to_dict())
print("  tramos:", M2.tramo.value_counts().to_dict())

rows = []
t0 = time.time()
for vol, g in M2.groupby("vol"):
    for _, r in g.sort_values("t").iterrows():
        R = refs_de(vol, r["t"], r["noche"], r["P"])
        nref = len(R)
        if vol not in zc.index:
            est = "sin_zc"
        else:
            cr, why = cruzada_de(vol, r["t"])
            est = "ok" if cr is not None else why
        rows.append(dict(vol=vol, t=r["t"], noche=r["noche"], tramo=r["tramo"],
                         n_ref=nref, est=est,
                         dsep_min=None if est != "ok" else abs(cr[1]) / 60.0))
    raster.cache_clear()
    print("  %-22s (%.0fs)" % (vol, time.time() - t0), flush=True)

E = pd.DataFrame(rows)
pickle.dump(E, open(HERE + "/embudo5.pkl", "wb"))
print("\n-- estado de la imagen cruzada --")
print(E.est.value_counts().to_dict())
print("-- sitios de referencia disponibles (a mas de 1,5 km de P, brecha >3 d) --")
print("  n_ref:", E.n_ref.value_counts().sort_index().to_dict())
print("  pasadas con menos de 3:", int((E.n_ref < MINREF).sum()))

F = E[(E.est == "ok") & (E.n_ref >= MINREF)].copy()
print("\n== MUESTRA FINAL: %d pasadas (de %d) ==" % (len(F), len(E)))
tb = F.groupby("vol").agg(pasadas=("t", "size"), noches=("noche", "nunique")).sort_values("pasadas", ascending=False)
print(tb.to_string())
print("  noches totales de volcan:", F.groupby(["vol", "noche"]).ngroups)
print("  volcanes con >=20 noches:", int((tb.noches >= 20).sum()), "de", len(tb))
print("  tramos:", F.tramo.value_counts().to_dict())
for t, g in F.groupby("tramo"):
    tb2 = g.groupby("vol").noche.nunique()
    print("   tramo %-4s: %d pasadas, %d noches, volcanes con >=20 noches: %d"
          % (t, len(g), g.groupby(["vol", "noche"]).ngroups, int((tb2 >= 20).sum())))
print("  |dt| de la cruzada (min): mediana %.0f  p10 %.0f  p90 %.0f  max %.0f"
      % (F.dsep_min.median(), F.dsep_min.quantile(.1), F.dsep_min.quantile(.9), F.dsep_min.max()))

# --- sensibilidad: separacion de los sitios de referencia
print("\n-- sensibilidad de la regla de separacion (cuantas pasadas quedan con <3 refs) --")
for sep in (0.75, 1.5, 3.0, 4.0):
    n_bad, n_ref5 = 0, 0
    for vol, g in M2.groupby("vol"):
        for _, r in g.iterrows():
            k = len(refs_de(vol, r["t"], r["noche"], r["P"], sep=sep))
            n_bad += (k < MINREF); n_ref5 += (k == 5)
    print("   sep > %.2f km:  con menos de 3 refs: %4d   con las 5: %4d  (de %d)" % (sep, n_bad, n_ref5, len(M2)))
