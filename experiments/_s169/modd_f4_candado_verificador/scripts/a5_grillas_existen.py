# P1: si alguna grilla_censo de la poblacion no existiera en el censo local, lo veria (os.path.exists sobre las 5321 rutas). P2: control positivo: una ruta inventada debe dar False.
import json, os, glob, collections
C='D:/vrp-trabajo/temporales/s162_modd/censo/'
p=json.load(open('D:/vrp-trabajo/temporales/s169_ver_candado/arbol/experiments/_s166_modd_f4/poblacion_f4.json',encoding='utf-8'))
g=[x['grilla_censo'] for x in p['pasadas'] if x['grilla_censo']]
ex=[os.path.exists(C+r) for r in g]
print('rutas', len(g), 'existen', sum(ex), 'control (ruta inventada existe):', os.path.exists(C+'run_0/x/grilla_0.npz'))
print('npz en el censo local (glob run_*/*/grilla_*.npz):', len(glob.glob(C+'run_*/*/grilla_*.npz')))
print('runs', collections.Counter(r.split('/')[0] for r in g))
print('ids_censo unicos', len({x['id_censo'] for x in p['pasadas'] if x['grilla_censo']}))
