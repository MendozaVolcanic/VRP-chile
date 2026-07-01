"""S118 C2 A/B — análisis de robo de cluster espacial (criterio pre-registrado A66).

POR QUÉ (fenómeno → criterio): MIROVA no cerca por geografía; nuestras cercas
intra-radio son parches (A55). El A/B pregunta: ¿apagar la cerca deja que un cluster
LEJANO le robe el primario al cráter en un volcán FOCAL, en una noche MIROVA-confirmada?
Si NO hay robo → gate OFF (clon-literal). Si hay robo → gate ON uniforme (excepción).
El eje que decide es ESPACIAL (A83), re-anclado al cráter (A61), NO el % de magnitud.

Entrada: artifacts descargados del reproc (gh run download). Cada job sube
s118c2ab-<arm>-<vol>-<start>/<vol>.json con SOLO los records de su chunk → este script
FUSIONA los chunks por (brazo, volcán) (dedup por datetime_utc+sensor).

Uso:
    gh run download <RUN_ID> -D experiments/_s118_c2ab/_artifacts
    python experiments/_s118_c2ab/analyze.py experiments/_s118_c2ab/_artifacts

Salida: experiments/_s118_c2ab/results.json + docs/AUDIT_S118_C2_GATES_AB.md
(números escritos por el script — fuente de verdad única, S91).
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
import yaml  # noqa: E402
from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402

ARMS = ["_c2ab_baseline", "_c2ab_pathd_off", "_c2ab_2pass_off", "_c2ab_both_off"]
GATE_OFF_ARMS = ["_c2ab_pathd_off", "_c2ab_2pass_off", "_c2ab_both_off"]
FOCAL = ["Lascar", "Lastarria", "Isluga", "PlanchonPeteroa", "PuyehueCordonCaulle"]
NEVADO = ["Llaima", "Copahue", "Villarrica", "NevadosDeChillan", "Tupungatito", "Chaiten"]
TIER_A = FOCAL + NEVADO

CONS = REPO / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
OCR = REPO / "data" / "mirova_reference" / "registro_vrp_ocr.csv"


def haversine_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return None
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def load_vol_geo():
    """Por volcán: GVP nominal (lat/lon, ancla MIROVA A13), vent físico, inner_radius_km."""
    raw = yaml.safe_load(open(REPO / "volcanoes.yaml", encoding="utf-8"))
    vols = raw.get("volcanoes", raw) if isinstance(raw, dict) else raw
    geo = {}
    for v in vols:
        geo[v["name"]] = {
            "gvp": (v.get("lat"), v.get("lon")),
            "vent": (v.get("vent_lat", v.get("lat")), v.get("vent_lon", v.get("lon"))),
            "inner_radius_km": v.get("inner_radius_km"),
        }
    return geo


def _date(dt_utc):
    return str(dt_utc)[:10] if dt_utc else None


def merge_arm_records(art_root: Path, arm: str, vol: str):
    """Fusiona los chunks de (arm, vol). Dedup por (datetime_utc, sensor)."""
    by_key = {}
    for d in sorted(art_root.glob(f"s118c2ab-{arm}-{vol}-*")):
        jf = d / f"{vol}.json"
        if not jf.exists():
            continue
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for r in data.get("records", []):
            by_key[(r.get("datetime_utc"), r.get("sensor"))] = r
    return list(by_key.values())


def mirova_nights():
    """{(volcano, date): [recs]} de MIROVA (CONS∪OCR), universo de noches confirmadas."""
    out = defaultdict(list)
    for vol in TIER_A:
        for r in load_mirova_alertas(cons_path=CONS, ocr_path=OCR, volcano=vol):
            d = _date(r.get("fecha_utc"))
            if d:
                out[(vol, d)].append(r)
    return out


def pc_crater_dist(rec, geo_v):
    """Distancia del primary_cluster.centroid al CRÁTER FÍSICO (vent), re-anclado (A61).

    NO usamos pc.centroid_dist_km crudo (mide desde el ancla de detección, que puede
    driftar A3/A63). Re-anclamos al vent físico — el punto que importa para "¿el cráter
    sigue siendo el primario?".
    """
    pc = rec.get("primary_cluster") or {}
    clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
    vlat, vlon = geo_v["vent"]
    return haversine_km(clat, clon, vlat, vlon), pc.get("vrp_mw"), pc.get("n_pixels")


def index_by_night(recs):
    """{date: record} priorizando el record con primary_cluster válido (mayor n_pixels)."""
    by = {}
    for r in recs:
        d = _date(r.get("datetime_utc"))
        if not d:
            continue
        pc = r.get("primary_cluster") or {}
        prev = by.get(d)
        if prev is None or (pc.get("n_pixels") or 0) > ((prev.get("primary_cluster") or {}).get("n_pixels") or 0):
            by[d] = r
    return by


def analyze(art_root: Path):
    geo = load_vol_geo()
    mir = mirova_nights()
    mir_dates = defaultdict(set)
    for (vol, d) in mir:
        mir_dates[vol].add(d)

    # Cargar records fusionados por (arm, vol) e indexar por noche.
    arm_vol_night = {}  # (arm, vol) -> {date: rec}
    coverage = {}       # (arm, vol) -> n_records
    for arm in ARMS:
        for vol in TIER_A:
            recs = merge_arm_records(art_root, arm, vol)
            arm_vol_night[(arm, vol)] = index_by_night(recs)
            coverage[(arm, vol)] = len(recs)

    # --- Criterio primario: robo de cluster en focales, noches MIROVA-confirmadas ---
    steal = {gate: defaultdict(lambda: {"n_nights": 0, "n_steal": 0, "detail": []})
             for gate in GATE_OFF_ARMS}
    for vol in TIER_A:
        inner = geo[vol]["inner_radius_km"]
        base_by = arm_vol_night.get(("_c2ab_baseline", vol), {})
        for d in sorted(mir_dates.get(vol, [])):
            base_rec = base_by.get(d)
            if base_rec is None:
                continue  # baseline no tiene esa noche (sin pasada/sin detección)
            b_dist, _bvrp, _bn = pc_crater_dist(base_rec, geo[vol])
            base_in = (b_dist is not None and inner is not None and b_dist <= inner)
            for gate in GATE_OFF_ARMS:
                rec = arm_vol_night.get((gate, vol), {}).get(d)
                s = steal[gate][vol]
                s["n_nights"] += 1
                if rec is None:
                    continue
                g_dist, gvrp, _gn = pc_crater_dist(rec, geo[vol])
                gate_in = (g_dist is not None and inner is not None and g_dist <= inner)
                # ROBO = baseline tenía el cráter dentro y el gate-OFF lo saca fuera
                if base_in and not gate_in:
                    s["n_steal"] += 1
                    s["detail"].append({
                        "date": d, "base_dist_km": round(b_dist, 2),
                        "gate_dist_km": round(g_dist, 2) if g_dist else None,
                        "inner_km": inner, "gate_vrp_mw": gvrp})

    # --- Secundaria: magnitud (ratio per-record arm/baseline) + cola inflada >1.5× ---
    # Mediana del ratio + cola: cuántos records inflan, cuántos son far (el frontend ya
    # los filtra) y cuántos MIROVA-confirmados. Es el "precio" de apagar la cerca.
    magnitude = {}
    for gate in GATE_OFF_ARMS:
        magnitude[gate] = {}
        for vol in TIER_A:
            b_all = {}
            for d in sorted(art_root.glob(f"s118c2ab-_c2ab_baseline-{vol}-*")):
                jf = d / f"{vol}.json"
                if jf.exists():
                    for r in json.loads(jf.read_text(encoding="utf-8")).get("records", []):
                        b_all[(r.get("datetime_utc"), r.get("sensor"))] = r
            a_all = {}
            for d in sorted(art_root.glob(f"s118c2ab-{gate}-{vol}-*")):
                jf = d / f"{vol}.json"
                if jf.exists():
                    for r in json.loads(jf.read_text(encoding="utf-8")).get("records", []):
                        a_all[(r.get("datetime_utc"), r.get("sensor"))] = r
            ratios, inflated = [], []
            for k, br in b_all.items():
                ar = a_all.get(k)
                if ar is None:
                    continue
                bv = (br.get("primary_cluster") or {}).get("vrp_mw") or 0
                av = (ar.get("primary_cluster") or {}).get("vrp_mw") or 0
                if bv > 0 and av > 0:
                    ratios.append(av / bv)
                    if av / bv > 1.5:
                        day = str(k[0])[:10]
                        inflated.append({
                            "date": day, "sensor": k[1], "base_mw": round(bv, 3),
                            "arm_mw": round(av, 3),
                            "distance_class": ar.get("distance_class"),
                            "mirova_confirmed": day in mir_dates.get(vol, set())})
            ratios.sort()
            magnitude[gate][vol] = {
                "n_pairs": len(ratios),
                "ratio_median": round(ratios[len(ratios) // 2], 3) if ratios else None,
                "n_inflated_gt1p5": len(inflated),
                "n_inflated_far": sum(1 for x in inflated if x["distance_class"] != "summit"),
                "n_inflated_mirova_conf": sum(1 for x in inflated if x["mirova_confirmed"]),
                "inflated": inflated,
            }

    results = {
        "coverage": {f"{a}|{v}": coverage[(a, v)] for (a, v) in coverage},
        "steal": {gate: {v: {"n_nights": steal[gate][v]["n_nights"],
                             "n_steal": steal[gate][v]["n_steal"],
                             "detail": steal[gate][v]["detail"]}
                         for v in TIER_A if steal[gate][v]["n_nights"]}
                  for gate in GATE_OFF_ARMS},
        "magnitude": magnitude,
        "config": {"FOCAL": FOCAL, "NEVADO": NEVADO},
    }
    return results, geo


def render_md(results):
    L = ["# AUDIT_S118 — A/B gates intra-radio C2: robo de cluster espacial",
         "",
         "Criterio pre-registrado (A66): gate→OFF si NO hay robo de cluster en focales en",
         "noches MIROVA-confirmadas; gate→ON uniforme si lo hay. Re-anclado al vent (A61).",
         "Generado por experiments/_s118_c2ab/analyze.py (S91: números del script).", ""]
    for gate in GATE_OFF_ARMS:
        L.append(f"## {gate}")
        L.append("")
        L.append("| Volcán | régimen | noches MIROVA | robos de cluster | veredicto local |")
        L.append("|---|---|---|---|---|")
        gd = results["steal"].get(gate, {})
        for vol in TIER_A:
            if vol not in gd:
                continue
            reg = "focal" if vol in FOCAL else "nevado"
            n = gd[vol]["n_nights"]
            st = gd[vol]["n_steal"]
            verd = "—" if reg == "nevado" else ("ROBO" if st else "ok")
            L.append(f"| {vol} | {reg} | {n} | {st} | {verd} |")
        L.append("")
        focal_steal = sum(gd.get(v, {}).get("n_steal", 0) for v in FOCAL)
        verdict = ("ON uniforme (excepción documentada)" if focal_steal
                   else "OFF (clon-literal — sin robo en focales)")
        L.append(f"**Veredicto {gate}: {verdict}** "
                 f"(robos en focales = {focal_steal}).")
        L.append("")
        # Secundaria: magnitud
        mg = results.get("magnitude", {}).get(gate, {})
        tot_pairs = sum((mg.get(v) or {}).get("n_pairs", 0) for v in TIER_A)
        tot_inf = sum((mg.get(v) or {}).get("n_inflated_gt1p5", 0) for v in TIER_A)
        tot_far = sum((mg.get(v) or {}).get("n_inflated_far", 0) for v in TIER_A)
        tot_mir = sum((mg.get(v) or {}).get("n_inflated_mirova_conf", 0) for v in TIER_A)
        meds = sorted(m["ratio_median"] for m in mg.values() if m and m.get("ratio_median"))
        L.append(f"*Magnitud (secundaria):* ratio mediano per-vol = "
                 f"{meds[len(meds)//2] if meds else '—'} · cola inflada >1.5× = "
                 f"**{tot_inf}/{tot_pairs}** records ({100*tot_inf/max(1,tot_pairs):.1f}%), "
                 f"de esos {tot_far} son `far` (el frontend ya los filtra) y {tot_mir} "
                 f"MIROVA-confirmados. Peores casos summit en `results.json > magnitude`.")
        L.append("")
    # Casos summit inflados (los únicos visibles en dashboard) del brazo both_off
    L.append("## Cola inflada visible (summit) — brazo both_off")
    L.append("")
    L.append("| Volcán | fecha | sensor | base MW | off MW | MIROVA conf |")
    L.append("|---|---|---|---|---|---|")
    for vol in TIER_A:
        m = results.get("magnitude", {}).get("_c2ab_both_off", {}).get(vol) or {}
        for x in m.get("inflated", []):
            if x["distance_class"] == "summit":
                L.append(f"| {vol} | {x['date']} | {x['sensor']} | {x['base_mw']} | "
                         f"{x['arm_mw']} | {'sí' if x['mirova_confirmed'] else 'no'} |")
    L.append("")
    return "\n".join(L)


def main():
    # Encoding Windows (CLAUDE.md): stdout cp1252 rompe con →/σ del render.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    art_root = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "experiments" / "_s118_c2ab" / "_artifacts"
    if not art_root.exists():
        print(f"No existe {art_root}. Primero: gh run download <RUN_ID> -D {art_root}")
        sys.exit(1)
    results, _geo = analyze(art_root)
    out_json = REPO / "experiments" / "_s118_c2ab" / "results.json"
    out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    md = render_md(results)
    out_md = REPO / "docs" / "AUDIT_S118_C2_GATES_AB.md"
    out_md.write_text(md, encoding="utf-8")
    print(f"results.json -> {out_json}")
    print(f"AUDIT_S118_C2_GATES_AB.md -> {out_md}")
    print()
    print(md)


if __name__ == "__main__":
    main()
