"""S48 NdC final: per-alert diagnosis + coverage analysis."""
import csv, json, sys, io
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]

def parse_dt(s):
    if not s: return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M","%Y-%m-%dT%H:%M:%SZ","%Y-%m-%dT%H:%M:%S","%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        except: pass
    try:
        dt = datetime.fromisoformat(s.replace("Z","+00:00"))
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
    except: return None

WIN_S = datetime(2026,4,16,tzinfo=timezone.utc)
WIN_E = datetime(2026,5,16,23,59,59,tzinfo=timezone.utc)

alertas = [
    {'ts': parse_dt('2026-05-14 05:48:02'), 'vrp_mir':0.06, 'dist_mir':0.38},
    {'ts': parse_dt('2026-05-02 05:24:01'), 'vrp_mir':0.03, 'dist_mir':0.0},
    {'ts': parse_dt('2026-04-17 06:48:01'), 'vrp_mir':0.02, 'dist_mir':2.7},
]

meq = json.loads((ROOT/'data/mirova_equivalent/NevadosDeChillan.json').read_text(encoding='utf-8'))['records']
exp = json.loads((ROOT/'data/experimental/NevadosDeChillan.json').read_text(encoding='utf-8'))['records']

def get_ts(r): return parse_dt(r.get('datetime_utc'))

# === Per-alert diagnosis ===
print("="*70); print("PER-ALERT DIAGNOSIS"); print("="*70)
for a in alertas:
    print(f"\n--- ALERT {a['ts'].isoformat()} VIIRS375 vrp_mir={a['vrp_mir']} dist_mir={a['dist_mir']} ---")
    for label, recs in [('meq',meq),('exp',exp)]:
        # match VIIRS_*_(NOT _750) within 30 min
        hits = []
        for r in recs:
            ts = get_ts(r)
            if not ts: continue
            if abs((ts-a['ts']).total_seconds()) > 1800: continue
            sens = r.get('sensor','')
            if 'VIIRS' in sens and '750' not in sens:  # I-band records
                hits.append((ts,r))
        print(f"  [{label}] VIIRS-I hits ±30min: {len(hits)}")
        for ts,r in hits:
            pc = r.get('primary_cluster') or {}
            n_anom = len(r.get('anomaly_pixels') or [])
            n_t1 = r.get('n_test1_pixels') or 0
            n_vent = r.get('n_vent_pixels') or 0
            print(f"    ts={ts.isoformat()} sens={r.get('sensor')} sat={r.get('satellite')}")
            print(f"      record.vrp_mw={r.get('vrp_mw')} pc.vrp={pc.get('vrp_mw')} pc.dist={pc.get('centroid_dist_km')} pc.n_pix={pc.get('n_pixels')}")
            print(f"      final_src={r.get('final_hotspot_source')} final_dist={r.get('final_hotspot_dist_km')} dist_class={r.get('distance_class')}")
            print(f"      n_anom_pix={n_anom} n_test1={n_t1} n_vent={n_vent} triggered_test1={r.get('triggered_test1')}")
            print(f"      sigma_bg={r.get('diag_sigma_bg_k')} eff_thr={r.get('diag_eff_threshold_k')} t_max={r.get('t_max_k')} t_bg={r.get('t_bg_k')}")
            print(f"      nti_bg={r.get('diag_nti_bg')} nti_max={r.get('diag_nti_max')} nti_std={r.get('diag_nti_std')}")
            print(f"      vent_hs_dist={r.get('vent_hotspot_dist_km')} vent_vrp={r.get('vrp_vent_mw')}")

# === Coverage VIIRS-I NdC vs PCC, Lascar ===
print("\n"+"="*70); print("VIIRS-I COVERAGE COMPARE (sat-disaggregated)"); print("="*70)
for vol in ('NevadosDeChillan','PuyehueCordonCaulle','Lascar','Lastarria'):
    p = ROOT/f'data/mirova_equivalent/{vol}.json'
    if not p.exists(): continue
    recs = json.loads(p.read_text(encoding='utf-8'))['records']
    i_cnt = Counter(); m_cnt = Counter(); mo_cnt = Counter()
    for r in recs:
        ts = get_ts(r)
        if not ts or not (WIN_S <= ts <= WIN_E): continue
        sens = r.get('sensor','')
        if 'VIIRS' in sens and '750' not in sens:
            i_cnt[sens] += 1
        elif 'VIIRS' in sens and '750' in sens:
            m_cnt[sens] += 1
        elif 'MODIS' in sens:
            mo_cnt[sens] += 1
    print(f"  {vol}: VIIRS-I={sum(i_cnt.values())} {dict(i_cnt)}, VIIRS-M={sum(m_cnt.values())}, MODIS={sum(mo_cnt.values())}")

# === Sigma_bg distribution NdC VIIRS-I ===
print("\n"+"="*70); print("STD_BG NdC VIIRS-I distribution (window)"); print("="*70)
import statistics
sigmas = []
for r in meq:
    ts = get_ts(r)
    if not ts or not (WIN_S <= ts <= WIN_E): continue
    sens = r.get('sensor','')
    if 'VIIRS' in sens and '750' not in sens:
        s = r.get('diag_sigma_bg_k')
        if s is not None: sigmas.append(s)
print(f"  n={len(sigmas)}, min={min(sigmas):.2f}, p50={statistics.median(sigmas):.2f}, p95={sorted(sigmas)[int(len(sigmas)*.95)]:.2f}, max={max(sigmas):.2f}, mean={statistics.mean(sigmas):.2f}")

# Same for Lascar (control)
sigmas_lasc = []
for r in json.loads((ROOT/'data/mirova_equivalent/Lascar.json').read_text(encoding='utf-8'))['records']:
    ts = get_ts(r)
    if not ts or not (WIN_S <= ts <= WIN_E): continue
    sens = r.get('sensor','')
    if 'VIIRS' in sens and '750' not in sens:
        s = r.get('diag_sigma_bg_k')
        if s is not None: sigmas_lasc.append(s)
print(f"  Lascar control: n={len(sigmas_lasc)}, min={min(sigmas_lasc):.2f}, p50={statistics.median(sigmas_lasc):.2f}, p95={sorted(sigmas_lasc)[int(len(sigmas_lasc)*.95)]:.2f}, max={max(sigmas_lasc):.2f}")
