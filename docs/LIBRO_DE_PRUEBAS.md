# Libro de pruebas: VRP Chile

Registro único de lo que este proyecto probó: una fila por prueba del catálogo de hipótesis S146 (frente H), con el instrumento que la midió, si ese instrumento sigue existiendo hoy, y sus enlaces (cuando hay un identificador compartido, nunca por parecido de redacción) con los mecanismos vivos de la cadena de detección (frente G) y con los cierres del grafo de dependencias (frente E). Generado por `scripts/libro_de_pruebas.py` a partir de:

- `experiments/_s146_auditoria/frente_E/grafo.json`
- `experiments/_s146_auditoria/frente_H/hipotesis.json`
- `experiments/_s146_auditoria/frente_G/inventario.json`

**No editar a mano**: ver la última sección, "Cómo agregar una prueba".

## Resumen

- Total de pruebas: **53**
- Con al menos un mecanismo del inventario G enlazado: **24** (sin enlace: 29)
- Con al menos un cierre del grafo E enlazado: **18** (sin enlace: 35)

**Por veredicto del frente H:**

| veredicto | pruebas |
|---|---|
| CONFIG | 30 |
| NUNCA | 6 |
| OBSOLETA | 4 |
| PERDIDO | 3 |
| SIGUE | 10 |

**Por estado del instrumento** (¿el script/workflow citado existe hoy?):

| estado | pruebas |
|---|---|
| EXISTE | 46 |
| NO_ENCONTRADO | 3 |
| SIN_RUTA | 4 |

## Tabla, ordenada por sesión

| id | sesión | qué se probó | instrumento (estado) | ventana de datos | configuración | veredicto (frente H) | veredicto original | mecanismos G | cierres E |
|---|---|---|---|---|---|---|---|---|---|
| H-34 | S16/S17, abril 2026 | H1, H2, H3, H5, H7, H8 (S17): sigma del venteo, caja de busqueda chica, descarga sin timeout, regresion de codigo, zona horaria del scraper, referencia erronea | commits y py-spy citados en el log: **SIN_RUTA** | abril 2026 | camino de venteo retirado | SIGUE | REFUTADAS (la causa real era NOAA-21, H10) | ,  | ,  |
| H-31 | S19, 2026-04-25 | N sigma uniforme 3 contra 5 (Coppola) y 12 (Di Bella) en el umbral de temperatura de brillo | docs/DRIFTS_S17.md (existe); 6 reprocesos locales: **EXISTE** | 30 dias, abril 2026 | PRE46, M260, SEC3 | OBSOLETA | REFUTADA: 3 sigma gana; 5 y 12 dan resultados identicos al … | ,  | ,  |
| H-33 | S21, 2026-04-25 | Sigma del fondo calculado solo en el ROI de cumbre (D6) para que el glaciar no infle el umbral | experiments/41_DIAGNOSIS_FINAL_S21.md (existe): **EXISTE** | 3 granulos | PRE46, camino de venteo (retirado S27) | OBSOLETA | REFUTADA | ,  | ,  |
| H-40 | S23, 2026-04-26 | Local p95 del ROI como umbral adicional (D7): agregarlo a VIIRS 375 o quitarlo de MODIS y V750 | tests/test_local_roi_paridad.py: **EXISTE** | no aplica |  | OBSOLETA | diferida 'requiere A/B contra OSF' | G-07, G-08, G-09 | ,  |
| H-32 | S24, 2026-04-26 | Aveni 2025 Ec. 9 (VRP por TIR) para el lago de lava de Villarrica; y k de Di Bella para VIIRS 375 | experiments/52_aveni_tir_poc.py (existe): **EXISTE** | 6 refs de Villarrica; 37 pares de Tupungatito | PRE46 | SIGUE | REFUTADAS | G-16 | ,  |
| H-39 | S27, 2026-04-30 | Hipotesis abiertas de S27 que nunca se probaron: dNTI con C1 negativo, camino solo TIR (TIRVolcH), composicion de caminos en cascada contra OR | ninguno: **SIN_RUTA** | no aplica |  | NUNCA | quedaron como 'hipotesis abiertas S28+' en MISSION | ,  | ,  |
| H-A01 | S27 a S29, 2026-04-30/05-01 | ADOPCION. Test 1 integrado en el ROI: sumar el exceso MIR de todo el disco de 3 km para ver focos sub-pixel (detector propio, D30) | runs 25148058512 y reintentos; perfil _mirova_literal.yaml (existe): **EXISTE** | 2026-01-29 a 2026-04-29 | PRE46 (el camino contextual contra el que 'subio el recall'… | CONFIG | ADOPTADO: recall 50 a 80 % | G-26, G-27, G-31 | ,  |
| H-30 | S33, 2026-05-05 | Filtro por pixel a 5 sigma sobre el Test 1 (Phase 1), sobre la mascara final (Phase 2) y fondo global (D4) | experiments/76_audit_independent.py, pipeline/audit_metrics.py (existen); runs 25339969705, 25401379853, 25414145698: **EXISTE** | 90 dias hasta abril 2026 | PRE46, M260, SEC3, ANCLA_TUP | OBSOLETA | REFUTADOS: -18,6 y -63 puntos de recall | ,  | C_S29 |
| H-A10 | S38 a S77, mayo 2026 | ADOPCIONES sin A/B propio leido: agrupamiento anclado al crater y filtro de distancia por pixel (S38), fondo global del Test 1 por volcan (S39), BT path apagado (S40), modo de pix… | workflows _archive/reproc-ab-d8-*.yml, reproc-ab-lbg-global.yml, reproc-ab-h8.yml, reproc-no-bt-path-15d.yml; experiments/84 a 89 (existen): **EXISTE** | ventanas de 15 a 30 dias entre 2026-04-12 y 2026-05-11 | M260, SEC3, ANCLA_TUP | CONFIG | ADOPTADOS | ,  | ,  |
| H-23 | S46, 2026-05-15/16 | Barrido Coppola literal de 22 variantes: C2 = 3, 4, 8; C1 = 0,01; sin dual-ROI; Di Bella n = 12; drifts 1 a 7 | experiments/87_audit_s46_round1.py y 87_results.md (existen); workflow _archive/reproc-s46-coppola-literal-ab.yml: **EXISTE** | 2026-04-16 a 2026-05-16 | M260, SEC3, ANCLA_TUP, PISO | CONFIG | se adopto drift234; el resto 'sin diferencia' | ,  | ,  |
| H-A02 | S46, 2026-05-16 | ADOPCION. Primer pase Tests 2 y 3 mas segundo pase (drift234) | experiments/87_results.md: **EXISTE** | 2026-04-16 a 2026-05-16 | M260, SEC3 | CONFIG | ADOPTADO por +0,7 de F1 y 'alineacion con el paper' | ,  | ,  |
| H-27 | S55, 2026-05-17 | Cuatro estrategias de agregacion (pixel maximo, Eq.16, umbral estricto, radio de 1 km) | experiments/100_aggregation_strategies_offline.py (existe): **EXISTE** | 5 casos de Villarrica | SEC3, M260, ANILLO con recorte a cero | CONFIG | NEGATIVA: todas dan 0 en 4 de 5 | G-13, G-36, G-37, G-42 | C_D25V |
| H-26 | S56, 2026-05-17 | Fondo por percentil bajo del anillo (p01 a p25) para igualar la magnitud de MIROVA | experiments/101_background_variants_offline.py (existe): **EXISTE** | 5 casos de Villarrica | SEC3, M260 | NUNCA | confirmada offline, descartada como 'probable hack' a favor… | G-13, G-36, G-37, G-42 | C_D25V |
| H-A03 | S58 a S63, mayo 2026 | ADOPCION. Kernel de fondo local por volcan (Villarrica, Planchon-Peteroa, Lastarria, Chaiten, PCC) | workflows _archive/reproc-ab-local-kernel-bg*.yml, reproc-ab-pcc-kernel.yml, reproc-ab-chaiten.yml; experiments/104, 105 (existen): **EXISTE** | 2026-04-16 a 2026-05-15 (Villarrica); 2026-03-01 a 2026-05-… | M260, SEC3 | CONFIG | ADOPTADO por volcan | G-13, G-36, G-37, G-42 | C_D25V |
| H-24 | S62, 2026-05-19 | Kernel de fondo local en Tupungatito ('refuta el kernel en glaciar', A19) | workflow _archive/reproc-ab-lastarria-tupungatito.yml; run 26072884472: **EXISTE** | 2026-03-01 a 2026-05-19 | M260, SEC3, ANCLA_TUP | CONFIG | NO ADOPTAR: 10,37x a 18,46x | ,  | ,  |
| H-25 | S62, 2026-05-19 | Bajar el radio interno de PCC de 20 a 7 km | run 26072886354: **SIN_RUTA** | marzo a mayo 2026 | M260, SEC3 | SIGUE | revertido (3,64x, peor) | ,  | ,  |
| H-22 | S71, 2026-05-21 | Camino contextual en cirrus alto (D9): compuerta atmosferica por t_bg (A) y co-validacion con BT o NTI (B) | workflows _archive/reproc-ab-path-d-{atm-gate,covalidation,cap}.yml; perfiles mirova_equivalent_path_d_*_v1.yaml; experiments/127, 130, 131…: **NO_ENCONTRADO** | 2026-02-20 a 2026-05-20 | M260, G3K, SEC3, PRE46 ya no (el primer pase habia entrado … | CONFIG | A y B rechazadas; C (tope de 5 MW) adoptada | G-05, G-10, G-11, G-12, G-24, G-40, G-52 | C_D9, C_D9CAP, C_S45 |
| H-29 | S72 a S73, mayo 2026 | Filtros de no aptos del segundo pase, retiro de los Test 1 K1, BT path encendido, sin tope | workflows _archive/reproc-ab-{unsuitable-filters,unsuitable-only,test1-retire-only,bt-path-on-v1,no-cap-v1}.yml; perfiles mirova_equivalent…: **NO_ENCONTRADO** | 2026-02-20 a 2026-05-20 | M260, SEC3, G3K | CONFIG | filtros de no aptos adoptados (S72); retiro K1 apagado; BT … | ,  | ,  |
| H-41 | S90/S93, 2026-05-30 | Compuerta de coherencia de 'campo difuso' en el pipeline (backlog S93) y supresion de cirrus en display (S90) | tasks/backlog_s93_pipeline_diffuse_field_gate.md: **EXISTE** | no aplica |  | NUNCA | anotada como opcional, nunca corrida | G-52 | ,  |
| H-21 | S99, 2026-06-03 | Alternativas a ctxpeak para la magnitud del Test 1: filtro por pixel (41 FN), contextual puro (31 FN por crater embebido), nucleo espacial, Eq.16 | experiments/_s99_audit/ab_test1_audit.py (existe); runs 26864573601 y 26885140366; perfiles _s99_test1_*.yaml: **EXISTE** | 2026-04-01 a 2026-05-31 (S100) | M260, G3K, SEC3 | CONFIG | descartadas; 'ctxpeak es el UNICO' | ,  | ,  |
| H-A04 | S100, 2026-06-04 | ADOPCION. ctxpeak (D10): intersectar el Test 1 con la mascara contextual y rescatar siempre el pixel mas caliente (keep_peak) | experiments/_s99_audit/ab_test1_fair.py (existe); run 26921561612: **EXISTE** | 2026-04-01 a 2026-05-31 | M260, SEC3, G3K | CONFIG | ADOPTADO: 0 FN nuevos, Tupungatito 18,4x a 1,24x | G-23, G-32, G-38, G-39, G-42 | C_D10, C_D19N |
| H-A05 | S101 a S103, 2026-06-05/08 | ADOPCION. Area de pixel a nadir fijo, MODIS (S102) y VIIRS (S103) | experiments/_s99_audit/audit_nadir_promote_r3.py, analyze_viirs_nadir_ab.py (existen); workflows _archive/reproc-s10{1,2,3}-*.yml: **EXISTE** | 2026-01-29 a 2026-06-07 | M260 (VIIRS 375), G3K, T1 | SIGUE | ADOPTADO: VIIRS 375 2,27x a 0,78x | G-10 | ,  |
| H-20 | S102, 2026-06-06 | 'ctxpeak es un parche redundante del sec3': A/B de 3 brazos (base, nadir+ctx, nadir sin ctx) | workflow _archive/reproc-s102-viirs-noctx-ab.yml; experiments/_s99_audit/analyze_viirs_3way.py (existe): **EXISTE** | 2026-04-01 a 2026-06-06 | M260, G3K, T1 | CONFIG | REFUTADA: nadir sin ctx es 2,43x peor | G-10 | ,  |
| H-02 | S104, 2026-06-09 | Co-validacion por pixel en NTI del Test 1: exigir que cada pixel del disco tenga firma propia en el indice | experiments/_s104_roi_probe/audit_ab_test1_nti.py (existe); run 27186289487; perfiles _archive/_test1_nti_covalidation_{enabled,disabled}.y…: **EXISTE** | 2026-01-29 a 2026-06-08 (segun el yml) | M260, G3K, T1, ANILLO, C2G | CONFIG | REFUTADO: 'apaga el Test 1' (la senal difusa no tiene firma… | ,  | ,  |
| H-03 | S104/S105, 2026-06-09 | Test 1 que integra NTI (y no radiancia MIR absoluta) con fondo de anillo | experiments/_s104_roi_probe/audit_ab_test1_nti_v2.py (existe); run 27223821692; perfil _archive/_test1_nti_integral.yaml; flag ENABLE_TEST1…: **EXISTE** | 2026-01-29 a 2026-06-08 | M260, G3K, ANILLO, C2G | CONFIG | REFUTADO por insuficiente: corrige 50 m de 1000 a 1500 m; '… | G-28 | ,  |
| H-01 | S105/S106, 2026-06-10 | Test 1 con fondo LOCAL sobre NTI: medir el exceso de la cumbre contra sus vecinos inmediatos y en el indice MIR/TIR, para que el valle tibio bajo un cono nevado no cuente como cal… | experiments/_s104_roi_probe/audit_local_sweep.py y audit_sensor_strat.py (existen); workflow _archive/reproc-s105-test1-nti-local-sweep.yml…: **EXISTE** | 2026-01-29 a 2026-06-08 | M260, G3K, T1, ANILLO, C2G; SEC3 hasta el 7 de junio | CONFIG | REFUTADO en todo el barrido k=2,0/2,5/3,0: 'el Test 1 se ap… | G-28 | ,  |
| H-19 | S106, 2026-06-11; S117 | Ancla del cumulo en el pico de NTI (brazo B) en vez del crater; y no re-anclar ctx_cluster (A84) | A/B S106: workflows _archive/reproc-s106-*.yml y experiments/_s106_fase2/ (existen). Probe S117: scratchpad/probe_ctx_cluster_s117.py NO EX…: **NO_ENCONTRADO** | 2026-01-29 a 2026-06-11 | M260, G3K, T1 | PERDIDO | brazo B descartado (Llaima 2263 m, peor); A84 'no reabrir' | ,  | C_A84 |
| H-A06 | S106 a S112, junio 2026 | ADOPCION. Ancla espacial honesta (VIIRS 375 S106, V750 S108) y magnitud de nucleo focal (MODIS S109, V750 S112) | experiments/_s106_fase2/, _s109_modis_mag/audit_focalmag_ab.py, _s112_v750focal/ (existen): **EXISTE** | 2026-01-29 a 2026-06-17 | M260, B21, G3K | CONFIG | ADOPTADOS; S109 con C2 por debajo de lo pre-registrado, rei… | ,  | ,  |
| H-18 | S107/S108, 2026-06-13/14 | Fondo local para la MAGNITUD en MODIS (huella o anillo alrededor del cumulo) | experiments/_s107_modis_localmag/ (existe); run 27480234385; perfiles _archive/_modis_localmag_*.yaml: **EXISTE** | 2026-01-29 a 2026-06-13 | B21, G3K, ANILLO | CONFIG | REFUTADO: mas records suben que se curan | G-13, G-36, G-37, G-42 | C_D25V |
| H-36 | S111 a S114, junio 2026 | far a summit en MODIS: 8 discriminantes, N sigma de la Tabla 1, tope de magnitud (AUC 0,45), contexto temporal Method-2, ancla de primer pase | experiments/_s111_d11/, _s114_audit/ (existen): **EXISTE** | abril a junio 2026 | B21, G3K, ANILLO, conectiva min | CONFIG | A82: fisicamente irreducible, no reabrir | ,  | C_A82, C_D19N |
| H-17 | S112, 2026-06-17 | Cuantificar el Muy Bajo de NdC con otro fondo para el Test 1 (anillos 1,5-3, 2-4, 3-5 km, NTI local, Eq.16, nucleo espacial) | experiments/_s112_test1_lowmag/audit_t1lm_ab.py (existe); run 27705248529; perfiles _archive/_t1lm_*.yaml: **EXISTE** | 2026-05-01 a 2026-06-17 | M260, G3K, T1 | CONFIG | NO ADOPTAR por criterio... y ADOPTADO el mismo dia por deci… | ,  | ,  |
| H-A07 | S112, 2026-06-17 | ADOPCION. Anillo intermedio de fondo para el Test 1 mas prioridad al cumulo debil (S112), por volcan (Lascar, NdC, Lastarria) | experiments/_s112_test1_lowmag/audit_t1lm_ab.py (existe); run 27705248529: **EXISTE** | 2026-05-01 a 2026-06-17 | M260, G3K | CONFIG | ADOPTADO contra su propio criterio, por evidencia externa (… | G-31, G-37 | ,  |
| H-35 | S116, 2026-06-27 | Discriminante fisico por record entre foco debil real y artefacto (barrido de candidatos, AUC 0,859) | JSON sin script (B-08): **SIN_RUTA** | 4.560 records summit | M260, B21, G3K | PERDIDO | A83: agotado | ,  | C_A83 |
| H-16 | S118, 2026-06-28/07-01 | Cercas intra-radio por camino (S83/S85): 'protegen al crater del robo de cumulo' | experiments/_s118_c2ab/ (existe); run 28312968093; perfiles _c2ab_*.yaml: **EXISTE** | ventanas dirigidas (el yml solo trae su fecha de alta) | M260 (en VIIRS 375), G3K, T1 | CONFIG | REFUTADA la hipotesis; cercas a OFF (#474) | ,  | ,  |
| H-A09 | S118 y S130 | ADOPCION. Retiro de los pisos VRP (S130) y apagado de las cercas intra-radio (S118) | experiments/_s126_piso/, _s130_piso_vrp/, _s118_c2ab/ (existen): **EXISTE** | 2026-05-01 a 2026-08-28 (piso) |  | SIGUE | ADOPTADOS | ,  | ,  |
| H-15 | S121, 2026-07-17 | Ancla honesta en MODIS (D12): dejar de etiquetar far el foco de Lascar cuando un pixel del Salar roba el hotspot | experiments/_s121_d12_ab/ (existe el directorio; el frente B y V-09 dan los artefactos por perdidos); workflow reproc-s121-d12-modis-ab.yml: **EXISTE** | 2025-02-15 a 2026-07-17 | B21, G3K, ANILLO | PERDIDO | NO ADOPTAR (destapa 131 records de artefacto) | G-33 | C_D12 |
| H-14 | S124, 2026-08-27/28 | Remuestreo a grilla UTM (F70), 4 brazos | experiments/_s124_f70/ (existe); perfiles _f70_{a,b}.yaml: **EXISTE** | 2026-06-25 a 2026-08-24 | M260, G3K, T1, grilla mal centrada (D17), sin bow tie | CONFIG | NO ADOPTAR; D16 'CERRADA, no reabrir' | G-10, G-12, G-14 | C_D16 |
| H-13 | S125, 2026-08-28 | Brazos de magnitud A, B, C (apagar dos reducciones y encender la corona) para el sub-reporte VIIRS | experiments/_s125_magnitud/02_veredicto_ab.py (existe); perfiles _s125_mag_*.yaml: **EXISTE** | 2026-06-25 a 2026-08-24 | M260, G3K, T1, PISO | CONFIG | NO ADOPTAR todavia: 2 de 4 criterios; la direccion era corr… | ,  | ,  |
| H-A08 | S125/S126, 2026-08-28/29 | ADOPCION de hecho. Mascara de nube apagada (#535 la apago creyendo que era un no-op; S126 decidio no revertir) | experiments/_s126_cloudmask/02_veredicto.py (existe); runs 33257081431 y 33257082834: **EXISTE** | SIN DATO exacto (tres volcanes, invierno 2026) | G3K, T1, PISO | CONFIG | SOSTENER el apagado | ,  | ,  |
| H-12 | S126/S127, 2026-08-29/30 | Corona Eq.6 (fondo por la corona de pixeles que rodea al cumulo), 2x2 con el filtro contextual | experiments/_s126_corona/01_veredicto.py (existe); perfiles _s126_corona_{on,off,ctxoff}.yaml: **EXISTE** | 2026-06-25 a 2026-08-24 | G3K, T1, PISO aun activo | CONFIG | NO ADOPTAR: Villarrica sube 0,045 en vez de bajar; 8 detecc… | G-13, G-36, G-37, G-42 | C_D25V |
| H-11 | S129/S130, 2026-08-31 | Fondos autorreferentes (GAP A: sacar los pixeles del Test 1 por pixel del pool de mu y sigma; fondo de magnitud) | experiments/_s129_ab_fondos/, _s130_ab_sustrato/ (existen); workflow reproc-s129-ab-fondos.yml: **EXISTE** | 2026-03-01 a 2026-05-28 | G3K, B21, conectiva min | SIGUE | SIN VEREDICTO: los brazos no difieren, el mecanismo casi no… | ,  | ,  |
| H-28 | S129, 2026-08-30 | Sumar todos los pixeles alertados de la escena, como escribe Coppola 2019 p. 3, en vez de publicar un solo cumulo; barrido de radio uniforme | experiments/_s129_suma/01_suma_vs_cluster.py y 02_radio_de_suma.py (existen): **EXISTE** | records de 2026 (SIN DATO si separa tramos: no abri el scri… | G3K, T1, ANILLO con recorte, keep_peak | NUNCA | NEGATIVO: el mejor radio uniforme (10 km) gana un volcan; '… | ,  | ,  |
| H-10 | S130, 2026-08-31/09-01 | ROI1 como caja de 5 km igual para todos (paper) en vez de circulo de 3 a 20 km por volcan (D18) | experiments/_s130_d18/ (existe); run 33456630043; perfiles _s130_d18_{caja,circulo}.yaml: **EXISTE** | 2026-05-29 a 2026-08-24 | G3K, B21, T1, ANILLO | CONFIG | NO ADOPTAR por ausencia de beneficio | G-15 | C_D18 |
| H-43 | S132, 2026-09-03 | A/B de distance_class en MODIS (decision 4 de AUDIT_S131) | experiments/_s132/ab_distance_class_modis.json (citado): **EXISTE** | SIN DATO | B21, G3K | CONFIG | NO ADOPTAR | ,  | C_A94 |
| H-08 | S133, 2026-09-05 | Area de pixel geolocalizada (en vez de nadir fijo) para corregir el gradiente cenital de la magnitud | experiments/_s133/analizar_ab_area.py, resultado_ab_area.json (existen); workflow reproc-s133-area-ab.yml: **EXISTE** | chunk 1: 2026-04-01 a 2026-05-31 (el yml llega a 08-31) | G3K, T1, ANILLO | CONFIG | NO ADOPTAR: invierte el signo del sesgo (veredicto declarad… | G-10 | ,  |
| H-09 | S133, 2026-09-05 | Banda 22 como primaria en MODIS (D21) | experiments/_s133/analizar_ab_b22.py, resultado_ab_b22.json (existen); workflow reproc-s133-b22-ab.yml: **EXISTE** | 2026-08-01 a 2026-08-31 | G3K, ANILLO, conectiva min | CONFIG | NO ADOPTAR (fallaron los dos criterios, el fondo cambio -1,… | G-08 | C_D21 |
| H-05 | S135, 2026-09-07 | Apagar keep_peak y/o condicionar el segundo pase (D19), 5 brazos | experiments/_s135_ab_d1d2/evaluar_ab.py y RESULTADO_FINAL.md (existen); workflow reproc-s135-ab-d1d2.yml; perfiles _s135_ab_*.yaml: **EXISTE** | 2026-06-01 a 2026-08-31 | G3K, T1, ANILLO | CONFIG | NO ADOPTAR: el brazo B (sin keep_peak) pierde 0 noches y qu… | G-23, G-32, G-38, G-39 | C_D19N |
| H-37 | S136, 2026-09-08 | Filtro por intensidad o distancia 'de Laiolo 2026' como clon literal | experiments/_s136/FILTRO_INTENSIDAD_DESCARTADO.md, piso_mirova.py (existen): **EXISTE** | canal NRT |  | SIGUE | DESCARTADO por dos vias | ,  | ,  |
| H-38 | S136, 2026-09-08 | Test 1 sin la interseccion contextual (tercer estado del eje: interseccion actual, contextual puro, sin interseccion) | experiments/_s136/probe_3brazos.py, RESULTADO_PROBE.md (existen); run 34274884640: **EXISTE** | 20 pasadas | G3K, ANILLO | NUNCA | INDETERMINADO por falta de sustrato (3 pasadas utiles de ne… | ,  | ,  |
| H-42 | S136 a S146 | Conectiva de los Tests 2 y 3: min (formula) contra max (prosa) | experiments/_s136/VEREDICTO_CONECTIVA.md, experiments/_s146_bateria/ (existen); workflow probe-s146-bateria-apendice.yml: **EXISTE** | 9 escenas MODIS del Apendice A (2000 a 2015) | se prueba con y sin B21 y G3K | SIGUE | S136: min no reproduce; S146: el mejor brazo usa max y da 9… | G-16 | ,  |
| H-07 | S141/S142, 2026-09-15 | Probe de vecinos tibios v1 y v2: en que etapa se pierden los vecinos del foco que MIROVA suma | experiments/_s141_fase1_probe{,_v2}/ (existen), runs 34929024703 y 34967596160: **EXISTE** | pasadas OSF 2025 reprocesadas con codigo de hoy | G3K, ANILLO | SIGUE | v1 INDETERMINADO; v2 HETEROGENEO en focal, INDETERMINADO en… | ,  | ,  |
| H-04 | S143, 2026-09-17/19 | Quitar la compuerta de 3 K (D22) y el fondo de anillo (D25) en VIIRS 375, brazo literal con 5 ablaciones | experiments/_s143_evaluador/ (existe), workflow reproc-s143-ab-d22d25.yml, perfiles _s142_ab_*.yaml: **EXISTE** | 2026-06-01 a 2026-08-31 | B21 no aplica; T1 activo en todos los brazos | SIGUE | NO ADOPTAR: ningun brazo cumple los tres | G-13, G-21, G-36, G-37, G-42 | C_D25V |
| H-06 | S144, 2026-09-19 | Medir con direccion (GeoTIFF UTM de MIROVA) si el cumulo lejano que publica keep_peak es el objeto de MIROVA | experiments/_s144_keep_peak_direccion/verificadores/ (existe): **EXISTE** | estratos ajenos a la muestra |  | NUNCA | CERRADO sin correr la medida (habria dado INCONCLUSO 90 % d… | ,  | ,  |

## Detalle del instrumento por prueba

Para cada ruta citada en el campo `instrumento` de la prueba: si existe directamente en el árbol, si sólo se encontró comprimida en `experiments/_archivo_ab_local/*.zip` (y en qué zip), o si no se encontró en ningún lado.

- **H-31**:
  - `docs/DRIFTS_S17.md`: EXISTE
- **H-33**:
  - `experiments/41_DIAGNOSIS_FINAL_S21.md`: EXISTE
- **H-40**:
  - `tests/test_local_roi_paridad.py`: EXISTE
- **H-32**:
  - `experiments/52_aveni_tir_poc.py`: EXISTE
- **H-A01**:
  - `_mirova_literal.yaml`: EXISTE (resuelto en `pipeline/profiles/_mirova_literal.yaml`)
- **H-30**:
  - `experiments/76_audit_independent.py`: EXISTE
  - `pipeline/audit_metrics.py`: EXISTE
- **H-A10**:
  - `reproc-ab-h8.yml`: EXISTE (resuelto en `.github/workflows/_archive/reproc-ab-h8.yml`)
  - `reproc-ab-lbg-global.yml`: EXISTE (resuelto en `.github/workflows/_archive/reproc-ab-lbg-global.yml`)
  - `reproc-no-bt-path-15d.yml`: EXISTE (resuelto en `.github/workflows/_archive/reproc-no-bt-path-15d.yml`)
  - `experiments/`: EXISTE
- **H-23**:
  - `87_results.md`: EXISTE (resuelto en `experiments/87_results.md`)
  - `_archive/reproc-s46-coppola-literal-ab.yml`: EXISTE (resuelto en `.github/workflows/_archive/reproc-s46-coppola-literal-ab.yml`)
  - `experiments/87_audit_s46_round1.py`: EXISTE
- **H-A02**:
  - `experiments/87_results.md`: EXISTE
- **H-27**:
  - `experiments/100_aggregation_strategies_offline.py`: EXISTE
- **H-26**:
  - `experiments/101_background_variants_offline.py`: EXISTE
- **H-A03**:
  - `reproc-ab-chaiten.yml`: EXISTE (resuelto en `.github/workflows/_archive/reproc-ab-chaiten.yml`)
  - `reproc-ab-pcc-kernel.yml`: EXISTE (resuelto en `.github/workflows/_archive/reproc-ab-pcc-kernel.yml`)
  - `experiments/`: EXISTE
- **H-24**:
  - `_archive/reproc-ab-lastarria-tupungatito.yml`: EXISTE (resuelto en `.github/workflows/_archive/reproc-ab-lastarria-tupungatito.yml`)
- **H-22**:
  - `_v1.yaml`: NO_ENCONTRADO
  - `experiments/`: EXISTE
- **H-29**:
  - `_v1.yaml`: NO_ENCONTRADO
- **H-41**:
  - `tasks/backlog_s93_pipeline_diffuse_field_gate.md`: EXISTE
- **H-21**:
  - `experiments/_s99_audit/ab_test1_audit.py`: EXISTE
- **H-A04**:
  - `experiments/_s99_audit/ab_test1_fair.py`: EXISTE
- **H-A05**:
  - `analyze_viirs_nadir_ab.py`: EXISTE (resuelto en `experiments/_s99_audit/analyze_viirs_nadir_ab.py`)
  - `experiments/_s99_audit/audit_nadir_promote_r3.py`: EXISTE
- **H-20**:
  - `_archive/reproc-s102-viirs-noctx-ab.yml`: EXISTE (resuelto en `.github/workflows/_archive/reproc-s102-viirs-noctx-ab.yml`)
  - `experiments/_s99_audit/analyze_viirs_3way.py`: EXISTE
- **H-02**:
  - `experiments/_s104_roi_probe/audit_ab_test1_nti.py`: EXISTE
- **H-03**:
  - `_archive/_test1_nti_integral.yaml`: EXISTE (resuelto en `pipeline/profiles/_archive/_test1_nti_integral.yaml`)
  - `experiments/_s104_roi_probe/audit_ab_test1_nti_v2.py`: EXISTE
  - `process_viirs.py`: EXISTE (resuelto en `pipeline/process_viirs.py`)
- **H-01**:
  - `_archive/reproc-s105-test1-nti-local-sweep.yml`: EXISTE (resuelto en `.github/workflows/_archive/reproc-s105-test1-nti-local-sweep.yml`)
  - `audit_sensor_strat.py`: EXISTE (resuelto en `experiments/_s104_roi_probe/audit_sensor_strat.py`)
  - `experiments/_s104_roi_probe/audit_local_sweep.py`: EXISTE
- **H-19**:
  - `scratchpad/probe_ctx_cluster_s117.py`: NO_ENCONTRADO
  - `experiments/_s106_fase2/`: EXISTE
- **H-A06**:
  - `_s109_modis_mag/audit_focalmag_ab.py`: EXISTE (resuelto en `experiments/_s109_modis_mag/audit_focalmag_ab.py`)
  - `experiments/_s106_fase2/`: EXISTE
- **H-18**:
  - `experiments/_s107_modis_localmag/`: EXISTE
- **H-36**:
  - `experiments/_s111_d11/`: EXISTE
- **H-17**:
  - `experiments/_s112_test1_lowmag/audit_t1lm_ab.py`: EXISTE
- **H-A07**:
  - `experiments/_s112_test1_lowmag/audit_t1lm_ab.py`: EXISTE
- **H-16**:
  - `experiments/_s118_c2ab/`: EXISTE
- **H-A09**:
  - `experiments/_s126_piso/`: EXISTE
- **H-15**:
  - `reproc-s121-d12-modis-ab.yml`: EXISTE (resuelto en `.github/workflows/reproc-s121-d12-modis-ab.yml`)
  - `experiments/_s121_d12_ab/`: EXISTE
- **H-14**:
  - `experiments/_s124_f70/`: EXISTE
- **H-13**:
  - `experiments/_s125_magnitud/02_veredicto_ab.py`: EXISTE
- **H-A08**:
  - `experiments/_s126_cloudmask/02_veredicto.py`: EXISTE
- **H-12**:
  - `experiments/_s126_corona/01_veredicto.py`: EXISTE
- **H-11**:
  - `reproc-s129-ab-fondos.yml`: EXISTE (resuelto en `.github/workflows/reproc-s129-ab-fondos.yml`)
  - `experiments/_s129_ab_fondos/`: EXISTE
- **H-28**:
  - `02_radio_de_suma.py`: EXISTE (resuelto en `experiments/_s129_suma/02_radio_de_suma.py`)
  - `experiments/_s129_suma/01_suma_vs_cluster.py`: EXISTE
- **H-10**:
  - `experiments/_s130_d18/`: EXISTE
- **H-43**:
  - `experiments/_s132/ab_distance_class_modis.json`: EXISTE
- **H-08**:
  - `experiments/_s133/analizar_ab_area.py`: EXISTE
  - `reproc-s133-area-ab.yml`: EXISTE (resuelto en `.github/workflows/reproc-s133-area-ab.yml`)
  - `resultado_ab_area.json`: EXISTE (resuelto en `experiments/_s133/resultado_ab_area.json`)
- **H-09**:
  - `experiments/_s133/analizar_ab_b22.py`: EXISTE
  - `reproc-s133-b22-ab.yml`: EXISTE (resuelto en `.github/workflows/reproc-s133-b22-ab.yml`)
  - `resultado_ab_b22.json`: EXISTE (resuelto en `experiments/_s133/resultado_ab_b22.json`)
- **H-05**:
  - `RESULTADO_FINAL.md`: EXISTE (resuelto en `experiments/_s135_ab_d1d2/RESULTADO_FINAL.md`)
  - `experiments/_s135_ab_d1d2/evaluar_ab.py`: EXISTE
  - `reproc-s135-ab-d1d2.yml`: EXISTE (resuelto en `.github/workflows/reproc-s135-ab-d1d2.yml`)
- **H-37**:
  - `experiments/_s136/FILTRO_INTENSIDAD_DESCARTADO.md`: EXISTE
  - `piso_mirova.py`: EXISTE (resuelto en `experiments/_s136/piso_mirova.py`)
- **H-38**:
  - `RESULTADO_PROBE.md`: EXISTE (resuelto en `experiments/_s136/RESULTADO_PROBE.md`)
  - `experiments/_s136/probe_3brazos.py`: EXISTE
- **H-42**:
  - `experiments/_s136/VEREDICTO_CONECTIVA.md`: EXISTE
  - `probe-s146-bateria-apendice.yml`: EXISTE (resuelto en `.github/workflows/probe-s146-bateria-apendice.yml`)
  - `experiments/_s146_bateria/`: EXISTE
- **H-07**:
  - `experiments/`: EXISTE
- **H-04**:
  - `reproc-s143-ab-d22d25.yml`: EXISTE (resuelto en `.github/workflows/reproc-s143-ab-d22d25.yml`)
  - `experiments/_s143_evaluador/`: EXISTE
- **H-06**:
  - `experiments/_s144_keep_peak_direccion/verificadores/`: EXISTE

## Cómo agregar una prueba

Este documento y su JSON gemelo (`docs/LIBRO_DE_PRUEBAS.json`) se generan corriendo `python scripts/libro_de_pruebas.py`: no se editan a mano, porque el guard `tests/test_guard_libro_de_pruebas_s146.py` falla si el JSON commiteado no coincide byte a byte con lo que el generador produce hoy.

Para agregar una prueba nueva:

1. Agregar un objeto al final de `experiments/_s146_auditoria/frente_H/hipotesis.json` (es una lista). Campos **obligatorios**: `id` (nuevo y único, ej. `H-54`), `que` (qué se probó, en lenguaje llano), `sesion_fecha`, `instrumento` (script o workflow que lo midió, con ruta: es lo que este libro comprueba contra el disco), `ventana_datos`, `veredicto_H`. Los demás campos (`config_divergente`, `veredicto_original`, `por_que`, `fuente`, `cobertura`, `profundidad`, `criterio_preregistrado`, `codigo_respecto_535`, `trabajo_que_apaga`) son opcionales para este libro, pero el frente H los usa: no borrarlos si ya existen en un objeto vecino.
2. Si la prueba toca un mecanismo del inventario (frente G) o sostiene o refuta un cierre del grafo de dependencias (frente E), citar el mismo identificador (D-número, A-número, flag `ENABLE_...`, o ruta de archivo) que ya usan `inventario.json` o `grafo.json`: el enlace lo arma este script solo, por coincidencia literal de identificador. Un enlace vacío después de agregar la prueba significa que no hay un identificador común todavía, no que el generador falló.
3. Volver a correr `python scripts/libro_de_pruebas.py` y commitear los dos archivos generados junto con el cambio al JSON de origen.

