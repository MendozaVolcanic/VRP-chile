"""
79 — A/B comparison H8 enabled vs disabled vs operacional baseline.

Corre cuando A/B reproceso run 25623575250 termina. Compara los tres datasets:
  - data/mirova_equivalent/        (operacional baseline, bug H8 activo)
  - data/_h8_pixel_filter_disabled (control A/B replica baseline)
  - data/_h8_pixel_filter_enabled  (fix H8 activo)

Para cada (volcán, sensor, datetime) reportar:
  - VRP en cada dataset
  - clase distance
  - n_anomalous_pixels
  - discarded vs preservado

Métricas agregadas:
  - Recall vs MIROVA consolidado (ALERTA_TERMICA)
  - Ratio mediano VRP-chile / MIROVA
  - FP rate (records con vrp_mw > 0 sin alerta MIROVA)
  - Delta entre H8 enabled y disabled (= efecto del fix)

Output: reports/h8_ab_comparison.{csv,md}
"""
from __future__ import annotations
import csv, json, sys, io, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_BASELINE = REPO_ROOT / "data" / "mirova_equivalent"
DATA_H8_OFF = REPO_ROOT / "data" / "_h8_pixel_filter_disabled"
DATA_H8_ON = REPO_ROOT / "data" / "_h8_pixel_filter_enabled"

VOL_MAP_TO_CONS = {
    'Isluga':'Isluga','Lascar':'Lascar','Lastarria':'Lastarria','Tupungatito':'Tupungatito',
    'PlanchonPeteroa':'PlanchonPeteroa','NevadosDeChillan':'Nevados de Chillan',
    'Copahue':'Copahue','Llaima':'Llaima','Villarrica':'Villarrica',
    'PuyehueCordonCaulle':'Puyehue-Cordon Caulle','Chaiten':'Chaitén',
}

# Inner radius por volcán (mismo que pipeline/audit_metrics.py)
INNER_RADIUS_KM = {
    'Lascar':5,'Lastarria':3,'Tupungatito':7,'Villarrica':5,
    'PuyehueCordonCaulle':20,'Copahue':4,'NevadosDeChillan':5,
    'Llaima':5,'Chaiten':5,'PlanchonPeteroa':3,'Isluga':5,
}


def load_consolidado_alertas():
    """Returns set of (vol_internal, sensor, time_str_minute) for ALERTA_TERMICA + FP."""
    p = "/tmp/cons_h8.csv"
    try:
        urllib.request.urlretrieve(
            "https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/monitoreo_satelital/registro_vrp_consolidado.csv", p)
    except Exception:
        pass
    alertas = {}  # (vol, sens, ts_minute) -> {tipo, vrp, dist}
    rev_map = {v: k for k, v in VOL_MAP_TO_CONS.items()}
    with open(p, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            v = r["Volcan"].strip()
            v_int = rev_map.get(v)
            if v_int is None: continue
            tipo = r["Tipo_Registro"].strip()
            ts = r["Fecha_Satelite_UTC"].strip()
            if len(ts) < 16: continue
            sens = r["Sensor"].strip()
            alertas[(v_int, sens, ts[:16])] = {
                "tipo": tipo,
                "vrp": float(r.get("VRP_MW", 0) or 0),
                "dist": float(r.get("Distancia_km", 0) or 0),
            }
    return alertas


def load_records(data_dir, since="2026-04-15"):
    """Returns {(vol, sensor, datetime_utc): record}."""
    out = {}
    if not data_dir.exists(): return out
    for jf in data_dir.glob("*.json"):
        vol = jf.stem
        with open(jf) as f: data = json.load(f)
        recs = data if isinstance(data, list) else data.get("records", [])
        for r in recs:
            dt = r.get("datetime_utc", "")
            if dt < since: continue
            sensor = r.get("sensor", "")
            out[(vol, sensor, dt)] = r
    return out


def sensor_archive_to_consolidado(sens):
    """Map VRP-chile sensor to consolidado sensor naming."""
    if "MODIS" in sens: return "MODIS"
    if "_750" in sens: return "VIIRS"
    return "VIIRS375"


def main():
    print("Loading consolidado MIROVA alertas...")
    alertas = load_consolidado_alertas()
    print(f"  {len(alertas)} entries (post 2026-04-10)")
    n_alerta = sum(1 for v in alertas.values() if v["tipo"] == "ALERTA_TERMICA")
    n_fp = sum(1 for v in alertas.values() if v["tipo"] == "FALSO_POSITIVO")
    print(f"  ALERTA_TERMICA: {n_alerta}, FP: {n_fp}")

    print("\\nLoading records...")
    baseline = load_records(DATA_BASELINE)
    h8_off = load_records(DATA_H8_OFF)
    h8_on = load_records(DATA_H8_ON)
    print(f"  baseline:  {len(baseline)} records")
    print(f"  h8 OFF:    {len(h8_off)} records")
    print(f"  h8 ON:     {len(h8_on)} records")

    if not h8_on or not h8_off:
        print("\\n!!! A/B data not yet available. Re-run when reproceso completes.")
        return

    # Union all keys
    all_keys = set(baseline.keys()) | set(h8_off.keys()) | set(h8_on.keys())
    print(f"\\n  union keys: {len(all_keys)}")

    rows = []
    for key in sorted(all_keys):
        vol, sens, dt = key
        sens_cons = sensor_archive_to_consolidado(sens)
        ts_min = dt[:16]
        m_alert = alertas.get((vol, sens_cons, ts_min))

        b = baseline.get(key, {})
        o = h8_off.get(key, {})
        n = h8_on.get(key, {})

        rows.append({
            "vol": vol, "sensor": sens, "datetime_utc": dt,
            "mirova_tipo": m_alert["tipo"] if m_alert else "",
            "mirova_vrp": m_alert["vrp"] if m_alert else "",
            "mirova_dist": m_alert["dist"] if m_alert else "",
            "baseline_vrp_mw": b.get("vrp_mw", ""),
            "baseline_disc": b.get("discarded_reason", ""),
            "h8_off_vrp_mw": o.get("vrp_mw", ""),
            "h8_off_disc": o.get("discarded_reason", ""),
            "h8_on_vrp_mw": n.get("vrp_mw", ""),
            "h8_on_disc": n.get("discarded_reason", ""),
            "h8_on_n_in_range": len(n.get("anomaly_pixels", [])),
            "h8_on_n_disc": n.get("discarded_n_pixels", 0),
        })

    # Write CSV
    reports = REPO_ROOT / "reports"
    reports.mkdir(exist_ok=True)
    out_csv = reports / "h8_ab_comparison.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\\n  wrote {out_csv}")

    # Métricas agregadas
    print("\\n=== MÉTRICAS RECALL vs ALERTA MIROVA ===")
    print(f"{'Profile':<20} {'Recall':<10} {'TP':>6} {'FN':>6}")
    print("-" * 50)
    for label, dataset in [("baseline", baseline), ("h8_off", h8_off), ("h8_on", h8_on)]:
        tp = fn = 0
        for (vol, sens, dt_min), info in alertas.items():
            if info["tipo"] != "ALERTA_TERMICA": continue
            sens_cons_options = ["MODIS"] if sens == "MODIS" else ["VIIRS"] if sens == "VIIRS" else ["VIIRS375"]
            # Find any record matching vol + sensor variant + minute
            found = False
            for k, r in dataset.items():
                if k[0] != vol: continue
                if k[2][:16] != dt_min: continue
                if sensor_archive_to_consolidado(k[1]) != sens: continue
                if (r.get("vrp_mw", 0) or 0) > 0:
                    found = True
                    break
            if found: tp += 1
            else: fn += 1
        recall = 100 * tp / (tp + fn) if (tp + fn) else 0
        print(f"{label:<20} {recall:>6.1f}%  {tp:>6} {fn:>6}")

    print("\\n=== MÉTRICAS RATIO VRP (vs MIROVA reported) ===")
    print(f"{'Profile':<20} {'n':<6} {'mediana':<10} {'mean':<10}")
    print("-" * 50)
    import statistics
    for label, dataset in [("baseline", baseline), ("h8_off", h8_off), ("h8_on", h8_on)]:
        ratios = []
        for (vol, sens, dt_min), info in alertas.items():
            if info["tipo"] != "ALERTA_TERMICA": continue
            if info["vrp"] <= 0: continue
            sens_cons = sens
            for k, r in dataset.items():
                if k[0] != vol: continue
                if k[2][:16] != dt_min: continue
                if sensor_archive_to_consolidado(k[1]) != sens_cons: continue
                vrp = r.get("vrp_mw", 0) or 0
                if vrp > 0:
                    ratios.append(vrp / info["vrp"])
                    break
        if ratios:
            print(f"{label:<20} {len(ratios):<6} {statistics.median(ratios):<10.2f} {statistics.mean(ratios):<10.2f}")

    # H8 specific recovery cases
    print("\\n=== RECOVERY CASES (h8_off vrp=0, h8_on vrp>0) ===")
    recovered = []
    for r in rows:
        if (r["h8_off_vrp_mw"] in (0, "0", 0.0)) and isinstance(r["h8_on_vrp_mw"], (int, float)) and r["h8_on_vrp_mw"] > 0:
            recovered.append(r)
    print(f"Total recovered: {len(recovered)}")
    for r in recovered[:15]:
        print(f"  {r['vol']:<22} {r['sensor']:<18} {r['datetime_utc']}: off=0 → on={r['h8_on_vrp_mw']}  mirova={r['mirova_tipo'] or '-'} ({r['mirova_vrp']}@{r['mirova_dist']}km)")

    # H8 specific regressions
    print("\\n=== REGRESSION CASES (h8_off vrp>0, h8_on vrp=0) ===")
    regressed = []
    for r in rows:
        if isinstance(r["h8_off_vrp_mw"], (int, float)) and r["h8_off_vrp_mw"] > 0 and (r["h8_on_vrp_mw"] in (0, "0", 0.0)):
            regressed.append(r)
    print(f"Total regressed: {len(regressed)}")
    for r in regressed[:10]:
        print(f"  {r['vol']:<22} {r['sensor']:<18} {r['datetime_utc']}: off={r['h8_off_vrp_mw']} → on=0  mirova={r['mirova_tipo'] or '-'}")


if __name__ == "__main__":
    main()
