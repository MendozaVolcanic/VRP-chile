"""S71 T1 F2.d — R3 audit independiente del winner Opcion C.

Politica R3 (S33+, vinculante): cualquier resultado A/B con mejora >30% requiere
un audit independiente que NO comparta codigo con el audit primario.

Diseño independiente respecto a experiments/128_path_d_ab_audit/audit.py:
  - 128 usa **matching per-night** (tolerancia ±3h, agrega MIROVA por dia UTC y
    cuenta TP/FP/FN como noches). Nuestra agregacion: **matching per-record**
    con tolerancia ±60 min y matching sensor-aware (MODIS<->MODIS,
    VIIRS<->VIIRS_*_750, VIIRS375<->VIIRS_*_375). Esto evita que MIROVA y
    nosotros se "encuentren" porque ambos detectaron en la misma noche pero
    sensores y horas distintos.
  - 128 calcula ratios sobre **eqVrp** (incluye legacy fallback global). Nosotros
    aplicamos la **regla canonica `pc.vrp_mw` validada por
    pc.centroid_dist <= inner_radius_km** (heredada del 76_audit_independent.py
    y de REAUDITORIA_S52). Si pc esta lejos del crater, la deteccion no cuenta
    como del crater — esto disciplina los ratios contra FPs lago/salar/lejanos.
  - 128 usa SOLO `registro_vrp_consolidado.csv`. Nosotros combinamos
    **CONS+OCR** como universo MIROVA (mas robusto contra gaps OCR).
  - Detector del bug D9 independiente: contamos records donde
    pc.vrp_mw>5 MW AND t_bg<260 K AND solo path D contribuyo
    (diag_n_bt_path=0, diag_n_nti_path=0, n_nti_rel_path=0, diag_n_dnti_ctx_path>0).

Verdict esperado:
  - COINCIDE si las 4 columnas reproducen las conclusiones cualitativas del 128
    (C winner, B colapsa NdC, bug count baseline=237 cae a 0 en C).
  - DISCREPANCIA si el winner cambia o NdC no se rompe en B — flagear como
    potencial bug-S33-style del audit primario.
"""
from __future__ import annotations

import io
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
OUT_DIR = Path(__file__).resolve().parent

# Datasets bajo evaluacion
PROFILES = {
    "baseline": DATA_DIR / "mirova_equivalent",
    "A_atm_gate": DATA_DIR / "mirova_equivalent_path_d_atm_gate_v1",
    "B_covalidation": DATA_DIR / "mirova_equivalent_path_d_covalidation_v1",
    "C_cap": DATA_DIR / "mirova_equivalent_path_d_cap_v1",
}

# Ground truth — CONS + OCR (independencia: 128 usa solo CONS)
CSV_CONS = DATA_DIR / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
CSV_OCR = DATA_DIR / "mirova_reference" / "registro_vrp_ocr.csv"

# Mapeo CSV -> nombre carpeta JSON
VOLC_CSV_TO_DIR = {
    "Lascar": "Lascar",
    "Lastarria": "Lastarria",
    "Tupungatito": "Tupungatito",
    "Villarrica": "Villarrica",
    "Puyehue-Cordon Caulle": "PuyehueCordonCaulle",
    "PuyehueCordonCaulle": "PuyehueCordonCaulle",
    "Copahue": "Copahue",
    "Nevados de Chillan": "NevadosDeChillan",
    "NevadosDeChillan": "NevadosDeChillan",
    "Llaima": "Llaima",
    "Chaiten": "Chaiten",
    "PlanchonPeteroa": "PlanchonPeteroa",
    "Planchon-Peteroa": "PlanchonPeteroa",
    "Isluga": "Isluga",
}
VOLS = sorted(set(VOLC_CSV_TO_DIR.values()))

# Inner radius por volcan (canonico MIROVA — copiado de 76_audit_independent.py)
INNER_RADIUS_KM = {
    "Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "Villarrica": 5,
    "PuyehueCordonCaulle": 20, "Copahue": 4, "NevadosDeChillan": 5,
    "Llaima": 5, "Chaiten": 5, "PlanchonPeteroa": 3, "Isluga": 5,
}

# Ventana temporal — interseccion de los 3 experimentos (segun 128)
# Usamos ventana fija ~90 dias terminando 2026-05-20 para reproducibilidad.
END_DT = datetime(2026, 5, 20, 23, 59, tzinfo=timezone.utc)
START_DT = END_DT - timedelta(days=90)

# Independencia: ±60 min (128 usa ±3h)
MATCH_TOL_MIN = 60

# Criterios verdict
BUG_VRP_MIN = 5.0     # MW
BUG_TBG_MAX = 260.0   # K
RATIO_LO, RATIO_HI = 0.5, 2.0
PRECISION_MIN = 0.50
RECALL_MIN = 0.70
N_MIROVA_MIN_FOR_RECALL = 10


def parse_csv_dt(s):
    return datetime.strptime(str(s).strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def parse_rec_dt(s):
    s = str(s).strip().replace("Z", "+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.fromisoformat(s)


def sensor_match(csv_sensor, rec_sensor):
    csv_s = (csv_sensor or "").strip()
    rs = (rec_sensor or "").strip()
    if csv_s == "MODIS":
        return rs.startswith("MODIS")
    if csv_s == "VIIRS":
        # M-band 750m
        return rs.startswith("VIIRS_") and rs.endswith("_750")
    if csv_s == "VIIRS375":
        return rs.startswith("VIIRS_") and not rs.endswith("_750")
    return False


def detection_vrp_canonical(rec, volcano):
    """pc.vrp_mw validado contra inner_radius_km. Sin fallback legacy global."""
    if rec is None:
        return 0.0
    if rec.get("distance_class") == "far":
        return 0.0
    pc = rec.get("primary_cluster")
    if pc is None:
        # No fallback — somos estrictos. Si no hay primary_cluster, no contamos.
        # (Diferencia respecto a 76: alli si habia fallback; nosotros queremos
        # disciplinar contra el ratio que devuelve `eqVrp` con legacy fallback.)
        return 0.0
    centroid_dist = pc.get("centroid_dist_km")
    inner = INNER_RADIUS_KM.get(volcano, 10)
    if centroid_dist is not None and centroid_dist > inner:
        return 0.0
    vrp = pc.get("vrp_mw", 0.0)
    return float(vrp) if vrp else 0.0


def is_path_d_only(rec):
    if rec is None:
        return False
    bt = rec.get("diag_n_bt_path", 0) or 0
    nti = rec.get("diag_n_nti_path", 0) or 0
    nti_rel = rec.get("n_nti_rel_path", 0) or 0
    dnti = rec.get("diag_n_dnti_ctx_path", 0) or 0
    return bt == 0 and nti == 0 and nti_rel == 0 and dnti > 0


def load_records(profile_dir, volcano):
    fp = profile_dir / f"{volcano}.json"
    if not fp.exists():
        return []
    raw = json.loads(fp.read_text(encoding="utf-8"))
    out = []
    for r in raw.get("records", []):
        try:
            dt = parse_rec_dt(r.get("datetime_utc", ""))
        except (ValueError, KeyError):
            continue
        if START_DT <= dt <= END_DT:
            r["_dt"] = dt
            out.append(r)
    return out


def load_mirova_universe():
    """Concatena CONS + OCR como universo MIROVA (independencia vs 128)."""
    parts = []
    for path, label in [(CSV_CONS, "CONS"), (CSV_OCR, "OCR")]:
        if not path.exists():
            continue
        df = pd.read_csv(path, low_memory=False)
        df["_source"] = label
        parts.append(df)
    df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    # Filtrar a alertas termicas en ventana
    df = df[df["Tipo_Registro"].astype(str).str.startswith("ALERTA_TERMICA")]
    df["_dt"] = df["Fecha_Satelite_UTC"].apply(parse_csv_dt)
    df = df[(df["_dt"] >= START_DT) & (df["_dt"] <= END_DT)]
    df = df[df["Volcan"].isin(VOLC_CSV_TO_DIR.keys())]
    df["_vol"] = df["Volcan"].map(VOLC_CSV_TO_DIR)
    df["VRP_MW"] = pd.to_numeric(df["VRP_MW"], errors="coerce").fillna(0.0)
    # De-dup: misma fecha+volcan+sensor puede aparecer en CONS y OCR
    df = df.drop_duplicates(subset=["_dt", "_vol", "Sensor"]).reset_index(drop=True)
    return df


def find_match(ref_dt, ref_sensor, recs):
    tol = timedelta(minutes=MATCH_TOL_MIN)
    best, best_delta = None, tol + timedelta(seconds=1)
    for r in recs:
        if not sensor_match(ref_sensor, r.get("sensor", "")):
            continue
        delta = abs(r["_dt"] - ref_dt)
        if delta <= tol and delta < best_delta:
            best, best_delta = r, delta
    return best


def audit_profile(profile_dir, mirova_df, label):
    by_vol = {v: {"refs": 0, "tps": 0, "fps": 0, "ratios": [],
                  "bug_count": 0, "path_d_only_high_count": 0}
              for v in VOLS}

    # Loop sobre alertas MIROVA → busca match
    for _, row in mirova_df.iterrows():
        vol = row["_vol"]
        by_vol[vol]["refs"] += 1
        recs = load_records(profile_dir, vol)
        rec = find_match(row["_dt"], row["Sensor"], recs)
        our_vrp = detection_vrp_canonical(rec, vol)
        if our_vrp > 0:
            by_vol[vol]["tps"] += 1
            mvrp = float(row["VRP_MW"])
            if mvrp > 0:
                by_vol[vol]["ratios"].append(our_vrp / mvrp)

    # Loop sobre records propios → FPs (records con eqVrp>0 sin match MIROVA)
    # y bug-counter D9.
    for vol in VOLS:
        recs = load_records(profile_dir, vol)
        sub = mirova_df[mirova_df["_vol"] == vol]
        for r in recs:
            vrp = detection_vrp_canonical(r, vol)
            # Bug D9 independiente
            if vrp > BUG_VRP_MIN and is_path_d_only(r):
                tbg = r.get("t_bg_k")
                if tbg is not None and float(tbg) < BUG_TBG_MAX:
                    by_vol[vol]["bug_count"] += 1
            if vrp > BUG_VRP_MIN and is_path_d_only(r):
                by_vol[vol]["path_d_only_high_count"] += 1
            # FP: VRP>0 pero ningun MIROVA del mismo sensor en ±60min
            if vrp > 0:
                tol = timedelta(minutes=MATCH_TOL_MIN)
                matched = False
                for _, row in sub.iterrows():
                    if not sensor_match(row["Sensor"], r.get("sensor", "")):
                        continue
                    if abs(row["_dt"] - r["_dt"]) <= tol:
                        matched = True
                        break
                if not matched:
                    by_vol[vol]["fps"] += 1

    # Compactar
    out = {"profile": label, "by_vol": {}, "global": {}}
    sum_bug = 0
    vols_ratio_ok = 0
    vols_recall_ok = 0
    vols_recall_total = 0
    vols_precision_ok = 0
    for vol, d in by_vol.items():
        rec_pct = d["tps"] / d["refs"] if d["refs"] else None
        prec = d["tps"] / (d["tps"] + d["fps"]) if (d["tps"] + d["fps"]) > 0 else None
        ratios_sorted = sorted(d["ratios"])
        ratio_med = ratios_sorted[len(ratios_sorted) // 2] if ratios_sorted else None
        out["by_vol"][vol] = {
            "refs": d["refs"], "tps": d["tps"], "fps": d["fps"],
            "fns": d["refs"] - d["tps"],
            "recall": rec_pct, "precision": prec,
            "ratio_med": ratio_med, "n_ratio": len(ratios_sorted),
            "bug_count": d["bug_count"],
            "path_d_only_high_count": d["path_d_only_high_count"],
        }
        sum_bug += d["bug_count"]
        if ratio_med is not None and RATIO_LO <= ratio_med <= RATIO_HI:
            vols_ratio_ok += 1
        if d["refs"] >= N_MIROVA_MIN_FOR_RECALL:
            vols_recall_total += 1
            if rec_pct is not None and rec_pct >= RECALL_MIN:
                vols_recall_ok += 1
        if prec is not None and prec >= PRECISION_MIN:
            vols_precision_ok += 1
    out["global"] = {
        "sum_bug": sum_bug,
        "vols_ratio_in_range": vols_ratio_ok,
        "vols_recall_ok": vols_recall_ok,
        "vols_recall_total": vols_recall_total,
        "vols_precision_ok": vols_precision_ok,
    }
    return out


def main():
    print(f"# R3 audit independiente Opcion C (S71 T1 F2.d)\n")
    print(f"Ventana: {START_DT.date()} -> {END_DT.date()}")
    print(f"Tolerancia matching: +/-{MATCH_TOL_MIN} min (128 usa +/-3h)")
    print(f"Universo MIROVA: CONS + OCR (128 usa solo CONS)")
    print(f"Ratio: pc.vrp_mw / mirova_vrp (sin fallback legacy)\n")

    mirova_df = load_mirova_universe()
    print(f"Total alertas MIROVA en ventana: {len(mirova_df)}")
    print(f"Por volcan: {mirova_df.groupby('_vol').size().to_dict()}\n")

    results = {}
    for label, prof_dir in PROFILES.items():
        if not prof_dir.exists():
            print(f"SKIP {label}: {prof_dir} no existe")
            continue
        print(f"Auditando {label}...")
        results[label] = audit_profile(prof_dir, mirova_df, label)

    # Print tabla per-vol
    print("\n## Tabla per-vol per-opcion\n")
    print("| Vol | Opt | refs | TP | FP | FN | recall | prec | ratio_med | n_ratio | bug |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for vol in VOLS:
        for opt in PROFILES:
            if opt not in results:
                continue
            d = results[opt]["by_vol"][vol]
            rec = f"{d['recall']:.2f}" if d["recall"] is not None else "-"
            prec = f"{d['precision']:.2f}" if d["precision"] is not None else "-"
            rmed = f"{d['ratio_med']:.2f}" if d["ratio_med"] is not None else "-"
            print(f"| {vol} | {opt} | {d['refs']} | {d['tps']} | {d['fps']} | {d['fns']} | {rec} | {prec} | {rmed} | {d['n_ratio']} | {d['bug_count']} |")

    # Resumen global
    print("\n## Cumplimiento criterios global\n")
    print("| Opcion | Vols ratio in [0.5,2] | Vols recall>=0.7 (n>=10) | Vols precision>=0.5 | Sum bug D9 |")
    print("|---|---:|---|---:|---:|")
    for opt, r in results.items():
        g = r["global"]
        print(f"| {opt} | {g['vols_ratio_in_range']}/11 | {g['vols_recall_ok']}/{g['vols_recall_total']} | {g['vols_precision_ok']}/11 | {g['sum_bug']} |")

    # Save JSON
    out_path = OUT_DIR / "audit_r3.json"
    out_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nJSON: {out_path}")


if __name__ == "__main__":
    main()
