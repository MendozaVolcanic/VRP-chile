# -*- coding: utf-8 -*-
"""Compara las salidas crudas de bitabit_crudo_v375.py (tag contra HEAD) en los tres perfiles, y el control.

Uso: python comparar_crudo.py <carpeta con tag_<perfil>.json, hoy_<perfil>.json y control_mirova_equivalent.json>
Sale 0 sólo si los tres perfiles dan IGUAL y el control da DISTINTO."""
import json
import sys
from pathlib import Path

d = Path(sys.argv[1])


def cargar(nombre):
    x = json.loads((d / nombre).read_text(encoding="utf-8"))
    flag = x.pop("__flag_ENABLE_V375_CODIGO_MIROVA")
    return json.dumps(x, sort_keys=True), flag


ok = True
for perfil in ("mirova_equivalent", "experimental", "experimental_ndc_focus"):
    (a, fa), (b, fb) = cargar(f"tag_{perfil}.json"), cargar(f"hoy_{perfil}.json")
    igual = a == b
    ok &= igual and fb is False
    print(f"{perfil}: {'IGUAL' if igual else 'DISTINTO'} (repr de cada float) | flag en el tag: {fa} | en HEAD: {fb}")
(a, _), (c, fc) = cargar("tag_mirova_equivalent.json"), cargar("control_mirova_equivalent.json")
puede_fallar = a != c and '"via_codigo_mirova": "sin_grilla"' in c
ok &= puede_fallar
print(f"control (HEAD con el flag encendido) contra el tag: {'DISTINTO' if a != c else 'IGUAL'}; "
      f"lleva la marca sin_grilla: {'si' if 'sin_grilla' in c else 'no'} | flag del perfil: {fc}")
print("VEREDICTO:", "BIT A BIT CON EL TAG, Y EL CONTROL PUEDE FALLAR" if ok else "ROJO")
sys.exit(0 if ok else 1)
