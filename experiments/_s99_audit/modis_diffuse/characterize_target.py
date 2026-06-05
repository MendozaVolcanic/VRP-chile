"""S101 — Target de fidelidad MIROVA-MODIS (fuente de la tabla §2 del design doc).

Qué detecta MIROVA desde MODIS, período completo, consolidado + OCR. Es el criterio
de aceptación del frente MODIS: nuestro pipeline debe quedar tan parco como esto.
Fuente de números S91: este script. Output stdout + JSON.
"""
import csv, glob, statistics
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

# --- Consolidado: ALERTA_TERMICA MODIS por volcán ---
cons = defaultdict(list)
rng = [None, None]
for r in csv.DictReader(open(REPO / 'latest_consolidado.csv', encoding='utf-8')):
    if r['Sensor'] != 'MODIS':
        continue
    d = r['Fecha_Satelite_UTC'][:10]
    rng[0] = d if rng[0] is None or d < rng[0] else rng[0]
    rng[1] = d if rng[1] is None or d > rng[1] else rng[1]
    if r['Tipo_Registro'] != 'ALERTA_TERMICA':
        continue
    try:
        cons[r['Volcan']].append((float(r['VRP_MW']), float(r['Distancia_km']), r['Clasificacion Mirova']))
    except ValueError:
        pass

# --- OCR: ALERTA MODIS (complemento, dedup vol+fecha) ---
ocr = defaultdict(set)
ocr_vrp = defaultdict(list)
_ocr_paths = (glob.glob(str(REPO / '*registro_vrp_ocr.csv'))
              + [str(REPO / 'data/mirova_reference/registro_vrp_ocr.csv'),
                 str(REPO / 'data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv')])
for path in _ocr_paths:
    try:
        rows = list(csv.DictReader(open(path, encoding='utf-8')))
    except OSError:
        continue
    for r in rows:
        if r.get('Sensor') != 'MODIS':
            continue
        try:
            v = float(r.get('VRP_MW', 0))
        except ValueError:
            continue
        if v <= 0 and 'ALERTA' not in r.get('Tipo_Registro', ''):
            continue
        key = (r['Volcan'], r['Fecha_Satelite_UTC'][:10])
        if key not in ocr[r['Volcan']]:
            ocr[r['Volcan']].add(key)
            ocr_vrp[r['Volcan']].append(v)

print(f"=== Target MIROVA-MODIS (período {rng[0]}..{rng[1]}) ===")
print(f"{'Volcan':<22}{'CONS':>5}{'OCR':>5}  VRP_MW cons(min/med/max)   Dist(med/max)  clases")
out = {'periodo': rng, 'cons': {}, 'ocr': {}}
tot = 0
for vol in sorted(set(cons) | set(ocr), key=lambda v: -len(cons.get(v, []))):
    cs = cons.get(vol, [])
    tot += len(cs)
    if cs:
        vrps = [x[0] for x in cs]; dists = [x[1] for x in cs if x[1] >= 0]
        clas = defaultdict(int)
        for x in cs:
            clas[x[2]] += 1
        md = statistics.median(dists) if dists else -1
        print(f"{vol:<22}{len(cs):>5}{len(ocr.get(vol,[])):>5}  "
              f"{min(vrps):.1f}/{statistics.median(vrps):.1f}/{max(vrps):.1f}      "
              f"{md:.1f}/{max(dists) if dists else -1:.1f}    {dict(clas)}")
        out['cons'][vol] = {'n': len(cs), 'vrp_min': round(min(vrps), 2),
                            'vrp_med': round(statistics.median(vrps), 2), 'vrp_max': round(max(vrps), 2),
                            'dist_med': round(md, 2)}
    else:
        print(f"{vol:<22}{0:>5}{len(ocr.get(vol,[])):>5}  (solo OCR: {sorted(ocr_vrp.get(vol,[]))})")
    if ocr.get(vol):
        out['ocr'][vol] = {'n': len(ocr[vol]), 'vrp_max': round(max(ocr_vrp[vol]), 1)}

print(f"\nTOTAL ALERTA_TERMICA MODIS (CONS): {tot}")
print("Cero MODIS (CONS+OCR):", sorted(
    set(['Isluga', 'Lastarria', 'PlanchonPeteroa', 'Puyehue-Cordon Caulle', 'Tupungatito']) - set(cons) - set(ocr)))
import json
json.dump(out, open(Path(__file__).parent / 'characterize_target_result.json', 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)
print('\n-> characterize_target_result.json')
