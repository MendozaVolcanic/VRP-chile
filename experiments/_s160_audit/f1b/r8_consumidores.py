"""R8 (contrafactual): el valor que un brazo cambia, llega a TODOS sus consumidores?

Control positivo (d) del plan: la caja de 5 x 5 km (flag enable_roi1_box_paper, variable _roi1_mask) llego al primer
pase y no al segundo en el codigo con que corrio el brazo G de S148 (regla A118). Este script cuenta, en un
process_viirs.py dado, los sitios donde la geometria de cumbre se decide con `inner_radius_km` y en cuales de ellos
participa `_roi1_mask` (o `roi1_summit_mask`, el helper que S149 agrego). Un sitio que decide cumbre sin mirar la
mascara es un consumidor al que el brazo no llega.

Pregunta 1: si la mascara no llegara al segundo pase, se veria? Si: el sitio `is_summit_mask = ... <= inner_radius_km`
del segundo pase aparece como consumidor sin mascara. Pregunta 2: si el script estuviera muerto, se veria? Si: exige
encontrar al menos un consumidor y al menos un sitio con mascara, o falla.

Uso: python r8_consumidores.py <process_viirs.py> [etiqueta]
"""
import re, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
p = sys.argv[1]; et = sys.argv[2] if len(sys.argv) > 2 else p
src = open(p, encoding="utf-8").read().splitlines()
consumidores = []
for i, l in enumerate(src, 1):
    if re.search(r"<=\s*inner_radius_km|<=\s*inner_km|roi1_summit_mask\(", l):
        # mira 6 lineas de contexto hacia atras y adelante por la mascara
        ctx = "\n".join(src[max(0, i - 7):i + 6])
        con_mask = bool(re.search(r"_roi1_mask|roi1_mask|roi1_summit_mask", ctx))
        consumidores.append((i, l.strip()[:90], con_mask))
print("archivo:", et)
print("sitios donde se decide cumbre por radio (o helper):", len(consumidores))
sin = 0
for i, l, m in consumidores:
    print("  l.%d %s | mascara en contexto: %s" % (i, l, "SI" if m else "NO"))
    sin += (not m)
assert consumidores and ("_roi1_mask" in "\n".join(src)), "instrumento muerto: no encontro consumidores o el archivo no tiene _roi1_mask"
print("R8:", "FALLA (%d consumidor(es) sin la mascara)" % sin if sin else "OK (todos los consumidores reciben la mascara)")
