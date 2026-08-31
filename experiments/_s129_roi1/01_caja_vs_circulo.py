# -*- coding: utf-8 -*-
"""S129 — el ROI1 del paper es una CAJA de 5 km; el nuestro es un CÍRCULO de 3 a 20.

LO QUE DICE EL CANON, verbatim (Coppola 2016a SP426.5):

    "the inner region (ROI1) consists of a box (5 x 5 km) centred on the
     volcano's summit"

Una caja de 5 x 5 km centrada en la cumbre, **igual para todos los volcanes**. Y el
criterio del propio paper para tener dos ROIs es que tengan "variable size and
different chance of finding a thermal anomaly".

LO QUE HACEMOS NOSOTROS: un CÍRCULO de radio `inner_radius_km`, distinto por volcán
— 3 km en Lastarria y Planchón-Peteroa, 4 en Copahue, 5 en seis, 7 en Tupungatito y
**20 en PCC**.

POR QUÉ IMPORTA, y no es cosmético. El ROI1 decide qué umbrales se aplican: dentro
rigen los de *summit* (N·σ = 5, C1 = 0,003) y fuera los de *scene* (N·σ = 10,
C1 = 0,010). O sea que agrandar el ROI1 **afloja el umbral** sobre más terreno.

Y hay dos agravantes:
  · **`MISSION.md` excluye lo per-volcán.** Un radio distinto por volcán es
    exactamente la clase de parche que la misión documenta como anti-patrón, y acá
    está en la geometría base de la detección.
  · **Es el eje que A82 nunca auditó.** S124 rebajó A82 —«el far→summit MODIS es
    irreducible»— justo porque la auditoría S114 en que se apoyaba cubrió umbrales,
    tests, kernel y second-run, pero NO la geometría del ROI.

QUÉ MIDE ESTE SCRIPT. Cuánto terreno de más cubre nuestro ROI1 frente al del paper, y
cuántas detecciones reciben hoy los umbrales laxos de *summit* que con la caja del
paper caerían en *scene*.

Read-only.
"""
import io
import json
import math
import os
import sys

import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
from _s126_lib import VENTS, bucket                              # noqa: E402

VENTANA = ("2026-01-01", "2026-12-31")
CAJA_KM = 5.0            # el lado de la caja de Coppola 2016a
SEMI = CAJA_KM / 2.0     # +-2,5 km desde la cumbre
AREA_CAJA = CAJA_KM ** 2

cfg = {v["name"]: v for v in yaml.safe_load(
    open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}

R = {"_meta": {"caja_paper_km": CAJA_KM, "area_caja_km2": AREA_CAJA,
               "cita": "Coppola 2016a SP426.5: the inner region (ROI1) consists of "
                       "a box (5 x 5 km) centred on the volcano's summit"}}
tab = {}

for vol in sorted(VENTS):
    p = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
    if not os.path.exists(p):
        continue
    vla, vlo = VENTS[vol]
    inner = cfg.get(vol, {}).get("inner_radius_km")
    if inner is None:
        continue
    area_nuestra = math.pi * inner ** 2

    # Detecciones que hoy caen dentro de NUESTRO ROI1 y que con la caja del paper
    # quedarian fuera. Se mide sobre los pixeles anomalos, que es donde el umbral
    # se aplica de verdad.
    dentro_nuestro = dentro_caja = 0
    por_sensor = {}
    for r in json.load(open(p, encoding="utf-8"))["records"]:
        d = r.get("datetime_utc", "")[:10]
        if not (VENTANA[0] <= d <= VENTANA[1]):
            continue
        b = bucket(r.get("sensor"))
        if b is None:
            continue
        for q in (r.get("anomaly_pixels") or []):
            la, lo = q.get("lat"), q.get("lon")
            if la is None or (q.get("vrp_mw") or 0) <= 0:
                continue
            dy = abs(la - vla) * 111.32
            dx = abs(lo - vlo) * 111.32 * math.cos(math.radians(vla))
            en_circulo = math.hypot(dx, dy) <= inner
            en_caja = dx <= SEMI and dy <= SEMI
            if not en_circulo:
                continue
            dentro_nuestro += 1
            s = por_sensor.setdefault(b, {"nuestro": 0, "caja": 0})
            s["nuestro"] += 1
            if en_caja:
                dentro_caja += 1
                s["caja"] += 1

    if not dentro_nuestro:
        continue
    tab[vol] = {
        "inner_radius_km": inner,
        "area_nuestra_km2": round(area_nuestra, 1),
        "veces_el_roi1_del_paper": round(area_nuestra / AREA_CAJA, 1),
        "pixeles_en_nuestro_roi1": dentro_nuestro,
        "pixeles_tambien_en_la_caja": dentro_caja,
        "pixeles_que_perderian_umbral_summit": dentro_nuestro - dentro_caja,
        "pct_que_perderia": round(100.0 * (dentro_nuestro - dentro_caja)
                                  / dentro_nuestro, 1),
        "por_sensor": {k: {**v, "pct_fuera_de_la_caja":
                           round(100.0 * (v["nuestro"] - v["caja"]) / v["nuestro"], 1)}
                       for k, v in sorted(por_sensor.items()) if v["nuestro"]},
    }

R["por_volcan"] = tab
os.makedirs(AQUI, exist_ok=True)
json.dump(R, open(os.path.join(AQUI, "01_caja_vs_circulo.json"), "w",
                  encoding="utf-8"), indent=1, ensure_ascii=False)

print("El ROI1 del paper es una CAJA de 5x5 km (25 km2) igual para todos.")
print("El nuestro es un CIRCULO de radio inner_radius_km, distinto por volcan.\n")
print("%-22s %7s %10s %8s %12s %12s %9s"
      % ("volcán", "r_km", "área km²", "×paper", "px en ROI1",
         "px en caja", "%pierde"))
for vol, f in sorted(tab.items(), key=lambda x: -x[1]["veces_el_roi1_del_paper"]):
    print("%-22s %7s %10.1f %8.1f %12d %12d %8.1f%%"
          % (vol, f["inner_radius_km"], f["area_nuestra_km2"],
             f["veces_el_roi1_del_paper"], f["pixeles_en_nuestro_roi1"],
             f["pixeles_tambien_en_la_caja"], f["pct_que_perderia"]))

tot_n = sum(f["pixeles_en_nuestro_roi1"] for f in tab.values())
tot_c = sum(f["pixeles_tambien_en_la_caja"] for f in tab.values())
print("\nTOTAL: %d píxeles reciben hoy el umbral laxo de summit; con la caja del "
      "paper serían %d (%.1f %% perdería el trato de summit)."
      % (tot_n, tot_c, 100.0 * (tot_n - tot_c) / tot_n))
print("escrito:", os.path.join(AQUI, "01_caja_vs_circulo.json"))
