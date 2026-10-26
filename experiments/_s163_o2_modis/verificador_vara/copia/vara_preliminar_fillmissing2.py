# -*- coding: utf-8 -*-
"""O2 MODIS, vara PRELIMINAR del fondo: el VRP de las 404 escenas del paquete calculado con la regla de
`fillmissing2(...,'linear')` que reproduce a MATLAB (Delaunay con desempate por perturbación simbólica, marco
x = fila, y = columna; `delaunay_perturbado.py`, blob f273a47a de la rama `s163-o2-alternativa` c95483d31, confirmada
por verificador limpio en 166 de 166 escenas de VIIRS 750 y 84 de 84).

POR QUÉ. En una alerta de 1 a 4 píxeles el VRP es la radiancia de esos píxeles menos un fondo que el .m de MIROVA
rellena por debajo de un halo de 3 x 3; en una grilla regular cuatro centros vecinos son cocirculares, la
triangulación no es única y cada implementación rompe el empate a su manera. Nuestro port usa la de scipy (Qhull), y
el O2 de VIIRS 750 mostró que eso no es lo que hace MATLAB. Esto mide cuánto cambia el VRP MODIS del port con la
regla de MATLAB, escena por escena. PRELIMINAR: la prueba de oro es correr `correr_o2_modis.m` en MATLAB (paquete de
esta misma carpeta), que espera a que Nicolás vuelva a entrar a MathWorks.

QUÉ CAMBIA Y QUÉ NO. Todo igual que `mirova_v750_r2.vrp` (el fondo del port: hueco = alertas, halo k x k con k = 3
para 4 píxeles o menos, suma de radiancia y de fondo sobre las alertas), salvo la función de relleno.

Las dos preguntas del instrumento:
1. ¿Mide sólo el fondo? Sí: con el relleno del propio port (`mirova_v750_r2._fillmissing2_lineal`) esta misma
   construcción tiene que dar el VRP del port recalculado en las 404 escenas (control de identidad, se imprime).
2. ¿Puede dar distinto de cero? Sí: el marco cambiado (x = columna) es el nulo de la rama alternativa; tiene que
   discrepar de la regla en alguna escena (si no, nada de esto discrimina en MODIS).
Además, como pidió la coordinadora: las escenas con alguna celda de alerta fuera de la envolvente convexa de las celdas
con valor (allí la regla cae al vecino más cercano y el borde casi no está probado) se informan aparte.
Uso: python vara_preliminar_fillmissing2.py   (escribe vara_preliminar_fillmissing2.json y _salida.txt)
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation
from scipy.spatial import Delaunay

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
ORACULO = Path("C:/vrp-trabajo/s162-modd/experiments/_s158_audit_r2/oraculo")
BLOB_DP = "f273a47a3aa9323087da10c8b8bdd5a68a4830e9"
MD5_ENTRADA = "fbe988bfa71775705daf854b50248045"


def blob(p):
    b = Path(p).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def hueco(m13, mask):
    enm = m13.copy()
    enm[mask] = np.nan
    k = 3 if mask.sum() <= 4 else (5 if mask.sum() <= 30 else 7)
    enm[binary_dilation(np.isnan(enm), structure=np.ones((k, k), bool))] = np.nan
    return enm


def fuera_envolvente(enm, mask):
    ok = np.isfinite(enm)
    P = np.column_stack(np.nonzero(ok)).astype(float)
    Q = np.column_stack(np.nonzero(mask)).astype(float)
    return int((Delaunay(P).find_simplex(Q) < 0).sum())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    assert blob(AQUI / "delaunay_perturbado.py") == BLOB_DP, "delaunay_perturbado.py no es el blob confirmado"
    assert hashlib.md5((AQUI / "entradas_o2_modis.mat").read_bytes()).hexdigest() == MD5_ENTRADA, "entrada distinta"
    import delaunay_perturbado as DP
    sys.path.insert(0, str(ORACULO))
    import mirova_v750_r2 as ORA
    from scipy.io import loadmat
    E = loadmat(AQUI / "entradas_o2_modis.mat")
    et = json.loads((AQUI / "entradas_o2_modis_etiquetas.json").read_text(encoding="utf-8"))
    filas, lineas = [], []

    def pr(*x):
        s = " ".join(str(y) for y in x)
        print(s, flush=True)
        lineas.append(s)

    for i, e in enumerate(et):
        m13 = E["M13"][:, :, i].astype(float)
        a = np.asarray(E["ALERTAS"][i, 0]).ravel().astype(int)
        mask = np.zeros(m13.shape, bool)
        mask[np.unravel_index(a - 1, m13.shape, order="F")] = True
        enm = hueco(m13, mask)
        lhot = float(np.nansum(m13[mask]))
        c = e["coef_area"] / 1e6
        v_port = (lhot - float(np.nansum(ORA._fillmissing2_lineal(enm)[mask]))) * c
        B, info = DP.rellenar(enm, "xy_fila_col")
        v_regla = (lhot - float(np.nansum(B[mask]))) * c
        Bn, _ = DP.rellenar(enm, "xy_col_fila")
        v_nulo = (lhot - float(np.nansum(Bn[mask]))) * c
        filas.append({**{k: e[k] for k in ("k", "lote", "volcan", "hora_utc", "variante", "npix")},
                      "vrp_port_recalculado_mw": e["vrp_port_recalculado_mw"], "vrp_port_aqui_mw": v_port,
                      "vrp_regla_matlab_mw": v_regla, "vrp_marco_cambiado_mw": v_nulo,
                      "alertas_fuera_envolvente": fuera_envolvente(enm, mask), "ilegales": info["ilegales"]})
    ident = [abs(f["vrp_port_aqui_mw"] / f["vrp_port_recalculado_mw"] - 1) for f in filas]
    pr("escenas:", len(filas), "| identidad con el relleno del port (dif. rel. <= 1e-9):",
       sum(x <= 1e-9 for x in ident), "de", len(filas), "| max", max(ident))
    pr("aristas ilegales de la triangulacion (control de la regla):", sum(f["ilegales"] for f in filas))
    nulo_dif = sum(abs(f["vrp_marco_cambiado_mw"] / f["vrp_regla_matlab_mw"] - 1) > 1e-9 for f in filas)
    pr("nulo (marco cambiado distinto de la regla a 1e-9):", nulo_dif, "de", len(filas))
    for grupo, sel in (("todas", lambda f: True), ("dentro de la envolvente", lambda f: f["alertas_fuera_envolvente"] == 0),
                       ("con alertas FUERA de la envolvente", lambda f: f["alertas_fuera_envolvente"] > 0)):
        g = [f for f in filas if sel(f)]
        pr("\n== %s (n %d)" % (grupo, len(g)))
        for n in (1, 2, 3, 4):
            r = np.array([f["vrp_port_recalculado_mw"] / f["vrp_regla_matlab_mw"] for f in g if f["npix"] == n])
            if r.size:
                pr("  npix %d: n %3d | port/regla mediana %.4f p5 %.4f p95 %.4f | |dif| > 1 %%: %3d | > 10 %%: %3d | "
                   "iguales a 1e-9: %3d" % (n, r.size, np.median(r), np.percentile(r, 5), np.percentile(r, 95),
                                           int(np.sum(np.abs(r - 1) > 0.01)), int(np.sum(np.abs(r - 1) > 0.10)),
                                           int(np.sum(np.abs(r - 1) <= 1e-9))))
    pr("\n== variante fisica (la que decide en MOD-D), por npix")
    for n in (1, 2, 3, 4):
        r = np.array([f["vrp_port_recalculado_mw"] / f["vrp_regla_matlab_mw"] for f in filas
                      if f["npix"] == n and f["variante"] == "fisica"])
        if r.size:
            pr("  npix %d: n %3d | port/regla mediana %.4f min %.4f max %.4f | |dif| > 10 %%: %d" % (
                n, r.size, np.median(r), r.min(), r.max(), int(np.sum(np.abs(r - 1) > 0.10))))
    pr("\n== las 12 escenas mas distintas (port/regla)")
    for f in sorted(filas, key=lambda f: -abs(np.log(f["vrp_port_recalculado_mw"] / f["vrp_regla_matlab_mw"])))[:12]:
        pr("  %-14s %-18s %s npix %d  port %.4f  regla %.4f  (x%.3f)%s" % (
            f["variante"], f["volcan"], f["hora_utc"], f["npix"], f["vrp_port_recalculado_mw"],
            f["vrp_regla_matlab_mw"], f["vrp_port_recalculado_mw"] / f["vrp_regla_matlab_mw"],
            "  FUERA DE ENVOLVENTE" if f["alertas_fuera_envolvente"] else ""))
    (AQUI / "vara_preliminar_fillmissing2.json").write_text(json.dumps(filas, indent=1, default=float), encoding="utf-8")
    (AQUI / "vara_preliminar_fillmissing2_salida.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
