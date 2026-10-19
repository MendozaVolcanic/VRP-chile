# -*- coding: utf-8 -*-
"""Verificador F5, paso 9: recuento por EFECTO (no por etiqueta) de los dos mecanismos de F5-01, sobre
cumulos.json (v02). spm_x>1,001 = el modo de un pixel bajo la magnitud; sel_x>1,001 = hay energia alertada
en otros cumulos. Se separa el factor en log para ver cual pesa mas. Denominador: pasadas pareadas con
cumulo identificado. Pregunta 1: si ningun mecanismo actuara, los dos conteos darian 0 (control: la pasada
10-10 06:30 V750 tiene que salir con sel_x ~6)."""
import json, math, os, statistics
from collections import Counter
C = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cumulos.json"), encoding="utf-8"))
for b in ("VIIRS750", "MODIS"):
    ok = [o for o in C if o["b"] == b and o["estado"] == "OK" and o["pub"] > 0]
    spm = [o for o in ok if o["spm_x"] > 1.001]; sel = [o for o in ok if o["sel_x"] > 1.001]
    amb = [o for o in ok if o["spm_x"] > 1.001 and o["sel_x"] > 1.001]
    af = [o for o in ok if o["tot_x"] > 1.001]
    print("== %s: pasadas con pub>0 = %d; afectadas %d; con efecto del modo de un pixel %d; con efecto de seleccion %d; ambos %d" % (b, len(ok), len(af), len(spm), len(sel), len(amb)))
    ls = sum(math.log(o["spm_x"]) for o in af); lc = sum(math.log(o["sel_x"]) for o in af)
    print("   peso en log del deficit total: modo de un pixel %.0f %%, seleccion %.0f %%" % (100 * ls / (ls + lc), 100 * lc / (ls + lc)))
    print("   factor del modo de un pixel (afectadas por el): mediana %.2f max %.2f" % (statistics.median(o["spm_x"] for o in spm), max(o["spm_x"] for o in spm)) if spm else "")
    print("   factor de seleccion (afectadas por ella): mediana %.2f max %.2f" % (statistics.median(o["sel_x"] for o in sel), max(o["sel_x"] for o in sel)) if sel else "")
    print("   modo MAX por banda de cenit (todas las pasadas con pub>0):")
    for lo, hi in ((0, 30), (30, 45), (45, 60), (60, 90)):
        e = [o for o in ok if lo <= o["zen"] < hi]
        if e:
            print("     %2d-%2d: MAX %d de %d; MAX con efecto %d; suma del cumulo < 5 MW en %d" % (lo, hi, sum(o["modo"] == "MAX" for o in e), len(e),
                  sum(o["spm_x"] > 1.001 for o in e), sum(o["suma_c"] < 5 for o in e)))
