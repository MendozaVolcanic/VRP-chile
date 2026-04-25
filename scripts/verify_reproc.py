"""verify_reproc.py — auditoría post-reproceso de records VRP Chile.

Mecanismo M2 instalado S18 2026-04-24 a pedido de Nicolás (auditoría meta).

Atiende los 3 supuestos rojos identificados en la auditoría S18:
  - #1 NOAA-21 calibración equivalente a SNPP/NOAA-20 (no validado empíricamente).
  - #3 1955 pixels en Lascar son ruido del altiplano (sin investigar).
  - #4 exclusion_zones P3.6 aplicando en el reproceso S18 (sin verificar).

Uso:
  python scripts/verify_reproc.py
  python scripts/verify_reproc.py --volcanoes Tupungatito,Chaiten,Lascar \
                                   --start 2026-04-08 --end 2026-04-22
  python scripts/verify_reproc.py --profile mirova_equivalent

Output: 4 secciones con banderas [OK]/[WARN]/[FAIL] + listado de records sospechosos.
Salida JSON adicional con --json para integrarlo en CI o golden tests.
"""

import argparse
import io
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import yaml


ROOT = Path(__file__).parent.parent
DEFAULT_VOLS = ["Tupungatito", "Chaiten", "Lascar"]

VIIRS_I = {"VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21"}
VIIRS_M = {"VIIRS_SNPP_750", "VIIRS_NOAA20_750", "VIIRS_NOAA21_750"}
ALL_VIIRS = VIIRS_I | VIIRS_M

# Umbrales físicos para las verificaciones
MAX_REASONABLE_BT_K = 600.0   # MIROVA observa T_hot < 1500 K en saturación; 600 K nocturno = sospechoso
MAX_REASONABLE_PX = 1000      # >1000 pixels anómalos en un solo record sugiere terreno difuso, no señal puntual
MAX_BT_DELTA_OK_K = 1.0       # delta median(BT NOAA-21) vs SNPP/NOAA-20 < 1K = calibración consistente
MAX_BT_DELTA_FAIL_K = 2.0     # >2K sugiere sesgo de calibración real
MIN_NOAA21_RATIO_OK = 0.5     # NOAA-21 debe traer >=50% de pasadas que SNPP en la misma ventana


def _utf8_stdout():
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def _load_yaml_volcanoes():
    with open(ROOT / "volcanoes.yaml", "r", encoding="utf-8") as f:
        return {v["name"]: v for v in yaml.safe_load(f)["volcanoes"]}


def _load_records(profile, vol, start, end):
    p = ROOT / "data" / profile / f"{vol}.json"
    if not p.exists():
        return []
    d = json.load(open(p, "r", encoding="utf-8"))
    out = []
    for r in d.get("records", []):
        try:
            dt = datetime.strptime(r.get("datetime_utc", "")[:16], "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        if not (start <= dt <= end):
            continue
        r["_dt"] = dt
        out.append(r)
    return out


def _flag(level):
    """Plain-ASCII tags for Windows console safety."""
    return {"OK": "[OK]   ", "WARN": "[WARN] ", "FAIL": "[FAIL] ", "SKIP": "[SKIP] "}[level]


def check_calibration_noaa21(vol, recs):
    """Compara BT_max NOAA-21 vs SNPP/NOAA-20 en pasadas del mismo día.

    Una calibración consistente da deltas < 1 K. >2 K sugiere sesgo real.
    """
    by_day = defaultdict(lambda: {"snpp": [], "n20": [], "n21": []})
    for r in recs:
        if r["sensor"] not in VIIRS_I:
            continue
        bt = r.get("t_max_k") or r.get("t_max_i04_k")
        if bt is None or bt <= 0:
            continue
        d = r["datetime_utc"][:10]
        if r["sensor"] == "VIIRS_SNPP":
            by_day[d]["snpp"].append(bt)
        elif r["sensor"] == "VIIRS_NOAA20":
            by_day[d]["n20"].append(bt)
        elif r["sensor"] == "VIIRS_NOAA21":
            by_day[d]["n21"].append(bt)

    deltas = []
    for d, stuff in by_day.items():
        if not stuff["n21"]:
            continue
        m_n21 = statistics.median(stuff["n21"])
        others = stuff["snpp"] + stuff["n20"]
        if not others:
            continue
        m_other = statistics.median(others)
        deltas.append(m_n21 - m_other)

    if not deltas:
        return ("SKIP", f"{vol}: sin pasadas NOAA-21 con SNPP/NOAA-20 en mismo día (no comparable)", {})

    avg = statistics.mean(deltas)
    abs_avg = abs(avg)
    n = len(deltas)
    if abs_avg < MAX_BT_DELTA_OK_K:
        level = "OK"
    elif abs_avg < MAX_BT_DELTA_FAIL_K:
        level = "WARN"
    else:
        level = "FAIL"
    msg = f"{vol}: delta BT(NOAA-21 - otros) = {avg:+.2f} K promedio en {n} días"
    return (level, msg, {"avg_delta_k": avg, "n_days": n, "deltas": deltas})


def check_exclusion_zones(vol, vol_cfg, recs):
    """Verifica que exclusion_zones P3.6 esté aplicando."""
    if not vol_cfg.get("exclude_zones"):
        return ("SKIP", f"{vol}: sin exclude_zones configurado en YAML", {})

    viirs_recs = [r for r in recs if r.get("sensor") in ALL_VIIRS]
    n_total = len(viirs_recs)
    n_excluded_present = sum(1 for r in viirs_recs if (r.get("n_excluded_water") or 0) > 0)

    if n_total == 0:
        return ("SKIP", f"{vol}: sin records VIIRS para verificar", {})

    pct = 100.0 * n_excluded_present / n_total
    if n_excluded_present == 0:
        level = "FAIL"
        msg = f"{vol}: 0/{n_total} VIIRS records con n_excluded_water>0 — exclusion_zones probablemente NO aplicó"
    elif pct < 5:
        level = "WARN"
        msg = f"{vol}: {n_excluded_present}/{n_total} ({pct:.1f}%) VIIRS records excluyeron pixels — bajo, verificar"
    else:
        level = "OK"
        msg = f"{vol}: {n_excluded_present}/{n_total} ({pct:.1f}%) VIIRS records excluyeron pixels (zona configurada)"
    return (level, msg, {"n_total": n_total, "n_with_exclusion": n_excluded_present, "pct": pct})


def check_suspicious_records(vol, recs):
    """Lista records con BT > 600 K o n_anomalous > 1000 (potencial flag mal enmascarado o ruido)."""
    suspects = []
    for r in recs:
        flags = []
        bt = r.get("t_max_k") or r.get("t_max_i04_k") or 0
        if bt > MAX_REASONABLE_BT_K:
            flags.append(f"BT={bt:.1f}K>{MAX_REASONABLE_BT_K:.0f}")
        nx = r.get("n_anomalous_pixels") or 0
        if nx > MAX_REASONABLE_PX:
            flags.append(f"n_pixels={nx}>{MAX_REASONABLE_PX}")
        if flags:
            suspects.append({
                "datetime_utc": r.get("datetime_utc"),
                "sensor": r.get("sensor"),
                "vrp_mw": r.get("vrp_mw"),
                "flags": flags,
            })

    if not suspects:
        return ("OK", f"{vol}: sin records sospechosos (BT>{MAX_REASONABLE_BT_K:.0f}K o n_pixels>{MAX_REASONABLE_PX})", {})

    level = "WARN"  # WARN no FAIL — pueden ser eventos reales (Lascar 1955 px puede ser pluma legítima)
    msg = f"{vol}: {len(suspects)} records sospechosos a revisar"
    return (level, msg, {"suspects": suspects})


def check_sensor_coverage(vol, recs):
    """Verifica que NOAA-21 esté trayendo pasadas en línea con SNPP."""
    counts = defaultdict(int)
    for r in recs:
        counts[r.get("sensor", "?")] += 1

    snpp_i = counts.get("VIIRS_SNPP", 0)
    n21_i = counts.get("VIIRS_NOAA21", 0)
    snpp_m = counts.get("VIIRS_SNPP_750", 0)
    n21_m = counts.get("VIIRS_NOAA21_750", 0)

    issues = []
    if snpp_i > 0:
        ratio_i = n21_i / snpp_i
        if ratio_i < MIN_NOAA21_RATIO_OK:
            issues.append(f"NOAA-21 I-band ratio {ratio_i:.2f}<{MIN_NOAA21_RATIO_OK} vs SNPP")
    if snpp_m > 0:
        ratio_m = n21_m / snpp_m
        if ratio_m < MIN_NOAA21_RATIO_OK:
            issues.append(f"NOAA-21 M-band ratio {ratio_m:.2f}<{MIN_NOAA21_RATIO_OK} vs SNPP")

    if issues:
        return ("WARN", f"{vol}: {'; '.join(issues)}", dict(counts))

    parts = []
    if snpp_i + n21_i > 0:
        parts.append(f"I={counts.get('VIIRS_SNPP',0)}/{counts.get('VIIRS_NOAA20',0)}/{counts.get('VIIRS_NOAA21',0)}")
    if snpp_m + n21_m > 0:
        parts.append(f"M={counts.get('VIIRS_SNPP_750',0)}/{counts.get('VIIRS_NOAA20_750',0)}/{counts.get('VIIRS_NOAA21_750',0)}")
    return ("OK", f"{vol}: cobertura SNPP/NOAA20/NOAA21 = " + " ".join(parts), dict(counts))


def main():
    _utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--volcanoes", default=",".join(DEFAULT_VOLS),
                    help=f"Lista CSV de volcanes a auditar. Default: {','.join(DEFAULT_VOLS)}")
    ap.add_argument("--profile", default="mirova_equivalent",
                    choices=["mirova_equivalent", "experimental",
                             "mirova_equivalent_backfill_nov2025", "s9_vent_permissive",
                             "nsigma_mir_5", "nsigma_mir_12"])
    ap.add_argument("--start", default="2026-04-08")
    ap.add_argument("--end", default="2026-04-22")
    ap.add_argument("--json", action="store_true", help="Print JSON output instead of human-readable")
    args = ap.parse_args()

    vols = [v.strip() for v in args.volcanoes.split(",") if v.strip()]
    start = datetime.strptime(args.start, "%Y-%m-%d")
    end = datetime.strptime(args.end + " 23:59", "%Y-%m-%d %H:%M")
    yaml_cfg = _load_yaml_volcanoes()

    results = {}
    for vol in vols:
        vol_cfg = yaml_cfg.get(vol, {})
        recs = _load_records(args.profile, vol, start, end)
        results[vol] = {
            "n_records": len(recs),
            "calibration": check_calibration_noaa21(vol, recs),
            "exclusion_zones": check_exclusion_zones(vol, vol_cfg, recs),
            "suspicious": check_suspicious_records(vol, recs),
            "coverage": check_sensor_coverage(vol, recs),
        }

    if args.json:
        # Limpio tuples para JSON serializable
        clean = {}
        for vol, r in results.items():
            clean[vol] = {
                "n_records": r["n_records"],
                "calibration": {"level": r["calibration"][0], "msg": r["calibration"][1], "data": r["calibration"][2]},
                "exclusion_zones": {"level": r["exclusion_zones"][0], "msg": r["exclusion_zones"][1], "data": r["exclusion_zones"][2]},
                "suspicious": {"level": r["suspicious"][0], "msg": r["suspicious"][1], "data": r["suspicious"][2]},
                "coverage": {"level": r["coverage"][0], "msg": r["coverage"][1], "data": r["coverage"][2]},
            }
        print(json.dumps(clean, indent=2, default=str))
        return

    print("=" * 92)
    print(f"VERIFY REPROC — perfil={args.profile} | ventana={args.start} a {args.end}")
    print("=" * 92)

    overall = []
    for vol, r in results.items():
        print(f"\n[{vol}] {r['n_records']} records en ventana")
        for check_name in ("coverage", "calibration", "exclusion_zones", "suspicious"):
            level, msg, _ = r[check_name]
            print(f"  {_flag(level)} {check_name:18s} {msg}")
            overall.append(level)
        # Listar sospechosos si hay
        susp_data = r["suspicious"][2]
        if susp_data.get("suspects"):
            for s in susp_data["suspects"][:5]:
                vrp = s.get("vrp_mw")
                vrp_str = f"{vrp:>8.1f}" if isinstance(vrp, (int, float)) else "    -   "
                print(f"           ! {str(s['datetime_utc']):18s} {str(s['sensor']):25s} vrp={vrp_str} flags={s['flags']}")

    print()
    print("-" * 92)
    n_ok = sum(1 for x in overall if x == "OK")
    n_warn = sum(1 for x in overall if x == "WARN")
    n_fail = sum(1 for x in overall if x == "FAIL")
    n_skip = sum(1 for x in overall if x == "SKIP")
    print(f"RESUMEN: {n_ok} OK | {n_warn} WARN | {n_fail} FAIL | {n_skip} SKIP")
    if n_fail:
        print("Hay verificaciones FAIL — investigar antes de seguir.")
    elif n_warn:
        print("Hay verificaciones WARN — revisar; pipeline funcional pero con observaciones.")
    else:
        print("Todo OK — pipeline funcionando dentro de tolerancias esperadas.")


if __name__ == "__main__":
    main()
