"""S163 D-39: que columnas difieren en registro_vrp_maestro_publicable.csv entre A y B, y de donde vienen las 76 nuevas."""
import csv, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'D:\vrp-trabajo\s163-d39\scripts'); import gl
S = r'D:\vrp-trabajo\s163-d39'
def leer(p):
    with open(p, encoding='utf-8', newline='') as f: r = csv.DictReader(f); return r.fieldnames, list(r)
ca, fa = leer(S + r'\sim\A\monitoreo_satelital\registro_vrp_maestro_publicable.csv'); cb, fb = leer(S + r'\sim\B\monitoreo_satelital\registro_vrp_maestro_publicable.csv')
print('cabecera', ca == cb, ca)
A = {gl._llave(f): f for f in fa}; B = {gl._llave(f): f for f in fb}
print('repetidas A', len(fa)-len(A), 'B', len(fb)-len(B))
camb = collections.Counter(); ej = {}
for k in set(A) & set(B):
    d = tuple(c for c in ca if A[k][c] != B[k][c])
    if d: camb[d] += 1; ej.setdefault(d, (k, [(c, A[k][c][:80], B[k][c][:80]) for c in d]))
for d, n in camb.most_common(): print(n, d, ej[d])
_, fp = leer(S + r'\sim\B\monitoreo_satelital\filas_perdidas_por_mezcla_2026.csv'); P = {gl._llave(f) for f in fp}
nue = set(B) - set(A)
print('nuevas', len(nue), 'en archivo de reposicion', sum(k in P for k in nue), collections.Counter(B[k].get('Fuente', B[k].get('Tipo_Registro')) for k in nue))
