"""S101 — Prueba decisiva frente MODIS: ¿recupera la magnitud sumar solo los
pixeles cerca del crater (nucleo geografico) en vez del cluster entero?

Hipotesis: Lascar (foco real al crater) -> VRP_crater ~ MIROVA (1-4 MW);
PCC/Tupungatito (campo difuso disperso) -> VRP_crater colapsa ~0.
Fuente de numeros: este script (S91, no transcribir). Output -> stdout + JSON.
"""
import json, yaml, csv, math, statistics
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

y = yaml.safe_load(open(REPO / 'volcanoes.yaml', encoding='utf-8'))
vols = y['volcanoes'] if 'volcanoes' in y else y
vols = vols if isinstance(vols, list) else list(vols.values())
vent = {}
for v in vols:
    n = v.get('name') or v.get('id')
    if v.get('vent_lat') is not None:
        vent[n] = (v['vent_lat'], v['vent_lon'])


def hav(a, b, c, d):
    R = 6371; r = math.pi / 180
    p1, p2 = a * r, c * r; dp = (c - a) * r; dl = (d - b) * r
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


# MIROVA MODIS ALERTA por (vol, dia)
mir = defaultdict(list)
for row in csv.DictReader(open(REPO / 'latest_consolidado.csv', encoding='utf-8')):
    if row['Sensor'] != 'MODIS' or row['Tipo_Registro'] != 'ALERTA_TERMICA':
        continue
    try:
        mir[(row['Volcan'], row['Fecha_Satelite_UTC'][:10])].append(float(row['VRP_MW']))
    except ValueError:
        pass

namemap = {'PuyehueCordonCaulle': 'Puyehue-Cordon Caulle',
           'NevadosDeChillan': 'Nevados de Chillan'}
VOLS = ['Lascar', 'PuyehueCordonCaulle', 'Tupungatito', 'Chaiten', 'Villarrica',
        'Llaima', 'PlanchonPeteroa', 'Copahue', 'Isluga', 'Lastarria', 'NevadosDeChillan']

out = {}
print(f"{'Volcan':<20}{'nMOD':>5}{'med_pc':>8}{'med_cr2':>8}{'med_cr3':>8}{'max_cr2':>8}  dias MIROVA-MODIS (pc/cr2 vs MIR)")
for vol in VOLS:
    p = REPO / 'data/mirova_equivalent' / f'{vol}.json'
    if not p.exists() or vol not in vent:
        continue
    o = json.load(open(p, encoding='utf-8'))
    recs = o['records'] if isinstance(o, dict) else o
    vlat, vlon = vent[vol]
    pcs, cr2, cr3, matched = [], [], [], []
    mname = namemap.get(vol, vol)
    for r in recs:
        if not r.get('sensor', '').startswith('MODIS'):
            continue
        pc = r.get('primary_cluster') or {}
        v = pc.get('vrp_mw', 0) or 0
        if v <= 0:
            continue
        aps = r.get('anomaly_pixels') or []
        s2 = sum(pp.get('vrp_mw', 0) or 0 for pp in aps
                 if pp.get('lat') is not None and hav(pp['lat'], pp['lon'], vlat, vlon) <= 2.0)
        s3 = sum(pp.get('vrp_mw', 0) or 0 for pp in aps
                 if pp.get('lat') is not None and hav(pp['lat'], pp['lon'], vlat, vlon) <= 3.0)
        pcs.append(v); cr2.append(s2); cr3.append(s3)
        day = str(r.get('datetime_utc', ''))[:10]
        if (mname, day) in mir:
            matched.append((day, round(v, 1), round(s2, 2), round(s3, 2), round(max(mir[(mname, day)]), 1)))

    def md(x):
        return round(statistics.median(x), 2) if x else 0
    ex = '  ' + ' '.join(f'{d[5:]}:pc{pc:.0f}/cr2{c2:.1f}vMIR{m:.1f}' for d, pc, c2, c3, m in matched[:5]) if matched else ''
    print(f'{vol:<20}{len(pcs):>5}{md(pcs):>8}{md(cr2):>8}{md(cr3):>8}{round(max(cr2),1) if cr2 else 0:>8}{ex}')
    out[vol] = {'n': len(pcs), 'med_pc': md(pcs), 'med_cr2': md(cr2), 'med_cr3': md(cr3),
                'max_cr2': round(max(cr2), 2) if cr2 else 0, 'matched': matched}

json.dump(out, open(Path(__file__).parent / 'test_crater_core_result.json', 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)
print('\n-> test_crater_core_result.json')
