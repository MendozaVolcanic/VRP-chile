# -*- coding: utf-8 -*-
"""S90 — prueba empírica del criterio de "artefacto incoherente" para ocultar del
gráfico (display-only, no toca pipeline). Diseño: brainstorming S90.

Métrica CRÍTICA de seguridad: de los records que el criterio ocultaría, ¿cuántos
tienen una alerta MIROVA REAL (CONS+OCR, universo completo)? DEBE ser 0 — nunca
ocultar algo que MIROVA publicó. Secundario: cuántos artefactos cirrus captura.

Replica el gate del dashboard (mirovaEqVrp summit) y el matching de computeMetrics
(±60min, mismo bucket de sensor). Cruza contra CONS (data/mirova) + OCR
(experiments/_s90_audit/ocr_universe.json)."""
import json, os, io, sys
from datetime import datetime
from collections import defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TIER_A = ['Chaiten','Copahue','Isluga','Lascar','Lastarria','Llaima',
          'NevadosDeChillan','PlanchonPeteroa','PuyehueCordonCaulle','Tupungatito','Villarrica']
INNER = {'Lastarria':3,'PlanchonPeteroa':3,'Copahue':4,'Lascar':5,'Isluga':5,
         'NevadosDeChillan':5,'Llaima':5,'Villarrica':5,'Chaiten':5,'Tupungatito':7,
         'PuyehueCordonCaulle':20}

def load(p):
    if not os.path.exists(p): return []
    d = json.load(open(p, encoding='utf-8')); return d.get('records', d) if isinstance(d, dict) else d

def bucket_ours(s):
    s = s or ''
    if s.startswith('MODIS'): return 'MODIS'
    if '750' in s: return 'VIIRS750'
    if s.startswith('VIIRS'): return 'VIIRS375'
    return None

def bucket_mir(s):
    s = (s or '').upper()
    if s == 'MODIS': return 'MODIS'
    if s == 'VIIRS375': return 'VIIRS375'
    if s == 'VIIRS': return 'VIIRS750'
    return None

def pt(s):
    try: return datetime.strptime((s or '')[:16], '%Y-%m-%d %H:%M')
    except: return None

def mirova_eq(r, inner):
    """Replica frontend mirovaEqVrp (Solo cráter): summit + pc dentro inner."""
    pc = r.get('primary_cluster')
    if not pc:
        v = r.get('vrp_mw') or 0; return v if v <= 50000 else 0
    dc = r.get('distance_class')
    if dc and dc != 'summit': return 0
    cd = pc.get('centroid_dist_km')
    if cd is not None and cd > inner: return 0
    v = pc.get('vrp_mw') or 0
    return v if v <= 50000 else 0

# OCR universe (construido en _s90_audit)
ocr = {}
ocr_path = os.path.join(BASE, 'experiments', '_s90_audit', 'ocr_universe.json')
if os.path.exists(ocr_path):
    ocr = json.load(open(ocr_path, encoding='utf-8'))

TOL_MIN = 60
def mirova_confirms(vol, dt, bucket, mir_recs):
    """¿Hay alerta MIROVA real (CONS+OCR) en ±60min mismo bucket?"""
    if dt is None: return False
    for m in mir_recs:
        cls = str(m.get('clasificacion','')).upper()
        if cls in ('NULO','RUTINA'): continue
        if not (float(m.get('VRP_MW') or 0) > 0): continue
        if bucket_mir(m.get('sensor')) != bucket: continue
        mdt = pt(m.get('datetime_utc'))
        if mdt and abs((mdt - dt).total_seconds()) <= TOL_MIN*60:
            return True
    return False

# combos (nombre, t_max_thresh_K, vrp_floor_MW)
COMBOS = [
    ('tmax<273 & vrp>0',   273.15, 0.0),
    ('tmax<273 & vrp>10',  273.15, 10.0),
    ('tmax<273 & vrp>20',  273.15, 20.0),
    ('tmax<268 & vrp>0',   268.15, 0.0),
    ('tmax<268 & vrp>10',  268.15, 10.0),
]
total_shown = 0
confirmed_total = 0
# por combo: hidden (no-conf), y CRÍTICO: confirmados que el criterio físico atraparía
stats = {name: {'hidden':0, 'confirmed_caught':0, 'hidden_hi_examples':[]} for name,_,_ in COMBOS}
per_vol = defaultdict(lambda: defaultdict(int))
for vol in TIER_A:
    inner = INNER.get(vol, 10)
    ours = load(os.path.join(BASE,'data','mirova_equivalent', vol+'.json'))
    mir = load(os.path.join(BASE,'data','mirova', vol+'.json')) + ocr.get(vol, [])
    for r in ours:
        eq = mirova_eq(r, inner)
        if eq <= 0: continue
        total_shown += 1
        dt = pt(r.get('datetime_utc')); bk = bucket_ours(r.get('sensor'))
        confirmed = mirova_confirms(vol, dt, bk, mir)
        if confirmed: confirmed_total += 1
        tmax = r.get('t_max_k')
        for name, thr, floor in COMBOS:
            phys = (tmax is not None) and (tmax < thr) and (eq > floor)
            if confirmed and phys:
                stats[name]['confirmed_caught'] += 1  # CRÍTICO: debe ser 0
            if (not confirmed) and phys:
                stats[name]['hidden'] += 1
                per_vol[name][vol] += 1
                if eq > 20 and len(stats[name]['hidden_hi_examples']) < 6:
                    stats[name]['hidden_hi_examples'].append(
                        f"{vol} {r.get('datetime_utc')} {r.get('sensor')} eq={eq:.0f}MW tmax={tmax:.0f}K")

lines = []
def out(s=''): lines.append(s)
out(f"Total mostrados en dashboard (mirovaEqVrp>0, Solo cráter): {total_shown}")
out(f"De ellos confirmados por MIROVA (CONS+OCR, ±60min, mismo bucket): {confirmed_total}")
out("")
out("CRITERIO = (NO confirmado) Y (t_max < thr) Y (VRP > floor).")
out("SEGURIDAD = #MIROVA-confirmadas que el criterio FÍSICO (thr,floor) atraparía.")
out("  DEBE ser 0 — si 0, ni siquiera la cláusula not-confirmed es necesaria para esos.")
out("")
out(f"{'Combo':22s} {'ocultaría':>10s} {'confirmadas atrapadas (=0!)':>28s}")
for name,_,_ in COMBOS:
    s = stats[name]
    out(f"{name:22s} {s['hidden']:>10d} {s['confirmed_caught']:>28d}")
out("")
for name,_,_ in COMBOS:
    out(f"--- {name}: por volcán --- {dict(per_vol[name])}")
    for ex in stats[name]['hidden_hi_examples']:
        out(f"    ej (>20MW): {ex}")
    out("")
open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'test_criterion.txt'),'w',encoding='utf-8').write('\n'.join(lines))
print('\n'.join(lines))
