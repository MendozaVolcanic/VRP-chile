# -*- coding: utf-8 -*-
# FICHA SDA — Probe de auditoria S112 "barrido datos extranos" (READ-ONLY, no toca pipeline).
# POR QUE: un operador SERNAGEOMIN que mira el dashboard nota records "raros" (rojo lejos del
# crater, magnitud alta sin actividad MIROVA, sensor que MIROVA no ve). Este probe cuantifica
# esos patrones sobre los 11 Tier A (mayo-junio 2026) y clasifica cada cluster extrano segun el
# marco A54/A69/A23 para producir una lista priorizada de QUE limpiar SIN destruir cat-b real.
import json, csv, math, io, sys, os
from collections import defaultdict, Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, 'data', 'mirova_equivalent')
CONS = os.path.join(ROOT, 'experiments', '_s111_d11', 'mirova_fresh', 'cons.csv')
OCR = os.path.join(ROOT, 'experiments', '_s111_d11', 'mirova_fresh', 'ocr.csv')

DATE_MIN = '2026-05-01'
DATE_MAX = '2026-07-01'

# 11 Tier A: nombre repo -> (vent_lat, vent_lon, inner_radius_km, [variantes nombre en CSV])
TIER_A = {
    'Lascar':              (-23.36293,  -67.731416, 5,  ['Lascar']),
    'Lastarria':           (-25.168,    -68.507,    3,  ['Lastarria']),
    'Tupungatito':         (-33.389044, -69.826374, 7,  ['Tupungatito']),
    'PlanchonPeteroa':     (-35.241099, -70.573345, 3,  ['PlanchonPeteroa', 'Planchon-Peteroa', 'Planchon Peteroa']),
    'NevadosDeChillan':    (-36.863,    -71.377,    5,  ['Nevados de Chillan', 'NevadosDeChillan', 'Nevados de Chillán']),
    'Chaiten':             (-42.8344815,-72.6528875,5,  ['Chaiten', 'Chaitén']),
    'Villarrica':          (-39.420227, -71.939876, 5,  ['Villarrica']),
    'Llaima':              (-38.692,    -71.729,    5,  ['Llaima']),
    'Copahue':             (-37.856,    -71.183,    4,  ['Copahue']),
    'Isluga':              (-19.15,     -68.83,     5,  ['Isluga']),
    'PuyehueCordonCaulle': (-40.525499, -72.146137, 20, ['Puyehue-Cordon Caulle', 'PuyehueCordonCaulle', 'Puyehue-Cordón Caulle']),
}

# sensor del record -> bucket MIROVA ("MODIS" | "VIIRS750" | "VIIRS375")
def sensor_bucket(s):
    s = (s or '').upper()
    if 'MODIS' in s:
        return 'MODIS'
    if 'VIIRS' in s and s.endswith('_750'):
        return 'VIIRS750'
    if 'VIIRS' in s:
        return 'VIIRS375'  # I-band sin sufijo (convencion A48)
    return 'OTHER'

# sensor del CSV MIROVA: "MODIS" | "VIIRS" (=750m) | "VIIRS375"
def csv_bucket(s):
    s = (s or '').upper()
    if s == 'MODIS':
        return 'MODIS'
    if s == 'VIIRS375':
        return 'VIIRS375'
    if s == 'VIIRS':
        return 'VIIRS750'
    return 'OTHER'

def haversine(la1, lo1, la2, lo2):
    R = 6371.0
    p1, p2 = math.radians(la1), math.radians(la2)
    dp = math.radians(la2 - la1); dl = math.radians(lo2 - lo1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def bearing(la1, lo1, la2, lo2):
    # rumbo del vent hacia el hotspot
    p1, p2 = math.radians(la1), math.radians(la2)
    dl = math.radians(lo2 - lo1)
    x = math.sin(dl)*math.cos(p2)
    y = math.cos(p1)*math.sin(p2) - math.sin(p1)*math.cos(p2)*math.cos(dl)
    b = (math.degrees(math.atan2(x, y)) + 360) % 360
    dirs = ['N','NE','E','SE','S','SW','W','NW']
    return dirs[int((b+22.5)//45) % 8], round(b, 0)

# ---------------------------------------------------------------------------
# 1. Cargar ground truth MIROVA (cons + ocr): set de noches con CUALQUIER registro
#    (ALERTA/RUTINA/FALSO_POSITIVO) por (vol, fecha_dia, bucket_sensor)
#    y un set "publicado" = ALERTA o RUTINA con VRP>0 (MIROVA reporta magnitud).
# ---------------------------------------------------------------------------
def load_gt():
    # variante CSV -> nombre repo
    name2repo = {}
    for repo, (_, _, _, variants) in TIER_A.items():
        for v in variants:
            name2repo[v] = repo
    gt_any = defaultdict(set)   # (repo, day, bucket) -> set de tipos
    gt_vrp = defaultdict(list)  # (repo, day, bucket) -> [VRP_MW de ALERTA/RUTINA]
    for path in (CONS, OCR):
        with open(path, encoding='utf-8') as f:
            for row in csv.DictReader(f):
                repo = name2repo.get(row['Volcan'])
                if not repo:
                    continue
                dt = (row.get('Fecha_Satelite_UTC') or '')[:10]
                if not (DATE_MIN <= dt < DATE_MAX):
                    continue
                b = csv_bucket(row.get('Sensor'))
                tipo = row.get('Tipo_Registro', '')
                gt_any[(repo, dt, b)].add(tipo)
                try:
                    vrp = float(row.get('VRP_MW') or 0)
                except ValueError:
                    vrp = 0.0
                if tipo in ('ALERTA_TERMICA', 'RUTINA') and vrp > 0:
                    gt_vrp[(repo, dt, b)].append(vrp)
    return gt_any, gt_vrp

# ---------------------------------------------------------------------------
# 2. Clasificacion fisica de un cluster extrano.
#    Discriminantes (marco A69/A23/A54):
#      - A69 topografico: NTI plano (nti_std bajo) + nadir nevado/glaciar + offset direccional
#      - A23/D9 cirrus: t_bg muy frio (<260K) path-D dominante
#      - incendio regional: dist > inner & dist > ~5km, fuera del edificio
#      - cat-b real: cerca del crater, NTI con estructura, cruza halo difuso conocido
# ---------------------------------------------------------------------------
def classify(rec, repo, vent, inner, dist_eff):
    # Devuelve UNA etiqueta primaria (mas el detalle) segun marco A23/A69/A54.
    # Discriminante de fondo: la distancia del CLUSTER (centroid) al vent es la
    # ubicacion honesta (A73); fh_dist puede estar anclada al vent o al pico.
    t_bg = rec.get('t_bg_k')
    nti_std = rec.get('diag_nti_std')
    n_dnti = rec.get('diag_n_dnti_ctx_path') or 0
    n_bt = rec.get('diag_n_bt_path') or 0
    pc = rec.get('primary_cluster') or {}
    geo = pc.get('geo_class')
    c_dist = pc.get('centroid_dist_km')
    bucket = sensor_bucket(rec.get('sensor'))
    cd = c_dist if c_dist is not None else (dist_eff if dist_eff is not None else 999)

    # PCC laccolito: offset real cat-b (A20). El cluster cae en la zona del lacolito
    # Cordon Caulle (~3-9 km del vent Puyehue). inner=20 lo pinta summit (A68).
    if repo == 'PuyehueCordonCaulle' and 3.0 <= cd <= 10.0:
        return ['catB_lacolito_PCC', f'cdist={round(cd,1)}']
    # Cirrus A23/D9: fondo extremo frio + path D contextual domina (MODIS sobre todo).
    if t_bg is not None and t_bg < 262 and n_dnti and n_dnti >= max(1, n_bt):
        return ['cirrus_A23', f'tbg={round(t_bg,1)} dnti={n_dnti} bt={n_bt}']
    # Cluster lejano (>10 km) con NTI plano sobre fondo frio invernal = anomalia
    # regional / nevado (no edificio). VIIRS BT-path masivo tipico.
    if cd > 10.0:
        flat = (nti_std is not None and nti_std < 0.012)
        return ['regional_far_' + ('flatNTI' if flat else 'struct'),
                f'cdist={round(cd,1)} nti_std={nti_std} bt={n_bt}']
    # Campo difuso MODIS A69: MODIS, cerca-ish del crater, dnti-path, fondo tibio,
    # MIROVA MODIS lo ve ~0 (insensitive to diffuse heat).
    if bucket == 'MODIS' and n_dnti and n_dnti >= max(1, n_bt) and cd <= 8.0:
        return ['diffuse_MODIS_A69', f'cdist={round(cd,1)} dnti={n_dnti} tbg={round(t_bg,1) if t_bg else None}']
    # Topografico A69 sobre nevado/glaciar (VIIRS, NTI plano, cerca del crater).
    if bucket != 'MODIS' and nti_std is not None and nti_std < 0.006 and cd <= 8.0:
        return ['topo_A69_flatNTI', f'cdist={round(cd,1)} nti_std={nti_std}']
    # Resto cerca del crater = candidato cat-b real (no clasificable como artefacto).
    if cd <= max(inner, 5.0):
        return ['catB_near_crater?', f'cdist={round(cd,1)}']
    return ['unclassified', f'cdist={round(cd,1)}']

def main():
    gt_any, gt_vrp = load_gt()

    per_vol = {}
    weird_all = []  # records extranos individuales para ranking global

    for repo, (vlat, vlon, inner, _variants) in TIER_A.items():
        path = os.path.join(DATA, repo + '.json')
        d = json.load(open(path, encoding='utf-8'))
        recs = [r for r in d['records'] if DATE_MIN <= (r.get('datetime_utc') or '') < DATE_MAX]
        flags = Counter()
        bearings = Counter()
        sensor_mismatch = Counter()  # bucket -> n records nuestros sin GT MIROVA ese sensor
        for rec in recs:
            pc = rec.get('primary_cluster') or {}
            pcvrp = pc.get('vrp_mw') or 0.0
            dclass = rec.get('distance_class')
            fh_dist = rec.get('final_hotspot_dist_km')
            c_dist = pc.get('centroid_dist_km')
            # distancia efectiva al vent: preferir centroid del cluster (pc = lo que MIROVA reporta)
            dist_eff = c_dist if c_dist is not None else fh_dist
            bucket = sensor_bucket(rec.get('sensor'))
            day = (rec.get('datetime_utc') or '')[:10]
            # offset direccional desde el vent al final_hotspot
            fh_lat, fh_lon = rec.get('final_hotspot_lat'), rec.get('final_hotspot_lon')
            brg = None
            if fh_lat is not None and fh_lon is not None and (fh_dist or 0) > 0.3:
                brg = bearing(vlat, vlon, fh_lat, fh_lon)

            # solo nos interesan records con senal (pcvrp>0 o detecto algo)
            has_signal = pcvrp > 0 or (rec.get('triggered_test1')) or (rec.get('vrp_mw') or 0) > 0
            if not has_signal:
                continue

            # ---- (1) summit pero lejos (efecto inner grande, A68) ----
            cond_summit_far = (dclass == 'summit' and fh_dist is not None and fh_dist > 10.0)
            # ---- (1b) INCOHERENCIA A46: cluster lejano (geo=far / cdist>10) pero dclass=summit ----
            cond_incoherent = (dclass == 'summit' and c_dist is not None and c_dist > 10.0)
            # ---- (2) pc.vrp alto sin actividad fuerte MIROVA ese sensor ----
            gt_alerta = 'ALERTA_TERMICA' in gt_any.get((repo, day, bucket), set())
            cond_highvrp = (pcvrp > 10.0)
            # ---- (3) sensor inconsistente: nuestro sensor reporta, MIROVA ese sensor 0 ese dia ----
            gt_has_sensor = bool(gt_vrp.get((repo, day, bucket)))
            cond_sensor_mismatch = (pcvrp > 1.0 and not gt_has_sensor)
            # ---- (4) offset direccional grande del vent fisico ----
            cond_offset = (fh_dist is not None and fh_dist > 3.0)
            # ---- (5) beyond-MIROVA: no cruza NINGUN registro MIROVA ese dia (cualquier sensor) ----
            any_gt_day = any((repo, day, b) in gt_any for b in ('MODIS','VIIRS750','VIIRS375'))
            cond_beyond = (pcvrp > 1.0 and not any_gt_day)

            if cond_summit_far:   flags['1_summit_far'] += 1
            if cond_incoherent:   flags['1b_incoherent_summit_farcluster'] += 1
            if cond_highvrp:      flags['2_highvrp>10'] += 1
            if cond_sensor_mismatch:
                flags['3_sensor_mismatch'] += 1
                sensor_mismatch[bucket] += 1
            if cond_offset:       flags['4_offset>3km'] += 1
            if cond_beyond:       flags['5_beyond_mirova'] += 1
            if brg:               bearings[brg[0]] += 1

            # "extrano" = dispara cualquier condicion fuerte (no el offset suave solo)
            is_weird = cond_summit_far or cond_incoherent or cond_highvrp or cond_sensor_mismatch or cond_beyond
            if is_weird:
                tags = classify(rec, repo, (vlat, vlon), inner, dist_eff)
                # score de "rareza" para ranking global
                score = 0.0
                if cond_highvrp: score += pcvrp
                if cond_summit_far: score += fh_dist * 2
                if cond_incoherent: score += (c_dist or 0) * 1.5
                if cond_beyond: score += 15
                if cond_sensor_mismatch: score += 8
                weird_all.append({
                    'vol': repo, 'date': day, 'time': (rec.get('datetime_utc') or '')[11:16],
                    'sensor': rec.get('sensor'), 'bucket': bucket,
                    'pcvrp': round(pcvrp, 2), 'fh_dist': round(fh_dist, 2) if fh_dist is not None else None,
                    'c_dist': round(c_dist, 2) if c_dist is not None else None,
                    'dclass': dclass, 'bearing': brg[0] if brg else None,
                    't_bg': round(rec.get('t_bg_k'), 1) if rec.get('t_bg_k') is not None else None,
                    'nti_std': rec.get('diag_nti_std'), 'nti_max': rec.get('diag_nti_max'),
                    'gt_alerta': gt_alerta, 'gt_sensor': gt_has_sensor, 'any_gt_day': any_gt_day,
                    'conds': [c for c, v in [('summit_far', cond_summit_far), ('highvrp', cond_highvrp),
                              ('sensor_mismatch', cond_sensor_mismatch), ('beyond', cond_beyond)] if v],
                    'tags': tags, 'score': round(score, 1),
                })

        per_vol[repo] = {
            'n_recs': len(recs),
            'n_signal': sum(1 for r in recs if (r.get('primary_cluster') or {}).get('vrp_mw', 0) or r.get('triggered_test1') or (r.get('vrp_mw') or 0) > 0),
            'flags': dict(flags),
            'bearings': dict(bearings),
            'sensor_mismatch_by_bucket': dict(sensor_mismatch),
            'inner': inner,
        }

    weird_all.sort(key=lambda x: x['score'], reverse=True)

    out = {'per_vol': per_vol, 'top_weird': weird_all[:40], 'n_weird_total': len(weird_all)}
    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weird_records_result.json')
    json.dump(out, open(outpath, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    # ---- resumen a stdout ----
    print('=== PER-VOL (mayo-jun 2026) ===')
    for v, s in per_vol.items():
        print(f"{v:22s} recs={s['n_recs']:4d} signal={s['n_signal']:4d} inner={s['inner']:2d} "
              f"flags={s['flags']} mismatch={s['sensor_mismatch_by_bucket']}")
    print()
    print('=== BEARINGS (offset direccional desde vent) ===')
    for v, s in per_vol.items():
        if s['bearings']:
            print(f"{v:22s} {s['bearings']}")
    print()
    # resumen por clasificacion primaria (tag[0])
    from collections import Counter as _C
    cls = _C(w['tags'][0] for w in weird_all)
    print('=== WEIRD por clasificacion primaria ===')
    for k, v in cls.most_common():
        print(f"  {k:28s} {v}")
    print()
    print(f"=== TOP 15 WEIRD (de {len(weird_all)}) ===")
    for w in weird_all[:15]:
        print(f"{w['vol']:18s} {w['date']} {w['time']} {w['bucket']:9s} "
              f"pcvrp={w['pcvrp']:7.2f} fh_dist={w['fh_dist']} c_dist={w['c_dist']} "
              f"{w['dclass']:6s} brg={w['bearing']} tbg={w['t_bg']} "
              f"conds={w['conds']} CLASS={w['tags']}")
    print(f"\nWROTE {outpath}")

if __name__ == '__main__':
    main()
