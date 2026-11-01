# -*- coding: utf-8 -*-
"""Verificador B2: ¿la huella nominal es la del sensor?, ¿«visto 2+ veces» mide duplicados del bow tie?, ¿las
rendijas del metodo A se cierran por el 20 % o a cualquier escala?

(a) Huella nominal (paso entre detectores a lo largo, a; paso entre frames a lo ancho, b) en el pixel del crater, por
    estrato de cenit, contra el cenit del sensor guardado en el npz (`sensor_zenith`) y contra el `z` de la tabla de
    objetivos. Si la huella fuera un modelo plano (1 km fijo) el paso no creceria con el cenit. El paso entre
    barridos a lo largo de la traza (`paso`) tiene que ser ~10 km en todo el barrido (10 detectores de 1 km al nadir).
(b) Doble conteo separado por origen: para cada punto del suelo de la caja ROI1, cuantas huellas lo contienen y
    cuantos BARRIDOS DISTINTOS entre ellas. 2+ huellas del MISMO barrido = traslape intra-barrido (no es bow tie);
    2+ barridos distintos = el mismo suelo en dos barridos (si es bow tie). Se reporta la fraccion de puntos con 2+
    barridos distintos con 'todos' y con A_centro_cubierto_ant.
(c) Rendijas: fraccion de suelo visto 0 veces con la huella a escala 1.0, 1.05, 1.10, 1.20 y 1.50 para 'todos',
    A_centro_cubierto_ant, B_filas_borde y C_sin_det0, estratos 40-50 y z>=50. Si los huecos nuevos de A son
    rendijas, se cierran ya a 1.05 o 1.10; los de C (detector entero sin copia) no se cierran ni a 1.5 en el nadir.
Pregunta 1: si el modelo de huella estuviera roto, (a) daria pasos sin relacion con el cenit; si el conteo de
duplicados mezclara intra e inter barrido, (b) lo separa. Pregunta 2: C_sin_det0 es el control positivo de huecos
reales en (c); 'todos' al nadir es el nulo (~0 huecos, ~0 duplicados).
Denominador: 403 pasadas evaluables del lote 40120713181 (2026-03-01 a 2026-10-21 UTC), caja ROI1 +/- 7,875 km,
puntos cada 200 m.
Uso: python -I v02_huella_y_duplicados.py
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # comun.py del auditor
import numpy as np  # noqa: E402
import comun as CM  # noqa: E402

AQUI = Path(__file__).resolve().parent
ESCALAS = [1.0, 1.05, 1.10, 1.20, 1.50]
METS = ["todos", "A_centro_cubierto_ant", "B_filas_borde", "C_sin_det0"]


def estrato(z):
    return "z<15" if z < 15 else "15-25" if z < 25 else "25-40" if z < 40 else "40-50" if z < 50 else "z>=50"


def cobertura_con_barridos(G, quitar, px, py, k=24, escala=1.0):
    """Como comun.conteo_cobertura, pero devuelve ademas cuantos barridos distintos cubren cada punto."""
    from scipy.spatial import cKDTree
    x, y = G["x"].ravel(), G["y"].ravel()
    scan = G["scan"].ravel()
    ax, ay, bx, by = (G[c].ravel() for c in ("ax", "ay", "bx", "by"))
    keep = ~quitar.ravel() & np.isfinite(x) & np.isfinite(ax) & np.isfinite(bx)
    idx = np.nonzero(keep)[0]
    tree = cKDTree(np.column_stack([x[idx], y[idx]]))
    _d, nb = tree.query(np.column_stack([px, py]), k=k)
    j = idx[nb]
    dx, dy = px[:, None] - x[j], py[:, None] - y[j]
    det = ax[j] * by[j] - ay[j] * bx[j]
    alpha = (dx * by[j] - dy * bx[j]) / det
    beta = (ax[j] * dy - ay[j] * dx) / det
    dentro = (np.abs(alpha) < 0.5 * escala) & (np.abs(beta) < 0.5 * escala)
    conteo = dentro.sum(axis=1)
    sc = np.where(dentro, scan[j], -1)
    sc_sorted = np.sort(sc, axis=1)
    distintos = (np.diff(sc_sorted, axis=1) != 0).sum(axis=1) + 1 - (sc_sorted[:, 0] == -1)
    distintos = np.where(conteo == 0, 0, distintos)
    return conteo, distintos


def main():
    pr, L = CM.pr_factory()
    obj, res = CM.objetivos(), CM.resultados()
    ids = [i for i in sorted(obj) if CM.evaluable(res.get(i))]
    pr(f"pasadas evaluables: {len(ids)}")
    huella = collections.defaultdict(list)
    zdiff = []
    paso_rel = []
    dup = collections.defaultdict(lambda: collections.defaultdict(list))
    rend = collections.defaultdict(lambda: collections.defaultdict(list))
    for i in ids:
        o, g = obj[i], obj[i]["grilla"]
        n = CM.cargar_nativo(i)
        G = CM.geometria(n, g["epsg"])
        ci, cj, _ = CM.pixel_crater(G, g)
        zc = float(n["sensor_zenith"][ci, cj])
        zdiff.append(abs(zc - o["z"]))
        e = estrato(o["z"])
        a = float(np.hypot(G["ax"][ci, cj], G["ay"][ci, cj]))
        b = float(np.hypot(G["bx"][ci, cj], G["by"][ci, cj]))
        huella[e].append((zc, a, b, float(G["paso"][cj])))
        paso_rel.append(float(np.nanmedian(G["paso"])) / 1000.0)
        px, py = CM.puntos_caja(g, 7875.0)
        for m in METS:
            q = CM.mascara_quitar(G, m)
            for s in ESCALAS:
                c, dist = cobertura_con_barridos(G, q, px, py, escala=s)
                rend[e][(m, s)].append(float((c == 0).mean()))
                if s == 1.0:
                    dup[e][m].append((float((c >= 2).mean()), float((dist >= 2).mean()),
                                      float(((c >= 2) & (dist < 2)).mean())))
    orden = ["z<15", "15-25", "25-40", "40-50", "z>=50"]
    pr(f"\n(a) cenit del npz en el pixel del crater vs z de la tabla: max |dif| {max(zdiff):.2f} grados, "
       f"mediana {np.median(zdiff):.2f} (n {len(zdiff)})")
    pr("    huella nominal en el pixel del crater (mediana por estrato): cenit, a (a lo largo, km), b (a lo ancho, km),"
       " paso entre barridos (km) [min; max de a y de b]")
    for e in orden:
        v = np.array(huella[e])
        pr(f"     {e:6s} n {len(v):3d}  z {np.median(v[:, 0]):5.1f}  a {np.median(v[:, 1]) / 1000:.2f} km "
           f"[{v[:, 1].min() / 1000:.2f}; {v[:, 1].max() / 1000:.2f}]  b {np.median(v[:, 2]) / 1000:.2f} km "
           f"[{v[:, 2].min() / 1000:.2f}; {v[:, 2].max() / 1000:.2f}]  paso {np.median(v[:, 3]) / 1000:.2f} km")
    pr(f"    paso entre barridos (mediana por pasada, km): min {min(paso_rel):.2f} max {max(paso_rel):.2f} "
       f"mediana {np.median(paso_rel):.2f} (tiene que ser ~10 km en todo el barrido)")
    pr("    10 detectores x a (km) por estrato, mediana: " + ", ".join(
        f"{e} {10 * np.median(np.array(huella[e])[:, 1]) / 1000:.1f}" for e in orden)
       + "  (si supera el paso de ~10 km, los barridos vecinos se pisan)")

    pr("\n(b) doble conteo en la caja ROI1, media por pasada: [2+ huellas | 2+ barridos distintos | 2+ huellas del mismo "
       "barrido unicamente]")
    for e in orden:
        for m in METS:
            v = np.array(dup[e][m])
            pr(f"     {e:6s} {m:24s} 2+: {v[:, 0].mean():.4f} | 2+ barridos: {v[:, 1].mean():.4f} | solo intra: "
               f"{v[:, 2].mean():.4f}")

    pr("\n(c) huecos (fraccion de suelo visto 0 veces) por escala de la huella, media por pasada")
    pr("     estrato metodo                   " + "  ".join(f"x{s:.2f}" for s in ESCALAS))
    for e in orden:
        for m in METS:
            pr(f"     {e:6s} {m:24s} " + "  ".join(f"{np.mean(rend[e][(m, s)]):.4f}" for s in ESCALAS))
    pr("   huecos NUEVOS de A respecto de 'todos' (A - todos), por escala:")
    for e in orden:
        pr(f"     {e:6s} " + "  ".join(
            f"x{s:.2f}: {np.mean(rend[e][('A_centro_cubierto_ant', s)]) - np.mean(rend[e][('todos', s)]):+.4f}"
            for s in ESCALAS))
    pr("   huecos NUEVOS de B respecto de 'todos' (B - todos), por escala:")
    for e in orden:
        pr(f"     {e:6s} " + "  ".join(
            f"x{s:.2f}: {np.mean(rend[e][('B_filas_borde', s)]) - np.mean(rend[e][('todos', s)]):+.4f}"
            for s in ESCALAS))
    pr("   huecos NUEVOS de C respecto de 'todos' (C - todos), por escala (control positivo: no se cierran):")
    for e in orden:
        pr(f"     {e:6s} " + "  ".join(
            f"x{s:.2f}: {np.mean(rend[e][('C_sin_det0', s)]) - np.mean(rend[e][('todos', s)]):+.4f}"
            for s in ESCALAS))
    (AQUI / "v02_huella_y_duplicados_salida.txt").write_bytes(("\n".join(L) + "\n").encode("utf-8"))
    json.dump({e: {f"{m}|{s}": rend[e][(m, s)] for (m, s) in rend[e]} for e in rend},
              open(AQUI / "v02_rendijas.json", "w", encoding="utf-8"))


if __name__ == "__main__":
    main()
