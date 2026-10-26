# -*- coding: utf-8 -*-
"""Reproduce M con la regla de MATLAB (78 pares, mediana d) y mide P1b bajo esa regla en TODAS las protegidas que K y
PM publican (no solo la de Lascar 2026-04-25 07:35). Importa las funciones del candado; no escribe en censo/."""
import json, math, statistics, sys
from pathlib import Path
import numpy as np
AQUI = Path("C:/vrp-trabajo/s162-modd/experiments/_s162_modis_paquete")
sys.path.insert(0, str(AQUI))
import evaluar_paquete as EP
import m_con_regla_matlab as MR
ART = "D:/vrp-trabajo/temporales/s162_modd/censo"
OUT = Path("D:/vrp-trabajo/temporales/s162_modd/verificador_censo")
pob = json.load(open(EP.POBLACION, encoding="utf-8"))
grillas = json.load(open(EP.GRILLAS, encoding="utf-8"))
crudas, recorridos, cab = EP.cargar(ART)
filas, _u, _e = EP.unir(crudas, pob)
for f in filas:
    f["_evaluable"], f["_motivo"] = EP.evaluable(f)
EP.armar_tabla(filas, grillas)
gid = MR.grillas_por_id(ART)
P, sin_g, no_pos = MR.pares_con_regla(filas, gid)
res = {"m_regla": MR.m_regla(P), "n_sin_grilla": len(sin_g), "no_positivo": no_pos, "n_grillas": len(gid)}
# P1b bajo la regla, en todas las protegidas con K y PM publicando
baja, sube, lista = [], [], []
for f in EP._ev(filas):
    if f["lab"] != "protegida" or not (EP._pub(f, "K") == 1 and EP._pub(f, "PM") == 1):
        continue
    mir = np.load(gid[f["id"]])["mir"].astype(float)
    v = MR.vrp_con(mir, MR.mascara(f["port"]["fisica"]["pixeles"], mir.shape), MR.regla)
    k, d = EP._mag(f, "K"), EP._mag(f, "PM")
    lista.append((f["vol"], f["dt"], k, d, round(v, 4), f["port"]["fisica"]["npix"], f.get("vrp_mirova")))
    if k >= 1.0 > v:
        baja.append(lista[-1])
    elif k < 1.0 <= v:
        sube.append(lista[-1])
res["p1b_con_regla"] = {"n_pares_protegidas": len(lista), "baja": baja, "n_sube": len(sube),
                        "cambian_de_lado_respecto_al_port": [x for x in lista if (x[3] >= 1.0) != (x[4] >= 1.0)]}
# identidad: con el relleno del port, la misma construccion da la magnitud del PM en todos los pares
sys.path.insert(0, str(EP.RAIZ / "experiments/_s159/portes"))
import mirova_port as MP
peor = 0.0
for p in P:
    f = next(x for x in filas if x["vol"] == p["vol"] and x["dt"] == p["clave"].split("|")[-1])
    mir = np.load(gid[f["id"]])["mir"].astype(float)
    vp = MR.vrp_con(mir, MR.mascara(f["port"]["fisica"]["pixeles"], mir.shape), MP.ORA._fillmissing2_lineal)
    peor = max(peor, abs(vp - f["port"]["fisica"]["vrp_mw"]))
res["identidad_port_peor_abs"] = peor
OUT.joinpath("p1b_regla_salida.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
