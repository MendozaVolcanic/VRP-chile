#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FICHA SDA — Deep-dive VIIRS375 (I-band) vs MIROVA, S114 (data fresca 2026-06-19).

POR QUE (fenomeno -> mecanismo -> numeros):
  VIIRS375 (I-band 375m) resuelve focos sub-pixel mas finos que VIIRS750/MODIS y es el
  sensor sano (paridad 99.1%). Este probe disecciona las 2 FN (Lastarria, NdC), cruza el
  universo MIROVA completo CONS+OCR (A11), filtra artefactos diurnos del OCR (A76 = pasada
  diurna cerca del mediodia solar refleja sol en nube -> NTI fantasma; perderlos es CORRECTO
  porque somos night-only), y mide la magnitud de la sobre-deteccion en RUTINA (A54/A68).

  Sensor mapping (A48): JSON sensor VIIRS_SNPP/NOAA20/NOAA21 -> VIIRS375 (I-band).
  Ground truth (A48): CSV Sensor "VIIRS375" = I-band ; "VIIRS" = VIIRS750 (M-band).
  Emparejado por-noche por fecha UTC (A67). pc.vrp_mw (A10), NO record.vrp_mw.
  Dia/noche (A76): Fecha_Captura_Chile es hora local (UTC-4). Diurno = hora local 10-15h.
"""
import csv, json, os, statistics
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CONS = os.path.join(HERE, "mirova_fresh", "cons.csv")
OCR  = os.path.join(HERE, "mirova_fresh", "ocr.csv")

WIN_START = "2026-05-01"
WIN_END   = "2026-06-30"
CAP = 50000

VOLS = {
    "Lascar": "Lascar", "Lastarria": "Lastarria", "Tupungatito": "Tupungatito",
    "PlanchonPeteroa": "PlanchonPeteroa", "NevadosDeChillan": "Nevados de Chillan",
    "Chaiten": "Chaiten", "Villarrica": "Villarrica", "Llaima": "Llaima",
    "Copahue": "Copahue", "Isluga": "Isluga", "PuyehueCordonCaulle": "Puyehue-Cordon Caulle",
}
CONS2JSON = {v: k for k, v in VOLS.items()}
INNER = {
    "Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3,
    "NevadosDeChillan": 5, "Chaiten": 5, "Villarrica": 5, "Llaima": 5,
    "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20,
}


def in_window(dt):
    return bool(dt) and WIN_START <= dt[:10] <= WIN_END


def is_viirs375_sensor(s):
    # CSV: "VIIRS375" only; "VIIRS" = VIIRS750
    return s == "VIIRS375"


def is_our_viirs375(s):
    s = s or ""
    if s.endswith("_750"):
        return False
    return s.startswith("VIIRS")


def local_hour(fecha_chile):
    """Hora local Chile (UTC-4) desde Fecha_Captura_Chile 'YYYY-MM-DD HH:MM:SS'."""
    if fecha_chile and len(fecha_chile) >= 13:
        try:
            return int(fecha_chile[11:13])
        except ValueError:
            return None
    return None


def is_daytime(hour):
    """A76: diurno = pasada cerca del mediodia solar (hora local 10-15h)."""
    return hour is not None and 10 <= hour <= 15


# ---------- 1. Cargar nuestros records VIIRS375 por (vol_cons, fecha) ----------
# our_recs[(vol_cons, date)] = list de dicts con diagnostico por record
our_recs = defaultdict(list)
for vjson, vcons in VOLS.items():
    path = os.path.join(ROOT, "data", "mirova_equivalent", vjson + ".json")
    d = json.load(open(path, encoding="utf-8"))
    inner = INNER[vjson]
    for rec in d["records"]:
        dt = rec.get("datetime_utc")
        if not in_window(dt):
            continue
        if not is_our_viirs375(rec.get("sensor", "")):
            continue
        pc = rec.get("primary_cluster") or {}
        vrp = pc.get("vrp_mw") or 0.0
        cdist = pc.get("centroid_dist_km")
        dclass = rec.get("distance_class")
        crater_ok = (0 < vrp <= CAP) and (cdist is not None and cdist <= inner)
        dash_ok = crater_ok and (not dclass or dclass == "summit")
        our_recs[(vcons, dt[:10])].append({
            "datetime_utc": dt, "sensor": rec.get("sensor"),
            "pc_vrp_mw": round(vrp, 4), "centroid_dist_km": round(cdist, 3) if cdist is not None else None,
            "distance_class": dclass, "crater_ok": crater_ok, "dash_ok": dash_ok,
            "final_hotspot_dist_km": rec.get("final_hotspot_dist_km"),
            "final_hotspot_source": rec.get("final_hotspot_source"),
            "nti_max": rec.get("nti_max"), "n_anom": rec.get("n_anomalous_pixels"),
        })


# ---------- 2. CONS: noches ALERTA VIIRS375 + RUTINA por vol ----------
# cons_alerta[(vol_cons, date)] = list de filas (vrp, dist, hora_local, daytime, dt_utc)
cons_alerta = defaultdict(list)
cons_rutina = defaultdict(list)
for vjson, vcons in VOLS.items():
    pass
with open(CONS, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        vol = r["Volcan"]
        if vol not in VOLS.values():
            continue
        dt = r["Fecha_Satelite_UTC"]
        if not in_window(dt):
            continue
        if not is_viirs375_sensor(r["Sensor"]):
            continue
        try:
            vrp = float(r["VRP_MW"])
        except (ValueError, TypeError):
            vrp = 0.0
        try:
            dist = float(r["Distancia_km"])
        except (ValueError, TypeError):
            dist = None
        h = local_hour(r["Fecha_Captura_Chile"])
        row = {"dt_utc": dt, "vrp": vrp, "dist": dist, "local_h": h,
               "daytime": is_daytime(h), "clas": r.get("Clasificacion Mirova")}
        if r["Tipo_Registro"] == "ALERTA_TERMICA":
            cons_alerta[(vol, dt[:10])].append(row)
        elif r["Tipo_Registro"] == "RUTINA":
            cons_rutina[(vol, dt[:10])].append(row)


# ---------- 3. Recall CONS + diagnostico FN ----------
fn_records = []
n_alerta_nights = 0
det_dash_nights = 0
# tambien: recall noche-noche EXCLUYENDO noches ALERTA puramente diurnas (A76)
n_alerta_nights_noct = 0
det_dash_nights_noct = 0
for (vol, date), rows in sorted(cons_alerta.items()):
    n_alerta_nights += 1
    o = our_recs.get((vol, date), [])
    detected = any(x["dash_ok"] for x in o)
    if detected:
        det_dash_nights += 1
    # nocturno: la noche tiene al menos una pasada MIROVA nocturna
    has_noct = any(not x["daytime"] for x in rows)
    if has_noct:
        n_alerta_nights_noct += 1
        if detected:
            det_dash_nights_noct += 1
    if not detected:
        # diagnostico de la FN
        max_row = max(rows, key=lambda x: x["vrp"])
        all_daytime = all(x["daytime"] for x in rows)
        diag = {
            "vol": vol, "date": date,
            "mirova_alerta_rows": rows,
            "mirova_max_vrp": round(max_row["vrp"], 4),
            "mirova_dist_km": max_row["dist"],
            "mirova_clas": max_row["clas"],
            "mirova_all_daytime": all_daytime,
            "our_records_count": len(o),
            "our_records": o,
        }
        # clasificar la causa
        if not o:
            cause = "no_record"  # no procesamos esa noche (sin pasada/sin fetch)
        else:
            any_crater = any(x["crater_ok"] for x in o)
            any_far = any(x["distance_class"] == "far" for x in o)
            has_pc0 = any((x["pc_vrp_mw"] == 0.0) for x in o)
            if any_crater and not detected:
                cause = "far_label_only"  # crater_ok pero dash bloqueo (distance_class far)
            elif any_far:
                cause = "distance_class_far"
            elif has_pc0:
                cause = "pc_vrp_zero"
            else:
                cause = "centroid_outside_inner_or_other"
        diag["cause"] = cause
        # interpretacion fisica
        if all_daytime:
            diag["interpretation"] = "diurna_A76 (perderla es CORRECTO, night-only)"
        elif max_row["vrp"] < 0.2:
            diag["interpretation"] = "sub-umbral A54 (Muy Bajo, foco sub-pixel debil)"
        else:
            diag["interpretation"] = "recuperable? revisar"
        fn_records.append(diag)


# ---------- 4. OCR: ALERTAS VIIRS375 que CONS no tiene (universo extra, A11) ----------
# Clasificar diurno/nocturno (A76). Solo cuentan como FN candidato las nocturnas no cubiertas.
cons_keys = set(cons_alerta.keys())  # (vol, date) ya en CONS ALERTA
ocr_alerta = defaultdict(list)
ocr_day = 0
ocr_night = 0
ocr_extra_night = []  # noches OCR VIIRS375 nocturnas que CONS no tiene como ALERTA
with open(OCR, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        vol = r["Volcan"]
        if vol not in VOLS.values():
            continue
        dt = r["Fecha_Satelite_UTC"]
        if not in_window(dt):
            continue
        if not is_viirs375_sensor(r["Sensor"]):
            continue
        # OCR ALERTA: incluye ALERTA_TERMICA_OCR y variantes; FALSO_POSITIVO_OCR no es ALERTA
        treg = r["Tipo_Registro"]
        if not treg.startswith("ALERTA"):
            continue
        h = local_hour(r["Fecha_Captura_Chile"])
        day = is_daytime(h)
        try:
            vrp = float(r["VRP_MW"])
        except (ValueError, TypeError):
            vrp = 0.0
        if day:
            ocr_day += 1
        else:
            ocr_night += 1
        ocr_alerta[(vol, dt[:10])].append({"dt_utc": dt, "vrp": vrp, "local_h": h, "daytime": day,
                                           "conf": r.get("Confianza_Validacion"), "clas": r.get("Clasificacion Mirova")})

# noches OCR nocturnas extra (no en CONS ALERTA) -> candidatos FN reales del universo ampliado
ocr_extra_night_detected = 0
ocr_extra_night_missed = 0
for (vol, date), rows in sorted(ocr_alerta.items()):
    has_noct = any(not x["daytime"] for x in rows)
    if not has_noct:
        continue
    if (vol, date) in cons_keys:
        continue  # ya contabilizado en CONS
    # esta noche aparece SOLO en OCR (nocturna). detectamos?
    o = our_recs.get((vol, date), [])
    detected = any(x["dash_ok"] for x in o)
    rec = {"vol": vol, "date": date, "detected": detected,
           "ocr_max_vrp": round(max(x["vrp"] for x in rows), 4),
           "n_rows_noct": sum(1 for x in rows if not x["daytime"])}
    if detected:
        ocr_extra_night_detected += 1
    else:
        ocr_extra_night_missed += 1
    ocr_extra_night.append(rec)


# ---------- 5. Sobre-deteccion en RUTINA (A54/A68) ----------
# Noches donde MIROVA reporta RUTINA VIIRS375 (no ALERTA) y nosotros reportamos summit pc.vrp>0
rutina_nights = 0
rutina_we_summit = 0
for (vol, date), rows in cons_rutina.items():
    # excluir noches que tambien son ALERTA (priorizar ALERTA)
    if (vol, date) in cons_alerta:
        continue
    rutina_nights += 1
    o = our_recs.get((vol, date), [])
    if any(x["dash_ok"] for x in o):
        rutina_we_summit += 1


# ---------- 6. Salida ----------
recall_cons = det_dash_nights / n_alerta_nights * 100 if n_alerta_nights else 0
recall_cons_noct = det_dash_nights_noct / n_alerta_nights_noct * 100 if n_alerta_nights_noct else 0
# recall CONS+OCR nocturno: denominador = noches CONS-noct + noches OCR-extra-noct
denom_union = n_alerta_nights_noct + len(ocr_extra_night)
num_union = det_dash_nights_noct + ocr_extra_night_detected
recall_union = num_union / denom_union * 100 if denom_union else 0

out = {
    "window": [WIN_START, WIN_END],
    "recall_cons_all_nights": {"det": det_dash_nights, "n": n_alerta_nights, "pct": round(recall_cons, 1)},
    "recall_cons_nocturnal_only": {"det": det_dash_nights_noct, "n": n_alerta_nights_noct, "pct": round(recall_cons_noct, 1)},
    "recall_cons_plus_ocr_nocturnal": {"det": num_union, "n": denom_union, "pct": round(recall_union, 1)},
    "fn_records": fn_records,
    "ocr_viirs375": {
        "alerta_rows_daytime_A76": ocr_day,
        "alerta_rows_nocturnal": ocr_night,
        "extra_nights_only_in_ocr_nocturnal": len(ocr_extra_night),
        "extra_nights_detected": ocr_extra_night_detected,
        "extra_nights_missed": ocr_extra_night_missed,
        "extra_nights_detail": ocr_extra_night,
    },
    "overdetection_rutina": {
        "rutina_only_nights": rutina_nights,
        "we_reported_summit": rutina_we_summit,
        "pct": round(rutina_we_summit / rutina_nights * 100, 1) if rutina_nights else 0,
    },
}
json.dump(out, open(os.path.join(HERE, "viirs375_deepdive.json"), "w", encoding="utf-8"), indent=1)

print("=== RECALL VIIRS375 (CONS) ===")
print("  all nights:      %d/%d = %.1f%%" % (det_dash_nights, n_alerta_nights, recall_cons))
print("  nocturnal only:  %d/%d = %.1f%%" % (det_dash_nights_noct, n_alerta_nights_noct, recall_cons_noct))
print("  CONS+OCR noct:   %d/%d = %.1f%%" % (num_union, denom_union, recall_union))
print()
print("=== 2 FN (CONS) ===")
for fn in fn_records:
    print("  %-20s %s  MIROVA max=%.3fMW dist=%s clas=%s  all_daytime=%s" % (
        fn["vol"], fn["date"], fn["mirova_max_vrp"], fn["mirova_dist_km"], fn["mirova_clas"], fn["mirova_all_daytime"]))
    print("     cause=%s  interp=%s  our_recs=%d" % (fn["cause"], fn["interpretation"], fn["our_records_count"]))
    for o in fn["our_records"]:
        print("       our: %s %s pc.vrp=%.4f cdist=%s class=%s crater_ok=%s dash_ok=%s fh_dist=%s fh_src=%s" % (
            o["datetime_utc"], o["sensor"], o["pc_vrp_mw"], o["centroid_dist_km"], o["distance_class"],
            o["crater_ok"], o["dash_ok"], o["final_hotspot_dist_km"], o["final_hotspot_source"]))
print()
print("=== OCR VIIRS375 (A11 universo + A76 diurno) ===")
print("  ALERTA rows daytime (A76 artefacto):", ocr_day)
print("  ALERTA rows nocturnal:", ocr_night)
print("  extra nights only-in-OCR nocturnal:", len(ocr_extra_night), "(detected=%d missed=%d)" % (ocr_extra_night_detected, ocr_extra_night_missed))
for e in ocr_extra_night:
    print("     %-20s %s detected=%s ocr_max=%.3f" % (e["vol"], e["date"], e["detected"], e["ocr_max_vrp"]))
print()
print("=== SOBRE-DETECCION RUTINA (A54/A68) ===")
print("  noches RUTINA-only VIIRS375: %d ; reportamos summit pc.vrp>0 en %d (%.1f%%)" % (
    rutina_nights, rutina_we_summit, rutina_we_summit / rutina_nights * 100 if rutina_nights else 0))
print()
print("WROTE viirs375_deepdive.json")
