# -*- coding: utf-8 -*-
"""S142: cota superior, SÓLO con el OSF, de la muestra nevada por año (VIIRS 375 m, noche).

POR QUÉ. La muestra exige nuestro pico persistido, y antes de 2025-02-15 no hay records nuestros.
Para decidir si vale un backfill hay que saber, antes de gastarlo, qué años podrían dar >= 3
volcanes nevados. Esta cota reemplaza "foco OSF a <= 0,75 km de NUESTRO pico" (H1) por "foco OSF a
<= 0,75 km del CRÁTER": no es el criterio, es un techo optimista (nuestro pico puede caer lejos, como
en Nevados de Chillán 2025, y la clase candidato/control depende de pub_n, que aquí no existe).

Mismo filtro de filas que scripts/descomponer_magnitud_osf.py (class 1, VRP > 0, Dayflag 0, 375 m)
más Npix >= 3 de muestra.py. Salida (S91): cota_osf_anual.json.
"""
import collections
import json
import os
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
for _p in (R, R / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

from descomponer_magnitud_osf import MAP, OSF_DEFECTO  # noqa: E402
from build_c2ab_windows import NEVADO  # noqa: E402
from run_pipeline import load_volcanoes  # noqa: E402
from pipeline.f5_core import _hav_km  # noqa: E402

RADIO = 0.75


def main():
    vents = {v["name"]: (v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])) for v in load_volcanoes()}
    o = pd.read_csv(OSF_DEFECTO)
    o["t"] = pd.to_datetime(o.timeUTC, format="%d/%m/%Y %H:%M", errors="coerce")
    o = o[o.Volc_Name.isin(MAP) & (o.Dayflag == 0) & (o["class"] == 1) & (o.VRP > 0) & (o.Npix >= 3)
          & (o.Resolution.astype(int) == 375)].copy()
    o["vol"] = o.Volc_Name.map(MAP)
    o = o[o.vol.isin(NEVADO)]
    cerca = collections.defaultdict(lambda: collections.Counter())
    total = collections.defaultdict(lambda: collections.Counter())
    for x in o.itertuples():
        y = int(x.t.year)
        total[y][x.vol] += 1
        if x.LAT == x.LAT and x.LON == x.LON and _hav_km(x.LAT, x.LON, *vents[x.vol]) <= RADIO:
            cerca[y][x.vol] += 1
    por_anio = {}
    for y in sorted(total):
        vols_ge3 = sorted(v for v, n in cerca[y].items() if n >= 3)
        por_anio[str(y)] = {"npix_ge_3": dict(sorted(total[y].items())),
                            "foco_le_0_75_km_crater": dict(sorted(cerca[y].items())),
                            "volcanes_con_ge_3_cerca": vols_ge3, "n_volcanes_con_ge_3_cerca": len(vols_ge3)}
    out = {"radio_km": RADIO, "nota": "techo optimista: cráter en vez de nuestro pico; sin clase candidato/control",
           "por_anio": por_anio}
    (HERE / "cota_osf_anual.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for y, b in por_anio.items():
        print(y, b["n_volcanes_con_ge_3_cerca"], b["foco_le_0_75_km_crater"])


if __name__ == "__main__":
    main()
