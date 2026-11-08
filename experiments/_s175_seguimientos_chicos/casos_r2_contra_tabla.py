# -*- coding: utf-8 -*-
"""S175: los casos de tests/test_r2_pixel_level.py contra la tabla de MIROVA y contra el TIF.

POR QUÉ. Tres casos fallaban en local con «no tiene primary_cluster.centroid ni final_hotspot ni
hotspot». Antes de decidir qué hacer con ellos hay que saber si es un FN nuestro (MIROVA vio algo y K
no) o si ninguno de los dos vio nada, y qué representa el centroide del TIF contra el que se compara.

Para cada caso imprime: VRP de la tabla de MIROVA; el record de hoy (K) y el del padre del merge de
#883 (detector anterior); y, del TIF, cuántos píxeles son mayores que 0, su máximo, y a cuántos km del
centro de la escena cae el centroide ponderado que usa la prueba.

USO: MIROVA_TIF_ARCHIVE=<archivo de TIF> python casos_r2_contra_tabla.py --temporal <carpeta>
(<carpeta> es la misma de comparar_magnitud_post_883.py, que exporta los records del padre de #883.)
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PADRE = "records_600968644"


def cargar_prueba():
    spec = importlib.util.spec_from_file_location("r2", ROOT / "tests" / "test_r2_pixel_level.py")
    t = importlib.util.module_from_spec(spec)
    sys.modules["r2"] = t
    spec.loader.exec_module(t)
    return t


def resumen(r):
    if r is None:
        return "sin record"
    pc = r.get("primary_cluster") or {}
    return ("n_anomalous_pixels=%s vrp_mw=%s pc_vrp_mw=%s distance_class=%s final_hotspot_source=%s via_codigo_mirova=%s"
            % (r.get("n_anomalous_pixels"), r.get("vrp_mw"), pc.get("vrp_mw"), r.get("distance_class"),
               r.get("final_hotspot_source"), r.get("via_codigo_mirova", "ausente")))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--temporal", required=True)
    a = ap.parse_args()
    t = cargar_prueba()
    for v, s, ts, _ed, ev, h in t.R2_CASES:
        gt = pd.Timestamp(ts)
        print("==", v, s, ts, "|", h, "| exp_vrp del caso:", ev)
        print("   tabla de MIROVA, VRP_MW:", t._vrp_tabla_mirova(v, s, gt))
        print("   hoy:        ", resumen(t._load_vrp_record_near(v, s, gt)))
        raiz = t.REPO_ROOT
        t.REPO_ROOT = Path(a.temporal) / PADRE
        print("   antes #883: ", resumen(t._load_vrp_record_near(v, s, gt)))
        t.REPO_ROOT = raiz
        tif = t._find_tif_for_granule(v, s, gt)
        px = np.array(t._read_tif_pixels(tif))
        c = t._weighted_centroid([tuple(p) for p in px])
        lat_c, lon_c = (px[:, 0].min() + px[:, 0].max()) / 2, (px[:, 1].min() + px[:, 1].max()) / 2
        print("   TIF %s: pixeles>0=%d max=%.3f mediana=%.3f; centroide ponderado a %.2f km del centro de la escena"
              % (tif.name, len(px), px[:, 2].max(), np.median(px[:, 2]), t._haversine_km(c[0], c[1], lat_c, lon_c)))


if __name__ == "__main__":
    main()
