# -*- coding: utf-8 -*-
"""Escribe hallazgos.csv del verificador VD con el módulo csv (campos con comas entre comillas)."""
import csv, os
C = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\vd"
T = "D:/vrp-trabajo/temporales/s179-audit"
filas = [
 ["551", "VERIFICA 551: CONFIRMADO EN PARTE. B1 publica con radiante y la retro decidió con cercano; 5 de 72 se reproduce, pero las 5 son sólo OCR con distancia dudosa y con la tabla sola radiante pierde 0 de 44",
  "pipeline/mirova_v750_codigo.py:670-726; experiments/_s172_retro_paquete/leer_retro.py:1274 (438a60a1e)", "CONFIRMADO EN PARTE", 3, "D",
  f"python vd1_cercano_vs_radiante.py {T}/main {T}/d/base /c/Users/nmend/vrp-temporales/s177_d2 /c/Users/nmend/vrp-temporales/s177_d4 {T}/vd vd1_cercano_vs_radiante_salida.json",
  os.path.join(C, "vd1_cercano_vs_radiante_salida.txt")],
 ["DEC-14", "VERIFICA DEC-14: REFUTADO. La lectura con candado calculó radiante con fila 6 y P1 sin pérdida; las pérdidas OCR de radiante en F26 son N-3",
  "git show ff8a39972:experiments/_s178_lectura/lectura.json; leer_retro.py:423-431", "REFUTADO", 1, "D",
  "git show ff8a39972:experiments/_s178_lectura/lectura.json (campo sensores.VIIRS375)", os.path.join(C, "vd5_lectura_retro_v375_salida.txt")],
 ["552", "VERIFICA 552: CONFIRMADO. Reemplazo MODIS deja el nulo en 0 pares y VERDE pasa a VIGILANCIA_CIEGA; no tapa una reversión, abre un issue diario",
  "scripts/vigilancia_guardia_modis.py:296-313,374-379,526-528 (438a60a1e)", "CONFIRMADO", 2, "D",
  f"python ../d/m3_vigilancia_tras_reemplazo.py {T}/main {T}/d/base {T}/vd/sim_modis rerun_m3_salida.json", os.path.join(C, "rerun_m3_salida.txt")],
 ["553", "VERIFICA 553: CONFIRMADO. El encendido de la regla sellada retrocede al 2026-11-08 18:04:23 UTC (processed_utc de D2) y el nulo VIIRS pasa de 223 a 0",
  "REGLA_REVERSION_V375E_BORRADOR.md:57-59; scripts/vigilancia_guardia_modis.py:124-146; scripts/reemplazar_ventana_reproceso.py:72-77", "CONFIRMADO", 3, "D",
  "python vd2_processed_utc.py /c/Users/nmend/vrp-temporales/s177_d2 /c/Users/nmend/vrp-temporales/s177_d4 ; python ../d/m3b_vigilancia_viirs_tras_reemplazo.py ...",
  os.path.join(C, "vd2_processed_utc_salida.txt")],
 ["554", "VERIFICA 554: CONFIRMADO EN PARTE. El plan sólo mide cobertura; pero marzo a octubre sí se leyeron contra MIROVA dentro de muestra en los A/B",
  "docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md:6-7,272-274 (62ccb8830); PREREGISTRO_RETRO_PAQUETE.md:130-136 (0472cd95e)", "CONFIRMADO EN PARTE", 2, "D",
  "git show 62ccb8830:docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md | sed -n 1,12p", os.path.join(C, "INFORME_VD.md")],
 ["DEC-1", "VERIFICA DEC-1: CONFIRMADO EN PARTE. La sombra de los 34 se abrió antes de la Compuerta A con una frase posterior interpretada (01:24 UTC); la página preliminar no tiene frase",
  "docs/superpowers/plans/2026-11-02-nrt-34-volcanes.md:397-401; tasks/LOOP_OBJETIVOS.md:1598-1604,1621 (0472cd95e)", "CONFIRMADO EN PARTE", 2, "D",
  "sed -n 1598,1604p tasks/LOOP_OBJETIVOS.md (0472cd95e)", os.path.join(C, "INFORME_VD.md")],
 ["DEC-7", "VERIFICA DEC-7: CONFIRMADO. #972 sin frase de Nicolás citada en bitácora, PR ni commit; página enlazada desde index.html",
  "tasks/LOOP_OBJETIVOS.md:699 (0472cd95e); frontend/index.html:419 (438a60a1e)", "CONFIRMADO", 2, "D",
  "git log -1 --format=%B bfab7c8c0 ; grep -n preliminar_34 frontend/index.html", os.path.join(C, "INFORME_VD.md")],
 ["DEC-17", "VERIFICA DEC-17: REFUTADO. El orden está como recomendación en Decisiones que espera el dueño; 3 noches respaldado por la regla sellada §3",
  "tasks/BLOQUE_ARRANQUE_S179.md:34-39,110 (0472cd95e); REGLA_REVERSION_V375E_BORRADOR.md:51 (438a60a1e)", "REFUTADO", 1, "D",
  "sed -n 34,46p tasks/BLOQUE_ARRANQUE_S179.md", os.path.join(C, "INFORME_VD.md")],
 ["VD-01", "Tras el reemplazo de VIIRS, las pasadas reprocesadas entre el 2026-11-08 18:04 UTC y el merge real de B1 entran al disparador de reversión pre-autorizado y a las cotas",
  "scripts/vigilancia_guardia_modis.py:221-223 (438a60a1e); REGLA_REVERSION_V375E_BORRADOR.md:57-59; PLAN_REEMPLAZO_HISTORIA_VIA_S178.md:284-286 (62ccb8830)",
  "CONFIRMADO (mecanismo) / SOSPECHA (que dispare)", 3, "D",
  f"python ../d/m3b_vigilancia_viirs_tras_reemplazo.py {T}/main {T}/d/base <sim> <salida.json>", os.path.join(C, "rerun_m3b_salida.txt")],
 ["VD-03", "El PR de B1 (#974) no dice que producción publicará con radiante mientras la retrospectiva decidió con cercano",
  "insumos/pr_974.json (cuerpo)", "CONFIRMADO", 2, "D",
  "python: re.finditer('(?i)(radiante|cercano|posici)', body) sobre insumos/pr_974.json y pr_983.json", os.path.join(C, "vd4_pr974_983_busqueda_posicion_salida.txt")],
 ["VD-02", "La lectura de la retrospectiva informa las pérdidas sólo OCR únicamente del brazo que decide; las del brazo de producción no se muestran",
  "experiments/_s172_retro_paquete/leer_retro.py:1309,1330-1333 (438a60a1e)", "CONFIRMADO", 2, "D",
  "ver vd1 y vd5", os.path.join(C, "vd5_lectura_retro_v375_salida.txt")],
 ["VD-04", "Las 5 protegidas perdidas de VIIRS 375 tienen una referencia de MIROVA débil o contradictoria (distancia 0 fija en marzo, aprox ambigua hasta 20-23 km en octubre, RUTINA en la tabla en Isluga 10-03)",
  "registro_vrp_ocr.csv y latest_consolidado.csv de 438a60a1e", "CONFIRMADO (filas) / SOSPECHA (lectura)", 2, "D",
  f"python vd3_filas_ocr_cinco.py {T}/d/base/latest_consolidado.csv {T}/d/base/data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv",
  os.path.join(C, "vd3_filas_ocr_cinco_salida.txt")],
]
with open(os.path.join(C, "hallazgos.csv"), "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    w.writerows(filas)
print(len(filas), "filas")
