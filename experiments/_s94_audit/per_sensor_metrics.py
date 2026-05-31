"""S94 — Re-análisis POR SENSOR con el loader corregido (PR #280, bug VIIRS750).

Contexto (§7 de docs/AUDIT_S93_artefactos_sobreestimacion.md):
  El loader `normalize_sensor` mapeaba mal la etiqueta CSV "VIIRS" (a secas =
  M-band 750m) → la bucketizaba como VIIRS375. Eso produjo el falso "MIROVA no
  usa VIIRS750" (0 alertas) en la tabla §6. PR #280 corrigió el loader. Hay que
  rehacer la tabla por-sensor con el bucketing correcto.

Computa, POR SENSOR (MODIS / VIIRS375 / VIIRS750), para los 11 Tier A, DOS vistas:

  A) CRUDO (match temporal ±60min, cualquier distancia, pc.vrp_mw>0):
     "¿vimos ALGO esa noche con ese sensor?" — recall de evento-noche.

  B) SUMMIT-GATED (frontend-equivalent): replica mirovaEqVrp + isThermalArtifact:
     una detección cuenta solo si distance_class=summit (dentro del inner_radius)
     y NO es artefacto térmico (cirrus / campo difuso). Es lo que el dashboard
     operacional muestra a Nicolás.

  Para cada vista: TP_ours (→ precisión), matched_mir (→ recall), ratio mediano.
  Recall restringido a la ventana de cobertura por volcán (min/max de nuestros
  records) — no penaliza fechas previas al pipeline.

  Además:
  - Split CONTEXTUAL-ONLY (diag_n_bt_path==0 ∧ diag_n_nti_path==0) de TP/FP por
    sensor — evalúa la seguridad de la co-validación path D (F3).
  - Deep-dive VIIRS750: distance_class de los FP + lista de alertas MIROVA no
    matcheadas (FN reales potenciales).

Match TEMPORAL por pasada (±60min), NO espacial — replica covalidation_impact.py
y computeMetrics() del frontend. §0.5: este script es la fuente de verdad; vuelca
JSON + imprime tablas. NO toca pipeline.
  python experiments/_s94_audit/per_sensor_metrics.py
"""
import sys, os, json, io
import datetime as dt
from statistics import median

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from pipeline.mirova_csv_loader import load_mirova_alertas

TIER_A = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan",
          "Llaima", "Chaiten", "PlanchonPeteroa", "Lastarria", "Isluga", "Tupungatito"]
INNER_KM = {"PuyehueCordonCaulle": 20, "Villarrica": 5, "Lascar": 5, "Copahue": 4,
            "NevadosDeChillan": 5, "Llaima": 5, "Chaiten": 5, "PlanchonPeteroa": 3,
            "Lastarria": 3, "Isluga": 5, "Tupungatito": 7}
CONS = os.path.join(REPO, "latest_consolidado.csv")
OCR = os.path.join(REPO, "data/mirova_reference/registro_vrp_ocr.csv")
BUCKETS = ["MODIS", "VIIRS375", "VIIRS750"]
WINDOW_S = 3600  # ±60 min = coincidencia de pasada


def our_bucket(s):
    """Convención del pipeline (A48): VIIRS_*_750=M-band; VIIRS_SNPP/NOAA*=I-band 375m."""
    s = str(s or "").upper()
    if "MODIS" in s:
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None


def parse(s):
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "").strip())
    except Exception:
        return None


def eq_vrp(r, inner):
    """Réplica de mirovaEqVrp(r, inner, includeFar=false) + isThermalArtifact.

    Devuelve el VRP "MIROVA-equivalente" que el dashboard muestra: 0 si la
    detección está fuera del inner_radius (far) o es artefacto térmico.
    """
    pc = r.get("primary_cluster") or {}
    vmw = pc.get("vrp_mw")
    if vmw is None:
        vfb = r.get("vrp_mw") or r.get("vrp_mir_mw") or 0
        return 0 if vfb > 50000 else vfb
    dc = r.get("distance_class")
    if dc and dc != "summit":
        return 0
    cd = pc.get("centroid_dist_km")
    if cd is not None and cd > inner:
        return 0
    base = 0 if (vmw or 0) > 50000 else (vmw or 0)
    # artefacto térmico (display-only S90/S93): cirrus o campo difuso
    tmax = r.get("t_max_k")
    npx = pc.get("n_pixels") or 0
    if base > 0 and tmax is not None:
        is_cirrus = (tmax < 273.15) and (base > 10)
        is_diffuse = (tmax < 278.15) and (npx >= 100) and (base >= 50) and ((base / npx) < 1.0)
        if is_cirrus or is_diffuse:
            return 0
    return base


def metrics(tp, n_ours, matched, n_mir, ratios):
    return {
        "N_ours": n_ours, "N_mir_in_coverage": n_mir, "TP_ours": tp, "matched_mir": matched,
        "precision": round(tp / n_ours, 4) if n_ours else None,
        "recall": round(matched / n_mir, 4) if n_mir else None,
        "ratio_median": round(median(ratios), 3) if ratios else None,
        "n_ratio_pairs": len(ratios),
    }


def main():
    bad_ts = {"ours": 0, "mir": 0}
    # acumuladores: vista 'raw' y 'summit'
    AGG = {view: {b: {"tp": 0, "n_ours": 0, "matched": 0, "n_mir": 0, "ratios": []}
                  for b in BUCKETS} for view in ("raw", "summit")}
    # contextual-only split (sobre la vista raw): tp/fp ctx-only por sensor
    CTX = {b: {"tp": 0, "tp_ctx": 0, "fp": 0, "fp_ctx": 0} for b in BUCKETS}
    # VIIRS750 deep-dive
    v750_fp_distclass = {}
    v750_fn = []  # alertas MIROVA VIIRS750 no matcheadas

    for vol in TIER_A:
        inner = INNER_KM[vol]
        d = json.load(open(os.path.join(REPO, f"data/mirova_equivalent/{vol}.json"), encoding="utf-8"))
        recs = d["records"] if isinstance(d, dict) and "records" in d else d

        ours_by_b = {b: [] for b in BUCKETS}  # list of dicts {t, vrp_raw, vrp_summit, ctx, dc}
        cov_times = []
        for r in recs:
            t = parse(r.get("datetime_utc"))
            if t is None:
                bad_ts["ours"] += 1
                continue
            cov_times.append(t)
            b = our_bucket(r.get("sensor"))
            if b is None:
                continue
            pc = r.get("primary_cluster") or {}
            vrp_raw = pc.get("vrp_mw") or 0
            vrp_sum = eq_vrp(r, inner)
            ctx = (r.get("diag_n_bt_path") == 0 and r.get("diag_n_nti_path") == 0)
            ours_by_b[b].append({"t": t, "raw": vrp_raw, "sum": vrp_sum, "ctx": ctx,
                                 "dc": r.get("distance_class")})
        if not cov_times:
            continue
        cov_min, cov_max = min(cov_times), max(cov_times)

        mir_by_b = {b: [] for b in BUCKETS}  # {t, vrp, dist, src}
        for a in load_mirova_alertas(CONS, OCR, volcano=vol):
            if (a.get("vrp_mw") or 0) <= 0:
                continue
            b = a.get("sensor_bucket")
            if b not in BUCKETS:
                continue
            t = parse(a.get("fecha_utc"))
            if t is None:
                bad_ts["mir"] += 1
                continue
            if not (cov_min <= t <= cov_max):
                continue
            mir_by_b[b].append({"t": t, "vrp": a.get("vrp_mw"), "dist": a.get("dist_km"),
                                "src": a.get("source")})

        for b in BUCKETS:
            ours = ours_by_b[b]
            mir = mir_by_b[b]
            for view, key in (("raw", "raw"), ("summit", "sum")):
                ag = AGG[view][b]
                # precisión: nuestras con vrp>0 que matchean ≥1 alerta
                tp = 0
                pos = [o for o in ours if o[key] > 0]
                ag["n_ours"] += len(pos)
                for o in pos:
                    hits = [m for m in mir if abs((o["t"] - m["t"]).total_seconds()) <= WINDOW_S]
                    if hits:
                        tp += 1
                        closest = min(mir, key=lambda m: abs((o["t"] - m["t"]).total_seconds()))
                        if closest["vrp"] and closest["vrp"] > 0:
                            ag["ratios"].append(o[key] / closest["vrp"])
                    elif view == "raw":
                        CTX[b]["fp"] += 1
                        if o["ctx"]:
                            CTX[b]["fp_ctx"] += 1
                        if b == "VIIRS750":
                            dc = o["dc"] or "none"
                            v750_fp_distclass[dc] = v750_fp_distclass.get(dc, 0) + 1
                    if hits and view == "raw":
                        CTX[b]["tp"] += 1
                        if o["ctx"]:
                            CTX[b]["tp_ctx"] += 1
                ag["tp"] += tp
                # recall: alertas que matchean ≥1 detección nuestra con vrp>0
                mm = 0
                for m in mir:
                    if any(abs((o["t"] - m["t"]).total_seconds()) <= WINDOW_S for o in pos):
                        mm += 1
                    elif view == "raw" and b == "VIIRS750":
                        v750_fn.append({"vol": vol, "t": m["t"].isoformat(), "vrp": m["vrp"],
                                        "dist": m["dist"], "src": m["src"]})
                ag["matched"] += mm
                ag["n_mir"] += len(mir)

    # --- resumen ---
    summary = {view: {b: metrics(AGG[view][b]["tp"], AGG[view][b]["n_ours"],
                                 AGG[view][b]["matched"], AGG[view][b]["n_mir"],
                                 AGG[view][b]["ratios"]) for b in BUCKETS}
               for view in ("raw", "summit")}

    out = {"window_min": WINDOW_S // 60, "universe": "CONS+OCR vrp>0, coverage-restricted",
           "bad_timestamps": bad_ts, "raw": summary["raw"], "summit_gated": summary["summit"],
           "ctx_only_split": CTX, "v750_fp_distance_class": v750_fp_distclass,
           "v750_fn_alerts": v750_fn}
    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "per_sensor_metrics.json")
    json.dump(out, open(outpath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    def print_table(title, view):
        print("=" * 92)
        print(title)
        print("=" * 92)
        print(f"{'Sensor':<11}{'N_ours':>8}{'N_mir(cov)':>12}{'TP_ours':>9}{'match_mir':>11}{'Precision':>11}{'Recall':>9}{'Ratio_med':>11}")
        for b in BUCKETS:
            s = summary[view][b]
            pr = f"{s['precision']*100:.1f}%" if s["precision"] is not None else "-"
            rc = f"{s['recall']*100:.1f}%" if s["recall"] is not None else "-"
            rt = f"{s['ratio_median']:.2f}x" if s["ratio_median"] is not None else "-"
            print(f"{b:<11}{s['N_ours']:>8}{s['N_mir_in_coverage']:>12}{s['TP_ours']:>9}{s['matched_mir']:>11}{pr:>11}{rc:>9}{rt:>11}")
        print()

    print_table("S94 — VISTA A: CRUDO (cualquier distancia, pc.vrp_mw>0). Universo CONS∪OCR, ±60min", "raw")
    print_table("S94 — VISTA B: SUMMIT-GATED (frontend mirovaEqVrp + isThermalArtifact)", "summit")

    print("=" * 92)
    print("CONTEXTUAL-ONLY split (vista CRUDO) — para evaluar co-validación path D (F3)")
    print("=" * 92)
    print(f"{'Sensor':<11}{'TP':>6}{'TP_ctx':>8}{'(=pierde)':>11}{'FP':>7}{'FP_ctx':>8}{'(=elimina)':>12}")
    for b in BUCKETS:
        c = CTX[b]
        tpp = f"{100*c['tp_ctx']/c['tp']:.0f}%" if c["tp"] else "-"
        fpp = f"{100*c['fp_ctx']/c['fp']:.0f}%" if c["fp"] else "-"
        print(f"{b:<11}{c['tp']:>6}{c['tp_ctx']:>8}{tpp:>11}{c['fp']:>7}{c['fp_ctx']:>8}{fpp:>12}")
    print()
    print("VIIRS750 deep-dive — distance_class de los FP (crudo):", v750_fp_distclass)
    print(f"VIIRS750 deep-dive — alertas MIROVA NO matcheadas (FN potenciales): {len(v750_fn)}")
    print("-" * 92)
    print(f"timestamps no parseables: ours={bad_ts['ours']} mir={bad_ts['mir']} (deben ser 0)")
    print(f"JSON → {outpath}")


if __name__ == "__main__":
    main()
