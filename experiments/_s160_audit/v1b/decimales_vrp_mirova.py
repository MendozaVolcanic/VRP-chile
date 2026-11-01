"""V1b-01: con cuantos decimales publica MIROVA el VRP de sus alertas, y cuantas caen en 1,00 MW (umbral de protegida).
Pregunta 1: si el VRP viniera con un decimal, la cuenta de dos decimales daria 0. Pregunta 2: si la lectura fallara, total 0 (assert)."""
import csv, sys, collections
c = collections.Counter(); cerca = collections.Counter()
for r in csv.DictReader(open(sys.argv[1], encoding='utf-8', errors='replace')):
    v = r['VRP_MW']
    if r['Tipo_Registro'].startswith('ALERTA') and v not in ('', '0.0'):
        c[len(v.split('.')[1]) if '.' in v else 0] += 1
        if 0.98 <= float(v) <= 1.02: cerca[v] += 1
assert sum(c.values()) > 0
print('alertas por numero de decimales:', dict(c)); print('alertas entre 0,98 y 1,02 MW:', dict(cerca))
