# -*- coding: utf-8 -*-
"""S134 F3 - ¿MIROVA publico las noches de cada clase de record?

Clases (VIIRS375, summit, magnitud publicada > 0, desde DESDE):
  T1  = final_hotspot_source test1_roi           (pico del Test 1, keep_peak)
  CFP = ctx_cluster con diag_n_first_pass_pixels>0 (Tests 2^3 genuinos)
  CSP = ctx_cluster con n_fp=0 y n_second_pass_recapture>0 (recaptura sin primer pase)
Referencia: CONS u OCR del scraper Mirova-v1 (A11), Sensor VIIRS375, VRP_MW>0, |dt|<=20 min.
Nombres del CSV verificados con Counter (A14). Instrumento: si el matcher estuviera muerto,
CFP de Lascar (control positivo) saldria ~0; se reporta.
"""
import io, json, math, os, sys, csv, datetime as dt
from collections import Counter, defaultdict
import yaml
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ROOT = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
DESDE = "2026-06-01"
CSVS = [os.path.join(WT, "latest_consolidado.csv"),
        os.path.join(ROOT, "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv")]
ALIAS = {"Villarrica": {"Villarrica"}, "Lascar": {"Lascar", "Láscar"}, "Llaima": {"Llaima"},
         "Tupungatito": {"Tupungatito"}, "Chaiten": {"Chaiten", "Chaitén"}, "Copahue": {"Copahue"},
         "Isluga": {"Isluga"}, "Lastarria": {"Lastarria"}, "NevadosDeChillan": {"Nevados de Chillan", "Nevados de Chillán", "NevadosDeChillan"},
         "PlanchonPeteroa": {"PlanchonPeteroa", "Planchon-Peteroa", "Planchón-Peteroa"},
         "PuyehueCordonCaulle": {"Puyehue-Cordon Caulle", "PuyehueCordonCaulle", "Puyehue-Cordón Caulle"}}

ref = defaultdict(list); sensores = Counter(); nombres = Counter()
for p in CSVS:
    for row in csv.DictReader(io.open(p, encoding="utf-8")):
        nombres[row["Volcan"]] += 1; sensores[row["Sensor"]] += 1
        if row["Sensor"] != "VIIRS375": continue
        try:
            v = float(row["VRP_MW"] or 0)
        except ValueError:
            continue
        if v <= 0: continue
        ts = dt.datetime.strptime(row["Fecha_Satelite_UTC"], "%Y-%m-%d %H:%M:%S")
        ref[row["Volcan"]].append(ts)
print("sensores CSV:", dict(sensores))
print("volcanes CSV (top):", nombres.most_common(14))

def match(vol, when):
    t = dt.datetime.strptime(when[:16], "%Y-%m-%d %H:%M")
    for a in ALIAS[vol]:
        for r in ref.get(a, []):
            if abs((r - t).total_seconds()) <= 20 * 60:
                return True
    return False

out = {}
print("\n%-20s | %-22s | %-22s | %-22s" % ("volcan", "T1 test1_roi n mirova%", "CFP ctx+firstpass", "CSP ctx solo 2do pase"))
for vol in ALIAS:
    d = json.load(io.open(os.path.join(ROOT, "data/mirova_equivalent", vol + ".json"), encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    cl = defaultdict(lambda: [0, 0])
    for r in recs:
        if str(r.get("datetime_utc", ""))[:10] < DESDE: continue
        s = r.get("sensor", "")
        if not (s.startswith("VIIRS") and not s.endswith("_750")): continue
        if r.get("distance_class") != "summit": continue
        pc = r.get("primary_cluster") or {}
        m = r.get("f5_core_vrp_mw"); m = pc.get("vrp_mw") if m is None else m
        if not m or m <= 0: continue
        src = r.get("final_hotspot_source")
        if src == "test1_roi": k = "T1"
        elif src == "ctx_cluster" and (r.get("diag_n_first_pass_pixels") or 0) > 0: k = "CFP"
        elif src == "ctx_cluster" and (r.get("diag_n_second_pass_recapture") or 0) > 0: k = "CSP"
        else: k = "otro"
        cl[k][0] += 1
        cl[k][1] += match(vol, r["datetime_utc"])
    f = lambda k: "%3d  %5.1f%%" % (cl[k][0], 100 * cl[k][1] / cl[k][0]) if cl[k][0] else "  -      -"
    print("%-20s | %-22s | %-22s | %-22s" % (vol, f("T1"), f("CFP"), f("CSP")))
    out[vol] = {k: {"n": v[0], "n_mirova": v[1]} for k, v in cl.items()}
json.dump(out, io.open(os.path.join(HERE, "cruce_mirova_por_clase.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
