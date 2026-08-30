# -*- coding: utf-8 -*-
"""S128 Fase 2 · P1(b) — ¿DONDE ANCLA MIROVA SU GRILLA? Evidencia externa para D17.

Corrige un A89 propio: el primer paso de esta sonda leyo `mirova_center` cuando la
clave real de volcanoes.yaml es `mirova_center_lat`/`mirova_center_lon`
(pipeline/geo_utils.py:40-41). Devolvio None en los 11 y el None se leyo como
"no esta configurado". Estaba configurado en los 11.

Lo que mide, sobre las 1.960 escenas del archivo externo:

  1. **El ancla.** Si los tres sensores (con 51x51, 67x67 y 134x134 pixeles de
     distinto tamano) comparten un borde, ese borde es el ancla de la grilla. Se
     mide el desacuerdo entre sensores en los cuatro bordes y en el centro.
  2. **El KMZ contra el TIF.** Nuestro `mirova_center_*` salio en S80 del
     `LatLonBox` de los KMZ. Si el KMZ y el TIF de la MISMA pasada no coinciden,
     entonces la coordenada que el pipeline usa como "centro de MIROVA" no es el
     centro de la escena que MIROVA publico.
  3. **El offset que le queda a nuestro regrid**, que hoy se centra en
     `volcano["lat"/"lon"]` (run_pipeline.py) y no en la grilla de MIROVA.

Read-only.
"""
import collections
import csv
import io
import json
import os
import re
import statistics as st
import sys
import zipfile

import rasterio
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
ARCH = os.path.join(os.path.dirname(ROOT), "mirova-tif-archive")
ALIAS_TIF = {"ChillanNevadosde": "NevadosDeChillan"}
M_LAT = 111320.0


def m_lon(lat):
    return 111320.0 * abs(__import__("math").cos(__import__("math").radians(lat)))


cfg = {v["name"]: v for v in yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"),
                                                 encoding="utf-8"))["volcanoes"]}
G = json.load(open(os.path.join(AQUI, "01_grilla_real.json"), encoding="utf-8"))
det = G["por_volcan_sensor"]

# ── 1. El ancla: desacuerdo entre sensores, borde por borde ────────────────
ancla = {}
for vol in sorted({k.split("|")[0] for k in det}):
    ss = {k.split("|")[1]: v for k, v in det.items() if k.startswith(vol + "|")}
    lat0 = ss[list(ss)[0]]["centro"][1]

    def sp(campo, eje):
        xs = [s[campo]["mediana"] for s in ss.values()]
        return round((max(xs) - min(xs)) * (M_LAT if eje == "lat" else m_lon(lat0)), 1)

    cs = [s["centro"] for s in ss.values()]
    ancla[vol] = {
        "oeste_m": sp("oeste", "lon"), "este_m": sp("este", "lon"),
        "sur_m": sp("sur", "lat"), "norte_m": sp("norte", "lat"),
        "centro_lon_m": round((max(c[0] for c in cs) - min(c[0] for c in cs)) * m_lon(lat0), 1),
        "centro_lat_m": round((max(c[1] for c in cs) - min(c[1] for c in cs)) * M_LAT, 1),
    }

# ── 2. El KMZ contra el TIF de la MISMA pasada ─────────────────────────────
def latlonbox(kmz_path):
    try:
        with zipfile.ZipFile(kmz_path) as z:
            nm = next((n for n in z.namelist() if n.lower().endswith(".kml")), None)
            if nm is None:
                return None
            t = z.read(nm).decode("utf-8", "replace")
    except Exception:                                          # noqa: BLE001
        return None
    g = {}
    for k in ("north", "south", "east", "west"):
        m = re.search(r"<%s>\s*([-\d.eE+]+)\s*</%s>" % (k, k), t)
        if not m:
            return None
        g[k] = float(m.group(1))
    return g


kmz_vs_tif = collections.defaultdict(list)
rows = list(csv.DictReader(open(os.path.join(ARCH, "index.csv"), encoding="utf-8")))
vistos = set()
for r in rows:
    key = (r["tif_path"], r["kmz_path"])
    if key in vistos or not r["kmz_path"]:
        continue
    vistos.add(key)
    vol = ALIAS_TIF.get(r["volcano"], r["volcano"])
    kp = os.path.join(ARCH, r["kmz_path"].replace("/", os.sep))
    tp = os.path.join(ARCH, r["tif_path"].replace("/", os.sep))
    if not (os.path.exists(kp) and os.path.exists(tp)):
        continue
    box = latlonbox(kp)
    if not box:
        continue
    try:
        with rasterio.open(tp) as ds:
            b = ds.bounds
    except Exception:                                          # noqa: BLE001
        continue
    la = (box["north"] + box["south"]) / 2
    kmz_vs_tif[vol + "|" + r["sensor"]].append({
        "oeste_m": (box["west"] - b.left) * m_lon(la),
        "este_m": (box["east"] - b.right) * m_lon(la),
        "sur_m": (box["south"] - b.bottom) * M_LAT,
        "norte_m": (box["north"] - b.top) * M_LAT,
        "centro_lon_m": ((box["east"] + box["west"]) / 2 - (b.left + b.right) / 2) * m_lon(la),
        "centro_lat_m": ((box["north"] + box["south"]) / 2 - (b.bottom + b.top) / 2) * M_LAT,
    })
kmz_res = {k: {kk: round(st.median([d[kk] for d in v]), 1) for kk in v[0]}
           | {"n": len(v)} for k, v in kmz_vs_tif.items()}

# ── 3. Lo que le queda de offset a nuestro regrid ─────────────────────────
offs = {}
for vol in sorted({k.split("|")[0] for k in det}):
    c = cfg.get(vol, {})
    ss = {k.split("|")[1]: v for k, v in det.items() if k.startswith(vol + "|")}
    fila = {}
    for s, v in sorted(ss.items()):
        clon, clat = v["centro"]
        f = {"centro_tif": [round(clat, 6), round(clon, 6)]}
        if c.get("lat") is not None:
            f["vs_volcano_latlon_m"] = [round((clon - c["lon"]) * m_lon(clat), 1),
                                        round((clat - c["lat"]) * M_LAT, 1)]
        if c.get("mirova_center_lat") is not None:
            f["vs_mirova_center_m"] = [
                round((clon - c["mirova_center_lon"]) * m_lon(clat), 1),
                round((clat - c["mirova_center_lat"]) * M_LAT, 1)]
        if c.get("vent_lat") is not None:
            f["vs_vent_m"] = [round((clon - c["vent_lon"]) * m_lon(clat), 1),
                              round((clat - c["vent_lat"]) * M_LAT, 1)]
        fila[s] = f
    offs[vol] = fila

R = {"_meta": {"escenas": G["_meta"], "a89": "la clave es mirova_center_lat/_lon "
               "(geo_utils.py:40-41), no mirova_center"},
     "ancla_desacuerdo_entre_sensores_m": ancla,
     "kmz_menos_tif_m": kmz_res, "offset_del_centro_del_tif_m": offs}
json.dump(R, open(os.path.join(AQUI, "01b_ancla.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)

print("== 1. ANCLA: desacuerdo entre los 3 sensores (m). 0 = ese borde es el ancla ==")
print("%-22s%9s%9s%9s%9s%10s%10s" % ("volcan", "OESTE", "este", "SUR", "norte",
                                     "c_lon", "c_lat"))
for v, a in sorted(ancla.items()):
    print("%-22s%9.1f%9.1f%9.1f%9.1f%10.1f%10.1f" % (
        v, a["oeste_m"], a["este_m"], a["sur_m"], a["norte_m"],
        a["centro_lon_m"], a["centro_lat_m"]))

print("\n== 2. KMZ menos TIF, misma pasada (m). 0 = el KMZ describe el mismo marco ==")
print("%-34s%5s%9s%9s%9s%9s%10s%10s" % ("volcan|sensor", "n", "oeste", "este",
                                        "sur", "norte", "c_lon", "c_lat"))
for k, d in sorted(kmz_res.items()):
    print("%-34s%5d%9.1f%9.1f%9.1f%9.1f%10.1f%10.1f" % (
        k, d["n"], d["oeste_m"], d["este_m"], d["sur_m"], d["norte_m"],
        d["centro_lon_m"], d["centro_lat_m"]))

print("\n== 3. Centro del TIF menos nuestras anclas (m; +E/+N) ==")
print("%-22s%-9s%22s%22s%20s" % ("volcan", "sensor", "vs volcano_lat/lon",
                                 "vs mirova_center", "vs vent"))
for v, f in sorted(offs.items()):
    for s, d in f.items():
        print("%-22s%-9s%22s%22s%20s" % (v, s, d.get("vs_volcano_latlon_m"),
                                         d.get("vs_mirova_center_m"), d.get("vs_vent_m")))
