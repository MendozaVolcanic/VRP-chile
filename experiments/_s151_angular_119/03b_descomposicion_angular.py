"""Tarea 1.19: en que factor vive la dependencia angular de R, conteo (F_n = n nuestro / Npix MIROVA) o exceso por
pixel (F_ex). Mismos pares S139 y misma regresion con efecto fijo por volcan que 03_pares_vs_huella.py.
Ademas: cobertura de pares a cada lado de cada limite (+-3 grados), por volcan, para saber si el escalon es medible."""
import sys, io, json, pathlib
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from huella import area_rel
p = pd.read_csv(r'C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/experiments/_s139_audit/magnitud/02_pares.csv')
p = p[(p.res == 375) & (p.R > 0) & (p.F_n > 0) & (p.F_ex > 0)].copy()
p['x_agr'] = -np.log([area_rel(z) for z in p.satzen])
p['lnNpix'] = np.log(p.Npix); p['lnFn'] = np.log(p.F_n); p['lnFex'] = np.log(p.F_ex); p['lnR'] = np.log(p.R)
p['lnn'] = np.log(p.pub_n)
SINK = ['Lascar', 'Isluga', 'Copahue']
rng = np.random.default_rng(5)
def fe(d, y):
    xd = d.x_agr - d.groupby('vol').x_agr.transform('mean'); yd = d[y] - d.groupby('vol')[y].transform('mean')
    return float((xd * yd).sum() / (xd ** 2).sum())
res = {}
for nom, d in {'V375 todos': p, 'sin kernel local': p[p.vol.isin(SINK)]}.items():
    res[nom] = {}
    for y in ('lnR', 'lnFn', 'lnFex', 'lnNpix', 'lnn'):
        b = fe(d, y)
        bs = [fe(d.iloc[rng.choice(len(d), len(d))], y) for _ in range(500)]
        res[nom][y] = dict(beta=round(b, 3), ic95=[round(float(x), 3) for x in np.percentile(bs, [2.5, 97.5])], n=int(len(d)))
        print(f'{nom:18s} {y:7s} beta sobre -lnA_nativo = {b:+.3f}  IC {np.round(np.percentile(bs,[2.5,97.5]),3)}  n={len(d)}')
print('\n(lnNpix: la prediccion de remuestreo es beta = -1 si MIROVA cuenta celdas en proporcion al area nativa; lnn: nuestro conteo)')
print('\ncobertura de pares a +-3 grados de cada limite (izq/der), por volcan')
cov = {}
for b in (36.32, 52.66):
    w = p[(p.satzen > b - 3) & (p.satzen < b + 3)]
    t = w.assign(lado=np.where(w.satzen >= b, 'der', 'izq')).groupby(['vol', 'lado']).size().unstack(fill_value=0)
    cov[str(b)] = t.to_dict('index'); print(f'limite {b}:'); print(t.to_string())
res['cobertura'] = cov
pathlib.Path(__file__).with_name('03b_salida.json').write_text(json.dumps(res, indent=1))
