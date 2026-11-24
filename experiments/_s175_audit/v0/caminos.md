# caminos.md: por dónde podría estar mal cada afirmación del frente F0

Escrito ANTES de abrir ningún archivo citado, sólo con el título, la ubicación y la gravedad de cada afirmación.
Verificador: Claude Sonnet 5.5 (claude-sonnet-5-5), sesión abierta por el orquestador; esfuerzo real declarado en VERIFICACION.md.

Caminos generales (valen para todas):
- G1. La copia local del repo (worktree) está atrasada o adelantada respecto de la base 752d348bc; hay que leer de la base (git show / instantánea en main), no del árbol de trabajo.
- G2. El número de línea citado ya driftó: la cita apunta a otra cosa en la base. Remapear por contenido.
- G3. Un script del auditor mide algo distinto de lo que su título dice (otra definición de «publica», de «cumbre», de «protegida»).
- G4. El script del auditor no corre o da otra salida hoy: eso ya es resultado.
- G5. La salida citada es de otra ventana temporal que la declarada, o el denominador se movió (A90).
- G6. La gravedad está inflada o rebajada respecto de la decisión de alerta que realmente tuerce.

Por afirmación:

101 (cumbres de VIIRS 750 en 0,0 MW sin camino, D25 no adoptada)
- 101a. El filtro «cúmulo de cumbre en 0,0 MW» incluye cúmulos que el tablero sí publica por otra ruta (f5_core_vrp_mw, vrp_mir_mw), así que no es «no publica».
- 101b. «MIROVA 0,36 MW» del ejemplo de Láscar es de otro canal (OCR o tabla) o de otra pasada que la nuestra; el pareo pasa por TOL_S y no por el mismo instante.
- 101c. La fracción 19 % depende de la ventana y del denominador; con otra ventana puede ser 5 % o 40 %.
- 101d. D25 no adoptada: la cita «D25 tal como está NO SE ADOPTA» puede ser de otra versión de D25 (hay A/B posteriores) y el estado vigente cambió; o «sin camino» es falso porque otra divergencia (D32, K) ya cubre el caso.
- 101e. «Ninguna protegida» depende de usar umbral 1 MW y de D-9; con la lectura A quizá alguna sí lo es.
- 101f. Los 0,0 son artefacto de que el cúmulo de cumbre se descartó por un tope (D9) y no un 0 real.

102 (D32: publicamos el cúmulo, MIROVA suma píxeles)
- 102a. El encabezado D32 ya no dice ABIERTA en la base (cambió de estado después de S147); la cita es de un commit viejo.
- 102b. La cita de la línea 3284 es de un archivo en otra rama, no de la base.
- 102c. La gravedad 4 no está re-medida: heredada. Hay que ver si hay medición posterior que la baje (p. ej. la rebaja de A10).
- 102d. «No es la palanca del 0,7» puede contradecir otra afirmación (p. ej. 104, K1 y el tope D9).

103 (C-10 / Decisión 6: veto de D18 colgando de una alerta MODIS de Láscar de 1,00 MW)
- 103a. La fila de latest_consolidado.csv l. 37438 no es la de Láscar MODIS 2026-03-27 07:10 en la base (el archivo cambió, la línea driftó), o el valor es 1,0 por redondeo (0,95 a 1,04) y no «exactamente».
- 103b. El umbral «protegida ≥ 1 MW» se evalúa con >= y con el valor sin redondear; con 1.0 exacto cuenta, pero si el valor real del banco es otro (OCR vs tabla) cambia.
- 103c. C-10 puede estar cerrado en COLA_CAMPO.md en la base (el auditor lee una copia previa), o el estado «abierto» se refiere a otra cosa.
- 103d. La cita de LOOP_OBJETIVOS.md l. 522 es de loop/activo en 395af8034 y esa línea no dice lo citado (drift).
- 103e. El record data/mirova_equivalent/Lascar.json puede no existir o el pareo puede no usar esa alerta (pasada sin nuestra).
- 103f. Que D18 «cuelgue» de esa alerta puede ser falso: el veto de D18 podría tener otra base además de ésta.

104 (K1 -0,8 y tope D9 acoplado a K1)
- 104a. Las líneas 1040 a 1045 de process_viirs_mod.py y 1472 a 1477 de process_viirs.py ya no tienen esa expresión (drift) o la condición `n_nti_path == 0` no es lo que acopla a K1.
- 104b. `nti_k1_night: -0.8` en el YAML no es el valor efectivo: el procesador lo sobreescribe o lo lee otro perfil (VRP_PROFILE), o K1 de VIIRS 750 viene de otra constante (-0,7 según el código MIROVA).
- 104c. «Acoplado» puede ser cierto sólo para una de las dos rutas (750 vs 375).
- 104d. El ejemplo de Nevados de Chillán VIIRS_SNPP_750 2026-10-01 06:00 UTC no muestra el efecto.
- 104e. Decisión 9 / V0b-01 / C-07 podrían estar cerradas por un PR posterior no incluido en la copia del auditor.

105 (C-09: fila OCR de Lastarria 2026-04-18 cuenta como protegida)
- 105a. La línea 931 del CSV OCR de la base no es esa fila (drift) o la clase `ambiguo` hace que etiquetar() la excluya de «protegida», así que no cuenta.
- 105b. D-9 ya trata las OCR de VIIRS 375 con distancia ambigua como no protegidas.
- 105c. Que la tabla tenga esa pasada como RUTINA 750 con 0,0 es otro canal; el banco usa el consolidado, no el OCR, para las protegidas.
- 105d. Que la fila entre a un A/B de VIIRS 375 depende de si el pareo cae dentro de TOL_S.
- 105e. «distancia entre 1,56 y 20,04 km» puede ser lectura de columnas desplazadas del CSV.

106 (V2-09: umbrales de cumbre hasta inner_radius vs caja 7×7)
- 106a. `ENABLE_ROI1_BOX_PAPER` en la línea 610 tiene otro default o el perfil lo enciende; el valor efectivo se lee con el perfil, no del código.
- 106b. El flag existe pero sólo vale para algunos procesadores (MODIS no); el defecto afecta a VIIRS pero no a MODIS.
- 106c. La caja de 7×7 de MIROVA es de la literatura/código; hay que ver que sea 7×7 y no otra (paper vs código OSF).
- 106d. El mismo flag lo mide S160/#918 «NO CUMPLE (veto)»: apagado deliberado, no un defecto abierto. CLAUDE.md A118 lo dice. Entonces «abierto» puede ser malinterpretación.
- 106e. Los inner_radius 3 a 20 km (tabla del CLAUDE.md) no coinciden con el volcanoes.yaml efectivo.

107 (rotación de EARTHDATA_TOKEN antes del 2026-11-27)
- 107a. La línea 28 del REGISTRO_CREDENCIALES.md cambió desde la cita; vencimiento distinto.
- 107b. El secret en GitHub tiene fecha updated_at distinta de la del insumo (se rotó después del insumo de hace horas).
- 107c. El vencimiento a 50 días se cuenta desde la emisión del token, no desde la fecha de update del secret: 2026-10-08 + 60 días = 2026-12-07, lo que sugiere 60 días y no 50 (CLAUDE.md dice 50). Chequear aritmética.
- 107d. DIAS_AVISO=10 en token_edad.py l. 27 puede no ser la semántica (aviso a 10 días antes del vencimiento) y la «rotar antes de 27-nov» ser coherente (vence 7-dic menos 10).
- 107e. Es una fecha futura, no un defecto: puede no ser un hallazgo.

109 (49 pasadas MODIS nocturnas que MIROVA lista y nosotros no bajamos)
- 109a. La lista de pasadas de MIROVA incluye pasadas diurnas o de latitud/ventana que MODIS no cubre sobre el volcán: «nocturna» mal acotada.
- 109b. «Nunca bajamos» ignora pasadas que sí tenemos con otro nombre de satélite (Terra/Aqua mal mapeado), con tolerancia de tiempo distinta.
- 109c. La fuente (png_index.csv, tif_index.csv, consolidado) no es la referencia vigente en la base; incluye filas posteriores.
- 109d. Las 49 incluyen duplicados (misma pasada contada por volcán y por canal).
- 109e. La ventana desde 2026-09-14 coincide con cambio de régimen (#535, TIF congelados desde 2026-09-22): las pasadas «de MIROVA» tras el 22-sep pueden venir de un TIF congelado, no de pasadas reales.
- 109f. El ejemplo Lascar MODIS 2026-09-28 01:30 UTC puede estar en data/mirova_equivalent (la bajamos y descartamos por nube/geometría).

110 (noches_sin_datos y recall ciegos a un satélite callado)
- 110a. Las líneas 363 a 380 de auto_audit_weekly.py cambiaron: el conteo `sin_datos` ya mira otra clave.
- 110b. El vigilante por plataforma a 72 h cubre el caso y el «ciego» es sólo del recall (ya declarado por el diseño).
- 110c. «Mide por sensor y noche con alerta»: si la noche no tiene alerta de MIROVA, nada que perder en recall, así que no es ciego sino por construcción.
- 110d. Las secciones 5 y 6 del script del auditor simulan el fallo con datos sintéticos que no son los reales.

113 (V3-02: medidor de cadencia ignora el disparador externo)
- 113a. Línea 69 de medir_cadencia_cron.py: la expresión es de otro bloque o el filtro `event != "schedule"` se aplica a otra cosa (p. ej. cuenta workflow_dispatch aparte).
- 113b. El «12,8 de las 16 corridas» viene de runs_nrt.json de hace horas; el valor con otra ventana cambia.
- 113c. cadencia.json lo lee alguien más (otro workflow, script o test) que `grep` por nombre no ve.
- 113d. El disparador externo (cron-job.org) llega como `workflow_dispatch` o `repository_dispatch`; el medidor puede contarlos en otra rama.

114 (hallazgos.csv no entran a git por .gitignore:40 *.csv)
- 114a. Línea 40 de .gitignore no es `*.csv` en la base; hay un `!` de excepción posterior que reincluye experiments/**.csv.
- 114b. `git check-ignore` lo marca porque el archivo existe en disco, pero versiones previas se forzaron con `git add -f` (hay más de 1 en la historia, el ls-tree en la base sólo ve 1 por la ruta usada).
- 114c. Los hallazgos.csv de S160 están en otro nombre o carpeta (no `_s1*_audit*`), así que «ya no existen» es falso.
- 114d. El último commit de la rama (ff34b782d) dice que fueron forzados, o sea que el hallazgo se resolvió después de la medición.
- 114e. «V2-13 no se puede clasificar» depende de lo que contenía el CSV viejo; no verificable sin él.

115 (166: RECALL_MIN calibrado sobre C0 juzga a K y la vía)
- 115a. La línea 120 de auto_audit_weekly.py cambió, o las bandas se leen de otro lado en producción (YAML).
- 115b. Las bandas 93,4 / 79,5 / 95,0 pueden haberse recalibrado en un PR posterior a S160; «C0» puede no ser la referencia de esas bandas.
- 115c. Las bandas son pisos de alarma, no juicios sobre el detector; que estén calibradas sobre C0 es deliberado y el hallazgo es de diseño.
- 115d. Las alertas #915/#936 abiertas hoy («fuera de banda») pueden ser justo el síntoma: relevancia para la gravedad.

Caminos que valen para el método del auditor (se comprueban al re-correr sus scripts):
- M1. El script usa la definición de «publica» reconstruida a mano y no el predicado del tablero con node (A97).
- M2. El script no tiene control positivo ni muestra que puede dar ≠ 0 (pregunta 1 del instrumento).
- M3. El script no distingue «no hay» de «no medí» (pregunta 2).
- M4. El script lee archivos del árbol de trabajo en vez de la base 752d348bc.

---
sha256 del contenido anterior a este pie: e312188e090dd5a86b000fb06aace01e267ba11fa4578c457f54e276ac55422b
Hora del servidor (GitHub Date): Sat, 07 Nov 2026 16:40:59 GMT
No se vuelve a editar.
