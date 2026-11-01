# Lista que verificas (de F4: 12 de 17 hallazgos; gravedad 3 o más)

Sólo título, ubicación, gravedad y comando del auditor. No abras C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f4\INFORME.md; sí puedes correr sus scripts (están en C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f4).

## 281 (gravedad 5, CONFIRMADO)
- TÍTULO: El reemplazo del historico con K (#883 en main) no bajo a ningun documento rector: CLAUDE.md MISSION.md SINTOMAS.md y el catalogo siguen diciendo que los datos son C0 antes del 2026-09-18
- UBICACIÓN: docs/MISSION.md:22-24; CLAUDE.md:127 190 1335; docs/SINTOMAS.md:9 19-21 109 198; docs/MIROVA_DIVERGENCES.md:1444 1507 1640 (main d516b9d8c)
- COMANDO DEL AUDITOR: git -C C:/vrp-trabajo/s159-pruebas show --stat 8471add46; grep -n 'DATOS_K_DESDE_UTC =' D:/vrp-trabajo/temporales/s160_audit/main/frontend/cambio_detector.js; python -I mis_conteos.py D:/vrp-trabajo/temporales/s160_audit/main
- SALIDA CRUDA: C:/vrp-trabajo/s159-pruebas/experiments/_s160_audit/f4/mis_conteos_salida.txt

## 282 (gravedad 4, CONFIRMADO)
- TÍTULO: El tope D9 de 5 MW bajo K casi no actua y las marcas S151 de A23 D9 y MISSION (1.565 topados 343 sobre 5 MW 7 pasadas de Chillan) ya no se reproducen: 16 y 183 en el corpus de hoy y 0 de 31 en Chillan
- UBICACIÓN: CLAUDE.md:381-390 (A23); docs/MISSION.md:134-140; docs/MIROVA_DIVERGENCES.md:221-235; docs/SINTOMAS.md:85-87
- COMANDO DEL AUDITOR: cd D:/vrp-trabajo/temporales/s160_audit/main && python -I C:/vrp-trabajo/s159-pruebas/experiments/_s150_meta_audit/verif_docs/contar_topados_d9.py; python -I mis_conteos.py ... (seccion 2)
- SALIDA CRUDA: C:/vrp-trabajo/s159-pruebas/experiments/_s160_audit/f4/t1_contar_topados_d9_salida.txt

## 283 (gravedad 4, CONFIRMADO)
- TÍTULO: D-4: los 439 (lectura A) y 992 (lectura B) de MISSION y CLAUDE.md no llevan ventana ni hash y el mismo script sobre la referencia congelada da 478 y 1.055
- UBICACIÓN: docs/MISSION.md:60-66; CLAUDE.md:1695; docs/S151_CRITERIO_CLASE_MIROVA.md:87 109 111
- COMANDO DEL AUDITOR: cd D:/vrp-trabajo/temporales/s160_audit/main && python -I scripts/clase_mirova.py --cons latest_consolidado.csv --ocr data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv
- SALIDA CRUDA: C:/vrp-trabajo/s159-pruebas/experiments/_s160_audit/f4/t1_clase_mirova_salida.txt

## 284 (gravedad 4, CONFIRMADO)
- TÍTULO: D-9 regla SN: de las '14 pasadas NONE con 0.04 MW o menos' solo 7 salen del script; las otras 7 y el '5 y 5 en 0.05' vienen de una lectura manual de imagenes sin instrumento persistido
- UBICACIÓN: docs/MISSION.md criterio de victoria punto 5; CLAUDE.md glosario Recall (marca D-9); experiments/_s151_alertas_minimas/README.md:32-36
- COMANDO DEL AUDITOR: cat experiments/_s151_alertas_minimas/frontera_salida.txt; sed -n 30,38p experiments/_s151_alertas_minimas/README.md
- SALIDA CRUDA: C:/vrp-trabajo/s159-pruebas/experiments/_s151_alertas_minimas/frontera_salida.txt

## 285 (gravedad 4, CONFIRMADO)
- TÍTULO: A118 en CLAUDE.md sigue diciendo 'D18 nunca se ha medido' sin marca cuando S151 la midio (KC NO CUMPLE veto) y SINTOMAS ya lo da por viejo
- UBICACIÓN: CLAUDE.md:1530 (main); docs/SINTOMAS.md:160; docs/MIROVA_DIVERGENCES.md:2300-2308
- COMANDO DEL AUDITOR: sed -n 1525,1535p D:/vrp-trabajo/temporales/s160_audit/main/CLAUDE.md
- SALIDA CRUDA: C:/vrp-trabajo/s159-pruebas/experiments/_s160_audit/f4/propagacion_grep_salida.txt

## 286 (gravedad 4, CONFIRMADO)
- TÍTULO: Todo S158 (D34 AUDIT_S158 marcas A113 de R2) vive solo en loop/activo (67 commits por delante); en main los textos que se leen primero siguen sin marca y en loop/activo U1 U3 U8 U9 U10 U11 U12 U13 y el encabezado de D27 siguen sin marca
- UBICACIÓN: CLAUDE.md:138 161 205 (main); docs/MISSION.md:290; docs/MIROVA_DIVERGENCES.md:1086; loop/activo: docs/MIROVA_DIVERGENCES.md:3314 2385 2875 1104; CLAUDE.md:152 181; docs/DISENO_D17_REMUESTREO_UTM.md:282
- COMANDO DEL AUDITOR: git -C C:/vrp-trabajo/s159-pruebas cat-file -e d516b9d8c:docs/AUDIT_S158.md; git show d516b9d8c:docs/MIROVA_DIVERGENCES.md | grep -c D34; grep -n 'trasladar\|igual para todos\|scene=0.010' docs/MIROVA_DIVERGENCES.md
- SALIDA CRUDA: C:/vrp-trabajo/s159-pruebas/experiments/_s160_audit/f4/propagacion.csv

## 287 (gravedad 4, CONFIRMADO)
- TÍTULO: El '1 SIN EVIDENCIA' de A113 (D9: 207 de 214 reales 0 fuga) sigue sin evidencia; S159 no lo toco; la memoria del agente lo repite sin marca y bajo K la poblacion que lo sostenia cambio
- UBICACIÓN: docs/audit_s146/FRENTE_A_SIN_RESPALDO.md:78 151; memoria/reference_s113_cirrus_d9_scope.md:3 17 23 36 37; memoria/project_s113_estado.md:34 40
- COMANDO DEL AUDITOR: grep -rln '207 de 214' experiments/_s159/ (vacio); python -I propagacion_grep.py (R3)
- SALIDA CRUDA: C:/vrp-trabajo/s159-pruebas/experiments/_s160_audit/f4/propagacion_grep_salida.txt

## 288 (gravedad 3, CONFIRMADO)
- TÍTULO: La memoria del agente (cargada en cada sesion) conserva cinco cierres o numeros ya rebajados sin marca: 'S27 Test1 cierra D4 (recall 50->80 %)' 207 de 214 '86 % enero' '482 pixeles' 'supervision manual ~5 %'
- UBICACIÓN: memoria/MEMORY.md:50-51; reference_s113_cirrus_d9_scope.md:3-37; reference_calidad_referencia_mirova_por_mes.md:11; reference_s123_reglas_a86_a88.md:23; reference_mirova_daytime_cloud_artifact.md:29-30; milestone_s27_h_s27_1_confirmada.md:3
- COMANDO DEL AUDITOR: python -I propagacion_grep.py ... (R3 R4 R9 R11 R12)
- SALIDA CRUDA: C:/vrp-trabajo/s159-pruebas/experiments/_s160_audit/f4/propagacion_grep_salida.txt

## 289 (gravedad 3, CONFIRMADO)
- TÍTULO: README.md de main describe el Test 1 integrado como detector vivo en cuatro pasajes sin ninguna marca de K
- UBICACIÓN: README.md:54 92 131 220 (main d516b9d8c)
- COMANDO DEL AUDITOR: git -C C:/vrp-trabajo/s159-pruebas show d516b9d8c:README.md | grep -n 'integrated-ROI\|Test 1'
- SALIDA CRUDA: C:/vrp-trabajo/s159-pruebas/experiments/_s160_audit/f4/propagacion.csv

## 290 (gravedad 3, CONFIRMADO)
- TÍTULO: D27 marca S151 (1.642 alertas 19 protegidas de tarde 233 de noche) ya no se reproduce sobre la referencia congelada: 1.589 / 20 / 228; la tabla perdio 53 alertas de esa ventana y la marca no lleva hash
- UBICACIÓN: docs/MIROVA_DIVERGENCES.md:2862 (D27 tercera marca S151)
- COMANDO DEL AUDITOR: python -I mis_conteos.py D:/vrp-trabajo/temporales/s160_audit/main (seccion 3)
- SALIDA CRUDA: C:/vrp-trabajo/s159-pruebas/experiments/_s160_audit/f4/mis_conteos_salida.txt

## 291 (gravedad 3, CONFIRMADO)
- TÍTULO: D33: el efecto (+5 a +7.5 %) se reproduce pero los n y las razones de la marca (24 records 12 pasadas 0.362 -> 0.382) son del corpus anterior a #883; hoy 581 records y 95 pasadas 0.493 -> 0.522
- UBICACIÓN: docs/MIROVA_DIVERGENCES.md:3196-3220; docs/SINTOMAS.md:58-60
- COMANDO DEL AUDITOR: F4_ROOT=D:/vrp-trabajo/temporales/s160_audit/main python -I t1_medir_efecto_lambda_copia.py --dest D:/vrp-trabajo/temporales/s160_audit/f4/lambda
- SALIDA CRUDA: C:/vrp-trabajo/s159-pruebas/experiments/_s160_audit/f4/t1_medir_efecto_lambda_salida.txt

## 293 (gravedad 3, CONFIRMADO)
- TÍTULO: Pendientes F2-H3 a F2-H9 de S158: ninguno resuelto en S159; H5 y H6 llevan marca S158 R2 solo en loop/activo; H3 H4 H7 H8 H9 siguen sin marca en las dos ramas
- UBICACIÓN: CLAUDE.md:205 (A4); docs/MISSION.md:290; CLAUDE.md:138 161; docs/MIROVA_DIVERGENCES.md:1086; pipeline/detection_context.py:974-984; documentacion/BIBLIOGRAPHY_SYNTHESIS.md:248
- COMANDO DEL AUDITOR: grep -rn 'F2-H[3-9]' experiments/_s159/ (vacio); grep -n 'S158' docs/MIROVA_DIVERGENCES.md | head (loop/activo)
- SALIDA CRUDA: C:/vrp-trabajo/s159-pruebas/experiments/_s160_audit/f4/propagacion.csv
