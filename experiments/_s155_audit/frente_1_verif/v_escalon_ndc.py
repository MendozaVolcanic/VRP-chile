"""Aproximacion (NO es el predicado del tablero, A97): records summit con primary_cluster.vrp_mw>0,
por tramo, en 34cea39e (C0 en 09-18..10-18) y en HEAD (K reprocesado). Sirve sólo para ver dónde cae el
escalon en la serie que ve el operador. Control: tramo 08-18..09-18 no fue reprocesado -> debe dar igual en
ambas refs (si no da igual, el instrumento no aisla el reproceso)."""
import json, subprocess, sys
vols=['NevadosDeChillan','Villarrica','Lascar']
tramos=[('2026-08-18','2026-09-18'),('2026-09-18','2026-10-18T09:57:30')]
for ref in ['34cea39e','HEAD']:
    for v in vols:
        d=json.loads(subprocess.run(['git','show',f'{ref}:data/mirova_equivalent/{v}.json'],capture_output=True).stdout)
        recs=d['records'] if isinstance(d,dict) else d
        out=[]
        for a,b in tramos:
            sel=[r for r in recs if a<=r.get('datetime_utc','')<b]
            pub=[r for r in sel if r.get('distance_class')=='summit' and ((r.get('primary_cluster') or {}).get('vrp_mw') or 0)>0]
            out.append(f"{a[:10]}: {len(pub)}/{len(sel)}")
        print(ref,v,' | '.join(out))
