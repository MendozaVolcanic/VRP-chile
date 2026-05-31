#!/usr/bin/env python
"""S95 Eje 5 — re-verificación CORRECTA del gate mirovaEqVrp.

CORRECCIÓN: la primera pasada (verify_gaps.py) replicó una lógica de gate
equivocada (stdout corrupto entrelazado ocultó la línea 904). El gate REAL del
frontend (index.html:891-912) es, en orden:
  1. si no hay primary_cluster -> fallback vrp_mw
  2. if (distance_class && distance_class!='summit' && !includeFar) return 0   <- L904
  3. if (!includeFar && pc.centroid_dist_km > innerKm) return 0                <- L908
  4. else return pc.vrp_mw
Es decir, distance_class GATEA PRIMERO. Un record con cluster dentro del inner
pero distance_class='far' SE OCULTA (incoherencia F47-style, Eje 5 CONFIRMADO).

Además el dashboard muestra `isThermalArtifact(r)? 0 : mirovaEqVrp(...)`.

Este script clasifica los records ocultos por la incoherencia para decidir si es
bug real (pérdida de detección summit) o ocultamiento deseable.
Salida: verify_eje5.json + stdout corto.
"""
import io, sys, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, 'data', 'mirova_equivalent')


def sensor_bucket(s):
    if not s:
        return 'OTHER'
    s = str(s)
    if s.startswith('MODIS'):
        return 'MODIS'
    if s.startswith('VIIRS'):
        return 'VIIRS750' if s.endswith('_750') else 'VIIRS375'
    return 'OTHER'


def load_records(path):
    d = json.loads(open(path, encoding='utf-8').read())
    return d.get('records', []) if isinstance(d, dict) else d


def is_cirrus_artifact(r, eq):
    if r.get('_mirova_confirmed'):
        return False
    tmk = r.get('t_max_k')
    if tmk is None or tmk >= 273.15:
        return False
    return eq > 10


def is_diffuse_artifact(r, eq):
    if r.get('_mirova_confirmed'):
        return False
    pc = r.get('primary_cluster') or {}
    tmk = r.get('t_max_k')
    if not pc or tmk is None or tmk >= 278.15:
        return False
    npx = pc.get('n_pixels') or 0
    if npx < 100:
        return False
    return eq >= 50 and (eq / npx) < 1.0


def mirova_eq_vrp_real(r, inner, include_far=False):
    """Réplica EXACTA de index.html:891-912 (sin sanity cap, irrelevante aquí)."""
    if not r:
        return 0.0, None
    pc = r.get('primary_cluster')
    if not pc:
        return (r.get('vrp_mw') or r.get('vrp_mir_mw') or 0.0), 'fallback'
    dc = r.get('distance_class')
    if dc and dc != 'summit' and not include_far:
        return 0.0, 'gate_distance_class'          # L904
    cd = pc.get('centroid_dist_km')
    if (not include_far) and cd is not None and cd > inner:
        return 0.0, 'gate_centroid'                # L908
    return (pc.get('vrp_mw') or 0.0), 'shown'


def main():
    yml = yaml.safe_load(open(os.path.join(ROOT, 'volcanoes.yaml'), encoding='utf-8'))
    vols = yml['volcanoes'] if isinstance(yml, dict) and 'volcanoes' in yml else yml
    vlist = vols if isinstance(vols, list) else list(vols.values())
    inner, ids = {}, []
    for v in vlist:
        if v.get('mirova_monitored'):
            vid = v.get('id') or v.get('name')
            inner[vid] = v.get('inner_radius_km', 5)
            ids.append(vid)

    # Foco: records ocultos por L904 (gate_distance_class) PERO cluster dentro del
    # inner y vrp>0 = la incoherencia F47-style.
    incoh = {'total': 0, 'by_sensor': {}, 'by_vol': {},
             'vrp_floor_5': 0, 'vrp_gt_5': 0,
             'mirova_confirmed': 0,
             'would_be_thermal_artifact': 0,   # se ocultarían igual por física
             'NOT_artifact_NOT_confirmed': 0,  # ocultados solo por la incoherencia
             'geo_class_summit': 0,
             'distance_class_values': {},
             'examples': []}

    for vid in sorted(set(ids)):
        path = os.path.join(DATA, vid + '.json')
        if not os.path.exists(path):
            continue
        ir = inner[vid]
        for r in load_records(path):
            pc = r.get('primary_cluster') or {}
            cd = pc.get('centroid_dist_km')
            pcv = pc.get('vrp_mw')
            dc = r.get('distance_class')
            if not (pc and isinstance(pcv, (int, float)) and pcv > 0):
                continue
            if not (isinstance(cd, (int, float)) and cd <= ir):
                continue
            # cluster DENTRO del inner con vrp>0
            if not (dc and dc != 'summit'):
                continue   # no es incoherente (es summit o sin dc)
            # -> ocultado por L904 pese a cluster summit-geometrico
            sb = sensor_bucket(r.get('sensor'))
            incoh['total'] += 1
            incoh['by_sensor'][sb] = incoh['by_sensor'].get(sb, 0) + 1
            incoh['by_vol'].setdefault(vid, {})
            incoh['by_vol'][vid][sb] = incoh['by_vol'][vid].get(sb, 0) + 1
            incoh['distance_class_values'][dc] = incoh['distance_class_values'].get(dc, 0) + 1
            if abs(pcv - 5.0) < 1e-6:
                incoh['vrp_floor_5'] += 1
            else:
                incoh['vrp_gt_5'] += 1
            if r.get('_mirova_confirmed'):
                incoh['mirova_confirmed'] += 1
            if (pc.get('geo_class') == 'summit'):
                incoh['geo_class_summit'] += 1
            # ¿se ocultaría igual por artefacto térmico (física)?
            # eq se evalúa como si pasara el gate (usar pcv)
            art = is_cirrus_artifact(r, pcv) or is_diffuse_artifact(r, pcv)
            if art:
                incoh['would_be_thermal_artifact'] += 1
            elif not r.get('_mirova_confirmed'):
                incoh['NOT_artifact_NOT_confirmed'] += 1
            if len(incoh['examples']) < 12:
                incoh['examples'].append({
                    'vol': vid, 'sensor': r.get('sensor'),
                    'dt': r.get('datetime_utc') or r.get('datetime'),
                    'pc_vrp': round(pcv, 3), 'cd': round(cd, 2), 'inner': ir,
                    'distance_class': dc, 'geo_class': pc.get('geo_class'),
                    't_max_k': r.get('t_max_k'),
                    'mir_conf': bool(r.get('_mirova_confirmed')),
                    'fhs': r.get('final_hotspot_source'),
                })

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'verify_eje5.json'), 'w', encoding='utf-8') as fh:
        json.dump(incoh, fh, indent=2, ensure_ascii=False)

    print('EJE5 CORREGIDO — records ocultos por L904 (distance_class!=summit) con cluster DENTRO del inner y vrp>0:')
    print('  TOTAL:', incoh['total'])
    print('  por sensor:', incoh['by_sensor'])
    print('  vrp==5.0 (piso MODIS):', incoh['vrp_floor_5'], '| vrp>5:', incoh['vrp_gt_5'])
    print('  MIROVA-confirmados (=pérdida real de recall):', incoh['mirova_confirmed'])
    print('  se ocultarían igual por artefacto térmico (física):', incoh['would_be_thermal_artifact'])
    print('  NI artefacto NI confirmado (ocultados SOLO por la incoherencia):', incoh['NOT_artifact_NOT_confirmed'])
    print('  geo_class==summit (cluster es summit pero dc=far):', incoh['geo_class_summit'])
    print('  valores distance_class:', incoh['distance_class_values'])
    print('  wrote verify_eje5.json (12 ejemplos dentro)')


if __name__ == '__main__':
    main()
