"""Tarea 1.19 (i): salto de Npix, VRP y VRP/Npix en los limites de las zonas de agregacion VIIRS, OSF v2.5.

Limites pre-registrados (PREREGISTRO.md): 36,32 y 52,66 grados de cenit (31,589 y 44,680 de barrido, ATBD de
geolocalizacion p. 14 y 27, altitud 833 km). Metodo: discontinuidad de regresion local (recta a cada lado,
ventana +-H grados) sobre y - media del volcan en la ventana (efecto fijo por volcan). IC: bootstrap por volcan
(conglomerado). Nulo: SatZen barajado dentro de cada volcan. Controles: MODIS 1 km (no agrega), angulos placebo,
y el barrido de la discontinuidad por todo el rango (el pico deberia caer en los limites, no donde yo diga).
"""
import sys, io, json, pathlib
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
OSF = r'C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv'
OUT = pathlib.Path(__file__).with_name('01_salida.json')
LIM = {'3:1->2:1': 36.32, '2:1->1:1': 52.66}
PLACEBO = [30.0, 44.0, 47.0, 60.0]
rng = np.random.default_rng(119)

o = pd.read_csv(OSF, encoding='latin-1')
o = o[(o.Npix > 0) & (o.VRP > 0)].copy()
o['z'] = o.SatZen.abs()
o['lnN'] = np.log(o.Npix)
o['lnV'] = np.log(o.VRP)
o['lnVN'] = o.lnV - o.lnN
o['n1'] = (o.Npix == 1).astype(float)
VARS = ['lnN', 'lnV', 'lnVN', 'n1']


def rd(d, b, H, var):
    """Salto en b: interceptos de una recta a cada lado, sobre y centrado por volcan en la ventana."""
    w = d[(d.z > b - H) & (d.z < b + H)]
    if len(w) < 40:
        return np.nan, len(w)
    y = w[var] - w.groupby('Volc_Name')[var].transform('mean')
    x = w.z.values - b
    der = x >= 0
    if der.sum() < 20 or (~der).sum() < 20:
        return np.nan, len(w)
    X = np.column_stack([np.ones(len(x)), der, x, x * der])
    beta = np.linalg.lstsq(X, y.values, rcond=None)[0]
    return beta[1], len(w)


def boot(d, b, H, var, B=200):
    d = d[(d.z > b - H) & (d.z < b + H)]
    vs = d.Volc_Name.unique()
    g = {v: d[d.Volc_Name == v] for v in vs}
    out = []
    for _ in range(B):
        m = rng.choice(vs, len(vs))
        dd = pd.concat([g[v].assign(Volc_Name=f'{v}#{i}') for i, v in enumerate(m)])
        out.append(rd(dd, b, H, var)[0])
    return np.nanpercentile(out, [2.5, 97.5])


def nulo(d, b, H, var, B=200):
    w = d[(d.z > b - H - 1) & (d.z < b + H + 1)].copy()
    out = []
    for _ in range(B):
        w['z'] = w.groupby('Volc_Name').z.transform(lambda s: rng.permutation(s.values))
        out.append(rd(w, b, H, var)[0])
    return float(np.nanpercentile(np.abs(out), 95))


def estratos(o):
    v = o[(o.Resolution == 375) & (o.Dayflag == 0) & (o['class'] == 1)]
    cnt = v.Volc_Name.value_counts()
    muchos = cnt[cnt >= 2000].index
    return {
        'V375 noche clase1': v,
        'V375 noche clase1, volcanes >=2000 filas': v[v.Volc_Name.isin(muchos)],
        'V375 noche clase1, resto': v[~v.Volc_Name.isin(muchos)],
        'V375 todas las filas': o[o.Resolution == 375],
        'V750 noche clase1 (replica, mismo esquema)': o[(o.Resolution == 750) & (o.Dayflag == 0) & (o['class'] == 1)],
        'MODIS 1km noche clase1 (control, sin agregacion)': o[(o.Resolution == 1000) & (o.Dayflag == 0) & (o['class'] == 1)],
    }, list(muchos)


res = {}
E, muchos = estratos(o)
print('volcanes con >=2000 filas V375 noche clase 1:', len(muchos), muchos)
for nom, d in E.items():
    print(f'\n=== {nom}: n={len(d)}, volcanes={d.Volc_Name.nunique()}')
    res[nom] = {}
    for H in (3.0,):
        for lab, b in list(LIM.items()) + [(f'placebo {p}', p) for p in PLACEBO]:
            fila = {}
            for var in VARS:
                j, n = rd(d, b, H, var)
                full = ('375' in nom and 'clase1' in nom and 'resto' not in nom and '>=' not in nom) or 'MODIS' in nom or 'V750' in nom
                ic = boot(d, b, H, var, B=150) if (lab in LIM and var in ('lnN', 'lnVN', 'lnV')) else [np.nan, np.nan]
                nl = nulo(d, b, H, var, B=150) if (lab in LIM and var in ('lnN', 'lnV') and full) else np.nan
                fila[var] = dict(salto=round(float(j), 4), ic95=[round(float(x), 4) for x in ic], nulo95_abs=None if np.isnan(nl) else round(nl, 4), n=int(n))
            res[nom][f'{lab}@{b}'] = fila
            s = '  '.join(f"{v}={fila[v]['salto']:+.3f}" + (f"[{fila[v]['ic95'][0]:+.3f},{fila[v]['ic95'][1]:+.3f}]" if not np.isnan(fila[v]['ic95'][0]) else '') + (f" nulo|{fila[v]['nulo95_abs']}|" if fila[v]['nulo95_abs'] else '') for v in VARS)
            print(f'  {lab:>14} b={b:5.2f} n={fila["lnN"]["n"]:6d}  {s}')

# barrido de la discontinuidad: donde cae el salto mas grande de lnN sin decirle donde buscar
print('\n=== barrido de la discontinuidad en lnN (H=2), paso 0.25 grados')
bar = {}
for nom in ['V375 noche clase1', 'V750 noche clase1 (replica, mismo esquema)', 'MODIS 1km noche clase1 (control, sin agregacion)']:
    d = E[nom]
    bs = np.arange(20.0, 66.01, 0.25)
    js = [rd(d, b, 2.0, 'lnN')[0] for b in bs]
    bar[nom] = dict(b=bs.round(2).tolist(), salto=[round(float(x), 4) for x in js])
    orden = np.argsort(js)[:5]
    print(f'  {nom}: 5 caidas mas grandes en lnN:', [(float(bs[i]), round(float(js[i]), 3)) for i in orden])
    print(f'     5 subidas mas grandes:', [(float(bs[i]), round(float(js[i]), 3)) for i in np.argsort(js)[::-1][:5]])
res['barrido_lnN'] = bar

# perfil por bin de 1 grado (para la tabla del informe)
v = E['V375 noche clase1']
v = v.assign(zb=np.floor(v.z))
perf = v.groupby('zb').agg(n=('Npix', 'size'), Npix_media=('Npix', 'mean'), Npix_med=('Npix', 'median'),
                           VRP_med=('VRP', 'median'), VN_med=('lnVN', lambda s: float(np.exp(s.median()))))
print('\n=== perfil V375 noche clase 1, bins de 1 grado alrededor de los limites')
print(perf.loc[30:58].round(3).to_string())
res['perfil'] = perf.reset_index().round(4).to_dict('list')

# por volcan: salto de lnN en cada limite, volcanes con muchas filas
print('\n=== salto lnN por volcan (H=3), volcanes >=2000 filas')
pv = {}
d0 = E['V375 noche clase1']
for vname in muchos:
    dv = d0[d0.Volc_Name == vname]
    pv[vname] = {lab: round(float(rd(dv, b, 3.0, 'lnN')[0]), 3) for lab, b in LIM.items()}
    print(f'  {vname[:22]:>22}: n={len(dv):5d}  ' + '  '.join(f'{k} {x:+.3f}' for k, x in pv[vname].items()))
res['por_volcan_lnN'] = pv
OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1))
print('\nescrito', OUT)
