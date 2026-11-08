# -*- coding: utf-8 -*-
"""VX S175: escribe hallazgos.csv (una fila por veredicto y por hallazgo propio) con el módulo csv, como manda el
preámbulo (un campo con comas sin comillas corre las columnas). Rutas con os.path.join para no pelear con las barras."""
import csv
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
VX = os.path.dirname(os.path.abspath(__file__))
F5 = os.path.join(os.path.dirname(VX), "f5")
TMP = os.path.join("C:\\", "Users", "nmend", "vrp-temporales", "s175_audit", "vx")
MEM = os.path.join("C:\\", "Users", "nmend", ".claude", "projects", "C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile",
                   "memory", "project_modis_geo_interp_offset.md")
j = os.path.join
py = 'python -I "{}"'.format
RE_302 = f'cd {TMP} && {py(j(VX, "vx_datos_base.py"))} && {py(j(VX, "vx_302_sensibilidad.py"))} && cd "{VX}" && python -I rerun_i2_extension.py'
RE_DATOS = f'cd {TMP} && {py(j(VX, "vx_datos_base.py"))}'
RE_SENS = f'cd {TMP} && {py(j(VX, "vx_datos_base.py"))} && {py(j(VX, "vx_302_sensibilidad.py"))}'

rows = [
    ("302-veredicto",
     "CONFIRMADO EN PARTE: 714 de 715 aciertos con distancia de la tabla son radialmente compatibles y el único «fuera» es "
     "Chillán V375 2026-10-18 06:48 (0,099 km); «mismo foco» no está medido (nulo por permutación 93 %)",
     f"{j(F5, 'i2_extension.py')}:33-34; scripts/banco_paridad.py:78,156,317 (base 752d348bc)",
     "CONFIRMADO EN PARTE", 2, "F5 posición", RE_302, j(VX, "vx_302_sensibilidad_salida.txt")),
    ("108-veredicto",
     "CONFIRMADO: las 10 filas de docs/COLA_CAMPO.md siguen «abierto» (último commit b941c8052, 2026-10-22) y el issue #943 "
     "(OPEN, 2026-11-04) responde C-06; el clasificador cubre 7 filas, no «C-02 a C-10»",
     f"docs/COLA_CAMPO.md:12-21 (base); {j(F5[:-2] + 'f0', 'f0_clasificador.py')}:137-139",
     "CONFIRMADO", 2, "F0 cola de campo",
     "git show 752d348bc:docs/COLA_CAMPO.md | grep -c '| abierto'; gh issue view 943 -R MendozaVolcanic/VRP-chile --json state,createdAt,title",
     j(TMP, "issue_943.json")),
    ("111-veredicto",
     "CONFIRMADO: nadie mide la fracción NRT de MODIS (product_version sólo en scripts/reparar_product_version_modis_s133.py y "
     "pipeline/); fetch.py 212-218 sólo 6.1/6.1NRT; decomiso 2026-09-30 (LAADS 199534, cita S159) pasó sin ejecutarse; "
     "nov-2026: 14 de 143 records MODIS NRT (9,8 %)",
     "pipeline/fetch.py:212-218 (base); experiments/_s159/biblio_2026/INFORME.md:66-69 (base); docs/AUDIT_S160.md:66",
     "CONFIRMADO", 2, "F0 vencimientos",
     RE_DATOS + "; git grep -n product_version 752d348bc -- scripts .github",
     j(VX, "vx_datos_base_salida.txt")),
    ("256-veredicto",
     "CONFIRMADO: la memoria dice «MxD03 se baja y se ignora» y «probe pendiente»; la vía de producción lo lee "
     "(process_modis.py:648 -> mirova_v750_codigo.py:842) con enable_modis_codigo_mirova true; 120 de 120 records MODIS "
     "Tier A procesados desde 2026-11-02T20:11Z llevan via_codigo_mirova true",
     f"{MEM}:3,11,17; memory/MEMORY.md:114; pipeline/process_modis.py:648 y pipeline/mirova_v750_codigo.py:842 (base)",
     "CONFIRMADO", 2, "F3 memoria vs código",
     f'grep -n "se ignora" "{MEM}"; git show 752d348bc:pipeline/process_modis.py | sed -n 637,662p; ' + RE_DATOS,
     j(VX, "vx_datos_base_salida.txt")),
    ("VX-01",
     "La prueba de extensión de F5 casi no distingue: con las distancias de MIROVA barajadas entre pares del mismo volcán y "
     "sensor, el 93 % igual sale «mismo cúmulo» (observado 99,86 %; nulo 91,3 a 95,0 %, 300 barajados)",
     f"{j(VX, 'vx_302_sensibilidad.py')} (bloque 2); {j(F5, 'i2_extension.py')}:33-34",
     "CONFIRMADO", 2, "F5 posición", RE_SENS, j(VX, "vx_302_sensibilidad_out.json")),
    ("VX-02",
     "El «al borde» de Chillán V375 2026-10-18 06:48 cambia de lado con el origen (desde el vent: compatible) y con la "
     "tolerancia (x0,5: 15 «fuera», 5 protegidas); la vara mirova_center reproduce la tabla en 5 de 8 TIF",
     f"{j(VX, 'vx_302_sensibilidad_salida.txt')} (bloques 1 y 3); {j(F5, 'i2_tif.out.txt')}",
     "CONFIRMADO", 2, "F5 posición", RE_SENS, j(VX, "vx_302_sensibilidad_salida.txt")),
    ("VX-03",
     "Sin tolerancia, la distancia de la tabla cae fuera del rango radial de nuestros píxeles en 519 de 715 aciertos: "
     "desfase sistemático que la tolerancia de dos píxeles tapa",
     f"{j(VX, 'vx_302_sensibilidad_salida.txt')} (mirova_center|tol_x0.0|todos_CONS)",
     "SOSPECHA", 2, "F5 posición", RE_SENS, j(VX, "vx_302_sensibilidad_salida.txt")),
    ("VX-04",
     "Record MODIS NRT Planchón-Peteroa Terra 2026-11-02 01:15 lleva 5 días sin subir a Standard y quedó en K (procesado "
     "antes del merge de la vía): único MODIS de la semana con detector efectivo K",
     f"{j(VX, 'vx_datos_base_salida.txt')} (nrt_viejos); pipeline/store.py:695-702 (base)",
     "CONFIRMADO el hecho, SOSPECHA la causa", 2, "F0 vencimientos", RE_DATOS, j(VX, "vx_datos_base_out.json")),
    ("VX-05",
     "Ningún record MODIS declara qué geolocalización se usó (geo_fuente no se persiste; la vía sólo deja via_codigo_mirova)",
     f"{j(VX, 'vx_datos_base_salida.txt')} (llaves_geo vacío); pipeline/process_modis.py:531-537,1767 (base)",
     "CONFIRMADO", 1, "F3 memoria vs código", RE_DATOS, j(VX, "vx_datos_base_salida.txt")),
]
salida = j(VX, "hallazgos.csv")
with open(salida, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    w.writerows(rows)
n = list(csv.DictReader(open(salida, encoding="utf-8")))
assert all(len(r) == 8 for r in n)
print("hallazgos.csv:", len(n), "filas, 8 columnas cada una ->", salida)
