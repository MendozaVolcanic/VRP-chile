# Publicacion (predicado del tablero via node) del record guardado HOY vs la del brazo C del probe 1.17,
# en los records de la muestra, separados por regimen de escritura.
import json, sys, io, glob, collections, datetime as D
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
REPO = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
sys.path.insert(0, REPO + '/scripts')
import banco_paridad as bp
B = "C:/Users/nmend/AppData/Local/Temp/claude/mxd03_117/"
H = json.load(open("C:/Users/nmend/AppData/Local/Temp/claude/deriva_123bis/historia_todos.json"))
ON = D.datetime(2026,5,28,16,39,tzinfo=D.timezone.utc); OFF = D.datetime(2026,7,1,20,46,tzinfo=D.timezone.utc)
pob = json.load(open(B + 'repo/experiments/_s151_mxd03_etiquetas/poblacion.json', encoding='utf-8'))
est = {(v, g['clave']): g for v, vv in pob['volcanes'].items() for g in vv['muestra']}
inner = {v: vv['inner_radius_km'] for v, vv in pob['volcanes'].items()}
probe = {}
for p in glob.glob(B + 'art/*/*.json'):
    d = json.load(open(p, encoding='utf-8'))
    if 'granulos' in d and 'job' in d:
        for g in d['granulos']:
            if g.get('estado') == 'ok': probe[(d['volcan'], g['clave'])] = g
recs = {}
for v in {r['v'] for r in H}:
    x = json.load(open(REPO + '/data/mirova_equivalent/%s.json' % v, encoding='utf-8')); x = x['records'] if isinstance(x, dict) else x
    recs[v] = {(r['datetime_utc'], r['sensor']): r for r in x}
casos = []; meta = []
for r in H:
    s = recs[r['v']].get((r['dt'], r['sensor']))
    slim = {k: s.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
    slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")} for p in (s.get("anomaly_pixels") or [])]
    casos.append([slim, inner[r['v']]]); meta.append((r, s))
pubs = bp.correr_node(casos)
c = collections.Counter(); ej = []
for (r, s), p in zip(meta, pubs):
    t = D.datetime.fromisoformat(r['escrito_utc']); reg = 'antes' if t < ON else ('gate_ON' if t < OFF else 'despues')
    g = probe[(r['v'], r['clave'])]; e = est[(r['v'], r['clave'])]
    pub_s = int(p[4]); pub_c = g['pub_c']; dc_s = s.get('distance_class'); dc_c = (g['c'] or {}).get('dc')
    c[(reg, e['estrato'], 'pub %d->%d' % (pub_s, pub_c), 'dc ' + ('igual' if dc_s == dc_c else '%s->%s' % (dc_s, dc_c)))] += 1
    if pub_s != e['pub_guardada']: ej.append(('pub_guardada difiere', r['v'], r['dt']))
    if reg == 'gate_ON' and (pub_s != pub_c or dc_s != dc_c): ej.append((r['v'], r['dt'], e['estrato'], e['lab'], e['prot'], 'pub', pub_s, pub_c, 'dc', dc_s, dc_c, 'n', r['n_s'], r['n_c']))
for k in sorted(c): print(k, c[k])
print('---'); [print(x) for x in ej]
