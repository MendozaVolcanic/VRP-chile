"""S139 magnitud, paso 4: (a) nivel caliente y fondo dentro del subconjunto de igual conteo
(si F_ex ~1 ahi es porque ambos coinciden o porque se compensan); (b) pares cuya fuente es el
Test 1 (final_hotspot_source=test1_roi) contra el resto: F_n, F_hot, F_bg.
Instrumento: si el fondo implicito fuera siempre igual al del anillo (L(t_bg_k)), F_bg no
distinguiria Test 1 del resto; se reporta la fraccion donde difiere. Denominador: pares V375 de 02."""
import pathlib, numpy as np, pandas as pd, math
R = pathlib.Path(__file__).resolve().parents[3]
d = pd.read_csv(R / 'experiments/_s139_audit/magnitud/02_pares.csv'); d = d[(d.res == 375) & d.Lbg_imp.notna() & (d.R > 0)].copy()
d['F_hot'] = (d.hot1_ours - d.bk1) / d.ex1; d['F_bg'] = d.F_ex / d.F_hot
C1, C2 = 1.191042e8, 14388.0
T = lambda L: C2 / (3.74 * math.log(C1 / (3.74 ** 5 * L) + 1)) if L > 0 else np.nan
d['dTbg'] = [T(a) - T(b) for a, b in zip(d.Lbg_imp, d.bk1)]; d['dTring'] = [T(a) - T(b) for a, b in zip(d.Lbg_ring, d.bk1)]
d['imp_vs_ring'] = (d.Lbg_imp - d.Lbg_ring) / d.Lbg_ring
d = d[d.F_hot > 0]
gm = lambda x: float(np.exp(np.log(x[(x > 0)]).mean()))
def t(g): return pd.Series({'n': len(g), 'R': gm(g.R), 'Fn': gm(g.F_n), 'Fhot': gm(g.F_hot), 'Fbg': gm(g.F_bg), 'dTbg_med_K': g.dTbg.median(),
                            'dTring_med_K': g.dTring.median(), 'frac_imp_ne_ring': (g.imp_vs_ring.abs() > .01).mean(), 'imp_vs_ring_med': g.imp_vs_ring.median()})
pd.set_option('display.width', 250); pd.set_option('display.max_columns', None)
print('igual conteo:'); print(t(d[d.pub_n == d.Npix]).round(3).to_dict())
print('conteo distinto:'); print(t(d[d.pub_n != d.Npix]).round(3).to_dict())
print('test1_roi vs resto:'); print(d.groupby('test1').apply(t).round(3))
print('por volcan:'); print(d.groupby('vol').apply(t).round(3))
