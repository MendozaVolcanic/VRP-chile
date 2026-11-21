"""S193: resume records.csv y pixeles.csv de medir_agua.py en tablas para el INFORME (salida: resumen.txt)."""
import os
import sys

import numpy as np
import pandas as pd

D = sys.argv[1]
rec = pd.read_csv(os.path.join(D, "records.csv"))
pix = pd.read_csv(os.path.join(D, "pixeles.csv"))
out = []
P = out.append

rec["periodo"] = np.where(rec.noche == 1, "noche", "dia")
rec["cerca5"] = rec.dist_km <= 5
P(f"records con deteccion: {len(rec)}; volcanes: {rec.volcan.nunique()}; pixeles: {len(pix)}")
P(f"ventana de fechas: {rec.datetime_utc.min()} a {rec.datetime_utc.max()}")
P("")
P("== Clase del pixel mas caliente (MIR) por familia y periodo ==")
t = rec.pivot_table(index=["familia", "periodo"], columns="clase_pico", values="volcan", aggfunc="count", fill_value=0)
t["total"] = t.sum(axis=1)
t["%agua"] = (100 * t.get("agua", 0) / t.total).round(1)
t["%orilla"] = (100 * t.get("orilla", 0) / t.total).round(1)
P(t.to_string())
P("")
P("== Por volcan: pasadas con deteccion y con el pico sobre agua (>=50 % de la celda) ==")
g = rec.groupby("volcan")
tv = pd.DataFrame({
    "det": g.size(),
    "agua": g.apply(lambda x: (x.clase_pico == "agua").sum()),
    "agua_noche": g.apply(lambda x: ((x.clase_pico == "agua") & (x.noche == 1)).sum()),
    "agua_<=5km": g.apply(lambda x: ((x.clase_pico == "agua") & x.cerca5).sum()),
    "orilla": g.apply(lambda x: (x.clase_pico == "orilla").sum()),
    "vrp_med_agua": g.apply(lambda x: x.loc[x.clase_pico == "agua", "vrp_mw"].median()),
    "vrp_max_agua": g.apply(lambda x: x.loc[x.clase_pico == "agua", "vrp_mw"].max()),
    "vrp_med_tierra": g.apply(lambda x: x.loc[x.clase_pico == "tierra", "vrp_mw"].median()),
    "dist_med_agua": g.apply(lambda x: x.loc[x.clase_pico == "agua", "dist_km"].median()),
})
tv["%agua"] = (100 * tv.agua / tv.det).round(1)
tv = tv.sort_values("agua", ascending=False)
P(tv.round(2).to_string())
P("")
P("== Totales ==")
for c in ["agua", "orilla", "tierra"]:
    s = rec[rec.clase_pico == c]
    P(f"{c}: {len(s)} pasadas ({100*len(s)/len(rec):.1f} %), VRP mediana {s.vrp_mw.median():.3f} MW, "
      f"p90 {s.vrp_mw.quantile(.9):.3f}, max {s.vrp_mw.max():.2f}, suma {s.vrp_mw.sum():.1f} MW; "
      f"noche {int((s.noche==1).sum())}; <=5 km {int(s.cerca5.sum())}; >=1 MW {int((s.vrp_mw>=1).sum())}")
P("")
P("== Agua: distribucion de VRP (MW) ==")
s = rec[rec.clase_pico == "agua"]
for lo, hi in [(0, .1), (.1, .5), (.5, 1), (1, 5), (5, 1e9)]:
    P(f"  [{lo},{hi}): {int(((s.vrp_mw>=lo)&(s.vrp_mw<hi)).sum())}")
P("")
P("== Agua por mes (todas las familias), noche y dia ==")
P(s.pivot_table(index="mes", columns="periodo", values="volcan", aggfunc="count", fill_value=0).to_string())
P("")
P("== Contraste: BT MIR del pico menos t_bg (K), por clase y periodo (solo con t_bg) ==")
r2 = rec.dropna(subset=["t_bg_k"]).copy()
r2["dT"] = r2.bt_pico_k - r2.t_bg_k
P(r2.groupby(["clase_pico", "periodo"]).dT.describe(percentiles=[.1, .5, .9]).round(1).to_string())
P("")
for V in ["LagunaDelMaule", "Villarrica", "PuyehueCordonCaulle", "Llaima", "Calbuco", "Osorno", "MochoChoshuenco"]:
    s = rec[rec.volcan == V]
    if not len(s):
        continue
    P(f"== {V}: clase por familia y periodo ==")
    P(s.pivot_table(index=["familia", "periodo"], columns="clase_pico", values="mes", aggfunc="count", fill_value=0).to_string())
    a = s[s.clase_pico == "agua"]
    if len(a):
        P(f"  agua por mes: {a.mes.value_counts().sort_index().to_dict()}")
        P(f"  agua: dist km mediana {a.dist_km.median():.1f} (min {a.dist_km.min():.1f}, max {a.dist_km.max():.1f}); "
          f"<=5 km {int(a.cerca5.sum())}; fuente {a.fuente.value_counts().to_dict()}")
        P(f"  agua: VRP mediana {a.vrp_mw.median():.3f}, max {a.vrp_mw.max():.2f} MW; >=1 MW {int((a.vrp_mw>=1).sum())}")
        a5 = a[a.cerca5]
        if len(a5):
            P("  agua a <=5 km (fecha, sensor, periodo, VRP, dist, n_pix, n_pix_agua):")
            for _, x in a5.sort_values("datetime_utc").iterrows():
                P(f"    {x.datetime_utc} {x.sensor} {x.periodo} {x.vrp_mw:.3f} MW {x.dist_km:.2f} km {x.n_pix}/{x.n_pix_agua}")
    P("")
with open(os.path.join(D, "resumen.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))
print("\n".join(out))
