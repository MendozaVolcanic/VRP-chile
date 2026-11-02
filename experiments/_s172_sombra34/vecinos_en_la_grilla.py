"""S172: qué otros volcanes de volcanoes.yaml caen dentro de la grilla de 51 x 51 km de cada uno de los 34.

POR QUÉ: la vía suma en vrp_mw TODOS los píxeles alertados de la grilla (D32), también los de fuera de la caja
sensible (con umbral más estricto). Un vecino activo dentro de la grilla puede aparecer en el record del volcán
tranquilo; el centroide (primary_cluster.centroid_dist_km) lo delata. Lista para la revisión de la sombra.
Uso: python experiments/_s172_sombra34/vecinos_en_la_grilla.py
"""
import sys
from pathlib import Path

import yaml
from pyproj import Transformer

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from pipeline import mirova_v750_codigo as MV  # noqa: E402

vols = yaml.safe_load((REPO / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]
nrt = set(yaml.safe_load((REPO / ".github/workflows/nrt.yml").read_text(encoding="utf-8"))
          ["jobs"]["process"]["strategy"]["matrix"]["volcano"])
refs = MV._referencias()
n = 0
for v in vols:
    if v["name"] in nrt:
        continue
    r = refs[v["name"]]
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{r['epsg']}", always_xy=True)
    dentro = []
    for w in vols:
        if w["name"] == v["name"]:
            continue
        x, y = t.transform(w["lon"], w["lat"])
        dx, dy = x - r["x0"], y - r["y0"]
        if abs(dx) <= 25000 and abs(dy) <= 25000:
            dentro.append(f"{w['name']}{' (Tier A)' if w['name'] in nrt else ''} a {((dx**2 + dy**2) ** 0.5) / 1000:.1f} km")
    if dentro:
        n += 1
        print(f"{v['name']:22s} {'; '.join(dentro)}")
print(f"\n{n} de 34 tienen otro volcán de volcanoes.yaml dentro de su grilla")
