# -*- coding: utf-8 -*-
"""S90 — construye records OCR por volcán en el esquema del dashboard
({datetime_utc, sensor, VRP_MW, distancia_km, clasificacion, source}) para
inyectar y medir recall CONS+OCR con la computeMetrics real. Dedupe contra CONS
(mismo bucket ±30min). Excluye FALSO_POSITIVO_OCR y NULO/RUTINA (no son alertas)."""
import csv, json, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# A14: variantes de nombre OCR -> nombre nuestro
NAME = {
  'Lascar':'Lascar','Isluga':'Isluga','Puyehue-Cordon Caulle':'PuyehueCordonCaulle',
  'Lastarria':'Lastarria','PlanchonPeteroa':'PlanchonPeteroa','Tupungatito':'Tupungatito',
  'Chaiten':'Chaiten','Villarrica':'Villarrica','Nevados de Chillan':'NevadosDeChillan',
  'Copahue':'Copahue','Llaima':'Llaima',
}
def bucket(s):
    s=(s or '').upper()
    if s=='MODIS': return 'MODIS'
    if s=='VIIRS375': return 'VIIRS375'
    if s=='VIIRS': return 'VIIRS750'
    return None
def to_min(s):  # "2026-03-28 07:50:00" -> epoch-ish minutos para dedup
    from datetime import datetime
    try: return datetime.strptime(s[:16],'%Y-%m-%d %H:%M')
    except: return None

# OCR rows -> por volcán
ocr_by_vol = {v:[] for v in NAME.values()}
with open(os.path.join(BASE,'data','mirova_reference','registro_vrp_ocr.csv'), encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row.get('Tipo_Registro') != 'ALERTA_TERMICA_OCR': continue
        cls = (row.get('Clasificacion Mirova') or '').upper()
        if cls in ('NULO','RUTINA'): continue
        try: vrp = float(row.get('VRP_MW') or 0)
        except: vrp = 0
        if not (vrp>0): continue
        vol = NAME.get(row.get('Volcan'))
        if not vol: continue
        if bucket(row.get('Sensor')) is None: continue
        dt = (row.get('Fecha_Satelite_UTC') or '')[:16]  # "YYYY-MM-DD HH:MM"
        try: dist = float(row.get('Distancia_km'))
        except: dist = None
        # OCR distancia_km suele ser 0.0 placeholder -> None (poco confiable, A11)
        ocr_by_vol[vol].append({
          'datetime_utc': dt, 'sensor': row.get('Sensor'), 'VRP_MW': vrp,
          'distancia_km': (dist if (dist and dist>0) else None),
          'clasificacion': row.get('Clasificacion Mirova'), 'source':'ocr'
        })

# dedup contra CONS (mismo bucket, ±30 min)
out = {}
summary = []
for vol, ocrs in ocr_by_vol.items():
    cons_path = os.path.join(BASE,'data','mirova', vol+'.json')
    cons = []
    if os.path.exists(cons_path):
        d = json.load(open(cons_path, encoding='utf-8')); cons = d.get('records',d) if isinstance(d,dict) else d
    cons_keys = []
    for c in cons:
        t = to_min(c.get('datetime_utc',''))
        if t: cons_keys.append((bucket(c.get('sensor')), t))
    kept = []
    dropped_dup = 0
    for o in ocrs:
        t = to_min(o['datetime_utc']); b = bucket(o['sensor'])
        dup = any(bb==b and abs((t-tt).total_seconds())<=1800 for bb,tt in cons_keys)
        if dup: dropped_dup += 1; continue
        kept.append(o)
    out[vol] = kept
    summary.append((vol, len(cons), len(ocrs), dropped_dup, len(kept)))

json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'ocr_universe.json'),'w',encoding='utf-8'), ensure_ascii=False)
print('vol                  CONS  OCRraw  dupCONS  OCRnew')
for v,c,o,dd,k in sorted(summary, key=lambda x:-x[4]):
    print(f'  {v:20s} {c:5d}  {o:5d}   {dd:5d}   {k:5d}')
print('OCR new total:', sum(s[4] for s in summary))
