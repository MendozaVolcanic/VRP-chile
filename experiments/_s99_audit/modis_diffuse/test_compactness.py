"""S101 — Validacion del discriminante de COMPACIDAD para el frente MODIS.

Hipotesis: un foco real (crater O flanco) concentra su energia (alta compacidad);
el campo difuso (contraste nieve/nube) la reparte por la escena (baja compacidad).
Compacidad = fraccion de energia VRP dentro de R_km del centro de masa de energia.

Cruce contra MIROVA (latest_consolidado ALERTA_TERMICA MODIS, matched dia):
- records MIROVA-confirmados deberian tener ALTA compacidad (foco real).
- records inflados SIN MIROVA deberian tener BAJA compacidad (difuso).

Fuente de numeros: este script (S91). Output stdout + JSON.
"""
import json, csv, math, statistics
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
R_COMPACT = 3.0  # km

def hav(a, b, c, d):
    R = 6371; r = math.pi / 180
    p1, p2 = a * r, c * r; dp = (c - a) * r; dl = (d - b) * r
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))

def compactness(aps):
    """% de energia dentro de R_COMPACT del centro de masa de energia."""
    pts = [(p['lat'], p['lon'], p.get('vrp_mw', 0) or 0) for p in aps
           if p.get('lat') is not None and (p.get('vrp_mw') or 0) > 0]
    if not pts:
        return None, 0
    W = sum(v for _, _, v in pts)
    if W <= 0:
        return None, 0
    clat = sum(la * v for la, lo, v in pts) / W
    clon = sum(lo * v for la, lo, v in pts) / W
    e_in = sum(v for la, lo, v in pts if hav(la, lo, clat, clon) <= R_COMPACT)
    return e_in / W, W

# MIROVA MODIS ALERTA por (vol, dia)
mir = defaultdict(list)
for row in csv.DictReader(open(REPO / 'latest_consolidado.csv', encoding='utf-8')):
    if row['Sensor'] == 'MODIS' and row['Tipo_Registro'] == 'ALERTA_TERMICA':
        try:
            mir[(row['Volcan'], row['Fecha_Satelite_UTC'][:10])].append(float(row['VRP_MW']))
        except ValueError:
            pass
namemap = {'PuyehueCordonCaulle': 'Puyehue-Cordon Caulle', 'NevadosDeChillan': 'Nevados de Chillan'}
VOLS = ['Lascar', 'PuyehueCordonCaulle', 'Tupungatito', 'Chaiten', 'Villarrica', 'Llaima',
        'PlanchonPeteroa', 'Copahue', 'Isluga', 'Lastarria', 'NevadosDeChillan']

# Acumular por categoria: (con MIROVA-MODIS) vs (sin), bucketeado por compacidad
conf_comp, noconf_comp = [], []  # compacidad de records con/ sin MIROVA matched
big_noconf = []  # inflados (pc>20) sin MIROVA: compacidad
detail = {}
for vol in VOLS:
    p = REPO / 'data/mirova_equivalent' / f'{vol}.json'
    if not p.exists():
        continue
    o = json.load(open(p, encoding='utf-8'))
    recs = o['records'] if isinstance(o, dict) else o
    mname = namemap.get(vol, vol)
    vol_conf, vol_big = [], []
    for r in recs:
        if not r.get('sensor', '').startswith('MODIS'):
            continue
        pc = r.get('primary_cluster') or {}
        v = pc.get('vrp_mw', 0) or 0
        if v <= 0:
            continue
        comp, W = compactness(r.get('anomaly_pixels') or [])
        if comp is None:
            continue
        day = str(r.get('datetime_utc', ''))[:10]
        has_mir = (mname, day) in mir
        if has_mir:
            conf_comp.append(comp); vol_conf.append(round(comp, 2))
        else:
            noconf_comp.append(comp)
            if v > 20:
                big_noconf.append(comp); vol_big.append(round(comp, 2))
    detail[vol] = {'n_conf': len(vol_conf), 'comp_conf': vol_conf[:8],
                   'n_big_noconf': len(vol_big),
                   'comp_big_noconf_median': round(statistics.median(vol_big), 3) if vol_big else None}

def pct(lst, thr, ge=True):
    if not lst:
        return None
    return round(100 * sum(1 for x in lst if (x >= thr if ge else x < thr)) / len(lst))

print(f"=== Discriminante COMPACIDAD (energia dentro de {R_COMPACT}km del centro-energia) ===\n")
print(f"Records CON MIROVA-MODIS confirmado (n={len(conf_comp)}):")
if conf_comp:
    print(f"  compacidad mediana={statistics.median(conf_comp):.2f}  "
          f">=50%: {pct(conf_comp,0.5)}%  >=80%: {pct(conf_comp,0.8)}%")
print(f"Records SIN MIROVA-MODIS (n={len(noconf_comp)}):")
if noconf_comp:
    print(f"  compacidad mediana={statistics.median(noconf_comp):.2f}  "
          f"<50%: {pct(noconf_comp,0.5,ge=False)}%  <20%: {pct(noconf_comp,0.2,ge=False)}%")
print(f"Records INFLADOS (pc>20MW) SIN MIROVA (n={len(big_noconf)}):")
if big_noconf:
    print(f"  compacidad mediana={statistics.median(big_noconf):.2f}  "
          f"<50%: {pct(big_noconf,0.5,ge=False)}%  <20%: {pct(big_noconf,0.2,ge=False)}%")

print("\nPor volcan (n_conf / compacidad de los conf | n inflados>20 sin MIR / su compacidad med):")
for vol in VOLS:
    d = detail.get(vol, {})
    print(f"  {vol:<20} conf={d.get('n_conf',0):<3} {str(d.get('comp_conf',[]))[:42]:<44} "
          f"big_noconf={d.get('n_big_noconf',0):<3} medComp={d.get('comp_big_noconf_median')}")

json.dump({'conf_n': len(conf_comp), 'noconf_n': len(noconf_comp), 'big_noconf_n': len(big_noconf),
           'conf_median': round(statistics.median(conf_comp), 3) if conf_comp else None,
           'big_noconf_median': round(statistics.median(big_noconf), 3) if big_noconf else None,
           'detail': detail},
          open(Path(__file__).parent / 'test_compactness_result.json', 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)
print('\n-> test_compactness_result.json')
