"""Tarea 1.19: la dependencia angular de NUESTRA razon contra MIROVA, explicada (o no) por la huella del pixel.

Pares: experiments/_s139_audit/magnitud/02_pares.csv (S139; 1.499 pasadas nocturnas V375 clase 1 del OSF 2025 con
record nuestro en el mismo minuto; R = magnitud publicada / VRP del OSF). Solo lectura.

Pregunta: si MIROVA conserva la energia (VRP plano en el cenit) y nosotros fijamos el area a nadir, la fisica de una
fuente de un pixel predice ln R = c + 1 * ln(A_nadir / A_nativo(cenit)), con escalones de +0,405 y +0,693 en 36,32 y
52,66 grados. Se ajusta beta con efecto fijo por volcan, contra dos regresores:
  - x_agr = -ln A_nativo con agregacion (con escalones), el pre-registrado;
  - x_sua = -ln A_nativo sin agregacion (crecimiento suave, sin escalones).
Si el escalon existe, x_agr gana; si la dependencia es suave y de otra causa, ninguno da beta ~1.
Control que puede fallar: cenit barajado dentro de cada volcan (beta debe caer a ~0), y MODIS/V750 de los mismos pares.
"""
import sys, io, json, pathlib
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from huella import area_rel
PARES = r'C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/experiments/_s139_audit/magnitud/02_pares.csv'
rng = np.random.default_rng(3)
p = pd.read_csv(PARES)
p = p[(p.res == 375) & (p.R > 0)].copy()
p['lnR'] = np.log(p.R)
p['lnRpc'] = np.log(p.R_pc)
p['x_agr'] = -np.log([area_rel(z) for z in p.satzen])
p['x_sua'] = -np.log([area_rel(z, False) for z in p.satzen])
p['s1'] = (p.satzen >= 36.32).astype(float); p['s2'] = (p.satzen >= 52.66).astype(float)
SINK = ['Lascar', 'Isluga', 'Copahue']


def fe(d, cols, y):
    g = d.vol
    Xd = np.column_stack([d[c] - d.groupby(g)[c].transform('mean') for c in cols])
    yd = d[y] - d.groupby(g)[y].transform('mean')
    b = np.linalg.lstsq(Xd, yd.values, rcond=None)[0]
    r = yd.values - Xd @ b
    return b, float(1 - (r ** 2).sum() / (yd.values ** 2).sum())


def boot(d, cols, y, B=500):
    vs = d.vol.unique(); idx = {v: np.where(d.vol.values == v)[0] for v in vs}
    out = []
    for _ in range(B):
        ii = np.concatenate([rng.choice(idx[v], len(idx[v])) for v in vs])
        out.append(fe(d.iloc[ii], cols, y)[0])
    return np.percentile(np.array(out), [2.5, 97.5], axis=0)


res = {}
for nom, d in {'V375 todos': p, 'V375 sin kernel local (Lascar, Isluga, Copahue)': p[p.vol.isin(SINK)],
               'Lascar': p[p.vol == 'Lascar'], 'Isluga': p[p.vol == 'Isluga']}.items():
    print(f'\n=== {nom}: n={len(d)}')
    r = {'n': int(len(d))}
    for y in ('lnR', 'lnRpc'):
        for cols in (['x_agr'], ['x_sua'], ['x_sua', 's1', 's2']):
            b, r2 = fe(d, cols, y)
            ic = boot(d, cols, y, B=300) if d.vol.nunique() > 1 else None
            if ic is None:
                ic = np.percentile([fe(d.iloc[rng.choice(len(d), len(d))], cols, y)[0] for _ in range(300)], [2.5, 97.5], axis=0)
            nul = []
            for _ in range(300):
                dd = d.copy()
                perm = dd.groupby('vol').satzen.transform(lambda s: rng.permutation(s.values)).values
                dd['x_agr'] = -np.log([area_rel(z) for z in perm]); dd['x_sua'] = -np.log([area_rel(z, False) for z in perm])
                dd['s1'] = (perm >= 36.32).astype(float); dd['s2'] = (perm >= 52.66).astype(float)
                nul.append(fe(dd, cols, y)[0])
            nul = np.percentile(np.abs(np.array(nul)), 95, axis=0)
            k = f'{y} ~ {"+".join(cols)}'
            r[k] = dict(beta=[round(float(x), 3) for x in b], ic95=[[round(float(a), 3), round(float(c), 3)] for a, c in zip(ic[0], ic[1])],
                        nulo_barajado_p95_abs=[round(float(x), 3) for x in nul], r2_dentro=round(r2, 3))
            print(f'  {k:28s} beta {np.round(b,3)}  IC {np.round(ic,3).tolist()}  nulo|p95| {np.round(nul,3)}  R2 {r2:.3f}')
    res[nom] = r
# perfil por banda de zona, mediana de R
p['zona'] = pd.cut(p.satzen, [0, 20, 36.32, 44, 52.66, 70], labels=['0-20', '20-36.3', '36.3-44', '44-52.7', '52.7-70'])
t = p.groupby(['zona'], observed=True).agg(n=('R', 'size'), R_med=('R', 'median'), pred=('x_agr', lambda s: float(np.exp(s).median())))
print('\n=== mediana de R por zona (todos V375) y prediccion A_nadir/A_nativo')
print(t.round(3).to_string())
t2 = p[p.vol.isin(SINK)].groupby('zona', observed=True).agg(n=('R', 'size'), R_med=('R', 'median'), pred=('x_agr', lambda s: float(np.exp(s).median())))
print('\n=== idem, sin kernel local'); print(t2.round(3).to_string())
res['perfil_todos'] = t.reset_index().astype({'zona': str}).to_dict('list')
res['perfil_sin_kernel'] = t2.reset_index().astype({'zona': str}).to_dict('list')
pathlib.Path(__file__).with_name('03_salida.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
