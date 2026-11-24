#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V1 (S175): escribe hallazgos.csv (veredictos 151 a 158 y hallazgos nuevos V1-01 a V1-04) con el módulo csv."""
import csv
import os

C = os.path.dirname(os.path.abspath(__file__))
R = "C:/Users/nmend/vrp-temporales/s175_audit/f1/root_base"
D = "C:/Users/nmend/vrp-temporales/s175_audit/f1/datos/e75a7d52d"
T = "C:/Users/nmend/vrp-temporales/s175_audit/v1"


def s(nombre):
    return os.path.join(C, nombre)


FILAS = [
    ("151", "VEREDICTO CONFIRMADO (consecuencia SOSPECHA baja): la vigilancia no mira si el record de produccion es de la via",
     "scripts/vigilancia_guardia_modis.py:200-203,171,273", "CONFIRMADO", 2, "F1",
     f"python re_mutaciones.py {R} 2026-11-07 (M6)", s("re_mutaciones_salida.json")),
    ("152", "VEREDICTO CONFIRMADO EN PARTE: caida a K en un volcan da VERDE; dejar de escribir da VIGILANCIA_CIEGA",
     "scripts/vigilancia_guardia_modis.py:345-360", "CONFIRMADO EN PARTE", 2, "F1",
     f"python mutaciones_propias.py {R} 2026-11-07 (V2d, V2e)", s("mutaciones_propias_salida.json")),
    ("153", "VEREDICTO CONFIRMADO EN PARTE: el pipeline no deja rastro del descarte; la vigilancia lo cuenta por semana",
     "pipeline/process_modis.py:657-658; pipeline/mirova_v750_codigo.py:804-808", "CONFIRMADO EN PARTE", 2, "F1",
     f"python claves_guardia_vs_prod.py {D}", s("claves_guardia_vs_prod_salida.txt")),
    ("154", "VEREDICTO CONFIRMADO: el NRT no re-escribe 8 dias; primera observacion de la via 19 h antes del encendido",
     "pipeline/store.py:695-699; REGLA_REVERSION_MODD_BORRADOR.md:162,318", "CONFIRMADO", 2, "F1",
     f"python reescritura_ventana.py {D}/mirova_equivalent 2026-11-02T20:11:43Z", s("reescritura_ventana_salida.txt")),
    ("155", "VEREDICTO REFUTADO en la consecuencia: la cabecera es del PNG y los PNG MODIS Latest10NTI siguen hasta 2026-11-07",
     "REGLA_REVERSION_MODD_BORRADOR.md:192; docs/S150_IMAGENES_SNPP.md:23-24", "REFUTADO", 1, "F1",
     "python sobre insumos/tif_index.csv y png_index.csv (VERIFICACION.md, 155)", s("VERIFICACION.md")),
    ("156", "VEREDICTO CONFIRMADO (anuncio EN PARTE): con la via, 6 flags de K en MODIS pasan a 0 y FUERA_DE_BANDA a VERDE",
     "scripts/auto_audit_weekly.py:427-429,1023-1025,1050-1059", "CONFIRMADO", 1, "F1",
     f"python audit_con_y_sin_via.py {R} {T}/audit", s("audit_con_y_sin_via_salida.json")),
    ("157", "VEREDICTO CONFIRMADO: recall VIA_MODIS sin flag hasta 15 noches; una protegida callada si da flag",
     "scripts/auto_audit_weekly.py:94,577-590", "CONFIRMADO", 1, "F1",
     f"python audit_via_calla.py {R} {T}/audit_calla", s("audit_via_calla_salida.json")),
    ("158", "VEREDICTO CONFIRMADO EN PARTE: un record mueve el encendido 2 s; un --overwrite masivo lo mueve al reproceso",
     "scripts/vigilancia_guardia_modis.py:98-115; pipeline/store.py:541", "CONFIRMADO EN PARTE", 1, "F1",
     f"python sensibilidad_encendido.py {R} {D}/mirova_equivalent", s("sensibilidad_encendido_salida.txt")),
    ("V1-01", "El plazo de 29 protegidas avanza con pasadas en que produccion no corrio la via",
     "scripts/vigilancia_guardia_modis.py:190-192,276-278", "CONFIRMADO", 2, "F1",
     f"python mutaciones_propias.py {R} 2026-11-07 (V2e, vistas)", s("mutaciones_propias_salida.json")),
    ("V1-02", "La ficha publica CPLT v1.18 dice que la via rige hasta 8 dias antes; los datos dicen 19 horas",
     "docs/FICHA_SDA_VRP_CHILE.md:7,25", "CONFIRMADO", 2, "F1",
     f"python reescritura_ventana.py {D}/mirova_equivalent 2026-11-02T20:11:43Z", s("reescritura_ventana_salida.txt")),
    ("V1-03", "La caida a K sin_mxd03 es inalcanzable desde el NRT",
     "scripts/run_pipeline.py:247-250; pipeline/process_modis.py:644-645", "CONFIRMADO", 1, "F1",
     "grep -rn process_modis.calculate_vrp scripts pipeline", s("VERIFICACION.md")),
    ("V1-04", "Falta el JSON de la guardia de un volcan y la vigilancia declara ciegos los once",
     "scripts/vigilancia_guardia_modis.py:375-378", "CONFIRMADO", 1, "F1",
     f"python re_mutaciones.py {R} 2026-11-07 (M3)", s("re_mutaciones_salida.json")),
]

with open(s("hallazgos.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    w.writerows(FILAS)
filas = list(csv.reader(open(s("hallazgos.csv"), encoding="utf-8")))
print(len(filas), sorted(set(len(x) for x in filas)))
