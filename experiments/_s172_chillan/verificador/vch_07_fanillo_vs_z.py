# vch_07: brazos O y O_fanillo de V750-C en las 28 alertas de Chillan que deciden (ablacion_por_pasada.csv de la papelera
# S171, sha db4e6ef7...), con el cenit unido por hora desde salidas/r02_pasadas.csv. Salida: salidas/v09_fanillo_vs_z.txt
import csv, math, statistics
A = [r for r in csv.DictReader(open('D:/vrp-trabajo/papelera_s171/s162-viirs750-f63ef4/experiments/_s162_v750c/ablacion_por_pasada.csv', encoding='utf-8')) if 'hill' in r['volcan'] and r['lab'] == 'pos' and r['decide'] == 'True']
Z = {r['dt']: float(r['z']) for r in csv.DictReader(open('salidas/r02_pasadas.csv', encoding='utf-8')) if r['b'] == 'VIIRS750'}
def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0] * len(v); i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]: j += 1
        for k in range(i, j + 1): r[o[k]] = (i + j) / 2 + 1
        i = j + 1
    return r
def sp(x, y):
    a, b = rank(x), rank(y); ma, mb = sum(a) / len(a), sum(b) / len(b)
    return sum((p - ma) * (q - mb) for p, q in zip(a, b)) / math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))
rows = []
for r in A:
    pub = r['O_fanillo_pub'] == 'True'
    rows.append((r['hora_utc'], Z.get(r['hora_utc']), pub, float(r['O_fanillo_vrp']) / float(r['mirova_vrp']) if pub else 0.0, float(r['O_vrp']) / float(r['mirova_vrp'])))
R = [x for x in rows if x[1] is not None]
print('alertas', len(rows), 'con z', len(R))
print('mediana O_fanillo solo publicadas', round(statistics.median([x[3] for x in R if x[2]]), 3), 'n', sum(1 for x in R if x[2]))
print('mediana O_fanillo con no publicadas = 0', round(statistics.median([x[3] for x in R]), 3), 'n', len(R))
print('Spearman O_fanillo(publicadas) vs z', round(sp([x[1] for x in R if x[2]], [x[3] for x in R if x[2]]), 3))
print('Spearman O_fanillo(no pub=0) vs z', round(sp([x[1] for x in R], [x[3] for x in R]), 3))
print('Spearman O (port completo) vs z', round(sp([x[1] for x in R], [x[4] for x in R]), 3))
print('no publicadas por fanillo z=', sorted(round(x[1], 1) for x in R if not x[2]))
