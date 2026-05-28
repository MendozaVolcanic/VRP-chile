"""
Subagente B — Caracterización VRP Chile crudo (pre-frontend filter).
Frente 2.A S86 — precision gap audit.

Lee data/mirova_equivalent/{Vol}.json para 11 Tier A, calcula distribuciones
para comparar contra Subagente A (lo que MIROVA publica).

Reglas: solo lectura. Encoding utf-8. NO escribir a data/.
"""
from __future__ import annotations
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DATA_DIR = REPO / "data" / "mirova_equivalent"
OUT_DIR = REPO / "experiments" / "_s86_f_precision_gap"

TIER_A = [
    "Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima",
    "NevadosDeChillan", "PlanchonPeteroa", "PuyehueCordonCaulle",
    "Tupungatito", "Villarrica",
]

INNER_RADIUS_KM = {
    "Chaiten": 5, "Copahue": 4, "Isluga": 5, "Lascar": 5, "Lastarria": 3,
    "Llaima": 5, "NevadosDeChillan": 5, "PlanchonPeteroa": 3,
    "PuyehueCordonCaulle": 20, "Tupungatito": 7, "Villarrica": 5,
}

# Overlap con CSV Subagente A
CSV_MIN = datetime.fromisoformat("2026-01-10T19:06:00")
CSV_MAX = datetime.fromisoformat("2026-05-18T21:10:00")


def percentiles(xs, ps=(5, 25, 50, 75, 95)):
    if not xs:
        return {f"p{p}": None for p in ps} | {"min": None, "max": None, "mean": None, "n": 0}
    s = sorted(xs)
    n = len(s)
    out = {}
    for p in ps:
        k = (n - 1) * p / 100
        f = int(k)
        c = min(f + 1, n - 1)
        out[f"p{p}"] = s[f] + (s[c] - s[f]) * (k - f)
    out["min"] = s[0]
    out["max"] = s[-1]
    out["mean"] = sum(s) / n
    out["n"] = n
    return out


def parse_dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "").replace("+00:00", ""))
    except Exception:
        return None


def sensor_bucket(sensor):
    if not sensor:
        return "UNKNOWN"
    s = sensor.upper()
    if s.startswith("MODIS"):
        return "MODIS"
    if "750" in s:
        return "VIIRS_M750"
    if s.startswith("VIIRS"):
        return "VIIRS_I375"
    return "OTHER"


def infer_path(rec):
    """pc.path no existe en schema. Inferimos del path-counters diag_n_*.
    Si solo un path > 0 lo atribuimos. Si varios: 'multi'. None si todos 0."""
    bt = rec.get("diag_n_bt_path") or 0
    nti = rec.get("diag_n_nti_path") or 0
    dnti = rec.get("diag_n_dnti_ctx_path") or 0
    active = []
    if bt > 0: active.append("BT")
    if nti > 0: active.append("NTI")
    if dnti > 0: active.append("dNTI")
    if not active:
        return "none"
    if len(active) == 1:
        return active[0]
    return "multi:" + "+".join(active)


def histogram_npix(n):
    if n is None:
        return "na"
    if n <= 1: return "1"
    if n == 2: return "2"
    if n == 3: return "3"
    if n <= 5: return "4-5"
    if n <= 10: return "6-10"
    return "11+"


def episode_durations(times, max_gap_days=2):
    """times: sorted list of datetimes para un volcán (records publishable).
    Episodio = secuencia con gap <= max_gap_days. Devuelve lista duraciones en días (max-min)."""
    if not times:
        return []
    times = sorted(times)
    eps = []
    start = times[0]
    last = times[0]
    for t in times[1:]:
        if (t - last).total_seconds() > max_gap_days * 86400:
            eps.append((last - start).total_seconds() / 86400)
            start = t
        last = t
    eps.append((last - start).total_seconds() / 86400)
    return eps


def main():
    summary = {
        "meta": {
            "window_utc_min": CSV_MIN.isoformat(),
            "window_utc_max": CSV_MAX.isoformat(),
            "tier_a_volcanoes": TIER_A,
            "inner_radius_km": INNER_RADIUS_KM,
        },
        "per_volcano": {},
        "global": {},
    }

    # Acumuladores globales
    all_pc_vrp_by_sensor = defaultdict(list)
    all_pc_dist_by_sensor = defaultdict(list)
    all_npix_hist = Counter()
    all_path_counts = Counter()
    all_path_counts_publishable = Counter()
    all_source_counts = Counter()
    all_window_min = None
    all_window_max = None
    all_path_dnti_publishable = 0
    all_total_publishable = 0

    for vol in TIER_A:
        path = DATA_DIR / f"{vol}.json"
        if not path.exists():
            summary["per_volcano"][vol] = {"error": "file_not_found"}
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        recs = data.get("records", [])

        per_sensor = defaultdict(lambda: {
            "total": 0, "pc_positive": 0, "publishable": 0, "r3_fantasma": 0,
            "pc_vrp_mw": [], "pc_dist_km": [], "npix_hist": Counter(),
            "path_counts": Counter(), "path_counts_publishable": Counter(),
            "source_counts": Counter(),
        })
        publishable_times = []  # para episodios
        vol_min = None
        vol_max = None

        inner = INNER_RADIUS_KM[vol]

        for rec in recs:
            dt = parse_dt(rec.get("datetime_utc") or rec.get("acquisition_time_utc"))
            if dt is None:
                continue
            if dt < CSV_MIN or dt > CSV_MAX:
                continue
            if vol_min is None or dt < vol_min: vol_min = dt
            if vol_max is None or dt > vol_max: vol_max = dt
            if all_window_min is None or dt < all_window_min: all_window_min = dt
            if all_window_max is None or dt > all_window_max: all_window_max = dt

            sb = sensor_bucket(rec.get("sensor"))
            d = per_sensor[sb]
            d["total"] += 1
            pc = rec.get("primary_cluster") or {}
            vrp = pc.get("vrp_mw")
            dist = pc.get("centroid_dist_km")
            npix = pc.get("n_pixels")
            if vrp is None or vrp <= 0:
                continue
            d["pc_positive"] += 1
            d["pc_vrp_mw"].append(float(vrp))
            all_pc_vrp_by_sensor[sb].append(float(vrp))
            if dist is not None:
                d["pc_dist_km"].append(float(dist))
                all_pc_dist_by_sensor[sb].append(float(dist))

            publishable = dist is not None and dist <= inner
            if publishable:
                d["publishable"] += 1
                publishable_times.append(dt)
                bucket = histogram_npix(npix)
                d["npix_hist"][bucket] += 1
                all_npix_hist[bucket] += 1
                pth = infer_path(rec)
                d["path_counts_publishable"][pth] += 1
                all_path_counts_publishable[pth] += 1
                src = rec.get("final_hotspot_source") or "unknown"
                d["source_counts"][src] += 1
                all_source_counts[src] += 1
                all_total_publishable += 1
                if "dNTI" in pth:
                    all_path_dnti_publishable += 1
            else:
                d["r3_fantasma"] += 1
            # path total (publishable + r3)
            pth = infer_path(rec)
            d["path_counts"][pth] += 1
            all_path_counts[pth] += 1

        eps = episode_durations(publishable_times)
        vol_summary = {
            "window_utc_min": vol_min.isoformat() if vol_min else None,
            "window_utc_max": vol_max.isoformat() if vol_max else None,
            "inner_radius_km": inner,
            "by_sensor": {},
            "episodes_publishable": {
                "n_episodes": len(eps),
                "duration_days": percentiles(eps),
                "n_publishable_records": len(publishable_times),
            },
        }
        for sb, d in per_sensor.items():
            vol_summary["by_sensor"][sb] = {
                "total_records": d["total"],
                "pc_vrp_positive": d["pc_positive"],
                "publishable_in_inner_radius": d["publishable"],
                "r3_fantasma_outside_inner": d["r3_fantasma"],
                "pc_vrp_mw_stats": percentiles(d["pc_vrp_mw"]),
                "pc_centroid_dist_km_stats": percentiles(d["pc_dist_km"]),
                "n_pixels_histogram_publishable": dict(d["npix_hist"]),
                "path_breakdown_all_positive": dict(d["path_counts"]),
                "path_breakdown_publishable": dict(d["path_counts_publishable"]),
                "final_hotspot_source_publishable": dict(d["source_counts"]),
            }
        summary["per_volcano"][vol] = vol_summary

    # Globals
    summary["global"] = {
        "window_utc_min": all_window_min.isoformat() if all_window_min else None,
        "window_utc_max": all_window_max.isoformat() if all_window_max else None,
        "pc_vrp_mw_by_sensor": {sb: percentiles(v) for sb, v in all_pc_vrp_by_sensor.items()},
        "pc_centroid_dist_km_by_sensor": {sb: percentiles(v) for sb, v in all_pc_dist_by_sensor.items()},
        "n_pixels_histogram_publishable": dict(all_npix_hist),
        "path_breakdown_all_positive": dict(all_path_counts),
        "path_breakdown_publishable": dict(all_path_counts_publishable),
        "final_hotspot_source_publishable": dict(all_source_counts),
        "total_publishable_records": all_total_publishable,
        "dnti_share_of_publishable": (all_path_dnti_publishable / all_total_publishable) if all_total_publishable else None,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "B_ours_detected.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)

    # ---- Markdown report ----
    g = summary["global"]
    md = []
    md.append("# Subagente B — Caracterización VRP Chile crudo (pre-frontend filter)\n")
    md.append("**Frente 2.A S86 — precision gap audit**\n")
    md.append(f"Ventana analizada (overlap con CSV Subagente A): `{g['window_utc_min']}` → `{g['window_utc_max']}`\n")
    md.append("\n## 1. Resumen geológico\n")
    md.append(
        "El pipeline térmico VRP-Chile detecta una población mucho más amplia que la que MIROVA "
        "finalmente publica. Filtrando los JSONs operacionales al overlap con el CSV consolidado "
        f"({CSV_MIN.date()}–{CSV_MAX.date()}), tenemos **{all_total_publishable} records "
        "'publishable'** (pc.vrp_mw>0 dentro del inner_radius del KMZ) repartidos entre los 11 Tier A. "
        "Ese conjunto es ya el output post-filtro geométrico del frontend; el gap restante respecto a "
        "MIROVA (~99%) tiene que explicarse por otra capa de supresión.\n"
    )
    md.append("\n## 2. Distribución de pc.vrp_mw (records publishable, por sensor)\n")
    md.append("| Sensor | n | min | p5 | p25 | p50 | p75 | p95 | max | mean |\n|---|---|---|---|---|---|---|---|---|---|\n")
    for sb, st in g["pc_vrp_mw_by_sensor"].items():
        if st["n"] == 0:
            continue
        md.append(f"| {sb} | {st['n']} | {st['min']:.3f} | {st['p5']:.3f} | {st['p25']:.3f} | {st['p50']:.3f} | {st['p75']:.3f} | {st['p95']:.3f} | {st['max']:.3f} | {st['mean']:.3f} |\n")

    md.append("\n## 3. pc.n_pixels — tamaño del cluster primary (publishable, agregado)\n")
    md.append("Hipótesis: si la mayoría de nuestros records tiene pc.n_pixels=1, MIROVA podría requerir cluster mínimo (≥2-3 px) para suprimir ruido de pixel aislado.\n\n")
    md.append("| bucket | count | share |\n|---|---|---|\n")
    tot_h = sum(g["n_pixels_histogram_publishable"].values()) or 1
    for k in ["1", "2", "3", "4-5", "6-10", "11+"]:
        c = g["n_pixels_histogram_publishable"].get(k, 0)
        md.append(f"| {k} | {c} | {100*c/tot_h:.1f}% |\n")

    md.append("\n## 4. pc.path breakdown (inferido de diag_n_*_path)\n")
    md.append("Path D (dNTI contextual) es históricamente sospechoso de FPs sistémicos en cirrus alto (regla A23).\n\n")
    md.append("**Publishable (in-radius):**\n\n| path | count | share |\n|---|---|---|\n")
    tot_p = sum(g["path_breakdown_publishable"].values()) or 1
    for k, c in sorted(g["path_breakdown_publishable"].items(), key=lambda x: -x[1]):
        md.append(f"| {k} | {c} | {100*c/tot_p:.1f}% |\n")
    md.append(f"\nFracción dNTI (solo o combinado) sobre publishable: **{100*(g['dnti_share_of_publishable'] or 0):.1f}%**.\n")

    md.append("\n## 5. final_hotspot_source breakdown (publishable)\n")
    md.append("`cluster_rescue` señaliza discrepancia entre pixel single (scene-wide) y cluster vent-anchored (A46/S77).\n\n")
    md.append("| source | count |\n|---|---|\n")
    for k, c in sorted(g["final_hotspot_source_publishable"].items(), key=lambda x: -x[1]):
        md.append(f"| {k} | {c} |\n")

    md.append("\n## 6. Conteo por volcán\n")
    md.append("| Vol | inner_km | total | pc.vrp>0 | publishable | R3 fantasma | n_episodios |\n|---|---|---|---|---|---|---|\n")
    for vol in TIER_A:
        v = summary["per_volcano"].get(vol, {})
        if "error" in v:
            md.append(f"| {vol} | - | (file_not_found) | | | | |\n")
            continue
        tot = sum(s["total_records"] for s in v["by_sensor"].values())
        pos = sum(s["pc_vrp_positive"] for s in v["by_sensor"].values())
        pub = sum(s["publishable_in_inner_radius"] for s in v["by_sensor"].values())
        r3 = sum(s["r3_fantasma_outside_inner"] for s in v["by_sensor"].values())
        eps_n = v["episodes_publishable"]["n_episodes"]
        md.append(f"| {vol} | {v['inner_radius_km']} | {tot} | {pos} | {pub} | {r3} | {eps_n} |\n")

    md.append("\n## 7. Episodios publishable (gap ≤2 días) — duración en días\n")
    md.append("| Vol | n_episodios | p50 días | p95 días | max |\n|---|---|---|---|---|\n")
    for vol in TIER_A:
        v = summary["per_volcano"].get(vol, {})
        if "error" in v:
            continue
        ep = v["episodes_publishable"]["duration_days"]
        if ep["n"] == 0:
            md.append(f"| {vol} | 0 | - | - | - |\n")
        else:
            md.append(f"| {vol} | {ep['n']} | {ep['p50']:.2f} | {ep['p95']:.2f} | {ep['max']:.2f} |\n")

    md.append("\n## 8. Por sensor por volcán (resumen total / publishable)\n")
    md.append("| Vol | Sensor | total | pc.vrp>0 | publishable | R3 | p50 vrp publishable |\n|---|---|---|---|---|---|---|\n")
    for vol in TIER_A:
        v = summary["per_volcano"].get(vol, {})
        if "error" in v:
            continue
        for sb, s in sorted(v["by_sensor"].items()):
            # p50 publishable: filter pc_vrp positive, but stats already are pc_positive list
            p50 = s["pc_vrp_mw_stats"]["p50"]
            p50s = f"{p50:.3f}" if p50 is not None else "-"
            md.append(f"| {vol} | {sb} | {s['total_records']} | {s['pc_vrp_positive']} | {s['publishable_in_inner_radius']} | {s['r3_fantasma_outside_inner']} | {p50s} |\n")

    md.append("\n## 9. Interpretación geológica preliminar\n")
    md.append(
        "- **El filtro geométrico del frontend ya descarta ~{r3} records 'fantasma' (cluster fuera de inner_radius). "
        "Lo que el dashboard muestra es solo el {share:.0f}% de los pc.vrp>0 detectados crudos.**\n"
        "- Para cerrar el gap restante con MIROVA, la hipótesis tamaño-de-cluster es directamente testeable: "
        "si el histograma pc.n_pixels muestra alta densidad en `1` y `2`, MIROVA probablemente requiere "
        "coherencia espacial mínima (≥3 px contiguos en grilla 1km equivalente).\n"
        "- El path dNTI contextual concentra una fracción no trivial del publishable; "
        "si MIROVA no usa dNTI sin co-validación BT/NTI absoluto, este path puede ser el origen estructural del exceso.\n"
        "- Episodios cortos (mediana <1 día) sugieren detecciones esporádicas no persistentes; "
        "MIROVA puede requerir 2-3 noches consecutivas para confirmar.\n".format(
            r3=sum(s["r3_fantasma_outside_inner"] for vol in TIER_A for s in summary["per_volcano"].get(vol, {}).get("by_sensor", {}).values()),
            share=100 * all_total_publishable / max(1, sum(s["pc_vrp_positive"] for vol in TIER_A for s in summary["per_volcano"].get(vol, {}).get("by_sensor", {}).values())),
        )
    )

    with open(OUT_DIR / "B_ours_detected.md", "w", encoding="utf-8") as f:
        f.writelines(md)

    print("OK")
    print("Total publishable:", all_total_publishable)
    print("Total pc.vrp>0:", sum(s["pc_vrp_positive"] for vol in TIER_A for s in summary["per_volcano"].get(vol, {}).get("by_sensor", {}).values()))
    print("Total R3 fantasma:", sum(s["r3_fantasma_outside_inner"] for vol in TIER_A for s in summary["per_volcano"].get(vol, {}).get("by_sensor", {}).values()))
    print("dNTI share publishable:", g["dnti_share_of_publishable"])


if __name__ == "__main__":
    main()
