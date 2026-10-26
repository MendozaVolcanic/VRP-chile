# -*- coding: utf-8 -*-
"""O2 MODIS: ¿la regla de fillmissing2 (vara preliminar) es lo que hizo MATLAB, escena por escena?

POR QUÉ. La vara preliminar (`vara_preliminar_fillmissing2.py`) calculó el fondo de las 404 escenas MODIS con la regla
que reproduce a MATLAB en VIIRS 750, pero en MODIS quedaron sin probar los bloques compactos de 2 x 2 píxeles (ninguna
escena de VIIRS los tenía) y la grilla de 51 x 51 (en VIIRS era 67 x 67). Ahora existe la corrida real de MATLAB R2026b
sobre el mismo paquete (`resultado_o2_modis.mat`, md5 d20cf7ddd3b6ba015c7b474afe627085). Se comparan el VRP y la matriz
de fondo completa (`BK`) dentro del hueco.

Las dos preguntas del instrumento:
1. ¿Puede dar distinto? Sí: el relleno del port (`_fillmissing2_lineal`) sobre la misma entrada se compara igual contra
   MATLAB y tiene que discrepar en las escenas donde la vara dice que difieren (si coincidiera, la comparación no ve).
2. ¿Es la corrida de este paquete? Se comprueban los md5 del resultado y de la entrada, y que NPIX de MATLAB sea el de
   cada máscara.
Uso: python regla_contra_matlab_modis.py
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
ORACULO = Path("C:/vrp-trabajo/s162-modd/experiments/_s158_audit_r2/oraculo")
TOL = 1e-9


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    from scipy.io import loadmat
    assert hashlib.md5((AQUI / "resultado_o2_modis.mat").read_bytes()).hexdigest() == "d20cf7ddd3b6ba015c7b474afe627085"
    assert hashlib.md5((AQUI / "entradas_o2_modis.mat").read_bytes()).hexdigest() == "fbe988bfa71775705daf854b50248045"
    import delaunay_perturbado as DP
    import vara_preliminar_fillmissing2 as V
    sys.path.insert(0, str(ORACULO))
    import mirova_v750_r2 as ORA
    R = loadmat(AQUI / "resultado_o2_modis.mat", squeeze_me=False)
    E = loadmat(AQUI / "entradas_o2_modis.mat")
    et = json.loads((AQUI / "entradas_o2_modis_etiquetas.json").read_text(encoding="utf-8"))
    filas, vistas = [], {}
    for i, e in enumerate(et):
        m13 = E["M13"][:, :, i].astype(float)
        a = np.asarray(E["ALERTAS"][i, 0]).ravel().astype(int)
        mask = np.zeros(m13.shape, bool)
        mask[np.unravel_index(a - 1, m13.shape, order="F")] = True
        enm = V.hueco(m13, mask)
        hueco = np.isnan(enm) & np.isfinite(m13)
        bk_m = np.asarray(R["BK"][i, 0], float)
        B, _ = DP.rellenar(enm, "xy_fila_col")
        Bp = ORA._fillmissing2_lineal(enm)
        c = e["coef_area"] / 1e6
        lhot = float(np.nansum(m13[mask]))
        v_mat = float(R["DL"][i, 0]) * c
        clave = (hashlib.sha1(m13.tobytes()).hexdigest(), tuple(a))
        forma = "2x2" if (mask.sum() == 4 and np.ptp(np.nonzero(mask)[0]) == 1 and np.ptp(np.nonzero(mask)[1]) == 1) \
            else "%d px" % mask.sum()
        filas.append({"k": e["k"], "npix": int(mask.sum()), "forma": forma, "distinta": clave not in vistas,
                      "variante": e["variante"], "volcan": e["volcan"], "hora": e["hora_utc"],
                      "rel_regla": abs((lhot - float(np.nansum(B[mask]))) * c / v_mat - 1),
                      "rel_port": abs((lhot - float(np.nansum(Bp[mask]))) * c / v_mat - 1),
                      "bk_regla": float(np.nanmax(np.abs(B - bk_m)[hueco])) if hueco.any() else 0.0,
                      "bk_port": float(np.nanmax(np.abs(Bp - bk_m)[hueco])) if hueco.any() else 0.0,
                      "npix_ok": int(R["NPIX"][i, 0]) == int(mask.sum())})
        vistas.setdefault(clave, i)
    print("NPIX de MATLAB = mascara:", sum(f["npix_ok"] for f in filas), "de", len(filas))
    for nombre, sel in (("todas las filas", lambda f: True), ("escenas distintas", lambda f: f["distinta"])):
        g = [f for f in filas if sel(f)]
        print("\n== %s (n %d)" % (nombre, len(g)))
        for forma in ("1 px", "2 px", "3 px", "4 px", "2x2"):
            h = [f for f in g if f["forma"] == forma]
            if not h:
                continue
            print("  %-5s n %3d | regla = MATLAB a 1e-9 (VRP): %3d | fondo en el hueco a 1e-9: %3d | max VRP %.1e"
                  " | port = MATLAB: %3d | port difiere > 1 %%: %3d" % (
                      forma, len(h), sum(f["rel_regla"] <= TOL for f in h), sum(f["bk_regla"] <= TOL for f in h),
                      max(f["rel_regla"] for f in h), sum(f["rel_port"] <= TOL for f in h),
                      sum(f["rel_port"] > 0.01 for f in h)))
    malos = [f for f in filas if f["rel_regla"] > TOL or f["bk_regla"] > TOL]
    print("\nescenas donde la regla NO es MATLAB:", len(malos))
    for f in malos[:15]:
        print("  ", {k: f[k] for k in ("k", "forma", "variante", "volcan", "hora", "rel_regla", "bk_regla")})
    (AQUI / "regla_contra_matlab_modis.json").write_text(json.dumps(filas, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
