"""Cuenta, por volcán y sensor, las celdas de la grilla de la vía que están a <= inner_radius_km del cráter
(la zona A del paso 1) y que en producción NO son de la región sensible (BOX != 2), o sea que con s_A = 5 y los
pisos sensibles cambiarían de umbral. Si alguna cuenta es > 0, el brazo s = 5,0 no es idéntico a producción por
construcción. Sólo lectura; corre desde la raíz del worktree."""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")
import numpy as np
import yaml

from pipeline import mirova_v750_codigo as MV
from pipeline.geo_utils import get_detection_anchor

vols = {v["name"]: v for v in yaml.safe_load(open("volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
ZONA = ["Lascar", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Llaima", "Villarrica",
        "Copahue", "Chaiten", "Lastarria"]
print("volcan familia inner_km celdas_zonaA de_ellas_no_sensibles(box!=2) sensibles_fuera_de_zonaA")
tot = 0
for nombre in ZONA:
    v = vols[nombre]
    lat, lon = get_detection_anchor(v)
    inner = float(v["inner_radius_km"])
    for fam in ("VIIRS750", "MODIS", "VIIRS375"):
        cfg = MV.FAMILIAS[fam]
        g = MV.grilla_del_volcan(nombre, paso_m=cfg["paso_m"], clave_roi=cfg["clave_roi"])
        if g is None:
            print(nombre, fam, "sin grilla")
            continue
        if cfg.get("roi1_half_m") is not None:
            box = MV.caja_v375(g, lat, lon, lado_sensible=cfg["lado_sensible"], half_roi1_m=cfg["roi1_half_m"])
        else:
            box = MV.caja_roi(g.get("roi", "def"), n=g["n"], celda_crater=MV.celda_de(g, lat, lon), inner_km=inner,
                              lado_sensible=cfg["lado_sensible"], lado_anillo=cfg["lado_anillo"], paso_m=g["paso"])
        box = box.copy()
        box[:, [0, -1]] = np.nan
        box[[0, -1], :] = np.nan
        pos = MV.posicion_de(g, lat, lon)
        r, q = np.indices(box.shape)
        zona = np.hypot(r - pos[0], q - pos[1]) * g["paso"] / 1000.0 <= inner
        zona &= ~np.isnan(box)
        no_sens = int((zona & (box != 2)).sum())
        sens_fuera = int((~zona & (box == 2)).sum())
        tot += no_sens
        print(nombre, fam, inner, int(zona.sum()), no_sens, sens_fuera)
print("total celdas zona A no sensibles:", tot)
