"""S32 P3+ — comparar recall global (vrp_mw>0) vs summit-only (Driver A) por volcán.

Hallazgo P3 Lascar: recall MODIS cae de 60.7% a 8.2% cuando aplicamos
mirovaEqVrp summit-only. Pregunta: ¿afecta solo Lascar o todos los Tier A?

Si Lascar es caso especial (Salar de Atacama coincidiendo temporalmente con
detecciones MIROVA del cráter), Driver A es correcto en filtrarlas.
Si afecta a todos, Driver A es demasiado restrictivo.
"""
from __future__ import annotations
import json, sys, io
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path("C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
CSV = ROOT / "01_05_2026_registro_vrp_consolidado.csv"
DATA = ROOT / "data" / "mirova_equivalent"

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

def mirova_eq_vrp(r):
    if not r: return 0
    pc = r.get('primary_cluster')
    if not pc: return r.get('vrp_mw') or 0
    if r.get('distance_class') and r.get('distance_class') != 'summit': return 0
    return pc.get('vrp_mw', 0)


df = pd.read_csv(CSV)
df['dt'] = df['Fecha_Satelite_UTC'].apply(parse_csv_dt)
df = df[(df['dt'] >= START_DT) & (df['dt'] <= END_DT)]
df = df[df['Volcan'].isin(VOLC_MAP.keys())]
df = df[df['Tipo_Registro'] == 'ALERTA_TERMICA']

print(f"# Recall global (vrp_mw>0) vs summit-only (Driver A) por volcán × sensor\n")
print(f"Window: {START_DT.date()} -> {END_DT.date()}")
print(f"Refs MIROVA ALERTA_TERMICA: {len(df)}\n")

print("| Volcán | Sensor | Refs | TP global | TP summit | Recall global | Recall summit | Δ pp |")
print("|---|---|---:|---:|---:|---:|---:|---:|")

for csv_v, our_v in VOLC_MAP.items():
    f = DATA / f"{our_v}.json"
    if not f.exists(): continue
    recs = []
    for r in json.loads(f.read_text(encoding='utf-8')).get('records', []):
        try: dt = parse_rec_dt(r['datetime_utc'])
        except: continue
        if START_DT <= dt <= END_DT:
            r['_dt'] = dt; recs.append(r)
    sub = df[df['Volcan']==csv_v]
    for sensor_label, sensor_match_fn in [('MODIS', lambda s: sensor_match('MODIS', s)),
                                           ('VIIRS750', lambda s: sensor_match('VIIRS', s)),
                                           ('VIIRS375', lambda s: sensor_match('VIIRS375', s))]:
        sub_s = sub[sub['Sensor'] == ('MODIS' if sensor_label=='MODIS' else
                                       'VIIRS' if sensor_label=='VIIRS750' else 'VIIRS375')]
        if sub_s.empty: continue
        tp_g, tp_s, n_refs = 0, 0, len(sub_s)
        for _, row in sub_s.iterrows():
            tol = timedelta(minutes=TOL_MIN)
            best, bd = None, tol + timedelta(seconds=1)
            for r in recs:
                if not sensor_match_fn(r.get('sensor','')): continue
                d = abs(r['_dt']-row['dt'])
                if d <= tol and d < bd: best, bd = r, d
            if best is None: continue
            if (best.get('vrp_mw') or 0) > 0: tp_g += 1
            if mirova_eq_vrp(best) > 0: tp_s += 1
        rec_g = tp_g/n_refs*100 if n_refs else 0
        rec_s = tp_s/n_refs*100 if n_refs else 0
        delta = rec_s - rec_g
        flag = " ⚠️" if delta < -20 else ""
        print(f"| {our_v} | {sensor_label} | {n_refs} | {tp_g} | {tp_s} | "
              f"{rec_g:.1f}% | {rec_s:.1f}% | {delta:+.1f}{flag} |")

print(f"\n## Interpretación\n")
print("- Δ pp negativo = summit-only (Driver A) pierde recall vs global. ⚠️ si <-20pp.")
print("- TP global = nuestro vrp_mw>0 coincide temporalmente con ALERTA_TERMICA MIROVA.")
print("- TP summit = nuestro primary_cluster está dentro inner_radius_km del cráter.")
print("- Caso esperado: TP summit < TP global (algunos clusters lejos cráter).")
print("- Caso peligroso: TP summit << TP global (la mayoría de detecciones lejos cráter).")
