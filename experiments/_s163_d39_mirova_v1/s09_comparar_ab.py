"""S163 D-39 (punto 1, consolidado): compara fila a fila, por llave (timestamp, Volcan, Sensor) y como texto,
el consolidado de main original, el que deja un ciclo con el codigo de main (A) y el que deja un ciclo con
main + PR #26 (B). Cuenta en las dos direcciones y lista lo agregado con su origen."""
import csv, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'D:\vrp-trabajo\s163-d39\scripts'); import gl
S = r'D:\vrp-trabajo\s163-d39'
def leer(p):
    with open(p, encoding='utf-8', newline='') as f: r = csv.DictReader(f); return r.fieldnames, list(r)
co, fo = leer(S + r'\scripts\cons_main_original.csv')
ca, fa = leer(S + r'\sim\A\monitoreo_satelital\registro_vrp_consolidado.csv')
cb, fb = leer(S + r'\sim\B\monitoreo_satelital\registro_vrp_consolidado.csv')
cp, fp = leer(S + r'\sim\B\monitoreo_satelital\filas_perdidas_por_mezcla_2026.csv')
print('cabeceras iguales O/A/B:', co == ca == cb)
def idx(fs):
    d = {}; rep = 0
    for f in fs:
        k = gl._llave(f); rep += k in d; d[k] = f
    return d, rep
O, ro = idx(fo); A, ra = idx(fa); B, rb = idx(fb); P, _ = idx(fp)
print(f'filas: original {len(fo)}  A {len(fa)}  B {len(fb)}; repetidas O/A/B {ro}/{ra}/{rb}')
for nom, X, Y in (('original->A', O, A), ('original->B', O, B), ('A->B', A, B)):
    perd = set(X) - set(Y); nue = set(Y) - set(X)
    camb = collections.Counter(); ej = {}
    for k in set(X) & set(Y):
        d = tuple(c for c in co if X[k].get(c, '') != Y[k].get(c, ''))
        if d: camb[d] += 1; ej.setdefault(d, (k, [(c, X[k][c], Y[k][c]) for c in d]))
    print(f'\n{nom}: llaves que desaparecen {len(perd)}; llaves nuevas {len(nue)}; filas comunes con algun campo distinto {sum(camb.values())}')
    for d, n in camb.most_common(): print('   ', n, d, ej[d])
    if nom == 'A->B':
        orig = collections.Counter('archivo de reposicion del PR' if k in P else 'otro' for k in nue)
        print('   origen de las nuevas:', dict(orig), '; tipos:', dict(collections.Counter(B[k]['Tipo_Registro'] for k in nue)))
        malos = [k for k in nue if k in P and any((P[k][c] or '') != (B[k][c] or '') for c in co if c not in ('Fecha_Proceso_UTC','Ultima_Actualizacion_UTC'))]
        print('   nuevas que difieren del archivo de reposicion fuera de las columnas UTC:', len(malos))
        llen = collections.Counter((bool(B[k]['Fecha_Proceso_UTC']), bool(B[k]['Ultima_Actualizacion_UTC'])) for k in nue)
        print('   columnas UTC llenas tras el backfill (proceso, ultima):', dict(llen))
# orden: B esta en el orden total del PR?
claves = [(-int(gl._llave(f)[0]), f['Volcan'], f['Sensor']) for f in fb]
print('\nB en orden (timestamp desc, Volcan, Sensor):', claves == sorted(claves))
