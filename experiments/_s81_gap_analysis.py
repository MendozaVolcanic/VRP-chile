"""
S81 Gap Analysis - MIROVA CSV vs nuestras detecciones, ventana 45d (2026-04-11 a 2026-05-26).
Tier A 11 volcanes. Pareo timestamp +-30 min y mismo sensor (normalizado).
"""
import csv, json, os, sys, io
from datetime import datetime, timedelta
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s80-consolidation"
CSV_CONS = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/sweet-austin-b5413b/15_05_2026_registro_vrp_consolidado.csv"
CSV_OCR = os.path.join(ROOT, "data/mirova_reference/registro_vrp_ocr.csv")
JSON_DIR = os.path.join(ROOT, "data/mirova_equivalent")

WINDOW_START = datetime(2026, 4, 11)
WINDOW_END = datetime(2026, 5, 26, 23, 59, 59)
PAIR_TOL_MIN = 30

# Tier A volcanes -> filename JSON + posibles nombres en CSV
TIER_A = {
    "Lascar":           {"json": "Lascar.json",            "csv_names": ["Lascar"]},
    "Lastarria":        {"json": "Lastarria.json",         "csv_names": ["Lastarria"]},
    "Isluga":           {"json": "Isluga.json",            "csv_names": ["Isluga"]},
    "NevadosDeChillan": {"json": "NevadosDeChillan.json",  "csv_names": ["Nevados de Chillan", "NevadosDeChillan", "Nevados de Chillán"]},
    "Llaima":           {"json": "Llaima.json",            "csv_names": ["Llaima"]},
    "Villarrica":       {"json": "Villarrica.json",        "csv_names": ["Villarrica"]},
    "Chaiten":          {"json": "Chaiten.json",           "csv_names": ["Chaiten", "Chaitén"]},
    "Copahue":          {"json": "Copahue.json",           "csv_names": ["Copahue"]},
    "PlanchonPeteroa":  {"json": "PlanchonPeteroa.json",   "csv_names": ["PlanchonPeteroa", "Planchon-Peteroa", "Planchón-Peteroa"]},
    "Tupungatito":      {"json": "Tupungatito.json",       "csv_names": ["Tupungatito"]},
    "PuyehueCordonCaulle": {"json": "PuyehueCordonCaulle.json", "csv_names": ["Puyehue-Cordon Caulle", "PuyehueCordonCaulle", "Puyehue Cordon Caulle", "Puyehue-Cordón Caulle"]},
}

def norm_sensor(s):
    s_raw = (s or "").upper()
    s = s_raw.replace("-","").replace(" ","").replace("_","")
    if s.startswith("MODIS"): return "MODIS"  # MODIS, MODISAQUA, MODISTERRA
    # VIIRS_<sat>_750 = M-band, VIIRS_<sat> (no 750) = I-band 375
    if "VIIRS" in s:
        if "750" in s or "VIIRSM" in s: return "VIIRS750"
        if "375" in s or "VIIRSI" in s: return "VIIRS375"
        # VIIRS_SNPP / VIIRS_NOAA20 / VIIRS_NOAA21 -> I-band default
        if "SNPP" in s or "NOAA" in s: return "VIIRS375"
        return "VIIRS"  # bare "VIIRS" from CSV - ambiguous
    return s

def parse_dt(s):
    for fmt in ("%Y-%m-%dT%H:%M:%S","%Y-%m-%dT%H:%M:%SZ","%Y-%m-%d %H:%M:%S","%Y-%m-%dT%H:%M:%S.%fZ"):
        try: return datetime.strptime(s.replace("Z",""), fmt.replace("Z",""))
        except: pass
    try: return datetime.fromisoformat(s.replace("Z",""))
    except: return None

# ---------- Load CSV MIROVA (CONS + OCR) ----------
def load_csv(path, source_tag):
    rows = []
    if not os.path.exists(path):
        print(f"WARN: {path} no existe", file=sys.stderr); return rows
    with open(path, encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                dt = datetime.strptime(row["Fecha_Satelite_UTC"], "%Y-%m-%d %H:%M:%S")
            except: continue
            if not (WINDOW_START <= dt <= WINDOW_END): continue
            tipo = row.get("Tipo_Registro","")
            # MIROVA "detección" = ALERTA_TERMICA (cons) or ALERTA_TERMICA_OCR (ocr).
            # RUTINA con VRP=0 = scene-clear, NO es detección.
            try: vrp = float(row.get("VRP_MW","0") or 0)
            except: vrp = 0.0
            is_detection = ("ALERTA" in tipo.upper()) and vrp > 0
            if not is_detection: continue
            rows.append({
                "dt": dt, "volcan_csv": row["Volcan"].strip(),
                "sensor": norm_sensor(row["Sensor"]),
                "vrp_mw": vrp,
                "dist_km": float(row.get("Distancia_km","0") or 0),
                "tipo": tipo, "source": source_tag,
                "clasificacion": row.get("Clasificacion Mirova","") or row.get("Clasificacion_Mirova","")
            })
    return rows

mirova_rows = load_csv(CSV_CONS, "CONS") + load_csv(CSV_OCR, "OCR")
print(f"# MIROVA rows en ventana (detecciones ALERTA con VRP>0): CONS+OCR = {len(mirova_rows)}", flush=True)

# index by volcano canonical
mirova_by_vol = defaultdict(list)
for r in mirova_rows:
    canon = None
    for k, meta in TIER_A.items():
        if r["volcan_csv"] in meta["csv_names"]:
            canon = k; break
    if canon: mirova_by_vol[canon].append(r)

# ---------- Load nuestros JSONs ----------
ours_by_vol = {}
for vol, meta in TIER_A.items():
    p = os.path.join(JSON_DIR, meta["json"])
    if not os.path.exists(p):
        ours_by_vol[vol] = []; continue
    try:
        d = json.load(open(p, encoding="utf-8"))
        recs = d.get("records", []) if isinstance(d, dict) else d
    except Exception as e:
        print(f"ERR loading {vol}: {e}", file=sys.stderr); ours_by_vol[vol]=[]; continue
    out = []
    for rec in recs:
        dt = parse_dt(rec.get("datetime_utc",""))
        if dt is None: continue
        if not (WINDOW_START <= dt <= WINDOW_END): continue
        # detección = pc.vrp_mw>0 o vrp_mw>0
        pc = rec.get("primary_cluster") or {}
        pc_vrp = pc.get("vrp_mw") if isinstance(pc,dict) else None
        vrp_mw = rec.get("vrp_mw", 0) or 0
        vrp_for_audit = pc_vrp if (pc_vrp is not None and pc_vrp > 0) else vrp_mw
        if not (vrp_for_audit and vrp_for_audit > 0): continue
        out.append({
            "dt": dt, "sensor": norm_sensor(rec.get("sensor","")),
            "vrp_mw": float(vrp_for_audit),
            "scene_vrp_mw": float(vrp_mw),
            "pc_vrp_mw": float(pc_vrp) if pc_vrp else None,
            "dist_km": rec.get("final_hotspot_dist_km") or rec.get("hotspot_dist_km") or 0,
            "n_pix": rec.get("n_anomalous_pixels",0),
            "distance_class": rec.get("distance_class","")
        })
    ours_by_vol[vol] = out

# ---------- Pareo ----------
def sensor_match(s_csv, s_ours):
    if s_csv == s_ours: return True
    # CSV "VIIRS" generico vs VIIRS375/750
    if s_csv == "VIIRS" and s_ours in ("VIIRS375","VIIRS750"): return True
    if s_ours == "VIIRS" and s_csv in ("VIIRS375","VIIRS750"): return True
    return False

def pair_records(mirova, ours, tol_min=PAIR_TOL_MIN):
    used_ours = set()
    matches = []
    fn = []
    for m in mirova:
        best = None; best_dt = None
        for i, o in enumerate(ours):
            if i in used_ours: continue
            if not sensor_match(m["sensor"], o["sensor"]): continue
            dd = abs((m["dt"]-o["dt"]).total_seconds())/60.0
            if dd <= tol_min and (best is None or dd < best_dt):
                best = i; best_dt = dd
        if best is not None:
            used_ours.add(best); matches.append((m, ours[best], best_dt))
        else:
            fn.append(m)
    fp = [ours[i] for i in range(len(ours)) if i not in used_ours]
    return matches, fn, fp

# ---------- Build per-volcano stats ----------
import statistics
header_main = ["Volcan", "n_mirova", "n_nuestros", "n_match", "n_FN", "n_FP", "ratio_med", "recall", "precision"]
table = []
all_fn, all_fp = [], []
ratios_by_vol_sensor = defaultdict(list)

for vol in TIER_A:
    mr = mirova_by_vol.get(vol, [])
    ou = ours_by_vol.get(vol, [])
    matches, fns, fps = pair_records(mr, ou)
    ratios = []
    for m,o,_ in matches:
        if m["vrp_mw"]>0:
            r = o["vrp_mw"]/m["vrp_mw"]
            ratios.append(r)
            ratios_by_vol_sensor[(vol, m["sensor"])].append(r)
    med = statistics.median(ratios) if ratios else None
    recall = len(matches)/len(mr) if mr else None
    prec = len(matches)/len(ou) if ou else None
    table.append([vol, len(mr), len(ou), len(matches), len(fns), len(fps),
                  f"{med:.2f}" if med else "-",
                  f"{recall:.2f}" if recall is not None else "-",
                  f"{prec:.2f}" if prec is not None else "-"])
    for m in fns: all_fn.append((vol, m))
    for o in fps: all_fp.append((vol, o))

# ---------- Output ----------
print("\n## Tabla principal Tier A (ventana 2026-04-11 a 2026-05-26, pareo ±30 min)")
print("| " + " | ".join(header_main) + " |")
print("|" + "|".join(["---"]*len(header_main)) + "|")
for row in table:
    print("| " + " | ".join(str(x) for x in row) + " |")

# Top FN
all_fn.sort(key=lambda x: -x[1]["vrp_mw"])
print("\n## Top 20 FN (MIROVA detectó, nosotros perdimos) — orden VRP MIROVA desc")
print("| # | Volcán | dt_UTC | sensor | VRP_MW | dist_km | tipo | source | clasif |")
print("|---|---|---|---|---|---|---|---|---|")
for i,(vol,m) in enumerate(all_fn[:20], 1):
    print(f"| {i} | {vol} | {m['dt'].isoformat()} | {m['sensor']} | {m['vrp_mw']:.2f} | {m['dist_km']:.2f} | {m['tipo']} | {m['source']} | {m['clasificacion']} |")

# Top FP
all_fp.sort(key=lambda x: -x[1]["vrp_mw"])
print("\n## Top 20 FP (nosotros gritamos, MIROVA no) — orden VRP nuestro desc")
print("| # | Volcán | dt_UTC | sensor | VRP_MW | dist_km | n_pix | class |")
print("|---|---|---|---|---|---|---|---|")
for i,(vol,o) in enumerate(all_fp[:20], 1):
    print(f"| {i} | {vol} | {o['dt'].isoformat()} | {o['sensor']} | {o['vrp_mw']:.2f} | {o['dist_km']:.2f} | {o['n_pix']} | {o['distance_class']} |")

# Ratio por vol x sensor
print("\n## Ratio mediana (nuestro/mirova) por volcán × sensor (Aveni tolerance 0.65-1.35)")
print("| Volcán | Sensor | n | ratio_med | p25 | p75 | dentro_banda? |")
print("|---|---|---|---|---|---|---|")
for (vol,sens), rs in sorted(ratios_by_vol_sensor.items()):
    if not rs: continue
    med = statistics.median(rs)
    rs_s = sorted(rs); p25 = rs_s[len(rs_s)//4]; p75 = rs_s[(3*len(rs_s))//4]
    ok = "OK" if 0.65 <= med <= 1.35 else "FUERA"
    print(f"| {vol} | {sens} | {len(rs)} | {med:.2f} | {p25:.2f} | {p75:.2f} | {ok} |")

# Sensor coverage FN
print("\n## Cobertura sensor en FN (cuántos FN son VIIRS-OCR vs MODIS-CONS)")
fn_by_src = defaultdict(int)
for _,m in all_fn:
    fn_by_src[(m["sensor"], m["source"])] += 1
for (s,src),n in sorted(fn_by_src.items(), key=lambda x:-x[1]):
    print(f"  {s:10s} {src:5s}  {n}")

# Volcanes con recall<60 o precision<50
print("\n## Volcanes problemáticos (recall<0.60 o precision<0.50)")
for row in table:
    vol,_,_,_,_,_,_,rec,prec = row
    try:
        rec_f = float(rec) if rec != "-" else None
        prec_f = float(prec) if prec != "-" else None
    except: continue
    flags=[]
    if rec_f is not None and rec_f<0.60: flags.append(f"recall={rec_f:.2f}")
    if prec_f is not None and prec_f<0.50: flags.append(f"prec={prec_f:.2f}")
    if flags:
        print(f"  - {vol}: {', '.join(flags)}")

print("\nDONE")
