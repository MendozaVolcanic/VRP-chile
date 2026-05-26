"""S81 audit of data/mirova_equivalent/ — numerical anomalies across 11 Tier A volcanoes."""
import json
import os
from collections import defaultdict, Counter

TIER_A = ['Lascar','Lastarria','Isluga','NevadosDeChillan','Llaima','Villarrica',
          'Chaiten','Copahue','PlanchonPeteroa','Tupungatito','PuyehueCordonCaulle']
INNER = {'Lastarria':3,'Lascar':5,'Isluga':5,'NevadosDeChillan':5,'Llaima':5,
         'Villarrica':5,'Chaiten':5,'PlanchonPeteroa':3,'Copahue':4,
         'Tupungatito':7,'PuyehueCordonCaulle':20}

base = 'data/mirova_equivalent'
all_recs = []
for v in TIER_A:
    with open(os.path.join(base, v+'.json'), encoding='utf-8') as f:
        d = json.load(f)
    for r in d.get('records', []):
        r['_vol'] = v
        all_recs.append(r)

print(f'Loaded {len(all_recs)} records across {len(TIER_A)} Tier A volcanoes\n')

# ===== 1. VRP out of range =====
vrp_buckets = {'>1000':[], '>5000':[], '>50000':[]}
for r in all_recs:
    vrp = r.get('vrp_mw') or 0
    if vrp > 50000: vrp_buckets['>50000'].append(r)
    elif vrp > 5000: vrp_buckets['>5000'].append(r)
    elif vrp > 1000: vrp_buckets['>1000'].append(r)

print('===== 1. VRP RANGE =====')
for k, lst in vrp_buckets.items():
    print(f'  VRP {k} MW: {len(lst)} records')

# Top 20 by VRP
top20 = sorted(all_recs, key=lambda r: r.get('vrp_mw') or 0, reverse=True)[:20]
print('\nTop 20 highest VRP:')
print(f'  {"vol":22s} {"datetime":22s} {"sensor":12s} {"vrp_mw":>12s} {"dist_km":>8s} {"class":8s} {"n_px":>5s}')
for r in top20:
    print(f'  {r["_vol"]:22s} {str(r.get("datetime_utc",""))[:19]:22s} {str(r.get("sensor","?"))[:12]:12s} {r.get("vrp_mw",0):12.1f} {r.get("final_hotspot_dist_km",0) or 0:8.2f} {str(r.get("distance_class","?")):8s} {r.get("n_anomalous_pixels",0):5d}')

# ===== 2. Distance class mismatch =====
print('\n===== 2. DISTANCE CLASS vs INNER RADIUS =====')
mismatches = []
for r in all_recs:
    d_km = r.get('final_hotspot_dist_km')
    cls = r.get('distance_class')
    if d_km is None or cls is None:
        continue
    inner = INNER[r['_vol']]
    if d_km <= inner and cls == 'far':
        mismatches.append(('SHOULD_BE_SUMMIT', r))
    elif d_km > inner and cls == 'summit':
        mismatches.append(('SHOULD_BE_FAR', r))

mm_counter = Counter()
mm_by_vol = defaultdict(lambda: Counter())
for kind, r in mismatches:
    mm_counter[kind] += 1
    mm_by_vol[r['_vol']][kind] += 1
print(f'Total mismatches: {len(mismatches)} ({dict(mm_counter)})')
for v in TIER_A:
    if mm_by_vol[v]:
        print(f'  {v}: {dict(mm_by_vol[v])}  (inner={INNER[v]})')

# Sample 10 mismatches
print('\nSample 10 mismatches:')
for kind, r in mismatches[:10]:
    print(f'  [{kind}] {r["_vol"]} {r.get("datetime_utc","?")[:19]} sensor={r.get("sensor","?")} dist={r.get("final_hotspot_dist_km")} class={r.get("distance_class")} inner={INNER[r["_vol"]]}')

# ===== 3. Saturation guard — VRP > 5000 MW =====
print('\n===== 3. SATURATION SUSPECTS (vrp > 5000 MW) =====')
sat = [r for r in all_recs if (r.get('vrp_mw') or 0) > 5000]
print(f'Total: {len(sat)}')
by_vol_sat = Counter(r['_vol'] for r in sat)
for v, c in by_vol_sat.most_common():
    print(f'  {v}: {c}')

# ===== 4. Schema gaps =====
print('\n===== 4. SCHEMA GAPS (diag_* fields post-S21) =====')
diag_fields = ['diag_sigma_bg_k','diag_eff_threshold_k','diag_nti_std','diag_nti_max','diag_nti_bg','t_bg_k']
gaps = defaultdict(lambda: defaultdict(int))
for r in all_recs:
    for f in diag_fields:
        if f not in r or r[f] is None:
            gaps[r['_vol']][f] += 1
for v in TIER_A:
    has_gaps = [(f, gaps[v][f]) for f in diag_fields if gaps[v].get(f, 0) > 0]
    if has_gaps:
        n = sum(1 for r in all_recs if r['_vol']==v)
        print(f'  {v} (n={n}): {has_gaps}')

# ===== 5. Cross-sensor coherence: same night, ratio >5x =====
print('\n===== 5. CROSS-SENSOR COHERENCE (same date, same vol, ratio > 5x) =====')
by_vol_date = defaultdict(list)
for r in all_recs:
    dt = (r.get('datetime_utc') or '')[:10]
    by_vol_date[(r['_vol'], dt)].append(r)

cross_anom = []
for (v, dt), recs in by_vol_date.items():
    if len(recs) < 2:
        continue
    # group by sensor family
    by_sens = defaultdict(list)
    for r in recs:
        s = r.get('sensor','?')
        # normalize: MODIS_Aqua, MODIS_Terra, VIIRS_NOAA20, VIIRS_SNPP, VIIRS_NOAA21
        by_sens[s].append(r.get('vrp_mw') or 0)
    sens_max = {s: max(v) for s, v in by_sens.items() if max(v) > 0}
    if len(sens_max) >= 2:
        vals = list(sens_max.values())
        mn, mx = min(vals), max(vals)
        if mn > 1 and mx/mn > 5:
            cross_anom.append((v, dt, sens_max, mx/mn))
print(f'Total: {len(cross_anom)}')
cross_anom.sort(key=lambda x: x[3], reverse=True)
print('Top 15:')
for v, dt, sm, ratio in cross_anom[:15]:
    print(f'  {v} {dt} ratio={ratio:.1f}x  {sm}')

# ===== 6. Cluster vs pixel ratio =====
print('\n===== 6. n_anomalous_pixels vs n_hotspots_clustered ratio =====')
ratios = []
for r in all_recs:
    npx = r.get('n_anomalous_pixels') or 0
    nh = r.get('n_hotspots_clustered') or 0
    if nh > 0 and npx > 0:
        ratios.append((npx/nh, r))
# Outliers: ratio > 100 (extreme) or ratio < 1 (impossible: clusters > pixels?)
extreme_hi = [(rr, r) for rr, r in ratios if rr > 100]
impossible = [(rr, r) for rr, r in ratios if rr < 1]
print(f'  ratio>100: {len(extreme_hi)}')
print(f'  ratio<1 (impossible: clusters>pixels): {len(impossible)}')
if extreme_hi:
    print('  Top 5 extreme high:')
    for rr, r in sorted(extreme_hi, key=lambda x: x[0], reverse=True)[:5]:
        print(f'    {r["_vol"]} {r.get("datetime_utc","")[:19]} npx={r.get("n_anomalous_pixels")} nh={r.get("n_hotspots_clustered")} ratio={rr:.1f}')
if impossible:
    print('  Sample 5 impossible:')
    for rr, r in impossible[:5]:
        print(f'    {r["_vol"]} {r.get("datetime_utc","")[:19]} npx={r.get("n_anomalous_pixels")} nh={r.get("n_hotspots_clustered")} ratio={rr:.2f}')

# ===== 7. Duplicates: same date+sensor+vol =====
print('\n===== 7. DUPLICATES (vol+datetime_utc+sensor) =====')
seen = defaultdict(list)
for r in all_recs:
    k = (r['_vol'], r.get('datetime_utc'), r.get('sensor'), r.get('granule'))
    seen[k].append(r)
dups = {k: v for k, v in seen.items() if len(v) > 1}
print(f'Exact dup keys (with granule): {len(dups)}')

seen2 = defaultdict(list)
for r in all_recs:
    k = (r['_vol'], r.get('datetime_utc'), r.get('sensor'))
    seen2[k].append(r)
dups2 = {k: v for k, v in seen2.items() if len(v) > 1}
print(f'Same vol+datetime+sensor (any granule): {len(dups2)}')
# How many have DIFFERENT vrp?
diff_vrp = 0
diff_examples = []
for k, lst in dups2.items():
    vs = set(round(r.get('vrp_mw') or 0, 3) for r in lst)
    if len(vs) > 1:
        diff_vrp += 1
        if len(diff_examples) < 5:
            diff_examples.append((k, lst))
print(f'  With DIFFERENT vrp_mw: {diff_vrp}')
for k, lst in diff_examples:
    print(f'    {k}: vrps={[round(r.get("vrp_mw") or 0, 2) for r in lst]} granules={[r.get("granule","?")[:40] for r in lst]}')

# ===== 8. VRP_TIR — check field existence =====
print('\n===== 8. VRP_TIR PRESENCE =====')
tir_keys = set()
for r in all_recs[:5000]:
    for k in r.keys():
        if 'tir' in k.lower():
            tir_keys.add(k)
print(f'TIR-related keys found: {tir_keys}')

# ===== Per-volcano summary table =====
print('\n===== PER-VOLCANO SUMMARY =====')
print(f'  {"vol":22s} {"n":>5s} {"vrp>1k":>7s} {"vrp>5k":>7s} {"vrp>50k":>8s} {"dist_mm":>8s} {"dups":>6s}')
for v in TIER_A:
    n = sum(1 for r in all_recs if r['_vol']==v)
    v1k = sum(1 for r in all_recs if r['_vol']==v and (r.get('vrp_mw') or 0) > 1000)
    v5k = sum(1 for r in all_recs if r['_vol']==v and (r.get('vrp_mw') or 0) > 5000)
    v50k = sum(1 for r in all_recs if r['_vol']==v and (r.get('vrp_mw') or 0) > 50000)
    mm = sum(mm_by_vol[v].values())
    dup = sum(1 for k, lst in dups2.items() if k[0]==v)
    print(f'  {v:22s} {n:5d} {v1k:7d} {v5k:7d} {v50k:8d} {mm:8d} {dup:6d}')
