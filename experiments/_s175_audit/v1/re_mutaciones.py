#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V1 (verificador S175): re-corre experiments/_s175_audit/f1/mutaciones_vigilancia.py SIN modificar su lógica.

Sólo cambia dos cosas del texto fuente, por las reglas de esta verificación:
1. MUT (carpeta de copias) pasa a C:/Users/nmend/vrp-temporales/s175_audit/v1/mutaciones (no escribo en f1/).
2. Al preparar cada mutación se borra la carpeta de la anterior (tope de disco 0,5 GB; cada copia pesa ~50 MB).
Las sustituciones se verifican (assert) para que una sustitución que no aplica no corra el original en silencio.

Uso: python -I re_mutaciones.py <root_base> <hoy> > salida.json
"""
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "f1" / "mutaciones_vigilancia.py"
src = SRC.read_text(encoding="utf-8")
viejo_mut = 'MUT = Path(ROOT).parent / "mutaciones"'
nuevo_mut = 'MUT = Path(r"C:/Users/nmend/vrp-temporales/s175_audit/v1/mutaciones")'
assert src.count(viejo_mut) == 1, "la línea MUT del auditor cambió"
src = src.replace(viejo_mut, nuevo_mut)
# Borrar la carpeta anterior al preparar la siguiente (no al terminar la corrida: tras M0 el auditor relee
# vgm.PRODUCCION, que apunta a la copia de M0).
viejo_out = "    if d.exists():\n        shutil.rmtree(d)\n"
nuevo_out = "    if MUT.exists():\n        shutil.rmtree(MUT)\n"
assert src.count(viejo_out) == 1, "la línea preparar del auditor cambió"
src = src.replace(viejo_out, nuevo_out)
sys.argv = [str(SRC)] + sys.argv[1:]
g = {"__name__": "__main__", "__file__": str(SRC)}
exec(compile(src, str(SRC), "exec"), g)
