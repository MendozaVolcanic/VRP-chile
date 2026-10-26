"""S163 D-39 (punto 1, OCR): registro_vrp_ocr.csv original vs brazo A vs brazo B, por llave y como texto.
Para las notas reparadas comprueba que el esqueleto ASCII es identico (la reparacion solo toca tramos no ASCII)
y que no queda mojibake. Ademas compara el maestro publicable A vs B."""
import csv, sys, collections, re
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'D:\vrp-trabajo\s163-d39\scripts'); import gl
S = r'D:\vrp-trabajo\s163-d39'
def leer(p):
    with open(p, encoding='utf-8', newline='') as f: r = csv.DictReader(f); return r.fieldnames, list(r)
def idx(fs): return {gl._llave(f): f for f in fs}
co, fo = leer(S + r'\scripts\ocr_main_original.csv')
res = {}
for d in ('A', 'B', 'B1'):
    c, f = leer(S + rf'\sim\{d}\monitoreo_satelital\registro_vrp_ocr.csv'); res[d] = (c, idx(f), len(f))
O = idx(fo)
print('columnas original', len(co), '| A', len(res['A'][0]), '| B', len(res['B'][0]), '| columnas nuevas en B:', [c for c in res['B'][0] if c not in co],
      '| orden de las viejas igual en B:', [c for c in res['B'][0] if c in co] == co)
MOJ = re.compile('Ã|â€|â‰|Â')
for nom, X, Y in (('original->A', O, res['A'][1]), ('A->B', res['A'][1], res['B'][1]), ('B1->B', res['B1'][1], res['B'][1])):
    perd, nue = set(X) - set(Y), set(Y) - set(X); camb = collections.Counter(); ej = {}
    for k in set(X) & set(Y):
        d = tuple(c for c in co if (X[k].get(c) or '') != (Y[k].get(c) or ''))
        if d: camb[d] += 1; ej.setdefault(d, (k, [(c, X[k][c][:90], Y[k][c][:90]) for c in d]))
    print(f'\n{nom}: llaves que desaparecen {len(perd)}; nuevas {len(nue)}; filas con algun campo distinto {sum(camb.values())}')
    for d, n in camb.most_common(): print('   ', n, d, ej[d])
    if nom == 'A->B':
        notas = [k for k in set(X) & set(Y) if X[k]['Nota_Validacion'] != Y[k]['Nota_Validacion']]
        asc = lambda s: re.sub(r'[^\x00-\x7f]', '', s)
        print('   notas cambiadas', len(notas), '; esqueleto ASCII identico:', sum(asc(X[k]['Nota_Validacion']) == asc(Y[k]['Nota_Validacion']) for k in notas),
              '; con mojibake antes:', sum(bool(MOJ.search(X[k]['Nota_Validacion'])) for k in notas), '; con mojibake despues:', sum(bool(MOJ.search(Y[k]['Nota_Validacion'])) for k in notas))
        print('   notas con mojibake en todo B:', sum(bool(MOJ.search(v['Nota_Validacion'] or '')) for v in Y.values()), '; en A:', sum(bool(MOJ.search(v['Nota_Validacion'] or '')) for v in X.values()))
        print('   Metodo_Clase en B (valores):', dict(collections.Counter(v.get('Metodo_Clase') for v in Y.values())))
for nom in ('registro_vrp_maestro_publicable.csv',):
    _, fa = leer(S + rf'\sim\A\monitoreo_satelital\{nom}'); _, fb = leer(S + rf'\sim\B\monitoreo_satelital\{nom}')
    A, B = idx(fa), idx(fb)
    camb = sum(1 for k in set(A) & set(B) if A[k] != B[k])
    print(f'\n{nom}: A {len(fa)} B {len(fb)}; desaparecen {len(set(A)-set(B))}; nuevas {len(set(B)-set(A))}; comunes distintas {camb}')
