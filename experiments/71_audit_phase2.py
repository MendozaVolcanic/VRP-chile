"""S33 Driver B Phase 2 audit — Phase 2 vs Phase 1 operacional.

Phase 1 ya operacional (data/mirova_equivalent/<vol>.json post-reproc S32).
Phase 2 reproc en data/mirova_equivalent_phase2/<vol>.json.

Compara cada profile contra CSV MIROVA NRT.

Criterios Phase 2 (más estrictos que Phase 1):
- Recall global ≥73% (baseline Phase 1).
- Ratio Chaiten ≤5× (vs 14.5× Phase 1).
- Ratio PCC ≤8× (vs 11.9× Phase 1).
- Lastarria/Villarrica/Planchón mantienen ratios Phase 1 (no regresión).
"""
from __future__ import annotations
import json, sys, io
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path("C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
CSV = ROOT / "01_05_2026_registro_vrp_consolidado.csv"

PROFILES = {
    "phase1_op":  ROOT / "data" / "mirova_equivalent",
    "phase2":     ROOT / "data" / "mirova_equivalent_phase2",
}

VOLC_MAP = {
    'Lascar':'Lascar','Lastarria':'Lastarria','Tupungatito':'Tupungatito',
    'Villarrica':'Villarrica','Puyehue-Cordon Caulle':'PuyehueCordonCaulle',
    'Copahue':'Copahue','Nevados de Chillan':'NevadosDeChillan',
    'Llaima':'Llaima','Chaiten':'Chaiten','PlanchonPeteroa':'PlanchonPeteroa',
    'Isluga':'Isluga'
}
END_DT = datetime(2026,4,29,23,59,tzinfo=timezone.utc)
START_DT = END_DT - timedelta(days=90)
TOL_MIN = 60


def parse_csv_dt(s): return datetime.strptime(s.strip(),"%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
def parse_rec_dt(s):
    s = s.strip().replace("Z","+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M"):
        try: return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except: continue
    return datetime.fromisoformat(s)
def sensor_match(ref, rec):
    if ref == "MODIS": return rec.startswith("MODIS")
    if ref == "VIIRS": return rec.startswith("VIIRS_") and rec.endswith("_750")
    if ref == "VIIRS375": return rec.startswith("VIIRS_") and not rec.endswith("_750")
    return False

def vrp_summit(rec):
    if not rec: return 0
    pc = rec.get('primary_cluster')
    if not pc: return rec.get('vrp_mw') or 0
    if rec.get('distance_class') and rec.get('distance_class') != 'summit': return 0
    return pc.get('vrp_mw', 0)

df = pd.read_csv(CSV)
df['dt'] = df['Fecha_Satelite_UTC'].apply(parse_csv_dt)
df = df[(df['dt'] >= START_DT) & (df['dt'] <= END_DT)]
df = df[df['Volcan'].isin(VOLC_MAP.keys())]
df_alerta = df[df['Tipo_Registro']=='ALERTA_TERMICA']

print(f"# Audit Phase 2 vs Phase 1 (operacional)\n")
print(f"Window: {START_DT.date()} -> {END_DT.date()}")
print(f"Refs MIROVA ALERTA_TERMICA: {len(df_alerta)}\n")


def load_recs(profile_dir, our_v):
    f = profile_dir / f"{our_v}.json"
    if not f.exists(): return []
    out = []
    for r in json.loads(f.read_text(encoding='utf-8')).get('records', []):
        try: dt = parse_rec_dt(r['datetime_utc'])
        except: continue
        if START_DT <= dt <= END_DT:
            r['_dt'] = dt; out.append(r)
    return out

def find_match(ref_dt, ref_sensor, recs):
    tol = timedelta(minutes=TOL_MIN)
    best, bd = None, tol + timedelta(seconds=1)
    for r in recs:
        if not sensor_match(ref_sensor, r.get('sensor','')): continue
        delta = abs(r['_dt']-ref_dt)
        if delta <= tol and delta < bd: best, bd = r, delta
    return best

def audit(label, profile_dir):
    print(f"\n## Profile: {label}\n")
    if not profile_dir.exists():
        print(f"❌ {profile_dir} no existe"); return None
    by_vol = defaultdict(lambda: {'refs':0,'tps':0,'ratios':[],'mirova_vrp':[],'our_vrp':[]})
    for csv_v, our_v in VOLC_MAP.items():
        recs = load_recs(profile_dir, our_v)
        sub = df_alerta[df_alerta['Volcan']==csv_v]
        for _, row in sub.iterrows():
            by_vol[our_v]['refs'] += 1
            rec = find_match(row['dt'], row['Sensor'], recs)
            if rec is None: continue
            ov = vrp_summit(rec)
            if ov > 0:
                by_vol[our_v]['tps'] += 1
                if row['VRP_MW'] > 0:
                    by_vol[our_v]['ratios'].append(ov/row['VRP_MW'])
                    by_vol[our_v]['mirova_vrp'].append(row['VRP_MW'])
                    by_vol[our_v]['our_vrp'].append(ov)
    print("| Volcán | Refs | TPs | Recall % | Ratio med | mediana MIROVA MW | mediana nuestro MW |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    g_refs, g_tps, all_ratios = 0, 0, []
    for v, d in sorted(by_vol.items()):
        g_refs += d['refs']; g_tps += d['tps']
        all_ratios.extend(d['ratios'])
        recall = d['tps']/d['refs']*100 if d['refs'] else 0.0
        rs = sorted(d['ratios'])
        med_r = rs[len(rs)//2] if rs else float('nan')
        ms = sorted(d['mirova_vrp'])
        med_m = ms[len(ms)//2] if ms else float('nan')
        os_ = sorted(d['our_vrp'])
        med_o = os_[len(os_)//2] if os_ else float('nan')
        rs_str = f"{med_r:.2f}" if rs else "NA"
        mm_str = f"{med_m:.3f}" if ms else "NA"
        oo_str = f"{med_o:.3f}" if os_ else "NA"
        print(f"| {v} | {d['refs']} | {d['tps']} | {recall:.1f} | {rs_str} | {mm_str} | {oo_str} |")
    g_recall = g_tps/max(1,g_refs)*100
    all_ratios.sort()
    g_med = all_ratios[len(all_ratios)//2] if all_ratios else float('nan')
    print(f"\n**GLOBAL — Recall: {g_recall:.1f}% ({g_tps}/{g_refs}). "
          f"Ratio mediano: {g_med:.2f}x.**")
    return {'recall': g_recall, 'ratio': g_med, 'by_vol': by_vol}

results = {}
for label, prof in PROFILES.items():
    results[label] = audit(label, prof)

print("\n" + "="*80)
print("\n## Comparación Phase 2 vs Phase 1\n")
P1, P2 = results.get('phase1_op'), results.get('phase2')
if P1 and P2:
    print("| Métrica | Phase 1 (operacional) | Phase 2 | Δ |")
    print("|---|---:|---:|---:|")
    print(f"| Recall global | {P1['recall']:.1f}% | {P2['recall']:.1f}% | {P2['recall']-P1['recall']:+.1f}pp |")
    print(f"| Ratio mediano | {P1['ratio']:.2f}x | {P2['ratio']:.2f}x | {(P2['ratio']/P1['ratio']-1)*100:+.0f}% |")

    # Por volcán crítico
    print("\n### Cambio ratio por volcán crítico (Chaiten/PCC objetivo Phase 2)\n")
    print("| Volcán | P1 ratio | P2 ratio | Δ |")
    print("|---|---:|---:|---:|")
    for v in ['Chaiten', 'PuyehueCordonCaulle', 'Lastarria', 'Villarrica', 'PlanchonPeteroa', 'Tupungatito', 'Lascar']:
        p1d = P1['by_vol'].get(v, {})
        p2d = P2['by_vol'].get(v, {})
        p1r = sorted(p1d.get('ratios', []))
        p2r = sorted(p2d.get('ratios', []))
        if not p1r or not p2r:
            print(f"| {v} | NA | NA | NA |"); continue
        m1, m2 = p1r[len(p1r)//2], p2r[len(p2r)//2]
        delta = (m2/m1-1)*100 if m1>0 else 0
        print(f"| {v} | {m1:.2f} | {m2:.2f} | {delta:+.0f}% |")

    # Veredicto
    print("\n## Veredicto Phase 2\n")
    chai_p2 = sorted(P2['by_vol'].get('Chaiten', {}).get('ratios', []))
    pcc_p2  = sorted(P2['by_vol'].get('PuyehueCordonCaulle', {}).get('ratios', []))
    chai_med = chai_p2[len(chai_p2)//2] if chai_p2 else float('inf')
    pcc_med  = pcc_p2[len(pcc_p2)//2] if pcc_p2 else float('inf')
    crit_recall = P2['recall'] >= 73
    crit_chai = chai_med <= 5
    crit_pcc = pcc_med <= 8
    print(f"- Recall ≥73%? {'OK' if crit_recall else 'NO'} ({P2['recall']:.1f}%)")
    print(f"- Chaiten ≤5x? {'OK' if crit_chai else 'NO'} ({chai_med:.2f}x)")
    print(f"- PCC ≤8x?     {'OK' if crit_pcc else 'NO'} ({pcc_med:.2f}x)")
    if crit_recall and crit_chai and crit_pcc:
        print("\n**Phase 2 APROBADO** — adoptar como operacional.")
    else:
        print("\n**Phase 2 PARCIAL** — refinamiento o documentar como mejora gradual.")
else:
    print("(Phase 2 reproc no disponible aún — esperar workflow A/B Phase 2.)")
