"""V1: ¿desde qué fecha los records de produccion fueron escritos por K?
Pregunta 1 del instrumento: si el backfill NO hubiera usado K, triggered_test1 seguiría True en
parte de los records de 09-18..10-18; si lo uso, cae a 0. Pregunta 2: si el campo no existiera
o fuera siempre False, el control (records antes del 2026-09-18) tambien daria 0 -> se mide aparte.
Ventana: records por datetime_utc; denominador = records del tramo. Corpus: data/mirova_equivalent/*.json
del worktree en cb90031a (origin/main 2026-10-19)."""
import json, glob, os, collections
tramos=[('2026-08-01','2026-09-18'),('2026-09-18','2026-10-18T09:57:30'),('2026-10-18T09:57:30','2026-12-31')]
tot=collections.Counter(); t1=collections.Counter(); proc=collections.defaultdict(set)
for f in sorted(glob.glob('data/mirova_equivalent/*.json')):
    d=json.load(open(f,encoding='utf-8')); recs=d['records'] if isinstance(d,dict) else d
    for r in recs:
        dt=r.get('datetime_utc','')
        for a,b in tramos:
            if a<=dt<b:
                tot[a]+=1; t1[a]+= bool(r.get('triggered_test1')) or (r.get('n_test1_pixels') or 0)>0
                proc[a].add((r.get('processed_utc') or '')[:10])
for a,b in tramos:
    print(f"tramo {a}..{b}: records={tot[a]} con_test1={t1[a]} ({100*t1[a]/max(tot[a],1):.1f}%) fechas_processed_utc={sorted(proc[a])[:3]}..{sorted(proc[a])[-3:]}")
