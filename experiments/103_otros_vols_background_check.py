"""
S58 — OTROS-VOLS-BACKGROUND-CHECK.

Pregunta: ¿el bug del background ring caliente (median sesgado por
lake/valley/salar) afecta también a los otros vols Tier A además de
Villarrica?

Método (offline, sin reproc):
1) Para cada Tier A, leer data/mirova_equivalent/<Vol>.json.
2) Filtrar VIIRS-I (375m) records con anomaly_pixels y primary_cluster
   válidos, dentro de la ventana 2026-04-16 → 2026-05-15 (30d).
3) Para cada record:
   - bg_median = t_bg_k  (median ring 5-25km, actual)
   - bg_sigma  = diag_sigma_bg_k
   - bg_p10_est = bg_median - 1.282 * bg_sigma  (proxy kernel local)
   - bg_p05_est = bg_median - 1.645 * bg_sigma  (proxy kernel local más sensible)
   - Para los AP con dist al centroide_pc < 2 km:
       * frac_over_median = #{bt_k > bg_median} / N
       * frac_over_p10    = #{bt_k > bg_p10_est} / N
4) Cargar CSV consolidado y contar ALERTAs MIROVA en window.
5) Para cada vol, comparar:
   - n_alertas_mirova vs n_records_con_pc_summit (con BT>p10)
   - ratio inflación potencial

Output: tabla CSV + ranking de vols donde el bug aplica.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from datetime import datetime
from pathlib import Path
from collections import defaultdict

REPO = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/nostalgic-aryabhata-e05d1e")
DATA = REPO / "data" / "mirova_equivalent"
CSV_PATH = REPO / "01_05_2026_registro_vrp_consolidado.csv"

WIN_START = datetime(2026, 4, 16)
WIN_END = datetime(2026, 5, 15, 23, 59, 59)

VIIRS_I_SENSORS = {"VIIRS_NOAA20", "VIIRS_NOAA21", "VIIRS_SNPP"}  # 375m

TIER_A = [
    "Villarrica",
    "Lascar",
    "Tupungatito",
    "Lastarria",
    "Copahue",
    "Llaima",
    "Isluga",
    "Chaiten",
    "PlanchonPeteroa",
    "NevadosDeChillan",
    "PuyehueCordonCaulle",
]

CSV_NAME_TO_JSON = {
    "Villarrica": "Villarrica",
    "Lascar": "Lascar",
    "Tupungatito": "Tupungatito",
    "Lastarria": "Lastarria",
    "Copahue": "Copahue",
    "Llaima": "Llaima",
    "Isluga": "Isluga",
    "Chaiten": "Chaiten",
    "Chaitén": "Chaiten",
    "Planchon-Peteroa": "PlanchonPeteroa",
    "Planchón-Peteroa": "PlanchonPeteroa",
    "PlanchonPeteroa": "PlanchonPeteroa",
    "Nevados de Chillan": "NevadosDeChillan",
    "Nevados de Chillán": "NevadosDeChillan",
    "NevadosDeChillan": "NevadosDeChillan",
    "Puyehue-Cordon Caulle": "PuyehueCordonCaulle",
    "Puyehue - Cordón Caulle": "PuyehueCordonCaulle",
    "PuyehueCordonCaulle": "PuyehueCordonCaulle",
}


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def parse_dt(s):
    if not s:
        return None
    try:
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", ""))
        return datetime.strptime(s[:16], "%Y-%m-%d %H:%M")
    except Exception:
        return None


def load_csv_alertas():
    """Count ALERTA MIROVA per volcano in window."""
    by_vol = defaultdict(lambda: {"alerta": 0, "rutina": 0, "total": 0})
    with CSV_PATH.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            vol_raw = row.get("Volcan", "").strip()
            vol = CSV_NAME_TO_JSON.get(vol_raw)
            if vol not in TIER_A:
                continue
            dt = parse_dt(row.get("Fecha_Satelite_UTC", ""))
            if not dt or not (WIN_START <= dt <= WIN_END):
                continue
            tipo = (row.get("Tipo_Registro") or "").upper()
            by_vol[vol]["total"] += 1
            if "ALERTA" in tipo:
                by_vol[vol]["alerta"] += 1
            elif "RUTINA" in tipo:
                by_vol[vol]["rutina"] += 1
    return by_vol


def analyze_volcano(vol):
    path = DATA / f"{vol}.json"
    if not path.exists():
        return None
    d = json.loads(path.read_text(encoding="utf-8"))
    recs = d.get("records", [])

    # Aggregate stats
    n_total_window = 0
    n_viirs_i = 0
    n_with_summit_pc = 0  # primary_cluster centroide <2km del vent? proxy = centroid_dist_km < 2
    n_detected_anything = 0  # records con vrp_mw>0 o n_anomalous_pixels>0
    n_alerta_proxy = 0  # records con pc.vrp_mw > 1 MW (proxy alerta)

    bg_medians = []
    bg_sigmas = []
    frac_over_median_summit = []
    frac_over_p10_summit = []
    pc_vrps = []
    record_vrps = []
    bt_minus_median_summit = []  # gradiente actual
    bt_minus_p10_summit = []     # gradiente kernel-local proxy

    for rec in recs:
        dt = parse_dt(rec.get("datetime_utc", ""))
        if not dt or not (WIN_START <= dt <= WIN_END):
            continue
        n_total_window += 1
        sensor = rec.get("sensor", "")
        if sensor not in VIIRS_I_SENSORS:
            continue
        n_viirs_i += 1

        bg_med = rec.get("t_bg_k")
        bg_sig = rec.get("diag_sigma_bg_k")
        if bg_med is not None:
            bg_medians.append(bg_med)
        if bg_sig is not None:
            bg_sigmas.append(bg_sig)

        pc = rec.get("primary_cluster")
        ap = rec.get("anomaly_pixels") or []
        vrp_total = rec.get("vrp_mw", 0) or 0
        if vrp_total > 0 or len(ap) > 0:
            n_detected_anything += 1
        record_vrps.append(vrp_total)

        if not pc or bg_med is None or bg_sig is None:
            continue

        cd = pc.get("centroid_dist_km")
        c_lat = pc.get("centroid_lat")
        c_lon = pc.get("centroid_lon")
        pc_vrp = pc.get("vrp_mw", 0) or 0
        pc_vrps.append(pc_vrp)

        if cd is None or cd >= 2.0:
            continue  # not a summit cluster
        n_with_summit_pc += 1
        if pc_vrp > 1.0:
            n_alerta_proxy += 1

        # AP that belong to the summit cluster (within 2km from centroid pc)
        summit_pix = []
        for p in ap:
            plat, plon = p.get("lat"), p.get("lon")
            pbt = p.get("bt_k")
            if plat is None or plon is None or pbt is None:
                continue
            d2c = haversine_km(c_lat, c_lon, plat, plon)
            if d2c <= 2.0:
                summit_pix.append(pbt)

        if not summit_pix:
            continue

        p10 = bg_med - 1.282 * bg_sig
        over_med = sum(1 for b in summit_pix if b > bg_med) / len(summit_pix)
        over_p10 = sum(1 for b in summit_pix if b > p10) / len(summit_pix)
        frac_over_median_summit.append(over_med)
        frac_over_p10_summit.append(over_p10)

        max_bt = max(summit_pix)
        bt_minus_median_summit.append(max_bt - bg_med)
        bt_minus_p10_summit.append(max_bt - p10)

    def med(xs):
        return statistics.median(xs) if xs else None

    return {
        "vol": vol,
        "n_total_window": n_total_window,
        "n_viirs_i": n_viirs_i,
        "n_with_summit_pc": n_with_summit_pc,
        "n_detected_anything": n_detected_anything,
        "n_alerta_proxy_pc_vrp_gt1": n_alerta_proxy,
        "bg_median_med_K": med(bg_medians),
        "bg_sigma_med_K": med(bg_sigmas),
        "frac_over_actual_median_summit_med": med(frac_over_median_summit),
        "frac_over_p10_kernel_proxy_med": med(frac_over_p10_summit),
        "delta_bt_max_minus_median_med_K": med(bt_minus_median_summit),
        "delta_bt_max_minus_p10_med_K": med(bt_minus_p10_summit),
        "pc_vrp_med_MW": med(pc_vrps),
        "pc_vrp_max_MW": max(pc_vrps) if pc_vrps else None,
        "record_vrp_med_MW": med(record_vrps),
    }


def main():
    print(f"Window: {WIN_START.date()} -> {WIN_END.date()}  (VIIRS-I 375m only)")
    print()

    csv_alertas = load_csv_alertas()

    rows = []
    for vol in TIER_A:
        r = analyze_volcano(vol)
        if r is None:
            print(f"  {vol}: NO JSON")
            continue
        ca = csv_alertas.get(vol, {})
        r["mirova_alerta_csv"] = ca.get("alerta", 0)
        r["mirova_rutina_csv"] = ca.get("rutina", 0)
        r["mirova_total_csv"] = ca.get("total", 0)
        # ratio inflación: detecciones nuestras vs alertas reales MIROVA
        if r["mirova_alerta_csv"] > 0:
            r["ratio_inflacion"] = round(r["n_alerta_proxy_pc_vrp_gt1"] / r["mirova_alerta_csv"], 2)
        else:
            r["ratio_inflacion"] = None if r["n_alerta_proxy_pc_vrp_gt1"] == 0 else float("inf")
        rows.append(r)

    # Print main table
    cols = [
        "vol",
        "mirova_alerta_csv",
        "n_with_summit_pc",
        "n_alerta_proxy_pc_vrp_gt1",
        "ratio_inflacion",
        "bg_median_med_K",
        "bg_sigma_med_K",
        "frac_over_actual_median_summit_med",
        "frac_over_p10_kernel_proxy_med",
        "delta_bt_max_minus_median_med_K",
        "delta_bt_max_minus_p10_med_K",
        "pc_vrp_med_MW",
        "pc_vrp_max_MW",
    ]
    widths = {c: max(len(c), 10) for c in cols}
    print(" | ".join(c.ljust(widths[c]) for c in cols))
    print("-+-".join("-" * widths[c] for c in cols))
    for r in rows:
        line = []
        for c in cols:
            v = r.get(c)
            if isinstance(v, float):
                s = f"{v:.3f}" if abs(v) < 100 else f"{v:.1f}"
            else:
                s = str(v)
            line.append(s.ljust(widths[c]))
        print(" | ".join(line))

    # Persist JSON for downstream
    out = REPO / "experiments" / "103_otros_vols_background_check.json"
    out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
