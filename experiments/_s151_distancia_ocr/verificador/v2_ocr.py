# -*- coding: utf-8 -*-
"""Punto 2: las distancias que el OCR SI midio (Distancia_km > 0) contra la lectura por serie de tiempo de Dist.png.
VIIRS 375 (la muestra archivada es solo VIIRS 375). Calado SOLO con pasadas de la TABLA (no se usa ninguna distancia
OCR para calar ni para eliminar: la que se evalua es OCR). Imagen: la primera 1-25 d despues (A) y la mas reciente (C).
Por fila: (1) duplicado en la tabla (+-3 min) -> distancia de la tabla; (2) hay marcador en su columna a +-0,6 km de
la distancia OCR; (3) estimacion por eliminacion con las pasadas de la tabla de esa noche; (4) firma "otra pasada":
la distancia OCR coincide (+-0,3 km) con una pasada de la tabla 0,005 a 1,5 d POSTERIOR, o con un marcador en una
columna posterior (0,15 a 3 d) y no con uno de la propia columna."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else __file__.rsplit("/", 1)[0])
from v2_comun import *
c, o, IMG = cargar()
tab = c[(c.Sensor == "VIIRS375") & (c.VRP_MW > 0) & c.Distancia_km.notna()][["vol", "t", "td", "Distancia_km", "Tipo_Registro"]]
tab_all = c[(c.Sensor == "VIIRS375") & c.Distancia_km.notna()][["vol", "t", "td", "Distancia_km", "VRP_MW"]]
med = o[(o.Distancia_km > 0)].copy()
print("filas OCR con distancia > 0:", len(med), "| por sensor", med.Sensor.value_counts().to_dict())
cortes = [("2026-06-11", "1 <06-11"), ("2026-06-13", "2 06-11..12"), ("2026-08-06", "3 06-13..08-05"), ("2026-10-09", "4 08-06..10-08"), ("9999", "5 >=10-09")]
med["tramo"] = med.Fecha_Satelite_UTC.map(lambda f: next(n for c_, n in cortes if f[:10] < c_))
CAL = {}
def cal(i):
    if i not in CAL:
        img = IMG.loc[i]; r = tab[tab.vol == img.vol]
        CAL[i] = calibrar(img, r.td.to_numpy(), r.Distancia_km.to_numpy())
    return CAL[i]
out = []
for r in med.itertuples():
    U = lim(r.vol); d0 = r.Distancia_km
    dd = (tab_all.vol == r.vol) & ((tab_all.td - r.td).abs() * 86400 < 180)
    d_tab = tab_all[dd].Distancia_km.iloc[0] if dd.any() else np.nan
    later = tab[(tab.vol == r.vol) & (tab.td - r.td > 0.005) & (tab.td - r.td <= 1.5)]
    otra_tab = bool((np.abs(later.Distancia_km - d0) <= 0.3).any())
    # la propia pasada en la tabla con distancia igual
    row = dict(vol=r.vol, t=r.t, sensor=r.Sensor, tipo=r.Tipo_Registro, tramo=r.tramo, ocr=d0, vrp=r.VRP_MW, d_tab=d_tab,
               otra_tab=otra_tab, real_ocr="cerca" if d0 <= U else "lejos")
    if r.Sensor != "VIIRS375":
        out.append(row); continue
    g = IMG[(IMG.vol == r.vol) & (IMG.lmd >= r.td + 1) & (IMG.lmd <= r.td + 25)]
    if g.empty:
        out.append(row); continue
    otras = tab[(tab.vol == r.vol) & ((tab.td - r.td).abs() <= W + 0.05) & ((tab.td - r.td).abs() * 86400 > 180)].Distancia_km.to_list()
    for var, i in (("A", g.lmd.idxmin()), ("C", g.lmd.idxmax())):
        img = IMG.loc[i]; cb = cal(i); tm = img.x + cb[2]
        incol = np.abs(tm - r.td) <= W
        pres = bool((incol & (np.abs(img.km - min(d0, 25)) <= TOL_KM)).any())
        post = (tm - r.td > W) & (tm - r.td <= 3)
        pres_post = bool((post & (np.abs(img.km - min(d0, 25)) <= 0.3)).any())
        cl, est, kmin, kmax, n = eliminar(r.td, tm, img.km, otras)
        dec = decidir(cl, est, kmin, kmax, U)
        row.update({f"{var}_pres": pres, f"{var}_prespost": pres_post, f"{var}_clase": cl, f"{var}_est": est, f"{var}_kmin": kmin,
                    f"{var}_kmax": kmax, f"{var}_ncol": n, f"{var}_dec": dec, f"{var}_pareos": cb[0], f"{var}_kmcol": sorted(np.round(img.km[incol], 2).tolist())})
    out.append(row)
X = pd.DataFrame(out)
X.to_csv("C:/Users/nmend/AppData/Local/Temp/claude/verifdist/v2/ocr_vs_serie.csv", index=False)

def resumen(X, var):
    print(f"\n######## imagen {'PRIMERA 1-25 d' if var=='A' else 'MAS RECIENTE 1-25 d'} (variante {var})")
    print("tramo | n | VIIRS375 | con imagen | dup tabla (err OCR-tabla med/p90, >2km) | marcador en su columna a la dist OCR | unico n, err med/p90, >2km | intervalo contiene OCR | lado: decididas, cambian | firma otra pasada (tabla posterior / marcador posterior sin propio)")
    for tr, g in X.groupby("tramo"):
        v = g[g.sensor == "VIIRS375"]; ci = v[v[f"{var}_clase"].notna()] if f"{var}_clase" in v else v.iloc[0:0]
        dt = g[g.d_tab.notna()]; edt = (dt.ocr - dt.d_tab).abs()
        u = ci[ci[f"{var}_clase"] == "unico"]; eu = (u.ocr.clip(upper=25) - u[f"{var}_est"]).abs()
        nu = ci[ci[f"{var}_clase"].isin(["solapado", "ambiguo"])]
        den = ((nu.ocr.clip(upper=25) >= nu[f"{var}_kmin"] - TOL_KM) & (nu.ocr.clip(upper=25) <= nu[f"{var}_kmax"] + TOL_KM))
        dc = ci[ci[f"{var}_dec"].isin(["cerca", "lejos"])]; camb = dc[dc[f"{var}_dec"] != dc.real_ocr]
        nopres = ci[~ci[f"{var}_pres"].astype(bool)]
        firma = nopres[nopres[f"{var}_prespost"].astype(bool) | nopres.otra_tab]
        print(f"{tr} | {len(g)} | {len(v)} | {len(ci)} | {len(dt)} ({edt.median():.2f}/{edt.quantile(.9):.2f}, {int((edt>2).sum())}) | "
              f"{int(ci[f'{var}_pres'].sum()) if len(ci) else 0}/{len(ci)} | {len(u)}, {eu.median():.2f}/{eu.quantile(.9):.2f}, {int((eu>2).sum())} | "
              f"{int(den.sum())}/{len(nu)} | {len(dc)}, {len(camb)} (cerca->lejos {int((camb.real_ocr=='cerca').sum())}, lejos->cerca {int((camb.real_ocr=='lejos').sum())}) | "
              f"{len(firma)} de {len(nopres)} sin marcador propio (tabla posterior {int(nopres.otra_tab.sum())}, marcador posterior {int(nopres[f'{var}_prespost'].astype(bool).sum())})")
        print(f"      sin_marcador {int((ci[f'{var}_clase']=='sin_marcador').sum())}, indecidible {int((ci[f'{var}_dec']=='indecidible').sum())}; tipos {g.tipo.value_counts().to_dict()}")
for var in "AC":
    resumen(X, var)
# discrepancia >2 km por fila, en todas las clases (|ocr - est| unico, o fuera del intervalo por >2 km)
def disc(r, var):
    cl = r[f"{var}_clase"]
    if cl == "unico": return abs(min(r.ocr, 25) - r[f"{var}_est"])
    if cl in ("solapado", "ambiguo"):
        o_ = min(r.ocr, 25); return max(0, r[f"{var}_kmin"] - o_, o_ - r[f"{var}_kmax"])
    return np.nan
for var in "AC":
    Y = X[X.get(f"{var}_clase").notna()].copy(); Y["disc"] = Y.apply(lambda r: disc(r, var), axis=1)
    print(f"\n[{var}] distancia OCR fuera de la lectura de la serie (km; unico=|dif|, intervalo=distancia al intervalo) por tramo:")
    for tr, g in Y.groupby("tramo"):
        dd = g.disc.dropna()
        print(f"   {tr}: n={len(dd)} mediana {dd.median():.2f} p90 {dd.quantile(.9):.2f} >2km {int((dd>2).sum())} ({100*(dd>2).mean():.1f} %); de las >2km, con firma otra pasada {int(((g.disc>2)&(g.otra_tab|g[f'{var}_prespost'].astype(bool))).sum())}")
