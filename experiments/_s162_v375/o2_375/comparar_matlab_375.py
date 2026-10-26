# -*- coding: utf-8 -*-
"""O2-375, prueba de oro: el fondo del VRP de MIROVA calculado por MATLAB (resultado_v375.mat, R2026b, corrida de S163
sobre el paquete de 138a931ee) contra la vara PRELIMINAR (vara_preliminar_375.json) y contra el port, escena por escena.

POR QUÉ. La vara reproduce `fillmissing2` con una regla escrita en Python (Delaunay perturbado de S163). Sólo MATLAB dice
qué hace `fillmissing2` de verdad en estas 422 escenas de 1 a 4 píxeles. Si la vara calza con MATLAB, deja de ser
preliminar; si no, la magnitud de V375-C se re-mide con MATLAB.

Las dos preguntas del instrumento. (1) Control positivo de la corrida: Etna da Tot_Lmir_bk 1,072886152 y la radiancia
caliente de MATLAB (LHOT) es la del port en las 422 (si los índices se hubieran leído mal no calzaría). (2) Control de que
la comparación puede fallar: MATLAB contra el FONDO DEL PORT tiene que dar diferencias en las escenas en que la vara ya
difería del port (137); si diera 0, la comparación no estaría mirando el fondo.
Además escribe matlab_v375.json con el formato de la vara (`vrp_vara_mw` = ΔL de MATLAB x 1,80e7 x 0,140625 / 1e6), para
`evaluar.py --vrp-vara`.
Uso: python -I comparar_matlab_375.py
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import scipy.io as sio

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
COEF_375 = 1.80e7 * 0.140625 / 1e6
COEF_750 = 1.97e7 * 0.5625 / 1e6
TOL_REL = 1e-9      # ΔL relativo: aritmética de doble precisión, no otra triangulación (O2: hasta 0,82 relativo)


def main():
    R = sio.loadmat(AQUI / "resultado_v375.mat", squeeze_me=True, struct_as_record=False)
    print("resultado_v375.mat md5", hashlib.md5((AQUI / "resultado_v375.mat").read_bytes()).hexdigest(),
          "| MATLAB", R["version_matlab"])
    et = R["ETNA"]
    print(f"Etna MATLAB: npix {int(et.NPIX)}, LHOT {et.LHOT:.9f}, LBK {et.LBK:.9f}, VRP {et.VRP * 1e6:.1f} W "
          "(OSF v2.5: 5, 1.965342180, 1.072886152, 9889528.4 W)")
    E = json.loads((AQUI / "entradas_v375_etiquetas.json").read_text(encoding="utf-8"))["escenas"]
    V = json.loads((AQUI / "vara_preliminar_375.json").read_text(encoding="utf-8"))
    vara = {e["posicion"]: e for e in V["escenas"]}
    VRP, NPIX, DL, LHOT, LBK = (np.ravel(R[k]).astype(float) for k in ("VRP", "NPIX", "DL", "LHOT", "LBK"))
    K = len(E)
    assert len(DL) == K
    ok_npix = int(sum(int(NPIX[n]) == E[n]["npix"] for n in range(K)))
    ok_hot = int(sum(abs(LHOT[n] - vara[E[n]["posicion"]]["l_hot"]) <= 1e-12 * max(1.0, abs(LHOT[n])) for n in range(K)))
    ok_coef = int(sum(abs(VRP[n] - DL[n] * COEF_750) <= 1e-9 * max(1.0, abs(VRP[n])) for n in range(K)))
    print(f"escenas {K}: NPIX igual {ok_npix}; LHOT igual a la vara/port {ok_hot}; VRP del .m = DL x coef. 750 {ok_coef}")
    rel_v = np.array([abs(DL[n] - vara[E[n]["posicion"]]["dl"]) / max(abs(DL[n]), 1e-15) for n in range(K)])
    dl_port = np.array([E[n]["vrp_port_mw"] / COEF_375 for n in range(K)])
    rel_p = np.abs(DL - dl_port) / np.maximum(np.abs(DL), 1e-15)
    rel_bk_v = np.array([abs(LBK[n] - vara[E[n]["posicion"]]["l_bk"]) / max(abs(LBK[n]), 1e-15) for n in range(K)])
    print(f"MATLAB contra la VARA: ΔL distinto (rel > {TOL_REL:g}) en {int((rel_v > TOL_REL).sum())}; máx rel ΔL "
          f"{rel_v.max():.2e}, máx rel L_bk {rel_bk_v.max():.2e}")
    print(f"MATLAB contra el PORT (control, tiene que fallar): ΔL distinto en {int((rel_p > TOL_REL).sum())}; "
          f"máx rel {rel_p.max():.3f}; la vara difería del port en "
          f"{sum(1 for e in V['escenas'] if e['rel'] > 1e-6)}")
    malas = [(E[n]["posicion"], E[n]["id"], E[n]["volcan"], E[n]["npix"], float(rel_v[n])) for n in range(K)
             if rel_v[n] > TOL_REL]
    print("escenas donde MATLAB y la vara difieren:", malas[:20])
    out = [{**vara[E[n]["posicion"]], "l_bk": float(LBK[n]), "dl": float(DL[n]), "vrp_vara_mw": float(DL[n] * COEF_375),
            "rel": float(rel_p[n])} for n in range(K)]
    Path(AQUI / "matlab_v375.json").write_text(json.dumps({
        "regla": {"estado": "MATLAB", "version": str(R["version_matlab"]),
                  "resultado_md5": hashlib.md5((AQUI / "resultado_v375.mat").read_bytes()).hexdigest()},
        "escenas": out}, indent=0), encoding="utf-8")
    print("escrito matlab_v375.json")
    assert int(et.NPIX) == 5 and abs(et.LBK - 1.072886152) < 5e-10
    assert ok_npix == ok_hot == ok_coef == K
    assert (rel_p > TOL_REL).sum() > 0, "el control no falla: la comparación no mira el fondo"
    print("VEREDICTO:", "LA VARA CALZA CON MATLAB" if not malas else f"LA VARA NO CALZA EN {len(malas)} ESCENAS")


if __name__ == "__main__":
    main()
