# -*- coding: utf-8 -*-
"""s05 (S173, cenit V750): escribe hallazgos.csv con el módulo csv (campos con comas van entre comillas)."""
import csv
from pathlib import Path

AQUI = Path(__file__).resolve().parent
C = "cd C:/Users/nmend/vrp-wt/s173_cenit/v750 && python -B s01_ablacion_chillan.py && python -B s02_razon_por_cenit.py && python -B s03_nativos_y_extra.py && python -B s04_robustez.py"
S3 = str(AQUI / "s03_salida.txt")
S2 = str(AQUI / "s02_salida.txt")
S4 = str(AQUI / "s04_salida.txt")
F = [
    ("CV750-01", "Dentro de la grilla solo el fondo de anillo de K reproduce la caida con el cenit; las demas piezas de K dejan la razon plana",
     "s03_nativos_y_extra.py:s03_salida.txt; repo/pipeline/process_viirs_mod.py:1072,1087", "CONFIRMADO", 4, "pieza/fondo (D25)", C, S3),
    ("CV750-02", "En el granulo nativo el fondo y la suma de MIROVA (brazo F de N) suben el nadir pero no aplanan la caida",
     "s03_nativos_y_extra.py:s03_salida.txt; src/probe_n.py:10-15", "CONFIRMADO (medicion); SOSPECHA (resto = D17)", 4, "remuestreo/area (D17)", C, S3),
    ("CV750-03", "La grilla alerta mas celdas por pixel nativo de lado (1,33 a 3,0), no significativo",
     "s03_nativos_y_extra.py:s03_salida.txt seccion CONTEO", "SOSPECHA", 2, "remuestreo/area (D17)", "python -B s03_nativos_y_extra.py", S3),
    ("CV750-04", "Medir solo VRP > 0 esconde la caida del fondo de anillo (6 pasadas oblicuas con VRP negativo)",
     "s02_salida.txt O_fanillo; s03_salida.txt O_fanillo; src/s162/ablacion.py:296-300", "CONFIRMADO", 2, "instrumento", "python -B s02_razon_por_cenit.py && python -B s03_nativos_y_extra.py", S2),
    ("CV750-05", "O_comp cae con el cenit pero no es la compuerta de K; O_comp1 (la de K) es plana",
     "src/s162/oraculo_ablacion.py:17-19; s03_salida.txt; s04_salida.txt", "CONFIRMADO", 1, "pieza/compuerta (D22)", "python -B s02_razon_por_cenit.py && python -B s04_robustez.py", S4),
]
with open(AQUI / "hallazgos.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    w.writerows(F)
print(open(AQUI / "hallazgos.csv", encoding="utf-8").read())
