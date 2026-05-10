"""
77 — R2 audit independiente del fix H8 (pixel-level distance filter).

Cruza:
  1. mirova-tif-archive (TIFs deterministic con acquisition_utc real)
  2. Mirova-v1 consolidado (latest.php scraping con ALERTA_TERMICA / FP / RUTINA)
  3. data/mirova_equivalent/*.json (records VRP-chile actuales con bug)
  4. data/_h8_pixel_filter_enabled/*.json (records con fix H8) — cuando esté disponible

Para cada acquisition con TIF capturado:
  - ¿MIROVA reportó ALERTA / FP / RUTINA?
  - ¿VRP-chile (legacy) descartó? ¿qué vrp_mw final?
  - ¿VRP-chile (H8) qué vrp_mw devuelve?
  - Dist match con MIROVA?

Output: reports/r2_h8_audit.csv + reports/r2_h8_summary.md
Independiente del audit_metrics.py para satisfacer R3.
"""
from __future__ import annotations
import csv, json, sys, io, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_INDEX = REPO_ROOT.parent.parent.parent.parent / "mirova-tif-archive" / "index.csv"
LEGACY_DATA = REPO_ROOT / "data" / "mirova_equivalent"
H8_DATA = REPO_ROOT / "data" / "_h8_pixel_filter_enabled"

# Map naming
VOL_MAP_TO_CONS = {
    'Isluga':'Isluga','Lascar':'Lascar','Lastarria':'Lastarria','Tupungatito':'Tupungatito',
    'PlanchonPeteroa':'PlanchonPeteroa','ChillanNevadosde':'Nevados de Chillan',
    'Copahue':'Copahue','Llaima':'Llaima','Villarrica':'Villarrica',
    'PuyehueCordonCaulle':'Puyehue-Cordon Caulle','Chaiten':'Chaitén',
}
ARCHIVE_TO_VRP = {
    'Isluga':'Isluga','Lascar':'Lascar','Lastarria':'Lastarria','Tupungatito':'Tupungatito',
    'PlanchonPeteroa':'PlanchonPeteroa','ChillanNevadosde':'NevadosDeChillan',
    'Copahue':'Copahue','Llaima':'Llaima','Villarrica':'Villarrica',
    'PuyehueCordonCaulle':'PuyehueCordonCaulle','Chaiten':'Chaiten',
}
SENS_ARCHIVE_TO_VRP = {
    'MODIS': ['MODIS_AQUA', 'MODIS_TERRA'],
    'VIIRS750': ['VIIRS_NOAA20_750', 'VIIRS_NOAA21_750', 'VIIRS_SNPP_750'],
    'VIIRS375': ['VIIRS_NOAA20', 'VIIRS_NOAA21', 'VIIRS_SNPP'],
}


def load_consolidado():
    p = "/tmp/cons.csv"
    try:
        urllib.request.urlretrieve(
            "https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/monitoreo_satelital/registro_vrp_consolidado.csv", p)
    except Exception as e:
        print(f"WARN consolidado fetch failed: {e}")
    cons = defaultdict(dict)  # (vol, sensor, time_str) -> {tipo, vrp, dist}
    with open(p, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            v = r["Volcan"].strip()
            v_arch = next((k for k, vv in VOL_MAP_TO_CONS.items() if vv == v), None)
            if v_arch is None: continue
            ts = r["Fecha_Satelite_UTC"].strip()
            sens = r["Sensor"].strip()
            cons[(v_arch, sens, ts)] = {
                "tipo": r["Tipo_Registro"].strip(),
                "vrp": float(r.get("VRP_MW", 0) or 0),
                "dist": float(r.get("Distancia_km", 0) or 0),
            }
    return cons


def load_archive_index():
    """Returns {(vol_archive, sensor_archive, acquisition_utc): row}"""
    out = {}
    if not ARCHIVE_INDEX.exists():
        print(f"WARN archive index not found at {ARCHIVE_INDEX}")
        return out
    with open(ARCHIVE_INDEX, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r.get("acquisition_utc"): continue
            key = (r["volcano"], r["sensor"], r["acquisition_utc"])
            out[key] = r
    return out


def load_vrp_records(data_dir):
    """Returns {(vol_archive, sensor_archive, datetime_utc): record}"""
    out = {}
    if not data_dir.exists():
        return out
    arch_to_vrp = ARCHIVE_TO_VRP
    vrp_to_arch = {v: k for k, v in arch_to_vrp.items()}
    for jf in data_dir.glob("*.json"):
        v_vrp = jf.stem
        v_arch = vrp_to_arch.get(v_vrp, v_vrp)
        try:
            with open(jf) as f: data = json.load(f)
        except Exception:
            continue
        recs = data if isinstance(data, list) else data.get("records", [])
        for r in recs:
            sens = r.get("sensor", "")
            ts = r.get("datetime_utc", "")
            if not sens or not ts: continue
            out[(v_arch, sens, ts)] = r
    return out


def main():
    print("Loading consolidado MIROVA...")
    cons = load_consolidado()
    print(f"  {len(cons)} entries")

    print(f"Loading archive index from {ARCHIVE_INDEX}")
    archive = load_archive_index()
    print(f"  {len(archive)} TIFs deterministic")

    print(f"Loading legacy VRP-chile records from {LEGACY_DATA}")
    legacy = load_vrp_records(LEGACY_DATA)
    print(f"  {len(legacy)} records (legacy)")

    print(f"Loading H8 VRP-chile records from {H8_DATA}")
    h8 = load_vrp_records(H8_DATA)
    print(f"  {len(h8)} records (H8 enabled)")

    # Para cada TIF en archive (con acq_utc), buscar:
    # - Mirova-v1 entry para misma (vol, sensor, time)
    # - VRP-chile legacy record más cercano
    # - VRP-chile H8 record más cercano
    rows = []
    for (v_arch, sens_arch, acq_iso), arch_row in archive.items():
        # Format acq for matching
        try:
            acq_dt = datetime.fromisoformat(acq_iso)
        except Exception:
            continue
        time_str = acq_dt.strftime("%Y-%m-%d %H:%M:%S")
        vrp_dt_str = acq_dt.strftime("%Y-%m-%d %H:%M")

        # Look up Mirova-v1 (within ±1 min — may have rounding)
        cons_match = None
        for delta in [0, 60, -60, 120, -120]:
            t = (acq_dt + timedelta(seconds=delta)).strftime("%Y-%m-%d %H:%M:%S")
            for sens_cons in (
                ["MODIS"] if sens_arch == "MODIS"
                else ["VIIRS"] if sens_arch == "VIIRS750"
                else ["VIIRS375"]
            ):
                cm = cons.get((v_arch, sens_cons, t))
                if cm:
                    cons_match = cm
                    break
            if cons_match: break

        # Look up VRP-chile legacy + H8 (any sensor variant matching)
        sens_vrp_options = SENS_ARCHIVE_TO_VRP.get(sens_arch, [])
        legacy_match = None
        h8_match = None
        for sens_vrp in sens_vrp_options:
            lm = legacy.get((v_arch, sens_vrp, vrp_dt_str))
            if lm and not legacy_match: legacy_match = (sens_vrp, lm)
            hm = h8.get((v_arch, sens_vrp, vrp_dt_str))
            if hm and not h8_match: h8_match = (sens_vrp, hm)

        rows.append({
            "vol": v_arch,
            "sensor_archive": sens_arch,
            "acquisition_utc": acq_iso,
            "tif_path": arch_row.get("tif_path", ""),
            "md5": arch_row.get("md5", "")[:10],
            "mirova_tipo": cons_match["tipo"] if cons_match else "",
            "mirova_vrp": cons_match["vrp"] if cons_match else "",
            "mirova_dist": cons_match["dist"] if cons_match else "",
            "legacy_sensor": legacy_match[0] if legacy_match else "",
            "legacy_vrp_mw": legacy_match[1].get("vrp_mw", "") if legacy_match else "",
            "legacy_vrp_mir": legacy_match[1].get("vrp_mir_mw", "") if legacy_match else "",
            "legacy_discarded": legacy_match[1].get("discarded_reason", "") if legacy_match else "",
            "legacy_n_disc_pix": len(legacy_match[1].get("discarded_anomaly_pixels", [])) if legacy_match else 0,
            "h8_vrp_mw": h8_match[1].get("vrp_mw", "") if h8_match else "",
            "h8_vrp_mir": h8_match[1].get("vrp_mir_mw", "") if h8_match else "",
            "h8_discarded": h8_match[1].get("discarded_reason", "") if h8_match else "",
            "h8_n_disc_pix": h8_match[1].get("discarded_n_pixels", 0) if h8_match else "",
        })

    print(f"\\nTotal cross-matches: {len(rows)}")

    # Write CSV
    reports = REPO_ROOT / "reports"
    reports.mkdir(exist_ok=True)
    out_csv = reports / "r2_h8_audit.csv"
    if rows:
        with open(out_csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"  wrote {out_csv}")

    # Summary
    print("\\n=== SUMMARY ===")
    n_with_mirova = sum(1 for r in rows if r["mirova_tipo"])
    n_alerta = sum(1 for r in rows if r["mirova_tipo"] == "ALERTA_TERMICA")
    n_fp = sum(1 for r in rows if r["mirova_tipo"] == "FALSO_POSITIVO")
    n_rutina = sum(1 for r in rows if r["mirova_tipo"] == "RUTINA")
    n_legacy_match = sum(1 for r in rows if r["legacy_sensor"])
    n_legacy_discarded = sum(1 for r in rows if r["legacy_discarded"])
    n_h8_match = sum(1 for r in rows if r["h8_vrp_mw"] != "")
    n_alerta_lost_legacy = sum(1 for r in rows if r["mirova_tipo"] == "ALERTA_TERMICA"
                                and r["legacy_vrp_mw"] == 0 and r["legacy_n_disc_pix"] > 0)

    print(f"TIFs deterministic en archive: {len(rows)}")
    print(f"  con MIROVA cross-match:    {n_with_mirova} (ALERTA={n_alerta}, FP={n_fp}, RUTINA={n_rutina})")
    print(f"  con VRP-chile legacy match: {n_legacy_match} (descartado={n_legacy_discarded})")
    print(f"  con VRP-chile H8 match:    {n_h8_match}")
    print(f"  ALERTA_TERMICA perdida en legacy (vrp=0 + disc_pix>0): {n_alerta_lost_legacy}")

    # Show specific recovery cases (legacy=0, H8>0)
    if n_h8_match:
        print("\\n=== RECOVERY CASES (legacy descarta, H8 preserva) ===")
        recovered = [r for r in rows if r["mirova_tipo"] == "ALERTA_TERMICA"
                     and (r["legacy_vrp_mw"] in (0, "0", 0.0))
                     and isinstance(r["h8_vrp_mw"], (int, float)) and r["h8_vrp_mw"] > 0]
        for r in recovered[:20]:
            print(f"  {r['vol']:<22} {r['sensor_archive']:<10} {r['acquisition_utc']}: "
                  f"MIROVA={r['mirova_vrp']}@{r['mirova_dist']}km  "
                  f"legacy={r['legacy_vrp_mw']}  H8={r['h8_vrp_mw']}")
        print(f"  total recovered: {len(recovered)}")
    else:
        print("\\n(H8 data not available yet — A/B run pending)")

    print(f"\\nFull audit: {out_csv}")


if __name__ == "__main__":
    main()
