"""S139 magnitud, paso 2: descomponer la razon nuestra/MIROVA pasada a pasada contra el OSF v2.5.

Pares: pasada nocturna OSF (Dayflag=0, class=1, VRP>0) de los 11 Tier A, ventana 2025-02-15 a
2025-12-01, contra nuestro record de la misma resolucion a +-10 min que detecta al crater
(predicado de eje6/02). Mismo k y misma A que MIROVA (verificado en 01), asi que la razon se
separa EXACTAMENTE en:  R = F_n * F_ex,  F_n = n_nuestro/Npix,  F_ex = exceso por pixel nuestro /
(hot-bk)/Npix.  En 375 m (donde los pixeles publicados se identifican: nucleo F5') F_ex se separa
ademas en nivel caliente (L(bt) nuestro vs hot/Npix) y fondo (L_bg implicito vs bk/Npix).

Pregunta 1: si la magnitud estuviera rota (p. ej. k o A mal), F_ex saldria lejos de 1 aun con
los mismos pixeles; si la seleccion estuviera rota, F_n lo mostraria. Pregunta 2: si el pareo
fuera azar, el desplazamiento de 6 h debe dejar ~0 pares (control negativo); control positivo:
Npix MIROVA crece con SatZen (01), el n nuestro no deberia si no remuestreamos.
Supuesto: la L_bg implicita por pixel es L(bt) - vrp_px/(kA) con los pixeles de vrp_px>0 (el
recorte a cero de 1416 hace que los pixeles con vrp 0 no informen fondo).
"""
import json, pathlib, bisect, math, sys
import numpy as np, pandas as pd
from datetime import datetime, timedelta
R = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R))
from pipeline.f5_core import f5_core_vrp_mw, _hav_km, F5_R_CORE_KM, F5_BT_EXT_K

MAP = {'Láscar': 'Lascar', 'Lastarria': 'Lastarria', 'Isluga': 'Isluga', 'Llaima': 'Llaima', 'Villarrica': 'Villarrica',
       'Chaitén': 'Chaiten', 'Copahue': 'Copahue', 'Planchón-Peteroa': 'PlanchonPeteroa',
       'Puyehue-Cordón Caulle': 'PuyehueCordonCaulle', 'Chillán, Nevados de': 'NevadosDeChillan', 'Tupungatito': 'Tupungatito'}
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3, "NevadosDeChillan": 5, "Chaiten": 5,
         "Villarrica": 5, "Llaima": 5, "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}
KA = {375: 18.0 * 140625, 750: 19.7 * 562500, 1000: 18.9 * 1e6}
LAM = {375: 3.74, 750: 4.05, 1000: 3.929}   # banda MIR que usa NUESTRO codigo (MODIS: B21, D21)
C1, C2 = 1.191042e8, 14388.0
def planck(T, l): return C1 / (l ** 5 * (math.exp(C2 / (l * T)) - 1))
T0, T1 = datetime(2025, 2, 15), datetime(2025, 12, 1)
osf = pd.read_csv(R / 'data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv')
osf['t'] = pd.to_datetime(osf.timeUTC, format='%d/%m/%Y %H:%M', errors='coerce')
o = osf[osf.Volc_Name.isin(MAP) & (osf.t >= T0) & (osf.t < T1) & (osf.Dayflag == 0)].copy()
o['vol'] = o.Volc_Name.map(MAP); o['res'] = o.Resolution.astype(int)
def res(s): return 1000 if s.startswith('MODIS') else (750 if s.endswith('_750') else 375)
ours = {}
for v in INNER:
    for r in json.load(open(R / f'data/mirova_equivalent/{v}.json', encoding='utf-8'))['records']:
        dt = datetime.strptime(r['datetime_utc'], '%Y-%m-%d %H:%M')
        if T0 - timedelta(hours=7) <= dt < T1 + timedelta(hours=7):
            ours.setdefault((v, res(r['sensor'])), []).append((dt, r))
for k in ours: ours[k].sort(key=lambda x: x[0])
def crater(r, v):
    pc = r.get('primary_cluster') or {}
    vr = pc.get('vrp_mw') or 0; d = pc.get('centroid_dist_km')
    return vr > 0 and d is not None and d <= INNER[v] and vr <= 50000 and r.get('distance_class') in ('summit', None)
def nearest(v, rs, t, tol=10):
    L = ours.get((v, rs), []); ts = [x[0] for x in L]; i = bisect.bisect_left(ts, t); best = None
    for j in (i - 1, i):
        if 0 <= j < len(L) and abs((L[j][0] - t).total_seconds()) <= tol * 60:
            if best is None or abs((L[j][0] - t).total_seconds()) < abs((best[0] - t).total_seconds()): best = L[j]
    return best
def core_pixels(r, inner):
    """Replica del conjunto de pixeles que suma f5_core_vrp_mw (misma logica, devuelve la lista)."""
    px = r.get('anomaly_pixels') or []; pc = r.get('primary_cluster') or {}
    if not px or pc.get('centroid_lat') is None: return None
    cand = [p for p in px if p.get('lat') is not None and _hav_km(p['lat'], p['lon'], pc['centroid_lat'], pc['centroid_lon']) <= inner]
    if not cand: return None
    pk = max(range(len(cand)), key=lambda i: (cand[i].get('vrp_mw') or 0, -i))
    # max() devuelve el primero en empates si usamos -i; f5 usa '>' estricto => primero. ok
    return [p for i, p in enumerate(cand) if i == pk or _hav_km(p['lat'], p['lon'], cand[pk]['lat'], cand[pk]['lon']) <= F5_R_CORE_KM
            or (p.get('bt_k') or 0) >= F5_BT_EXT_K]

def build(shift_h=0):
    rows = []
    for _, x in o[(o['class'] == 1) & (o.VRP > 0)].iterrows():
        m = nearest(x.vol, x.res, x.t.to_pydatetime() + timedelta(hours=shift_h))
        if m is None or not crater(m[1], x.vol): continue
        r = m[1]; pc = r['primary_cluster']; ka = KA[x.res]; lam = LAM[x.res]; inner = INNER[x.vol]
        d = dict(vol=x.vol, res=x.res, satzen=abs(x.SatZen), Npix=x.Npix, osf_mw=x.VRP / 1e6,
                 hot1=x.Tot_Lmir_hot / x.Npix, bk1=x.Tot_Lmir_bk / x.Npix, ex1=(x.Tot_Lmir_hot - x.Tot_Lmir_bk) / x.Npix,
                 pc_mw=pc['vrp_mw'], pc_n=pc['n_pixels'], n_anom=r.get('n_anomalous_pixels'), sensor=r['sensor'],
                 t_bg=r.get('t_bg_k'), dt_min=(m[0] - x.t.to_pydatetime()).total_seconds() / 60,
                 test1=r.get('final_hotspot_source') == 'test1_roi', single=pc.get('single_pixel_mode'))
        d['Lbg_ring'] = planck(r['t_bg_k'], lam) if r.get('t_bg_k') else np.nan
        px = r.get('anomaly_pixels') or []
        inn = [p for p in px if (p.get('dist_km') is not None and p['dist_km'] <= inner)]
        d['scene_inner_mw'] = sum(p.get('vrp_mw') or 0 for p in inn); d['scene_inner_n'] = len(inn)
        d['scene_mw'] = r.get('vrp_mw'); d['n_px_saved'] = len(px)
        if x.res == 375:
            f5 = r.get('f5_core_vrp_mw'); cp = core_pixels(r, inner)
            d['f5_persist'] = f5
            if cp:
                d['core_mw'] = sum(p.get('vrp_mw') or 0 for p in cp); d['core_n'] = len(cp)
                pos = [p for p in cp if (p.get('vrp_mw') or 0) > 0 and p.get('bt_k')]
                if pos:
                    Lh = [planck(p['bt_k'], lam) for p in pos]
                    d['hot1_ours'] = float(np.mean([planck(p['bt_k'], lam) for p in cp if p.get('bt_k')]))
                    d['Lbg_imp'] = float(np.median([Lh[i] - p['vrp_mw'] * 1e6 / ka for i, p in enumerate(pos)]))
                    d['n_zero'] = len(cp) - len(pos)
            pub, npub = (f5, d.get('core_n')) if (f5 is not None and d.get('core_n')) else (pc['vrp_mw'], pc['n_pixels'])
        else:
            pub, npub = pc['vrp_mw'], pc['n_pixels']
        d['pub_mw'], d['pub_n'] = pub, npub
        rows.append(d)
    return pd.DataFrame(rows)

d = build(0)
neg = build(6)
print(f'CONTROL NEGATIVO: pares con desplazamiento +6 h = {len(neg)} (real = {len(d)})')
d['R_pc'] = d.pc_mw / d.osf_mw; d['R'] = d.pub_mw / d.osf_mw
d['F_n'] = d.pub_n / d.Npix
d['ex_ours'] = d.pub_mw * 1e6 / (d.res.map(KA) * d.pub_n)
d['F_ex'] = d.ex_ours / d.ex1
d['zbin'] = pd.cut(d.satzen, [0, 15, 25, 35, 50, 90])
d.to_csv(R / 'experiments/_s139_audit/magnitud/02_pares.csv', index=False)
print('pares por res', d.res.value_counts().to_dict(), '| |dt| max min', d.dt_min.abs().max())
print('\n== reproducir eje6: mediana R con pc.vrp_mw por res'); print(d.groupby('res').R_pc.median().round(3))
print('== R publicado (V375 = f5 persistido, fallback pc)'); print(d.groupby('res').R.median().round(3))
if 'f5_persist' in d:
    s = d[(d.res == 375) & d.core_mw.notna() & d.f5_persist.notna()]
    print('chequeo replica f5: |core_mw - f5_persist|>1e-3 en', ((s.core_mw - s.f5_persist).abs() > 1e-3).sum(), 'de', len(s))
    print('V375 pares con f5 persistido:', d[(d.res == 375)].f5_persist.notna().sum(), 'de', (d.res == 375).sum())
def gm(x): x = x[(x > 0) & np.isfinite(x)]; return float(np.exp(np.log(x).mean())) if len(x) else np.nan
def table(g):
    return pd.Series({'n': len(g), 'R_med': g.R.median(), 'R_gm': gm(g.R), 'Fn_gm': gm(g.F_n), 'Fex_gm': gm(g.F_ex),
                      'Fn_med': g.F_n.median(), 'Fex_med': g.F_ex.median(), 'Npix_med': g.Npix.median(), 'pub_n_med': g.pub_n.median(),
                      'pc_n_med': g.pc_n.median(), 'R_pc_med': g.R_pc.median()})
pd.set_option('display.width', 250); pd.set_option('display.max_columns', None)
print('\n== descomposicion geometrica (R_gm = Fn_gm * Fex_gm exacto) por res'); print(d.groupby('res').apply(table).round(3))
print('\n== por res x SatZen'); print(d.groupby(['res', 'zbin'], observed=True).apply(table).round(3))
print('\n== por res x volcan'); print(d.groupby(['res', 'vol']).apply(table).round(3))
print('\n== V375 por n publicado (1,2,3-5,6+)')
v = d[d.res == 375].copy(); v['nb'] = pd.cut(v.pub_n, [0, 1, 2, 5, 1000])
print(v.groupby('nb', observed=True).apply(table).round(3))
print('\n== V375 por Npix MIROVA (1,2,3-5,6+)'); v['Nb'] = pd.cut(v.Npix, [0, 1, 2, 5, 1000])
print(v.groupby('Nb', observed=True).apply(table).round(3))
print('\n== V375 separacion del exceso por pixel: nivel caliente y fondo (mediana)')
v = v[v.Lbg_imp.notna()]
v['F_hot'] = (v.hot1_ours - v.bk1) / v.ex1          # exceso con NUESTRO nivel caliente y el FONDO de MIROVA
v['F_bg'] = v.F_ex / v.F_hot                        # lo que agrega usar NUESTRO fondo
v['dbg_imp'] = v.Lbg_imp / v.bk1; v['dbg_ring'] = v.Lbg_ring / v.bk1; v['dhot'] = v.hot1_ours / v.hot1
print('n', len(v), '| mediana Lbg_imp/bk1', round(v.dbg_imp.median(), 4), '| Lbg_ring/bk1', round(v.dbg_ring.median(), 4),
      '| hot1_ours/hot1', round(v.dhot.median(), 4))
print('gm F_ex', round(gm(v.F_ex), 3), 'gm F_hot', round(gm(v.F_hot), 3), 'gm F_bg', round(gm(v.F_bg), 3), '(F_hot<=0 descartados en gm:', (v.F_hot <= 0).sum(), ')')
T = lambda L, l: (C2 / (l * math.log(C1 / (l ** 5 * L) + 1)) if L > 0 else np.nan)
v['Tbg_imp'] = [T(L, 3.74) for L in v.Lbg_imp]; v['Tbk_osf'] = [T(L, 3.74) for L in v.bk1]; v['Thot1'] = [T(L, 3.74) for L in v.hot1]
v['Thot_ours'] = [T(L, 3.74) for L in v.hot1_ours]
print('T (K) medianas: fondo nuestro implicito', round(v.Tbg_imp.median(), 2), '| t_bg_k anillo', round(v.t_bg.median(), 2),
      '| fondo MIROVA bk/Npix', round(v.Tbk_osf.median(), 2), '| caliente MIROVA hot/Npix', round(v.Thot1.median(), 2), '| caliente nuestro', round(v.Thot_ours.median(), 2))
print('diferencia de fondo (nuestro implicito - MIROVA) en K, cuantiles', (v.Tbg_imp - v.Tbk_osf).quantile([.1, .25, .5, .75, .9]).round(2).to_dict())
print('fondo implicito vs anillo: |Lbg_imp-Lbg_ring|/Lbg_ring > 1%:', ((v.Lbg_imp - v.Lbg_ring).abs() / v.Lbg_ring > .01).mean().round(3))
print(v.groupby('vol').apply(lambda g: pd.Series({'n': len(g), 'Tbg_imp-Tbk': (g.Tbg_imp - g.Tbk_osf).median(), 'Thot_ours-Thot': (g.Thot_ours - g.Thot1).median(),
      'Fhot_gm': gm(g.F_hot), 'Fbg_gm': gm(g.F_bg), 'Fn_gm': gm(g.F_n), 'R_gm': gm(g.R), 'test1_frac': g.test1.mean()})).round(3))
print('\n== V375 por SatZen: Fhot/Fbg'); print(v.groupby('zbin', observed=True).apply(lambda g: pd.Series({'n': len(g), 'Fn': gm(g.F_n), 'Fhot': gm(g.F_hot), 'Fbg': gm(g.F_bg), 'R': gm(g.R),
      'dTbg': (g.Tbg_imp - g.Tbk_osf).median()})).round(3))
print('\n== escena dentro del radio vs publicado (V375), mediana de razones a MIROVA')
w = d[d.res == 375]
print('R pub', round(w.R.median(), 3), '| R pc', round(w.R_pc.median(), 3), '| R suma anomaly_pixels dentro inner', round((w.scene_inner_mw / w.osf_mw).median(), 3),
      '| R vrp_mw escena', round((w.scene_mw / w.osf_mw).median(), 3), '| pares con 100 px guardados (tope)', (w.n_px_saved >= 100).sum())
print('n dentro inner / Npix mediana', round((w.scene_inner_n / w.Npix).median(), 3), '| n_anom / Npix', round((w.n_anom / w.Npix).median(), 3))
print('\n== control positivo: correlacion Spearman con SatZen (V375): Npix', round(w.Npix.corr(w.satzen, method='spearman'), 3),
      '| pub_n', round(w.pub_n.corr(w.satzen, method='spearman'), 3), '| pc_n', round(w.pc_n.corr(w.satzen, method='spearman'), 3),
      '| R', round(w.R.corr(w.satzen, method='spearman'), 3))
print('== Spearman pub_n vs Npix por res:', d.groupby('res').apply(lambda g: round(g.pub_n.corr(g.Npix, method='spearman'), 3)).to_dict())
