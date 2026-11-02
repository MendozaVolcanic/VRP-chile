# -*- coding: utf-8 -*-
"""vch_03 (verificador S172): efecto fijo por noche: pendiente de log(nuestro) y log(MIROVA) contra el cenit DENTRO de
una misma noche (el volcan cambia poco en 1 a 3 h), con IC por bootstrap de noches. Responde: la caida con el cenit, es
nuestra, de MIROVA, o de ambos? (CH172-01 y 07).
P1: control positivo: se fabrica nuestro' = nuestro * exp(-0.03*(z - media_noche)) y la pendiente debe bajar ~0.03.
P2: control negativo: z barajado DENTRO de cada noche: la pendiente media debe ser ~0 y el IC cubrirlo.
Noche = fecha UTC del record (como auto_audit). Pares = pasadas con alerta CONS/OCR (unidos) y nuestra magnitud > 0 (s02 reproducido).
"""
import csv, json, math, random, statistics, collections
R = list(csv.DictReader(open('salidas/r02_pasadas.csv', encoding='utf-8')))
rng = random.Random(1723)

def pend(rows, extra=None):
    num = den = 0.0
    por = collections.defaultdict(list)
    for r in rows: por[r['n']].append(r)
    xs, ys = [], []
    for n, v in por.items():
        if len(v) < 2: continue
        mz = sum(x['z'] for x in v) / len(v); my = sum(x['y'] for x in v) / len(v)
        for x in v:
            xs.append(x['z'] - mz); ys.append(x['y'] - my)
    d = sum(a * a for a in xs)
    return (sum(a * b for a, b in zip(xs, ys)) / d if d else None, len(xs))

out = {}
for b in ('MODIS', 'VIIRS375', 'VIIRS750'):
    P = [dict(n=r['dt'][:10], z=float(r['z']), lo=math.log(float(r['disp'])), lm=math.log(float(r['vrp_M'])))
         for r in R if r['b'] == b and r['pub'] == '1' and float(r['disp']) > 0 and r['vrp_M'] not in ('', 'None') and float(r['vrp_M']) > 0]
    mk = lambda key: [dict(n=p['n'], z=p['z'], y=p[key]) for p in P]
    o, m = pend(mk('lo')), pend(mk('lm'))
    ratio = [dict(n=p['n'], z=p['z'], y=p['lo'] - p['lm']) for p in P]
    rr = pend(ratio)
    noches = sorted({p['n'] for p in P}); porn = {n: [p for p in P if p['n'] == n] for n in noches}
    bs = []
    for _ in range(3000):
        T = [x for n in [rng.choice(noches) for _ in noches] for x in porn[n]]
        s = pend([dict(n=str(i) + x['n'], z=x['z'], y=x['lo'] - x['lm']) for i, x in enumerate(T)]) if False else None
        # bootstrap correcto: cada noche remuestreada conserva su etiqueta de bloque (indice de extraccion)
        blocks = []
        for k, n in enumerate([rng.choice(noches) for _ in noches]):
            blocks += [dict(n=f'{k}', z=x['z'], y=x['lo'] - x['lm']) for x in porn[n]]
        s = pend(blocks)[0]
        if s is not None: bs.append(s)
    bs.sort()
    # control positivo
    pos = pend([dict(n=p['n'], z=p['z'], y=p['lo'] - p['lm'] - 0.03 * p['z']) for p in P])[0]
    # control negativo: z barajado dentro de noche
    negs = []
    for _ in range(500):
        Q = []
        for n, v in porn.items():
            zz = [x['z'] for x in v]; rng.shuffle(zz)
            Q += [dict(n=n, z=z, y=x['lo'] - x['lm']) for x, z in zip(v, zz)]
        s = pend(Q)[0]
        if s is not None: negs.append(s)
    negs.sort()
    n_multi = sum(1 for v in porn.values() if len(v) >= 2)
    out[b] = dict(n_pares=len(P), n_noches=len(noches), n_noches_con_2mas=n_multi, n_pares_en_esas=o[1],
                  pendiente_log_nuestro_por_grado=round(o[0], 4) if o[0] is not None else None,
                  pendiente_log_mirova_por_grado=round(m[0], 4) if m[0] is not None else None,
                  pendiente_log_razon_por_grado=round(rr[0], 4) if rr[0] is not None else None,
                  IC95_bootstrap_noches_razon=[round(bs[int(.025 * len(bs))], 4), round(bs[int(.975 * len(bs)) - 1], 4)] if bs else None,
                  factor_razon_por_30_grados=round(math.exp(30 * rr[0]), 3) if rr[0] is not None else None,
                  control_positivo_pendiente_con_menos003_inyectado=round(pos, 4),
                  control_negativo_z_barajado_p2_5_p97_5=[round(negs[int(.025 * len(negs))], 4), round(negs[int(.975 * len(negs)) - 1], 4)])
print(json.dumps(out, indent=1, ensure_ascii=False))
json.dump(out, open('salidas/v03_dentro_de_noche.json', 'w'), indent=1, ensure_ascii=False)
