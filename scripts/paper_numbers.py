# -*- coding: utf-8 -*-
"""paper_numbers.py — TODOS los números del manuscrito, recalculados desde la data.

POR QUÉ EXISTE
==============
El borrador del paper (`docs/PAPER_VRP_CHILE_DRAFT_S72.md`) cita números de S119 (julio
2026). Desde entonces cambiaron nadir-fijo, la máscara de nube (D14), el piso VRP (S130), la
magnitud del operador en VIIRS 375 (F5', S132) y se abrió D19. Cada sesión de pipeline
invalida el texto si los números viven en el texto. Acá viven en un script: el texto lleva
placeholders `[NUM: clave]` y las tablas se regeneran con `python scripts/paper_numbers.py`.
Regla S91: ningún número del paper se transcribe a mano.

QUÉ PRODUCE
===========
  docs/paper/numbers.json   — todas las claves, con la DEFINICIÓN dentro (A90: sin
                              denominador y ventana, un número no es una afirmación)
  docs/paper/TABLAS.md      — Tablas 2, 3 y 4 del borrador en markdown, con cabecera de
                              definiciones, listas para pegar.

DEFINICIONES (heredadas de las auditorías, citadas por script de origen)
======================================================================
Tier A       = los 11 volcanes con radius_km = 25 en volcanoes.yaml (S14).
Bucket       = MODIS (MODIS_*), VIIRS750 (VIIRS_*_750), VIIRS375 (VIIRS_* sin sufijo). A48.
Ventana      = --desde .. --hasta (default 2026-01-01 .. último record), por datetime_utc.
Ventana GT   = toda comparación contra MIROVA (recall, pares, «noches sin alerta») se recorta
               además a la última fecha PRESENTE en el CSV de referencia. Sin ese recorte, los
               días posteriores al ground truth cuentan como «detectamos y MIROVA no», que es
               falso: MIROVA no fue observada. El JSON publica `ventana_ground_truth`.
Noche ALERTA = (volcán, bucket, fecha UTC) con ≥1 fila ALERTA_TERMICA/ALERTA_TERMICA_OCR
               en CONS ∪ OCR (loader canónico A11; nocturna 03-09 UTC según el loader).
               Origen: experiments/_s119_audit/eje2_recall_magnitud.py.
Record CRÁTER  = pc.vrp_mw > 0 y pc.vrp_mw ≤ 50 000 y pc.centroid_dist_km ≤ inner_radius_km.
Record DASHBOARD = CRÁTER y distance_class ∈ {summit, None}. (S119/S114.)
Recall       = noches ALERTA con ≥1 record DASHBOARD del mismo (volcán, bucket, fecha) /
               noches ALERTA. Se reporta también con CRÁTER (detección sin la etiqueta A46).
Par por pasada = record DASHBOARD × fila ALERTA del mismo bucket con |Δt| ≤ 20 min y
               VRP_MW > 0; si hay varias, la más cercana. Origen:
               experiments/_s131_audit/magnitud/03_pares_por_pasada.py.
Magnitud nuestra = f5_core_vrp_mw si bucket VIIRS375 y el campo existe (lo que el operador
               ve, S132, A10 matiz), si no pc.vrp_mw.
Razón        = mediana de (nuestra / MIROVA) sobre los pares; IQR; n pares.
Sin alerta   = noches con record DASHBOARD y sin noche ALERTA. NO se rotulan «falsos
               positivos»: A54 (95 % son anomalías físicamente reales o fallas del cruce).

Read-only sobre data/. Encoding UTF-8 forzado (Windows).
"""
import argparse
import io
import json
import os
import statistics as st
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
import yaml  # noqa: E402

from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402

SNAP = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot")
CONS = os.path.join(SNAP, "registro_vrp_consolidado.csv")
OCR = os.path.join(SNAP, "registro_vrp_ocr.csv")
DATA = os.path.join(ROOT, "data", "mirova_equivalent")
OUT_DIR = os.path.join(ROOT, "docs", "paper")
BUCKETS = ("MODIS", "VIIRS750", "VIIRS375")
# El snapshot que lee el cargador canónico puede quedar atrás del CSV que el workflow
# `sync-mirova-csv.yml` refresca cada hora en la raíz del repo (canal partido, familia A17).
# Acá NO se elige archivo: se mide la última fecha realmente presente y se recorta con ella.
CAP_MW = 50000.0
PAR_DT_MIN = 20


def bucket_of(sensor: str):
    if sensor.startswith("MODIS"):
        return "MODIS"
    if sensor.endswith("_750"):
        return "VIIRS750"
    if sensor.startswith("VIIRS"):
        return "VIIRS375"
    return None


def load_volcanoes():
    cfg = yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))
    vols = [v for v in cfg["volcanoes"] if v.get("active", True)]
    tier_a = [v for v in vols if v.get("radius_km") == 25]
    return vols, tier_a


def load_records(vol_name):
    p = os.path.join(DATA, f"{vol_name}.json")
    if not os.path.exists(p):
        return []
    return json.load(open(p, encoding="utf-8"))["records"]


def magnitud_operador(rec, bucket):
    pc = rec.get("primary_cluster") or {}
    if bucket == "VIIRS375" and rec.get("f5_core_vrp_mw") is not None:
        return float(rec["f5_core_vrp_mw"]), "f5_core_vrp_mw"
    return float(pc.get("vrp_mw") or 0.0), "pc.vrp_mw"


def es_crater(rec, inner):
    pc = rec.get("primary_cluster") or {}
    vrp = pc.get("vrp_mw") or 0.0
    cd = pc.get("centroid_dist_km")
    return (0 < vrp <= CAP_MW) and (cd is not None and inner is not None and cd <= inner)


def es_dashboard(rec, inner):
    dc = rec.get("distance_class")
    return es_crater(rec, inner) and (not dc or dc == "summit")


def parse_dt(s):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except (ValueError, TypeError):
            pass
    return None


def git_head():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                                       text=True).strip()
    except Exception:
        return None


def tabla2(tier_a, desde, hasta):
    filas = []
    for v in tier_a:
        recs = [r for r in load_records(v["name"]) if desde <= r["datetime_utc"][:10] <= hasta]
        por_bucket = defaultdict(int)
        for r in recs:
            b = bucket_of(r.get("sensor", ""))
            if b:
                por_bucket[b] += 1
        fechas = sorted(r["datetime_utc"] for r in recs)
        filas.append({
            "volcano": v["name"], "display_name": v.get("display_name", v["name"]),
            "vent_lat": v.get("vent_lat"), "vent_lon": v.get("vent_lon"),
            "mirova_center_lat": v.get("mirova_center_lat"),
            "mirova_center_lon": v.get("mirova_center_lon"),
            "radius_km": v.get("radius_km"), "inner_radius_km": v.get("inner_radius_km"),
            "n_records": len(recs), "n_por_bucket": dict(por_bucket),
            "primer_record": fechas[0] if fechas else None,
            "ultimo_record": fechas[-1] if fechas else None,
        })
    return filas


def tabla3():
    """Coeficientes Wooster efectivos en el código + validación empírica OSF v2.5 (S14)."""
    import pipeline.process_modis as pm
    import pipeline.process_viirs as pv
    import pipeline.process_viirs_mod as pvm
    calib = json.load(open(os.path.join(ROOT, "experiments", "21_results.json"), encoding="utf-8"))
    res = calib["results"]

    def coef(mod):
        return {k: getattr(mod, k) for k in dir(mod) if "WOOSTER" in k and isinstance(getattr(mod, k), (int, float))}

    return {
        "fuente_validacion": "experiments/21_results.json (S14, OSF v2.5, n_rows_total=%d)" % calib["n_rows_total"],
        "generated_utc_validacion": calib["generated_utc"],
        "sensores": {
            "MODIS_1000m": {"coef_codigo": coef(pm), **{k: res["MODIS_1000m"][k] for k in ("n", "matched_formula", "matched_value", "matched_error_pct", "a_pix_mode")}},
            "VIIRS_750m": {"coef_codigo": coef(pvm), **{k: res["VIIRS_750m"][k] for k in ("n", "matched_formula", "matched_value", "matched_error_pct", "a_pix_mode")}},
            "VIIRS_375m": {"coef_codigo": coef(pv), **{k: res["VIIRS_375m"][k] for k in ("n", "matched_formula", "matched_value", "matched_error_pct", "a_pix_mode")}},
        },
    }


def fin_ground_truth(alertas):
    """Última fecha UTC con una fila de MIROVA. Más allá no hay con qué comparar."""
    f = [a["fecha_utc"][:10] for a in alertas if a.get("fecha_utc")]
    return max(f) if f else None


def tabla4(tier_a, desde, hasta):
    alertas = load_mirova_alertas(cons_path=CONS, ocr_path=OCR)
    fin_gt = fin_ground_truth(alertas)
    if fin_gt and fin_gt < hasta:
        hasta = fin_gt   # recorte: sin ground truth no hay comparación posible
    inner = {v["name"]: v.get("inner_radius_km") for v in tier_a}
    # MIROVA: noches ALERTA y filas por (vol, bucket)
    noches = defaultdict(set)
    filas_mir = defaultdict(list)
    for a in alertas:
        f = a.get("fecha_utc") or ""
        if not f or not (desde <= f[:10] <= hasta) or a["sensor_bucket"] not in BUCKETS:
            continue
        if a["volcano"] not in inner:
            continue
        noches[(a["volcano"], a["sensor_bucket"])].add(f[:10])
        dt = parse_dt(f)
        if dt and (a.get("vrp_mw") or 0) > 0:
            filas_mir[(a["volcano"], a["sensor_bucket"])].append((dt, float(a["vrp_mw"])))
    out = {}
    for v in tier_a:
        name = v["name"]
        recs = [r for r in load_records(name) if desde <= r["datetime_utc"][:10] <= hasta]
        for b in BUCKETS:
            rb = [r for r in recs if bucket_of(r.get("sensor", "")) == b]
            noches_crater = {r["datetime_utc"][:10] for r in rb if es_crater(r, inner[name])}
            noches_dash = {r["datetime_utc"][:10] for r in rb if es_dashboard(r, inner[name])}
            nm = noches.get((name, b), set())
            tp_d = len(nm & noches_dash)
            tp_c = len(nm & noches_crater)
            # pares por pasada
            mir_rows = sorted(filas_mir.get((name, b), []))
            razones, fuente_mag = [], defaultdict(int)
            for r in rb:
                if not es_dashboard(r, inner[name]):
                    continue
                dt = parse_dt(r["datetime_utc"])
                if dt is None:
                    continue
                cand = [(abs((m[0] - dt).total_seconds()), m[1]) for m in mir_rows
                        if abs((m[0] - dt).total_seconds()) <= PAR_DT_MIN * 60]
                if not cand:
                    continue
                _, mvrp = min(cand)
                ours, src = magnitud_operador(r, b)
                if ours > 0 and mvrp > 0:
                    razones.append(ours / mvrp)
                    fuente_mag[src] += 1
            q = sorted(razones)

            def pct(p):
                if not q:
                    return None
                k = (len(q) - 1) * p
                lo, hi = int(k), min(int(k) + 1, len(q) - 1)
                return round(q[lo] + (q[hi] - q[lo]) * (k - lo), 3)

            out[f"{name}|{b}"] = {
                "volcano": name, "bucket": b, "n_records": len(rb),
                "noches_alerta_mirova": len(nm),
                "tp_dashboard": tp_d, "tp_crater": tp_c,
                "recall_dashboard": round(tp_d / len(nm), 3) if nm else None,
                "recall_crater": round(tp_c / len(nm), 3) if nm else None,
                "noches_dashboard_sin_alerta": len(noches_dash - nm),
                "n_noches_dashboard": len(noches_dash),
                "pares_pasada": len(razones),
                "razon_mediana": round(st.median(razones), 3) if razones else None,
                "razon_q25": pct(0.25), "razon_q75": pct(0.75),
                "fuente_magnitud": dict(fuente_mag),
            }
    out["_ventana_ground_truth"] = {"desde": desde, "hasta": hasta,
                                    "fin_csv_mirova": fin_gt,
                                    "nota": "recall, pares y «noches sin alerta» se calculan sólo acá"}
    return out


def agregados(t4):
    agg = {}
    for b in BUCKETS:
        filas = [x for x in t4.values() if isinstance(x, dict) and x.get("bucket") == b]
        nm = sum(x["noches_alerta_mirova"] for x in filas)
        tpd = sum(x["tp_dashboard"] for x in filas)
        tpc = sum(x["tp_crater"] for x in filas)
        agg[b] = {"noches_alerta_mirova": nm, "tp_dashboard": tpd, "tp_crater": tpc,
                  "recall_dashboard": round(tpd / nm, 3) if nm else None,
                  "recall_crater": round(tpc / nm, 3) if nm else None,
                  "volcanes_con_razon": sum(1 for x in filas if x["razon_mediana"] is not None),
                  "volcanes_en_banda_0_5_2_0": sum(1 for x in filas if x["razon_mediana"] is not None and 0.5 <= x["razon_mediana"] <= 2.0)}
    return agg


def md_tablas(num):
    L = []
    L.append("# Tablas del manuscrito — generadas por `scripts/paper_numbers.py`\n")
    gt = num["ventana_ground_truth"]
    L.append(f"> Generado {num['generated_utc']} · HEAD `{num['git_head']}` · ventana de records {num['ventana']['desde']} → {num['ventana']['hasta']}.\n"
             f"> **Comparación contra MIROVA recortada a {gt['desde']} → {gt['hasta']}** (última fila del CSV de referencia: {gt['fin_csv_mirova']}); "
             f"más allá no hay ground truth y una noche nuestra no puede contarse como «sin alerta». "
             f"Ground truth CONS ∪ OCR (cargador canónico). **No editar a mano: regenerar.**\n")
    L.append("Definiciones: ver docstring del script y `numbers.json` → `definiciones`.\n")
    L.append("\n## Table 2 — Tier A volcanoes\n")
    L.append("| Volcano | Vent (lat, lon) | MIROVA grid centre (lat, lon) | R (km) | inner (km) | n records | MODIS / V750 / V375 | first | last |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for f in num["tabla2"]:
        nb = f["n_por_bucket"]
        L.append(f"| {f['display_name']} | {f['vent_lat']}, {f['vent_lon']} | {f['mirova_center_lat']}, {f['mirova_center_lon']} | {f['radius_km']} | {f['inner_radius_km']} | {f['n_records']} | "
                 f"{nb.get('MODIS', 0)} / {nb.get('VIIRS750', 0)} / {nb.get('VIIRS375', 0)} | {f['primer_record']} | {f['ultimo_record']} |")
    L.append("\n## Table 3 — MIR radiative power coefficients (Wooster) and OSF v2.5 validation\n")
    L.append(f"Validation source: {num['tabla3']['fuente_validacion']}.\n")
    L.append("| Sensor | k in code | matched formula (OSF v2.5) | k matched | n rows | median error (%) | A_pix mode |")
    L.append("|---|---|---|---|---|---|---|")
    for s, d in num["tabla3"]["sensores"].items():
        L.append(f"| {s} | {d['coef_codigo']} | {d['matched_formula']} | {d['matched_value']:.0f} | {d['n']} | {d['matched_error_pct']:.3g} | {d['a_pix_mode']} |")
    L.append("\n## Table 4 — Validation against MIROVA NRT per volcano and sensor\n")
    L.append("Recall = MIROVA alert nights recovered by a dashboard-valid record (same volcano, sensor bucket, UTC date). "
             "Ratio = median ours/MIROVA over pass-level pairs (|Δt| ≤ 20 min). «no alert» nights are NOT false positives (A54).\n")
    L.append("| Volcano | Sensor | n records | MIROVA alert nights | recall (dashboard) | recall (crater) | dashboard nights w/o alert | pairs | ratio median [IQR] |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for k, x in num["tabla4"].items():
        if k.startswith("_"):
            continue
        rz = f"{x['razon_mediana']} [{x['razon_q25']}–{x['razon_q75']}]" if x["razon_mediana"] is not None else "—"
        L.append(f"| {x['volcano']} | {x['bucket']} | {x['n_records']} | {x['noches_alerta_mirova']} | {x['recall_dashboard']} | {x['recall_crater']} | {x['noches_dashboard_sin_alerta']}/{x['n_noches_dashboard']} | {x['pares_pasada']} | {rz} |")
    L.append("\n### Aggregate by sensor\n")
    L.append("| Sensor | MIROVA alert nights | recall (dashboard) | recall (crater) | volcanoes with ratio | in band [0.5, 2.0] |")
    L.append("|---|---|---|---|---|---|")
    for b, a in num["agregados"].items():
        L.append(f"| {b} | {a['noches_alerta_mirova']} | {a['recall_dashboard']} | {a['recall_crater']} | {a['volcanes_con_razon']} | {a['volcanes_en_banda_0_5_2_0']} |")
    return "\n".join(L) + "\n"


def main():
    if hasattr(sys.stdout, "buffer"):  # sólo como script: al importarlo desde pytest no se toca
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="2026-01-01")
    ap.add_argument("--hasta", default=None, help="default: último record en data/")
    ap.add_argument("--out", default=OUT_DIR)
    ap.add_argument("--tests", action="store_true",
                    help="cuenta los tests recolectados por pytest (clave n_tests_collected; ~10 s)")
    args = ap.parse_args()
    vols, tier_a = load_volcanoes()
    hasta = args.hasta
    if hasta is None:
        ult = [r["datetime_utc"] for v in tier_a for r in load_records(v["name"])]
        hasta = max(ult)[:10] if ult else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    num = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "git_head": git_head(),
        "ventana": {"desde": args.desde, "hasta": hasta},
        "definiciones": __doc__.split("DEFINICIONES")[1].split("Read-only")[0].strip(),
        "n_volcanes_configurados": len(vols),
        "n_tier_a": len(tier_a),
        "tier_a": [v["name"] for v in tier_a],
        "tabla2": tabla2(tier_a, args.desde, hasta),
        "tabla3": tabla3(),
    }
    num["tabla4"] = tabla4(tier_a, args.desde, hasta)
    num["ventana_ground_truth"] = num["tabla4"].pop("_ventana_ground_truth")
    num["agregados"] = agregados(num["tabla4"])
    num["n_records_tier_a_ventana"] = sum(f["n_records"] for f in num["tabla2"])
    if args.tests:
        try:
            out = subprocess.check_output([sys.executable, "-m", "pytest", "tests", "-q", "--collect-only",
                                           "-p", "no:cacheprovider"], cwd=ROOT, text=True, stderr=subprocess.STDOUT)
            ult = [l for l in out.splitlines() if "test" in l and ("collected" in l or "selected" in l)]
            num["n_tests_collected"] = int(ult[-1].split()[0]) if ult else None
            num["n_tests_definicion"] = "pytest tests --collect-only (tests recolectados, no ejecutados)"
        except Exception as e:  # noqa: BLE001
            num["n_tests_collected"] = None
            num["n_tests_error"] = str(e)[:200]
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "numbers.json"), "w", encoding="utf-8") as fh:
        json.dump(num, fh, indent=1, ensure_ascii=False)
    with open(os.path.join(args.out, "TABLAS.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md_tablas(num))
    print(f"ventana {args.desde} → {hasta} · HEAD {num['git_head']} · Tier A {len(tier_a)}/{len(vols)} · "
          f"records {num['n_records_tier_a_ventana']}")
    for b, a in num["agregados"].items():
        print(f"  {b:9s} noches ALERTA {a['noches_alerta_mirova']:4d} · recall dashboard {a['recall_dashboard']} · "
              f"crater {a['recall_crater']} · en banda {a['volcanes_en_banda_0_5_2_0']}/{a['volcanes_con_razon']}")
    print(f"→ {os.path.join(args.out, 'numbers.json')}\n→ {os.path.join(args.out, 'TABLAS.md')}")


if __name__ == "__main__":
    main()
