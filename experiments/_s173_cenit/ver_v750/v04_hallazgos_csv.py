# -*- coding: utf-8 -*-
"""v04 (verificador S173, cenit V750): escribe hallazgos.csv con el modulo csv."""
import csv
from pathlib import Path

AQUI = Path(__file__).resolve().parent
C = "cd C:/Users/nmend/vrp-wt/s173_cenit/ver_v750 && "
F = [
    ("VV750-01", "La ventana efectiva son 20 dias de una erupcion (12 noches) y el universo son los objetivos de N (28 de 31 alertas); s02 sobredeclara abril a octubre",
     "v750/s02_razon_por_cenit.py:128; v750/s02_salida.txt (ventana de los positivos)", "CONFIRMADO", 2, "instrumento/ventana",
     C + "python -B v01_pareo_propio.py", str(AQUI / "v01_salida.txt")),
    ("VV750-02", "F del 2026-10-01 05:24 topado por D9 (5,0 MW, sin tope 6,214), dejado como |dif| max 1,21 sin veredicto; K de main 2026-10-24 05:30 tambien topado",
     "v750/s03_salida.txt (F record pc vs F_pc_central); insumos/n/run_39682867040 resultados_02.json id 319 F; repo/data/mirova_equivalent/NevadosDeChillan.json 2026-10-24 05:30",
     "CONFIRMADO", 2, "instrumento/D9", C + "python -B v02_dentro_de_la_noche.py", str(AQUI / "v02_salida.txt")),
    ("VV750-03", "Condicion necesaria de la SOSPECHA area/remuestreo: f requerido de F (1,3/1,9/2,2) cabe bajo 4,39x del ATBD y F x sec(z) queda plano; K requiere 6x",
     "v03_area_y_placebo.py:v03_salida.txt secciones (2) y (2 bis); ref_s131_ley_de_area.md:106-116", "CONFIRMADO (condicion necesaria); SOSPECHA (atribucion)", 2,
     "remuestreo/area (D17)", C + "VRP_PROFILE=mirova_equivalent python -B v03_area_y_placebo.py", str(AQUI / "v03_salida.txt")),
    ("VV750-04", "O_comp (compuerta en los dos pases) cae dentro de la noche 21 de 25 (p 0,0003) con un tercio del tamano del fondo de anillo; no es la compuerta de K",
     "v02_dentro_de_la_noche.py:v02_salida.txt (b bis); repo/pipeline/detection_context.py:822-835; repo/pipeline/process_viirs_mod.py:916", "CONFIRMADO", 1,
     "pieza/compuerta (D22)", C + "python -B v02_dentro_de_la_noche.py", str(AQUI / "v02_salida.txt")),
    ("VV750-05", "El control positivo (4) de s01 no puede fallar mientras el codigo corra; el placebo +1 dia 0/47 depende del subconjunto (9 de 82 en la misma ventana)",
     "v750/s01_ablacion_chillan.py:112-117; v750/s02_razon_por_cenit.py:149,163-164; v01_salida.txt; v03_salida.txt (1)", "CONFIRMADO", 1, "instrumento/controles",
     C + "python -B v01_pareo_propio.py && VRP_PROFILE=mirova_equivalent python -B v03_area_y_placebo.py", str(AQUI / "v03_salida.txt")),
    ("VV750-06", "El placebo VRP de MIROVA barajado no es nulo por construccion (-0,430 FUERA en la ventana larga): el pc de K cae solo con el cenit (-0,469) y MIROVA es plano (-0,098)",
     "v01_pareo_propio.py:v01_salida.txt; v02_dentro_de_la_noche.py:v02_salida.txt (a)", "CONFIRMADO", 1, "instrumento/nulo",
     C + "python -B v01_pareo_propio.py && python -B v02_dentro_de_la_noche.py", str(AQUI / "v02_salida.txt")),
    ("VV750-07", "Los 3 positivos con VRP solo del OCR traen el VRP truncado a entero: sesgo de hasta 1 MW en esas razones",
     "repo/data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv (Nota_Validacion: VRP truncado); v01_salida.txt (fuente CONS 28, OCR 3)", "CONFIRMADO", 1,
     "vara/OCR", C + "python -B v01_pareo_propio.py", str(AQUI / "v01_salida.txt")),
]
with open(AQUI / "hallazgos.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    w.writerows(F)
print(open(AQUI / "hallazgos.csv", encoding="utf-8").read())
