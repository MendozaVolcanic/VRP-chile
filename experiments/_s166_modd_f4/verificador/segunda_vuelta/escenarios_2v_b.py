# -*- coding: utf-8 -*-
"""Escenario T2c: casi toda la identidad sale por motivo sellado; y T6: tabla de 'protegida sellada de K' con OCR."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import escenarios_2v as S
P, EV, F, mundo, dia, correr, ident_ok = S.P, S.EV, S.F, S.mundo, S.dia, S.correr, S.ident_ok

f = mundo()
n = sum(1 for x in f if x["grilla_censo"])
sobrevive = [x for x in f if x["grilla_censo"]][:1]
for x in f:
    if x["grilla_censo"] and x is not sobrevive[0]:
        x["motivo"] = "volcan_fuera_del_granulo"
idn = {(x["vol"], x["dt"]): v for x in sobrevive for v in [dict(mismo_granulo=True, misma_mascara=True, dvrp=0.0, misma_clase=True)]}
r = correr(f, ident=idn, n_grillas=n)
c = r["controles"]
print("T2c: %d de %d pasadas con grilla del censo marcadas volcan_fuera_del_granulo" % (n - 1, n))
print("   identidad", c["identidad"]["estado"], "n_con_grilla", c["identidad"]["n_con_grilla"], "| cobertura", c["cobertura"]["estado"],
      "| fuera_del_denominador", c["cobertura"]["fuera_del_denominador"], "| veredicto", r["veredicto"], "| P2 V", r["brazos"]["V"]["p2"]["estado"])
