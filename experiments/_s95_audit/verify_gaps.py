#!/usr/bin/env python
"""S95 — verificación reproducible de los hallazgos del audit de gaps sistémicos.

Integridad §0.5: este script es la fuente de verdad de los números del doc
docs/AUDIT_S95_gaps_sistemicos.md. NO transcribir números a mano.

Cubre:
- Eje 1: gap Test1 anomaly_pixels=[] en MODIS / VIIRS750 (records test1 con pc.vrp>0
  y anomaly_pixels vacío) por bucket de sensor.
- Eje 5: re-test del supuesto F47-latente con la lógica REAL del frontend
  (mirovaEqVrp usa pc.centroid_dist_km <= inner_radius para records con primary_cluster;
  distance_class solo es fallback legacy). Refuta/confirma "records ocultos".

Salida: experiments/_s95_audit/verify_gaps.json + stdout.
"""
import io, sys, os, json, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, 'data', 'mirova_equivalent')


def sensor_bucket(s):
    """Convención verificada (A48): MODIS_* = MODIS; VIIRS_*_750 = M750;
    VIIRS_{SNPP,NOAA20,NOAA21} sin sufijo = I375."""
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
    if isinstance(d, dict):
        return d.get('records', [])
    return d


def main():
    yml = yaml.safe_load(open(os.path.join(ROOT, 'volcanoes.yaml'), encoding='utf-8'))
    vols = yml['volcanoes'] if isinstance(yml, dict) and 'volcanoes' in yml else yml
    vlist = vols if isinstance(vols, list) else list(vols.values())
    inner = {}
    monitored_ids = []
    for v in vlist:
        vid = v.get('id') or v.get('name')
        if v.get('mirova_monitored'):
            inner[vid] = v.get('inner_radius_km', 5)
            monitored_ids.append(vid)

    out = {'inner_radius': inner, 'monitored': sorted(set(monitored_ids)),
           'eje1_test1_gap': {}, 'eje5': {}}

    # Acumuladores
    eje1 = {}  # sensor -> count
    eje1_by_vol = {}
    # Eje5
    shown = {}            # pc within inner & vrp>0 (REAL gate -> shown)
    hidden_far = {}       # pc beyond inner (REAL gate -> hidden, correcto)
    incoherent = {}       # pc within inner & vrp>0 PERO distance_class != summit
    agent_wrong_gate = {} # lo que ocultaría el gate (mal) del Eje5: dc!=summit & pc within & vrp>0
    cluster_rescue = {}
    no_pc = {}

    for vid in sorted(set(monitored_ids)):
        path = os.path.join(DATA, vid + '.json')
        if not os.path.exists(path):
            continue
        recs = load_records(path)
        ir = inner.get(vid, 5)
        for r in recs:
            sb = sensor_bucket(r.get('sensor'))
            pc = r.get('primary_cluster') or {}
            pcv = pc.get('vrp_mw')
            cd = pc.get('centroid_dist_km')
            aps = r.get('anomaly_pixels') or []
            fhs = r.get('final_hotspot_source')
            dc = r.get('distance_class')

            # Eje 1: test1 gap
            if fhs == 'test1' and isinstance(pcv, (int, float)) and pcv > 0 and len(aps) == 0:
                eje1[sb] = eje1.get(sb, 0) + 1
                eje1_by_vol.setdefault(vid, {})
                eje1_by_vol[vid][sb] = eje1_by_vol[vid].get(sb, 0) + 1

            # Eje 5: replicar gate REAL
            if pc and isinstance(pcv, (int, float)) and isinstance(cd, (int, float)):
                if pcv > 0:
                    if cd <= ir:
                        shown[sb] = shown.get(sb, 0) + 1
                        if dc != 'summit':
                            incoherent[sb] = incoherent.get(sb, 0) + 1
                            agent_wrong_gate[sb] = agent_wrong_gate.get(sb, 0) + 1
                    else:
                        hidden_far[sb] = hidden_far.get(sb, 0) + 1
            else:
                if isinstance(pcv, (int, float)) and pcv > 0:
                    no_pc[sb] = no_pc.get(sb, 0) + 1

            if fhs == 'cluster_rescue':
                cluster_rescue[vid] = cluster_rescue.get(vid, 0) + 1

    out['eje1_test1_gap'] = {'by_sensor': eje1, 'by_vol': eje1_by_vol,
                             'total': sum(eje1.values())}
    out['eje5'] = {
        'shown_pc_within_inner_vrp_pos': shown,
        'hidden_pc_beyond_inner': hidden_far,
        'incoherent_within_inner_but_distclass_not_summit': incoherent,
        'agent_wrong_gate_would_hide': agent_wrong_gate,
        'records_vrp_pos_without_usable_pc': no_pc,
        'cluster_rescue_by_vol': cluster_rescue,
        'note': ('REAL gate uses pc.centroid_dist_km<=inner. "incoherent" records '
                 'are SHOWN under real gate (return pc.vrp_mw); only the agent-misread '
                 'gate (distance_class) would hide them.'),
    }

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verify_gaps.json'),
              'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)

    print('=== EJE 1: gap Test1 anomaly_pixels vacío (test1 & pc.vrp>0 & aps==[]) ===')
    print('  por sensor:', eje1, ' TOTAL:', sum(eje1.values()))
    print('  por volcán:', json.dumps(eje1_by_vol, ensure_ascii=False))
    print()
    print('=== EJE 5: re-test F47-latente con gate REAL (pc.centroid_dist_km<=inner) ===')
    print('  SHOWN (pc within inner, vrp>0):', shown, ' TOTAL:', sum(shown.values()))
    print('  HIDDEN correcto (pc beyond inner):', hidden_far, ' TOTAL:', sum(hidden_far.values()))
    print('  Incoherentes (within inner pero distance_class!=summit) -> SHOWN bajo gate real:',
          incoherent, ' TOTAL:', sum(incoherent.values()))
    print('  Lo que ocultaría el gate MAL-LEÍDO del Eje5 (distance_class):',
          agent_wrong_gate, ' TOTAL:', sum(agent_wrong_gate.values()))
    print('  cluster_rescue por vol:', cluster_rescue)
    print()
    print('wrote verify_gaps.json')


if __name__ == '__main__':
    main()
