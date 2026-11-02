# -*- coding: utf-8 -*-
"""vch_04 (verificador S172): Simpson por plataforma y mezcla de regimenes de codigo en los pares de Chillan.
P1: control positivo: Spearman global de la razon contra z debe reproducir s03 (-0.867/-0.5/-0.814).
P2: si 'sha'/'proc' vinieran vacios se imprime SIN DATO en vez de 'un solo regimen'.
Pares = pasadas publicadas con alerta (union CONS+OCR, D-9 SN) del CSV reproducido en salidas/r02_pasadas.csv.
"""
import csv, collections, math, statistics, json
R = list(csv.DictReader(open('salidas/r02_pasadas.csv', encoding='utf-8')))
def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0]*len(v); i = 0
    while i < len(o):
        j = i
        while j+1 < len(o) and v[o[j+1]] == v[o[i]]: j += 1
        for k in range(i, j+1): r[o[k]] = (i+j)/2+1
        i = j+1
    return r
def sp(x, y):
    if len(x) < 4: return None
    a, b = rank(x), rank(y); ma, mb = sum(a)/len(a), sum(b)/len(b)
    return round(sum((p-ma)*(q-mb) for p, q in zip(a, b))/math.sqrt(sum((p-ma)**2 for p in a)*sum((q-mb)**2 for q in b)), 3)
out = {}
for b in ('MODIS', 'VIIRS375', 'VIIRS750'):
    P = [r for r in R if r['b'] == b and r['pub'] == '1' and float(r['disp']) > 0 and r['vrp_M'] not in ('', 'None') and float(r['vrp_M']) > 0]
    rz = lambda S: [float(r['disp'])/float(r['vrp_M']) for r in S]
    zz = lambda S: [float(r['z']) for r in S]
    d = {'global': (sp(zz(P), rz(P)), len(P))}
    plat = collections.defaultdict(list)
    for r in P: plat[r['sensor'].replace('_750', '').split('_')[-1]].append(r)
    for k, S in plat.items(): d['plataforma_' + k] = (sp(zz(S), rz(S)), len(S))
    # spearman parcial dado plataforma (rangos dentro de plataforma)
    xs, ys = [], []
    for k, S in plat.items():
        if len(S) >= 3:
            rx, ry = rank(zz(S)), rank(rz(S))
            xs += [(a-(len(S)+1)/2)/len(S) for a in rx]; ys += [(a-(len(S)+1)/2)/len(S) for a in ry]
    n = len(xs); mx, my = sum(xs)/n, sum(ys)/n
    d['parcial_dentro_de_plataforma'] = (round(sum((a-mx)*(c-my) for a, c in zip(xs, ys))/math.sqrt(sum((a-mx)**2 for a in xs)*sum((c-my)**2 for c in ys)), 3), n)
    shas = collections.Counter(r['sha'] or 'SIN_SHA' for r in P)
    procs = [r['proc'] for r in P if r['proc']]
    d['codigo_sha_en_pares'] = dict(shas)
    d['processed_utc_min_max'] = (min(procs), max(procs)) if procs else 'SIN DATO'
    out[b] = d
print(json.dumps(out, indent=1, ensure_ascii=False))
json.dump(out, open('salidas/v04_plataforma_regimen.json', 'w'), indent=1, ensure_ascii=False)
