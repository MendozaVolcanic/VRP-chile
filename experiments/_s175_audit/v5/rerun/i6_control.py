# -*- coding: utf-8 -*-
"""Línea base roja (3): un record pareado desfasado 3 min a propósito tiene que aparecer en I6 como «sin par a 120 s con
record a 120-600 s». Además cuenta alertas nocturnas de la referencia contra pasadas nuestras para ver que el cero de
I6 no es un instrumento muerto. Usa f5_medir.i6 sin modificarla."""
import copy, os, sys, collections
from datetime import timedelta
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import f5_medir as fm
B = fm.cargar()
pv, ns, nv, n = fm.bp.indexar_referencia(B["filas"], B["coords"], B["win"], regla_minimas=fm.aw.REGLA_MINIMAS)
n_al = collections.Counter((vb[1]) for vb, l in pv.items() for d, f in l if fm.bp.es_alerta(f["tipo"]))
print("filas de alerta nocturnas por sensor (sin dedup por minuto):", dict(n_al))
B2 = copy.copy(B); B2["recs"] = [dict(r) for r in B["recs"]]
obj = next(r for r in B2["recs"] if r["lab"] == "pos" and r["vol"] == "NevadosDeChillan" and r["b"] == "VIIRS375")
print("record desfasado:", obj["vol"], obj["sensor"], obj["dt"])
obj["dt"] = obj["dt"] + timedelta(minutes=3)
fm.i6(B2, pv)
print("control:", fm.R["I6"]["alertas_mirova"], fm.R["I6"]["casos_120_600"][:3])
