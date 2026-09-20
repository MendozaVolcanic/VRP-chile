# Notas en curso frente B (S146). Se consolida en docs/audit_s146/FRENTE_B_CIERRES_CON_SCRIPT.md

## Control positivo D26 (MIROVA_DIVERGENCES.md:2353-2359): REDESCUBIERTO
- El cierre no cita el script por ruta (dice "S136 midio que..."), asi que un barrido por rutas NO lo encuentra
  (b00: control positivo False). Leccion de metodo: hay que seguir citas indirectas ("SNNN midio").
- experiments/_s136/que_rama_manda.py:41 lee solo diag_mu_dnti / diag_sd_dnti. Corre hoy (salida: MODIS 100 %, V375 99,9 %, V750 99,9 % cumbre).
- b01_control_d26.py agrega deti: sigma manda en cumbre V375 7,4 %, V750 16,6 %. Coincide con docs/audit_s145/DIVERGENCIAS_MENORES_VERIFICADAS.md.

## B-01 D16 (MIROVA_DIVERGENCES.md:1857-1900) "La grilla UTM NO explica el sub-reporte, CERRADA (refutada)" + "NO REABRIR"
- script 04_tabla_brazos.py CORRE y reproduce la tabla (Lascar .47/.46/.58/.58, PCC .75/.64/.64).
- MAS ESTRECHO: linea 38 filtra Sensor == VIIRS375 y linea 59 descarta 750 y MODIS; ventana 2026-06-25..08-24 (61 dias); n por volcan 1 a 40 (Copahue n=1, NdC n=2);
  grilla centrada en volcano lat/lon y no en mirova_center (D17); sin bow-tie. El titulo generaliza a "la grilla UTM".
- D16 l.1893-1894 sigue afirmando "recall 96->96, 0 de 19 eventos ancla" y docs/S124_F70_VEREDICTO.md:97-99 dice que ningun script commiteado los produce.
- Contradiccion viva: D17 (nota S130) dice que el mecanismo geometrico SI quedo probado por el angulo y que el brazo fiel es bow-tie + regrid.

## S98 ancla (MIROVA_DIVERGENCES.md:1249): tests/test_detection_anchor.py 10 tests PASAN (corrido). El guard mide funcion+config; el cableado lo verifique por grep (run_pipeline.py:234/277/324). MIDE LO QUE DICE (como guard anti-revert). Los numeros 5.76->1.25 km no los re-medi: SIN DATO.
## GAP#A guard tests/test_guard_gap_a_pool_musigma_s128.py: 5 tests PASAN. Es guard de reapertura, no cierre.
## B-02 sustrato K1 (MIROVA_DIVERGENCES.md:1341-1358; CLAUDE.md:119 "Efecto nulo hoy por falta de sustrato")
- copia del script corre: MODIS 11/12181 0,09 %, V750 28/23833 0,12 %, V375 320/24023 1,33 % (persistido: 11717/22920/23105; 1,36 %). Reproduce.
- lee n_nti_path = sum(nti_path_hot); process_modis.py:662-668 define nti_path_hot = roi & NTI>K1 & bt_mir > t_bg + NTI_BT_SANITY_K (3.0 K). O sea NO es "pixeles con NTI > -0,8" del paper, es eso Y la compuerta de 3 K (misma familia que D22).
- Para "el flag es no-op hoy": MIDE LO QUE DICE (el flag pasa justo nti_path_hot). Para "acota el alcance empirico del GAP #A contra el paper a <0,1 %" y "sustrato estructural, no repetir": MAS ESTRECHO. Tamano de la diferencia: SIN DATO (requiere granulos).

## D18 A/B S130 NO ADOPTAR (MIROVA_DIVERGENCES.md:2067-2092): veredicto_d18.py SOLO LEIDO (los brazos _s130_d18_* no estan en disco; requiere --dir con artefactos del run 33456630043). Mide 6 volcanes, 2026-05-29..08-24, sensores mezclados (no estratifica por sensor), y el texto lo dice ("los seis"). Generaliza "casi inerte en la practica" desde 6 de 11. Coherente; reproducibilidad SIN DATO.
## B-03 A85 / RESUELTO S118 (MIROVA_DIVERGENCES.md:1440-1453; CLAUDE.md A85) "0 robos en 214 noches focales"
- experiments/_s118_c2ab/analyze.py SOLO LEIDO (los artefactos no estan; escribe en docs/ y results.json, no se corre).
- l.112-123 index_by_night: UN record por noche, el de mayor n_pixels, mezclando sensores, elegido por separado en cada brazo. No es por pasada ni por sensor.
- l.148-165: n_nights suma toda noche MIROVA con record en baseline, aunque base_in sea False o el brazo no tenga record: en esas noches el robo es imposible por construccion y cuentan en el 214. Denominador efectivo: SIN DATO (results.json solo guarda n_nights y n_steal).
- l.40 OCR = data/mirova_reference/registro_vrp_ocr.csv, el CONGELADO (236 lineas contra 967 del snapshot vivo, contado hoy con wc -l).
- ventanas de 14 dias alrededor de alertas (windows.json), 5 focales. La regla A85 generaliza a "la seleccion vent-anchored es robusta".

## A81/A94 impacto neto etiqueta far (CLAUDE.md A94; experiments/_s136/impacto_neto.py): CORRE. Hoy 973 noches, 924 publica, 4 OCULTA (3 NdC, 1 Tupungatito), 45 sin nada; 95,0 -> 95,4 %. Reproduce el patron (texto: 1 noche util de 946; 94,8 a 95,2). Unidad noche declarada. Salvedad: predicado "publica" reconstruido a mano (distance_class==summit y cd<=inner), no el del dashboard con node (A97 es posterior). MIDE LO QUE DICE.
## B-04 A82 / D11 CIERRE S114 "se descarto TODO con datos ... barrido de 8 discriminantes AUC~0.5 ... FISICAMENTE IRREDUCIBLE" (MIROVA_DIVERGENCES.md:1304-1313, 1365-1370; CLAUDE.md A82)
- experiments/_s114_audit/discriminant_sweep.py CORRE hoy: POS n=72, NEG n=785; v375_coval_mag 0,888; dT 0,738; resto 0,39-0,64.
- l.69 solo MODIS. l.79-82: POS = SOLO Lascar (un volcan); NEG = lista "NEVADOS" que incluye Lastarria, Isluga, PP y PCC (no nevados) con etiqueta MIROVA = RUTINA.
- La etiqueta "artefacto A69" es "MIROVA no publico ALERTA MODIS esa noche". A54 (mismo CLAUDE.md) dice que ~46 % de lo que MIROVA no publica es calor real. El AUC mide "predecir la etiqueta MIROVA con Lascar como unico positivo", no "foco real vs artefacto topografico". Clase y volcan estan confundidos (POS = 1 volcan).
- features = escalares persistidos por record (diag_*), uno a la vez.

## A83 (CLAUDE.md A83; docs/AUDIT_S116_FOLLOWUP.md:5): respaldo = experiments/_s116_followup/c2_discriminator.json SIN SCRIPT commiteado (ls: solo 3 json; grep del nombre solo lo halla en el doc). NO CORRE (script ausente). El json declara tp_label = "ALERTA_TERMICA ... RUTINA/FP no cuentan": "artifact_rejection" = rechazo de lo NO confirmado por MIROVA. Mismo patron de etiqueta que B-04.
## A84 (CLAUDE.md:989-1000): scratchpad/probe_ctx_cluster_s117.py NO EXISTE en el repo (ls scratchpad: no existe; find sin resultados; git ls-files sin resultados). NO CORRE. La otra pata (A/B S106, spec 2026-06-11 §8) solo leida: brazo B descartado con Villarrica 884 m / Llaima 2263 m y recall Llaima 1/1; el criterio "offN -> 0" del brazo A es cierto por construccion (el ancla se fija al vent). Artefactos no locales: SIN DATO.
## D14 / Registro S127 (MIROVA_DIVERGENCES.md:1704-1765): copia de experiments/_s126_cloudmask/02_veredicto.py CORRE y reproduce (176 de 181; Villarrica n=8 0,764->0,832; Lascar n=35 0,434->0,501; NdC muestra insuficiente). "ningun volcan sale de banda" = 2 volcanes con muestra, solo VIIRS375, solo noches con alerta MIROVA, 3 de 11 volcanes, ventana 2026-06-25..08-24. El costo en sobre-publicacion (det 99->229 etc.) esta declarado en el mismo doc. MAS ESTRECHO leve.

## S143 A/B D22/D25 NO ADOPTAR (HYPOTHESIS_LOG.md:1516-1525): SOLO LEIDO (evaluar.py necesita brazos descargados). Alcance declarado: VIIRS 375, 9 volcanes, 2026-06-01..08-31. El brazo literal mejora criterio 2 (0,917->0,547) y 3 (0,773->0,945) y cae por criterio 1 con 5 perdidas que el verificador (VERIFICADOR_VEREDICTO.md H1) dice que NO son otro objeto. Reconocido en el repo (A107, CIERRE_FRENTE_KEEP_PEAK_S144 §5.2 deja reabrible). MIDE LO QUE DICE; el "no adoptar" depende de un criterio que su verificador declaro incapaz de decidir.
## D19 H1 REFUTADA (MIROVA_DIVERGENCES.md:2150-2156): refuta con UNA pasada (Villarrica 2026-07-01), asimetrico por diseno y declarado. Solo leido.
## libro de cuentas (A12, D5): copia de scripts/libro_de_cuentas.py CORRE: D5 0,73->0,741 OK; A12 Lascar 16,9 / Isluga 8,3 OK; flags_true 28 OK. b02_a12_delta_t.py: Isluga 8,3 (todos) / 8,5 (solo detecciones summit); Lascar 16,9 / 19,1. A12 corregida MIDE LO QUE DICE (t_max es de toda la escena, V375).
## A98 (874 de 877): experiments/_s139_audit/eje2/banco_noches.py SOLO LEIDO. Predicado del operador con node, controles C_TODO/C_NADA, negativos limpios, ventana 2026-01-10..09-07 declarada. MIDE LO QUE DICE. Ojo: con 0,905 de publicacion en negativos, un recall de 0,997 por noche casi no discrimina (el propio banco lo muestra).
## B-05 A99 "a igual conteo la razon es 0,995 ... no de formula ni calibracion" (CLAUDE.md A99; docs/audit_s139/MAGNITUD_DESCOMPOSICION_OSF.md:187-188)
- 04_fondo_y_test1.py CORRE hoy: igual conteo n=342 R=0,995 Fn=1,0 Fhot=1,14 Fbg=0,873. El 0,995 es PRODUCTO de dos factores opuestos de ~14 % (1,14 x 0,873); el docstring del script lo plantea ("coinciden o se compensan") y la salida dice: se compensan.
- subconjunto: solo VIIRS 375, clase 1 OSF v2.5, 343 pares de 1.499, 233 de 1 pixel, Lastarria 86 / PP 63 / Isluga 60 / PCC 47; Villarrica 8, NdC 1.
- el cierre derivado ("no hay que volver a buscar el deficit en k, en A, en la banda I04 ni en Planck") generaliza desde ahi.

## A104 (62,1 % / 87,1 %): experiments/_s142_linea_base/RESULTADOS.md HOY dice V375 antes_535 62,6 % de 358 y despues_571 86,5 % de 325 (87,1 % aparece solo en nevado estricta de 233). BLOQUE_ARRANQUE_S143.md:16 cita "87,1 % de 295". La salida persistida fue regenerada con mas datos: el numero de CLAUDE.md ya no coincide con el persistido (A90). Comparacion antes/despues es temporal (12-28 ago vs 1-17 sep), no A/B. Gravedad 1. No corri el script (baja referencia del remoto).
## B-06 D20 "despreciable (cuantificado S128)" (MIROVA_DIVERGENCES.md:2194, 2219-2222)
- No hay script S128 citado (AUDIT_S128.md:654-659 es prosa: "lo cuantifique con Planck").
- La comparacion fue contra el margen a K1 (~0,14). El umbral que gobierna MODIS segun S136 es el piso C1 = 0,003 (que_rama_manda: 100 %).
- "en el dNTI se cancela" esta argumentado, no medido. b03_d20_banda31_vs_32.py (Planck isotermo; control reproduce 0,0001 y 0,0054): para un pixel 10 K mas tibio que sus vecinos la diferencia de dNTI entre bandas es 0,0011-0,0022 (35-74 % de C1); con 15 K llega a 0,0036 (120 % de C1). Efecto en escenas reales: SIN DATO.
