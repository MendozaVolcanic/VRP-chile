# -*- coding: utf-8 -*-
"""S127 — matriz sensor x tratamiento: quien recibe que, y en que bloque.

POR QUE: nadie audito nunca si los tres sensores reciben el MISMO tratamiento
metodologico. S126 fue descubriendo el mosaico de a pedazos y siempre por accidente:
la corona estaba solo en MODIS, el focal en MODIS y V750 pero no en V375, el anillo
intermedio solo en V375. Ese mosaico crecio sin plan, y cada casilla vacia es o una
decision deliberada que nadie escribio, o un port que quedo a medias.

La distincion importa porque los dos A/B de la corona que salieron INCONCLUSOS en S126
fallaron exactamente ahi: el primero (#539) la cableo solo en el bloque Test 1 cuando
el 96 % de las noches que se comparan vienen del bloque contextual. No es que la corona
no sirviera — es que no llegaba adonde se mide.

Por eso la matriz se construye POR BLOQUE, no por archivo: saber que un helper "esta en
process_viirs.py" no dice nada si esta en el bloque que casi no se compara.

Persiste en 01_paridad_de_tratamiento.json.
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

SENSORES = [
    ("MODIS", "process_modis.py"),
    ("VIIRS375", "process_viirs.py"),
    ("VIIRS750", "process_viirs_mod.py"),
]

# Helpers de magnitud y de deteccion cuyo reparto entre sensores importa.
HELPERS = [
    ("cluster_corona_background", "fondo local Eq.6 (magnitud)"),
    ("apply_corona_magnitude_v375", "wrapper de la corona (magnitud)"),
    ("cluster_focal_vrp_mw", "nucleo focal/contextual (magnitud)"),
    ("apply_single_pixel_mode", "single-pixel sub-MW (magnitud)"),
    ("compute_local_background", "kernel 8-vecinos per-pixel (magnitud)"),
    ("compute_test1_mir", "Test 1 integrado sobre MIR absoluto (deteccion)"),
    ("compute_test1_nti", "Test 1 integrado sobre NTI (deteccion)"),
    ("apply_contextual_test1_filter", "filtro contextual del Test 1 (deteccion)"),
    ("spatial_core_filter", "nucleo espacial (deteccion)"),
    ("intermediate_ring_bg_bt", "anillo intermedio [1,5-3] km (fondo)"),
    ("apply_second_pass_intra_radio_gate", "cerca intra-radio 2a pasada"),
    ("compute_vrp_lava_lake_eq16", "Eq.16 lava lake sub-pixel (magnitud)"),
    ("apply_d9_scene_cap", "cap D9 de escena"),
]

fuentes = {}
for nombre, archivo in SENSORES:
    p = os.path.join(ROOT, "pipeline", archivo)
    fuentes[nombre] = io.open(p, encoding="utf-8", errors="replace").read()


def call_sites(texto, helper):
    """Cuenta llamadas reales, sin contar la definicion ni el import."""
    n = len(re.findall(r"(?<![\w.])%s\s*\(" % re.escape(helper), texto))
    if re.search(r"^\s*def\s+%s\s*\(" % re.escape(helper), texto, re.M):
        n -= 1                      # la definicion vive en el mismo archivo
    return max(n, 0)


print("MATRIZ SENSOR x TRATAMIENTO — S127")
print("=" * 92)
print("%-38s %10s %10s %10s   %s"
      % ("helper", "MODIS", "V375", "V750", "que hace"))
print("-" * 92)

matriz = {}
asimetricos = []
for helper, glosa in HELPERS:
    fila = {s: call_sites(fuentes[s], helper) for s, _ in SENSORES}
    matriz[helper] = {"glosa": glosa, "call_sites": fila}
    presentes = [s for s, n in fila.items() if n > 0]
    if 0 < len(presentes) < 3:
        asimetricos.append((helper, glosa, presentes))
    print("%-38s %10d %10d %10d   %s"
          % (helper[:38], fila["MODIS"], fila["VIIRS375"], fila["VIIRS750"], glosa))

print("\nASIMETRIAS (el helper esta en algunos sensores y no en todos)")
print("-" * 92)
for helper, glosa, presentes in asimetricos:
    faltan = [s for s, _ in SENSORES if s not in presentes]
    print("  %-38s esta en %-22s falta en %s"
          % (helper[:38], ",".join(presentes), ",".join(faltan)))

res = {"matriz": matriz,
       "asimetrias": [{"helper": h, "glosa": g, "presente_en": p,
                       "falta_en": [s for s, _ in SENSORES if s not in p]}
                      for h, g, p in asimetricos]}
dest = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "01_paridad_de_tratamiento.json")
json.dump(res, io.open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", os.path.relpath(dest, ROOT).replace("\\", "/"))
