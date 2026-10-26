"""Tarea 1.19 (i): nulo medido del escalon (A110), version que no se contamina con el escalon real.

En 01b el nulo desplazaba los dos escalones juntos y los quitaba del modelo, asi que un escalon real cercano se
filtraba al placebo. Aca el modelo SIEMPRE lleva los dos escalones reales (36,32 y 52,66) y se le agrega UN escalon
placebo en c, barrido de 12 a 66 grados cada 0,5 excluyendo +-2,5 de cada limite. La distribucion de |placebo| es el
ruido estructural del perfil a ese nivel de modelo. Mismo efecto fijo volcan x mes y spline de 01b.
"""
import sys, io, json, pathlib
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
OSF = r'C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv'
B1, B2 = 36.32, 52.66
KN = np.arange(8, 68, 4.0)
o = pd.read_csv(OSF, encoding='utf-8')
o = o[(o.Npix > 0) & (o.VRP > 0) & (o.Dayflag == 0) & (o['class'] == 1)].dropna(subset=['Volc_Name', 'timeUTC', 'SatZen']).copy()
o['z'] = o.SatZen.abs()
o['g'] = o.Volc_Name + '|' + pd.to_datetime(o.timeUTC, dayfirst=True).dt.strftime('%Y%m')
o['lnN'] = np.log(o.Npix); o['lnV'] = np.log(o.VRP); o['lnVN'] = o.lnV - o.lnN


def preparar(d):
    gid = pd.factorize(d.g)[0]; cnt = np.bincount(gid); keep = cnt[gid] >= 2
    d = d[keep]; gid = pd.factorize(d.g)[0]; cnt = np.bincount(gid)
    def dm(M):
        M = np.atleast_2d(M.T).T if M.ndim == 1 else M
        s = np.zeros((cnt.size, M.shape[1])); np.add.at(s, gid, M)
        return M - s[gid] / cnt[gid, None]
    z = d.z.values
    base = dm(np.column_stack([z] + [np.maximum(z - k, 0) for k in KN] + [(z >= B1) * 1.0, (z >= B2) * 1.0]))
    return z, base, dm


res = {}
for nom, d in {'V375': o[o.Resolution == 375], 'V375 SNPP (sat 3)': o[(o.Resolution == 375) & (o.Satellite == 3)],
               'V375 NOAA-20 (sat 4)': o[(o.Resolution == 375) & (o.Satellite == 4)],
               'V750': o[o.Resolution == 750], 'MODIS': o[o.Resolution == 1000]}.items():
    z, base, dm = preparar(d)
    res[nom] = {}
    for var in ('lnN', 'lnV', 'lnVN'):
        dd = d.copy(); gid = pd.factorize(dd.g)[0]; cnt = np.bincount(gid); dd = dd[cnt[gid] >= 2]
        y = dm(dd[var].values.reshape(-1, 1))[:, 0]
        b0 = np.linalg.lstsq(base, y, rcond=None)[0]
        pl = []
        for c in np.arange(12, 66.01, 0.5):
            if abs(c - B1) < 2.5 or abs(c - B2) < 2.5:
                continue
            X = np.column_stack([base, dm(((z >= c) * 1.0).reshape(-1, 1))])
            b = np.linalg.lstsq(X, y, rcond=None)[0]
            pl.append((float(c), float(b[-1])))
        a = np.abs([x for _, x in pl])
        res[nom][var] = dict(salto_3a2=round(float(b0[-2]), 4), salto_2a1=round(float(b0[-1]), 4),
                             placebo_p95_abs=round(float(np.percentile(a, 95)), 4), placebo_max_abs=round(float(a.max()), 4),
                             placebo_n=len(a), placebo_top=[(c, round(x, 3)) for c, x in sorted(pl, key=lambda t: -abs(t[1]))[:5]])
        print(f'{nom} {var}: 3:1->2:1 {b0[-2]:+.3f}  2:1->1:1 {b0[-1]:+.3f}  placebo |p95| {np.percentile(a,95):.3f} max {a.max():.3f} (n={len(a)})  top {res[nom][var]["placebo_top"][:3]}')
pathlib.Path(__file__).with_name('01c_salida.json').write_text(json.dumps(res, indent=1))
