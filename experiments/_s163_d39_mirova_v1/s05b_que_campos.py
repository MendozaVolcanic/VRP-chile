"""S163 D-39: en las filas del PR que difieren del padre del episodio, que columnas difieren y como; y donde estan las 29 sin padre."""
import subprocess, sys, csv, io, collections
sys.path.insert(0, r'D:\vrp-trabajo\s163-d39\scripts'); import gl
exec(open(r'D:\vrp-trabajo\s163-d39\scripts\s05_verificar_reposicion_pr.py', encoding='utf-8').read().split("pr = tabla")[0])
pr = tabla('pr26', 'monitoreo_satelital/filas_perdidas_por_mezcla_2026.csv')
padres = {e: {gl._llave(f): f for f in tabla(e + '^')} for e in EPIS}
hijos = {e: {gl._llave(f) for f in tabla(e)} for e in EPIS}
cols = collections.Counter(); ejemplos = {}; sinpadre = []
for f in pr:
    k = gl._llave(f)
    hit = [e for e in EPIS if k in padres[e] and k not in hijos[e]]
    if not hit: sinpadre.append(f); continue
    p = padres[hit[-1]][k]
    d = tuple(c for c in f if (p.get(c) or '') != (f.get(c) or ''))
    if d:
        cols[d] += 1
        ejemplos.setdefault(d, [(c, p.get(c), f.get(c)) for c in d])
for d, n in cols.most_common(): print(n, d, ejemplos[d])
print('sin padre:', len(sinpadre), collections.Counter((f['Fecha_Satelite_UTC'][:7], f['Tipo_Registro']) for f in sinpadre))
print('  ', [ (f['Fecha_Satelite_UTC'], f['Volcan'], f['Sensor']) for f in sinpadre[:6]])
# tambien: en que padres (aunque el episodio no la pierda) aparecen
for f in sinpadre[:29]:
    k = gl._llave(f); en = [e for e in EPIS if k in padres[e]]
    if en: print('   en padre pero NO perdida en ese episodio', k, en)
