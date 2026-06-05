"""S101 — Refinacion: validar CO-VALIDACION VIIRS375 como discriminante MODIS.

Hipotesis (plan S93 F3, scope S99 opcion C): un record MODIS es real si VIIRS375
tambien detecta al crater en +-ventana; si no, es artefacto de campo difuso.
MIROVA usa VIIRS375 de caballo. Auditoria: 74 TP MODIS 100% cubiertos por VIIRS375.

Para cada record MODIS con pc.vrp>0, busca si hay un record NUESTRO VIIRS375 'summit'
(distance_class==summit o centroid<=inner) en +-WIN dias. Cruza con:
  - MIROVA-MODIS confirmado (deberia tener co-val).
  - inflados >20MW sin MIROVA (deberia NO tener co-val -> co-val los suprime).

Convencion sensor (A48): VIIRS_{SNPP,NOAA20,NOAA21}=I-band 375m; *_750=M-band; MODIS_*.
Fuente S91: este script. Output stdout + JSON.
"""
import json, csv, math, statistics
from collections import defaultdict
from pathlib import Path
from datetime import date

REPO = Path(__file__).resolve().parents[3]
WIN = 1  # +-dias
INNER = {'Lascar': 5, 'PuyehueCordonCaulle': 20, 'Tupungatito': 7, 'Chaiten': 5,
         'Villarrica': 5, 'Llaima': 5, 'PlanchonPeteroa': 3, 'Copahue': 4,
         'Isluga': 5, 'Lastarria': 3, 'NevadosDeChillan': 5}

def is_v375(s):
    s = (s or '').upper()
    return s.startswith('VIIRS') and not s.endswith('_750')

def dnum(s):
    try:
        y, m, d = map(int, s[:10].split('-')); return date(y, m, d).toordinal()
    except Exception:
        return None

# MIROVA MODIS matched
mir = defaultdict(set)
for r in csv.DictReader(open(REPO / 'latest_consolidado.csv', encoding='utf-8')):
    if r['Sensor'] == 'MODIS' and r['Tipo_Registro'] == 'ALERTA_TERMICA':
        mir[r['Volcan']].add(r['Fecha_Satelite_UTC'][:10])
namemap = {'PuyehueCordonCaulle': 'Puyehue-Cordon Caulle', 'NevadosDeChillan': 'Nevados de Chillan'}
VOLS = list(INNER)

tot_conf = {'covalid': 0, 'no': 0}
tot_big = {'covalid': 0, 'no': 0}
detail = {}
for vol in VOLS:
    p = REPO / 'data/mirova_equivalent' / f'{vol}.json'
    if not p.exists():
        continue
    o = json.load(open(p, encoding='utf-8'))
    recs = o['records'] if isinstance(o, dict) else o
    inner = INNER[vol]
    # dias con VIIRS375 summit (nuestro)
    v375_days = set()
    for r in recs:
        if not is_v375(r.get('sensor', '')):
            continue
        pc = r.get('primary_cluster') or {}
        cd = pc.get('centroid_dist_km')
        summit = (r.get('distance_class') == 'summit') or (cd is not None and cd <= inner and (pc.get('vrp_mw', 0) or 0) > 0)
        if summit:
            dn = dnum(r.get('datetime_utc', ''))
            if dn:
                v375_days.add(dn)
    def has_coval(dn):
        return any((dn + k) in v375_days for k in range(-WIN, WIN + 1))
    mname = namemap.get(vol, vol)
    cconf = {'covalid': 0, 'no': 0}; cbig = {'covalid': 0, 'no': 0}
    for r in recs:
        if not r.get('sensor', '').startswith('MODIS'):
            continue
        v = (r.get('primary_cluster') or {}).get('vrp_mw', 0) or 0
        if v <= 0:
            continue
        dn = dnum(r.get('datetime_utc', ''))
        if dn is None:
            continue
        cov = has_coval(dn)
        day = str(r.get('datetime_utc', ''))[:10]
        if day in mir.get(mname, set()):
            (cconf['covalid' if cov else 'no']); cconf['covalid' if cov else 'no'] += 1
            tot_conf['covalid' if cov else 'no'] += 1
        elif v > 20:
            cbig['covalid' if cov else 'no'] += 1
            tot_big['covalid' if cov else 'no'] += 1
    detail[vol] = {'conf': cconf, 'big': cbig}

print(f"=== Co-validación VIIRS375 (±{WIN}d, summit) como discriminante MODIS ===\n")
nc = tot_conf['covalid'] + tot_conf['no']
nb = tot_big['covalid'] + tot_big['no']
print(f"MODIS CON MIROVA confirmado (foco real, n={nc}):")
print(f"   co-validados por VIIRS375: {tot_conf['covalid']} ({100*tot_conf['covalid']//nc if nc else 0}%)  "
      f"sin co-val: {tot_conf['no']}  <- co-val NO debería borrar estos")
print(f"\nMODIS inflados >20MW sin MIROVA (difuso?, n={nb}):")
print(f"   co-validados por VIIRS375: {tot_big['covalid']} ({100*tot_big['covalid']//nb if nb else 0}%)  "
      f"sin co-val: {tot_big['no']} ({100*tot_big['no']//nb if nb else 0}%)  <- co-val SÍ debería suprimir estos")
print("\nPor volcán [conf covalid/no | big covalid/no]:")
for vol in VOLS:
    d = detail.get(vol, {})
    c, b = d.get('conf', {}), d.get('big', {})
    print(f"  {vol:<20} conf {c.get('covalid',0)}/{c.get('no',0)}    big>20 {b.get('covalid',0)}/{b.get('no',0)}")

json.dump({'conf': tot_conf, 'big': tot_big, 'detail': detail, 'win': WIN},
          open(Path(__file__).parent / 'test_covalidation_result.json', 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)
print("\n-> test_covalidation_result.json")
