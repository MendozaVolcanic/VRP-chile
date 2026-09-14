"""S139 magnitud, paso 8: la razon segun cuan disperso esta lo que MIROVA suma.
OSF trae LAT/LON (centroide de sus pixeles) y Max_Dist (m, la mayor distancia de un pixel al volcan).
Si parte del deficit es que MIROVA suma pixeles lejanos del crater que nosotros no publicamos
(suma de ROI vs cumulo, S129), R y F_n deben caer cuando Max_Dist crece; control positivo: NdC
feb-2025 (incendio a 15-19 km, paso 7) debe caer en el bin mas lejano con R ~0.
Instrumento: si Max_Dist no informara nada, R seria plano entre bins. Denominador: pares V375 de 02."""
import pathlib, math, numpy as np, pandas as pd
R = pathlib.Path(__file__).resolve().parents[3]
src = open(R / 'experiments/_s139_audit/magnitud/02_descomposicion_pares.py', encoding='utf-8').read().split('d = build(0)')[0]
src = src.replace("d['pub_mw'], d['pub_n'] = pub, npub", "d['pub_mw'], d['pub_n'] = pub, npub; d['maxd_km'] = x.Max_Dist / 1000; d['mlat'] = x.LAT; d['mlon'] = x.LON; d['vlat'] = x.Volc_LAT; d['vlon'] = x.Volc_LON")
g = {'__file__': str(R / 'experiments/_s139_audit/magnitud/02_descomposicion_pares.py')}
exec(compile(src, '02', 'exec'), g)
d = g['build'](0)
d = d[d.res == 375].copy()
hav = g['_hav_km']
d['mcen_km'] = [hav(a, b, c, e) for a, b, c, e in zip(d.mlat, d.mlon, d.vlat, d.vlon)]
d['R'] = d.pub_mw / d.osf_mw; d['F_n'] = d.pub_n / d.Npix
d['F_ex'] = d.pub_mw * 1e6 / (18.0 * 140625 * d.pub_n) / d.ex1
gm = lambda x: float(np.exp(np.log(x[(x > 0) & np.isfinite(x)]).mean()))
def t(q): return pd.Series({'n': len(q), 'R_gm': gm(q.R), 'Fn_gm': gm(q.F_n), 'Fex_gm': gm(q.F_ex), 'Npix_med': q.Npix.median(), 'pub_n_med': q.pub_n.median(), 'R_med': q.R.median()})
pd.set_option('display.width', 250); pd.set_option('display.max_columns', None)
d['maxd_bin'] = pd.cut(d.maxd_km, [-.01, .5, 1, 2, 3, 5, 100])
d['inner_ok'] = d.maxd_km <= d.vol.map(g['INNER'])
print('== por Max_Dist de MIROVA (km)'); print(d.groupby('maxd_bin', observed=True).apply(t).round(3))
print('\n== Max_Dist dentro del inner_radius del volcan vs fuera'); print(d.groupby('inner_ok').apply(t).round(3))
print('\n== centroide MIROVA a > inner del volcan, por volcan'); print(d[d.mcen_km > d.vol.map(g['INNER'])].groupby('vol').apply(t).round(3))
x = d[d.maxd_km <= 1.0]
print('\n== solo pares con Max_Dist <= 1 km (lo que MIROVA suma esta pegado al crater), por volcan'); print(x.groupby('vol').apply(t).round(3))
y = d[d.mcen_km <= d.vol.map(g['INNER'])]
print('\n== total excluyendo pares con centroide MIROVA fuera del inner:', t(y).round(3).to_dict(), '| total todos:', t(d).round(3).to_dict())
