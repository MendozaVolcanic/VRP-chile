"""S85 Fase C — Audit naturaleza de R3 violators residuales.

Hipótesis (Nicolás S85): los R3 violators residuales post-Fase B' corresponden
mayormente a **cuerpos térmicos NO-volcánicos conocidos** (lagos, salares,
glaciares, fumarolas crónicas, lava fields antiguos). MIROVA suprime estos
clusters con criterios contextuales vent-anchored fuertes que no están
documentados en papers.

Audit:
1. Para cada R3 violator MODIS + VIIRS en profile `enabled` (post B'),
   extraer centroide del cluster (lat/lon ponderado por VRP de los pixels).
2. Cruzar contra `exclude_zones` documentadas en `volcanoes.yaml`.
3. Para los R3 que NO caen en zona documentada, agruparlos por proximidad
   espacial (clustering simple) → identificar zonas térmicas nuevas
   que conviene catalogar.
4. Reportar per-vol: % R3 en zona documentada vs zona nueva vs huérfanos.

Output: `docs/F_S81_C_R3_NATURE_AUDIT.md` + JSON detallado.

Uso:
    python experiments/_s85_f_s81_c/r3_nature_audit.py
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "experiments" / "_s85_f_s81_c"
DOCS_OUT = ROOT / "docs" / "F_S81_C_R3_NATURE_AUDIT.md"

# Profile post-adopción Fase B' (data ya en disco del A/B run 26557588067)
PROFILE_DIR = "mirova_equivalent_f_s81_b_prime_2nd_pass_gate_enabled"

WINDOW_START = datetime(2026, 4, 12)
WINDOW_END = datetime(2026, 5, 26, 23, 59)

TIER_A = [
    "PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue",
    "NevadosDeChillan", "Llaima", "Chaiten", "PlanchonPeteroa",
    "Lastarria", "Isluga", "Tupungatito",
]

# Cluster grouping radius para R3 sin zona documentada — pixels MODIS son
# ~1km × sec³(θ_z) elongation; usamos 3km para considerar varios R3 del mismo
# "sitio" como una unidad. Para VIIRS 375m bastaría con 1km pero unificamos.
GEOGRAPHIC_CLUSTER_RADIUS_KM = 3.0


def parse_dt(s: str) -> datetime | None:
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def sensor_short(s: str) -> str:
    s = (s or "").upper()
    if "MODIS" in s:
        return "MODIS"
    if "VIIRS" in s:
        return "VIIRS"
    return s


def load_volcanoes_config() -> dict[str, dict]:
    """Carga config per-vol con inner_radius_km + exclude_zones documentadas."""
    y = yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))
    out = {}
    for v in y["volcanoes"]:
        out[v["name"]] = {
            "lat": float(v["lat"]),
            "lon": float(v["lon"]),
            "mirova_center_lat": float(v.get("mirova_center_lat", v["lat"])),
            "mirova_center_lon": float(v.get("mirova_center_lon", v["lon"])),
            "inner_radius_km": float(v.get("inner_radius_km", 5)),
            "exclude_zones": v.get("exclude_zones") or [],
        }
    return out


def cluster_centroid(anomaly_pixels: list[dict]) -> tuple[float, float] | None:
    """Calcula centroide ponderado por VRP de los anomaly_pixels.

    Si no hay vrp_mw en pixels, usa promedio simple lat/lon.
    """
    if not anomaly_pixels:
        return None
    total_w = 0.0
    sum_lat = 0.0
    sum_lon = 0.0
    for p in anomaly_pixels:
        lat = p.get("lat")
        lon = p.get("lon")
        if lat is None or lon is None:
            continue
        w = float(p.get("vrp_mw") or p.get("radiance") or 1.0)
        if w <= 0:
            w = 1.0
        sum_lat += lat * w
        sum_lon += lon * w
        total_w += w
    if total_w == 0:
        return None
    return (sum_lat / total_w, sum_lon / total_w)


def classify_against_zones(lat: float, lon: float,
                            zones: list[dict]) -> str | None:
    """Devuelve nombre de zona si (lat,lon) cae dentro de alguna, else None."""
    for z in zones:
        zlat = float(z["lat"])
        zlon = float(z["lon"])
        zradius = float(z["radius_km"])
        if haversine_km(lat, lon, zlat, zlon) <= zradius:
            return z["name"]
    return None


def find_r3_violators_with_centroid(vol: str, vcfg: dict) -> list[dict]:
    """Carga R3 violators del profile enabled con centroide cluster."""
    p = ROOT / "data" / PROFILE_DIR / f"{vol}.json"
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    inner_r = vcfg["inner_radius_km"]
    zones = vcfg["exclude_zones"]
    out = []
    for r in data.get("records", []):
        dt = parse_dt(r.get("datetime_utc", ""))
        if dt is None or not (WINDOW_START <= dt <= WINDOW_END):
            continue
        if r.get("final_hotspot_source") != "eruption":
            continue
        pc = r.get("primary_cluster") or {}
        pc_dist = float(pc.get("centroid_dist_km") or 0)
        pc_vrp = float(pc.get("vrp_mw") or 0)
        if pc_vrp <= 0 or pc_dist <= inner_r:
            continue
        # R3 violator confirmed
        # Tomar anomaly_pixels del record para calcular centroide
        ap = r.get("anomaly_pixels") or []
        cen = cluster_centroid(ap)
        if cen is None:
            # Fallback: usar pc.centroid_lat/lon o final_hotspot_*
            cen_lat = pc.get("centroid_lat") or r.get("final_hotspot_lat")
            cen_lon = pc.get("centroid_lon") or r.get("final_hotspot_lon")
            if cen_lat is None or cen_lon is None:
                continue
            cen = (float(cen_lat), float(cen_lon))
        zone_match = classify_against_zones(cen[0], cen[1], zones)
        out.append({
            "vol": vol,
            "dt": dt.isoformat(),
            "sensor": sensor_short(r.get("sensor", "")),
            "centroid_lat": cen[0],
            "centroid_lon": cen[1],
            "pc_dist_km": pc_dist,
            "pc_vrp_mw": pc_vrp,
            "pc_n_pixels": int(pc.get("n_pixels") or 0),
            "inner_radius_km": inner_r,
            "n_anomalous_pixels": int(r.get("n_anomalous_pixels") or 0),
            "zone_match": zone_match,
        })
    return out


def discover_geographic_clusters(records: list[dict],
                                  vol_lat: float, vol_lon: float,
                                  radius_km: float = GEOGRAPHIC_CLUSTER_RADIUS_KM) -> list[dict]:
    """Agrupa R3 SIN zone_match por proximidad espacial.

    Algoritmo simple: para cada record sin zona, buscar otros records dentro
    de radius_km. Cluster = grupo conexo (single-pass union-find lite).
    """
    unmatched = [r for r in records if r["zone_match"] is None]
    n = len(unmatched)
    if n == 0:
        return []
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(n):
        for j in range(i+1, n):
            d = haversine_km(unmatched[i]["centroid_lat"], unmatched[i]["centroid_lon"],
                             unmatched[j]["centroid_lat"], unmatched[j]["centroid_lon"])
            if d <= radius_km:
                union(i, j)

    groups: dict[int, list[dict]] = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(unmatched[i])

    clusters = []
    for gid, members in groups.items():
        if len(members) < 2:
            continue  # huérfano, no es cluster
        # Centroide del cluster geográfico = promedio de centroides
        clat = sum(m["centroid_lat"] for m in members) / len(members)
        clon = sum(m["centroid_lon"] for m in members) / len(members)
        dist_to_vent = haversine_km(vol_lat, vol_lon, clat, clon)
        # Direction NSEW
        dlat = clat - vol_lat
        dlon = clon - vol_lon
        ns = "N" if dlat > 0 else "S"
        ew = "E" if dlon > 0 else "W"
        bearing = f"{ns}{ew}"
        clusters.append({
            "n_records": len(members),
            "centroid_lat": round(clat, 4),
            "centroid_lon": round(clon, 4),
            "dist_from_vent_km": round(dist_to_vent, 2),
            "bearing": bearing,
            "sensors": sorted(set(m["sensor"] for m in members)),
            "dt_range": [min(m["dt"] for m in members), max(m["dt"] for m in members)],
        })
    clusters.sort(key=lambda c: -c["n_records"])
    return clusters


def main() -> int:
    print("[Fase C] R3 nature audit")
    vols_cfg = load_volcanoes_config()

    all_records: list[dict] = []
    per_vol_summary = []
    geographic_discoveries: dict[str, list[dict]] = {}

    for vol in TIER_A:
        if vol not in vols_cfg:
            continue
        vcfg = vols_cfg[vol]
        recs = find_r3_violators_with_centroid(vol, vcfg)
        all_records.extend(recs)

        n_total = len(recs)
        n_zone = sum(1 for r in recs if r["zone_match"] is not None)
        n_unmatched = n_total - n_zone

        clusters = discover_geographic_clusters(recs, vcfg["lat"], vcfg["lon"])
        n_in_new_clusters = sum(c["n_records"] for c in clusters)
        n_orphans = n_unmatched - n_in_new_clusters

        per_vol_summary.append({
            "vol": vol,
            "n_r3_total": n_total,
            "n_in_documented_zone": n_zone,
            "n_in_new_cluster": n_in_new_clusters,
            "n_orphans": n_orphans,
            "documented_zones": [z["name"] for z in vcfg["exclude_zones"]],
            "inner_radius_km": vcfg["inner_radius_km"],
            "new_clusters": clusters,
        })
        geographic_discoveries[vol] = clusters

    # Salida JSON
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "r3_nature_detail.json").write_text(
        json.dumps({
            "profile": PROFILE_DIR,
            "window": [WINDOW_START.isoformat(), WINDOW_END.isoformat()],
            "n_total_r3": len(all_records),
            "per_vol": per_vol_summary,
            "all_records": all_records,
        }, indent=2, default=str),
        encoding="utf-8",
    )

    # Markdown
    n_total = len(all_records)
    n_zone_total = sum(s["n_in_documented_zone"] for s in per_vol_summary)
    n_new_total = sum(s["n_in_new_cluster"] for s in per_vol_summary)
    n_orph_total = sum(s["n_orphans"] for s in per_vol_summary)

    md = []
    md.append("# Audit Fase C — Naturaleza de R3 violators residuales (S85)\n")
    md.append(f"**Profile**: `{PROFILE_DIR}` (post-Fase B' adoptada)\n")
    md.append(f"**Ventana**: {WINDOW_START.date()} → {WINDOW_END.date()}\n")
    md.append(f"**Total R3**: {n_total} (MODIS + VIIRS)\n\n")

    md.append("## Hipótesis a verificar (Nicolás S85)\n\n")
    md.append("> MIROVA prioriza anomalías volcánicas claras (vent-anchored) y\n")
    md.append("> suprime cuerpos térmicos no-volcánicos (lagos, salares,\n")
    md.append("> glaciares, fumarolas crónicas) salvo casos extremos como\n")
    md.append("> incendios grandes.\n\n")

    md.append("Si la hipótesis es correcta, esperamos que la mayoría de los\n")
    md.append(f"{n_total} R3 caigan en (a) zonas térmicas documentadas en\n")
    md.append("`volcanoes.yaml exclude_zones` o (b) clusters geográficos\n")
    md.append("nuevos identificables como features físicas no-volcánicas.\n\n")

    md.append("## Distribución global\n\n")
    md.append(f"| Categoría | # R3 | % |\n|---|---:|---:|\n")
    pct = lambda x: f"{100*x/n_total:.1f}%" if n_total else "—"
    md.append(f"| En zona DOCUMENTADA (exclude_zones existente) | {n_zone_total} | {pct(n_zone_total)} |\n")
    md.append(f"| En cluster geográfico NUEVO (>1 R3 a <3km) | {n_new_total} | {pct(n_new_total)} |\n")
    md.append(f"| Huérfanos (R3 aislados) | {n_orph_total} | {pct(n_orph_total)} |\n")
    md.append(f"| **Total** | **{n_total}** | **100%** |\n\n")

    # Per-volcano
    md.append("## Por volcán\n\n")
    md.append("| Volcán | R3 total | En zona doc | En cluster nuevo | Huérfanos | inner_km |\n")
    md.append("|---|---:|---:|---:|---:|---:|\n")
    for s in per_vol_summary:
        md.append(
            f"| {s['vol']} | {s['n_r3_total']} | {s['n_in_documented_zone']} | "
            f"{s['n_in_new_cluster']} | {s['n_orphans']} | {s['inner_radius_km']} |\n"
        )
    md.append("\n")

    # Clusters geográficos nuevos detectados
    md.append("## Clusters geográficos nuevos detectados (candidatos exclude_zones)\n\n")
    md.append(f"Agrupados por proximidad ≤{GEOGRAPHIC_CLUSTER_RADIUS_KM} km. Solo se listan\n")
    md.append("clusters con ≥2 R3 (huérfanos quedan sin agrupar).\n\n")
    md.append("| Volcán | n_R3 | lat | lon | dist_vent | bearing | sensores | rango fechas |\n")
    md.append("|---|---:|---:|---:|---:|---|---|---|\n")
    n_clusters_total = 0
    for vol, clusters in geographic_discoveries.items():
        for c in clusters:
            n_clusters_total += 1
            md.append(
                f"| {vol} | {c['n_records']} | {c['centroid_lat']} | "
                f"{c['centroid_lon']} | {c['dist_from_vent_km']} | "
                f"{c['bearing']} | {','.join(c['sensors'])} | "
                f"{c['dt_range'][0][:10]} → {c['dt_range'][1][:10]} |\n"
            )
    md.append(f"\n**Total clusters nuevos**: {n_clusters_total}\n\n")

    # Veredict
    md.append("## Veredict hipótesis Nicolás S85\n\n")
    pct_identified = (n_zone_total + n_new_total) / n_total if n_total else 0
    md.append(f"- R3 identificados (zona doc + cluster nuevo): "
              f"**{n_zone_total + n_new_total}/{n_total} ({100*pct_identified:.1f}%)**\n")
    md.append(f"- R3 huérfanos (sin patrón geográfico): "
              f"**{n_orph_total}/{n_total} ({100*n_orph_total/n_total:.1f}%)**\n\n")
    if pct_identified >= 0.70:
        md.append("✅ **HIPÓTESIS CONFIRMADA** (≥70% R3 en zonas identificables).\n")
        md.append("Acción: implementar gate de supresión MIROVA-style usando "
                  "exclude_zones extendidas + vent-anchoring fuerte.\n")
    elif pct_identified >= 0.40:
        md.append("⚠️  **HIPÓTESIS PARCIALMENTE CONFIRMADA** (40-70% R3 identificables).\n")
        md.append("Acción: implementar gate parcial + investigar mecanismo "
                  "complementario para los huérfanos.\n")
    else:
        md.append("❌ **HIPÓTESIS REFUTADA EMPÍRICAMENTE** (<40% R3 identificables).\n")
        md.append("Acción: redirigir investigación a otro mecanismo (geometría "
                  "cluster, single-pixel pixel mode edge cases, etc).\n")
    md.append("\n## Próximos pasos sugeridos\n\n")
    md.append("1. Para cada cluster nuevo identificado, identificar feature física\n")
    md.append("   (Google Maps / Sentinel-2 imagery / GVP catálogo del volcán).\n")
    md.append("2. Agregar exclude_zones documentadas a `volcanoes.yaml`.\n")
    md.append("3. A/B test gate `enable_r3_zone_suppression` (nuevo flag).\n")
    md.append("4. Si confirma reducción R3 ≥70% sin pérdida TPs → adoptar S86.\n")
    md.append("\n## Refs\n\n")
    md.append("- Adopción B': `docs/F_S81_B_PRIME_ADOPTION_S85.md`\n")
    md.append("- Beyond MIROVA roadmap: `docs/BEYOND_MIROVA_EXTENSIONS.md`\n")
    md.append("- Detalle JSON: `experiments/_s85_f_s81_c/r3_nature_detail.json`\n")

    DOCS_OUT.parent.mkdir(parents=True, exist_ok=True)
    DOCS_OUT.write_text("".join(md), encoding="utf-8")
    print(f"[Fase C] N total R3 = {n_total}")
    print(f"[Fase C] En zona doc: {n_zone_total} ({100*n_zone_total/n_total:.1f}%)")
    print(f"[Fase C] En cluster nuevo: {n_new_total} ({100*n_new_total/n_total:.1f}%)")
    print(f"[Fase C] Huérfanos: {n_orph_total} ({100*n_orph_total/n_total:.1f}%)")
    print(f"[Fase C] -> {DOCS_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
