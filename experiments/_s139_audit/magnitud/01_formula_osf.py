"""S139 magnitud, paso 1: verificar la formula de MIROVA en el OSF v2.5, todas las filas.

Hipotesis: VRP = k * A_fija * (Tot_Lmir_hot - Tot_Lmir_bk), con Tot_* = suma sobre Npix,
k/A fijos por resolucion (375: 18.0*140625; 750: 19.7*562500; 1000: 18.9*1e6), sin SatZen.

Pregunta 1 (si lo medido estuviera roto, lo veria?): si MIROVA usara area variable con SatZen,
el cociente VRP/(hot-bk) creceria con SatZen; lo mido por bins. Si usara otro k, el cociente
no daria la constante. Pregunta 2 (instrumento muerto?): control negativo, cociente con A
equivocada (usar el k*A de otra resolucion) debe fallar; control positivo, Npix vs SatZen.
Denominador: todas las filas del CSV (615.470), luego subconjunto Chile.
"""
import pathlib, numpy as np, pandas as pd
R = pathlib.Path(__file__).resolve().parents[3]
o = pd.read_csv(R / 'data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv')
print('filas', len(o), 'Resolution', o.Resolution.value_counts().to_dict())
KA = {375: 18.0 * 140625, 750: 19.7 * 562500, 1000: 18.9 * 1e6}
o['dL'] = o.Tot_Lmir_hot - o.Tot_Lmir_bk
o = o[o.Resolution.isin(KA)]
o['ka_eff'] = o.VRP / o.dL
o['rel'] = o.ka_eff / o.Resolution.map(KA)
bins = [0, 15, 25, 35, 50, 90]
o['zbin'] = pd.cut(o.SatZen.abs(), bins)
print('\n== cociente VRP/(k*A*(hot-bk)), por resolucion: cuantiles')
print(o.groupby('Resolution').rel.describe(percentiles=[.01, .5, .99]).round(5))
print('fraccion |rel-1|<0.001 por res:', o.assign(ok=(o.rel - 1).abs() < 1e-3).groupby('Resolution').ok.mean().round(5).to_dict())
print('\n== mediana rel por res x SatZen bin (si MIROVA usara area variable creceria)')
print(o.pivot_table(index='zbin', columns='Resolution', values='rel', aggfunc='median', observed=True).round(5))
print('\n== control negativo: rel con k*A de 375 aplicado a 1000 (debe dar ~7.5)')
print((o[o.Resolution == 1000].ka_eff / KA[375]).median().round(3))
print('\n== control positivo: Npix mediana/media por res x SatZen bin (remuestreo => crece)')
print(o.pivot_table(index='zbin', columns='Resolution', values='Npix', aggfunc=['median', 'mean'], observed=True).round(2))
print('\n== Npix==1 fraccion por res x bin')
print(o.assign(n1=o.Npix == 1).pivot_table(index='zbin', columns='Resolution', values='n1', aggfunc='mean', observed=True).round(3))
print('\n== radiancia de fondo media por pixel bk/Npix y exceso por pixel (hot-bk)/Npix, por res x bin (mediana)')
o['bk1'] = o.Tot_Lmir_bk / o.Npix; o['ex1'] = o.dL / o.Npix
print(o.pivot_table(index='zbin', columns='Resolution', values=['bk1', 'ex1'], aggfunc='median', observed=True).round(4))
# Tot_Lmir_bk / Npix para Chile: la T de brillo equivalente (para chequear que es suma por pixel)
C1, C2 = 1.191042e8, 14388.0
lam = {375: 3.74, 750: 4.05, 1000: 3.959}
def bt(L, l):
    return C2 / (l * np.log(C1 / (l ** 5 * L) + 1))
o['Tbk1'] = [bt(L, lam[r]) if L > 0 else np.nan for L, r in zip(o.bk1, o.Resolution)]
print('\n== T equivalente de bk/Npix (K), mediana por res y Dayflag; si Tot fuera suma deberia dar T de superficie plausible')
print(o.pivot_table(index='Dayflag', columns='Resolution', values='Tbk1', aggfunc='median').round(1))
print('T de bk total sin dividir (si NO fuera suma, esta seria la plausible):')
o['Tbk_tot'] = [bt(L, lam[r]) if L > 0 else np.nan for L, r in zip(o.Tot_Lmir_bk, o.Resolution)]
print(o[o.Npix >= 5].pivot_table(index='Dayflag', columns='Resolution', values=['Tbk1', 'Tbk_tot'], aggfunc='median').round(1))
