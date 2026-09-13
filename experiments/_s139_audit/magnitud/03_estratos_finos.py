"""S139 magnitud, paso 3: estratos finos sobre 02_pares.csv (sin volver a leer records).

Por que: (a) Simpson (regla S126): la mezcla de volcanes cambia entre bins de SatZen, asi que se
repite la tendencia dentro de Lascar e Isluga y Lastarria; (b) control de instrumento: cuando
MIROVA y nosotros contamos el MISMO numero de pixeles, F_n = 1 por construccion y la razon queda
en F_ex puro; si k, A, banda o fondo estuvieran mal, ahi se veria (y si el remuestreo importa,
F_ex caeria con SatZen dentro de ese subconjunto).
Denominador: 1.499 pares V375 nocturnos 2025-02-15 a 2025-12-01 (02).
"""
import pathlib, numpy as np, pandas as pd
R = pathlib.Path(__file__).resolve().parents[3]
d = pd.read_csv(R / 'experiments/_s139_audit/magnitud/02_pares.csv')
d = d[d.res == 375].copy()
d['zbin'] = pd.cut(d.satzen, [0, 15, 25, 35, 50, 90])
gm = lambda x: float(np.exp(np.log(x[(x > 0) & np.isfinite(x)]).mean())) if ((x > 0) & np.isfinite(x)).any() else np.nan
pd.set_option('display.width', 250); pd.set_option('display.max_columns', None)
def t(g):
    return pd.Series({'n': len(g), 'R_gm': gm(g.R), 'Fn_gm': gm(g.F_n), 'Fex_gm': gm(g.F_ex), 'Npix_med': g.Npix.median(),
                      'pub_n_med': g.pub_n.median(), 'ex1_med': g.ex1.median(), 'ex_ours_med': g.ex_ours.median()})
print('== mismo numero de pixeles (pub_n == Npix): F_ex puro')
s = d[d.pub_n == d.Npix]
print(t(s).round(3).to_dict())
print(s.groupby('zbin', observed=True).apply(t, include_groups=False).round(3))
print(s.assign(Nk=s.Npix).groupby('Nk').apply(t).round(3).head(6))
print('\n== tendencia SatZen dentro de volcan (n>=150)')
for v in ['Lascar', 'Isluga', 'Lastarria', 'PuyehueCordonCaulle', 'PlanchonPeteroa']:
    print(v); print(d[d.vol == v].groupby('zbin', observed=True).apply(t, include_groups=False).round(3))
print('\n== reparto del log de la razon (V375 total): share = mean(log F)/mean(log R)')
lr = np.log(d.R[d.R > 0]).mean(); print('log R', round(lr, 4), '| share F_n', round(np.log(d.F_n).mean() / lr, 3), '| share F_ex', round(np.log(d.F_ex[d.F_ex > 0]).mean() / lr, 3))
v = d[d.Lbg_imp.notna()].copy()
v['F_hot'] = (v.hot1_ours - v.bk1) / v.ex1; v['F_bg'] = v.F_ex / v.F_hot
v = v[(v.F_hot > 0) & (v.R > 0)]
lr = np.log(v.R).mean()
print('subconjunto con fondo implicito n', len(v), '| gm R', round(np.exp(lr), 3), '| gm F_n', round(gm(v.F_n), 3), '| gm F_hot', round(gm(v.F_hot), 3),
      '| gm F_bg', round(gm(v.F_bg), 3), '| gm seleccion F_n*F_hot', round(gm(v.F_n * v.F_hot), 3))
print('share seleccion (F_n*F_hot)', round(np.log(v.F_n * v.F_hot).mean() / lr, 3), '| share fondo F_bg', round(np.log(v.F_bg).mean() / lr, 3))
print('\n== sin Chaiten/Villarrica/NdC (volcanes con R>1 o colapso):')
w = d[~d.vol.isin(['Chaiten', 'Villarrica', 'NevadosDeChillan'])]; print(t(w).round(3).to_dict())
print('\n== V375 fraccion de pares con fuente test1_roi y su R_gm:', round(d.test1.mean(), 3), round(gm(d[d.test1].R), 3), 'vs resto', round(gm(d[~d.test1].R), 3))
print('== Npix MIROVA vs SatZen en Chile (mediana por bin) y global en 01: Chile', d.groupby('zbin', observed=True).Npix.median().to_dict())
