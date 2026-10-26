# Lista que verificas (de F1B: 5 de 17 hallazgos; gravedad 3 o más)

Sólo título, ubicación, gravedad y comando del auditor. No abras C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f1b\INFORME.md; sí puedes correr sus scripts (están en C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f1b).

## 180 (gravedad 4, CONFIRMADO para el codigo del run de S148 y SOSPECHA para el codigo exacto de S130)
- TÍTULO: El NO ADOPTAR de D18 en S130 salio de un instrumento que no podia ver la caja: Test 1 integrado encendido (R9) y segundo pase sin la mascara (R8); el frente sigue cerrado hoy por S151 sobre otra premisa (geolocalizacion MODIS)
- UBICACIÓN: docs/s130/VEREDICTO_AB_D18.md:3; origin/s146-ab/35572961810:pipeline/process_viirs.py:1313; CLAUDE.md A114 y A118; docs/MIROVA_DIVERGENCES.md:2385-2393
- COMANDO DEL AUDITOR: python -B experiments/_s160_audit/f1b/r8_consumidores.py D:/vrp-trabajo/temporales/s160_audit/f1b/process_viirs_ramaG.py
- SALIDA CRUDA: experiments/_s160_audit/f1b/r8_ramaG_salida.txt

## 181 (gravedad 4, CONFIRMADO (la discrepancia 133 contra 137 es SOSPECHA en su causa))
- TÍTULO: El A/B de la conectiva (S148) se declaro CONFIRMADA mientras su evaluador imprime INDECIDIBLE: el control positivo esta calibrado para produccion con Test 1 y el veredicto se tomo de otro script; reproducido hoy (C4 C6 C7 falsos; recall del control 133 de 143 contra 137 del documento)
- UBICACIÓN: docs/S148_RESULTADO_AB_CONECTIVA.md:64-70 y 76-79; experiments/_s146_ab_sin_test1/evaluar.py:757-775
- COMANDO DEL AUDITOR: python -B experiments/_s146_ab_sin_test1/evaluar.py --control <S>/_s146_ab_sin_test1 --brazo <S>/_s147_ab_sin_test1_max --out experiments/_s160_audit/f1b/s148/real.json (S = D:/vrp-trabajo/temporales/s160_audit/f1b/s148/experiments/_s146_ab_sin_test1/salidas/35548121381)
- SALIDA CRUDA: experiments/_s160_audit/f1b/s148/real_stdout.txt

## 182 (gravedad 4, CONFIRMADO)
- TÍTULO: El A/B de D22 y D25 (S143) decidio sobre una ventana que cruza #535 sin tramo y pisa tres hitos de la referencia sin separarlos y con el Test 1 integrado encendido; su NO ADOPTAR es lo que hoy cierra D22 (S150 no la rehace)
- UBICACIÓN: experiments/_s143_evaluador/parametros.json (ventana 2026-06-01 a 2026-08-31); experiments/_s143_evaluador/evaluar.py (0 coincidencias de 535); docs/MIROVA_DIVERGENCES.md:2734; experiments/_s150_ab_d22/PREREGISTRO.md:3
- COMANDO DEL AUDITOR: grep -c 535 experiments/_s143_evaluador/evaluar.py; python -B experiments/_s143_evaluador/evaluar.py --dir D:/vrp-trabajo/temporales/s160_audit/f1b/s143/s143_ab --ref-cons <main>/latest_consolidado.csv --ref-ocr <main>/data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv --B 1000
- SALIDA CRUDA: experiments/_s160_audit/f1b/s143/base_stdout.txt

## 188 (gravedad 3, CONFIRMADO)
- TÍTULO: El A/B diurno sobre C0 tiene un G1 que empata con su propio p95 (W3 a W6: +0.2303 contra +0.2303) y una ventana W4 que cruza #535 sin partir; no cambia el NO ADOPTAR (W2 a W6 falla con margen y G2 falla por saturacion 2236 de 2511) pero el evaluador decide el A/B pendiente sobre K
- UBICACIÓN: origin/loop/activo:experiments/_s151_ab_diurno/salidas/W2_W6_s154/evaluar_salida.txt:322-327 y 571; experiments/_s151_ab_diurno/PREREGISTRO.md:62-67
- COMANDO DEL AUDITOR: git show origin/loop/activo:experiments/_s151_ab_diurno/salidas/W2_W6_s154/evaluar_salida.txt | sed -n 322-327p
- SALIDA CRUDA: experiments/_s160_audit/f1b/INFORME.md (transcripcion)

## 189 (gravedad 3, SOSPECHA (censo de subagente; ventana leida por mi en el README))
- TÍTULO: Los tres probes MxD03 (1.17 1.21 1.23) decidieron NO ADOPTAR bajo C0 sobre una ventana 2026-03-01 a 2026-10-12 que cruza #535 sin tramo y con artefactos fuera del repo (%TEMP%): no reproducibles hoy y pendientes de repetir sobre K
- UBICACIÓN: experiments/_s151_mxd03_etiquetas/README.md:68; experiments/_s159/mxd03_prereg/PREREGISTRO_MXD03.md:3
- COMANDO DEL AUDITOR: ls experiments/_s151_mxd03_*
- SALIDA CRUDA: experiments/_s160_audit/f1b/matriz_instrumentos.csv

## Celdas FALLA de la matriz de F1b (se verifican todas: plan §4). Sólo instrumento y fila; el razonamiento del auditor no se entrega.

- S125 A/B de magnitud (R1 |  R2 | fila R4_poblacion | scripts: OK (NO ADOPTAR con la causa aislada)
- S125 A/B de magnitud (R1 |  R2 | fila R11_tolerancia | scripts: OK (NO ADOPTAR con la causa aislada)
- S125 A/B de magnitud (R1 |  R2 | fila R16_nombre | scripts: OK (NO ADOPTAR con la causa aislada)
- S126 A/B de la corona Eq.6 en VIIRS 375 | docs/S126_CORONA_PREREGISTRO.md + experiments/_s126_corona/01_veredicto.py | fila R2_cobertura | scripts: R2/R6: placebo.py + correr_evaluador_raiz.py -> s126/*.txt; R7: r7_barajado_s126.py -> s126/r7_barajado_salida.txt
- S126 A/B de la corona Eq.6 en VIIRS 375 | docs/S126_CORONA_PREREGISTRO.md + experiments/_s126_corona/01_veredicto.py | fila R9_saturacion | scripts: R2/R6: placebo.py + correr_evaluador_raiz.py -> s126/*.txt; R7: r7_barajado_s126.py -> s126/r7_barajado_salida.txt
- S126 A/B de la corona Eq.6 en VIIRS 375 | docs/S126_CORONA_PREREGISTRO.md + experiments/_s126_corona/01_veredicto.py | fila R14_referencia | scripts: R2/R6: placebo.py + correr_evaluador_raiz.py -> s126/*.txt; R7: r7_barajado_s126.py -> s126/r7_barajado_salida.txt
- S129 A/B de fondos (GAP #A pool mu sigma) | docs/s129/PREREGISTRO_AB_FONDOS.md + experiments/_s129_ab_fondos/veredicto.py | fila R9_saturacion | scripts: solo lectura
- S129 A/B de fondos (GAP #A pool mu sigma) | docs/s129/PREREGISTRO_AB_FONDOS.md + experiments/_s129_ab_fondos/veredicto.py | fila R14_referencia | scripts: solo lectura
- S130 A/B de D18 (caja de 5 x 5 km) | docs/s130/PREREGISTRO_AB_D18.md + experiments/_s130_d18/veredicto_d18.py | fila R8_contrafactual | scripts: R8: r8_consumidores.py sobre origin/s146-ab/35572961810:pipeline/process_viirs.py -> r8_ramaG_salida.txt
- S130 A/B de D18 (caja de 5 x 5 km) | docs/s130/PREREGISTRO_AB_D18.md + experiments/_s130_d18/veredicto_d18.py | fila R9_saturacion | scripts: R8: r8_consumidores.py sobre origin/s146-ab/35572961810:pipeline/process_viirs.py -> r8_ramaG_salida.txt
- S130 A/B de D18 (caja de 5 x 5 km) | docs/s130/PREREGISTRO_AB_D18.md + experiments/_s130_d18/veredicto_d18.py | fila R14_referencia | scripts: R8: r8_consumidores.py sobre origin/s146-ab/35572961810:pipeline/process_viirs.py -> r8_ramaG_salida.txt
- S130 A/B de D18 (caja de 5 x 5 km) | docs/s130/PREREGISTRO_AB_D18.md + experiments/_s130_d18/veredicto_d18.py | fila R16_nombre | scripts: R8: r8_consumidores.py sobre origin/s146-ab/35572961810:pipeline/process_viirs.py -> r8_ramaG_salida.txt
- S135 A/B de D1 y D2 (keep_peak y segundo pase) 5 brazos | docs/PREREGISTRO_AB_D1_D2_S135.md + experiments/_s135_ab_d1d2/evaluar_ab.py | fila R9_saturacion | scripts: solo lectura
- S135 A/B de D1 y D2 (keep_peak y segundo pase) 5 brazos | docs/PREREGISTRO_AB_D1_D2_S135.md + experiments/_s135_ab_d1d2/evaluar_ab.py | fila R14_referencia | scripts: solo lectura
- S136 probe de 3 brazos (Test 1 contextual) | docs/PREREGISTRO_PROBE_S136_TEST1_CONTEXTUAL.md + experiments/_s136/evaluar_3brazos.py | fila R1_preregistro | scripts: solo lectura
- S136 probe de 3 brazos (Test 1 contextual) | docs/PREREGISTRO_PROBE_S136_TEST1_CONTEXTUAL.md + experiments/_s136/evaluar_3brazos.py | fila R9_saturacion | scripts: solo lectura
- S136 probe de 3 brazos (Test 1 contextual) | docs/PREREGISTRO_PROBE_S136_TEST1_CONTEXTUAL.md + experiments/_s136/evaluar_3brazos.py | fila R14_referencia | scripts: solo lectura
- S136 Apendice A y conectiva (prosa contra formula) | experiments/_s136/conformidad_apendice.py + VEREDICTO_CONECTIVA.md | fila R1_preregistro | scripts: solo lectura
- S136 Apendice A y conectiva (prosa contra formula) | experiments/_s136/conformidad_apendice.py + VEREDICTO_CONECTIVA.md | fila R16_nombre | scripts: solo lectura
- S143 A/B D22 y D25 (6 brazos) | docs/PREREGISTRO_AB_D22_D25_S143.md + experiments/_s143_evaluador/evaluar.py | fila R5_nulo | scripts: R2/R6: placebo.py + evaluar.py -> s143/placebo.md s143/placebo4.md; base: s143/base.md
- S143 A/B D22 y D25 (6 brazos) | docs/PREREGISTRO_AB_D22_D25_S143.md + experiments/_s143_evaluador/evaluar.py | fila R9_saturacion | scripts: R2/R6: placebo.py + evaluar.py -> s143/placebo.md s143/placebo4.md; base: s143/base.md
- S143 A/B D22 y D25 (6 brazos) | docs/PREREGISTRO_AB_D22_D25_S143.md + experiments/_s143_evaluador/evaluar.py | fila R10_regimen | scripts: R2/R6: placebo.py + evaluar.py -> s143/placebo.md s143/placebo4.md; base: s143/base.md
- S143 A/B D22 y D25 (6 brazos) | docs/PREREGISTRO_AB_D22_D25_S143.md + experiments/_s143_evaluador/evaluar.py | fila R14_referencia | scripts: R2/R6: placebo.py + evaluar.py -> s143/placebo.md s143/placebo4.md; base: s143/base.md
- S144 keep_peak con direccion | docs/PREREGISTRO_KEEP_PEAK_DIRECCION_S144.md + docs/CIERRE_FRENTE_KEEP_PEAK_S144.md | fila R1_preregistro | scripts: solo lectura
- S146 A/B sin Test 1 integrado | experiments/_s146_ab_sin_test1/PREREGISTRO.md + evaluar.py | fila R16_nombre | scripts: R2/R6: placebo.py + evaluar.py -> s148/placebo_stdout.txt s148/sin_dia_stdout.txt
- S146 A2 vara corregida | experiments/_s146_a2/evaluar_vara_corregida.py + docs/audit_s146/A2_CRITERIO_PRE_REGISTRADO.md | fila R1_preregistro | scripts: solo lectura
- S147/S148 A/B de la conectiva (brazo F max) | experiments/_s147_ab_conectiva/PREREGISTRO.md + docs/S148_RESULTADO_AB_CONECTIVA.md + experiments/_s146_ab_sin_test1/evaluar.py (reusado) + experiments/_s147_lectura/lectura_por_tramo.py | fila R8_contrafactual | scripts: R6: s148/real_stdout.txt s148/placebo_stdout.txt; R8: r8_ramaG_salida.txt
- S147/S148 A/B de la conectiva (brazo F max) | experiments/_s147_ab_conectiva/PREREGISTRO.md + docs/S148_RESULTADO_AB_CONECTIVA.md + experiments/_s146_ab_sin_test1/evaluar.py (reusado) + experiments/_s147_lectura/lectura_por_tramo.py | fila R16_nombre | scripts: R6: s148/real_stdout.txt s148/placebo_stdout.txt; R8: r8_ramaG_salida.txt
- S149 pre-registro de invierno (conectiva fuera de septiembre) | experiments/_s149_prereg_invierno/PREREGISTRO_INVIERNO.md + evaluar_ventana.py | fila R1_preregistro | scripts: solo lectura
- S150 A/B de D22 (sin compuerta sobre max) | experiments/_s150_ab_d22/PREREGISTRO.md + recuperacion_d22.py | fila R5_nulo | scripts: solo lectura
- S150 prueba de Nevados de Chillan en erupcion | experiments/_s150_ndc/PREREGISTRO_NDC.md + medir_ndc.py | fila R6_placebo | scripts: ndc_autoprueba_salida.txt
- S150 prueba de Nevados de Chillan en erupcion | experiments/_s150_ndc/PREREGISTRO_NDC.md + medir_ndc.py | fila R16_nombre | scripts: ndc_autoprueba_salida.txt
- S151 A/B diurno de VIIRS (D-10 y D27) | experiments/_s151_ab_diurno/PREREGISTRO.md + evaluar_diurno.py | fila R10_regimen | scripts: solo lectura (origin/loop/activo:experiments/_s151_ab_diurno/salidas/W2_W6_s154/evaluar_salida.txt l.322-327 y 571)
- S151 A/B diurno de VIIRS (D-10 y D27) | experiments/_s151_ab_diurno/PREREGISTRO.md + evaluar_diurno.py | fila R11_tolerancia | scripts: solo lectura (origin/loop/activo:experiments/_s151_ab_diurno/salidas/W2_W6_s154/evaluar_salida.txt l.322-327 y 571)
- S151 caja de 5 x 5 km sobre K (D18) | experiments/_s151_prereg_caja/PREREGISTRO.md + evaluar_caja.py | fila R4_poblacion | scripts: caja_autoprueba_salida.txt (no corrio: pide DIR_NDC)
- S151 caja de 5 x 5 km sobre K (D18) | experiments/_s151_prereg_caja/PREREGISTRO.md + evaluar_caja.py | fila R11_tolerancia | scripts: caja_autoprueba_salida.txt (no corrio: pide DIR_NDC)
- S151 caja de 5 x 5 km sobre K (D18) | experiments/_s151_prereg_caja/PREREGISTRO.md + evaluar_caja.py | fila R13_distribucion | scripts: caja_autoprueba_salida.txt (no corrio: pide DIR_NDC)
- S151 presupuesto de magnitud (1.14) | experiments/_s151_presupuesto_magnitud/PREREGISTRO.md + a_ a e_ | fila R1_preregistro | scripts: solo lectura
- S151 presupuesto de magnitud (1.14) | experiments/_s151_presupuesto_magnitud/PREREGISTRO.md + a_ a e_ | fila R14_referencia | scripts: solo lectura
- S151 MxD03 etiquetas (1.17) | experiments/_s151_mxd03_etiquetas/ + evaluar_mxd03.py | fila R10_regimen | scripts: solo lectura
- S151 MxD03 cumulo (1.21) | experiments/_s151_mxd03_cumulo_121/ + evaluar_cumulo.py | fila R10_regimen | scripts: solo lectura
- S151 MxD03 sola (1.23) | experiments/_s151_mxd03_sola_123/ + evaluar_sola.py | fila R10_regimen | scripts: solo lectura
- S151 saturacion en Chillan (1.18) | experiments/_s151_saturacion_chillan/ + evaluar_saturacion.py | fila R14_referencia | scripts: solo lectura
- CONTROL (c) S159 frente N estimador ponderado de F | experiments/_s159/n/ (resumen.json; 07_censo_analizar_salida.txt) | fila R3_censo | scripts: r3_censo_vs_ponderado.py -> r3_censo_vs_ponderado_salida.txt
- CONTROL (d) S148 caja G/H (A118) | docs/audit_s148/POR_QUE_LA_CAJA_NO_APAGA.md | fila R8_contrafactual | scripts: r8_consumidores.py -> r8_ramaG_salida.txt r8_main_salida.txt
