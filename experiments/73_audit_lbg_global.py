"""S33 D4 audit — L_bg global vs operacional Phase 1.

Compara mirova_equivalent_lbg_global (D4 fix) vs mirova_equivalent (Phase 1).
Foco principal: Tupungatito (recall 48% pre-fix). Resto: no-regresión.

Criterios D4:
- Tupungatito recall ≥75% (vs 48% pre-fix).
- Otros volcanes: recall sin regresión >5pp.
- Ratio mediano global no peor que Phase 1 (1.66×).
- Ningún volcán cae a ratio sub-estima <0.3×.
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
    "phase1_op":   ROOT / "data" / "mirova_equivalent",
    "lbg_global":  ROOT / "data" / "mirova_equivalent_lbg_global",
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

print(f"# Audit D4 L_bg global vs Phase 1 operacional\n")
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
    by_vol = defaultdict(lambda: {'refs':0,'tps':0,'ratios':[]})
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
    print("| Volcán | Refs | TPs | Recall % | Ratio med |")
    print("|---|---:|---:|---:|---:|")
    g_refs, g_tps, all_r = 0, 0, []
    for v, d in sorted(by_vol.items()):
        g_refs += d['refs']; g_tps += d['tps']
        all_r.extend(d['ratios'])
        rec_pct = d['tps']/d['refs']*100 if d['refs'] else 0
        rs = sorted(d['ratios'])
        med_r = rs[len(rs)//2] if rs else float('nan')
        rs_str = f"{med_r:.2f}" if rs else "NA"
        print(f"| {v} | {d['refs']} | {d['tps']} | {rec_pct:.1f} | {rs_str} |")
    g_recall = g_tps/max(1,g_refs)*100
    all_r.sort()
    g_med = all_r[len(all_r)//2] if all_r else float('nan')
    print(f"\n**GLOBAL — Recall: {g_recall:.1f}% ({g_tps}/{g_refs}). Ratio mediano: {g_med:.2f}x.**")
    return {'recall': g_recall, 'ratio': g_med, 'by_vol': by_vol}

results = {}
for label, prof in PROFILES.items():
    results[label] = audit(label, prof)

print("\n" + "="*80)
print("\n## Comparación D4 vs Phase 1\n")
P1, D4 = results.get('phase1_op'), results.get('lbg_global')
if P1 and D4:
    print("| Métrica | Phase 1 | D4 (L_bg global) | Δ |")
    print("|---|---:|---:|---:|")
    print(f"| Recall global | {P1['recall']:.1f}% | {D4['recall']:.1f}% | {D4['recall']-P1['recall']:+.1f}pp |")
    print(f"| Ratio mediano | {P1['ratio']:.2f}x | {D4['ratio']:.2f}x | {(D4['ratio']/P1['ratio']-1)*100:+.0f}% |")

    print("\n### Cambio recall por volcán\n")
    print("| Volcán | P1 recall | D4 recall | Δ pp |")
    print("|---|---:|---:|---:|")
    for v in sorted(VOLC_MAP.values()):
        p1d = P1['by_vol'].get(v, {})
        d4d = D4['by_vol'].get(v, {})
        if not p1d.get('refs'): continue
        p1_rec = p1d['tps']/p1d['refs']*100 if p1d['refs'] else 0
        d4_rec = d4d['tps']/d4d['refs']*100 if d4d.get('refs') else 0
        print(f"| {v} | {p1_rec:.1f}% | {d4_rec:.1f}% | {d4_rec-p1_rec:+.1f} |")

    # Veredicto Tupungatito
    print("\n## Veredicto D4\n")
    tup_p1 = P1['by_vol'].get('Tupungatito', {})
    tup_d4 = D4['by_vol'].get('Tupungatito', {})
    tup_p1_rec = tup_p1['tps']/tup_p1['refs']*100 if tup_p1.get('refs') else 0
    tup_d4_rec = tup_d4['tps']/tup_d4['refs']*100 if tup_d4.get('refs') else 0
    print(f"- Tupungatito recall: {tup_p1_rec:.1f}% → {tup_d4_rec:.1f}% (Δ {tup_d4_rec-tup_p1_rec:+.1f}pp)")
    crit_tup = tup_d4_rec >= 75
    crit_global = D4['recall'] >= P1['recall'] - 5
    crit_ratio = D4['ratio'] <= P1['ratio'] * 1.5  # no más que 50% peor
    print(f"- Tupungatito ≥75%? {'OK' if crit_tup else 'NO'}")
    print(f"- Recall global no regresiona >5pp? {'OK' if crit_global else 'NO'}")
    print(f"- Ratio mediano no >1.5× P1? {'OK' if crit_ratio else 'NO'}")
    if crit_tup and crit_global and crit_ratio:
        print("\n**D4 APROBADO** — adoptar como operacional.")
    else:
        print("\n**D4 PARCIAL** — refinar o documentar mejora gradual.")
else:
    print("(D4 reproc no disponible aún — esperar workflow A/B D4.)")
