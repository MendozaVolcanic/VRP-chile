"""Tarea 1.19: R dividido por la prediccion de la huella, por zona de agregacion. Si la huella explica la dependencia
angular, R / (A_nadir/A_nativo) queda plano entre zonas. Control que puede fallar: dividir por la huella SIN
agregacion (crecimiento suave): si los escalones importan, ese cociente NO queda plano. Pares S139."""
import sys, io, json, pathlib
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from huella import area_rel
p = pd.read_csv(r'C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/experiments/_s139_audit/magnitud/02_pares.csv')
p = p[(p.res == 375) & (p.R > 0)].copy()
p['q_agr'] = p.R * [area_rel(z) for z in p.satzen]
p['q_sua'] = p.R * [area_rel(z, False) for z in p.satzen]
p['zona'] = pd.cut(p.satzen, [0, 20, 36.32, 44, 52.66, 70], labels=['0-20', '20-36.3', '36.3-44', '44-52.7', '52.7-70']).astype(str)
rng = np.random.default_rng(11); out = {}
for nom, d in {'V375 todos': p, 'sin kernel local (Lascar, Isluga, Copahue)': p[p.vol.isin(['Lascar', 'Isluga', 'Copahue'])], 'Lascar': p[p.vol == 'Lascar']}.items():
    t = d.groupby('zona').agg(n=('R', 'size'), R=('R', 'median'), R_sobre_huella=('q_agr', 'median'), R_sobre_suave=('q_sua', 'median'))
    for c in ('R', 'q_agr', 'q_sua'):
        bs = np.array([[d[d.zona == z][c].sample(frac=1, replace=True, random_state=int(rng.integers(1e9))).median() for z in t.index] for _ in range(300)])
        lo, hi = np.percentile(bs, [2.5, 97.5], axis=0)
        t[f'{c}_ic'] = [f'[{a:.2f}; {b:.2f}]' for a, b in zip(lo, hi)]
    rango = {c: round(float(t[c].max() / t[c].min()), 3) for c in ('R', 'R_sobre_huella', 'R_sobre_suave')}
    print(f'\n=== {nom}  (max/min entre zonas: {rango})'); print(t.round(3).to_string())
    out[nom] = dict(tabla=t.round(4).reset_index().to_dict('list'), max_sobre_min=rango)
pathlib.Path(__file__).with_name('03d_salida.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
