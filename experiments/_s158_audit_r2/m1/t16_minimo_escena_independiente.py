# M1 T16. Recuento propio de F4-H1 / V3-F4-H1: fraccion de pasadas nocturnas cuyo umbral estadistico de escena
# mu+10*sigma (dNTI) queda bajo el minimo fijo. Pregunta 1: si diag_sd_dnti no fuera el sigma que usa el umbral de
# escena (por ejemplo si fuera el del pool de la cumbre), el control sobre el umbral efectivo lo mostraria: se compara
# con la regla C2_DNTI_SCENE_NIGHT/ DNTI_CONTEXTUAL_C1_SCENE leidas de pipeline.profile. Pregunta 2: control positivo =
# la fraccion bajo 0.010 debe ser mucho menor que bajo 0.0225 (monotonia) y mu/sd no deben ser constantes.
# Noche: solar_zenith_deg > 90. Ventana: 2026-03-01.. (todos los records son K, ver t2b). Tier A.
import json,os,numpy as np,pandas as pd,subprocess,sys
os.environ['VRP_PROFILE']='mirova_equivalent'
import importlib; sys.path.insert(0,'.')
import pipeline.profile as P
print('perfil efectivo: C2_DNTI_SCENE_NIGHT',P.C2_DNTI_SCENE_NIGHT,'DNTI_CONTEXTUAL_C1_SCENE',P.DNTI_CONTEXTUAL_C1_SCENE,'DNTI_CONTEXTUAL_C1_SUMMIT',P.DNTI_CONTEXTUAL_C1_SUMMIT,'C2 summit',P.C2_DNTI_SUMMIT_NIGHT)
TIER=['PuyehueCordonCaulle','Villarrica','Lascar','Copahue','NevadosDeChillan','Llaima','Chaiten','PlanchonPeteroa','Lastarria','Isluga','Tupungatito']
rows=[]
for v in TIER:
    for r in json.load(open(f'data/mirova_equivalent/{v}.json',encoding='utf-8'))['records']:
        if r['datetime_utc']<'2026-03-01' or (r.get('solar_zenith_deg') or 0)<=90: continue
        s=r['sensor']; sc='MODIS' if s.startswith('MODIS') else ('V750' if s.endswith('_750') else 'V375')
        rows.append((sc,r.get('diag_mu_dnti'),r.get('diag_sd_dnti'),r['datetime_utc']))
d=pd.DataFrame(rows,columns=['s','mu','sd','t'])
for s,g in d.groupby('s'):
    ok=g.dropna(subset=['mu','sd'])
    thr=ok.mu+P.C2_DNTI_SCENE_NIGHT*ok.sd
    print(f'{s}: n nocturnos {len(g)}, con diag {len(ok)} | mu+{P.C2_DNTI_SCENE_NIGHT:g}sd < 0.010: {(thr<0.010).mean():.3f} | < 0.020: {(thr<0.020).mean():.3f} | < 0.0225: {(thr<0.0225).mean():.3f} | mediana {thr.median():.4f} | mu constante? {ok.mu.nunique()>5} sd mediana {ok.sd.median():.5f}')
k=d[(d.s=='V750')&(d.t>='2026-09-18')].dropna(subset=['mu','sd']); t=k.mu+10*k.sd
print('V750 ventana K (2026-09-18..): n',len(k),'<0.010: %.3f  <0.0225: %.3f'%((t<0.010).mean(),(t<0.0225).mean()))
