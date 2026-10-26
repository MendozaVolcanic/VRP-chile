# -*- coding: utf-8 -*-
"""Prueba del paquete O2-375 antes de mandarlo a MATLAB: lee `entradas_v375.mat` como lo lee MATLAB y comprueba que cada
escena es la del port.

Las dos preguntas del instrumento. (1) Si los índices estuvieran mal (fila por columna, base 0 en vez de 1, otra escena),
los píxeles decodificados no serían los del port y la radiancia caliente no daría la del port: se exigen 422 de 422
iguales. Control negativo: la misma cuenta con los índices leídos en orden de fila (el error típico) tiene que fallar.
(2) Que el fondo del port, recalculado aquí sobre la radiancia guardada, dé el VRP del port a 1e-6 MW: prueba que el
paquete trae la misma grilla que midió el port (float32), no otra.
Uso: python -I probar_paquete_375.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import numpy as np
import scipy.io as sio

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import brazos as BR  # noqa: E402

ORA, MP = BR.ORA, BR.MP
N = 134
COEF_375 = 1.80e7 * 0.140625 / 1e6      # MW por unidad de ΔL (CLAUDE.md «Reglas científicas»)


def main():
    S = sio.loadmat(AQUI / "entradas_v375.mat")
    E = json.loads((AQUI / "entradas_v375_etiquetas.json").read_text(encoding="utf-8"))["escenas"]
    RAD, ALE, NAL = S["RAD"], S["ALE"], np.ravel(S["NAL"])
    K = RAD.shape[2]
    assert K == len(E) and RAD.shape[:2] == (N, N), (RAD.shape, len(E))
    ok_pix = ok_hot = ok_vrp = mal_fila = 0
    peor = 0.0
    for n, e in enumerate(E):
        idx = ALE[n, :NAL[n]].astype(int)
        filas, cols = (idx - 1) % N, (idx - 1) // N              # columna mayor, base 1
        pix = sorted(zip(filas.tolist(), cols.tolist()))
        ok_pix += pix == [tuple(p) for p in e["pixeles_fila_col"]]
        rad = RAD[:, :, n].astype(np.float64)
        ok_hot += abs(float(rad[filas, cols].sum()) - e["l_hot_port"]) < 1e-9
        fr, cr = (idx - 1) // N, (idx - 1) % N                   # control negativo: leído en orden de fila
        mal_fila += sorted(zip(fr.tolist(), cr.tolist())) != [tuple(p) for p in e["pixeles_fila_col"]]
        mask = np.zeros((N, N), bool)
        mask[filas, cols] = True
        r = ORA.vrp(rad, mask)
        v = r["deltaL"] * COEF_375
        d = abs(v - e["vrp_port_mw"])
        peor = max(peor, d)
        ok_vrp += d < 1e-6
    print(f"escenas {K}: píxeles iguales al port {ok_pix}; radiancia caliente igual {ok_hot}; VRP del fondo del port "
          f"igual a 1e-6 MW {ok_vrp} (peor diferencia {peor:.2e} MW)")
    print(f"control negativo (índices leídos en orden de fila): escenas que dejan de calzar {mal_fila} de {K}")
    print("Etna:", {k: np.ravel(S[k]).shape for k in ("ETNA_M13", "ETNA_M15", "ETNA_BOX")},
          "DAY", float(np.ravel(S["ETNA_DAY"])[0]), "SG", round(float(np.ravel(S["ETNA_SG"])[0]), 2))
    assert ok_pix == ok_hot == ok_vrp == K, "el paquete no reproduce al port"
    assert mal_fila > 0.5 * K, "el control negativo no falla: la prueba no distingue el orden de los índices"
    print("PAQUETE O2-375 OK")


if __name__ == "__main__":
    main()
