# -*- coding: utf-8 -*-
"""Cerca/lejos con el limite de alerta REAL de cada volcan (volcanes.py de Mirova-v1: Lastarria 3, Planchon Peteroa 3,
Copahue 4, Tupungatito 7, Puyehue Cordon Caulle 20, el resto 5 km), sobre el control completo: las pasadas de la tabla
de hasta 24,5 km (control_tabla.csv) MAS las de mas de 24,5 km (control_sobre_25km.csv), que el panel no dibuja.
Uso: python decision.py <carpeta_salidas>"""
import sys
import pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
SAL = sys.argv[1]
LIM = {"Lastarria": 3.0, "PlanchonPeteroa": 3.0, "Copahue": 4.0, "Tupungatito": 7.0, "PuyehueCordonCaulle": 20.0}
TOL = 0.6
a = pd.read_csv(f"{SAL}/control_tabla.csv")
a = a[a.dist <= 24.5]
b = pd.read_csv(f"{SAL}/control_sobre_25km.csv")
x = pd.concat([a.assign(grupo="<=24,5 km"), b.assign(grupo=">24,5 km")], ignore_index=True)


def decidir(r):
    U = LIM.get(r.vol, 5.0)
    if r.clase == "sin_marcador":
        return "sin_marcador"
    lo, hi = (r.est, r.est) if r.clase == "unico" else (r.kmin, r.kmax)
    if hi < U - TOL: return "cerca"
    if lo > U + TOL: return "lejos"
    return "indecidible"


x["dec"] = x.apply(decidir, axis=1)
x["real"] = [("cerca" if d <= LIM.get(v, 5.0) else "lejos") for d, v in zip(x.dist, x.vol)]
print(f"pasadas de control: {len(x)} (<=24,5 km {len(a)}, >24,5 km {len(b)}); ventana {x.t.min()} a {x.t.max()}")
print(pd.crosstab([x.real, x.grupo], x.dec, margins=True).to_string())
d = x[x.dec.isin(["cerca", "lejos"])]
mal = d[d.dec != d.real]
print(f"\ndecididas {len(d)} de {len(x)} ({100*len(d)/len(x):.1f} %); erradas {len(mal)} ({100*len(mal)/len(d):.1f} % de las decididas)")
print(f"   'cerca' decidido: {(d.dec=='cerca').sum()}, de las cuales eran lejos {((d.dec=='cerca')&(d.real=='lejos')).sum()} "
      f"(de ellas a mas de 24,5 km: {((d.dec=='cerca')&(d.real=='lejos')&(d.grupo=='>24,5 km')).sum()})")
print(f"   'lejos' decidido: {(d.dec=='lejos').sum()}, de las cuales eran cerca {((d.dec=='lejos')&(d.real=='cerca')).sum()}")
s = x[x.dec == "sin_marcador"]
print(f"\n'sin_marcador' {len(s)}: a mas de 24,5 km {(s.grupo=='>24,5 km').sum()}, lejos {(s.real=='lejos').sum()}")
print("\nerradas por volcan:", mal.groupby("vol").size().to_dict())
