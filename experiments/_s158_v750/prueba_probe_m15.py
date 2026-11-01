# -*- coding: utf-8 -*-
"""C-SIN del probe de M15 (S158): contador, relleno y cobertura sobre arreglos sinteticos, sin red.

Escena 6x6 con valores puestos a mano. Debe encontrar todos y solo los pixeles con M13 valido y M15 NaN, separarlos
por codigo, rellenar solo esos con la media de sus vecinos validos, y medir distancia cero de cobertura cuando hay un
pixel valido en la misma posicion geografica (duplicado del bowtie). Mutaciones: si el contador o el relleno
tocaran tambien pixeles con M13 NaN, o si el relleno usara el pixel perdido mismo, las aserciones fallan.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_m15 as pm  # noqa: E402


def escena():
    H = W = 6
    dn13 = np.full((H, W), 1000, dtype=np.int64)
    dn15 = np.full((H, W), 2000, dtype=np.int64)
    qf15 = np.zeros((H, W), dtype=np.int64)
    bt13 = np.full((H, W), 270.0)
    bt15 = np.full((H, W), 260.0)
    bt15[2, 3] = 266.0                      # vecino tibio, para que la media no sea trivial
    # (2,2): M15 bowtie, M13 sano -> perdido, codigo 65533
    dn15[2, 2] = 65533
    bt15[2, 2] = np.nan
    qf15[2, 2] = 256
    # (4,4): M15 sobre el techo -> perdido sin sentinela
    bt15[4, 4] = np.nan
    bt15c = bt15.copy()
    bt15c[4, 4] = 343.0
    # (0,5): M13 y M15 en sentinela -> NO es perdido de NTI (M13 tambien falta)
    dn13[0, 5] = 65533
    dn15[0, 5] = 65533
    bt13[0, 5] = np.nan
    bt15[0, 5] = np.nan
    bt13[3, 1] = 300.0                      # el mas caliente, con M15 valido
    lat = np.repeat(np.arange(H, dtype=float)[:, None], W, axis=1) * 0.01
    lon = np.repeat(np.arange(W, dtype=float)[None, :], H, axis=0) * 0.01
    lat[5, 0], lon[5, 0] = lat[2, 2], lon[2, 2]   # duplicado geografico de (2,2), valido en las dos bandas
    return dn13, dn15, qf15, bt13, bt15, bt15c, lat, lon


def main():
    dn13, dn15, qf15, bt13, bt15, bt15c, lat, lon = escena()
    ventana = np.ones_like(bt13, dtype=bool)
    c, perdido = pm.contar(dn13, dn15, qf15, bt13, bt15, bt15c, ventana)
    assert c["nti_perdido"] == 2, c
    assert set(zip(*np.nonzero(perdido))) == {(2, 2), (4, 4)}, np.nonzero(perdido)
    assert c["nti_perdido_por_codigo_m15"] == {"65533": 1}, c
    assert c["nti_perdido_sin_sentinela"] == 1, c
    assert c["m15_sentinela"] == {"65533": 2}, c
    assert c["m13_sentinela"] == {"65533": 1}, c
    assert c["m15_mask256_bowtie"] == 1 and c["m15_sobre_techo"] == 1, c
    assert c["m13_max_k"] == 300.0 and c["max_m13_nti_perdido"] is False, c
    r, n = pm.rellenar_m15(bt15, perdido)
    assert n == 2
    esperado = np.mean([260.0] * 7 + [266.0])   # 8 vecinos de (2,2), todos validos, uno tibio
    assert abs(r[2, 2] - esperado) < 1e-4, (r[2, 2], esperado)
    assert np.isnan(r[0, 5]), "relleno toco un pixel con M13 NaN"
    assert np.array_equal(np.isnan(r), np.isnan(bt15) & ~perdido), "relleno cambio algo fuera de los perdidos"
    valido = np.isfinite(bt13) & np.isfinite(bt15)
    cob = pm.cobertura(lat, lon, perdido, valido, ventana)
    assert cob["n"] == 2 and cob["dist_km"][0] == 0.0, cob   # (2,2) cubierto por su duplicado (5,0)
    assert cob["dist_km"][1] > 0.5, cob
    assert abs(cob["espaciado_validos_km_mediana"] - 1.112) < 0.01, cob   # paso de 0,01 grado; sin contarse a si mismo
    # mutacion: un contador que tomara todo M15 NaN como perdido daria 3, no 2
    mut = (~np.isfinite(bt15))
    assert int(mut.sum()) == 3 and int(perdido.sum()) == 2
    print("C-SIN OK", c["nti_perdido"], c["nti_perdido_por_codigo_m15"], round(float(r[2, 2]), 3), cob["dist_km"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
