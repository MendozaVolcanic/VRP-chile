"""Tarea 1.19 (i), version con efecto fijo volcan x mes: escalones en los limites de agregacion.

Por que una segunda version: en 01_rd_osf.py la ventana +-3 grados deja a la mayoria de los volcanes con filas a
un solo lado (cada volcan se ve desde un juego discreto de orbitas, asi que su SatZen toma pocos valores), y el
efecto fijo dentro de la ventana diluye el salto hacia cero. Aca el modelo usa TODO el rango de cenit:

  y = efecto fijo (volcan x anio-mes) + spline lineal continuo de cenit (nudos cada 4 grados) + escalon en b1 + escalon en b2

El spline continuo absorbe el crecimiento suave del pixel y no puede imitar un escalon. El efecto fijo volcan x mes
compara pasadas del mismo volcan en el mismo mes de actividad. IC: bootstrap por volcan. Nulo MEDIDO (A110):
los mismos escalones desplazados delta grados (|delta| >= 2.5), donde no hay ningun limite fisico; y MODIS 1 km.
"""
import sys, io, json, pathlib
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
OSF = r'C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv'
B1, B2 = 36.32, 52.66
KN = np.arange(8, 68, 4.0)
rng = np.random.default_rng(1190)

o = pd.read_csv(OSF, encoding='utf-8')
o = o[(o.Npix > 0) & (o.VRP > 0) & (o.Dayflag == 0) & (o['class'] == 1)].dropna(subset=['Volc_Name', 'timeUTC', 'SatZen']).copy()
o['z'] = o.SatZen.abs()
o['ym'] = pd.to_datetime(o.timeUTC, dayfirst=True).dt.strftime('%Y%m')
o['g'] = o.Volc_Name + '|' + o.ym
o['lnN'] = np.log(o.Npix); o['lnV'] = np.log(o.VRP); o['lnVN'] = o.lnV - o.lnN


def disenio(z, b1, b2):
    cols = [z] + [np.maximum(z - k, 0) for k in KN] + [(z >= b1).astype(float), (z >= b2).astype(float)]
    return np.column_stack(cols)


def ajuste(d, var, b1=B1, b2=B2):
    X = disenio(d.z.values, b1, b2)
    gid = pd.factorize(d.g)[0]
    cnt = np.bincount(gid)
    keep = cnt[gid] >= 2
    X, y, gid = X[keep], d[var].values[keep], pd.factorize(d.g.values[keep])[0]
    cnt = np.bincount(gid)
    sx = np.zeros((cnt.size, X.shape[1])); np.add.at(sx, gid, X)
    sy = np.bincount(gid, weights=y)
    Xd = X - sx[gid] / cnt[gid, None]
    yd = y - sy[gid] / cnt[gid]
    beta = np.linalg.lstsq(Xd, yd, rcond=None)[0]
    return beta[-2], beta[-1]


def boot(d, var, B=200):
    vs = d.Volc_Name.unique()
    idx = {v: np.where(d.Volc_Name.values == v)[0] for v in vs}
    out = []
    for i in range(B):
        m = rng.choice(vs, len(vs))
        parts = []
        for k, v in enumerate(m):
            dd = d.iloc[idx[v]].copy(); dd['g'] = dd.g + f'#{k}'; dd['Volc_Name'] = f'{v}#{k}'
            parts.append(dd)
        out.append(ajuste(pd.concat(parts), var))
    out = np.array(out)
    return np.percentile(out[:, 0], [2.5, 97.5]), np.percentile(out[:, 1], [2.5, 97.5])


def nulo(d, var):
    sal = []
    for delta in np.arange(-12, 12.01, 0.5):
        if abs(delta) < 2.5:
            continue
        s1, s2 = ajuste(d, var, B1 + delta, B2 + delta)
        sal += [s1, s2]
    sal = np.abs(np.array(sal))
    return float(np.percentile(sal, 95)), float(sal.max()), len(sal)


v = o[o.Resolution == 375]
cnt = v.Volc_Name.value_counts()
muchos = cnt[cnt >= 2000].index
E = {
    'V375 noche clase1': v,
    'V375, volcanes >=2000 filas': v[v.Volc_Name.isin(muchos)],
    'V375, resto': v[~v.Volc_Name.isin(muchos)],
    'V375, Chile (11 Tier A del OSF)': v[v.Volc_Name.str.contains('scar|Isluga|Lastarria|Caulle|Copahue|Chait|Chill|Villarrica|Llaima|Peteroa|Tupungatito|Nevados', regex=True)],
    'V750 noche clase1 (replica)': o[o.Resolution == 750],
    'MODIS 1km noche clase1 (control)': o[o.Resolution == 1000],
}
SOLO = sys.argv[1] if len(sys.argv) > 1 else None
res = {}
for nom, d in E.items():
    if SOLO and SOLO not in nom:
        continue
    res[nom] = {'n': int(len(d)), 'volcanes': int(d.Volc_Name.nunique())}
    print(f'\n=== {nom}: n={len(d)} volcanes={d.Volc_Name.nunique()}')
    for var in ('lnN', 'lnV', 'lnVN'):
        s1, s2 = ajuste(d, var)
        B = 100 if len(d) > 100000 else 200
        ic1, ic2 = boot(d, var, B=B) if var != 'lnVN' or 'V375 noche' in nom else ([np.nan] * 2, [np.nan] * 2)
        n95, nmax, nn = nulo(d, var)
        res[nom][var] = dict(salto_3a2=round(s1, 4), ic_3a2=[round(float(x), 4) for x in ic1],
                             salto_2a1=round(s2, 4), ic_2a1=[round(float(x), 4) for x in ic2],
                             nulo_desplazado_p95_abs=round(n95, 4), nulo_max_abs=round(nmax, 4), nulo_n=nn)
        print(f'  {var:5s} 3:1->2:1 {s1:+.3f} [{ic1[0]:+.3f},{ic1[1]:+.3f}]   2:1->1:1 {s2:+.3f} [{ic2[0]:+.3f},{ic2[1]:+.3f}]'
              f'   nulo desplazado |p95| {n95:.3f} max {nmax:.3f} (n={nn})')
pathlib.Path(__file__).with_name(f'01b_salida{"_" + SOLO if SOLO else ""}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
print('\nprediccion fuente extensa (pre-registro): lnN -0.405 y -0.693; lnV 0; lnVN +0.405 y +0.693')
