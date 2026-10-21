# -*- coding: utf-8 -*-
"""F3: ¿los píxeles de MIROVA son los nuestros más algunos más fríos, o son otros? Comparación a igual conteo.

POR QUÉ: la descomposición (analizar_pares.py) da que alertamos menos píxeles que MIROVA (R_N 0,75 cerca del nadir,
0,5 en oblicuo) pero más calientes (L_hot por píxel 1,12). Dos mecanismos físicos lo explican y predicen cosas distintas:
  H-halo (MIROVA suma vecinos más tibios del mismo foco: remuestreo lineal que reparte el foco, o segundo pase más
    sensible): entonces la SUMA de nuestros k = N_M píxeles más calientes ≈ la suma de MIROVA cuando tenemos >= k, y
    el píxel más caliente nuestro ≈ el de MIROVA cuando N_M = 1.
  H-suavizado (el remuestreo baja el pico): cuando N_M = 1 el L_hot de MIROVA es MENOR que nuestro píxel más caliente.
  H-fondo (el déficit es el fondo restado): L_bk por píxel distinto, L_hot igual.
Instrumento: (1) si el pareo estuviera roto, la razón de L_hot a igual k no tendría por qué estar cerca de 1: es su
propio control; (2) se reporta cuántas pasadas tienen n_nuestro >= N_M (si ninguna, SIN DATO).
Fondo: se compara el L_bk medio por píxel de MIROVA con nuestros dos fondos persistidos (anillo 5-25 km y kernel local).
Uso: python -B mismo_k.py <raiz> <pares_osf2025.csv>
"""
import json, os, sys
import numpy as np
import pandas as pd

ROOT, PARES = sys.argv[1], sys.argv[2]
C1, C2 = 1.191042e8, 14388.0
LAM = {"V375": 3.740, "V750": 4.050, "MODIS": 3.959}
pl = lambda bt, lam: C1 / (lam ** 5 * (np.exp(C2 / (lam * np.asarray(bt, float))) - 1))
def bucket(s):
    s = str(s or "").upper()
    return ("V750" if "750" in s else "V375") if "VIIRS" in s else "MODIS"

P = pd.read_csv(PARES, parse_dates=["t"])
P = P[(P.pareo == "ok") & (P.cls == 1) & (P.n_all > 0)]
recs = {}
for vol in P.vol.unique():
    d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", f"{vol}.json"), encoding="utf-8"))
    for r in (d.get("records", d) if isinstance(d, dict) else d):
        recs[(vol, bucket(r.get("sensor")), str(r.get("datetime_utc"))[:16])] = r
out = []
for _, m in P.iterrows():
    # el pareo original tomó el record más cercano; se reubica por (vol, sensor, minuto) con tolerancia de 5 min
    r = None
    for dm in range(0, 6):
        for s in (1, -1):
            k = (m.vol, m.b, (m.t + pd.Timedelta(minutes=s * dm)).strftime("%Y-%m-%d %H:%M"))
            if k in recs:
                r = recs[k]; break
        if r is not None:
            break
    if r is None:
        continue
    px = r.get("anomaly_pixels") or []
    if len(px) != (r.get("n_anomalous_pixels") or 0):
        continue
    Lh = np.sort(pl([p["bt_k"] for p in px], LAM[m.b]))[::-1]
    k = int(m.N_M)
    row = {"vol": m.vol, "b": m.b, "zen": m.zen_M, "N_M": k, "n_o": len(Lh),
           "Lhot_px_M": m.Lhot_M / k, "Lbk_px_M": m.Lbk_M / k,
           "Lbg_ring": r.get("diag_L_bg_w_m2_sr_um"), "Lbg_local": r.get("diag_L_bg_local_w_m2_sr_um"),
           "top1_o": Lh[0]}
    if len(Lh) >= k:
        row["topk_hot_ratio"] = Lh[:k].sum() / m.Lhot_M
        row["topk_exc_ratio_bgM"] = (Lh[:k].sum() - m.Lbk_M) / (m.Lhot_M - m.Lbk_M)
    out.append(row)
D = pd.DataFrame(out)
D["tr"] = pd.cut(D.zen, [0, 40, 75], labels=["<=40", ">40"])
print(f"pasadas clase 1 con píxeles listados completos: {len(D)}; con n_nuestro >= N_M: {D.topk_hot_ratio.notna().sum()}")
pd.set_option("display.width", 250)
print("\n(1) a igual conteo k = N_M: ΣL_hot de nuestros k más calientes / ΣL_hot MIROVA, y exceso con el fondo de MIROVA")
g = D.dropna(subset=["topk_hot_ratio"]).groupby(["b", "vol", "tr"], observed=True)
print(g.agg(n=("N_M", "size"), N_M=("N_M", "median"), hot=("topk_hot_ratio", "median"),
            exc=("topk_exc_ratio_bgM", "median")).round(3).to_string())
print("\n(2) N_M = 1 y nosotros >= 1: nuestro píxel más caliente / el único de MIROVA (L_hot), por sensor y tramo")
u = D[D.N_M == 1]
print(u.assign(r=u.top1_o / u.Lhot_px_M).groupby(["b", "tr"], observed=True).r.describe(percentiles=[.25, .5, .75]).round(3).to_string())
print("\n(3) fondo: L_bk medio por píxel de MIROVA / nuestro fondo de anillo (5-25 km) y / nuestro kernel local, por volcán (mediana)")
D["bgM_ring"] = D.Lbk_px_M / D.Lbg_ring
D["bgM_local"] = D.Lbk_px_M / D.Lbg_local
print(D.groupby(["b", "vol"]).agg(n=("N_M", "size"), n_local=("Lbg_local", lambda x: x.notna().sum()),
                                  bgM_ring=("bgM_ring", "median"), bgM_local=("bgM_local", "median")).round(3).to_string())
D.to_csv(os.path.join(os.path.dirname(PARES) or ".", "mismo_k_filas.csv"), index=False)
