#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S114 — Deep-dive PARIDAD VIIRS750 (M-band 750m) vs MIROVA, data fresca 2026-06-19.

POR QUE (fenomeno -> mecanismo -> numeros):
  VIIRS750 (M13, 4.05 um, pixel 750m) resuelve focos sub-pixel mas gruesos que VIIRS375.
  La re-auditoria S114 dio recall CRATER == DASHBOARD = 85.7% (60/70): NO hay brecha A46
  far->summit (det_crater == det_dash) -> las ~10 noches perdidas son FN GENUINAS, no un
  bug de coherencia. Esta sonda clasifica cada FN:
    (a) FN real sub-umbral: senal debil que 750m no resuelve; MIROVA integra ROI completo.
        Sintoma: NO tenemos record esa noche, o lo tenemos con pc.vrp=0 + nti_max plano (~-0.9).
    (b) recuperable: tenemos el cluster crateriano (pc.vrp>0, centroid<=inner) pero un gate
        (distance_class, cap) lo tira. Si det_crater==det_dash NO deberia haber ninguno.
    (c) MIROVA marginal: VRP_MW MIROVA muy bajo (<0.3 MW) -> el "FN" es ruido de borde.

  Tambien cruza OCR (A11: universo MIROVA = CONS+OCR; A76: artefacto diurno OCR no cuenta FN)
  y caracteriza los 2 far->summit VIIRS750 Tupungatito (cluster crateriano pero class=far).

Mapeo sensores (A48): VIIRS_*_750 -> VIIRS750. Emparejado por-noche (A67). pc.vrp_mw (A10).
Ventana 2026-05-01 .. 2026-06-30.
"""
import csv, json, os, statistics
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CONS = os.path.join(HERE, "mirova_fresh", "cons.csv")
OCR = os.path.join(HERE, "mirova_fresh", "ocr.csv")

WIN_START, WIN_END = "2026-05-01", "2026-06-30"
SENS = "VIIRS750"
CAP = 50000

VOLS = {"Lascar": "Lascar", "Lastarria": "Lastarria", "Tupungatito": "Tupungatito",
        "PlanchonPeteroa": "PlanchonPeteroa", "NevadosDeChillan": "Nevados de Chillan",
        "Chaiten": "Chaiten", "Villarrica": "Villarrica", "Llaima": "Llaima",
        "Copahue": "Copahue", "Isluga": "Isluga", "PuyehueCordonCaulle": "Puyehue-Cordon Caulle"}
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3,
         "NevadosDeChillan": 5, "Chaiten": 5, "Villarrica": 5, "Llaima": 5,
         "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}
CONS2JSON = {v: k for k, v in VOLS.items()}


def in_window(dt):
    return bool(dt) and WIN_START <= dt[:10] <= WIN_END


def is_v750_csv(s):
    return s == "VIIRS"  # en el CSV "VIIRS" = VIIRS750 (M-band); "VIIRS375" = I-band


# ---------- 1. MIROVA cons: ALERTAS VIIRS750 por (vol_json, date) ----------
# guardamos lista de (vrp, dist) por noche para reportar MAX VRP + dist
mir_cons = defaultdict(list)  # (vol_json, date) -> [(vrp, dist), ...]
with open(CONS, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["Volcan"] not in VOLS.values():
            continue
        if not is_v750_csv(r["Sensor"]):
            continue
        dt = r["Fecha_Satelite_UTC"]
        if not in_window(dt):
            continue
        if r["Tipo_Registro"] != "ALERTA_TERMICA":
            continue
        try:
            vrp = float(r["VRP_MW"])
        except (ValueError, TypeError):
            vrp = 0.0
        try:
            dist = float(r["Distancia_km"])
        except (ValueError, TypeError):
            dist = None
        mir_cons[(CONS2JSON[r["Volcan"]], dt[:10])].append((vrp, dist))

# ---------- 1b. MIROVA OCR: ALERTA_TERMICA_OCR VIIRS750 (A11) ----------
mir_ocr = defaultdict(list)  # (vol_json, date) -> [(vrp, dist, confianza, hora), ...]
with open(OCR, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["Volcan"] not in VOLS.values():
            continue
        if r["Sensor"] != "VIIRS":  # OCR usa "VIIRS" = 750 M-band tambien
            continue
        dt = r["Fecha_Satelite_UTC"]
        if not in_window(dt):
            continue
        if r["Tipo_Registro"] != "ALERTA_TERMICA_OCR":
            continue
        try:
            vrp = float(r["VRP_MW"])
        except (ValueError, TypeError):
            vrp = 0.0
        try:
            dist = float(r["Distancia_km"])
        except (ValueError, TypeError):
            dist = None
        hhmm = dt[11:16] if len(dt) >= 16 else ""
        mir_ocr[(CONS2JSON[r["Volcan"]], dt[:10])].append(
            (vrp, dist, r.get("Confianza_Validacion", ""), hhmm))


# ---------- 2. Nuestros records VIIRS750 indexados por (vol_json, date) ----------
ours = defaultdict(list)  # (vol_json, date) -> [rec_summary, ...]
far2summit = []
for vjson in VOLS:
    d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", vjson + ".json"), encoding="utf-8"))
    inner = INNER[vjson]
    for rec in d["records"]:
        if not str(rec.get("sensor", "")).endswith("_750"):
            continue
        dt = rec.get("datetime_utc")
        if not in_window(dt):
            continue
        pc = rec.get("primary_cluster") or {}
        vrp = pc.get("vrp_mw") or 0.0
        cdist = pc.get("centroid_dist_km")
        dclass = rec.get("distance_class")
        tmax, tbg = rec.get("t_max_k"), rec.get("t_bg_k")
        summ = {
            "datetime": dt, "sensor": rec.get("sensor"),
            "pc_vrp_mw": round(vrp, 4),
            "centroid_dist_km": round(cdist, 2) if cdist is not None else None,
            "distance_class": dclass,
            "nti_max": rec.get("nti_max"), "nti_bg": rec.get("nti_bg"),
            "t_max_k": tmax, "t_bg_k": tbg,
            "dT": round(tmax - tbg, 2) if (tmax is not None and tbg is not None) else None,
            "triggered_test1": rec.get("triggered_test1"),
            "n_anomalous_pixels": rec.get("n_anomalous_pixels"),
            "n_pixels_cluster": pc.get("n_pixels"),
            "final_hotspot_dist_km": rec.get("final_hotspot_dist_km"),
            "final_hotspot_source": rec.get("final_hotspot_source"),
            "n_2pass_recapture": rec.get("diag_n_second_pass_recapture"),
            "n_first_pass_pixels": rec.get("diag_n_first_pass_pixels"),
        }
        crater_ok = (0 < vrp <= CAP) and (cdist is not None and cdist <= inner)
        summ["crater_ok"] = crater_ok
        ours[(vjson, dt[:10])].append(summ)
        if crater_ok and dclass == "far":
            far2summit.append(dict(summ, vol=vjson))


# ---------- 3. Clasificar cada FN ----------
fns = []
recall_rows = []
for vjson in VOLS:
    alerta_dates = sorted({d for (v, d) in mir_cons if v == vjson})
    n_alerta = len(alerta_dates)
    det = 0
    miss = []
    for date in alerta_dates:
        cons_list = mir_cons[(vjson, date)]
        mir_vrp = max(v for v, _ in cons_list)
        mir_dist = next((dd for vv, dd in sorted(cons_list, reverse=True) if dd is not None), None)
        recs = ours.get((vjson, date), [])
        inner = INNER[vjson]
        crater_recs = [r for r in recs if r["crater_ok"]]
        det_crater = bool(crater_recs)
        det_dash = any(r["crater_ok"] and (not r["distance_class"] or r["distance_class"] == "summit") for r in recs)
        if det_dash:
            det += 1
            continue
        # ----- es FN. Clasificar -----
        # OCR mismo dia?
        ocr_list = mir_ocr.get((vjson, date), [])
        # categoria
        if mir_vrp < 0.3:
            cat = "c_mirova_marginal"
        elif det_crater and not det_dash:
            cat = "b_recuperable_gate"  # tenemos cluster crater pero etiquetado far
        else:
            # no tenemos cluster crater. ver si hay record VIIRS750 esa noche (sub-umbral)
            if recs:
                # tenemos pasada pero pc.vrp=0 o lejos -> sub-umbral
                cat = "a_subumbral_record_descartado"
            else:
                cat = "a_subumbral_sin_pasada"
        fn = {
            "vol": vjson, "date": date,
            "mirova_vrp_mw": round(mir_vrp, 3), "mirova_dist_km": mir_dist,
            "n_records_v750_esa_noche": len(recs),
            "our_records": recs,
            "ocr_mismo_dia": [{"vrp": o[0], "dist": o[1], "conf": o[2], "hora": o[3]} for o in ocr_list],
            "categoria": cat,
        }
        fns.append(fn)
        miss.append((date, round(mir_vrp, 3), cat))
    recall_rows.append({"vol": vjson, "n_alerta": n_alerta, "det_dash": det,
                        "recall_pct": round(det / n_alerta * 100, 1) if n_alerta else None,
                        "fn_dates": miss})


# ---------- 4. Recall CONS+OCR (A11): noche con ALERTA OCR cuenta como universo MIROVA ----------
# universo = noches con ALERTA cons O ALERTA ocr. detectada = det_dash nuestro.
agg_cons = {"n": 0, "det": 0}
agg_cons_ocr = {"n": 0, "det": 0}
for vjson in VOLS:
    cons_dates = {d for (v, d) in mir_cons if v == vjson}
    ocr_dates = {d for (v, d) in mir_ocr if v == vjson}
    inner = INNER[vjson]

    def detected(date):
        recs = ours.get((vjson, date), [])
        return any(r["crater_ok"] and (not r["distance_class"] or r["distance_class"] == "summit") for r in recs)

    for date in cons_dates:
        agg_cons["n"] += 1
        if detected(date):
            agg_cons["det"] += 1
    for date in (cons_dates | ocr_dates):
        agg_cons_ocr["n"] += 1
        if detected(date):
            agg_cons_ocr["det"] += 1


# ---------- 5. Salida ----------
print("=" * 78)
print("VIIRS750 DEEP-DIVE S114 — cons+ocr fresco 2026-06-19  | ventana", WIN_START, "..", WIN_END)
print("=" * 78)
print()
print(">>> RECALL VIIRS750 (dashboard gate) <<<")
print("  CONS    : %.1f%% (%d/%d)" % (agg_cons["det"] / agg_cons["n"] * 100, agg_cons["det"], agg_cons["n"]))
print("  CONS+OCR: %.1f%% (%d/%d)" % (agg_cons_ocr["det"] / agg_cons_ocr["n"] * 100, agg_cons_ocr["det"], agg_cons_ocr["n"]))
print()
print(">>> FN por VOL <<<")
for r in recall_rows:
    if r["n_alerta"] == 0:
        continue
    fnstr = "; ".join("%s(%.2fMW,%s)" % (d, v, c.split("_")[0]) for d, v, c in r["fn_dates"]) or "—"
    print("  %-18s alerta=%2d det=%2d recall=%5s%%  FN: %s" % (
        r["vol"], r["n_alerta"], r["det_dash"], r["recall_pct"], fnstr))
print()
catc = defaultdict(int)
for fn in fns:
    catc[fn["categoria"]] += 1
print(">>> CLASIFICACION FN (total %d) <<<" % len(fns))
for c, n in sorted(catc.items()):
    print("  %-32s %d" % (c, n))
print()
print(">>> DETALLE cada FN <<<")
for fn in fns:
    print("  %-16s %s  MIROVA=%.3fMW @%.2fkm  cat=%s  n_rec=%d  OCR=%d" % (
        fn["vol"], fn["date"], fn["mirova_vrp_mw"],
        fn["mirova_dist_km"] if fn["mirova_dist_km"] is not None else -1,
        fn["categoria"], fn["n_records_v750_esa_noche"], len(fn["ocr_mismo_dia"])))
    for r in fn["our_records"]:
        print("      rec %s  pc.vrp=%.3f centroid=%s class=%s nti_max=%s dT=%s trig1=%s n_anom=%s" % (
            r["datetime"][11:], r["pc_vrp_mw"], r["centroid_dist_km"], r["distance_class"],
            r["nti_max"], r["dT"], r["triggered_test1"], r["n_anomalous_pixels"]))
    for o in fn["ocr_mismo_dia"]:
        print("      OCR vrp=%.3f dist=%s conf=%s hora=%s" % (o["vrp"], o["dist"], o["conf"], o["hora"]))
print()
print(">>> FAR->SUMMIT VIIRS750 (cluster crateriano real, distance_class=far) <<<")
print("  total:", len(far2summit))
for x in far2summit:
    print("  %-16s %s  pc.vrp=%.3f centroid=%.2fkm class=%s" % (
        x["vol"], x["datetime"], x["pc_vrp_mw"], x["centroid_dist_km"], x["distance_class"]))
    print("      final_hotspot dist=%s src=%s | nti_max=%s nti_bg=%s dT=%s (t_max=%s t_bg=%s)" % (
        x["final_hotspot_dist_km"], x["final_hotspot_source"], x["nti_max"], x["nti_bg"],
        x["dT"], x["t_max_k"], x["t_bg_k"]))
    print("      triggered_test1=%s n_anom=%s n_2pass_recapture=%s n_first_pass=%s n_pixels_cluster=%s" % (
        x["triggered_test1"], x["n_anomalous_pixels"], x["n_2pass_recapture"],
        x["n_first_pass_pixels"], x["n_pixels_cluster"]))

out = {
    "ventana": [WIN_START, WIN_END],
    "recall_cons": agg_cons, "recall_cons_ocr": agg_cons_ocr,
    "recall_rows": recall_rows,
    "fn_classification_counts": dict(catc),
    "fns": fns,
    "far2summit_v750": far2summit,
}
json.dump(out, open(os.path.join(HERE, "viirs750_deepdive.json"), "w", encoding="utf-8"), indent=1)
print()
print("WROTE viirs750_deepdive.json")
