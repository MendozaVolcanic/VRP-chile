# -*- coding: utf-8 -*-
"""O2-375: cuántas de las 422 escenas tienen celdas del hueco FUERA de la envolvente convexa de las celdas conocidas.

POR QUÉ. La regla de `fillmissing2` de S163 está verificada dentro de la envolvente (166 de 166, 84 de 84), pero la
extrapolación en el borde casi no está probada (reserva del verificador, rama s163-o2-alternativa c95483d31). Fuera de
la envolvente `rellenar` pone el vecino más cercano, y MATLAB podría hacer otra cosa. Sólo pesan las celdas de ALERTA,
porque L_bk suma el fondo nada más que ahí; el resto del hueco dilatado se informa también.

Qué hace. Mismo hueco que `vara_preliminar_375.vrp_regla` (alertas y NaN propios de la grilla, dilatados 3 x 3) en los
ejes de la regla (x = fila, y = columna); prueba de pertenencia con `scipy.spatial.Delaunay.find_simplex` (la envolvente
no depende de la triangulación). Después, la magnitud de V375-C (mediana vara/MIROVA en las positivas de 1 a 4 px) con
y sin esas escenas.
Uso: python -I envolvente_v375.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import numpy as np
import scipy.io as sio
from scipy.ndimage import binary_dilation
from scipy.spatial import Delaunay

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
N = 134
BRAZOS = ("M14", "C13", "C14", "C21", "M13", "M21", "PIX7", "SENS", "CIRC", "SENS_PT")


def main():
    S = sio.loadmat(AQUI / "entradas_v375.mat")
    E = json.loads((AQUI / "entradas_v375_etiquetas.json").read_text(encoding="utf-8"))["escenas"]
    vara = {e["posicion"]: e for e in json.loads((AQUI / "vara_preliminar_375.json").read_text(encoding="utf-8"))["escenas"]}
    RAD, ALE, NAL = S["RAD"], S["ALE"], np.ravel(S["NAL"])
    filas, cols = np.indices((N, N))
    fuera_ale, fuera_hueco, nan_grilla = {}, {}, 0
    for n, e in enumerate(E):
        idx = ALE[n, :NAL[n]].astype(int)
        mask = np.zeros((N, N), bool)
        mask[(idx - 1) % N, (idx - 1) // N] = True
        enm = RAD[:, :, n].astype(np.float64).copy()
        nan_grilla += int(np.isnan(enm).any())
        enm[mask] = np.nan
        hueco = binary_dilation(np.isnan(enm), structure=np.ones((3, 3), bool))
        ok = ~hueco
        P = np.column_stack([filas[ok], cols[ok]]).astype(float)
        tri = Delaunay(P)
        qa = np.column_stack([filas[mask], cols[mask]]).astype(float)
        qh = np.column_stack([filas[hueco], cols[hueco]]).astype(float)
        fa = int((tri.find_simplex(qa) < 0).sum())
        fh = int((tri.find_simplex(qh) < 0).sum())
        if fa:
            fuera_ale[e["posicion"]] = fa
        if fh:
            fuera_hueco[e["posicion"]] = fh
    print(f"escenas {len(E)}; con NaN propios en la grilla {nan_grilla}")
    print(f"con celdas de ALERTA fuera de la envolvente: {len(fuera_ale)} (las que pesan en L_bk)")
    print(f"con alguna celda del hueco dilatado fuera de la envolvente: {len(fuera_hueco)}")
    for pos in sorted(set(fuera_ale) | set(fuera_hueco)):
        e, v = E[pos], vara[pos]
        print(f"  pos {pos} id {e['id']} {e['volcan']} {e['hora_utc']} {e['clase']} npix {e['npix']} "
              f"alertas fuera {fuera_ale.get(pos, 0)} hueco fuera {fuera_hueco.get(pos, 0)} "
              f"pixeles {e['pixeles_fila_col']} vara/port {v['vrp_vara_mw'] / v['vrp_port_mw'] if v['vrp_port_mw'] else float('nan'):.4f}")
    excl = set(fuera_ale)
    print("\nmagnitud (mediana vara/MIROVA, positivas de 1 a 4 px): todas | sin las de alertas fuera de la envolvente")
    for b in BRAZOS:
        fil = [(e, vara[e["posicion"]]) for e in E if b in e["brazos"] and e["clase"].startswith("pos")
               and (e.get("mirova_vrp_mw") or 0) > 0]
        if not fil:
            continue
        r_all = [v["vrp_vara_mw"] / e["mirova_vrp_mw"] for e, v in fil]
        r_in = [v["vrp_vara_mw"] / e["mirova_vrp_mw"] for e, v in fil if e["posicion"] not in excl]
        print(f"  {b:7s} n {len(r_all):3d} {np.median(r_all):.3f} | n {len(r_in):3d} {np.median(r_in):.3f}")


if __name__ == "__main__":
    main()
