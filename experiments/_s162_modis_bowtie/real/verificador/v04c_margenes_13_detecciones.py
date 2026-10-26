# -*- coding: utf-8 -*-
"""Verificador B3/B4: cuan al filo del umbral esta cada deteccion del port ('todos') y como queda con A_ant y A_sig.

Para cada una de las 13 pasadas con deteccion y cada metodo, replica las dos pasadas contextuales del oraculo y mide,
por celda alertada, el margen minimo (c - u) sobre el umbral que la alerto (pasada 1 o 2, con el umbral de su caja:
ROI1 usa u_*1, ROI2 usa u_*2), y por celda NO alertada de la caja ROI1/ROI2 el margen maximo (que tan cerca estuvo de
entrar). Un margen de 1e-5 en NTI es ruido de remuestreo (A_sig movio sigma global 3e-6 en el caso 79).
Tambien cuenta, para A_ant y A_sig: celdas que entran o salen, y si la celda que cambia tenia |margen| < 1e-4 en 'todos'.
Pregunta 1: si las detecciones fueran robustas, los margenes minimos serian >> 1e-3 y A no las moveria. Pregunta 2:
en las pasadas donde A no quita nada, los margenes son identicos (se imprime).
Denominador: 13 pasadas con deteccion del port en el lote 40120713181 (11 protegidas + 1120 + 1251).
Uso: python -I v04c_margenes_13_detecciones.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np  # noqa: E402
import comun as CM  # noqa: E402

AQUI = Path(__file__).resolve().parent
ORA = CM.MP.ORA
CASOS = [19, 23, 31, 65, 75, 79, 83, 89, 97, 141, 147, 1120, 1251]
METS = ["todos", "A_centro_cubierto_ant", "A_centro_cubierto_sig"]


def margenes(mir, tir, box, dayflag, cfg):
    """Replica ORA.detectar (dos pasadas) y devuelve mascara final y, por celda, el margen de la pasada que la
    alerto (o el mejor margen de las dos si no se alerto), con el umbral de su caja."""
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
        u_abs, s1, s2, n1, n2, e1, e2 = (-0.7, 10, 5, 0.02, 0.003, 0.01, 0.003) if dayflag == 0 else \
            (-0.5, 15, 15, 0.02, 0.02, 0.02, 0.02)
        with np.errstate(invalid="ignore"):
            absol = nti_roi > u_abs
        m13_esp = ORA.temperatura_a_radiancia(bt15, ORA.LAMBDA_M13)
        with np.errstate(invalid="ignore", divide="ignore"):
            nti_esp0 = (m13_esp - m15) / (m13_esp + m15)

        def una_pasada(exc):
            p = ORA._pasada_contextual(nti_roi, bt15, m15, excl, m0, m1, m2, exc, s1, s2, n1, n2, e1, e2)
            pob = nti_roi.copy()
            pob[exc] = np.nan
            fondo_loc = ORA._media_3x3_omitnan(pob)
            fondo_loc[excl] = np.nan
            c_nti = pob - fondo_loc
            with np.errstate(invalid="ignore"):
                c_nti[c_nti < -0.1] = np.nan
            nti_esp = nti_esp0.copy()
            nti_esp[exc] = np.nan
            nti_esp[excl] = np.nan
            d = p[3]
            if "coef" not in d:
                return p, np.full(nti.shape, np.nan)
            ref = np.polyval(np.array(d["coef"]), nti_esp)
            eti = pob - ref
            c_eti = eti - ORA._media_3x3_omitnan(eti)
            c_eti[excl] = np.nan
            # margen por celda = min(c_nti - u_nti, c_eti - u_eti) con el umbral de su caja (1: ROI1 y fuera; 2: ROI2)
            u_n = np.where(box == 2, d["u_nti2"], d["u_nti1"])
            u_e = np.where(box == 2, d["u_eti2"], d["u_eti1"])
            marg = np.minimum(c_nti - u_n, c_eti - u_e)
            return p, marg

        p1, marg1 = una_pasada(absol)
        ctx1 = p1[0] | p1[1] | p1[2]
        p2, marg2 = una_pasada(absol | ctx1)
        ctx2 = p2[0] | p2[1] | p2[2]
        mask = ctx1 | absol | ctx2
        # margen de la celda: si alerto en p1, marg1; si alerto en p2, marg2; si no, el max de ambas (lo mas cerca)
        marg = np.where(ctx1, marg1, np.where(ctx2, marg2, np.fmax(marg1, marg2)))
        return mask, marg, absol


def main():
    pr, L = CM.pr_factory()
    obj, res = CM.objetivos(), CM.resultados()
    cfg = CM.MP.SENSORES["MODIS"]
    pr("id   volcan             z     metodo                  npix  min margen alertadas | max margen no alertadas (ROI) | "
       "entran / salen vs todos [celda: margen en todos]")
    filo = 0
    for i in CASOS:
        o, r, g = obj[i], res[i], obj[i]["grilla"]
        n = CM.cargar_nativo(i)
        G = CM.geometria(n, g["epsg"])
        box = CM.MP.caja(g, g["X0"], g["Y0"], "fisica")
        roi = box >= 1
        base = None
        for m in METS:
            q = CM.mascara_quitar(G, m)
            mir, tir = CM.PP.grillar(CM.crop_desde_nativo(n, q), g, g["epsg"])
            mask, marg, absol = margenes(mir, tir, box, r["dayflag"], cfg)
            al = mask & ~absol
            mn = float(np.nanmin(marg[al])) if al.any() else float("nan")
            mx = float(np.nanmax(marg[roi & ~mask])) if (roi & ~mask).any() else float("nan")
            if m == "todos":
                base = (mask.copy(), marg.copy())
                cambios = ""
            else:
                entran = [tuple(map(int, c)) for c in np.argwhere(mask & ~base[0])]
                salen = [tuple(map(int, c)) for c in np.argwhere(base[0] & ~mask)]
                cambios = f"entran {[(c, round(float(base[1][c]), 6)) for c in entran]} salen {[(c, round(float(base[1][c]), 6)) for c in salen]}"
                filo += sum(abs(base[1][c]) < 1e-4 for c in entran + salen)
            pr(f"{i:5d} {o['volcan']:18s} {o['z']:5.1f} {m:22s} {int(mask.sum()):4d}  {mn:+.6f} | {mx:+.6f} | {cambios}")
    pr(f"\ncelulas que entran o salen con A_ant o A_sig cuyo |margen| en 'todos' era < 1e-4 (filo del umbral): {filo}")
    (AQUI / "v04c_margenes_13_detecciones_salida.txt").write_bytes(("\n".join(L) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
