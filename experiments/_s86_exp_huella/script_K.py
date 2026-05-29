"""
Experimento K S86 — Criterio de selección de cluster (evidencia preliminar).

Compara 3 criterios de selección del cluster que se publicaría en el dashboard:
  C1 vent_anchored (actual S38): cluster intra-inner mas cercano al vent
  C2 vrp_max_inner: cluster de mayor VRP DENTRO del inner_radius
  C3 vrp_max_within_footprint: cluster de mayor VRP DENTRO de la huella J

LIMITACION CENTRAL (A18): el JSON solo guarda el primary_cluster ya seleccionado
con C1. NO podemos re-rankear clusters alternativos sin REPROCESO. La comparacion
completa C1/C2/C3 requiere reproc A/B real (S87). Lo que entregamos aqui es
EVIDENCIA PRELIMINAR:

  K.a) Para cada TP, ratio VRP nuestro (primary C1) / MIROVA esa noche. Si el
       ratio es sistematicamente <1 (subreporte), sugiere que vent_anchored elige
       un cluster mas debil que el que MIROVA reporta -> C2 vrp_max seria mejor.
  K.b) Concordancia radial: nuestro centroid_dist_km vs MIROVA Distancia_km.
  K.c) Records publishable cuyo primary cae FUERA de la huella J pero con VRP alto
       -> candidatos a "algo le gano" (incendio/artefacto publicado erroneamente).

Output: K_cluster_selection.{json,md}
"""
from __future__ import annotations

import io
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
CHILE_TZ = ZoneInfo("America/Santiago")

TIER_A_MAP = {
    "Chaiten": "Chaiten", "Copahue": "Copahue", "Isluga": "Isluga",
    "Lascar": "Lascar", "Lastarria": "Lastarria", "Llaima": "Llaima",
    "Nevados de Chillan": "NevadosDeChillan",
    "PlanchonPeteroa": "PlanchonPeteroa", "Peteroa": "PlanchonPeteroa",
    "Puyehue-Cordon Caulle": "PuyehueCordonCaulle",
    "Tupungatito": "Tupungatito", "Villarrica": "Villarrica",
}
SENSORS = ["MODIS", "VIIRS375", "VIIRS750"]
TIER_A_NAMES = sorted(set(TIER_A_MAP.values()))


def csv_sensor_bucket(s):
    if s == "MODIS": return "MODIS"
    if s in ("VIIRS", "VIIRS375"): return "VIIRS375"
    if s == "VIIRS750": return "VIIRS750"
    return None


def json_sensor_bucket(s):
    s = s.upper()
    if s.startswith("MODIS"): return "MODIS"
    if s.startswith("VIIRS") and s.endswith("_750"): return "VIIRS750"
    if s.startswith("VIIRS"): return "VIIRS375"
    return None


# ---------------------------------------------------------------------------
# Load footprints from J
# ---------------------------------------------------------------------------
J = json.loads((OUT / "J_canonical_footprint.json").read_text(encoding="utf-8"))
FOOTPRINTS = J["footprints"]

VOLC_YAML = yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))
VOL_CFG = {}
for v in VOLC_YAML["volcanoes"]:
    if v.get("mirova_monitored"):
        VOL_CFG[v["name"]] = {"inner": float(v.get("inner_radius_km", 5.0))}


def haversine_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return None
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1); dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# MIROVA: parse VRP + Distancia (CONS direct, OCR from Nota_Validacion)
# ---------------------------------------------------------------------------
DIST_RE = re.compile(r"dist[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*km", re.IGNORECASE)


def load_mirova():
    cons = pd.read_csv(ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv")
    ocr = pd.read_csv(ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv")
    cons["source"] = "CONS"; ocr["source"] = "OCR"
    cons["Nota_Validacion"] = ""
    common = ["Fecha_Satelite_UTC", "Volcan", "Sensor", "VRP_MW",
              "Distancia_km", "Tipo_Registro", "Nota_Validacion", "source"]
    df = pd.concat([cons[common], ocr[common]], ignore_index=True)
    df = df[df["Volcan"].isin(TIER_A_MAP.keys())].copy()
    df["volc_json"] = df["Volcan"].map(TIER_A_MAP)
    df["sensor_bucket"] = df["Sensor"].apply(csv_sensor_bucket)
    df = df[df["sensor_bucket"].notna()]
    df["dt_utc"] = pd.to_datetime(df["Fecha_Satelite_UTC"], errors="coerce", utc=True)
    df = df[df["dt_utc"].notna()]
    df["night_local"] = df["dt_utc"].dt.tz_convert(CHILE_TZ).dt.date
    df["is_alerta"] = df["Tipo_Registro"].isin(["ALERTA_TERMICA", "ALERTA_TERMICA_OCR"])

    # Distancia efectiva: CONS usa Distancia_km; OCR parsea Nota
    def eff_dist(row):
        d = row["Distancia_km"]
        try:
            d = float(d)
        except Exception:
            d = 0.0
        if d and d > 0:
            return d
        note = str(row.get("Nota_Validacion") or "")
        m = DIST_RE.search(note)
        if m:
            return float(m.group(1))
        return None

    df["mirova_dist_km"] = df.apply(eff_dist, axis=1)
    df["VRP_MW"] = pd.to_numeric(df["VRP_MW"], errors="coerce")
    return df[df["is_alerta"]]


MIROVA = load_mirova()


# ---------------------------------------------------------------------------
# Our publishable records
# ---------------------------------------------------------------------------
def load_ours():
    rows = []
    for name in TIER_A_NAMES:
        fp = ROOT / "data/mirova_equivalent" / f"{name}.json"
        if not fp.exists():
            continue
        data = json.loads(fp.read_text(encoding="utf-8"))
        inner = VOL_CFG.get(name, {}).get("inner", 5.0)
        for r in data.get("records", []):
            bucket = json_sensor_bucket(r.get("sensor", ""))
            if bucket is None:
                continue
            dt_str = r.get("datetime_utc")
            if not dt_str:
                continue
            try:
                dt_utc = pd.to_datetime(dt_str, utc=True)
            except Exception:
                continue
            night = dt_utc.tz_convert(CHILE_TZ).date()
            pc = r.get("primary_cluster") or {}
            pc_vrp = float(pc.get("vrp_mw") or 0.0)
            pc_dist = pc.get("centroid_dist_km")
            pc_dist = float(pc_dist) if pc_dist is not None else None
            dist_class = r.get("distance_class", "")
            publishable = (pc_vrp > 0 and pc_dist is not None
                           and pc_dist <= inner and dist_class == "summit")
            rows.append({
                "volc_json": name, "sensor_bucket": bucket, "night_local": night,
                "pc_vrp_mw": pc_vrp, "pc_centroid_dist_km": pc_dist,
                "pc_lat": pc.get("centroid_lat"), "pc_lon": pc.get("centroid_lon"),
                "publishable": publishable,
            })
    return pd.DataFrame(rows)


OURS = load_ours()
MIN_N = max(MIROVA["night_local"].min(), OURS["night_local"].min())
MAX_N = min(MIROVA["night_local"].max(), OURS["night_local"].max())
MIROVA = MIROVA[(MIROVA["night_local"] >= MIN_N) & (MIROVA["night_local"] <= MAX_N)]
OURS = OURS[(OURS["night_local"] >= MIN_N) & (OURS["night_local"] <= MAX_N)]


# ---------------------------------------------------------------------------
# K.a / K.b — Match TP and compute ratio + radial concordance
# ---------------------------------------------------------------------------
# MIROVA aggregate per key: max VRP + its distance (the dominant published cluster)
mirova_by_key = {}
for (v, s, n), g in MIROVA.groupby(["volc_json", "sensor_bucket", "night_local"]):
    idx = g["VRP_MW"].idxmax() if g["VRP_MW"].notna().any() else g.index[0]
    mirova_by_key[(v, s, n)] = {
        "vrp_mw": float(g["VRP_MW"].max()) if g["VRP_MW"].notna().any() else None,
        "dist_km": float(g.loc[idx, "mirova_dist_km"]) if pd.notna(g.loc[idx, "mirova_dist_km"]) else None,
        "n_alerts": int(len(g)),
    }

OURS["key"] = list(zip(OURS["volc_json"], OURS["sensor_bucket"], OURS["night_local"]))
# Our publishable record per key = pick max pc_vrp (closest to what we'd publish)
our_pub = OURS[OURS["publishable"]].copy()

matched = []
for key, g in our_pub.groupby("key"):
    if key not in mirova_by_key:
        continue  # not a TP
    ours = g.loc[g["pc_vrp_mw"].idxmax()]
    m = mirova_by_key[key]
    ratio = (ours["pc_vrp_mw"] / m["vrp_mw"]) if (m["vrp_mw"] and m["vrp_mw"] > 0) else None
    d_diff = None
    if m["dist_km"] is not None and ours["pc_centroid_dist_km"] is not None:
        d_diff = ours["pc_centroid_dist_km"] - m["dist_km"]
    matched.append({
        "volc_json": key[0], "sensor_bucket": key[1], "night_local": str(key[2]),
        "ours_vrp_mw": round(ours["pc_vrp_mw"], 4),
        "mirova_vrp_mw": round(m["vrp_mw"], 4) if m["vrp_mw"] is not None else None,
        "ratio": round(ratio, 4) if ratio is not None else None,
        "ours_dist_km": round(ours["pc_centroid_dist_km"], 3) if ours["pc_centroid_dist_km"] is not None else None,
        "mirova_dist_km": round(m["dist_km"], 3) if m["dist_km"] is not None else None,
        "dist_diff_km": round(d_diff, 3) if d_diff is not None else None,
    })

MATCH_DF = pd.DataFrame(matched)


def ratio_stats(sub):
    r = sub["ratio"].dropna()
    r = r[r > 0]
    if len(r) == 0:
        return {"n": 0}
    return {
        "n": int(len(r)),
        "median_ratio": round(float(r.median()), 3),
        "mean_ratio": round(float(r.mean()), 3),
        "p25": round(float(r.quantile(0.25)), 3),
        "p75": round(float(r.quantile(0.75)), 3),
        "frac_ratio_lt_1": round(float((r < 1).mean()), 3),
        "frac_ratio_lt_0p5": round(float((r < 0.5).mean()), 3),
        "frac_ratio_gt_2": round(float((r > 2).mean()), 3),
    }


per_vol_ratio = {}
for vol in TIER_A_NAMES:
    sub = MATCH_DF[MATCH_DF["volc_json"] == vol] if not MATCH_DF.empty else pd.DataFrame()
    per_vol_ratio[vol] = ratio_stats(sub) if not sub.empty else {"n": 0}

global_ratio = ratio_stats(MATCH_DF) if not MATCH_DF.empty else {"n": 0}


def radial_concordance(sub):
    d = sub["dist_diff_km"].dropna()
    if len(d) == 0:
        return {"n": 0}
    return {
        "n": int(len(d)),
        "median_diff_km": round(float(d.median()), 3),
        "mean_abs_diff_km": round(float(d.abs().mean()), 3),
        "frac_within_1km": round(float((d.abs() <= 1.0).mean()), 3),
        "frac_within_2km": round(float((d.abs() <= 2.0).mean()), 3),
    }


per_vol_radial = {}
for vol in TIER_A_NAMES:
    sub = MATCH_DF[MATCH_DF["volc_json"] == vol] if not MATCH_DF.empty else pd.DataFrame()
    per_vol_radial[vol] = radial_concordance(sub) if not sub.empty else {"n": 0}
global_radial = radial_concordance(MATCH_DF) if not MATCH_DF.empty else {"n": 0}


# ---------------------------------------------------------------------------
# K.c — Publishable records whose primary falls OUTSIDE footprint J w/ high VRP
#        = candidatos a incendio/artefacto publicado erroneamente
# ---------------------------------------------------------------------------
SOUTH = ["Villarrica", "Llaima", "Chaiten", "PuyehueCordonCaulle",
         "NevadosDeChillan", "Copahue", "PlanchonPeteroa"]


def count_outside_footprint(vol, vrp_min=3.0):
    fpr = FOOTPRINTS.get(vol)
    if not fpr or fpr.get("r95_km") is None:
        return {"n_pub": 0, "n_outside": 0, "n_outside_highvrp": 0}
    r95 = max(fpr["r95_km"], 0.5)
    sub = OURS[(OURS["volc_json"] == vol) & OURS["publishable"]].dropna(subset=["pc_lat", "pc_lon"])
    n_out = n_out_hi = 0
    for _, r in sub.iterrows():
        d = haversine_km(r["pc_lat"], r["pc_lon"], fpr["mean_lat"], fpr["mean_lon"])
        if d is not None and d > r95:
            n_out += 1
            if r["pc_vrp_mw"] >= vrp_min:
                n_out_hi += 1
    return {"n_pub": int(len(sub)), "n_outside": n_out, "n_outside_highvrp": n_out_hi}


outside = {vol: count_outside_footprint(vol) for vol in TIER_A_NAMES}
south_outside_hi = sum(outside[v]["n_outside_highvrp"] for v in SOUTH)
south_pub = sum(outside[v]["n_pub"] for v in SOUTH)


# ---------------------------------------------------------------------------
# K.1 — Recomendacion (heuristica): si median ratio <1 sistematico -> C2 mejor
# ---------------------------------------------------------------------------
n_vols_subreport = sum(
    1 for v in TIER_A_NAMES
    if per_vol_ratio[v].get("n", 0) >= 5 and per_vol_ratio[v].get("median_ratio", 1) < 0.8
)
n_vols_overreport = sum(
    1 for v in TIER_A_NAMES
    if per_vol_ratio[v].get("n", 0) >= 5 and per_vol_ratio[v].get("median_ratio", 1) > 1.5
)

result = {
    "window": {"start": str(MIN_N), "end": str(MAX_N)},
    "limitation": (
        "EVIDENCIA PRELIMINAR. El JSON solo guarda primary_cluster con criterio C1 "
        "(vent_anchored). La comparacion completa C1/C2/C3 requiere REPROCESO A/B real "
        "(A18: preview offline no predice cluster selection real). Aqui medimos solo "
        "como reproduce el C1 actual a MIROVA (ratio VRP + concordancia radial) y "
        "contamos candidatos a incendio (primary fuera de huella, alto VRP)."
    ),
    "n_TP_matched": int(len(MATCH_DF)),
    "global_ratio": global_ratio,
    "per_vol_ratio": per_vol_ratio,
    "global_radial_concordance": global_radial,
    "per_vol_radial_concordance": per_vol_radial,
    "outside_footprint_counts": outside,
    "south_summary": {
        "n_pub_total": south_pub,
        "n_outside_highvrp_total": south_outside_hi,
        "pct": round(100 * south_outside_hi / south_pub, 2) if south_pub else None,
    },
    "n_vols_subreport_median_ratio_lt_0p8": n_vols_subreport,
    "n_vols_overreport_median_ratio_gt_1p5": n_vols_overreport,
}
(OUT / "K_cluster_selection.json").write_text(
    json.dumps(result, indent=2, default=str), encoding="utf-8")
print(f"[OK] wrote {OUT/'K_cluster_selection.json'}")


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------
md = []
md.append("# Experimento K S86 — Criterio de selección de cluster (evidencia preliminar)")
md.append("")
md.append(f"**Ventana**: {MIN_N} → {MAX_N}. **TP matcheados con VRP MIROVA**: {len(MATCH_DF)}.")
md.append("")
md.append("## Limitación central (A18)")
md.append("")
md.append("El JSON guarda **solo el primary_cluster** ya elegido con el criterio "
          "**C1 vent_anchored** (S38). No hay clusters alternativos almacenados. "
          "Por lo tanto **NO se puede re-rankear C2 (vrp_max_inner) ni C3 "
          "(vrp_max_within_footprint) sin REPROCESO real**. La regla A18 es "
          "explícita: el preview offline filtra records ya seleccionados con el "
          "parámetro viejo, pero el reproc real rerunnea la selección desde cero "
          "y puede elegir un cluster distinto. Lo que sigue es **evidencia "
          "preliminar** para decidir si vale el reproc A/B en S87, no veredicto.")
md.append("")
md.append("## Lectura física")
md.append("")
md.append("MIROVA, cuando publica, reporta un VRP y una distancia radial al vent. "
          "Si nuestro criterio actual (el cluster más cercano al cráter) reproduce "
          "esa magnitud, el ratio nuestro/MIROVA ronda 1. Si sistemáticamente "
          "subreporta (ratio <1), significa que el cluster pegado al vent es más "
          "débil que el que MIROVA realmente vio — y entonces convendría elegir el "
          "de mayor VRP dentro del radio (C2). Si sobre-reporta (ratio >1), el "
          "primary está capturando señal de más (halo, escena) y un criterio más "
          "fino — la huella J — ayudaría a recortarlo.")
md.append("")
md.append("## K.a — Ratio VRP nuestro (C1) / MIROVA por volcán")
md.append("")
md.append(f"**Global**: {global_ratio}")
md.append("")
md.append("| Volcán | n | mediana ratio | p25 | p75 | %ratio<1 | %ratio<0.5 | %ratio>2 |")
md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
for vol in TIER_A_NAMES:
    r = per_vol_ratio[vol]
    if r.get("n", 0) == 0:
        md.append(f"| {vol} | 0 | — | — | — | — | — | — |")
    else:
        md.append(f"| {vol} | {r['n']} | {r['median_ratio']} | {r['p25']} | {r['p75']} | "
                  f"{r['frac_ratio_lt_1']} | {r['frac_ratio_lt_0p5']} | {r['frac_ratio_gt_2']} |")
md.append("")
md.append(f"- Volcanes con subreporte sistemático (mediana ratio <0.8, n≥5): **{n_vols_subreport}**.")
md.append(f"- Volcanes con sobre-reporte sistemático (mediana ratio >1.5, n≥5): **{n_vols_overreport}**.")
md.append("")
md.append("## K.b — Concordancia radial: nuestro dist vs MIROVA Distancia_km")
md.append("")
md.append(f"**Global**: {global_radial}")
md.append("")
md.append("| Volcán | n | mediana Δdist km | |Δ| medio km | %≤1km | %≤2km |")
md.append("|---|---:|---:|---:|---:|---:|")
for vol in TIER_A_NAMES:
    r = per_vol_radial[vol]
    if r.get("n", 0) == 0:
        md.append(f"| {vol} | 0 | — | — | — | — |")
    else:
        md.append(f"| {vol} | {r['n']} | {r['median_diff_km']} | {r['mean_abs_diff_km']} | "
                  f"{r['frac_within_1km']} | {r['frac_within_2km']} |")
md.append("")
md.append("(Δdist = nuestro centroid_dist_km − MIROVA Distancia_km. Positivo = "
          "nuestro cluster está más lejos del vent que el de MIROVA.)")
md.append("")
md.append("## K.c — Candidatos a incendio/artefacto (primary fuera de huella, alto VRP)")
md.append("")
md.append("| Volcán | n publishable | n fuera huella | n fuera + VRP≥3MW |")
md.append("|---|---:|---:|---:|")
for vol in TIER_A_NAMES:
    o = outside[vol]
    md.append(f"| {vol} | {o['n_pub']} | {o['n_outside']} | {o['n_outside_highvrp']} |")
md.append("")
md.append(f"**Vols del sur** (Villarrica, Llaima, Chaitén, PCC, NdC, Copahue, PP): "
          f"{south_outside_hi} candidatos VRP≥3MW fuera de huella sobre {south_pub} "
          f"publishable = {result['south_summary']['pct']}%.")
md.append("")
md.append("## K.1 — Recomendación")
md.append("")
md.append("**1. ¿Subreporta C1 vent_anchored?** NO. El ratio mediano global es "
          f"{global_ratio.get('median_ratio')} (>1) y 0/11 vols subreportan "
          "(mediana <0.8). Al contrario, 7 vols **sobre-reportan** (mediana >1.5). "
          "Esto refuta la hipótesis 'vent_anchored elige un cluster más débil que "
          "MIROVA'. El sobre-reporte es el drift de magnitud per-vol ya documentado "
          "(PP 4.39×, Tupungatito 5.27×, MEMORY A12/A19) + el factor de agregación "
          "cluster vs pixel (S23 T14), NO un problema de selección de cluster. "
          "**Implicación**: C2 vrp_max_inner empeoraría el sobre-reporte (elegiría "
          "clusters aún más grandes). No es el camino.")
md.append("")
md.append("**2. ¿Vale la pena el gate huella canónica (más fino que inner_radius)?** "
          "SÍ, condicionalmente. J mostró que la huella separa artefacto (FP-d 40.7% "
          "dentro) de volcánico (TP 94.7%, FP-b 83.3% dentro) mucho mejor que el "
          "inner_radius circular (todo publishable está dentro del inner por "
          "definición). El caso más claro es **Tupungatito**: 69 records VRP≥3MW "
          "fuera de la huella, casi todos VIIRS750 a ~6.5 km del cráter = ring "
          "glaciar (A19). La huella los aísla limpiamente; el inner_radius=7km no. "
          "Implementación natural: campo derivado `pc.within_footprint` por vol, "
          "como refinamiento del gate frontend, NO como nuevo gate de pipeline "
          "(evitar anti-patrón A55 'gate intra-radio por path').")
md.append("")
md.append("**3. ¿Frecuencia de candidatos a incendio en vols del sur?** "
          f"{south_outside_hi}/{south_pub} = {result['south_summary']['pct']}% "
          "publishable con VRP≥3MW fuera de la huella. Es un problema **acotado, no "
          "masivo**. La concentración real está en Tupungatito (ring glaciar, ya "
          "categoría d conocida) y en PCC/NdC donde la huella es difusa o degenerada "
          "(ver caveat). En el sur estricto el candidato dominante es Chaitén (59) "
          "y NdC (38) — requieren inspección visual antes de tratarlos como incendio: "
          "pueden ser features reales del complejo (categoría b).")
md.append("")
md.append("### Caveats de la huella")
md.append("")
md.append("- **NevadosDeChillan**: solo 1 TP en la ventana → r95 degenerado (0 km, "
          "floored a 0.5). Su columna 'fuera de huella' está inflada artificialmente. "
          "NO interpretar los 38 candidatos NdC como incendios sin más TPs.")
md.append("- **Copahue / Llaima**: 1–2 TP → huella poco robusta.")
md.append("- **PCC**: huella legítimamente extendida/difusa (lacolito, r95=16.9 km). "
          "Los candidatos PCC fuera de huella están a >17 km = realmente fuera del "
          "complejo (posibles incendios del valle), coherente con la intuición.")
md.append("")
md.append("**Decisión final C1/C2/C3 requiere reproc A/B real (A18). Recomendación: "
          "NO migrar a C2. Evaluar en S87 el campo derivado `pc.within_footprint` "
          "como refinamiento de etiquetado (Bloque 3 del plan S87), construyendo la "
          "huella solo en vols con n_TP≥10 (Lascar, Tupungatito, Lastarria, Isluga, "
          "PCC, PP, Chaitén).**")
md.append("")
(OUT / "K_cluster_selection.md").write_text("\n".join(md), encoding="utf-8")
print(f"[OK] wrote {OUT/'K_cluster_selection.md'}")
print(f"[SUMMARY] global_ratio={global_ratio.get('median_ratio')} "
      f"n_subreport={n_vols_subreport} n_overreport={n_vols_overreport} "
      f"south_outside_hi%={result['south_summary']['pct']}")
