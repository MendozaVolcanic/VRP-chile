"""
Subagente E S86 — Auditoría profunda de "FPs": ¿artefacto o realidad física?

Reusa la lógica de cruce de script_C (CONS+OCR como ground truth MIROVA) para
identificar los FPs operacionales actuales. Luego:

Tarea 1: re-cruza con tolerancia ±1 día sobre OCR para detectar (a) "falsos FP"
         (MIROVA SÍ los publicó pero el cruce exacto los perdió por mismatch).
Tarea 2: clasificación geográfica (b)/(c)/(d) usando coords del cluster
         comparadas contra:
           - mirova_center / vent / inner_radius KMZ
           - 18 clusters cartografiados S85 Fase C
           - features volcánicas conocidas (Smithsonian GVP).
Tarea 3: 20 FPs aleatorios estratificados para validación humana en Earth.
Tarea 4: lectura volcán-por-volcán.

Output: E_fp_classification.{json,md}
"""
from __future__ import annotations

import io
import json
import math
import random
import sys
from collections import Counter, defaultdict
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
OUT.mkdir(parents=True, exist_ok=True)

CHILE_TZ = ZoneInfo("America/Santiago")
random.seed(42)

# ---------------------------------------------------------------------------
# Mapping replicado de script_C
# ---------------------------------------------------------------------------
TIER_A_MAP = {
    "Chaiten":               "Chaiten",
    "Copahue":               "Copahue",
    "Isluga":                "Isluga",
    "Lascar":                "Lascar",
    "Lastarria":             "Lastarria",
    "Llaima":                "Llaima",
    "Nevados de Chillan":    "NevadosDeChillan",
    "PlanchonPeteroa":       "PlanchonPeteroa",
    "Peteroa":               "PlanchonPeteroa",
    "Puyehue-Cordon Caulle": "PuyehueCordonCaulle",
    "Tupungatito":           "Tupungatito",
    "Villarrica":            "Villarrica",
}


def csv_sensor_bucket(s):
    if s == "MODIS": return "MODIS"
    if s in ("VIIRS", "VIIRS375"): return "VIIRS375"
    if s == "VIIRS750": return "VIIRS750"
    return None


def json_sensor_bucket(s):
    s = (s or "").upper()
    if s.startswith("MODIS"): return "MODIS"
    if s.startswith("VIIRS") and s.endswith("_750"): return "VIIRS750"
    if s.startswith("VIIRS"): return "VIIRS375"
    return None


# ---------------------------------------------------------------------------
# Volcanoes config
# ---------------------------------------------------------------------------
VOLC_YAML = yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))
VOL_CFG = {}
for v in VOLC_YAML["volcanoes"]:
    if v.get("mirova_monitored"):
        VOL_CFG[v["name"]] = {
            "vent_lat": float(v.get("vent_lat")),
            "vent_lon": float(v.get("vent_lon")),
            "mirova_lat": float(v.get("mirova_center_lat") or v["vent_lat"]),
            "mirova_lon": float(v.get("mirova_center_lon") or v["vent_lon"]),
            "inner": float(v.get("inner_radius_km", 5.0)),
            "exclude_zones": v.get("exclude_zones") or [],
        }

TIER_A = sorted(VOL_CFG.keys())


# ---------------------------------------------------------------------------
# Features volcánicas extendidas (S85 Fase C + GVP)
# Coords verificadas en docs/F_S81_C_1_ZONES_CATALOG.md
# ---------------------------------------------------------------------------
# Categoría B (volcánico real, MIROVA no necesariamente publica)
VOLCANIC_EXTENDED = {
    "NevadosDeChillan": [
        {"name": "Cerro Blanco / Nuevo subcomplejo",  "lat": -36.831, "lon": -71.397, "r": 3.0, "src": "S85FaseC c6"},
        {"name": "Cráteres alineados NW",              "lat": -36.870, "lon": -71.400, "r": 4.0, "src": "GVP 17 puntos eruptivos"},
    ],
    "Llaima": [
        {"name": "Pichi-Llaima cono",                   "lat": -38.696, "lon": -71.743, "r": 2.0, "src": "S85FaseC c13"},
        {"name": "Conos adventicios SW",                "lat": -38.722, "lon": -71.845, "r": 3.0, "src": "S85FaseC c14 (~40 adventicios)"},
    ],
    "Lastarria": [
        {"name": "Lazufre / Cordón del Azufre",         "lat": -25.174, "lon": -68.627, "r": 5.0, "src": "S85FaseC c17, Frontiers 2023 sulfur flows"},
    ],
    "Tupungatito": [
        {"name": "Cráter norte breached caldera",       "lat": -33.391, "lon": -69.823, "r": 2.0, "src": "S85FaseC c18"},
    ],
    "PlanchonPeteroa": [
        # PP es complejo multi-cráter Planchón+Peteroa+Azufre (A22)
        {"name": "Cráter Planchón (N)",                 "lat": -35.224, "lon": -70.570, "r": 2.0, "src": "GVP Planchon-Peteroa complex"},
        {"name": "Cráter Azufre (S)",                   "lat": -35.260, "lon": -70.578, "r": 2.0, "src": "GVP — Azufre flanco S del complejo"},
    ],
    "PuyehueCordonCaulle": [
        # Lacolito difuso fuera del centroide (A20) - el lacolito 2011-2012 está al N-NW
        {"name": "Lacolito 2011-2012",                  "lat": -40.520, "lon": -72.180, "r": 4.0, "src": "Bertin 2019 lacolito 707km² intrusión"},
        {"name": "Cordón Caulle fissure swarm",         "lat": -40.535, "lon": -72.190, "r": 5.0, "src": "GVP fisural NW-SE 17km"},
    ],
    "Copahue": [
        # cráter principal con lago + alineación 9 cráteres ENE-WSW
        {"name": "Alineamiento cráteres ENE-WSW",       "lat": -37.856, "lon": -71.190, "r": 2.5, "src": "S85FaseC c4 (flanco SW cráter)"},
    ],
    "Lascar": [
        {"name": "Cráter Aguas Calientes (satélite)",   "lat": -23.399, "lon": -67.767, "r": 2.0, "src": "S85FaseC c1, GVP"},
    ],
    "Chaiten": [],
    "Isluga": [],
    "Villarrica": [],
}

# Categoría C (geotermal / lacustre / NO volcánico real)
GEOTERMAL_NONVOLC = {
    "Copahue": [
        {"name": "Campo geotermal Las Máquinas",        "lat": -37.831, "lon": -71.182, "r": 2.0, "src": "S85FaseC c2, 165 t CO2/d"},
        {"name": "Lago Caviahue",                       "lat": -37.880, "lon": -71.090, "r": 3.0, "src": "exclude_zones existente"},
    ],
    "NevadosDeChillan": [
        {"name": "Cuenca Río Diguillín (Pinto/Coihueco)", "lat": -37.009, "lon": -71.390, "r": 4.0, "src": "S85FaseC c11"},
        {"name": "Laderas glaciales NW lejanas",        "lat": -36.800, "lon": -71.430, "r": 3.0, "src": "S85FaseC c7,c9,c10"},
    ],
    "PlanchonPeteroa": [
        {"name": "Ladera argentina Malargüe NE",        "lat": -35.051, "lon": -70.502, "r": 3.0, "src": "S85FaseC c15"},
        {"name": "Valle Río Claro argentino NE",        "lat": -35.231, "lon": -70.390, "r": 3.0, "src": "S85FaseC c16"},
    ],
    "Llaima": [
        {"name": "Bosque/cultivo Cherquenco SW lejano", "lat": -38.876, "lon": -71.906, "r": 4.0, "src": "S85FaseC c12"},
    ],
    "Villarrica": [
        # exclude_zones existentes operacionales (Lago Calafquen, urbano Pucón)
    ],
    "Lastarria": [],
    "Lascar": [],
    "Tupungatito": [],
    "Chaiten": [],
    "Isluga": [],
    "PuyehueCordonCaulle": [],
}


def haversine_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2): return None
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))


def bearing_deg(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2): return None
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl)*math.cos(p2)
    y = math.cos(p1)*math.sin(p2) - math.sin(p1)*math.cos(p2)*math.cos(dl)
    b = math.degrees(math.atan2(x, y))
    return (b + 360) % 360


def bearing_to_cardinal(b):
    if b is None: return "?"
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return dirs[int((b + 11.25) % 360 / 22.5)]


# ---------------------------------------------------------------------------
# Load MIROVA refs CONS+OCR (idéntico script_C pero conservo Fecha_Captura_Chile)
# ---------------------------------------------------------------------------
def load_mirova():
    cons = pd.read_csv(ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv")
    ocr = pd.read_csv(ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv")
    cons["source"] = "CONS"; ocr["source"] = "OCR"
    cols = ["Fecha_Satelite_UTC","Volcan","Sensor","VRP_MW","Distancia_km","Tipo_Registro","source"]
    df = pd.concat([cons[cols], ocr[cols]], ignore_index=True)
    df = df[df["Volcan"].isin(TIER_A_MAP)].copy()
    df["volc_json"] = df["Volcan"].map(TIER_A_MAP)
    df["sensor_bucket"] = df["Sensor"].apply(csv_sensor_bucket)
    df = df[df["sensor_bucket"].notna()]
    df["dt_utc"] = pd.to_datetime(df["Fecha_Satelite_UTC"], errors="coerce", utc=True)
    df = df[df["dt_utc"].notna()]
    df["night_local"] = df["dt_utc"].dt.tz_convert(CHILE_TZ).dt.date
    df["is_alerta"] = df["Tipo_Registro"].isin(["ALERTA_TERMICA","ALERTA_TERMICA_OCR"])
    return df


# ---------------------------------------------------------------------------
# Load nuestros records (idéntico script_C pero conservando coords cluster)
# ---------------------------------------------------------------------------
def load_ours():
    rows = []
    for vol in TIER_A:
        fp = ROOT / "data/mirova_equivalent" / f"{vol}.json"
        if not fp.exists(): continue
        data = json.loads(fp.read_text(encoding="utf-8"))
        cfg = VOL_CFG[vol]
        for r in data.get("records", []):
            bucket = json_sensor_bucket(r.get("sensor",""))
            if bucket is None: continue
            dt_str = r.get("datetime_utc") or r.get("acquisition_time_utc")
            if not dt_str: continue
            try:
                dt_utc = pd.to_datetime(dt_str, utc=True)
            except Exception:
                continue
            night = dt_utc.tz_convert(CHILE_TZ).date()
            pc = r.get("primary_cluster") or {}
            pc_vrp = float(pc.get("vrp_mw") or 0.0)
            pc_dist = pc.get("centroid_dist_km")
            pc_dist = float(pc_dist) if pc_dist is not None else None
            pc_lat = pc.get("centroid_lat")
            pc_lon = pc.get("centroid_lon")
            try:
                pc_lat = float(pc_lat) if pc_lat is not None else None
                pc_lon = float(pc_lon) if pc_lon is not None else None
            except Exception:
                pc_lat = pc_lon = None
            dist_class = r.get("distance_class","")

            publishable = (
                pc_vrp > 0
                and pc_dist is not None
                and pc_dist <= cfg["inner"]
                and dist_class == "summit"
            )
            n_bt = int(r.get("diag_n_bt_path") or 0)
            n_nti = int(r.get("diag_n_nti_path") or 0)
            n_dnti = int(r.get("diag_n_dnti_ctx_path") or 0)
            paths = []
            if n_bt: paths.append("A")
            if n_nti: paths.append("BC")
            if n_dnti: paths.append("D")
            path_str = "+".join(paths) if paths else "none"

            rows.append({
                "volc_json": vol,
                "sensor_raw": r.get("sensor",""),
                "sensor_bucket": bucket,
                "dt_utc": dt_utc,
                "night_local": night,
                "pc_vrp_mw": pc_vrp,
                "pc_n_pixels": int(pc.get("n_pixels") or 0),
                "pc_centroid_dist_km": pc_dist,
                "pc_lat": pc_lat,
                "pc_lon": pc_lon,
                "pc_path": path_str,
                "publishable": publishable,
                "t_bg_k": r.get("t_bg_k"),
                "t_max_k": r.get("t_max_k"),
            })
    return pd.DataFrame(rows)


MIROVA = load_mirova()
OURS = load_ours()
print(f"[INFO] MIROVA loaded: {len(MIROVA)} rows | ALERTAs: {MIROVA['is_alerta'].sum()}")
print(f"[INFO] OURS loaded: {len(OURS)} rows | publishable: {OURS['publishable'].sum()}")

MIN_N = max(MIROVA["night_local"].min(), OURS["night_local"].min())
MAX_N = min(MIROVA["night_local"].max(), OURS["night_local"].max())
MIROVA = MIROVA[(MIROVA["night_local"] >= MIN_N) & (MIROVA["night_local"] <= MAX_N)]
OURS = OURS[(OURS["night_local"] >= MIN_N) & (OURS["night_local"] <= MAX_N)]
print(f"[INFO] Window: {MIN_N} -> {MAX_N}")


# ---------------------------------------------------------------------------
# Identificar FPs operacionales actuales
# ---------------------------------------------------------------------------
mirova_alerta_keys = set()
mirova_alerta_by_vol_sensor = defaultdict(set)  # para tolerancia +/- 1d
for _, row in MIROVA[MIROVA["is_alerta"]].iterrows():
    key = (row["volc_json"], row["sensor_bucket"], row["night_local"])
    mirova_alerta_keys.add(key)
    mirova_alerta_by_vol_sensor[(row["volc_json"], row["sensor_bucket"])].add(row["night_local"])

# Cualquier ALERTA en MIROVA agrupada por vol (sin sensor) para tolerancia más laxa
mirova_alerta_by_vol = defaultdict(set)
for (vol, _sens, night) in mirova_alerta_keys:
    mirova_alerta_by_vol[vol].add(night)

# Para tarea 1: cross-sensor flexibility (MIROVA puede haber publicado VIIRS pero nosotros vemos MODIS misma noche)
mirova_alerta_keys_anysensor = set((vol, n) for (vol, _s, n) in mirova_alerta_keys)


# Publishable records nuestros
PUB = OURS[OURS["publishable"]].copy().reset_index(drop=True)
print(f"[INFO] Publishable records nuestros: {len(PUB)}")

def is_match_strict(row):
    return (row["volc_json"], row["sensor_bucket"], row["night_local"]) in mirova_alerta_keys

PUB["match_strict"] = PUB.apply(is_match_strict, axis=1)
FP_STRICT = PUB[~PUB["match_strict"]].copy().reset_index(drop=True)
print(f"[INFO] FPs estrictos (cruce exacto): {len(FP_STRICT)}")


# ---------------------------------------------------------------------------
# TAREA 1 — Re-cruzar con tolerancia ±1 día y cross-sensor
# ---------------------------------------------------------------------------
def recover_a_class(row):
    vol = row["volc_json"]; bucket = row["sensor_bucket"]; night = row["night_local"]
    # ±1 día mismo sensor
    for dd in (-1, 1):
        cand = night + timedelta(days=dd)
        if (vol, bucket, cand) in mirova_alerta_keys:
            return f"±1d_same_sensor(d={dd})"
    # mismo día cualquier sensor
    if (vol, night) in mirova_alerta_keys_anysensor:
        return "same_night_cross_sensor"
    # ±1 día cualquier sensor
    for dd in (-1, 1):
        cand = night + timedelta(days=dd)
        if (vol, cand) in mirova_alerta_keys_anysensor:
            return f"±1d_cross_sensor(d={dd})"
    return None


FP_STRICT["recovery_a"] = FP_STRICT.apply(recover_a_class, axis=1)
FP_A = FP_STRICT[FP_STRICT["recovery_a"].notna()].copy()
FP_RESIDUAL = FP_STRICT[FP_STRICT["recovery_a"].isna()].copy().reset_index(drop=True)
print(f"[TAREA 1] FPs recuperados como categoría (a): {len(FP_A)} / {len(FP_STRICT)} = {len(FP_A)/max(len(FP_STRICT),1)*100:.1f}%")
print(f"[TAREA 1] FPs residuales para clasificación geográfica: {len(FP_RESIDUAL)}")
print("[TAREA 1] desglose recovery_a:")
for k, n in Counter(FP_A["recovery_a"]).most_common():
    print(f"   {k}: {n}")


# ---------------------------------------------------------------------------
# TAREA 2 — Clasificación geográfica
# ---------------------------------------------------------------------------
def classify_geographic(row):
    vol = row["volc_json"]
    cfg = VOL_CFG[vol]
    lat, lon = row["pc_lat"], row["pc_lon"]
    t_bg = row["t_bg_k"]
    n_pix = row["pc_n_pixels"]
    pc_dist = row["pc_centroid_dist_km"]

    # Sin coords → solo dist
    if lat is None or lon is None:
        # caer a clasificación heurística por dist + path
        if pc_dist is not None and pc_dist <= cfg["inner"] * 0.5:
            return "b_volcanic_real_no_coords", "cluster intra-inner_radius/2 sin coords (presumido cráter)"
        return "d_artifact_no_coords", "sin coords, dist incierta"

    # Distancia al mirova_center / vent
    d_mirova = haversine_km(lat, lon, cfg["mirova_lat"], cfg["mirova_lon"])
    d_vent   = haversine_km(lat, lon, cfg["vent_lat"], cfg["vent_lon"])

    # ¿Coincide con feature volcánica extendida del complejo?
    for f in VOLCANIC_EXTENDED.get(vol, []):
        d = haversine_km(lat, lon, f["lat"], f["lon"])
        if d is not None and d <= f["r"]:
            return "b_volcanic_real_complex", f"≤{f['r']:.1f}km de {f['name']} ({f['src']})"

    # ¿Coincide con geotermal/lacustre no-volcánico?
    for f in GEOTERMAL_NONVOLC.get(vol, []):
        d = haversine_km(lat, lon, f["lat"], f["lon"])
        if d is not None and d <= f["r"]:
            return "c_geothermal_lacustrine", f"≤{f['r']:.1f}km de {f['name']} ({f['src']})"

    # ¿Dentro del cráter / vent estricto (<2 km del vent oficial)?
    if d_vent is not None and d_vent <= 2.0:
        return "b_volcanic_real_summit", f"≤2.0km vent nominal ({d_vent:.2f} km)"

    # ¿Dentro del mirova_center inner pero sin feature catalogada?
    if d_mirova is not None and d_mirova <= cfg["inner"]:
        # Heurística artefacto: cirrus alto frío (A23)
        try:
            if t_bg is not None and float(t_bg) < 260.0:
                return "d_artifact_cirrus", f"intra-inner pero t_bg={float(t_bg):.1f}K <260K (cirrus A23)"
        except Exception:
            pass
        # Heurística artefacto: glaciar Tupungatito ring warm (A19)
        if vol == "Tupungatito" and d_vent is not None and d_vent > 3.0:
            return "d_artifact_glacier_ring", f"Tupungatito ring glaciar (d_vent={d_vent:.2f}km, A19)"
        # singleton lejos del vent (>inner*0.7)
        if d_vent is not None and d_vent > cfg["inner"] * 0.7 and n_pix <= 3:
            return "d_artifact_singleton", f"singleton {n_pix}px lejos del vent ({d_vent:.2f}km)"
        return "b_volcanic_real_unmapped", f"intra-inner sin feature catalogada (d_vent={d_vent:.2f}km)"

    # Fuera del inner pero fue publishable? (no debería, pero por consistencia)
    return "d_artifact_outside_inner", f"d_mirova={d_mirova:.2f}km > inner={cfg['inner']:.1f}"


classif = FP_RESIDUAL.apply(classify_geographic, axis=1, result_type="expand")
FP_RESIDUAL["category"] = classif[0]
FP_RESIDUAL["reason"] = classif[1]


def collapse_cat(c):
    if c.startswith("b_"): return "b_volcanic_real"
    if c.startswith("c_"): return "c_geothermal_nonvolc"
    if c.startswith("d_"): return "d_artifact"
    return "unknown"


FP_RESIDUAL["category_top"] = FP_RESIDUAL["category"].apply(collapse_cat)

# Matriz vol × categoría
matrix = (FP_RESIDUAL.groupby(["volc_json","category_top"]).size()
          .unstack(fill_value=0).reindex(TIER_A, fill_value=0))
for col in ["b_volcanic_real","c_geothermal_nonvolc","d_artifact"]:
    if col not in matrix.columns: matrix[col] = 0
matrix = matrix[["b_volcanic_real","c_geothermal_nonvolc","d_artifact"]]
matrix["total"] = matrix.sum(axis=1)
matrix_total = matrix.sum(axis=0)

print("\n[TAREA 2] Matriz volcán × categoría (FPs residuales post-Tarea 1):")
print(matrix.to_string())
print("\nTotal:")
print(matrix_total.to_string())

cat_detail = Counter(FP_RESIDUAL["category"])
print("\n[TAREA 2] Detalle subcategorías:")
for k, n in cat_detail.most_common():
    print(f"   {k}: {n}")


# ---------------------------------------------------------------------------
# TAREA 3 — 20 FPs estratificados para validación humana
# ---------------------------------------------------------------------------
# Tomar 20 estratificados: ~2 por volcán + variedad de categorías
sample_rows = []
for vol in TIER_A:
    sub = FP_RESIDUAL[FP_RESIDUAL["volc_json"] == vol]
    if len(sub) == 0: continue
    n = min(2, len(sub))
    idx = random.sample(list(sub.index), n)
    sample_rows.extend(idx)
# Si <20, completar con random
if len(sample_rows) < 20:
    pool = list(set(FP_RESIDUAL.index) - set(sample_rows))
    extra = random.sample(pool, min(20 - len(sample_rows), len(pool)))
    sample_rows.extend(extra)
sample_rows = sample_rows[:20]

SAMPLE = FP_RESIDUAL.loc[sample_rows].copy()


def fmt_sample_row(r):
    cfg = VOL_CFG[r["volc_json"]]
    d_vent = haversine_km(r["pc_lat"], r["pc_lon"], cfg["vent_lat"], cfg["vent_lon"])
    b = bearing_deg(cfg["vent_lat"], cfg["vent_lon"], r["pc_lat"], r["pc_lon"])
    return {
        "vol": r["volc_json"],
        "sensor": r["sensor_bucket"],
        "night": str(r["night_local"]),
        "lat": round(r["pc_lat"], 4) if r["pc_lat"] is not None else None,
        "lon": round(r["pc_lon"], 4) if r["pc_lon"] is not None else None,
        "d_vent_km": round(d_vent, 2) if d_vent is not None else None,
        "bearing": bearing_to_cardinal(b),
        "pc_vrp_mw": round(float(r["pc_vrp_mw"]), 3),
        "pc_n_pixels": int(r["pc_n_pixels"]),
        "t_bg_k": round(float(r["t_bg_k"]), 1) if r["t_bg_k"] else None,
        "path": r["pc_path"],
        "category": r["category"],
        "reason": r["reason"],
    }


SAMPLE_LIST = [fmt_sample_row(r) for _, r in SAMPLE.iterrows()]


# ---------------------------------------------------------------------------
# Output JSON
# ---------------------------------------------------------------------------
out_json = {
    "window": {"start": str(MIN_N), "end": str(MAX_N)},
    "n_publishable_records": int(len(PUB)),
    "n_fp_strict": int(len(FP_STRICT)),
    "tarea_1_recovery_a": {
        "n_recovered_as_a": int(len(FP_A)),
        "pct_of_fp": round(len(FP_A)/max(len(FP_STRICT),1)*100, 2),
        "recovery_breakdown": dict(Counter(FP_A["recovery_a"])),
        "n_residual": int(len(FP_RESIDUAL)),
    },
    "tarea_2_geographic_matrix": {
        "by_vol_x_cat": {vol: {c: int(matrix.loc[vol, c]) for c in matrix.columns}
                        for vol in matrix.index},
        "totals": {c: int(matrix_total[c]) for c in matrix.columns},
        "subcat_detail": {k: int(n) for k, n in cat_detail.most_common()},
        "pct_residual": {
            "b_volcanic_real": round(int(matrix_total["b_volcanic_real"])/max(len(FP_RESIDUAL),1)*100, 2),
            "c_geothermal_nonvolc": round(int(matrix_total["c_geothermal_nonvolc"])/max(len(FP_RESIDUAL),1)*100, 2),
            "d_artifact": round(int(matrix_total["d_artifact"])/max(len(FP_RESIDUAL),1)*100, 2),
        },
    },
    "tarea_3_sample_for_human_review": SAMPLE_LIST,
}

(OUT / "E_fp_classification.json").write_text(json.dumps(out_json, indent=2, default=str), encoding="utf-8")
print(f"\n[OK] JSON escrito: {OUT/'E_fp_classification.json'}")


# ---------------------------------------------------------------------------
# Output Markdown
# ---------------------------------------------------------------------------
md = []
md.append("# Subagente E S86 — Auditoría profunda FPs: artefacto vs realidad física\n")
md.append(f"**Ventana**: {MIN_N} → {MAX_N}  ")
md.append(f"**Publishable records nuestros**: {len(PUB)}  ")
md.append(f"**FPs estrictos (cruce exacto vs CONS+OCR)**: {len(FP_STRICT)}\n")

md.append("## Hallazgo central\n")
n_a = len(FP_A); n_b = int(matrix_total["b_volcanic_real"]); n_c = int(matrix_total["c_geothermal_nonvolc"]); n_d = int(matrix_total["d_artifact"])
total_classified = n_a + n_b + n_c + n_d
md.append(f"De los {len(FP_STRICT)} FPs operacionales:\n")
md.append(f"- **(a) Falsos FP (MIROVA SÍ publicó, mismatch ±1d / cross-sensor)**: {n_a} = **{n_a/total_classified*100:.1f}%**")
md.append(f"- **(b) Anomalía volcánica REAL no publicada por MIROVA**: {n_b} = **{n_b/total_classified*100:.1f}%**")
md.append(f"- **(c) Geotermal / lacustre NO volcánico real**: {n_c} = **{n_c/total_classified*100:.1f}%**")
md.append(f"- **(d) Artefacto (cirrus / glaciar / singleton)**: {n_d} = **{n_d/total_classified*100:.1f}%**\n")

md.append(f"**Realidad física total ((a)+(b)+(c))**: {n_a+n_b+n_c} = **{(n_a+n_b+n_c)/total_classified*100:.1f}%**  ")
md.append(f"**Artefactos ((d))**: {n_d} = **{n_d/total_classified*100:.1f}%**\n")

md.append("## Tarea 1 — Recuperación categoría (a) por tolerancia\n")
md.append("| Mecanismo de recuperación | n |")
md.append("|---|---:|")
for k, n in Counter(FP_A["recovery_a"]).most_common():
    md.append(f"| {k} | {n} |")
md.append(f"| **Total recuperados (a)** | **{n_a}** |")
md.append(f"| **Residuales para Tarea 2** | **{len(FP_RESIDUAL)}** |\n")

md.append("## Tarea 2 — Matriz volcán × categoría (FPs residuales)\n")
md.append("| Volcán | b (volcánico real) | c (geotermal no-volc) | d (artefacto) | total |")
md.append("|---|---:|---:|---:|---:|")
for vol in matrix.index:
    md.append(f"| {vol} | {matrix.loc[vol,'b_volcanic_real']} | {matrix.loc[vol,'c_geothermal_nonvolc']} | {matrix.loc[vol,'d_artifact']} | {matrix.loc[vol,'total']} |")
md.append(f"| **TOTAL** | **{matrix_total['b_volcanic_real']}** | **{matrix_total['c_geothermal_nonvolc']}** | **{matrix_total['d_artifact']}** | **{matrix_total['total']}** |\n")

md.append("### Subcategorías detalladas\n")
md.append("| Subcategoría | n |")
md.append("|---|---:|")
for k, n in cat_detail.most_common():
    md.append(f"| {k} | {n} |")
md.append("")

md.append("## Tarea 3 — 20 FPs para validación humana (Google Earth / KMZ)\n")
md.append("Lat/lon decimal grados. Sensor + noche local Chile. Pegar lat,lon en Earth.\n")
md.append("| # | Volcán | Sensor | Noche | Lat | Lon | dist vent | bearing | VRP MW | n pix | t_bg K | Path | Categoría | Razón |")
md.append("|---:|---|---|---|---:|---:|---:|---|---:|---:|---:|---|---|---|")
for i, s in enumerate(SAMPLE_LIST, 1):
    md.append(f"| {i} | {s['vol']} | {s['sensor']} | {s['night']} | {s['lat']} | {s['lon']} | {s['d_vent_km']} | {s['bearing']} | {s['pc_vrp_mw']} | {s['pc_n_pixels']} | {s['t_bg_k']} | {s['path']} | {s['category']} | {s['reason']} |")
md.append("")

md.append("## Tarea 4 — Lectura geológica volcán por volcán\n")

geo_readings = {
    "Chaiten": (
        "Cráter actual con domo riolítico post-2008 al fondo de la caldera. "
        "Señal térmica esperada: domo central + fumarolas residuales. "
        "Inner=5km cubre el cráter completo (~1.3km diámetro). "
    ),
    "Copahue": (
        "Cráter El Agrio con lago crater hiperácido + alineamiento E-W de 9 cráteres. "
        "Señal térmica real: cráter + Las Máquinas (geotermal NO eruptivo, 165 t CO2/d). "
        "MIROVA suprime Las Máquinas. Lago Caviahue ya en exclude_zones. "
    ),
    "Isluga": (
        "Cráter cumbre con fumarolas persistentes, sin lago. "
        "Señal MIROVA esperada: pixel summit por fumarolas + ΔT ~20K. "
        "Tier A Alto, calibración natural sin patches. "
    ),
    "Lascar": (
        "Cráter activo V (V-shape) con lava lake intermitente. ΔT ~21.6K. "
        "Tier A Alto. Cluster cráter Aguas Calientes 5km SW podría ser satélite real. "
        "Mejor calibrado del Tier A. "
    ),
    "Lastarria": (
        "Cráter cumbre + sistema Lazufre (Cordón del Azufre) regional 12km SW con sulfur flows e InSAR inflación. "
        "Inner=3km del KMZ es muy estrecho para Lazufre. "
        "Frontiers 2023 confirma sulfur flows = anomalía térmica REAL no eruptiva pero volcánica. "
    ),
    "Llaima": (
        "Cráter cumbre + Pichi-Llaima (cono coalescente SSE) + ~40 conos adventicios SW-NE arc. "
        "Inner=5km cubre cráter principal pero no los conos. "
        "Cluster Pichi-Llaima 1.28km SW es feature volcánica real del complejo. "
    ),
    "NevadosDeChillan": (
        "Complejo 17 cráteres alineados NW-SE incluyendo subcomplejo Cerro Blanco / Nuevo. "
        "Cuenca Río Diguillín 16km SW = geotermal no eruptivo (Pinto/Coihueco). "
        "Inner=5km insuficiente para el complejo extendido. "
    ),
    "PlanchonPeteroa": (
        "Multi-cráter: Planchón (N), Peteroa (centro), Azufre (S, flanco). "
        "Comportamiento bimodal A22 (S70 T1 N=7): a veces aísla Peteroa, a veces el halo regional. "
        "Mediana ratio 2.08× varianza alta. Inner=3km cubre solo Peteroa. "
    ),
    "PuyehueCordonCaulle": (
        "Lacolito 2011-2012 = anomalía difusa NO focal de 707km² (A20). "
        "El método R2 con centroide NO aplica acá. Cordón Caulle fisural NW-SE 17km. "
        "Inner=20km del KMZ refleja esta extensión. "
    ),
    "Tupungatito": (
        "Cráter norte breached caldera con cono piroclástico activo + ring glaciar enorme. "
        "Patrón térmico A19: ring glaciar warm-relativo confunde kernel local. "
        "Kernel-bg EMPEORA Tupungatito (10.37→18.46×). Inner=7km incluye el ring. "
    ),
    "Villarrica": (
        "Lava lake persistente en cráter cumbre, ΔT ~12K (Tier A Muy Bajo). "
        "Señal sub-pixel característica. Glaciar cumbre puede producir mezcla. "
        "Exclude_zones existentes: Lago Calafquen + zona urbana Pucón. "
    ),
}

for vol in TIER_A:
    total = int(matrix.loc[vol, "total"])
    b = int(matrix.loc[vol, "b_volcanic_real"])
    c = int(matrix.loc[vol, "c_geothermal_nonvolc"])
    d = int(matrix.loc[vol, "d_artifact"])
    md.append(f"### {vol}")
    md.append(f"{geo_readings.get(vol, '')}")
    md.append(f"**FPs residuales**: {total} (b={b}, c={c}, d={d})")
    if total > 0:
        dom = "b" if b == max(b,c,d) else ("c" if c == max(b,c,d) else "d")
        if dom == "b":
            md.append("**Lectura**: nuestros FPs caen en features volcánicas reales del complejo → MIROVA scope más estrecho que el nuestro acá.")
        elif dom == "c":
            md.append("**Lectura**: nuestros FPs son geotermal/lacustre no eruptivo → extender `exclude_zones` con flag.")
        else:
            md.append("**Lectura**: nuestros FPs son artefactos (cirrus / glaciar / singleton) → fix de pipeline.")
    md.append("")

md.append("## Recomendación de scope (decisión Nicolás)\n")

pct_real = (n_a+n_b+n_c)/total_classified*100 if total_classified else 0
pct_b = n_b/total_classified*100 if total_classified else 0
pct_d = n_d/total_classified*100 if total_classified else 0

md.append(f"Realidad física agregada (a+b+c) = {pct_real:.1f}%. Solo artefactos puros (d) = {pct_d:.1f}%.\n")
md.append("### Opciones de scope\n")
md.append("**A. Clon MIROVA estricto**: aceptar gap precisión 0.024 como inherente. Cualquier FP es ruido contra MIROVA. NO extender geometría ni exclude_zones. ")
md.append("Pro: literal, defendible ante reviewers. Con: deja afuera ~{}% señales volcánicas reales del complejo que MIROVA simplemente no publica por su scope NRT operacional.\n".format(int(pct_b)))
md.append("**B. Clon + volcánico extra (RECOMENDADO si b ≳ d)**: extender geometría per-vol (additional_centers, extended_radius) para capturar sub-complejos reales (Cerro Blanco NdC, Lazufre Lastarria, Pichi-Llaima, complejo PP). Mantener exclude_zones con flag para (c) Las Máquinas / Río Diguillín. ")
md.append("Pro: precisión sube sin perder TPs MIROVA, etiqueta honesta 'detectamos feature volcánica X que MIROVA no publica'. Con: divergencia controlada del clon literal — requiere documentar cada extensión.\n")
md.append("**C. Detección térmica amplia (Beyond MIROVA)**: redefinir objetivo como 'monitoreo térmico volcánico chileno' independiente de MIROVA. Geotermal real se reporta como categoría separada. ")
md.append("Pro: producto único para SERNAGEOMIN. Con: pierde la simplicidad del benchmark MIROVA, cambia el contrato del proyecto.\n")

md.append("### Veredicto\n")
if pct_b > pct_d:
    md.append(f"**Opción B**. Categoría (b) volcánico real = {pct_b:.1f}% > artefactos (d) = {pct_d:.1f}%. ")
    md.append("La mayoría del gap precisión es scope MIROVA más estrecho, no bugs nuestros. ")
    md.append("La cartografía S85 Fase C ya tiene las coordenadas listas para extender geometría.")
elif pct_d > pct_b * 2:
    md.append(f"**Opción A**. Artefactos (d) = {pct_d:.1f}% dominan claramente. Priorizar fix Path D cirrus (A23) y Tupungatito glaciar (A19) antes de extender scope.")
else:
    md.append(f"**Mixto A+B**. b={pct_b:.1f}% y d={pct_d:.1f}% son comparables. Hacer fix de artefactos primero (D9 Path D cirrus), reauditoría, y recién entonces decidir extensión geometría.")

(OUT / "E_fp_classification.md").write_text("\n".join(md), encoding="utf-8")
print(f"[OK] MD escrito: {OUT/'E_fp_classification.md'}")
