# -*- coding: utf-8 -*-
"""d01 CONTROL POSITIVO: la divergencia D13. Mi metodo debe dar ~31 % en RECORDS y ~70,7 % en MAGNITUD.
Preguntas del instrumento: (1) si la cerca no existiera en los datos (todo summit) daria 0 % en ambos: fallaria
contra el valor esperado, si. (2) instrumento muerto (0 records) imprime n=0 y aborta.
Magnitud: predicado RECONSTRUIDO en Python (no node): se espera 'cerca de' 70,7, no identidad."""
import io, sys, json
from dlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = cargar(); R = [(v, r) for v in VOLS for r in D[v]]
assert len(R) > 50000
def frac_records(lo, hi):
    den = [r for v, r in R if lo <= r["datetime_utc"][:10] <= hi and pcv(r) > 0]
    num = [r for r in den if r.get("distance_class") and r["distance_class"] != "summit"]
    return len(num), len(den), round(100*len(num)/len(den), 2)
def frac_mw(lo, hi):
    sub = [r for v, r in R if lo <= r["datetime_utc"][:10] <= hi and es_noche(r)]
    a = sum(publicado(r) for r in sub); b = sum(sin_cerca(r) for r in sub)
    return len(sub), round(a, 2), round(b, 2), round(100*(b-a)/b, 1)
out = {"records_historia_al_2026-08-25": frac_records("2000", "2026-08-25"),
       "records_regimen_actual_0901_0919": frac_records("2026-09-01", "2026-09-19"),
       "mw_regimen_actual_0901_0919(n,dibuja,sin_cerca,pct_apagado)": frac_mw("2026-09-01", "2026-09-19"),
       "mw_regimen_previo_0601_0825": frac_mw("2026-06-01", "2026-08-25"),
       "mw_toda_la_historia_al_0825": frac_mw("2000", "2026-08-25")}
json.dump(out, open("d01_control_D13.json", "w"), indent=1)
for k, v in out.items(): print(k, v)
