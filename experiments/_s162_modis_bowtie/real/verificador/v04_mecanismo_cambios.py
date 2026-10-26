# -*- coding: utf-8 -*-
"""Verificador B3/B4: POR QUE cambia la publicacion o la magnitud al quitar duplicados, caso por caso.

Fenomeno. El detector del port es contextual: cada celda se compara con su vecindario 3 x 3 y con la media y la
desviacion del indice en TODA la grilla (51 x 51 km), y el fondo del VRP se rellena por triangulacion alrededor del
cumulo. Quitar pixeles nativos en el borde del barrido cambia la triangulacion del remuestreo y, con ella, celdas
lejos del crater; eso mueve mu y sigma y los umbrales (u_nti1 = max(mu + 10 sigma, 0,02); u_eti1 analogo). Asi que la
magnitud o la deteccion PUEDEN cambiar aunque el foco salga una sola vez. Aqui se mide, para cada pasada con
deteccion en 'todos' (13) y el caso 1093 que gana con C:
  - fraccion de pixeles nativos quitados por A_ant / A_sig; cuantos quitados caen en la caja ROI1 y a < 2,5 km de
    alguna celda alertada;
  - cuantas celdas de la grilla cambian de valor MIR en la caja ROI1 y en toda la grilla, y el max |dBT| en ROI1;
  - umbrales de la pasada 1 (u_nti1, u_eti1) con 'todos' y con cada A;
  - para cada celda alertada con 'todos': margen de la celda sobre el umbral en la pasada 1 (c_nti - u_nti1, en
    unidades de sigma_nti) con 'todos' y con A; si la celda deja de alertarse, cual test falla.
Pregunta 1: si la deteccion fuera insensible al remuestreo, los margenes no cambiarian; si cambiara solo por el
foco duplicado, las celdas cambiadas estarian todas a < 2,5 km del crater. Pregunta 2: en las pasadas donde A no
quita nada (nadir), todo tiene que salir identico (nulo por construccion, se imprime).
Denominador: 14 pasadas (13 con deteccion del port + 1093) del lote 40120713181.
Uso: python -I v04_mecanismo_cambios.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # comun.py del auditor
import numpy as np  # noqa: E402
import comun as CM  # noqa: E402

AQUI = Path(__file__).resolve().parent
ORA = CM.MP.ORA
CASOS = [19, 23, 31, 65, 75, 79, 83, 89, 97, 141, 147, 1120, 1251, 1093]
METS = ["A_centro_cubierto_ant", "A_centro_cubierto_sig"]


def contextual(mir, tir, box, dayflag, cfg):
    """Replica las lineas de ORA.detectar / _pasada_contextual necesarias para el margen de la pasada 1
    (mismo codigo, mismas lineas del .m citadas ahi). Devuelve c_nti, c_eti, diag de la pasada 1 y mascara p1."""
    with CM.MP.longitudes(cfg):
        m13 = np.asarray(mir, float)
        m15 = np.array(tir, float)
        box = np.array(box, float)
        box[:, [0, -1]] = np.nan
        box[[0, -1], :] = np.nan
        m0 = np.where(box == 0, 1.0, np.nan)
        m1 = np.where(box == 1, 1.0, np.nan)
        m2 = np.where(box == 2, 1.0, np.nan)
        excl = np.isnan(box)
        bt15 = ORA.radiancia_a_temperatura(m15, ORA.LAMBDA_M15)
        with np.errstate(invalid="ignore"):
            frio = bt15 <= 200
        bt15[frio] = np.nan
        m15[frio] = np.nan
        with np.errstate(invalid="ignore", divide="ignore"):
            nti = (m13 - m15) / (m13 + m15)
        nti_roi = nti.copy()
        nti_roi[excl] = np.nan
        if dayflag == 0:
            u_abs, s1, s2, n1, n2, e1, e2 = -0.7, 10, 5, 0.02, 0.003, 0.01, 0.003
        else:
            u_abs, s1, s2, n1, n2, e1, e2 = -0.5, 15, 15, 0.02, 0.02, 0.02, 0.02
        with np.errstate(invalid="ignore"):
            absol = nti_roi > u_abs
        pob = nti_roi.copy()
        pob[absol] = np.nan
        fondo_loc = ORA._media_3x3_omitnan(pob)
        fondo_loc[excl] = np.nan
        c_nti = pob - fondo_loc
        with np.errstate(invalid="ignore"):
            c_nti[c_nti < -0.1] = np.nan
        a0, a1, a2, diag = ORA._pasada_contextual(nti_roi, bt15, m15, excl, m0, m1, m2, absol, s1, s2, n1, n2, e1,
                                                  e2)
        m13_esp = ORA.temperatura_a_radiancia(bt15, ORA.LAMBDA_M13)
        with np.errstate(invalid="ignore", divide="ignore"):
            nti_esp = (m13_esp - m15) / (m13_esp + m15)
        nti_esp[absol] = np.nan
        nti_esp[excl] = np.nan
        c_eti = np.full_like(c_nti, np.nan)
        if "coef" in diag:
            ref = np.polyval(np.array(diag["coef"]), nti_esp)
            eti = pob - ref
            c_eti = eti - ORA._media_3x3_omitnan(eti)
            c_eti[excl] = np.nan
    return c_nti, c_eti, diag, (a0 | a1 | a2), box


def main():
    pr, L = CM.pr_factory()
    obj, res = CM.objetivos(), CM.resultados()
    cfg = CM.MP.SENSORES["MODIS"]
    resumen = []
    for i in CASOS:
        o, r, g = obj[i], res[i], obj[i]["grilla"]
        n = CM.cargar_nativo(i)
        G = CM.geometria(n, g["epsg"])
        X, Y = CM.MP.centros(g)
        roi1 = (np.abs(X - g["X0"]) <= CM.MP.HALF_ROI1_M) & (np.abs(Y - g["Y0"]) <= CM.MP.HALF_ROI1_M)
        mir0, tir0 = CM.PP.grillar(CM.crop_desde_nativo(n), g, g["epsg"])
        p0 = CM.MP.correr(mir0, tir0, g, g["X0"], g["Y0"], r["dayflag"], r["sunglint"], cfg, modo="fisica",
                          semillas=0)
        box = CM.MP.caja(g, g["X0"], g["Y0"], "fisica")
        cn0, ce0, d0, m10, _ = contextual(mir0, tir0, box, r["dayflag"], cfg)
        with CM.MP.longitudes(cfg):
            bt0 = ORA.radiancia_a_temperatura(np.asarray(mir0, float), cfg["lam_mir"])
        celdas0 = [tuple(q[:2]) for q in p0["pixeles"]]
        pr(f"\n== {i} {o['volcan']} {o['hora_utc']} z {o['z']:.1f} clase {o['clase']} MIROVA {o['mirova_vrp']} | todos: "
           f"npix {p0['npix']} VRP {p0['vrp_mw']} celdas {celdas0} | u_nti1 {d0['u_nti1']:.5f} (mu {d0['mu_nti']:.5f} "
           f"sd {d0['sd_nti']:.5f}) u_eti1 {d0.get('u_eti1', float('nan')):.5f} (sd_e {d0.get('sd_eti', float('nan')):.5f})")
        for m in METS:
            q = CM.mascara_quitar(G, m)
            mir, tir = CM.PP.grillar(CM.crop_desde_nativo(n, q), g, g["epsg"])
            p = CM.MP.correr(mir, tir, g, g["X0"], g["Y0"], r["dayflag"], r["sunglint"], cfg, modo="fisica",
                             semillas=0)
            cn, ce, d, m1, _ = contextual(mir, tir, box, r["dayflag"], cfg)
            with CM.MP.longitudes(cfg):
                bt = ORA.radiancia_a_temperatura(np.asarray(mir, float), cfg["lam_mir"])
            # pixeles nativos quitados: donde caen
            qq = q & np.isfinite(G["x"])
            dcr = np.hypot(G["x"] - g["X0"], G["y"] - g["Y0"])
            en_roi1 = qq & (np.abs(G["x"] - g["X0"]) <= CM.MP.HALF_ROI1_M) & (np.abs(G["y"] - g["Y0"]) <= CM.MP.HALF_ROI1_M)
            cerca = np.zeros_like(qq)
            for (a, b) in celdas0:
                cerca |= np.hypot(G["x"] - X[a, b], G["y"] - Y[a, b]) < 2500
            # celdas de la grilla que cambian
            camb = ~np.isclose(mir, mir0, equal_nan=True)
            dbt = np.abs(bt - bt0)
            celdas = [tuple(qv[:2]) for qv in p["pixeles"]]
            ratio = (p["vrp_mw"] / p0["vrp_mw"]) if (p["vrp_mw"] and p0["vrp_mw"]) else None
            pr(f"   {m:22s} npix {p['npix']} VRP {p['vrp_mw']} ratio {ratio if ratio is None else round(ratio, 3)} "
               f"celdas {celdas}")
            pr(f"      quitados: {int(qq.sum())} de {int(np.isfinite(G['x']).sum())} nativos ({qq.mean():.3f}); en caja "
               f"ROI1: {int(en_roi1.sum())}; a < 2,5 km de una celda alertada: {int((qq & cerca).sum())}; "
               f"quitado mas cercano al crater: {np.nanmin(np.where(qq, dcr, np.nan)) / 1000 if qq.any() else float('nan'):.2f} km")
            pr(f"      celdas de la grilla con MIR distinto: {int(camb.sum())} de {camb.size} (en ROI1 {int((camb & roi1).sum())} de "
               f"{int(roi1.sum())}); max |dBT| en ROI1 {np.nanmax(np.where(roi1, dbt, np.nan)):.3f} K; "
               f"max |dBT| en celdas alertadas {max([dbt[a, b] for (a, b) in celdas0], default=float('nan')):.3f} K")
            pr(f"      umbrales p1: u_nti1 {d['u_nti1']:.5f} (mu {d['mu_nti']:.5f} sd {d['sd_nti']:.5f}) "
               f"u_eti1 {d.get('u_eti1', float('nan')):.5f} (sd_e {d.get('sd_eti', float('nan')):.5f})")
            for (a, b) in sorted(set(celdas0) | set(celdas)):
                est = ("alerta" if (a, b) in celdas0 else "no") + "->" + ("alerta" if (a, b) in celdas else "no")
                pr(f"      celda ({a},{b}) {est:12s} BT {bt0[a, b]:.2f}->{bt[a, b]:.2f} K | c_nti {cn0[a, b]:+.5f}->{cn[a, b]:+.5f} "
                   f"(u1 {d0['u_nti1']:.5f}->{d['u_nti1']:.5f}) | c_eti {ce0[a, b]:+.5f}->{ce[a, b]:+.5f} "
                   f"(u1 {d0.get('u_eti1', float('nan')):.5f}->{d.get('u_eti1', float('nan')):.5f}) | p1 {bool(m10[a, b])}->{bool(m1[a, b])}")
            resumen.append((i, m, o["z"], int(qq.sum()), int(en_roi1.sum()), int((qq & cerca).sum()),
                            int((camb & roi1).sum()), p0["npix"], p["npix"], ratio))
    pr("\n== resumen (id, metodo, z, quitados, quitados en ROI1, quitados a <2,5 km de alertada, celdas ROI1 cambiadas, "
       "npix todos, npix metodo, ratio VRP)")
    for t in resumen:
        pr("  ", t)
    (AQUI / "v04_mecanismo_cambios_salida.txt").write_bytes(("\n".join(L) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
