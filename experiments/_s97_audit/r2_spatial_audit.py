"""S97 — AUDITORÍA ESPACIAL R2: ¿dónde detectamos vs dónde ve el calor MIROVA (TIF) vs el cráter?

El gap de mi 1ra auditoría (no detectado, señalado por Nicolás): miré métricas
agregadas (recall/ratio) pero NO la UBICACIÓN FÍSICA de las detecciones. Tupungatito
detecta al SE (glaciar), no en el lago. Puede pasar en TODOS los volcanes.

Este script usa los TIF de MIROVA (../mirova-tif-archive, ~mayo) como ground-truth de
UBICACIÓN. Por cada pasada matcheada (nuestro record <-> TIF mismo sensor ±90min):
  - centroide ponderado de radiancia del TIF  = dónde ve el calor MIROVA (método R2, A24).
  - centroide de nuestro primary_cluster        = dónde detectamos nosotros.
  - vent (cráter real, volcanoes.yaml)          = dónde está el cráter.
Distancias: d_tif_crater, d_ours_crater, d_ours_tif.

Diagnóstico:
  - d_ours_tif chico  -> coincidimos con MIROVA en ubicación (aunque esté lejos del cráter).
  - d_tif_crater grande -> MIROVA tb ve el calor lejos del cráter (campo real desplazado / coord).
  - d_ours_crater grande con d_tif_crater chico -> NUESTRO error de ubicación (displacement).

Integridad §0.5: números del script. rasterio para leer TIF (georef).
Uso: PYTHONIOENCODING=utf-8 python r2_spatial_audit.py
"""
import sys, os, io, json, math, csv
from datetime import datetime
from statistics import median
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARCH = os.path.abspath(os.path.join(REPO, "..", "mirova-tif-archive"))
sys.path.insert(0, REPO)
import yaml
import rasterio
import numpy as np
_fd = os.dup(1)
OUT = io.TextIOWrapper(os.fdopen(_fd, "wb"), encoding="utf-8", write_through=True)

TIER = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan",
        "Llaima", "Chaiten", "PlanchonPeteroa", "Lastarria", "Isluga", "Tupungatito"]
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "Villarrica": 5,
         "PuyehueCordonCaulle": 20, "Copahue": 4, "NevadosDeChillan": 5, "Llaima": 5,
         "Chaiten": 5, "PlanchonPeteroa": 3, "Isluga": 5}
# nombre del volcán en el archivo TIF (difiere para NdC)
TIF_NAME = {"NevadosDeChillan": "ChillanNevadosde"}


def hav(a, b, c, d):
    R = 6371; p = math.pi / 180
    dphi = (c - a) * p; dl = (d - b) * p
    return 2 * R * math.asin(math.sqrt(math.sin(dphi / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin(dl / 2) ** 2))


def bucket(sensor):
    s = str(sensor or "").upper()
    if "MODIS" in s: return "MODIS"
    if s.endswith("_750"): return "VIIRS750"
    if s.startswith("VIIRS"): return "VIIRS375"
    return "OTHER"


def parse_dt(s):
    if not s: return None
    s = s.replace("T", " ").split("+")[0].split(".")[0]
    for f in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try: return datetime.strptime(s, f)
        except ValueError: continue
    return None


def tif_fname_dt(path):
    # data/tif/Vol/20260509_034632_VIIRS375.tif -> 2026-05-09 03:46:32
    base = os.path.basename(path)
    try:
        return datetime.strptime(base[:15], "%Y%m%d_%H%M%S")
    except ValueError:
        return None


# config vent
ydoc = yaml.safe_load(open(os.path.join(REPO, "volcanoes.yaml"), encoding="utf-8"))
vols = ydoc if isinstance(ydoc, list) else ydoc.get("volcanoes", ydoc)
VENT = {}
for v in vols:
    if v.get("name") in TIER:
        VENT[v["name"]] = (v.get("vent_lat") or v.get("lat"), v.get("vent_lon") or v.get("lon"))

# index TIF por volcán
tif_by_vol = {v: [] for v in TIER}
with open(os.path.join(ARCH, "index.csv"), encoding="utf-8") as f:
    for row in csv.DictReader(f):
        volname = row.get("volcano")
        # mapear nombre TIF -> canónico
        canon = next((k for k, tn in TIF_NAME.items() if tn == volname), volname)
        if canon not in tif_by_vol:
            continue
        dt = tif_fname_dt(row.get("tif_path", ""))
        if dt:
            tif_by_vol[canon].append({"sensor": row.get("sensor"), "dt": dt, "path": row.get("tif_path")})


def tif_centroid(path):
    """Centroide ponderado de radiancia del TIF (lat,lon) + suma + n_pix. None si vacío."""
    full = os.path.join(ARCH, path)
    if not os.path.exists(full):
        return None
    try:
        with rasterio.open(full) as src:
            arr = src.read(1).astype(float)
            valid = (arr > 0) & np.isfinite(arr)
            if not valid.any():
                return None
            rows, cols = np.where(valid)
            w = arr[valid]
            cy = float(np.average(rows, weights=w)); cx = float(np.average(cols, weights=w))
            lon, lat = src.xy(cy, cx)
            return (lat, lon, float(w.sum()), int(valid.sum()))
    except Exception:
        return None


def cluster_mag(r, inner):
    pc = r.get("primary_cluster")
    if not pc: return 0
    if r.get("distance_class") and r.get("distance_class") != "summit": return 0
    cd = pc.get("centroid_dist_km")
    if cd is not None and cd > inner: return 0
    v = pc.get("vrp_mw") or 0
    return 0 if v > 50000 else v


W = OUT.write
W("=" * 118 + "\n")
W("AUDITORÍA ESPACIAL R2 — ¿dónde detectamos vs dónde ve el calor el TIF de MIROVA vs el cráter?\n")
W("d_tif_crater: calor MIROVA al cráter · d_ours_crater: nuestro cluster al cráter · d_ours_tif: acuerdo de ubicación.\n")
W("Match nuestro-record <-> TIF mismo sensor ±90min, ventana del archivo (~mayo).\n")
W("=" * 118 + "\n\n")
W(f"{'Volcán':<20}{'nPares':>7}{'d_tif_crát':>11}{'d_ours_crát':>12}{'d_ours_tif':>11}{'offset_mc':>10}  diagnóstico\n")
W("-" * 118 + "\n")

global_rows = []
for vol in TIER:
    recs = json.load(open(os.path.join(REPO, f"data/mirova_equivalent/{vol}.json"), encoding="utf-8")).get("records", [])
    inner = INNER.get(vol, 5)
    vlat, vlon = VENT[vol]
    tifs = tif_by_vol[vol]
    # índice TIF por bucket
    by_b = {}
    for t in tifs:
        by_b.setdefault(t["sensor"], []).append(t)
    d_tc, d_oc, d_ot = [], [], []
    for r in recs:
        cl = cluster_mag(r, inner)
        if cl <= 0:
            continue
        pc = r.get("primary_cluster") or {}
        olat, olon = pc.get("centroid_lat"), pc.get("centroid_lon")
        if olat is None:
            continue
        b = bucket(r.get("sensor"))
        dt = parse_dt(r.get("datetime_utc"))
        if not dt or b not in by_b:
            continue
        # match TIF mismo bucket ±90min
        best, bd = None, None
        for t in by_b[b]:
            d = abs((t["dt"] - dt).total_seconds())
            if d <= 5400 and (bd is None or d < bd):
                best, bd = t, d
        if not best:
            continue
        c = tif_centroid(best["path"])
        if not c:
            continue
        tlat, tlon = c[0], c[1]
        d_tc.append(hav(vlat, vlon, tlat, tlon))
        d_oc.append(hav(vlat, vlon, olat, olon))
        d_ot.append(hav(olat, olon, tlat, tlon))
    mc = next((hav(vlat, vlon, v.get("mirova_center_lat"), v.get("mirova_center_lon"))
               for v in vols if v.get("name") == vol and v.get("mirova_center_lat")), None)
    if not d_tc:
        W(f"{vol:<20}{0:>7}{'—':>11}{'—':>12}{'—':>11}{(('%.2f'%mc) if mc else '—'):>10}  (sin pares TIF)\n")
        continue
    mtc, moc, mot = median(d_tc), median(d_oc), median(d_ot)
    # diagnóstico
    if mot <= 1.0 and mtc <= 2.0:
        diag = "OK: coincidimos con MIROVA, en cráter"
    elif mot <= 1.5 and mtc > 3.0:
        diag = "MIROVA TB ve calor lejos del cráter (campo/coord)"
    elif moc > 3.0 and mtc <= 2.0:
        diag = "*** DISPLACEMENT NUESTRO: detectamos lejos, MIROVA en cráter ***"
    elif mot > 2.0:
        diag = "*** DISCREPAMOS con MIROVA en ubicación ***"
    else:
        diag = "revisar"
    W(f"{vol:<20}{len(d_tc):>7}{mtc:>11.2f}{moc:>12.2f}{mot:>11.2f}{(('%.2f'%mc) if mc else '—'):>10}  {diag}\n")
    global_rows.append((vol, len(d_tc), mtc, moc, mot))

W("-" * 118 + "\n")
W("\nLectura: 'd_ours_tif' chico = nuestra ubicación coincide con el TIF de MIROVA (aunque\n")
W("ambos estén lejos del cráter mapeado). 'd_tif_crater' grande = el propio MIROVA ve el\n")
W("calor lejos del cráter -> el desplazamiento es del CAMPO TÉRMICO (o de la coord), no\n")
W("necesariamente nuestro error. Displacement NUESTRO = d_ours_crater grande con d_tif_crater chico.\n")
OUT.flush()
