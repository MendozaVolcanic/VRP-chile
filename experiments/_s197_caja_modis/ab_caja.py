# -*- coding: utf-8 -*-
# FICHA (SDA, CPLT 372): A/B de medición, sólo lectura, local. No escribe en data/.
"""S197: caja sensible de MODIS «def» (producción) contra «crater», sobre los recortes nativos del A/B de D36.

POR QUÉ: issue #1106 (experiments/_s197_1106/INFORME.md). Pre-registro: PREREGISTRO.md de esta carpeta.
Uso: python experiments/_s197_caja_modis/ab_caja.py <carpeta_artefactos_d36> <salida_dir>
Escribe <salida_dir>/x/p1_resultados_0.json con brazos A (def) y C (crater), en el formato de p1_runner.py, más el
control contra el brazo A guardado por el run 44016042341.
"""
import json
import os
import sys
import glob
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for _p in (RAIZ, RAIZ / "experiments/_s190_d36"):
    sys.path.insert(0, str(_p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import numpy as np  # noqa: E402
import yaml  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402
from p1_runner import slim  # noqa: E402

ART, OUT = Path(sys.argv[1]), Path(sys.argv[2])
VOLS = {v["name"]: v for v in yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
pas = []
for f in sorted(glob.glob(str(ART / "*" / "p1_resultados_*.json"))):
    d = Path(f).parent
    for p in json.load(open(f, encoding="utf-8"))["pasadas"]:
        p["_dir"] = d
        pas.append(p)
out = []
ctrl = {"A_local_igual_actions": [0, 0], "difieren": [], "C_igual_A_celda_central": [0, 0], "sin_npz": []}
for p in pas:
    if p.get("estado") != "ok":
        out.append({k: p.get(k) for k in ("volcan", "granule", "dt", "estado", "estratos")})
        continue
    v = VOLS[p["volcan"]]
    alat, alon = get_detection_anchor(v)
    alat = v["lat"] if alat is None else alat
    alon = v["lon"] if alon is None else alon
    g = p["granule"].split(".")
    npz = p["_dir"] / "nativos" / ("%s_%s.%s_%s.npz" % (p["volcan"], g[1], g[2], g[0]))
    if not npz.exists():
        ctrl["sin_npz"].append(str(npz.name))
        out.append({**{k: p.get(k) for k in ("volcan", "granule", "dt", "estratos")}, "estado": "sin_npz"})
        continue
    z = np.load(npz)
    ang = {k: z[k] for k in z.files if k not in ("mir", "tir", "lat", "lon")}
    nombre = MV.volcan_por_coordenadas(v["lat"], v["lon"])
    sensor = "MODIS_TERRA" if g[0].startswith("MOD") else "MODIS_AQUA"
    br = {}
    for b, t in (("A", "def"), ("C", "crater")):
        r = MV.calcular_vrp_granulo({"MIR": z["mir"], "TIR": z["tir"]}, z["lat"], z["lon"], ang, nombre, alat, alon,
                                    v.get("inner_radius_km"), sensor, familia="MODIS", tipo_roi=t)
        br[b] = slim(r)
    gr = MV.grilla_del_volcan(nombre, paso_m=MV.FAMILIAS["MODIS"]["paso_m"], clave_roi="roi_modis")
    central = tuple(MV.celda_de(gr, alat, alon)) == (gr["n"] // 2, gr["n"] // 2)
    ig = json.dumps(br["A"], sort_keys=True) == json.dumps(p["brazos"]["A"], sort_keys=True)
    ctrl["A_local_igual_actions"][0] += ig
    ctrl["A_local_igual_actions"][1] += 1
    if not ig:
        ctrl["difieren"].append({"volcan": p["volcan"], "dt": p["dt"],
                                 "local": {k: br["A"].get(k) for k in ("vrp_mw", "n", "dc", "pc_vrp")},
                                 "actions": {k: p["brazos"]["A"].get(k) for k in ("vrp_mw", "n", "dc", "pc_vrp")}})
    if central:
        ctrl["C_igual_A_celda_central"][0] += json.dumps(br["C"], sort_keys=True) == json.dumps(br["A"], sort_keys=True)
        ctrl["C_igual_A_celda_central"][1] += 1
    out.append({**{k: p.get(k) for k in ("volcan", "granule", "dt", "estratos", "dist_i0_km", "n_sel_45km")},
                "estado": "ok", "celda_central": central, "brazos": br, "control_copia_igual": True,
                "control_produccion": {}})
(OUT / "x").mkdir(parents=True, exist_ok=True)
json.dump({"pasadas": out}, open(OUT / "x" / "p1_resultados_0.json", "w", encoding="utf-8"), indent=1,
          ensure_ascii=False, default=str)
json.dump(ctrl, open(OUT / "controles.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("A local == Actions:", ctrl["A_local_igual_actions"], "| C == A en celda central:", ctrl["C_igual_A_celda_central"],
      "| sin npz:", len(ctrl["sin_npz"]))
for x in ctrl["difieren"][:10]:
    print("  difiere", x)
