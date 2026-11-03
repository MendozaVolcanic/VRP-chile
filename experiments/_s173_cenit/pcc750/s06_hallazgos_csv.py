# -*- coding: utf-8 -*-
"""s06: escribe hallazgos.csv con el módulo csv (un campo con comas sin comillas correría las columnas)."""
import csv
from pathlib import Path
AQUI = Path(__file__).resolve().parent
C = "C:/Users/nmend/vrp-wt/s173_cenit/pcc750/"
H = [
 ("CPCC750-01", "Fondo de anillo de K con recorte explica el déficit de NIVEL en PCC V750 a todo cenit",
  "repo/pipeline/process_viirs_mod.py:548,570,1072,1087; s03_salida.txt; s04_salida.txt", "CONFIRMADO", 4, "fondo D25",
  "python -B s02_ablacion_pcc.py && python -B s03_razon_brazos_por_cenit.py && python -B s04_mecanismo_y_robustez.py",
  C + "s03_salida.txt"),
 ("CPCC750-02", "La pendiente de K con el cenit es de ceros: fracasos 6/18 bajo 30 y 8/11 sobre 30",
  "s04_salida.txt §(1) §(3); s01_salida.txt", "CONFIRMADO", 4, "pendiente", "python -B s04_mecanismo_y_robustez.py",
  C + "s04_salida.txt"),
 ("CPCC750-03", "No detecciones nativas de K (7 de 29, incl. pérdida aceptada 2026-10-10) no las reproduce ninguna pieza de K en la grilla",
  "s04_salida.txt §(1); s03_salida.txt DETALLE", "CONFIRMADO (mecanismo SOSPECHA)", 3, "detección nativa / D17",
  "python -B s04_mecanismo_y_robustez.py", C + "s04_salida.txt"),
 ("CPCC750-04", "Caja del ejemplo (7x7) muda en PCC: 0 de 72 pasadas; producción tiene roi_v750 def para PCC",
  "s02_salida.txt; repo/pipeline/grillas_mirova.yaml:38; repo/pipeline/mirova_v750_codigo.py:821", "CONFIRMADO", 3,
  "ROI / instrumento", "python -B s02_ablacion_pcc.py", C + "s02_salida.txt"),
 ("CPCC750-05", "Anillo del oráculo de ablación S162 va de inner a 25 km, no 5-25 como K",
  "src/s162/oraculo_ablacion.py:177,222; repo/pipeline/process_viirs_mod.py:570", "CONFIRMADO", 2, "instrumento",
  "python -B s02_ablacion_pcc.py && python -B s03_razon_brazos_por_cenit.py", C + "s02_salida.txt"),
 ("CPCC750-06", "El port de MIROVA en la grilla (S y C) no es plano contra MIROVA en PCC",
  "s03_salida.txt; s04_salida.txt §(3) §(4b)", "CONFIRMADO (causa SOSPECHA)", 2, "instrumento / ROI",
  "python -B s03_razon_brazos_por_cenit.py", C + "s03_salida.txt"),
 ("CPCC750-07", "F nativo (fondo del código) no deja déficit de remuestreo en magnitud y queda 1,3x sobre MIROVA",
  "s03_salida.txt; s04_salida.txt §(3)", "CONFIRMADO (causa SOSPECHA)", 2, "remuestreo D17",
  "python -B s03_razon_brazos_por_cenit.py", C + "s03_salida.txt"),
 ("CPCC750-08", "En la ventana del auto-audit la pendiente no se ve; sí en la ventana larga",
  "s01_salida.txt; repo/data/audit_continuous/latest.json", "CONFIRMADO", 1, "ventana A90",
  "python -B s01_razon_k_por_pasada.py", C + "s01_salida.txt"),
 ("CPCC750-09", "En el campo difuso el halo del fondo de MIROVA pesa: sin halo C cae a 0,773 / 0,433",
  "s03_salida.txt; repo/pipeline/process_viirs_mod.py:417,1073", "CONFIRMADO (extrapolación a D25 SOSPECHA)", 2,
  "fondo D25", "python -B s03_razon_brazos_por_cenit.py", C + "s03_salida.txt"),
]
with open(AQUI / "hallazgos.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    w.writerows(H)
print("filas:", len(H))
