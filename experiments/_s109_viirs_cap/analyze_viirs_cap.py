"""S109 candidate (b): VIIRS as co-validation / cap of MODIS magnitude.
READ-ONLY cross-sensor analysis over data/mirova_equivalent/*.json + latest_consolidado.csv.

Definitions:
- "MODIS inflated summit night": a record with sensor in MODIS_* AND pc.vrp_mw>5
  AND primary_cluster.centroid_dist_km <= inner_radius_km (cluster IS at the crater,
  not the single-pixel distance_class which is the A46/A61 asymmetry trap).
- "Our VIIRS detected summit same night": exists a VIIRS record (375 I-band = no _750
  suffix, or 750 M-band = _750) with pc.vrp_mw>0 and centroid_dist_km<=inner_radius_km,
  within +/-WINDOW hours of the MODIS observation.
"""
import json, csv, collections, datetime, statistics, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
VOLS = ['Chaiten','Villarrica','Llaima','Tupungatito','PuyehueCordonCaulle']
INNER = {'Chaiten':5,'Villarrica':5,'Llaima':5,'Tupungatito':7,'PuyehueCordonCaulle':20}
WINDOW_H = 12.0
MODIS_THRESH = 5.0

def parse_dt(s):
    # "2026-01-29 02:35" UTC
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=datetime.timezone.utc)

def is_modis(s): return s.startswith('MODIS')
def is_viirs375(s): return s.startswith('VIIRS') and not s.endswith('_750')
def is_viirs750(s): return s.startswith('VIIRS') and s.endswith('_750')
def is_viirs(s): return s.startswith('VIIRS')

def pcvrp(r): return (r.get('primary_cluster') or {}).get('vrp_mw', 0) or 0
def pcdist(r): return (r.get('primary_cluster') or {}).get('centroid_dist_km', None)

def load(v):
    d = json.load(open(os.path.join(ROOT,'data','mirova_equivalent',v+'.json')))
    return d['records']

# ---------------- Analysis 1 & 2 ----------------
print("="*70)
print("ANALYSIS 1+2: VIIRS coverage & magnitude on MODIS-inflated summit nights")
print(f"  MODIS inflated = sensor MODIS, pc.vrp_mw>{MODIS_THRESH}, cluster<=inner_radius")
print(f"  VIIRS summit   = sensor VIIRS, pc.vrp_mw>0, cluster<=inner_radius, +/-{WINDOW_H}h")
print("="*70)

summary = {}
for v in VOLS:
    recs = load(v)
    inner = INNER[v]
    # MODIS inflated summit nights
    modis_hi = []
    for r in recs:
        if is_modis(r['sensor']) and pcvrp(r)>MODIS_THRESH:
            cd = pcdist(r)
            if cd is not None and cd <= inner:
                modis_hi.append(r)
    # all viirs summit records (for matching)
    viirs_summit = []
    for r in recs:
        if is_viirs(r['sensor']) and pcvrp(r)>0:
            cd = pcdist(r)
            if cd is not None and cd <= inner:
                viirs_summit.append((parse_dt(r['datetime_utc']), r))

    n_modis = len(modis_hi)
    matched = 0
    matched375 = 0
    matched750 = 0
    ratios = []  # modis_vrp / viirs_vrp (best viirs match)
    for r in modis_hi:
        t0 = parse_dt(r['datetime_utc'])
        mv = pcvrp(r)
        cands = [(abs((vt-t0).total_seconds())/3600.0, vr) for vt,vr in viirs_summit
                 if abs((vt-t0).total_seconds())/3600.0 <= WINDOW_H]
        if cands:
            matched += 1
            if any(is_viirs375(vr['sensor']) for _,vr in cands): matched375 += 1
            if any(is_viirs750(vr['sensor']) for _,vr in cands): matched750 += 1
            # pick highest-vrp viirs match as the "anchor candidate"
            best = max(cands, key=lambda x: pcvrp(x[1]))[1]
            vv = pcvrp(best)
            if vv>0:
                ratios.append(mv/vv)
    pct = 100.0*matched/n_modis if n_modis else float('nan')
    summary[v] = dict(n_modis_inflated=n_modis, matched=matched, pct=pct,
                      matched375=matched375, matched750=matched750,
                      ratios=ratios)
    print(f"\n{v} (inner={inner}km):")
    print(f"  MODIS-inflated summit nights: {n_modis}")
    if n_modis:
        print(f"  with VIIRS summit same night (+/-{WINDOW_H}h): {matched} ({pct:.0f}%)  [375:{matched375} 750:{matched750}]")
        if ratios:
            print(f"  MODIS/VIIRS magnitude ratio: median={statistics.median(ratios):.1f}x  "
                  f"min={min(ratios):.1f} max={max(ratios):.1f}  n={len(ratios)}")
        else:
            print(f"  no VIIRS magnitude to compare")

# pooled
print("\n" + "-"*70)
tot_modis = sum(s['n_modis_inflated'] for s in summary.values())
tot_match = sum(s['matched'] for s in summary.values())
all_ratios = [x for s in summary.values() for x in s['ratios']]
print(f"POOLED: {tot_match}/{tot_modis} MODIS-inflated nights have VIIRS summit "
      f"({100.0*tot_match/tot_modis:.0f}%)" if tot_modis else "POOLED: none")
if all_ratios:
    print(f"POOLED MODIS/VIIRS ratio: median={statistics.median(all_ratios):.1f}x  "
          f"p25={statistics.quantiles(all_ratios,n=4)[0]:.1f} p75={statistics.quantiles(all_ratios,n=4)[2]:.1f}")

# ---------------- Analysis 3: MIROVA CSV by sensor ----------------
print("\n" + "="*70)
print("ANALYSIS 3: latest_consolidado.csv ALERTA counts by sensor per volcano")
print("="*70)
csv_path = os.path.join(ROOT,'latest_consolidado.csv')
# name variants
ALIASES = {
    'Chaiten':{'Chaiten','Chaitén'},
    'Villarrica':{'Villarrica'},
    'Llaima':{'Llaima'},
    'Tupungatito':{'Tupungatito'},
    'PuyehueCordonCaulle':{'PuyehueCordonCaulle','Puyehue-Cordon Caulle','PuyehueCordonCaulle ','Puyehue Cordon Caulle','Cordon Caulle','Puyehue'},
    'Lascar':{'Lascar','Láscar'},
}
rows = list(csv.DictReader(open(csv_path, encoding='utf-8-sig')))
print("CSV cols:", list(rows[0].keys()))
# what tipo_registro values mean an actual detection
tipos = collections.Counter(r['Tipo_Registro'] for r in rows)
print("Tipo_Registro values:", dict(tipos))
for vkey, names in {**ALIASES}.items():
    sub = [r for r in rows if r['Volcan'] in names]
    if not sub:
        print(f"\n{vkey}: 0 rows in CSV (names tried {names})"); continue
    by_sensor_all = collections.Counter(r['Sensor'] for r in sub)
    # "ALERTA" = thermal alert rows (not RUTINA/NULO). Use Tipo_Registro containing ALERTA
    alerta = [r for r in sub if 'ALERTA' in (r['Tipo_Registro'] or '').upper()]
    by_sensor_alerta = collections.Counter(r['Sensor'] for r in alerta)
    print(f"\n{vkey}: total CSV rows={len(sub)}")
    print(f"   ALL by sensor: {dict(by_sensor_all)}")
    print(f"   ALERTA by sensor: {dict(by_sensor_alerta)}")
