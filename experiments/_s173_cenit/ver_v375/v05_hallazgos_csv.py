# -*- coding: utf-8 -*-
"""v05 (verificador V375, S173): escribe hallazgos.csv con el modulo csv (un campo con comas sin comillas corre las
columnas; csv.writer las entrecomilla solo). Una fila por hallazgo propio VV375-nn y una por veredicto CV375-nn.
Uso: python -I v05_hallazgos_csv.py <hallazgos.csv>"""
import csv, sys

C = "C:/Users/nmend/vrp-wt/s173_cenit/ver_v375/"
filas = [
    ("VV375-01", "La firma de remuestreo del auditor contradice la tarea 1.14 seccion 3.2 y mide lo que el remuestreo hace por construccion",
     "experiments/_s151_presupuesto_magnitud/README.md:78-84 (origin/main); rerun/s04_salida.json npix_via_por_tramo", "CONFIRMADO (contradiccion) / SOSPECHA (cual vale)", 3, "cenit V375",
     "python -B rerun/s04_firmas_por_cenit.py rerun/s02_v375e_pasadas.csv rerun/s01_k_pasadas.csv ../v375/_s157_a_pasadas.json rerun/s04_salida.json", C + "rerun/s04_salida.json"),
    ("VV375-02", "La via de los lotes retrospectivos no es la via de produccion entera: el remuestreo es del probe (port S159), el resto del pipeline",
     "C:/Users/nmend/vrp-wt/s173_cenit/v375/s02_v375e_retro.py:56-72; experiments/_s162_v375/brazos.py:34-36 (loop/activo)", "SOSPECHA", 2, "instrumento",
     "leer s02_v375e_retro.py l. 56-72 y pipeline/mirova_v750_codigo.py:198-224", C + "rerun/s02_v375e_salida.txt"),
    ("VV375-03", "Con el factor de area se aplana es por construccion; el techo fondo cero mas area se pasa a 1,70 sobre 50 grados",
     "experiments/_s157_magnitud_chillan/a_pasadas.py:25-28,246-247; rerun/s04_salida.json s157_f_area, s157_G_area_fondo0", "CONFIRMADO", 2, "cenit V375",
     "python -B rerun/s04_firmas_por_cenit.py rerun/s02_v375e_pasadas.csv rerun/s01_k_pasadas.csv ../v375/_s157_a_pasadas.json rerun/s04_salida.json", C + "rerun/s04_salida.json"),
    ("VV375-04", "El cenit del record de K es el del pixel mas cercano al final_hotspot, no el del volcan; en Chillan no cambia ningun tramo",
     "pipeline/process_viirs.py:2249-2253; pipeline/scan_geometry.py:395-430; v02_salida.json B_dz_max_Kz_menos_zvia", "CONFIRMADO", 1, "cenit V375",
     "python -I v02_lotes_cenit_c13.py rerun/s02_v375e_pasadas.csv rerun/s01_k_pasadas.csv v02_salida.json", C + "v02_salida.json"),
    ("VV375-05", "Los 66 pares de K los escribieron 21 shas de codigo (41 reproceso, 25 NRT); todos K y los dos grupos caen con el cenit",
     "v01_salida.json por_codigo_sha; git log 34cea39e..origin/main -- pipeline/process_viirs.py", "CONFIRMADO", 1, "A104",
     "python -I v01_pareo_propio.py copia_main rerun/s01_k_pasadas.csv v01_salida.json", C + "v01_salida.json"),
    ("VV375-06", "La primera corrida con datos de la sombra es la del 2026-11-03 y el cron llega 4 a 8 horas tarde",
     "scripts/ventana_sombra.py:23; runs 41118756898 41232878558 41341608741 41541988051", "CONFIRMADO", 1, "insumos",
     "gh api repos/MendozaVolcanic/VRP-chile/actions/workflows/sombra-codigo-mirova.yml/runs?per_page=10", C + "INFORME.md"),
    ("CV375-01", "Veredicto: CONFIRMADO (K 0,753/0,562 Spearman -0,515 fuera; via 0,922/1,000 +0,283 dentro; via/K 1,205 a 1,758; n 27, 14 noches)",
     "rerun/s03_salida.json; v01_salida.json", "CONFIRMADO", 4, "cenit V375",
     "python -B rerun/s03_estratos_cenit.py rerun/s01_k_pasadas.csv rerun/s02_v375e_pasadas.csv rerun/s03_salida.json", C + "rerun/s03_salida.json"),
    ("CV375-02", "Veredicto: CONFIRMADO EN PARTE (vacia por diseno: FECHA_MINIMA 2026-11-03; paso Commit skipped en las 4 corridas programadas)",
     "scripts/ventana_sombra.py:23,44-45; .github/workflows/sombra-codigo-mirova.yml paso Commit sombra data", "CONFIRMADO EN PARTE", 2, "insumos",
     "python -B rerun/s00_sombra_existe.py <repo>; gh api repos/MendozaVolcanic/VRP-chile/actions/runs/41541988051/jobs", C + "INFORME.md"),
    ("CV375-03", "Veredicto: CONFIRMADO EN PARTE (numeros si; firma de D17 sigue SOSPECHA y contradice 1.14 seccion 3.2)",
     "rerun/s04_salida.json npix_via_por_tramo, npos_K_por_tramo", "CONFIRMADO EN PARTE", 3, "cenit V375",
     "python -B rerun/s04_firmas_por_cenit.py ...", C + "rerun/s04_salida.json"),
    ("CV375-04", "Veredicto: CONFIRMADO EN PARTE (fondo cero sigue cayendo, Spearman -0,363 apenas fuera; el aplanado con area es por construccion)",
     "rerun/s04_salida.json s157_G_fondo0, s157_G_area", "CONFIRMADO EN PARTE", 2, "cenit V375",
     "python -B rerun/s04_firmas_por_cenit.py ...", C + "rerun/s04_salida.json"),
    ("CV375-05", "Veredicto: CONFIRMADO (6 brazos de ROI identicos, n 14, n 3 bajo 30; brazos del port ORA)",
     "rerun/s03_salida.json ROI_brazos_sobre_MIROVA; experiments/_s162_v375/brazos.py:1-34", "CONFIRMADO", 3, "ablacion",
     "python -B rerun/s03_estratos_cenit.py ...", C + "rerun/s03_salida.json"),
    ("CV375-06", "Veredicto: CONFIRMADO (D25 en el catalogo es el fondo del anillo regional con recorte; el borde del barrido es D17 y D28)",
     "docs/MIROVA_DIVERGENCES.md:2861,2317,3034 (origin/main)", "CONFIRMADO", 2, "marco",
     "git show origin/main:docs/MIROVA_DIVERGENCES.md | sed -n 2861p", C + "INFORME.md"),
    ("CV375-07", "Veredicto: CONFIRMADO (sin ablacion por pieza en V375; la de V750 no tiene pieza de remuestreo ni familia 375)",
     "pipeline/mirova_v750_codigo.py:397,584,687; experiments/_s162_v750c/ablacion.py:46-55", "CONFIRMADO", 2, "ablacion",
     "git grep -i ablaci origin/loop/activo -- experiments/_s165_v375_via experiments/_s172_chillan", C + "INFORME.md"),
    ("CV375-08", "Veredicto: CONFIRMADO EN PARTE (13 de 46 si; 9 dentro de la banda de jitter del probe, 4 en escenas de 1 y 4 pixeles; npix identico 46/46)",
     "v02_salida.json C13_detalle_gt; experiments/_s162_v375/PREREGISTRO_E.md:132-134", "CONFIRMADO EN PARTE", 1, "instrumento",
     "python -I v02_lotes_cenit_c13.py rerun/s02_v375e_pasadas.csv rerun/s01_k_pasadas.csv v02_salida.json", C + "v02_salida.json"),
    ("CV375-09", "Veredicto: CONFIRMADO (2026-08-20 05:12 NOAA-21 0,06 MW y 2026-09-05 05:48 SNPP 0,14 MW, CONS; K 0 pixeles; via 0,073 y 0,196)",
     "rerun/s01_k_pasadas.csv (esas filas); rerun/s03_salida.txt via_pub_K_no", "CONFIRMADO", 2, "deteccion",
     "python -B rerun/s03_estratos_cenit.py ...", C + "rerun/s03_salida.txt"),
]
with open(sys.argv[1], "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    for f in filas:
        w.writerow(f)
print("filas escritas:", len(filas))
