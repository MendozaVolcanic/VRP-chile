# -*- coding: utf-8 -*-
"""s06: escribe hallazgos.csv con el modulo csv (un campo con comas sin comillas correria las columnas)."""
import csv
C = "D:/vrp-trabajo/temporales/s172_chillan/"
filas = [
 ("CH172-01", "El deficit de Chillan depende del angulo cenital del satelite en los tres sensores a la vez",
  "s03_estratos.py : s03_salida.json", "CONFIRMADO", 4, "magnitud",
  "python -B s02_pareo_por_pasada.py D:/vrp-trabajo/temporales/s172_chillan/repo 2026-04-01 2026-10-26 s02_v_abr_oct && python -B s03_estratos.py s02_v_abr_oct_pasadas.csv s03_salida.json",
  C + "s03_salida.json"),
 ("CH172-02", "Las 3 alertas protegidas MODIS perdidas de Chillan estan todas a ~58 grados de cenit",
  "s02_lista_alertas.txt (MODIS 2026-10-12 07:20, 2026-10-15 01:05, 2026-10-25 07:20); modd_resultado_f4.json chillan.recuperadas",
  "CONFIRMADO", 4, "recall/magnitud", "grep MODIS s02_lista_alertas.txt", C + "s02_lista_alertas.txt"),
 ("CH172-03", "En VIIRS 750 el fondo de anillo solo reproduce el deficit de Chillan dentro del port de MIROVA",
  "origin/claude/s162-viirs750-f63ef4:experiments/_s162_v750c/verificador/medir3_salida.txt l. 8 y 24", "SOSPECHA", 3, "magnitud",
  "git show origin/claude/s162-viirs750-f63ef4:experiments/_s162_v750c/verificador/medir3_salida.txt", C + "v750c_medir3_salida.txt"),
 ("CH172-04", "El auto-audit (maximo de la noche / maximo de la noche) subestima el deficit por pasada y no exige la misma pasada",
  "scripts/auto_audit_weekly.py:683 y l. 584-587", "CONFIRMADO", 2, "instrumento",
  "python -B s01_reproducir_autoaudit.py D:/vrp-trabajo/temporales/s172_chillan/repo_20261026 s01_salida.json && python -B s02_pareo_por_pasada.py D:/vrp-trabajo/temporales/s172_chillan/repo 2026-08-27 2026-10-26 s02_v_autoaudit",
  C + "s02_v_autoaudit_resumen.json"),
 ("CH172-05", "Queda un deficit de 15 a 25 % aun cerca del nadir (z < 30)",
  "s03_salida.json por_cenit z<30; modd_resultado_f4.json chillan.mediana_z_le30", "CONFIRMADO", 2, "magnitud",
  "python -B s03_estratos.py s02_v_abr_oct_pasadas.csv s03_salida.json", C + "s03_salida.json"),
 ("CH172-06", "Antes de la fase fuerte las alertas debiles de VIIRS 375 se pierden porque el pixel del cumulo sale con VRP 0",
  "s02_lista_alertas.txt (VIIRS375 2026-05-14 a 2026-09-14, pub 0)", "CONFIRMADO", 2, "recall",
  "grep VIIRS375 s02_lista_alertas.txt | grep 'pub 0'", C + "s02_lista_alertas.txt"),
]
with open(C + "hallazgos.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    w.writerows(filas)
print("ok", len(filas))
