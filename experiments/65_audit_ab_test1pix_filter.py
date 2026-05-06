"""S32 P2 Driver B — audit comparativo A/B test1 pixel filter.

Compara `data/mirova_equivalent_test1pix_filter/<vol>.json` (flag ON) vs
`data/mirova_equivalent_test1pix_disabled/<vol>.json` (flag OFF, control)
contra el CSV consolidado MIROVA NRT.

Métricas reportadas por volcán y global:
- Recall (TPs / refs MIROVA)
- Ratio mediano nuestro/MIROVA (sobre TPs con VRP>0 ambos)
- Mediana MW MIROVA / mediana MW nuestro
- Cantidad records con vrp_mw>0
- Cantidad records que dispararon Test 1

Criterio aceptación (plan S32 P2 Driver B):
- Recall global >= 83.5% (paridad con S31+ baseline).
- Ratio mediano global <= 1.5x.
- Ningún volcán cae a sub-detección <0.3x mediana.
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
    "filter_ON":  ROOT / "data" / "mirova_equivalent_test1pix_filter",
    "filter_OFF": ROOT / "data" / "mirova_equivalent_test1pix_disabled",
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


def parse_csv_dt(s):
    return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
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


df = pd.read_csv(CSV)
df['dt'] = df['Fecha_Satelite_UTC'].apply(parse_csv_dt)
df = df[(df['dt'] >= START_DT) & (df['dt'] <= END_DT)]
df = df[df['Volcan'].isin(VOLC_MAP.keys())]
df_alerta = df[df['Tipo_Registro'] == 'ALERTA_TERMICA']
print(f"# Audit A/B test1 pixel filter\n")
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
        delta = abs(r['_dt'] - ref_dt)
        if delta <= tol and delta < bd: best, bd = r, delta
    return best


INNER_RADIUS_KM = {
    'Lascar': 5, 'Lastarria': 3, 'Tupungatito': 7, 'Villarrica': 5,
    'PuyehueCordonCaulle': 20, 'Copahue': 4, 'NevadosDeChillan': 5,
    'Llaima': 5, 'Chaiten': 5, 'PlanchonPeteroa': 3, 'Isluga': 5,
}

def vrp_summit_only(rec, volc=None):
    """Replica de mirovaEqVrp del frontend con fix S33.
    Bug pre-S33: distance_class='summit' (final_hotspot Test1 cerca) pero
    primary_cluster a 24km en Salar daba pc.vrp_mw inflado del Salar.
    Fix: validar pc.centroid_dist_km <= inner_radius_km del volcán."""
    if not rec: return 0
    pc = rec.get('primary_cluster')
    if not pc: return rec.get('vrp_mw') or 0
    if rec.get('distance_class') and rec.get('distance_class') != 'summit': return 0
    inner_km = INNER_RADIUS_KM.get(volc, 10)
    pc_dist = pc.get('centroid_dist_km')
    if pc_dist is not None and pc_dist > inner_km:
        return 0
    return pc.get('vrp_mw', 0)


def audit_profile(label, profile_dir):
    print(f"\n## Profile: {label}\n")
    if not profile_dir.exists():
        print(f"❌ Dir {profile_dir} no existe — workflow no completado o failed")
        return None
    by_vol = defaultdict(lambda: {'refs':0,'tps':0,'ratios':[],'mirova_vrp':[],'our_vrp':[],'n_test1':0})
    for csv_v, our_v in VOLC_MAP.items():
        recs = load_recs(profile_dir, our_v)
        sub = df_alerta[df_alerta['Volcan'] == csv_v]
        for _, row in sub.iterrows():
            by_vol[our_v]['refs'] += 1
            rec = find_match(row['dt'], row['Sensor'], recs)
            if rec is None: continue
            our_vrp = vrp_summit_only(rec, our_v)
            if our_vrp > 0:
                by_vol[our_v]['tps'] += 1
                if row['VRP_MW'] > 0:
                    by_vol[our_v]['ratios'].append(our_vrp / row['VRP_MW'])
                    by_vol[our_v]['mirova_vrp'].append(row['VRP_MW'])
                    by_vol[our_v]['our_vrp'].append(our_vrp)
            if rec.get('triggered_test1'):
                by_vol[our_v]['n_test1'] += 1
    # Tabla
    print("| Volcán | Refs | TPs | Recall % | Ratio med | mediana MIROVA MW | mediana nuestro MW | n_T1 |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    g_refs, g_tps, all_ratios = 0, 0, []
    for v, d in sorted(by_vol.items()):
        g_refs += d['refs']; g_tps += d['tps']
        all_ratios.extend(d['ratios'])
        recall = (d['tps']/d['refs']*100) if d['refs'] else 0.0
        rs = sorted(d['ratios'])
        med_r = rs[len(rs)//2] if rs else float('nan')
        ms = sorted(d['mirova_vrp'])
        med_m = ms[len(ms)//2] if ms else float('nan')
        os_ = sorted(d['our_vrp'])
        med_o = os_[len(os_)//2] if os_ else float('nan')
        print(f"| {v} | {d['refs']} | {d['tps']} | {recall:.1f} | "
              f"{med_r:.2f}" if rs else f"| {v} | {d['refs']} | {d['tps']} | {recall:.1f} | NA |"
              + f" | {med_m:.3f} | {med_o:.3f} | {d['n_test1']} |"
              if rs else "")
    g_recall = g_tps/max(1,g_refs)*100
    all_ratios.sort()
    g_med = all_ratios[len(all_ratios)//2] if all_ratios else float('nan')
    print(f"\n**GLOBAL — Recall: {g_recall:.1f}% ({g_tps}/{g_refs}). "
          f"Ratio mediano: {g_med:.2f}x (n={len(all_ratios)}).**")
    return {'recall': g_recall, 'ratio': g_med, 'n_tps': g_tps, 'n_refs': g_refs}


print("="*80)
results = {}
for label, prof_dir in PROFILES.items():
    results[label] = audit_profile(label, prof_dir)

print("\n" + "="*80)
print("\n## Comparación final A vs B\n")
print("| Métrica | filter_OFF (control) | filter_ON (experimental) | Δ |")
print("|---|---:|---:|---:|")
ON, OFF = results.get('filter_ON'), results.get('filter_OFF')
if ON and OFF:
    print(f"| Recall global | {OFF['recall']:.1f}% | {ON['recall']:.1f}% | "
          f"{ON['recall']-OFF['recall']:+.1f} pp |")
    print(f"| Ratio mediano | {OFF['ratio']:.2f}x | {ON['ratio']:.2f}x | "
          f"{(ON['ratio']/OFF['ratio']-1)*100:+.0f}% |")

    # Verdict
    print("\n## Veredicto\n")
    crit_recall = ON['recall'] >= 83.5
    crit_ratio = ON['ratio'] <= 1.5
    print(f"- Recall ≥83.5%? **{'OK' if crit_recall else 'NO'}** ({ON['recall']:.1f}%)")
    print(f"- Ratio ≤1.5x?   **{'OK' if crit_ratio else 'NO'}** ({ON['ratio']:.2f}x)")
    if crit_recall and crit_ratio:
        print("\n**APROBADO** — fix Driver B valida hipótesis. Considerar adoptar como operacional.")
    else:
        print("\n**NO APROBADO** — analizar por qué falla criterio. Driver B requiere refinamiento.")
else:
    print("Datos incompletos — esperar workflow completo.")
