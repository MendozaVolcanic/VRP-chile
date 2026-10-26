"""Tarea 1.19: escalon en 52,66 grados DENTRO de los volcanes que tienen pares a los dos lados (+-3 grados).
Lo predicho por la fisica de un pixel (pre-registro): ln R sube +0,693 al cruzar hacia afuera. Control: el mismo
contraste en 44 y 60 grados (sin limite), con la misma ventana. Pares S139 (02_pares.csv), solo lectura."""
import sys, io, json, pathlib
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = pd.read_csv(r'C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/experiments/_s139_audit/magnitud/02_pares.csv')
p = p[(p.res == 375) & (p.R > 0)].copy(); p['lnR'] = np.log(p.R); p['lnRpc'] = np.log(p.R_pc)
rng = np.random.default_rng(7); out = {}
for b in (52.66, 36.32, 44.0, 47.0, 60.0):
    w = p[(p.satzen > b - 3) & (p.satzen < b + 3)].assign(der=lambda d: d.satzen >= b)
    ok = w.groupby('vol').der.agg(lambda s: s.sum() >= 5 and (~s).sum() >= 5)
    vols = ok[ok].index.tolist(); w = w[w.vol.isin(vols)]
    def est(d, y):
        g = d.groupby(['vol', 'der'])[y].median().unstack()
        n = d.groupby('vol').size()
        if len(g) == 0 or True not in g.columns or False not in g.columns:
            return np.nan
        return float(((g[True] - g[False]) * n).sum() / n.sum())
    r = {}
    for y in ('lnR', 'lnRpc'):
        e = est(w, y)
        idx = [np.where(w.vol.values == v)[0] for v in vols]
        bs = [est(w.iloc[np.concatenate([rng.choice(i, len(i)) for i in idx])], y) for _ in range(300)] if vols else [np.nan]
        r[y] = dict(salto=round(e, 3), ic95=[round(float(x), 3) for x in np.nanpercentile(bs, [2.5, 97.5])])
    out[str(b)] = dict(volcanes=vols, n=int(len(w)), **r)
    print(f'b={b:5.2f} volcanes a ambos lados (>=5 c/u): {vols} n={len(w)}  lnR {r["lnR"]}  lnRpc {r["lnRpc"]}')
pathlib.Path(__file__).with_name('03c_salida.json').write_text(json.dumps(out, indent=1))
