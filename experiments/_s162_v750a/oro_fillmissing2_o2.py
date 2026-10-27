# -*- coding: utf-8 -*-
"""S162 V750-A: el fillmissing2 de la vía contra MATLAB R2026b en todas las escenas de O2 (vara completa).

POR QUÉ. La prueba de tests/ lleva 8 escenas; ésta recorre las 166 con alerta: VRP de pipeline/mirova_v750_codigo.py
contra el VRP de MATLAB (1e-12 relativo) y, en las que guardan la matriz de fondo (las 191 primeras), el fondo celda por
celda en el hueco. Control: el mismo recorrido con el fillmissing2 de Qhull (el del oráculo viejo) tiene que fallar en
varias, o el instrumento no distingue. El fondo se compara con el patrón de NaN de MATLAB (fuera de la envolvente MATLAB
no extrapola), no con nanmax, que se saltaba esas celdas y así dio por bueno un vecino más cercano en Etna.
Uso: python oro_fillmissing2_o2.py --o2 <carpeta con entradas_o2.mat y resultado_o2.mat de la rama s163-o2-paquete>
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np
import scipy.io as sio
from scipy.ndimage import binary_dilation

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "experiments/_s158_audit_r2/oraculo"))
import importlib  # noqa: E402
import mirova_v750_r2 as ORA  # noqa: E402

MD5_RESULTADO = "1f7fdc4bed0f8cb6223204bbce42ba43"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--o2", required=True, type=Path)
    ap.add_argument("--modulo", default="pipeline.mirova_v750_codigo", help="para el nulo: una copia mutada del módulo")
    a = ap.parse_args()
    MV = importlib.import_module(a.modulo)
    rp = a.o2 / "resultado_o2.mat"
    assert hashlib.md5(rp.read_bytes()).hexdigest() == MD5_RESULTADO, "resultado_o2.mat no es el de S163"
    S, R = sio.loadmat(a.o2 / "entradas_o2.mat"), sio.loadmat(rp)
    n_vrp = ok_vrp = n_bk = ok_bk = qh_mal = 0
    fuera = []
    peor = 0.0
    for k in range(S["M13"].shape[2]):
        al = R["ALERTAS"][k, 0].ravel().astype(int) - 1
        if al.size == 0:
            continue
        m13 = S["M13"][:, :, k].astype(float)
        mask = np.zeros(m13.shape, bool)
        mask.T.flat[al] = True                     # índices lineales de MATLAB, por columnas
        v = MV.vrp_mirova(m13, mask)
        rel = abs(v["VRP_MW"] / float(R["VRP"][k, 0]) - 1)
        peor = max(peor, rel)
        n_vrp += 1
        ok_vrp += rel < 1e-12
        bk = R["BK"][k, 0]
        if bk.size:
            enm = m13.copy()
            enm[mask] = np.nan
            kk = 3 if mask.sum() <= 4 else (5 if mask.sum() <= 30 else 7)
            enm[binary_dilation(np.isnan(enm), structure=np.ones((kk, kk), bool))] = np.nan
            h = np.isnan(enm)
            n_bk += 1
            Bm = MV._fillmissing2_lineal(enm)
            # el patrón de NaN tiene que ser el de MATLAB (no extrapola fuera de la envolvente); nanmax solo se lo salta
            ok_bk += bool(np.array_equal(np.isnan(Bm[h]), np.isnan(bk[h])) and np.nanmax(np.abs(Bm - bk)[h]) < 1e-12)
            qh_mal += np.nanmax(np.abs(ORA._fillmissing2_lineal(enm) - bk)[h]) > 1e-9
            # verificador de S163: la extrapolación (vecino más cercano fuera de la envolvente convexa de las celdas
            # con dato) casi no está probada; esas escenas se cuentan aparte, como NO CUBIERTAS por el oro
            from scipy.spatial import Delaunay
            fil, col = np.indices(enm.shape)
            dt = Delaunay(np.column_stack([fil[~h], col[~h]]).astype(float))
            n_fuera = int((dt.find_simplex(np.column_stack([fil[h], col[h]]).astype(float)) < 0).sum())
            if n_fuera:
                fuera.append((k, n_fuera))
    print(f"VRP igual a MATLAB (1e-12 relativo): {ok_vrp} de {n_vrp} | peor diferencia relativa {peor:.2e}")
    print(f"fondo igual a MATLAB celda por celda: {ok_bk} de {n_bk}")
    print(f"escenas con celdas del hueco FUERA de la envolvente convexa (MATLAB las deja en NaN): "
          f"{len(fuera)} {fuera} (en VIIRS 750 sólo Etna; VIIRS 375 y MODIS lo confirmaron con MATLAB real en 22 escenas)")
    print(f"control, fillmissing2 de Qhull: fondos distintos de MATLAB {qh_mal} de {n_bk} (tiene que ser más de 0)")
    bien = ok_vrp == n_vrp and ok_bk == n_bk and n_vrp >= 166 and n_bk >= 84 and qh_mal > 0
    print("== oro:", "VERDE" if bien else "ROJO")
    return 0 if bien else 1


if __name__ == "__main__":
    sys.exit(main())
