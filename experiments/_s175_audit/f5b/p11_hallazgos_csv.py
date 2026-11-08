# -*- coding: utf-8 -*-
"""P11 (F5b): escribe hallazgos.csv con el módulo csv (una fila por hallazgo del INFORME.md, IDs 351 a 355)."""
import csv, os
D = os.path.dirname(os.path.abspath(__file__))
C = "<CARPETA>"
filas = [
    {"id": "351",
     "titulo": "Cuatro protegidas VIIRS de Chillan son (iii): en la misma pasada el foco de MIROVA esta a 1,0 a 2,5 km del punto que publicamos (VIIRS375 2026-10-18 05:06, 21,25 MW, 1,02 km; VIIRS750 2026-10-29 06:42, 29,35 MW, 2,16 km; VIIRS750 2026-10-10 06:54 y 2026-10-16 06:42 con pixel poco prominente); 6 MODIS (iii) sin validar",
     "archivo_linea": r"%s\p8_clasificar.py -> p8_clases.csv (clase iii); %s\p13_estratos.out.txt; our_lat/our_lon de experiments/_s175_audit/f5/i2_pares.csv" % (C, C),
     "confianza": "CONFIRMADO la medicion; SOSPECHA que sea otra fuente y no otro pixel del mismo cumulo", "gravedad": "3", "eje": "posicion post 22-sep (identidad del acierto)",
     "comando_reproduccion": 'cd C:\\Users\\nmend\\vrp-temporales\\s175_audit\\f5b && python -I "%s\\p8_clasificar.py" && python -I "%s\\p13_estratos.py"; Chillan VIIRS_NOAA21 2026-10-18 05:06 UTC y VIIRS_NOAA21_750 2026-10-29 06:42 UTC' % (C, C),
     "salida_cruda": os.path.join(D, "p8_clases.csv") + "; " + os.path.join(D, "p13_estratos.out.txt")},
    {"id": "352",
     "titulo": "En Chillan el control de distancia falla por poco en 30 protegidas: la mancha de MIROVA cae en la celda central (0,02 km) y la tabla dice 0,84 a 1,35 km, nunca 0; el origen de la Distancia_km de MIROVA no es el centro de la grilla o el pixel alertado no es el mas claro; nuestro punto a 0,36 km (mediana) de la mancha",
     "archivo_linea": r"%s\p13_estratos.out.txt (iv por control fallido, Chillan); %s\p8_clases.csv (d_png_mirova_center_km 0,018); volcanoes.yaml NevadosDeChillan mirova_center y vent a 0,39 km" % (C, C),
     "confianza": "CONFIRMADO el desajuste y la cuantizacion de la tabla; SOSPECHA la causa", "gravedad": "2", "eje": "posicion post 22-sep (vara de distancia)",
     "comando_reproduccion": 'python -I "%s\\p13_estratos.py"; Chillan VIIRS_NOAA20 2026-10-18 06:00 UTC (medido 0,018 km, tabla 0,84)' % C,
     "salida_cruda": os.path.join(D, "p13_estratos.out.txt")},
    {"id": "353",
     "titulo": "El archivo no capturo laminas Latest10NTI MODIS en 12 de 46 dias desde el 22-sep (23 a 30-sep y 8 a 11-oct, los 11 volcanes) ni VIIRS en 2 a 3 dias; Lascar MODIS 25-sep y 8-oct y Chillan MODIS 2026-10-10 07:40 (3,95 MW, protegida) no tienen lamina y su posicion es irrecuperable",
     "archivo_linea": r"C:\Users\nmend\vrp-temporales\s175_audit\insumos\png_index.csv (indice del archivo, ola 0); repo MendozaVolcanic/mirova-tif-archive (poller, fuera de este repo)",
     "confianza": "CONFIRMADO", "gravedad": "3", "eje": "posicion post 22-sep (cobertura de la vara)",
     "comando_reproduccion": 'python -I "%s\\p10_cobertura_laminas.py"; python -I "%s\\p9_lascar_modis.py"' % (C, C),
     "salida_cruda": os.path.join(D, "p10_cobertura_laminas.out.txt") + "; " + os.path.join(D, "p9_lascar_modis_out.json") + "; " + os.path.join(D, "p8_clases.csv")},
    {"id": "354",
     "titulo": "La lamina MODIS no sirve de vara de posicion con el pixel mas claro: en 7 aciertos MODIS de Lascar con TIF, el pixel mas claro del panel cae a 3,6 a 5,8 km del maximo del TIF en 5 de 7 y el maximo del TIF no reproduce la distancia de la tabla en 4 de 7; las clases MODIS post 22-sep (15 i, 6 iii, 3 iv) son SOSPECHA",
     "archivo_linea": r"%s\f5b_lib.py (pixel_mas_claro); %s\p7_mas_casos.py (casos MODIS); experiments/_s175_audit/f5/i2_tif.py (vara de F5, sin casos MODIS)" % (C, C),
     "confianza": "CONFIRMADO", "gravedad": "2", "eje": "posicion post 22-sep (validacion MODIS)",
     "comando_reproduccion": 'python -I "%s\\p7_mas_casos.py" (Lascar MODIS 2026-06-27 01:35, 06-24 08:00, 06-21 07:45, 07-30 07:55, 06-14 01:20, 06-17 01:40, 07-09 07:40 UTC)' % C,
     "salida_cruda": os.path.join(D, "p7_mas_casos_out.json")},
    {"id": "355",
     "titulo": "La lamina MODIS redondea el VRP a entero y pinta el marco gris: Lascar 2026-10-26 07:55 dice VRP = 0 MW con marco gris mientras la tabla da 0,29 MW ALERTA_TERMICA (Muy Bajo); ademas 10 aciertos VIIRS750 tienen marco gris en la lamina",
     "archivo_linea": r"C:\Users\nmend\vrp-temporales\s175_audit\f5b\png_p9\20261026_103015_MODIS_Latest10NTI.png (panel 1); tabla: C:\Users\nmend\vrp-temporales\s175_audit\insumos\snapshot_consolidado_base.csv, fila Lascar MODIS 2026-10-26 07:55:00",
     "confianza": "CONFIRMADO en ese caso; que sea regla general del redondeo es SOSPECHA", "gravedad": "1", "eje": "posicion post 22-sep (lectura de la lamina)",
     "comando_reproduccion": 'python -I "%s\\p9_lascar_modis.py" y abrir la lamina; Lascar MODIS_AQUA 2026-10-26 07:55 UTC; python -I "%s\\p13_estratos.py" (marcos grises)' % (C, C),
     "salida_cruda": os.path.join(D, "p9_lascar_modis_out.json") + "; " + os.path.join(D, "p13_estratos.out.txt")},
]
with open(os.path.join(D, "hallazgos.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    w.writeheader()
    w.writerows(filas)
print("hallazgos.csv:", len(filas), "filas")
