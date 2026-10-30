# Pregunta 1: si la poblacion estuviera rota (conteos mal), esta medicion lo veria? Si: recuenta desde el json crudo.
# Pregunta 2: si el script estuviera muerto, imprimiria otra cosa? Si: imprime conteos y un control positivo (cuenta de una clave inexistente da 0).
# Denominador: pasadas de poblacion_f4.json (3db87f50d). Ventana: C 2026-03-01..2026-10-16, E 2026-10-17..2026-10-26.
import json, collections, sys
p = json.load(open('D:/vrp-trabajo/temporales/s169_ver_candado/arbol/experiments/_s166_modd_f4/poblacion_f4.json', encoding='utf-8'))
P = p['pasadas']
print('n pasadas', len(P), 'unicas (vol,dt)', len({(x['vol'], x['dt']) for x in P}))
print('campos fila0', sorted(P[0].keys()))
print('por tramo', collections.Counter(x['tramo'] for x in P))
gc = [x for x in P if x.get('grilla_censo')]
print('con grilla_censo truthy', len(gc), collections.Counter(x['tramo'] for x in gc))
print('grilla_censo valores distintos tipo', collections.Counter(type(x.get('grilla_censo')).__name__ for x in P), collections.Counter(str(x.get('grilla_censo'))[:12] for x in P[:3]))
print('claves presentes y falsy', sum(1 for x in P if 'grilla_censo' in x and not x['grilla_censo']))
pr = [x for x in P if x['lab'] == 'protegida']
print('protegidas lab', len(pr), collections.Counter(x['tramo'] for x in pr))
print('protegidas lab_union', sum(1 for x in P if x.get('lab_union') == 'protegida'))
print('lab', collections.Counter(x['lab'] for x in P))
print('sin_pasada_nuestra', len(p['sin_pasada_nuestra']), len(p['sin_pasada_nuestra_detalle']))
print('dias excl', p['dias_e_excluidos'], 'head_e', {k: (v if not isinstance(v, (list, dict)) else type(v).__name__) for k, v in p['head_e'].items()})
print('ventanas', p['ventanas'], 'tol', p['tol_s'], 'regla', p['regla_minimas'])
print('rango dt C', min(x['dt'] for x in P if x['tramo']=='C'), max(x['dt'] for x in P if x['tramo']=='C'))
print('rango dt E', min(x['dt'] for x in P if x['tramo']=='E'), max(x['dt'] for x in P if x['tramo']=='E'))
print('tramo vs frontera 2026-10-17', sum(1 for x in P if (x['dt'] >= '2026-10-17') != (x['tramo']=='E')))
print('E con grilla', sum(1 for x in P if x['tramo']=='E' and x.get('grilla_censo')))
print('volcanes', collections.Counter(x['vol'] for x in P))
print('control positivo (clave inexistente):', sum(1 for x in P if x.get('NO_EXISTE_XYZ')))
print('conteos', p['conteos'])
print('granulos', len(p['granulos']), 'partes', len(p['partes']), p['partes'][:2] if p['partes'] else None)
print('carga_partes', p['carga_partes'][:3])
# protegidas con vrp_mirova
print('protegidas vrp_mirova min', min(x['vrp_mirova'] for x in pr), 'todas >=1', all(x['vrp_mirova'] >= 1 for x in pr))
print('bajo1 vrp rango', [x['vrp_mirova'] for x in P if x['lab']=='bajo1'][:5])
print('hora nocturna: todas noche?', collections.Counter(str(x.get('noche')) for x in P))
print('sensor', collections.Counter(x.get('sensor') for x in P))
