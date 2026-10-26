"""S163 D-39: llaves repetidas hoy en main (la guarda del PR #26 dejaria el ciclo en rojo si las hay)."""
import sys, collections
sys.path.insert(0, r'D:\vrp-trabajo\s163-d39\scripts')
import gl
for f in ['monitoreo_satelital/registro_vrp_consolidado.csv', 'monitoreo_satelital/registro_vrp_ocr.csv']:
    t = open(f, encoding='utf-8').read()
    ks = gl._llaves(t)
    c = collections.Counter(ks); d = {k: v for k, v in c.items() if v > 1}
    print(f, 'filas', len(ks), 'llaves distintas', len(c), 'repetidas', sum(v-1 for v in d.values()), list(d.items())[:5])
    print('  revisar(hoy, hoy) =', gl.revisar(t, t))
