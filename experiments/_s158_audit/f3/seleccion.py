# -*- coding: utf-8 -*-
"""F3: ¿dónde se pierde la energía entre lo que alertamos y lo que publicamos? Pares clase 1 del OSF 2025.
Etapas, en sumas por volcán y sensor (MW, con la energía de MIROVA como vara):
  E_esc  = VRP de todos nuestros alertados (ΔL listados * k*A; sin tope D9)
  E_rec  = record.vrp_mir_mw (escena con tope D9 aplicado)
  E_pc   = primary_cluster.vrp_mw (cúmulo vent_anchored, con tope D9)
  E_pub  = magnitud publicada (mirovaEqVrpCore aproximada: F5' en V375, si no cúmulo; 0 si no summit o fuera del inner)
Se cuentan además los cúmulos topados en 5,0 MW exactos (D9) y lo que MIROVA dio en esas pasadas.
Instrumento: si el tope no actuara nunca, E_rec = E_esc; el script imprime ambos (control: tiene que haber pasadas con
E_rec < E_esc si el tope actúa, y ninguna con E_rec > E_esc).
Uso: python -B seleccion.py pares_osf2025.csv
"""
import sys
import numpy as np, pandas as pd
KA = {"V375": 18.0 * 140625, "V750": 19.7 * 562500, "MODIS": 18.9 * 1e6}
d = pd.read_csv(sys.argv[1], parse_dates=["t"])
d = d[(d.pareo == "ok") & (d.cls == 1)].copy()
d["pub_ok"] = d.pub_ok.astype(str) == "True"
f5 = d.f5.where(d.b == "V375").fillna(0); pc = d.pc_vrp.fillna(0)
d["E_pub"] = np.where(d.pub_ok, np.where(f5 > 0, f5, pc), 0.0)
d["E_esc"] = d.dL_o * d.b.map(KA) / 1e6
d["E_rec"] = d.vrp_scene_o.fillna(0)
d["E_pc"] = pc
d["E_f5"] = np.where(f5 > 0, f5, pc)
d["tope"] = np.isclose(pc, 5.0)
d["tr"] = pd.cut(d.zen_M, [0, 40, 75], labels=["<=40", ">40"])
print("control del tope: pasadas con E_rec < E_esc - 1e-3:", int((d.E_rec < d.E_esc - 1e-3).sum()), "; con E_rec > E_esc + 1e-2:", int((d.E_rec > d.E_esc + 1e-2).sum()))
pd.set_option("display.width", 250)
t = d.groupby(["b", "vol", "tr"], observed=True).agg(n=("VRP_M", "size"), M=("VRP_M", "sum"), esc=("E_esc", "sum"), rec=("E_rec", "sum"),
                                                   pc=("E_pc", "sum"), f5=("E_f5", "sum"), pub=("E_pub", "sum"), n_tope=("tope", "sum"),
                                                   no_pub=("pub_ok", lambda x: int((~x).sum())))
for c in ["esc", "rec", "pc", "f5", "pub"]:
    t[c] = (t[c] / t.M).round(3)
t["M"] = t.M.round(1)
print("energías como fracción de la de MIROVA (sumas):")
print(t.to_string())
tp = d[d.tope]
print(f"\ncúmulos topados en 5,0 MW: {len(tp)}; VRP de MIROVA en esas pasadas: mediana {tp.VRP_M.median():.2f} MW, suma {tp.VRP_M.sum():.1f}; nuestra escena sin tope: mediana {tp.E_esc.median():.2f}")
print(tp.groupby(["b", "vol"]).agg(n=("VRP_M", "size"), M_med=("VRP_M", "median"), esc_med=("E_esc", "median"), tbg=("tbg", "median")).round(2).to_string())
