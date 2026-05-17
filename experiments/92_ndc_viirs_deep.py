"""S48 NdC VIIRS-I deep dive: 3 alertas MIROVA recall 0/3, 20 records vs 65 MODIS."""
from __future__ import annotations
import csv, json, sys, io
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
VOL = "NevadosDeChillan"
WIN_START = datetime(2026, 4, 16, tzinfo=timezone.utc)
WIN_END = datetime(2026, 5, 16, 23, 59, 59, tzinfo=timezone.utc)

CSV_PATH = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
MEQ_PATH = ROOT / "data" / "mirova_equivalent" / f"{VOL}.json"
EXP_PATH = ROOT / "data" / "experimental" / f"{VOL}.json"

def parse_dt(s):
    if s is None: return None
    s = str(s).strip()
    if not s: return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S",
                "%d/%m/%Y %H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except: pass
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except:
        return None

# ---------- 1. MIROVA refs for NdC in window, VIIRS-I focus ----------
print("=" * 70)
print("STEP 1: MIROVA refs NdC 30d window (all sensors)")
print("=" * 70)
mir_refs = []
with open(CSV_PATH, encoding="utf-8") as f:
    rdr = csv.DictReader(f)
    cols = rdr.fieldnames
    print(f"CSV cols: {cols}")
    for row in rdr:
        if row.get("Volcan", "").strip() != VOL:
            continue
        ts = parse_dt(row.get("Fecha_Satelite_UTC") or row.get("timestamp"))
        if not ts or not (WIN_START <= ts <= WIN_END):
            continue
        mir_refs.append({
            "ts": ts,
            "sat": "",
            "sensor": row.get("Sensor", "").strip(),
            "vrp_mw": row.get("VRP_MW"),
            "alert": row.get("Clasificacion Mirova", "").strip() or row.get("Tipo_Registro", "").strip(),
            "tipo": row.get("Tipo_Registro", "").strip(),
            "dist": row.get("Distancia_km"),
            "row": row,
        })

print(f"NdC refs in window: {len(mir_refs)}")
by_sensor = Counter(r["sensor"] for r in mir_refs)
by_sat = Counter(r["sat"] for r in mir_refs)
by_alert = Counter(r["alert"] for r in mir_refs)
print(f"By sensor: {dict(by_sensor)}")
print(f"By sat: {dict(by_sat)}")
print(f"By alert: {dict(by_alert)}")

# VIIRS-I = sensor containing "I" 375 or sat begins with NOAA/SNPP with I-band
viirs_i_refs = [r for r in mir_refs if "375" in r["sensor"] or r["sensor"] in ("VIIRS_I", "VIIRSI", "VIIRS375")]
# fallback: detect by sensor string
if not viirs_i_refs:
    viirs_i_refs = [r for r in mir_refs if "VIIRS" in r["sensor"].upper() and ("375" in r["sensor"] or "I" in r["sensor"])]
print(f"\nVIIRS-I 375m refs: {len(viirs_i_refs)}")
for r in viirs_i_refs:
    print(f"  {r['ts'].isoformat()} sat={r['sat']} sensor={r['sensor']} vrp={r['vrp_mw']} alert={r['alert']} dist={r['dist']}")

# Filter to ALERTA_TERMICA only (ground truth for recall)
viirs_i_alerts = [r for r in viirs_i_refs if "ALERTA" in r["alert"].upper()]
print(f"\nVIIRS-I ALERTA_TERMICA: {len(viirs_i_alerts)}")
for r in viirs_i_alerts:
    print(f"  {r['ts'].isoformat()} sat={r['sat']} vrp={r['vrp_mw']} dist={r['dist']}")

# ---------- 2. Compare to VRP-chile records ----------
print("\n" + "=" * 70)
print("STEP 2: VRP-chile records for each VIIRS-I MIROVA alert")
print("=" * 70)
meq = json.loads(MEQ_PATH.read_text(encoding="utf-8"))
exp = json.loads(EXP_PATH.read_text(encoding="utf-8"))
meq_recs = meq.get("records") or meq.get("data") or (meq if isinstance(meq, list) else [])
exp_recs = exp.get("records") or exp.get("data") or (exp if isinstance(exp, list) else [])
print(f"meq records: {len(meq_recs)}, exp records: {len(exp_recs)}")
print(f"meq top keys: {list(meq.keys()) if isinstance(meq, dict) else 'list'}")
if meq_recs:
    print(f"first rec keys: {list(meq_recs[0].keys())[:30]}")

def get_ts(r):
    for k in ("acquisition_dt_utc", "timestamp_utc", "acq_dt_utc", "dt_utc", "timestamp", "datetime_utc"):
        if k in r and r[k]:
            return parse_dt(r[k])
    return None

def get_sensor(r):
    return r.get("sensor") or r.get("product") or r.get("source", "")

# Build index by timestamp
for alert in viirs_i_alerts:
    print(f"\n--- ALERT {alert['ts'].isoformat()} sat={alert['sat']} vrp_mirova={alert['vrp_mw']} ---")
    for label, recs in [("meq", meq_recs), ("exp", exp_recs)]:
        matches = []
        for r in recs:
            ts = get_ts(r)
            if not ts: continue
            if abs((ts - alert["ts"]).total_seconds()) <= 1800:
                sens = get_sensor(r)
                if "VIIRS" in sens.upper() and ("375" in sens or "I" in sens.upper()):
                    matches.append((ts, r))
        if not matches:
            # broader: any VIIRS within 30 min
            for r in recs:
                ts = get_ts(r)
                if not ts: continue
                if abs((ts - alert["ts"]).total_seconds()) <= 1800:
                    matches.append((ts, r))
        print(f"  [{label}] matches ±30min: {len(matches)}")
        for ts, r in matches[:3]:
            sens = get_sensor(r)
            pc = r.get("primary_cluster") or {}
            print(f"    ts={ts.isoformat()} sens={sens} pc.vrp={pc.get('vrp_mw')} pc.dist={pc.get('centroid_dist_km')} "
                  f"src={r.get('final_hotspot_source')} n_anom={len(r.get('anomaly_pixels') or [])} "
                  f"std_bg_i04={r.get('std_bg_i04')} threshold_mir={r.get('threshold_mir')}")

# ---------- 3. Coverage VIIRS-I NdC vs PCC ----------
print("\n" + "=" * 70)
print("STEP 3: VIIRS-I coverage NdC vs PCC")
print("=" * 70)
def viirs_i_counts(path):
    if not path.exists(): return None
    d = json.loads(path.read_text(encoding="utf-8"))
    recs = d.get("records") or d.get("data") or (d if isinstance(d, list) else [])
    sat_count = Counter()
    ts_list = []
    for r in recs:
        ts = get_ts(r)
        if not ts or not (WIN_START <= ts <= WIN_END): continue
        sens = get_sensor(r)
        if "VIIRS" in sens.upper() and ("375" in sens or "I" in sens.upper() and "M" not in sens.upper().replace("VIIRS","")):
            sat_count[r.get("satellite", "?")] += 1
            ts_list.append(ts)
    return sat_count, sorted(ts_list)

for vol in ("NevadosDeChillan", "PuyehueCordonCaulle", "Lascar"):
    p = ROOT / "data" / "mirova_equivalent" / f"{vol}.json"
    if not p.exists():
        print(f"  {vol}: missing")
        continue
    sc, tslist = viirs_i_counts(p)
    print(f"  {vol}: VIIRS-I in 30d = {sum(sc.values())}, by sat = {dict(sc)}")
    if tslist:
        # check gaps >2 days
        gaps = []
        for a, b in zip(tslist, tslist[1:]):
            gap_h = (b - a).total_seconds() / 3600
            if gap_h > 48:
                gaps.append((a.date(), b.date(), round(gap_h, 1)))
        print(f"    gaps >48h: {len(gaps)}")
        for g in gaps[:5]:
            print(f"      {g}")

# ---------- 4. NdC ALL records by sensor (anomaly check) ----------
print("\n" + "=" * 70)
print("STEP 4: NdC all-sensor breakdown")
print("=" * 70)
sens_cnt = Counter()
sat_cnt = Counter()
for r in meq_recs:
    ts = get_ts(r)
    if not ts or not (WIN_START <= ts <= WIN_END): continue
    sens_cnt[get_sensor(r)] += 1
    sat_cnt[r.get("satellite", "?")] += 1
print(f"By sensor (meq): {dict(sens_cnt)}")
print(f"By sat (meq): {dict(sat_cnt)}")

sens_cnt_e = Counter()
sat_cnt_e = Counter()
for r in exp_recs:
    ts = get_ts(r)
    if not ts or not (WIN_START <= ts <= WIN_END): continue
    sens_cnt_e[get_sensor(r)] += 1
    sat_cnt_e[r.get("satellite", "?")] += 1
print(f"By sensor (exp): {dict(sens_cnt_e)}")
print(f"By sat (exp): {dict(sat_cnt_e)}")

# ---------- 5. std_bg_i04 stats for nights near alerts ----------
print("\n" + "=" * 70)
print("STEP 5: std_bg_i04 distribution VIIRS-I records NdC")
print("=" * 70)
stds = []
for r in meq_recs:
    ts = get_ts(r)
    if not ts or not (WIN_START <= ts <= WIN_END): continue
    sens = get_sensor(r)
    if "VIIRS" in sens.upper() and "375" in sens:
        s = r.get("std_bg_i04")
        if s is not None:
            stds.append(s)
print(f"std_bg_i04 samples: {len(stds)}, min={min(stds) if stds else None}, max={max(stds) if stds else None}, "
      f"mean={sum(stds)/len(stds) if stds else None}")
