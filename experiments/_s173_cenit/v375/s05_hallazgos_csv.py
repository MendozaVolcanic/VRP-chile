# -*- coding: utf-8 -*-
"""s05: escribe hallazgos.csv con el módulo csv (un campo con comas sin comillas correría las columnas)."""
import csv
C = "C:/Users/nmend/vrp-wt/s173_cenit/v375/"
H = [
 ("CV375-01", "V375-E queda plana con el cenit en Chillán y K cae: la pieza que corrige la caída oblicua está dentro de la vía",
  "s03_estratos_cenit.py:s03_salida.json (B_K, B_via_publicada, B_via_sobre_K)", "CONFIRMADO", 4, "cenit V375",
  "python -B s03_estratos_cenit.py s01_k_pasadas.csv s02_v375e_pasadas.csv s03_salida.json", C + "s03_salida.txt"),
 ("CV375-02", "La sombra V375-E no tiene ningún record: data/sombra_codigo_mirova/ no existe en origin/main; la ventana empieza el 2026-11-03",
  "s00_sombra_existe.py:s00_salida.txt; .github/workflows/sombra-codigo-mirova.yml (cron 0 15 * * *)", "CONFIRMADO", 3, "insumos",
  "python -B s00_sombra_existe.py <repo>", C + "s00_salida.txt"),
 ("CV375-03", "El remuestreo deja su firma: los alertados de la vía crecen con el cenit y los de K no; la diferencia de fondo es constante",
  "s04_firmas_por_cenit.py:s04_salida.json (npix_via_por_tramo, npos_K_por_tramo, tbgK_menos_tbgvia_K)", "SOSPECHA", 3, "cenit V375",
  "python -B s04_firmas_por_cenit.py s02_v375e_pasadas.csv s01_k_pasadas.csv _s157_a_pasadas.json s04_salida.json", C + "s04_salida.txt"),
 ("CV375-04", "Con fondo cero K sigue cayendo con el cenit; con el factor de área se aplana (techos de la tarea 1.33 partidos por cenit)",
  "s04_firmas_por_cenit.py:s04_salida.json (s157_G_fondo0, s157_G_area)", "CONFIRMADO", 3, "cenit V375",
  "python -B s04_firmas_por_cenit.py s02_v375e_pasadas.csv s01_k_pasadas.csv _s157_a_pasadas.json s04_salida.json", C + "s04_salida.txt"),
 ("CV375-05", "La caja o ROI no es la pieza en Chillán: los seis brazos de V375-C dan la misma razón por tramo",
  "s03_estratos_cenit.py:s03_salida.json (ROI_brazos_sobre_MIROVA)", "CONFIRMADO", 3, "ablación",
  "python -B s03_estratos_cenit.py s01_k_pasadas.csv s02_v375e_pasadas.csv s03_salida.json", C + "s03_salida.txt"),
 ("CV375-06", "El encargo llama D25 a la geometría del borde; en el catálogo D25 es el fondo del anillo regional con recorte a cero",
  "docs/MIROVA_DIVERGENCES.md:2861 (origin/main 5de08ebf6)", "CONFIRMADO", 3, "marco",
  "git show origin/main:docs/MIROVA_DIVERGENCES.md | sed -n 2861p", C + "_div.md"),
 ("CV375-07", "No existe ninguna salida por pasada que aísle remuestreo, fondo, media 3x3, umbrales o compuerta en VIIRS 375",
  "pipeline/mirova_v750_codigo.py:198,322,397,584,687 (origin/main); experiments/_s162_v375/brazos.py (sólo ROI)", "CONFIRMADO", 2, "ablación",
  "git ls-tree -r origin/loop/activo experiments/_s162_v375/", C + "INFORME.md"),
 ("CV375-08", "La vía re-corrida y el C13 del probe difieren más de 1e-3 MW en 13 de 46 pasadas, 4 de ellas con más de 4 píxeles",
  "s02_v375e_retro.py:s02b_control_c13_detalle.txt", "SOSPECHA", 1, "instrumento",
  "python -B s02_v375e_retro.py <repo> s01_k_pasadas.csv s02_v375e", C + "s02b_control_c13_detalle.txt"),
 ("CV375-09", "La vía publica dos alertas débiles de MIROVA que K calla (2026-08-20 05:12 y 2026-09-05 05:48)",
  "s03_estratos_cenit.py:s03_salida.txt (via_pub_K_no)", "CONFIRMADO", 2, "detección",
  "python -B s03_estratos_cenit.py s01_k_pasadas.csv s02_v375e_pasadas.csv s03_salida.json", C + "s03_salida.txt"),
]
with open(C + "hallazgos.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    w.writerows(H)
print(len(H), "filas")
