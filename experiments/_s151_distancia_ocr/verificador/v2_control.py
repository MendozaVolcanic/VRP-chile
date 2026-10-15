# -*- coding: utf-8 -*-
"""Punto 1: reproduce el control del estudio en el marco del verificador y mide caminos de falla.
Variantes: A estudio (calado con todas las conocidas, primera imagen 1-25 d despues)
           B calado SIN las pasadas conocidas de la noche de control (+-0.5 d)  [circularidad]
           C imagen MAS RECIENTE 1-25 d despues (lo que recomienda el par. 7 y usa el par. 5), calado como A
           D = B + C
Salida: v2/control_variantes.csv y stdout."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else __file__.rsplit("/", 1)[0])
from v2_comun import *
c, o, IMG = cargar()
tab = c[(c.Sensor == "VIIRS375") & (c.VRP_MW > 0) & c.Distancia_km.notna()][["vol", "t", "td", "Distancia_km", "Tipo_Registro"]].assign(f="tabla")
og = o[(o.Sensor == "VIIRS375") & (o.Fecha_Satelite_UTC >= "2026-06-13") & o.Distancia_km.notna() & (o.Tipo_Registro != "ALERTA_SIN_GEOMETRIA_OCR")][["vol", "t", "td", "Distancia_km", "Tipo_Registro"]].assign(f="ocr")
K = pd.concat([tab, og]).sort_values(["vol", "t", "f"]).reset_index(drop=True)
dup = (K.vol == K.vol.shift()) & ((K.t - K.t.shift()).dt.total_seconds().abs() < 180)
K = K[~dup].reset_index(drop=True)
print("conocidas", len(K), "tabla", (K.f == "tabla").sum())
CAL = {}
def cal_full(i):
    if i not in CAL:
        img = IMG.loc[i]; r = K[K.vol == img.vol]
        CAL[i] = calibrar(img, r.td.to_numpy(), r.Distancia_km.to_numpy())
    return CAL[i]
out = []
for r in tab.itertuples():
    g = IMG[(IMG.vol == r.vol) & (IMG.lmd >= r.td + 1) & (IMG.lmd <= r.td + 25)]
    if g.empty: continue
    otras = K[(K.vol == r.vol) & ((K.td - r.td).abs() <= W + 0.05) & ((K.td - r.td).abs() * 86400 > 180)].Distancia_km.to_list()
    for var in "ABCD":
        i = g.lmd.idxmin() if var in "AB" else g.lmd.idxmax()
        img = IMG.loc[i]
        if var in "AC":
            cb = cal_full(i)
        else:
            rr = K[(K.vol == r.vol) & ((K.td - r.td).abs() > 0.5)]
            cb = calibrar(img, rr.td.to_numpy(), rr.Distancia_km.to_numpy())
        tm = img.x + cb[2]
        pres = bool(((np.abs(tm - r.td) <= TOL_T) & (np.abs(img.km - min(r.Distancia_km, 25)) <= TOL_KM)).any())
        cl, est, kmin, kmax, n = eliminar(r.td, tm, img.km, otras)
        U = lim(r.vol)
        out.append(dict(var=var, vol=r.vol, t=r.t, tipo=r.Tipo_Registro, dist=r.Distancia_km, pres=pres, clase=cl, est=est,
                        kmin=kmin, kmax=kmax, n_col=n, pareos=cb[0], s=cb[2], dias_img=img.lmd - r.td,
                        dec=decidir(cl, est, kmin, kmax, U), real="cerca" if r.Distancia_km <= U else "lejos"))
X = pd.DataFrame(out)
X.to_csv("C:/Users/nmend/AppData/Local/Temp/claude/verifdist/v2/control_variantes.csv", index=False)
for var, F in X.groupby("var"):
    a = F[F.dist <= 24.5]
    u = a[a.clase == "unico"]; e = (u.est - u.dist.clip(upper=25)).abs()
    nu = a[a.clase.isin(["solapado", "ambiguo"])]
    dentro = ((nu.dist.clip(upper=25) >= nu.kmin - TOL_KM) & (nu.dist.clip(upper=25) <= nu.kmax + TOL_KM))
    d = F[F.dec.isin(["cerca", "lejos"])]; mal = d[d.dec != d.real]
    print(f"\n== variante {var}: control <=24,5 km n={len(a)}, total {len(F)}, dias imagen mediana {F.dias_img.median():.1f}")
    print(f"   dibujadas {a.pres.sum()} de {len(a)} ({100*a.pres.mean():.1f} %)")
    print(f"   unico n={len(u)} err mediana {e.median():.2f} p90 {e.quantile(.9):.2f} >2km {int((e>2).sum())} ({100*(e>2).mean():.1f} %)")
    print(f"   solap/ambig n={len(nu)} dentro {dentro.sum()} ({100*dentro.mean():.1f} %)")
    print(f"   decision: decididas {len(d)} de {len(F)} ({100*len(d)/len(F):.1f} %), erradas {len(mal)} ({100*len(mal)/max(len(d),1):.1f} %): cerca->lejos {((mal.real=='cerca')).sum()}, lejos->cerca {((mal.real=='lejos')).sum()}")
    print(f"   sin_marcador {(F.dec=='sin_marcador').sum()} (lejos {((F.dec=='sin_marcador')&(F.real=='lejos')).sum()})")
    # errores solo entre ALERTA (lo que se aplicara son alertas)
    al = d[d.tipo.str.startswith("ALERTA")]
    print(f"   solo ALERTA: decididas {len(al)}, erradas {(al.dec!=al.real).sum()} ({100*(al.dec!=al.real).mean():.1f} %); real lejos entre ALERTA decididas: {(al.real=='lejos').sum()}")
