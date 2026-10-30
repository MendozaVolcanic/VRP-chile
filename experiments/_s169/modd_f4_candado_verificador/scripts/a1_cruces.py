# P1: detecta si grilla_censo se confunde con neg_limpio (coincidencia numerica 5321). P2: control positivo: el cruce debe distinguir ambas poblaciones (filas distintas).
import json, collections
p=json.load(open('D:/vrp-trabajo/temporales/s169_ver_candado/arbol/experiments/_s166_modd_f4/poblacion_f4.json',encoding='utf-8'))
P=p['pasadas']
c=collections.Counter((x['tramo'], x['lab'], bool(x['grilla_censo'])) for x in P)
for k,v in sorted(c.items()): print(k,v)
# las 144 sin grilla en C: distintas a neg_limpio?
sg=[x for x in P if x['tramo']=='C' and not x['grilla_censo']]
print('C sin grilla', len(sg), collections.Counter(x['lab'] for x in sg))
ids=[x['grilla_censo'] for x in P if x['grilla_censo']]
print('grilla_censo unicos', len(set(ids)), 'ej', ids[:2], 'formato run_/grilla_NNNN?')
import re
print('patron', collections.Counter(bool(re.match(r'^run_\d+/grilla_\d+\.npz$', i)) for i in ids))
# esperado: 5321 = 5465-144
print('5465-144 =', 5465-144)
# protegidas: por volcan y tramo
print(collections.Counter((x['vol'],x['tramo']) for x in P if x['lab']=='protegida'))
ch=[x for x in P if x['vol']=='NevadosDeChillan' and x['lab']=='protegida' and x['tramo']=='E']; print('chillan E protegidas', [(x['dt'], x['vrp_mirova'], x['z']) for x in ch])
