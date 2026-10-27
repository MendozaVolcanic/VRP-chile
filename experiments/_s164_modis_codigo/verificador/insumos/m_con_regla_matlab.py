# -*- coding: utf-8 -*-
"""MOD-D, adenda 4 punto 5 y apéndice punto 8: M informada TAMBIÉN con el fondo de la regla de `fillmissing2` de MATLAB.
Script aparte (VCR-03 de la segunda vuelta): no edita ni reemplaza `evaluar_paquete.py`; lo importa para leer el censo
con las mismas funciones y cambia sólo la magnitud del PM en los pares de M.

POR QUÉ. El VRP del port en alertas de 1 a 4 píxeles depende de cómo se rompe el empate de la triangulación con que el
`.m` rellena el fondo bajo la alerta. La regla de MATLAB (Delaunay con perturbación simbólica, marco x = fila;
`delaunay_perturbado.py`, blob f273a47a, copiada de la rama `s163-o2-alternativa`) reproduce el fondo de MATLAB R2026b
en 191 de 191 escenas MODIS distintas (`experiments/_s163_o2_modis/RESULTADO_O2_MODIS_MATLAB.md`, verificado). La
coordinadora S163 decidió (D-48) que esta columna deja de ser preliminar; se informa al lado de la sellada y no la
reemplaza. Alcance: 161 de esas 191 escenas son de Láscar, huecos de 3 x 3; SIN DATO que MIROVA use ese `.m` en MODIS.

QUÉ HACE. Con la grilla 51 x 51 de cada pasada (`grilla_NNNN.npz`, variante `fisica`, que guarda el arnés) y la
máscara de alertas del PM (sus `pixeles`), arma el hueco del `.m` (alertas más halo k x k, k = 3 hasta 4 píxeles, 5
hasta 30, 7 sobre 30), lo rellena con la regla, y calcula VRP = (suma de la radiancia MIR de las alertas menos la suma
del fondo) x 1,89e7 x 1,0 km2 / 1e6. Con eso recalcula d de M y su regla (`regla_m` del blob sellado de evaluar_d25).

Las dos preguntas del instrumento:
1. ¿Mide sólo el fondo? `probar()`: con el relleno del port en vez de la regla, la misma construcción da el VRP de
   `mirova_port.vrp` a 1e-12 (identidad), y con la regla da el de `delaunay_perturbado.rellenar` aplicado a mano.
2. ¿Puede dar distinto? `probar()`: en una escena sintética de 1 píxel con empate, la regla y el port difieren.
Uso: python -I m_con_regla_matlab.py --art DIR [--ref DIR] [--commit SHA]   |   python -I m_con_regla_matlab.py --probar
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import statistics
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import evaluar_paquete as EP  # noqa: E402
import delaunay_perturbado as DP  # noqa: E402

BLOB_DP = "f273a47a3aa9323087da10c8b8bdd5a68a4830e9"
COEF_MODIS = 1.89e7 * 1.0 / 1e6


def hueco(m13, mask):
    enm = np.asarray(m13, float).copy()
    enm[mask] = np.nan
    n = int(mask.sum())
    k = 3 if n <= 4 else (5 if n <= 30 else 7)
    enm[binary_dilation(np.isnan(enm), structure=np.ones((k, k), bool))] = np.nan
    return enm


def vrp_con(m13, mask, rellenar):
    enm = hueco(m13, mask)
    fondo = rellenar(enm)
    return (float(np.nansum(np.asarray(m13, float)[mask])) - float(np.nansum(fondo[mask]))) * COEF_MODIS


def regla(enm):
    return DP.rellenar(enm, "xy_fila_col")[0]


def mascara(pixeles, forma):
    m = np.zeros(forma, bool)
    for q in pixeles:
        m[int(q[0]), int(q[1])] = True
    return m


def grillas_por_id(art):
    return {int(Path(p).stem.split("_")[1]): p for p in glob.glob(str(Path(art) / "**" / "grilla_*.npz"), recursive=True)}


def pares_con_regla(filas, grillas):
    out, sin_grilla, no_positivo = [], [], []
    for f in EP._ev(filas):
        if f["lab"] not in ("protegida", "bajo1") or not (EP._pub(f, "K") == 1 and EP._pub(f, "PM") == 1):
            continue
        k, mm = EP._mag(f, "K"), f.get("vrp_mirova")
        if not (k > 0 and mm and mm > 0):
            continue
        g = grillas.get(f.get("id"))
        if g is None:
            sin_grilla.append((f["vol"], f["dt"]))
            continue
        mir = np.load(g)["mir"].astype(float)
        v = vrp_con(mir, mascara(f["port"]["fisica"]["pixeles"], mir.shape), regla)
        if not v > 0:
            no_positivo.append((f["vol"], f["dt"], v))
            continue
        out.append({"k": k, "d": v, "m": mm, "d_port": EP._mag(f, "PM"), "clave": "%s|MODIS|%s" % (f["vol"], f["dt"]),
                    "bloque": EP._bloque(f), "vol": f["vol"], "npix": f["port"]["fisica"]["npix"]})
    return out, sin_grilla, no_positivo


def m_regla(P):
    if not P:
        return {"n": 0, "regla": "SIN PARES"}
    d = [abs(math.log10(p["d"] / p["m"])) - abs(math.log10(p["k"] / p["m"])) for p in P]
    W = EP.D.pesos_bloque([p["bloque"] for p in P])
    r, lo, hi = EP.D.regla_m(d, W)
    cambio = [p["d"] / p["d_port"] for p in P]
    return {"n": len(P), "regla": r, "ic95_d": [lo, hi], "mediana_d": statistics.median(d),
            "regla_sobre_port_mediana": statistics.median(cambio),
            "pares_que_cambian_mas_de_10pct": sum(abs(c - 1) > 0.10 for c in cambio)}


def probar():
    """Identidad con el port, igualdad con la regla aplicada a mano y un caso de empate donde difieren."""
    sys.path.insert(0, str(EP.RAIZ / "experiments/_s159/portes"))
    import mirova_port as MP
    assert EP.blob(AQUI / "delaunay_perturbado.py") == BLOB_DP, "delaunay_perturbado.py no es el blob confirmado"
    rng = np.random.default_rng(162)
    mir = 0.1 + rng.normal(0, 0.002, (51, 51))
    mir[25, 25] = 0.3
    mask = np.zeros(mir.shape, bool)
    mask[25, 25] = True
    v_port = vrp_con(mir, mask, MP.ORA._fillmissing2_lineal)
    ref = MP.vrp(mir, mask, MP.SENSORES["MODIS"])["VRP_MW"]
    assert abs(v_port - ref) <= 1e-12 * max(1.0, abs(ref)), ("identidad con el port", v_port, ref)
    enm = hueco(mir, mask)
    v_regla = vrp_con(mir, mask, regla)
    a_mano = (float(mir[25, 25]) - float(DP.rellenar(enm, "xy_fila_col")[0][25, 25])) * COEF_MODIS
    assert abs(v_regla - a_mano) <= 1e-12, ("regla a mano", v_regla, a_mano)
    # La triangulación depende sólo de qué celdas tienen valor: con el mismo hueco en una grilla llena, el port elige
    # siempre la misma pareja de celdas (medido: 0 de 30 semillas difieren con el foco en el centro). En las escenas
    # reales el foco cambia de posición y hay bordes de barrido vacíos; así se arma aquí, y se exige que regla y port
    # difieran en al menos 5 de 20 (medido al escribir: 13 de 20), o la comparación no podría ver nada.
    distintas = 0
    for s in range(20):
        r = np.random.default_rng(s)
        x = 0.1 + r.normal(0, 0.002, (51, 51))
        i, j = r.integers(20, 31, 2)
        x[i, j] = 0.3
        if s % 2:
            x[:r.integers(3, 15), :] = np.nan
        mk = np.zeros(x.shape, bool)
        mk[i, j] = True
        distintas += abs(vrp_con(x, mk, regla) - vrp_con(x, mk, MP.ORA._fillmissing2_lineal)) > 1e-6
    assert distintas >= 5, "regla y port difieren en %d de 20 escenas de 1 pixel: la comparacion no ve" % distintas
    return {"vrp_port": v_port, "vrp_regla": v_regla, "semillas_donde_difieren": int(distintas)}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", default=None)
    ap.add_argument("--ref", default=None)
    ap.add_argument("--commit", default=None)
    ap.add_argument("--probar", action="store_true")
    a = ap.parse_args()
    print("prueba:", probar())
    if a.probar:
        return
    pob = json.load(open(EP.POBLACION, encoding="utf-8"))
    grillas = json.load(open(EP.GRILLAS, encoding="utf-8"))
    crudas, recorridos, cab = EP.cargar(a.art)
    filas, _union, _esp = EP.unir(crudas, pob)
    for f in filas:
        f["_evaluable"], f["_motivo"] = EP.evaluable(f)
    EP.armar_tabla(filas, grillas)
    P, sin_grilla, no_pos = pares_con_regla(filas, grillas_por_id(a.art))
    res = {"m_con_regla_matlab": m_regla(P), "m_sellada": EP.m(filas, "PM"), "sin_grilla": sin_grilla[:20],
           "n_sin_grilla": len(sin_grilla), "no_positivo": no_pos[:20], "commits": sorted({c.get("commit") for c in cab}),
           "commit_esperado": a.commit}
    print(json.dumps({k: v for k, v in res.items() if k != "m_sellada"}, ensure_ascii=False, indent=1, default=str))
    print("M sellada (port):", {k: res["m_sellada"].get(k) for k in ("n", "regla", "ic95_d", "mediana_d")})
    (Path(a.art) / "m_con_regla_matlab.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str),
                                                        encoding="utf-8")


if __name__ == "__main__":
    main()
