# Frente H (S146): lo que creemos haber probado y no probamos

> Auditoría de sólo lectura, 2026-09-20 (hora del servidor al empezar: 11:34 UTC). No se modificó
> ningún archivo existente, no se corrió pytest, no se re-ejecutó ningún A/B ni se bajó nada. Se
> crearon sólo este informe y los archivos de `experiments/_s146_auditoria/frente_H/`
> (`tabla.py` es la fuente única de la tabla y de `hipotesis.json`; `extraer_workflows.py` produce
> `workflows_ab.json`). Cada afirmación lleva la línea que abrí en esta sesión. Lo no verificado se
> marca SOSPECHA o SIN DATO. La columna "prof." dice hasta dónde llegué en cada fila: **A** abrí el
> instrumento (script, workflow o perfil), **B** leí el documento que declara el veredicto, **C**
> sólo la entrada de `docs/HYPOTHESIS_LOG.md` o la regla de `CLAUDE.md`.

## 0. Lo que cambia la lectura de todo lo demás: cuatro hechos de fecha

Antes de la tabla, cuatro hechos que fijé con `git` y que deciden el veredicto de casi todas las filas.

1. **La máscara de nube de 260 K no era del perfil, estaba escrita a mano en el código, y sólo en
   VIIRS 375.** `git log -S"260.0" -- pipeline/process_viirs.py` da dos commits: `a6e9a6ee4`
   (2026-04-05, "cloud mask for VIIRS 375m") y `1888c1e3e` (2026-08-28 19:00 -0400, #535). El diff de
   #535 quita `CLOUD_BT_THRESHOLD = 260.0` y pone `CLOUD_MASK_BT_K`, con el comentario "este sensor
   ignoraba `cloud_mask_bt_k` mientras MODIS sí la leía". `process_viirs_mod.py` no tiene ninguna
   máscara (grep de `CLOUD` da cero). Consecuencia: **todo A/B de VIIRS 375 corrido entre el 5 de
   abril y el 28 de agosto de 2026 corrió con la máscara puesta, dijera lo que dijera su perfil**
   (los perfiles que abrí, `_s126_corona_on`, `_s129_ab_control` y `_s130_d18_caja`, dicen `cloud_mask_bt_k: 0.0`; el comentario de `_s125_cloudmask_on.yaml:8-9` dice que el operacional ya lo fijaba en 0). Los A/B de MODIS y de VIIRS 750 no
   están afectados por este cambio.
2. **El régimen lo fija el código que procesa, no la fecha del gránulo.** El propio proyecto lo dejó
   escrito en `experiments/_s136/RESULTADO_PROBE.md:14-19` y lo midió (producción contra reproceso
   del mismo gránulo con código distinto: difieren 11 de 16). Por eso la columna que importa en la
   tabla es "código respecto de #535", no la ventana de los datos. Con eso **corrijo al hallazgo A-13
   del frente A en un punto**: el A/B de D18 (ventana 2026-05-29 a 08-24) NO corrió en el régimen
   viejo. Su flag se mergeó el 2026-08-31 (`d6d9b8e05`), tres días después de #535, así que reprocesó
   datos de invierno con la máscara ya apagada. Lo mismo vale para la corona (S127), los fondos
   (S129), el área y la banda 22 (S133), S135 y S143. F70 (datos commiteados el 2026-08-27) y el
   piloto de magnitud de S125 (2026-08-28 15:06 UTC, ocho horas antes de #535) sí corrieron con la
   máscara.
3. **La detección contextual contra la que se adoptó el Test 1 integrado ya no existe.** El Test 1
   entró al operacional el 2026-05-01 (`d6e64dc0b`, S29). El primer pase de los Tests 2 y 3 más el
   segundo pase entraron el 2026-05-16 (`3d25ea16e`, S46), y desde entonces los caminos viejos "se
   calcularon arriba (diag) pero no contribuyen" (`pipeline/process_viirs.py:1235-1237`, blame
   `958a7a189`, 2026-05-15). El "+30 puntos de recall" de S27 se midió contra una detección que dos
   semanas después fue reemplazada.
4. **El área con sec³ duró hasta el 2026-06-05 en MODIS (#354) y hasta el 2026-06-07/08 en VIIRS
   (#368, #373).** Todo lo de magnitud anterior a esas fechas (el kernel de fondo por volcán, el
   Tupungatito de A19, el barrido de S46) se midió con un área que multiplicaba por 1 a 5 fuera del
   nadir.

## 1. Cobertura, primero

| fuente | cómo | lo que NO cubrí |
|---|---|---|
| `docs/HYPOTHESIS_LOG.md` (1.567 líneas, 67 encabezados `## H`, de los cuales 1 es la plantilla: **66 entradas**) | **entero**, en tres tramos | nada. Las 66 están mapeadas a una fila o a "confirmada, fuera del censo" en el apéndice A |
| `docs/AUDIT_S146.md`, `docs/PLAN_PARIDAD_POST_AUDITORIA_S146.md`, `docs/audit_s146/FASE1_SUSTRATO_SOBREPUBLICACION.md` | enteros | |
| `docs/MIROVA_DIVERGENCES.md` (2.834 líneas) | **por tramos**: todos los encabezados, y las secciones D9 (222-300, 579-648), S33 (733-770), H_S27_1 y S28/S29 (784-935), D10/S103 (1365-1400), D11 (1420-1460), D14 (1829-1900), más un barrido de "NO ADOPTAR, REFUTAD, descartad, empeora" sobre todo el archivo | el cuerpo de D12, D13, D15 a D31 más allá de los encabezados y de lo que otros frentes ya citan |
| `docs/MISSION.md` (262 líneas) | líneas 60 a 262 (la puerta, los anti-patrones, las hipótesis abiertas de S27) | 1 a 59 |
| `CLAUDE.md`, reglas A | las tenía cargadas enteras como instrucciones de la sesión | |
| Workflows de A/B y probe | **los 93** (72 de `_archive/` más 21 vivos con `reproc` o `probe` en el nombre), por script: fechas, volcanes, sensores y fecha de alta en `workflows_ab.json` | sólo abrí a mano el de S105; el resto es extracción automática de texto, y las fechas pueden incluir la del comentario de cabecera |
| Perfiles de `pipeline/profiles/` (73) y `_archive/` (89) | listados; abrí los de la máscara de nube; leí el perfil efectivo con `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile"` (28 flags en True) | no abrí el resto uno por uno |
| Informes de A/B | leí el veredicto y la ventana de: S99, S100, S102, S103, S108, S109, S112, S118, S121, S124 (F70, Villarrica, selección de cúmulo), S125, S126 (máscara, piso), S127, S129 (suma, radio), S130 (fondos, D18, gradiente), S131, S132 (los dos), S133 (área, B22), S135, S136 (puerta, probe, filtro de intensidad, sustrato) | `AUDIT_S105/S106/S110/S111/S114/S116/S119/S122/S123/S125_PROFUNDA/S127/S128/S131/S134/S138` no los abrí: uso lo que `CLAUDE.md`, el catálogo y `AUDIT_S146.md` citan de ellos |
| Scripts de medición | **abrí** `experiments/_s104_roi_probe/audit_local_sweep.py` y `experiments/87_audit_s46_round1.py`; comprobé que existen otros 32 citados (lista en la sección 3) | no corrí ninguno |
| `tasks/backlog_*.md` (5) | `backlog_s27`, `backlog_s115`, `backlog_s93` por encabezados y líneas clave | `backlog_data_integrity_session`, `backlog_s32` (son de esquema y de datos, no de detección) |
| `docs/audit_s146/FRENTE_F_FIDELIDAD_VIIRS.md` | lo encontré al final: leí la lista de hallazgos y F-01, F-02, F-07 | el resto. Lo cruzo en la sección 5 para no duplicar |
| Bloques de arranque y notas de cierre de `tasks/` | **no cubiertos**, salvo por un `grep` de "nunca se corrió / probó / midió" sobre `docs/`, `CLAUDE.md` y `tasks/` | es el hueco más grande de este frente para "ideas anotadas y abandonadas" |

**La tabla tiene 53 filas**: 43 de cosas descartadas, refutadas o nunca medidas y 10 de adopciones.
No es el universo: los A/B de mayo (S38 a S44, S72 a S73) están agrupados en dos filas (H-29 y H-A10)
con sólo existencia y ventana verificadas, y lo digo en la fila.

## 2. La tabla

Códigos de la columna de configuración: **M260** máscara de 260 K cableada (sólo VIIRS 375, 5 de
abril a 28 de agosto); **PRE46** máscara de píxeles armada con los caminos viejos (antes del 16 de
mayo); **G3K** compuerta `bt > t_bg + 3 K` (D22); **B21** banda 21 primaria en MODIS (D21); **SEC3**
área con sec³; **T1** Test 1 integrado activo (D30); **ANILLO** fondo por mediana de anillo (D25);
**PISO** pisos VRP; **C2G** cercas intra-radio activas; **ANCLA_TUP** ancla de Tupungatito en el
centro de caja del KMZ y no en el cráter. Veredicto H: **SIGUE** sigue valiendo; **CONFIG** vale
sólo bajo su configuración o su criterio; **PERDIDO** instrumento perdido; **NUNCA** nunca se midió;
**OBSOLETA** el mecanismo medido ya no existe en el código.

| ID | qué se probó (fenómeno) | sesión y fecha | instrumento | ventana de los datos | código respecto de #535 | sensores y volcanes | config. de entonces hoy divergente | métrica y unidad | criterio antes de ver | veredicto original | veredicto H | prof. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H-01 | Test 1 con fondo LOCAL sobre NTI: medir el exceso de la cumbre contra sus vecinos inmediatos y en el indice MIR/TIR, para que el valle tibio bajo un cono nevado no cuente como calor (A69) | S105/S106, 2026-06-10 | experiments/_s104_roi_probe/audit_local_sweep.py y audit_sensor_strat.py (existen); workflow _archive/reproc-s105-test1-nti-local-sweep.yml; perfiles _archive/_test1_nti_local{,_ks20,_ks25}.yaml; flag ENABLE_TEST1_LOCAL_BG_NTI sigue en el codigo, apagado | 2026-01-29 a 2026-06-08 | ANTES | VIIRS 375; Tupungatito, Villarrica, Llaima, Lascar, Lastarria (5 de 11). Generalizado a 'el sesgo no es separable a escala local' para todos | M260, G3K, T1, ANILLO, C2G; SEC3 hasta el 7 de junio | corrimiento al norte en metros (mediana), conteo de RECORDS con Test 1 disparado, y 'recall' por noche definido como 'existe algun record VIIRS 375 ese dia' (audit_local_sweep.py:70-71), sin exigir deteccion ni publicacion. Sin negativos limpios, sin predicado del dashboard, sin nulo | SI (design 2026-06-10 par. 12, antes de correr) | REFUTADO en todo el barrido k=2,0/2,5/3,0: 'el Test 1 se apaga en noches ALERTA' (Tupungatito 59/75, Villarrica 3/11 a k=2,0) | **CONFIG** | A |
| H-02 | Co-validacion por pixel en NTI del Test 1: exigir que cada pixel del disco tenga firma propia en el indice | S104, 2026-06-09 | experiments/_s104_roi_probe/audit_ab_test1_nti.py (existe); run 27186289487; perfiles _archive/_test1_nti_covalidation_{enabled,disabled}.yaml | 2026-01-29 a 2026-06-08 (segun el yml) | ANTES | VIIRS 375, 5 volcanes | M260, G3K, T1, ANILLO, C2G | si el Test 1 sigue disparando; posicion | design 2026-06-09 | REFUTADO: 'apaga el Test 1' (la senal difusa no tiene firma por pixel) | **CONFIG** | B |
| H-03 | Test 1 que integra NTI (y no radiancia MIR absoluta) con fondo de anillo | S104/S105, 2026-06-09 | experiments/_s104_roi_probe/audit_ab_test1_nti_v2.py (existe); run 27223821692; perfil _archive/_test1_nti_integral.yaml; flag ENABLE_TEST1_NTI_INTEGRAL apagado, rama solo en process_viirs.py | 2026-01-29 a 2026-06-08 | ANTES | VIIRS 375, 5 volcanes | M260, G3K, ANILLO, C2G | metros de corrimiento al norte; controles de recall y magnitud 'sin cambio' | SI | REFUTADO por insuficiente: corrige 50 m de 1000 a 1500 m; 'inocuo' | **CONFIG** | B |
| H-04 | Quitar la compuerta de 3 K (D22) y el fondo de anillo (D25) en VIIRS 375, brazo literal con 5 ablaciones | S143, 2026-09-17/19 | experiments/_s143_evaluador/ (existe), workflow reproc-s143-ab-d22d25.yml, perfiles _s142_ab_*.yaml | 2026-06-01 a 2026-08-31 | DESPUES (datos de invierno reprocesados con codigo posterior a #535) | VIIRS 375, 9 volcanes. No dice nada de V750 ni MODIS (declarado) | B21 no aplica; T1 activo en todos los brazos | pasadas en negativo limpio, noches para recall, razon de magnitud; con verificador y linea base | SI, v2 con verificador antes de correr | NO ADOPTAR: ningun brazo cumple los tres | **SIGUE** | C |
| H-05 | Apagar keep_peak y/o condicionar el segundo pase (D19), 5 brazos | S135, 2026-09-07 | experiments/_s135_ab_d1d2/evaluar_ab.py y RESULTADO_FINAL.md (existen); workflow reproc-s135-ab-d1d2.yml; perfiles _s135_ab_*.yaml | 2026-06-01 a 2026-08-31 | DESPUES | VIIRS 375, 6 volcanes (Isluga, Lascar, Lastarria, PCC, Planchon-Peteroa, Tupungatito). Sin nevados del sur | G3K, T1, ANILLO | noches confirmadas perdidas (260), % de artefacto quitado, paridad AGREGADA (mediana unica de los 6 volcanes) | SI | NO ADOPTAR: el brazo B (sin keep_peak) pierde 0 noches y quita 100 % del artefacto, pero falla el criterio 3 por 0,692 contra 0,708 | **CONFIG** | B |
| H-06 | Medir con direccion (GeoTIFF UTM de MIROVA) si el cumulo lejano que publica keep_peak es el objeto de MIROVA | S144, 2026-09-19 | experiments/_s144_keep_peak_direccion/verificadores/ (existe) | estratos ajenos a la muestra | DESPUES | VIIRS 375; el fenomeno es de Lastarria (12 de 15 pasadas) |  | contraste de campo con nulos medidos | SI, siete versiones | CERRADO sin correr la medida (habria dado INCONCLUSO 90 % de las veces) | **NUNCA** | C |
| H-07 | Probe de vecinos tibios v1 y v2: en que etapa se pierden los vecinos del foco que MIROVA suma | S141/S142, 2026-09-15 | experiments/_s141_fase1_probe{,_v2}/ (existen), runs 34929024703 y 34967596160 | pasadas OSF 2025 reprocesadas con codigo de hoy | DESPUES | VIIRS 375; estrato nevado sin muestra | G3K, ANILLO | fraccion de vecinos por test limitante, por volcan, con controles C1 a C4 | SI | v1 INDETERMINADO; v2 HETEROGENEO en focal, INDETERMINADO en nevado | **SIGUE** | C |
| H-08 | Area de pixel geolocalizada (en vez de nadir fijo) para corregir el gradiente cenital de la magnitud | S133, 2026-09-05 | experiments/_s133/analizar_ab_area.py, resultado_ab_area.json (existen); workflow reproc-s133-area-ab.yml | chunk 1: 2026-04-01 a 2026-05-31 (el yml llega a 08-31) | DESPUES | VIIRS 375, 8 volcanes, 643 pares por pasada | G3K, T1, ANILLO | razon de magnitud por bin de cenit, sobre pares donde MIROVA publico | SI | NO ADOPTAR: invierte el signo del sesgo (veredicto declarado PARCIAL, solo chunk 1) | **CONFIG** | B |
| H-09 | Banda 22 como primaria en MODIS (D21) | S133, 2026-09-05 | experiments/_s133/analizar_ab_b22.py, resultado_ab_b22.json (existen); workflow reproc-s133-b22-ab.yml | 2026-08-01 a 2026-08-31 | DESPUES | MODIS; solo Lascar (n=61) y Villarrica (n=70), pareado por granulo | G3K, ANILLO, conectiva min | invariancia: razon ON/OFF dentro de 0,95 a 1,05 y cambio del fondo | SI | NO ADOPTAR (fallaron los dos criterios, el fondo cambio -1,2 K) | **CONFIG** | B |
| H-10 | ROI1 como caja de 5 km igual para todos (paper) en vez de circulo de 3 a 20 km por volcan (D18) | S130, 2026-08-31/09-01 | experiments/_s130_d18/ (existe); run 33456630043; perfiles _s130_d18_{caja,circulo}.yaml | 2026-05-29 a 2026-08-24 | DESPUES (flag mergeado el 2026-08-31, d6d9b8e05; perfil con cloud_mask_bt_k 0.0) | 6 volcanes, tres sensores segun el perfil | G3K, B21, T1, ANILLO | detecciones perdidas y paridad sobre records comunes (5.551); control de instrumento: 366 records cambian | SI (PREREGISTRO_AB_D18.md) | NO ADOPTAR por ausencia de beneficio | **CONFIG** | A |
| H-11 | Fondos autorreferentes (GAP A: sacar los pixeles del Test 1 por pixel del pool de mu y sigma; fondo de magnitud) | S129/S130, 2026-08-31 | experiments/_s129_ab_fondos/, _s130_ab_sustrato/ (existen); workflow reproc-s129-ab-fondos.yml | 2026-03-01 a 2026-05-28 | DESPUES | 5 volcanes | G3K, B21, conectiva min | cuatro firmas pre-registradas | SI | SIN VEREDICTO: los brazos no difieren, el mecanismo casi no tiene sustrato | **SIGUE** | B |
| H-12 | Corona Eq.6 (fondo por la corona de pixeles que rodea al cumulo), 2x2 con el filtro contextual | S126/S127, 2026-08-29/30 | experiments/_s126_corona/01_veredicto.py (existe); perfiles _s126_corona_{on,off,ctxoff}.yaml | 2026-06-25 a 2026-08-24 | DESPUES (perfiles con cloud 0.0, corridos el 29 y 30 de agosto) | VIIRS 375, 5 volcanes (Villarrica, Planchon-Peteroa, Lascar, PCC, NdC) | G3K, T1, PISO aun activo | un par por NOCHE con el maximo de ambos lados; criterio 5 = cero detecciones perdidas | SI (S126_CORONA_PREREGISTRO.md) | NO ADOPTAR: Villarrica sube 0,045 en vez de bajar; 8 detecciones perdidas de 2.179 (0,37 %) | **CONFIG** | B |
| H-13 | Brazos de magnitud A, B, C (apagar dos reducciones y encender la corona) para el sub-reporte VIIRS | S125, 2026-08-28 | experiments/_s125_magnitud/02_veredicto_ab.py (existe); perfiles _s125_mag_*.yaml | 2026-06-25 a 2026-08-24 | ANTES (datos commiteados 2026-08-28 15:06 UTC, ocho horas antes de #535) | VIIRS 375, 4 volcanes, 15 a 57 noches | M260, G3K, T1, PISO | volcanes en banda, IC bootstrap, FN nuevos; por noche | SI | NO ADOPTAR todavia: 2 de 4 criterios; la direccion era correcta en 4 de 4 | **CONFIG** | B |
| H-14 | Remuestreo a grilla UTM (F70), 4 brazos | S124, 2026-08-27/28 | experiments/_s124_f70/ (existe); perfiles _f70_{a,b}.yaml | 2026-06-25 a 2026-08-24 | ANTES | VIIRS 375, 11 volcanes; n = 1 y 2 en dos de ellos (V-04) | M260, G3K, T1, grilla mal centrada (D17), sin bow tie | mediana de 61 dias, pareado por pasada | SI (en el perfil _f70_b.yaml) | NO ADOPTAR; D16 'CERRADA, no reabrir' | **CONFIG** | B |
| H-15 | Ancla honesta en MODIS (D12): dejar de etiquetar far el foco de Lascar cuando un pixel del Salar roba el hotspot | S121, 2026-07-17 | experiments/_s121_d12_ab/ (existe el directorio; el frente B y V-09 dan los artefactos por perdidos); workflow reproc-s121-d12-modis-ab.yml | 2025-02-15 a 2026-07-17 | ANTES (no afecta: MODIS leia el perfil) | MODIS, 4 volcanes | B21, G3K, ANILLO | noches 'curadas' = cumulo dentro del inner, sin cargar ninguna referencia (V-09); destape de records path D sobre 5 MW | SI | NO ADOPTAR (destapa 131 records de artefacto) | **PERDIDO** | B |
| H-16 | Cercas intra-radio por camino (S83/S85): 'protegen al crater del robo de cumulo' | S118, 2026-06-28/07-01 | experiments/_s118_c2ab/ (existe); run 28312968093; perfiles _c2ab_*.yaml | ventanas dirigidas (el yml solo trae su fecha de alta) | ANTES | 11 Tier A, 4 brazos | M260 (en VIIRS 375), G3K, T1 | robo de cumulo en noches focales confirmadas (214); cola inflada en RECORDS | SI (A66) | REFUTADA la hipotesis; cercas a OFF (#474) | **CONFIG** | B |
| H-17 | Cuantificar el Muy Bajo de NdC con otro fondo para el Test 1 (anillos 1,5-3, 2-4, 3-5 km, NTI local, Eq.16, nucleo espacial) | S112, 2026-06-17 | experiments/_s112_test1_lowmag/audit_t1lm_ab.py (existe); run 27705248529; perfiles _archive/_t1lm_*.yaml | 2026-05-01 a 2026-06-17 | ANTES | VIIRS 375; NdC, Lascar, Lastarria; 3 ALERTAS de NdC | M260, G3K, T1 | error log de magnitud en 3 alertas e 'inflacion RUTINA' por pasada (24 en control contra 52 a 54 en los anillos) | SI, endurecido por revision adversarial | NO ADOPTAR por criterio... y ADOPTADO el mismo dia por decision (ver seccion 4, H-A07) | **CONFIG** | A |
| H-18 | Fondo local para la MAGNITUD en MODIS (huella o anillo alrededor del cumulo) | S107/S108, 2026-06-13/14 | experiments/_s107_modis_localmag/ (existe); run 27480234385; perfiles _archive/_modis_localmag_*.yaml | 2026-01-29 a 2026-06-13 | no aplica (MODIS) | MODIS, 6 volcanes | B21, G3K, ANILLO | RECORDS inflados (pc.vrp > 5 MW) que bajan a 5 o menos: 4 % y 20 % contra 85 % pre-registrado | SI (A66) | REFUTADO: mas records suben que se curan | **CONFIG** | B |
| H-19 | Ancla del cumulo en el pico de NTI (brazo B) en vez del crater; y no re-anclar ctx_cluster (A84) | S106, 2026-06-11; S117 | A/B S106: workflows _archive/reproc-s106-*.yml y experiments/_s106_fase2/ (existen). Probe S117: scratchpad/probe_ctx_cluster_s117.py NO EXISTE (B-09) | 2026-01-29 a 2026-06-11 | ANTES | VIIRS 375 y 750, 5 a 6 volcanes | M260, G3K, T1 | metros de corrimiento al norte | SI | brazo B descartado (Llaima 2263 m, peor); A84 'no reabrir' | **PERDIDO** | C |
| H-20 | 'ctxpeak es un parche redundante del sec3': A/B de 3 brazos (base, nadir+ctx, nadir sin ctx) | S102, 2026-06-06 | workflow _archive/reproc-s102-viirs-noctx-ab.yml; experiments/_s99_audit/analyze_viirs_3way.py (existe) | 2026-04-01 a 2026-06-06 | ANTES | VIIRS, 11 volcanes | M260, G3K, T1 | razon de magnitud sobre records donde MIROVA publico | SI | REFUTADA: nadir sin ctx es 2,43x peor | **CONFIG** | B |
| H-21 | Alternativas a ctxpeak para la magnitud del Test 1: filtro por pixel (41 FN), contextual puro (31 FN por crater embebido), nucleo espacial, Eq.16 | S99, 2026-06-03 | experiments/_s99_audit/ab_test1_audit.py (existe); runs 26864573601 y 26885140366; perfiles _s99_test1_*.yaml | 2026-04-01 a 2026-05-31 (S100) | ANTES | 3 volcanes (Tupungatito entre ellos), VIIRS 375 | M260, G3K, SEC3 | FN de magnitud en records (pc.vrp = 0 donde MIROVA detecto); razon mediana | parcial | descartadas; 'ctxpeak es el UNICO' | **CONFIG** | B |
| H-22 | Camino contextual en cirrus alto (D9): compuerta atmosferica por t_bg (A) y co-validacion con BT o NTI (B) | S71, 2026-05-21 | workflows _archive/reproc-ab-path-d-{atm-gate,covalidation,cap}.yml; perfiles mirova_equivalent_path_d_*_v1.yaml; experiments/127, 130, 131 (existen) | 2026-02-20 a 2026-05-20 | ANTES | 11 Tier A, tres sensores | M260, G3K, SEC3, PRE46 ya no (el primer pase habia entrado 5 dias antes) | conteo de RECORDS con vrp > 5 MW solo path D y t_bg < 260 K; 'recall 7/7' por volcan | NO consta | A y B rechazadas; C (tope de 5 MW) adoptada | **CONFIG** | A |
| H-23 | Barrido Coppola literal de 22 variantes: C2 = 3, 4, 8; C1 = 0,01; sin dual-ROI; Di Bella n = 12; drifts 1 a 7 | S46, 2026-05-15/16 | experiments/87_audit_s46_round1.py y 87_results.md (existen); workflow _archive/reproc-s46-coppola-literal-ab.yml | 2026-04-16 a 2026-05-16 | ANTES | 11 Tier A, tres sensores | M260, SEC3, ANCLA_TUP, PISO | TP/FN/FP en RECORDS; FP definido SOLO como 'detectamos cuando el scraper marca FALSO_POSITIVO' (87_audit_s46_round1.py:153, 202) | SI (reglas de decision en el design) | se adopto drift234; el resto 'sin diferencia' | **CONFIG** | A |
| H-24 | Kernel de fondo local en Tupungatito ('refuta el kernel en glaciar', A19) | S62, 2026-05-19 | workflow _archive/reproc-ab-lastarria-tupungatito.yml; run 26072884472 | 2026-03-01 a 2026-05-19 | ANTES | VIIRS 375, Tupungatito | M260, SEC3, ANCLA_TUP | razon mediana sobre records con alerta; recall 70 a 87 | NO | NO ADOPTAR: 10,37x a 18,46x | **CONFIG** | C |
| H-25 | Bajar el radio interno de PCC de 20 a 7 km | S62, 2026-05-19 | run 26072886354 | marzo a mayo 2026 | ANTES | PCC | M260, SEC3 | razon mediana | NO | revertido (3,64x, peor) | **SIGUE** | C |
| H-26 | Fondo por percentil bajo del anillo (p01 a p25) para igualar la magnitud de MIROVA | S56, 2026-05-17 | experiments/101_background_variants_offline.py (existe) | 5 casos de Villarrica | ANTES | Villarrica, VIIRS 375, n = 5 | SEC3, M260 | razon por caso, con el percentil APROXIMADO como mediana menos k sigma | NO | confirmada offline, descartada como 'probable hack' a favor del kernel local | **NUNCA** | C |
| H-27 | Cuatro estrategias de agregacion (pixel maximo, Eq.16, umbral estricto, radio de 1 km) | S55, 2026-05-17 | experiments/100_aggregation_strategies_offline.py (existe) | 5 casos de Villarrica | ANTES | Villarrica, n = 5 | SEC3, M260, ANILLO con recorte a cero | razon por caso | NO | NEGATIVA: todas dan 0 en 4 de 5 | **CONFIG** | C |
| H-28 | Sumar todos los pixeles alertados de la escena, como escribe Coppola 2019 p. 3, en vez de publicar un solo cumulo; barrido de radio uniforme | S129, 2026-08-30 | experiments/_s129_suma/01_suma_vs_cluster.py y 02_radio_de_suma.py (existen) | records de 2026 (SIN DATO si separa tramos: no abri el script) | mezcla probable | VIIRS 375, 9 volcanes con n de 5 o mas noches | G3K, T1, ANILLO con recorte, keep_peak | volcanes en banda 0,7 a 1,4; un par por noche | SI | NEGATIVO: el mejor radio uniforme (10 km) gana un volcan; 'pasa a brazo del A/B' | **NUNCA** | B |
| H-29 | Filtros de no aptos del segundo pase, retiro de los Test 1 K1, BT path encendido, sin tope | S72 a S73, mayo 2026 | workflows _archive/reproc-ab-{unsuitable-filters,unsuitable-only,test1-retire-only,bt-path-on-v1,no-cap-v1}.yml; perfiles mirova_equivalent_*_v1.yaml (existen) | 2026-02-20 a 2026-05-20 | ANTES | 11 Tier A | M260, SEC3, G3K | SIN DATO (no abri los audits) | SIN DATO | filtros de no aptos adoptados (S72); retiro K1 apagado; BT path apagado | **CONFIG** | A (solo existencia y ventana) |
| H-30 | Filtro por pixel a 5 sigma sobre el Test 1 (Phase 1), sobre la mascara final (Phase 2) y fondo global (D4) | S33, 2026-05-05 | experiments/76_audit_independent.py, pipeline/audit_metrics.py (existen); runs 25339969705, 25401379853, 25414145698 | 90 dias hasta abril 2026 | ANTES | 11 Tier A | PRE46, M260, SEC3, ANCLA_TUP | recall global en RECORDS y razon mediana | NO (se corrigio la metrica despues de ver el resultado, por un bug real) | REFUTADOS: -18,6 y -63 puntos de recall | **OBSOLETA** | B |
| H-31 | N sigma uniforme 3 contra 5 (Coppola) y 12 (Di Bella) en el umbral de temperatura de brillo | S19, 2026-04-25 | docs/DRIFTS_S17.md (existe); 6 reprocesos locales | 30 dias, abril 2026 | ANTES | 3 volcanes (Tupungatito, Chaiten, Lascar) | PRE46, M260, SEC3 | F1 en records | SI (elegir el de mayor F1) | REFUTADA: 3 sigma gana; 5 y 12 dan resultados identicos al bit por el tope de 7 K | **OBSOLETA** | C |
| H-32 | Aveni 2025 Ec. 9 (VRP por TIR) para el lago de lava de Villarrica; y k de Di Bella para VIIRS 375 | S24, 2026-04-26 | experiments/52_aveni_tir_poc.py (existe) | 6 refs de Villarrica; 37 pares de Tupungatito | ANTES | Villarrica, Tupungatito | PRE46 | razon por caso | SI | REFUTADAS | **SIGUE** | C |
| H-33 | Sigma del fondo calculado solo en el ROI de cumbre (D6) para que el glaciar no infle el umbral | S21, 2026-04-25 | experiments/41_DIAGNOSIS_FINAL_S21.md (existe) | 3 granulos | ANTES | Tupungatito, n = 3 granulos | PRE46, camino de venteo (retirado S27) | razon de sigmas (0,81 contra menos de 0,5 esperado) | SI | REFUTADA | **OBSOLETA** | C |
| H-34 | H1, H2, H3, H5, H7, H8 (S17): sigma del venteo, caja de busqueda chica, descarga sin timeout, regresion de codigo, zona horaria del scraper, referencia erronea | S16/S17, abril 2026 | commits y py-spy citados en el log | abril 2026 | ANTES | infraestructura | camino de venteo retirado | varias | en parte | REFUTADAS (la causa real era NOAA-21, H10) | **SIGUE** | C |
| H-35 | Discriminante fisico por record entre foco debil real y artefacto (barrido de candidatos, AUC 0,859) | S116, 2026-06-27 | JSON sin script (B-08) | 4.560 records summit | ANTES | tres sensores agregados | M260, B21, G3K | AUC contra la etiqueta 'MIROVA publico' | NO | A83: agotado | **PERDIDO** | C |
| H-36 | far a summit en MODIS: 8 discriminantes, N sigma de la Tabla 1, tope de magnitud (AUC 0,45), contexto temporal Method-2, ancla de primer pase | S111 a S114, junio 2026 | experiments/_s111_d11/, _s114_audit/ (existen) | abril a junio 2026 | no aplica (MODIS) | MODIS | B21, G3K, ANILLO, conectiva min | AUC y recall en records contra la etiqueta de MIROVA | en parte | A82: fisicamente irreducible, no reabrir | **CONFIG** | C |
| H-37 | Filtro por intensidad o distancia 'de Laiolo 2026' como clon literal | S136, 2026-09-08 | experiments/_s136/FILTRO_INTENSIDAD_DESCARTADO.md, piso_mirova.py (existen) | canal NRT | DESPUES | 11 Tier A |  | lectura del PDF mas minimo publicado por MIROVA | no aplica | DESCARTADO por dos vias | **SIGUE** | B |
| H-38 | Test 1 sin la interseccion contextual (tercer estado del eje: interseccion actual, contextual puro, sin interseccion) | S136, 2026-09-08 | experiments/_s136/probe_3brazos.py, RESULTADO_PROBE.md (existen); run 34274884640 | 20 pasadas | DESPUES | VIIRS 375; 3 pasadas de nevado con sustrato | G3K, ANILLO | razon de magnitud por pasada | SI | INDETERMINADO por falta de sustrato (3 pasadas utiles de nevado) | **NUNCA** | B |
| H-39 | Hipotesis abiertas de S27 que nunca se probaron: dNTI con C1 negativo, camino solo TIR (TIRVolcH), composicion de caminos en cascada contra OR | S27, 2026-04-30 | ninguno | no aplica | no aplica | no aplica |  | no aplica | no aplica | quedaron como 'hipotesis abiertas S28+' en MISSION | **NUNCA** | B |
| H-40 | Local p95 del ROI como umbral adicional (D7): agregarlo a VIIRS 375 o quitarlo de MODIS y V750 | S23, 2026-04-26 | tests/test_local_roi_paridad.py | no aplica | no aplica | tres sensores |  | no aplica | no aplica | diferida 'requiere A/B contra OSF' | **OBSOLETA** | A |
| H-41 | Compuerta de coherencia de 'campo difuso' en el pipeline (backlog S93) y supresion de cirrus en display (S90) | S90/S93, 2026-05-30 | tasks/backlog_s93_pipeline_diffuse_field_gate.md | no aplica | no aplica | MODIS sobre todo |  | no aplica | no aplica | anotada como opcional, nunca corrida | **NUNCA** | B |
| H-42 | Conectiva de los Tests 2 y 3: min (formula) contra max (prosa) | S136 a S146 | experiments/_s136/VEREDICTO_CONECTIVA.md, experiments/_s146_bateria/ (existen); workflow probe-s146-bateria-apendice.yml | 9 escenas MODIS del Apendice A (2000 a 2015) | DESPUES | MODIS, escenas del paper (no son volcanes chilenos salvo Villarrica A6) | se prueba con y sin B21 y G3K | conformes de 9 | vara de A2 re-escrita en S146 | S136: min no reproduce; S146: el mejor brazo usa max y da 9 de 9 | **SIGUE** | B |
| H-43 | A/B de distance_class en MODIS (decision 4 de AUDIT_S131) | S132, 2026-09-03 | experiments/_s132/ab_distance_class_modis.json (citado) | SIN DATO | DESPUES | MODIS | B21, G3K | cuatro criterios, fallo C2 | SI | NO ADOPTAR | **CONFIG** | B (encabezado) |
| H-A01 | ADOPCION. Test 1 integrado en el ROI: sumar el exceso MIR de todo el disco de 3 km para ver focos sub-pixel (detector propio, D30) | S27 a S29, 2026-04-30/05-01 | runs 25148058512 y reintentos; perfil _mirova_literal.yaml (existe) | 2026-01-29 a 2026-04-29 | ANTES | 11 Tier A; VIIRS 375 en S27, V750 en S28, MODIS en S29 | PRE46 (el camino contextual contra el que 'subio el recall' ya no existe), M260, SEC3, ANCLA_TUP | recall en RECORDS de alerta (507), contando como acierto 'pc.vrp > 0 O triggered_test1' (DIVERGENCES:884-885); FP contados solo como detecciones far (3.840 contra 3.500). Sin negativos limpios | NO consta | ADOPTADO: recall 50 a 80 % | **CONFIG** | B |
| H-A02 | ADOPCION. Primer pase Tests 2 y 3 mas segundo pase (drift234) | S46, 2026-05-16 | experiments/87_results.md | 2026-04-16 a 2026-05-16 | ANTES | 11 Tier A | M260, SEC3 | F1 en records; +3 TP (los 3 de MODIS), FP constante en 39 | SI | ADOPTADO por +0,7 de F1 y 'alineacion con el paper' | **CONFIG** | A |
| H-A03 | ADOPCION. Kernel de fondo local por volcan (Villarrica, Planchon-Peteroa, Lastarria, Chaiten, PCC) | S58 a S63, mayo 2026 | workflows _archive/reproc-ab-local-kernel-bg*.yml, reproc-ab-pcc-kernel.yml, reproc-ab-chaiten.yml; experiments/104, 105 (existen) | 2026-04-16 a 2026-05-15 (Villarrica); 2026-03-01 a 2026-05-19 (resto) | ANTES | VIIRS 375 sobre todo; extendido a MODIS por TDD sin A/B propio (HYPOTHESIS_LOG:1035-1040) | M260, SEC3 | razon mediana sobre records donde MIROVA alerto (Villarrica n = 2 casos comparables, luego 5); N de records summit baja 65 % | parcial | ADOPTADO por volcan | **CONFIG** | C |
| H-A04 | ADOPCION. ctxpeak (D10): intersectar el Test 1 con la mascara contextual y rescatar siempre el pixel mas caliente (keep_peak) | S100, 2026-06-04 | experiments/_s99_audit/ab_test1_fair.py (existe); run 26921561612 | 2026-04-01 a 2026-05-31 | ANTES | VIIRS 375; 272 pares, 256 en 6 volcanes; Llaima 0 pares, Villarrica 2, Copahue 1, NdC 3 | M260, SEC3, G3K | pares record a record donde MIROVA publico; recall y razon. Sin negativos | NO consta para el criterio 'justo' (se escribio tras detectar un confusor de cobertura) | ADOPTADO: 0 FN nuevos, Tupungatito 18,4x a 1,24x | **CONFIG** | A |
| H-A05 | ADOPCION. Area de pixel a nadir fijo, MODIS (S102) y VIIRS (S103) | S101 a S103, 2026-06-05/08 | experiments/_s99_audit/audit_nadir_promote_r3.py, analyze_viirs_nadir_ab.py (existen); workflows _archive/reproc-s10{1,2,3}-*.yml | 2026-01-29 a 2026-06-07 | ANTES | 11 Tier A; MODIS con n = 1 fuera de Lascar (S102_NADIR_PROMOTE_RESULTS:19-24, 42) | M260 (VIIRS 375), G3K, T1 | razon mediana global por sensor sobre records con referencia; FN a nivel record | SI (target en design 2026-06-06) | ADOPTADO: VIIRS 375 2,27x a 0,78x | **SIGUE** | B |
| H-A06 | ADOPCION. Ancla espacial honesta (VIIRS 375 S106, V750 S108) y magnitud de nucleo focal (MODIS S109, V750 S112) | S106 a S112, junio 2026 | experiments/_s106_fase2/, _s109_modis_mag/audit_focalmag_ab.py, _s112_v750focal/ (existen) | 2026-01-29 a 2026-06-17 | ANTES | 5 a 6 volcanes por A/B, resto promovido por reproceso | M260, B21, G3K | S109: 0 diferencias de deteccion en granulos comunes (1.791), control Lascar 1,000, foco preservado; C2 de cura 71 % contra 85 % pre-registrado | SI (A66) | ADOPTADOS; S109 con C2 por debajo de lo pre-registrado, reinterpretado como 'metrica de maximizar' | **CONFIG** | B |
| H-A07 | ADOPCION. Anillo intermedio de fondo para el Test 1 mas prioridad al cumulo debil (S112), por volcan (Lascar, NdC, Lastarria) | S112, 2026-06-17 | experiments/_s112_test1_lowmag/audit_t1lm_ab.py (existe); run 27705248529 | 2026-05-01 a 2026-06-17 | ANTES | VIIRS 375; 3 alertas de NdC | M260, G3K | el A/B midio inflacion en pasadas RUTINA: 24 (control) contra 54 (anillo 1,5 a 3 km) | SI, y el veredicto pre-registrado fue NO ADOPTAR | ADOPTADO contra su propio criterio, por evidencia externa (Sentinel-2 vio 6 pixeles calientes en NdC el 16 de junio) y decision de Nicolas 'recall sobre precision' | **CONFIG** | A |
| H-A08 | ADOPCION de hecho. Mascara de nube apagada (#535 la apago creyendo que era un no-op; S126 decidio no revertir) | S125/S126, 2026-08-28/29 | experiments/_s126_cloudmask/02_veredicto.py (existe); runs 33257081431 y 33257082834 | SIN DATO exacto (tres volcanes, invierno 2026) | es el cambio mismo | VIIRS 375; NdC, Villarrica, Lascar | G3K, T1, PISO | noches ciegas recuperadas (176 de 181); paridad con n = 8 y 35 | el script se escribio antes de terminar los reprocesos | SOSTENER el apagado | **CONFIG** | B |
| H-A09 | ADOPCION. Retiro de los pisos VRP (S130) y apagado de las cercas intra-radio (S118) | S118 y S130 | experiments/_s126_piso/, _s130_piso_vrp/, _s118_c2ab/ (existen) | 2026-05-01 a 2026-08-28 (piso) | el piso, DESPUES | 11 Tier A |  | piso: que suprime sobre lo visible; cercas: robo de cumulo | SI | ADOPTADOS | **SIGUE** | B |
| H-A10 | ADOPCIONES sin A/B propio leido: agrupamiento anclado al crater y filtro de distancia por pixel (S38), fondo global del Test 1 por volcan (S39), BT path apagado (S40), modo de pixel unico sub-MW (F52-B), compuerta de consistencia TIR (F46), guarda de saturacion (S73), tope de 5 MW (S71) | S38 a S77, mayo 2026 | workflows _archive/reproc-ab-d8-*.yml, reproc-ab-lbg-global.yml, reproc-ab-h8.yml, reproc-no-bt-path-15d.yml; experiments/84 a 89 (existen) | ventanas de 15 a 30 dias entre 2026-04-12 y 2026-05-11 | ANTES | 11 Tier A | M260, SEC3, ANCLA_TUP | SIN DATO (no abri los audits) | SIN DATO | ADOPTADOS | **CONFIG** | A (solo existencia y ventana) |

### Por qué, fila por fila (con fuente)

- **H-01** (CONFIG). El criterio protegia la redundancia del mismo detector que hoy sostiene 57,8 % de la sobre-publicacion de VIIRS 375 (FASE1_SUSTRATO:79). A k=2,0 el brazo bajo los disparos del Test 1 a la mitad (Tupungatito 465 a 220, Villarrica 462 a 177, Llaima 428 a 209), curo el corrimiento (1047/748/1097 m a 182/170/206 m) y el propio informe dice que 'el recall global se sostiene porque otros paths rescatan esas noches'. Nunca se midio publicacion por noche ni negativos limpios. Repetir: mismo perfil, codigo de hoy, banco de paridad S145 *Fuente: docs/superpowers/specs/2026-06-10-test1-local-bg-nti-design.md:209-245 y :254-270; audit_local_sweep.py:62-76.*
- **H-02** (CONFIG). Mismo defecto de criterio que H-01: 'apaga el Test 1' se conto como dano sin medir si la noche se sigue publicando por el camino contextual ni cuanto baja la publicacion en negativos. Hoy FASE1 mide que sin Test 1 siguen seguras 71 de 75 noches *Fuente: docs/MIROVA_DIVERGENCES.md:1429-1430.*
- **H-03** (CONFIG). Se juzgo solo por POSICION. Nunca se midio su efecto sobre la publicacion en negativos limpios, que es la pregunta de hoy. Un brazo 'inocuo' en recall y magnitud que cambia de MIR absoluto a NTI es candidato barato a re-medir *Fuente: docs/MIROVA_DIVERGENCES.md:1431-1434; CLAUDE.md A69 nota S125.*
- **H-04** (SIGUE). Es el A/B mejor instrumentado del proyecto y corrio en el regimen actual. Lo que si queda cojo es el criterio 1 (cota escalar sin acimut, A107): las 5 perdidas del literal son 4 y son coincidencias de radio. La atribucion (todo el descenso viene de apagar keep_peak; D22 y D25 empujan en contra) sigue valiendo y no hay que repetirla *Fuente: docs/HYPOTHESIS_LOG.md:1525-1538.*
- **H-05** (CONFIG). El criterio 3 es una paridad agregada que hoy se sabe defectuosa por dos lados: A100 (keep_peak daba paridad por accidente, con el pixel equivocado a ~3 km) y V-12 (el agregado compensa entre volcanes de 0,66 a 1,39). El brazo B fue rechazado por 0,016 de una metrica que premiaba el artefacto. No hay que re-correrlo: hay que re-evaluar sus salidas con criterio por volcan y negativos limpios *Fuente: experiments/_s135_ab_d1d2/RESULTADO_FINAL.md:9-25; CLAUDE.md A100; docs/AUDIT_S146.md:75.*
- **H-06** (NUNCA). La medida pre-registrada no se corrio. Lo que si se midio (nulos y controles) sigue valiendo como leccion de instrumento (A109, A110). El cierre no habilita ni prohibe apagar keep_peak *Fuente: docs/HYPOTHESIS_LOG.md:1540-1567.*
- **H-07** (SIGUE). Bien instrumentado y en el regimen actual. No justifica A/B. El hallazgo post hoc (dETI 52 de 52 en la ruta contextual, compuerta BT 18 de 18 en la del Test 1, piso C1 en los 70) queda como pista declarada, no como veredicto *Fuente: docs/HYPOTHESIS_LOG.md:1499-1523.*
- **H-08** (CONFIG). El documento del veredicto se declara parcial y no encontre en docs/ el veredicto de los chunks 2 y 3 (SIN DATO: no abri resultado_ab_area.json). Ademas el area sola no es el remuestreo (A66 rebajada): el brazo fiel, bow tie mas remuestreo centrado en get_grid_center, nunca se corrio *Fuente: docs/s133/AB_AREA_VEREDICTO_CHUNK1.md:1-10; docs/MIROVA_DIVERGENCES.md:2072, 2122.*
- **H-09** (CONFIG). El criterio era de INVARIANCIA, no de paridad: 'la paridad nunca se midio (n = 2)' (audit_s139/VERIFICADOR.md:30-32). Un mes, dos volcanes, con la compuerta puesta, y S137 mostro que banda y compuerta interactuan. Hoy la bateria del Apendice A da 9 de 9 al brazo con banda 22. No es una refutacion de D21 *Fuente: docs/s133/AB_B22_VEREDICTO.md:1-12; docs/audit_s139/VERIFICADOR.md:30-32.*
- **H-10** (CONFIG). Correccion a A-13 del frente A: este A/B NO corrio en el regimen viejo. El regimen lo fija el codigo que procesa, no la fecha del granulo (experiments/_s136/RESULTADO_PROBE.md:14-19), y el codigo es posterior a #535. Lo que si le falta es la unidad: nunca se midio publicacion en negativos limpios, y la caja manda pixeles a umbrales mas estrictos, que es la direccion que hoy interesa (la caja de PCC pasa de 20 km a 5). Re-evaluar las salidas ya generadas, sin re-correr *Fuente: docs/s130/VEREDICTO_AB_D18.md:1-14; git d6d9b8e05; pipeline/profiles/_s130_d18_caja.yaml:76.*
- **H-11** (SIGUE). La falta de sustrato se volvio a ver hoy por otra via: diag_n_nti_path > 0 en 5 de 954 pasadas V375 y 0 en el resto (FASE1_SUSTRATO:18). Ojo: vale para volcanes sin fase efusiva; con lava expuesta el sustrato aparece *Fuente: docs/s130/AB_FONDOS_SIN_SUSTRATO.md:1-14.*
- **H-12** (CONFIG). Dos defectos hoy conocidos: (1) la paridad por maximo nocturno infla 0,1 a 0,2 contra la de pasada (audit_s139/VERIFICADOR.md:28-29); (2) el criterio 5 conto como perdida 8 detecciones de 0,021 a 0,042 MW sin preguntar si eran noches que MIROVA confirma: en el regimen de hoy perder publicaciones de centesimas de MW en negativos limpios es el objetivo, no el dano. Es la misma familia que D25, que S145 implemento apagado *Fuente: docs/S127_CORONA_RESULTADO.md:26-79.*
- **H-13** (CONFIG). Corrio con la mascara de 260 K, que en invierno dejaba sin fondo pasadas enteras de Villarrica y Lascar (69 y 29 noches ciegas, S126_CLOUDMASK_RESULTADO:19-24). Muestra insuficiente declarada por el propio informe *Fuente: docs/S125_AB_MAGNITUD_RESULTADO.md:10-42; git 69c1e4c9e.*
- **H-14** (CONFIG). Ya rebajado por V-04: lo refutado fue el regrid F70, no la grilla de MIROVA. Agrego: corrio ademas con la mascara de 260 K. El propio veredicto reconoce que ningun script commiteado produce uno de sus numeros (S124_F70_VEREDICTO.md:97-99) *Fuente: docs/S124_F70_VEREDICTO.md:1-5, 52-110; docs/AUDIT_S146.md:70.*
- **H-15** (PERDIDO). V-09: el 76 exacto es NO VERIFICABLE y 'curada' no era 'MIROVA confirmo'. Con tasa base de 89,1 % de cumulo dentro del inner (V-02) la metrica no distingue actividad *Fuente: docs/AUDIT_S121_D12_AB.md:1-50; docs/AUDIT_S146.md:73.*
- **H-16** (CONFIG). Para la pregunta que se hizo (robo) sigue valiendo, con el matiz B-03 (incluye noches donde el robo es imposible). Para la pregunta de hoy NUNCA se midio: cuanto subio la publicacion en negativos limpios al apagar las cercas. El costo se conto en records inflados sobre 1,5x, no en pasadas publicadas donde MIROVA callo *Fuente: docs/AUDIT_S118_C2_GATES_AB.md:3-65; docs/HYPOTHESIS_LOG.md:9-27.*
- **H-17** (CONFIG). Unico A/B anterior a S139 que midio inflacion en noches RUTINA, y dio que el anillo intermedio la DUPLICA. Se adopto igual. Ver H-A07 *Fuente: docs/S112_TEST1_LOWMAG_AB_RESULTS.md:3-48.*
- **H-18** (CONFIG). Es la misma familia fisica que D25 (fondo por vecinos), que S138 identifico como 'la palanca real' y S145 implemento apagado en V750. La refutacion de S108 se midio con banda 21 (que S137 mostro que fabrica el primer pase MODIS) y con una metrica de records sobre 5 MW, sin referencia (MIROVA casi no publica MODIS fuera de Lascar). No refuta D25 y nadie lo ha dicho por escrito *Fuente: docs/AUDIT_S108_AB_MODIS_VEREDICTO.md:1-41.*
- **H-19** (PERDIDO). La pata S106 tiene instrumento; la pata S117 (indistinguibles en n_pixels y VRP) lo perdio. El frente A dice que A84 se reproduce igual. Es de posicion, no de publicacion: baja prioridad *Fuente: CLAUDE.md A84; docs/audit_s146/FRENTE_B_CIERRES_CON_SCRIPT.md:66, 227.*
- **H-20** (CONFIG). El propio proyecto lo dejo escrito en S136: 'ambas son previas a #535, que bajo el fondo global 6 a 8 K en nevados... hoy no tiene respaldo' (MISSION_GATE_S136:80-81). Y la metrica premiaba a keep_peak por accidente (A100) *Fuente: CLAUDE.md A66; docs/MISSION_GATE_S136_TEST1_CONTEXTUAL.md:78-84.*
- **H-21** (CONFIG). El brazo B de S135 es contextual puro y dio 0 perdidas en 260 noches con Tupungatito adentro (28 noches), en el regimen actual. Los '31 FN' de S99 eran records con magnitud cero, no noches sin publicar *Fuente: docs/MIROVA_DIVERGENCES.md:1365; docs/S99_TEST1_AB_RESULTS.md:19-54; docs/MISSION_GATE_S136_TEST1_CONTEXTUAL.md:80.*
- **H-22** (CONFIG). Reabierta hoy por V-01. Agrego una SOSPECHA de instrumento: desde el 2026-05-15 el comentario del codigo dice que los caminos legacy 'se calcularon arriba (diag) pero no contribuyen cuando ON' (process_viirs.py:1235-1237, blame 958a7a189), y la evidencia de S70 ('100 % disparan SOLO por path D') se leyo de diag_n_dnti_ctx_path el 2026-05-20. Si el contador ya era solo diagnostico, la atribucion al path D de S70/S71 no mide lo que dice. No lo verifique corriendo nada *Fuente: docs/MIROVA_DIVERGENCES.md:282-296, 579-648; pipeline/process_viirs.py:1235-1237.*
- **H-23** (CONFIG). El FP vale 39 en 18 de las 22 variantes: el instrumento era ciego a la sobre-publicacion, porque una pasada RUTINA donde publicamos no contaba como nada. Todo lo que ese barrido dice sobre C1, C2, dual-ROI o n = 12 respecto de precision es SIN DATO. Subir C2 o C1 en el ROI de cumbre nunca se midio contra negativos limpios *Fuente: experiments/87_results.md:8-31; experiments/87_audit_s46_round1.py:145-215.*
- **H-24** (CONFIG). Se midio UN DIA ANTES de descubrir que el ancla de Tupungatito apuntaba al centro de caja del KMZ y que el cumulo elegido era el flanco SE, falso (H_S64, HYPOTHESIS_LOG:259-279; corregido S65, 2026-05-20). El 18,46x es del glaciar del flanco, no del crater. A19 generaliza desde ahi a 'ring glaciar empeora con kernel'. Ademas area con sec3 y mascara de 260 K *Fuente: docs/HYPOTHESIS_LOG.md:283-307 y 259-279; CLAUDE.md A19.*
- **H-25** (SIGUE). Vale como leccion de metodo (A18). Como parametro por volcan la puerta de la mision lo rechaza igual (backlog_s115.md:5-14) *Fuente: docs/HYPOTHESIS_LOG.md:311-330.*
- **H-26** (NUNCA). Se midio con un proxy gaussiano sobre 5 casos de un volcan, y se descarto por argumento de fidelidad. No hay que retomarla: el canon dice media de vecinos, no percentil de anillo (D25) *Fuente: docs/HYPOTHESIS_LOG.md:1163-1211.*
- **H-27** (CONFIG). Operaban sobre anomaly_pixels ya recortados a cero por el fondo de anillo (el propio log lo dice). Lo refutado es 'agregar distinto arregla la magnitud con ESTE fondo'. Con fondo de vecinos (D25) nunca se probaron *Fuente: docs/HYPOTHESIS_LOG.md:1215-1247.*
- **H-28** (NUNCA). Se midio offline sobre los pixeles persistidos (tope de 100, con nuestro fondo y nuestro recorte). El brazo de reproceso que el propio documento pide nunca se corrio. No es una refutacion de la suma de escena *Fuente: docs/s129/RADIO_DE_SUMA.md:17-80.*
- **H-29** (CONFIG). Cobertura declarada, no verificada: solo confirme que los workflows y perfiles existen y su ventana. V-05 ya establecio que el filtro corre desde S72 *Fuente: experiments/_s146_auditoria/frente_H/workflows_ab.json.*
- **H-30** (OBSOLETA). La mascara sobre la que actuaban (caminos legacy) ya no es la de produccion. El recall se media como OR con triggered_test1. D4 fondo global 'refutado' aca se adopto por volcan ocho dias despues (S39, 36cf58316) *Fuente: docs/MIROVA_DIVERGENCES.md:733-768.*
- **H-31** (OBSOLETA). Dos de los tres brazos eran el mismo brazo (instrumento sin poder), y el camino de temperatura de brillo esta apagado desde S40 (2026-05-13) con sustrato cero hoy (FASE1_SUSTRATO:15-21). No apaga nada vigente *Fuente: docs/HYPOTHESIS_LOG.md:754-773.*
- **H-32** (SIGUE). Son de formula, no de deteccion ni de regimen: el k de 18,0 quedo respaldado por Coppola 2026 Tabla 1 (AUDIT_S146:158) y la Ec. 9 no es del canal NRT (H14, H16) *Fuente: docs/HYPOTHESIS_LOG.md:864-882, 1436-1451.*
- **H-33** (OBSOLETA). El camino que usaba ese umbral (venteo con tope de 3 K) se retiro en S27. Tres granulos de un volcan *Fuente: docs/HYPOTHESIS_LOG.md:681-699.*
- **H-34** (SIGUE). Son de infraestructura y de adquisicion; ningun cambio de regimen las toca. H10 (NOAA-21) esta verificado limpio por el frente A *Fuente: docs/HYPOTHESIS_LOG.md:532-643.*
- **H-35** (PERDIDO). V-03: etiqueta defectuosa, paradoja de Simpson (0,554 dentro de volcan y sensor). La puerta de la mision prohibe igual un discriminante por record contra la etiqueta de MIROVA: no retomar *Fuente: docs/AUDIT_S146.md:72.*
- **H-36** (CONFIG). Ya rebajada tres veces (S124, S138, S146 V-02). No agrego medicion. Lo que habria que repetir es la tasa base por volcan con banda 22 y sin compuerta, no los discriminantes *Fuente: CLAUDE.md A82; docs/AUDIT_S146.md:69.*
- **H-37** (SIGUE). La lectura documental la repitio el verificador de S141 (P-01). Un piso de intensidad cortaria alertas reales de 0,02 a 0,06 MW (NdC) *Fuente: experiments/_s136/FILTRO_INTENSIDAD_DESCARTADO.md:1-30; docs/MIROVA_DIVERGENCES.md:1853-1860.*
- **H-38** (NUNCA). El brazo 'nunca se corrio en este regimen' como reproceso (MISSION_GATE_S136:87-89). El probe dice que donde el filtro actua la magnitud casi se duplica (1,17 a 2,23 con n = 3): indicio, no veredicto *Fuente: experiments/_s136/SUSTRATO_RESUELVE_EL_DESENLACE.md:14-25.*
- **H-39** (NUNCA). Siguen listadas en docs/MISSION.md:231-236 sin medicion. La de composicion (cascada contra OR) es justo lo que FASE1 midio hoy por otra via: el Test 1 no entra a la mascara, compite por la fuente del cumulo *Fuente: docs/MISSION.md:229-236.*
- **H-40** (OBSOLETA). El umbral sigue en process_modis.py:614-617 pero cuelga del camino de temperatura de brillo, que esta apagado. Nunca se midio y ya no hace falta *Fuente: docs/HYPOTHESIS_LOG.md:831-841; pipeline/process_modis.py:614-617.*
- **H-41** (NUNCA). La puerta de la mision la trata como parche (A72: artefacto se arregla en la deteccion, no se esconde). Se lista por cobertura; no se propone *Fuente: tasks/backlog_s93_pipeline_diffuse_field_gate.md:1-49.*
- **H-42** (SIGUE). Es fidelidad al Apendice A y corre con el codigo de hoy. No dice nada de la sobre-publicacion en VIIRS (AUDIT_S146:118-120). Tres brazos INDECIDIBLES por no guardar posicion *Fuente: docs/AUDIT_S146.md:96-120.*
- **H-43** (CONFIG). Solo lei el encabezado. A94 y V-02 ya dicen que el frente de la etiqueta rinde una noche de 946 y que la tasa base lo vuelve indiscriminante *Fuente: docs/s132/AB_DISTANCE_CLASS_MODIS.md:1-8.*
- **H-A01** (CONFIG). La justificacion (+30 puntos de recall) se midio contra una deteccion contextual que dos semanas despues fue reemplazada por el primer pase Tests 2 y 3 mas segundo pase (S46). Hoy, en el regimen actual, sin Test 1 siguen seguras 71 de 75 noches VIIRS 375 y 0 se pierden seguro, mientras sostiene solo 186 de 322 negativos publicados (FASE1:79-88). El aporte de recall que justifico la adopcion nunca se re-midio despues de S46. Y el acierto se contaba con el disparo del propio Test 1, o sea circular *Fuente: docs/MIROVA_DIVERGENCES.md:848-935; git d6e64dc0b, 3d25ea16e.*
- **H-A02** (CONFIG). La ganancia medida son 3 records MODIS. El efecto sobre la publicacion en negativos no se pudo ver con ese instrumento (H-23). La adopcion es defendible por fidelidad, no por la medicion *Fuente: experiments/87_results.md:8-60.*
- **H-A03** (CONFIG). Tres defectos: es una conmutacion por volcan que la mision prohibe (MISSION:93-99 lo declara deuda); Villarrica se decidio con n = 2; y el -65 % de records summit en Villarrica nunca se leyo como lo que hoy importa (menos publicacion en negativos). D25 propone lo mismo uniforme. El R2 retroactivo de S70 lo valido con un caso por volcan *Fuente: docs/HYPOTHESIS_LOG.md:965-1018, 283-307, 50-80.*
- **H-A04** (CONFIG). A100 y D19 ya mostraron que keep_peak publica como summit a 0,0 km un pixel del borde del disco, mas frio que el fondo, y que la paridad salia por accidente. En S143 todo el descenso de publicacion en negativos (0,917 a 0,547) viene de apagarlo. La adopcion nunca miro negativos y los nevados del sur tenian 0 a 3 pares *Fuente: docs/S100_TEST1_FULL_AB.md:16-50; docs/HYPOTHESIS_LOG.md:1535.*
- **H-A05** (SIGUE). El cambio es de formula y esta respaldado por la calibracion S14 y por Coppola 2026 Tabla 1. Lo que NO vale es leer 0,78 como 'paridad sana': S130 midio que la razon cae de 0,740 cerca del nadir a 0,253 mas alla de 50 grados aun con nadir fijo. A67 ya anoto el efecto colateral: menos detecciones (Villarrica 636 a 602), que nunca se conto en negativos *Fuente: docs/S102_NADIR_PROMOTE_RESULTS.md:8-42; CLAUDE.md A66, A67.*
- **H-A06** (CONFIG). En MODIS no hay referencia fuera de Lascar, asi que 'curar' fue bajar records de mas de 5 MW, no acercarse a MIROVA. El plan definitivo dice que MODIS publica igual con alerta (11,5 %) que sin ella (10,2 %). No lo re-medi *Fuente: docs/AUDIT_S109_MODIS_FOCAL_VEREDICTO.md:4-41; docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md:30-36.*
- **H-A07** (CONFIG). Es la unica adopcion cuyo A/B midio la sobre-publicacion y la vio duplicarse, y aun asi entro a mirova_equivalent, gateada por volcan. Bajo la regla S143 (primero igualar, lo demas al experimental) es candidata directa a mudarse. ENABLE_TEST1_INTERMEDIATE_BG y ENABLE_TEST1_PRIORITY_WEAK_CLUSTER siguen en True (leido de pipeline.profile hoy) *Fuente: docs/S112_TEST1_LOWMAG_AB_RESULTS.md:3-48.*
- **H-A08** (CONFIG). Fiel al paper (Laiolo 2026 p. 4, verificado S128), asi que la decision es correcta por la mision. Pero el costo se midio mal para la pregunta de hoy: 'solo 21 de 286 detecciones nuevas caen en noches que MIROVA confirma' (S126_CLOUDMASK_RESULTADO:63), o sea 265 publicaciones nuevas donde MIROVA no alerto, leidas como 'cara negativa chica'. Es el origen medido del salto 62,1 a 87,1 % *Fuente: docs/S126_CLOUDMASK_RESULTADO.md:11-76.*
- **H-A09** (SIGUE). Los dos van hacia el literal. Ninguno conto cuanto sube la publicacion en negativos limpios, pero ambos quitan cosas que MIROVA no tiene. Cobertura declarada: no abri los scripts del piso *Fuente: docs/S126_PISO_VRP_ES_UN_NO_OP.md:1-14; docs/AUDIT_S118_C2_GATES_AB.md.*
- **H-A10** (CONFIG). Cobertura declarada, no verificada. Todas anteriores a nadir fijo y a #535, con ventanas de dos a cuatro semanas. El tope de 5 MW si lo verifico V-01 como funcionando *Fuente: experiments/_s146_auditoria/frente_H/workflows_ab.json; git log -S sobre mirova_equivalent.yaml.*

## 3. Los CONFIG y los PERDIDO, ordenados por cuánto trabajo apagan

Conteo por veredicto (salida de `tabla.py`): **CONFIG 30, SIGUE 10, NUNCA 6, OBSOLETA 4, PERDIDO 3**.

### 3.1 Los que más apagan

**H-01 (apaga 5). El Test 1 con fondo local sobre NTI se refutó por proteger al detector que hoy es el problema.**
Qué pasa en el volcán: en un cono nevado de noche la cumbre está a unos 272 K y el valle a unos
281 K. Cualquier método que sume "exceso de radiancia MIR sobre un anillo lejano" ve el valle tibio
como calor (A69). S105 diseñó la cura que la física pide: medir el exceso contra los vecinos
inmediatos y en el índice MIR/TIR, que atenúa la topografía. S106 la corrió con barrido de k y
predicciones escritas antes. Lo que dio, leído de `docs/superpowers/specs/2026-06-10-test1-local-bg-nti-design.md:213-219`:

| volcán | corrimiento al norte, m (anillo → k=2,0) | records con Test 1 disparado | "recall" |
|---|---|---|---|
| Tupungatito | 1047 → 182 | 465 → 220 | 75/75 → 75/75 |
| Villarrica | 748 → 170 | 462 → 177 | 8/11 → 8/11 |
| Llaima | 1097 → 206 | 428 → 209 | 1/1 → 1/1 |
| Láscar (control) | 23 → 43 | 446 → 409 | 117/127 → 117/127 |
| Lastarria (control) | 886 → 742 | 441 → 424 | 94/105 → 94/105 |

Se refutó porque "el Test 1 se apaga en noches ALERTA" (Tupungatito 59 de 75, Villarrica 3 de 11),
con el argumento de que "degradarlo en las noches reales adelgaza la redundancia" (líneas 233-238).
Tres cosas que abrí hoy cambian esa lectura:

- el "recall" de ese script **no mide detección**: `audit_local_sweep.py:70-71` cuenta una noche
  como acertada si existe cualquier record VIIRS 375 con esa fecha, haya o no detección. Es una
  medida de cobertura de gránulos, y por eso da idéntica en los cinco brazos;
- **nunca se midió la publicación por noche con el predicado del dashboard, ni los negativos
  limpios**. La única cantidad sensible que el A/B produjo es la caída de los disparos del Test 1, y
  se contó como daño;
- hoy está medido (`docs/audit_s146/FASE1_SUSTRATO_SOBREPUBLICACION.md:79-88`) que el Test 1 solo
  sostiene 186 de los 322 negativos limpios publicados en VIIRS 375 y que sin él siguen seguras 71
  de 75 noches positivas, con 0 pérdidas seguras.

Qué habría que repetir: nada nuevo de código. El flag `ENABLE_TEST1_LOCAL_BG_NTI` sigue en
`pipeline/profile.py:288` y en `pipeline/process_viirs.py:1110`, y los perfiles están en
`pipeline/profiles/_archive/_test1_nti_local{,_ks20,_ks25}.yaml`. Falta correrlo con el código de
hoy y evaluarlo con el banco de paridad de S145. SOSPECHA que no verifiqué: que el flag siga
funcionando después de tres meses de cambios alrededor.

**H-A01 (apaga 5). La adopción del Test 1 integrado se justificó con un recall que nunca se volvió a medir.**
`docs/MIROVA_DIVERGENCES.md:848-870`: recall de ~50 % a 80 % (406 de 507 records) sobre 2026-01-29 a
04-29. Tres problemas: (a) el acierto se contaba como "`pc.vrp_mw` o `triggered_test1`" (línea 887),
o sea que el disparo del propio Test 1 contaba como detección: circular; (b) los FP se contaron sólo
como detecciones `far` (3.840 contra 3.500, líneas 876-879), nunca como pasadas donde MIROVA calló;
(c) la detección contextual de abril ya no existe (hecho 3 de la sección 0). El frente que eso apaga
es exactamente la Fase 2 del plan: hoy se teme apagar el Test 1 "porque subió el recall de 50 a
80 %" (`docs/PLAN_PARIDAD_POST_AUDITORIA_S146.md:163-166`), y ese número es de otra detección.

**H-23 (apaga 5). El barrido de 22 variantes de S46 era ciego a la sobre-publicación.**
`experiments/87_audit_s46_round1.py:153` y `:202`: un FP es sólo "detectamos cuando el scraper marca
`FALSO_POSITIVO` en ese timestamp". Una pasada RUTINA donde publicamos no contaba. Resultado
(`experiments/87_results.md:8-31`): **FP = 39 en 18 de las 22 variantes** (las otras cuatro son subconjuntos por sensor o un brazo aislado: 38, 38, 26 y 0), con C2 en 3, 4 u 8, con o
sin dual-ROI, con n = 12. De ahí salió la idea, repetida después, de que "los umbrales no mueven la
precisión". No se sabe: el instrumento no podía verlo. Lo mismo vale, más suave, para todo A/B
anterior a S139: ninguno tiene negativos limpios salvo S112, que sí los midió (H-17).

**H-A04 (apaga 5). `ctxpeak` se adoptó con 272 pares donde MIROVA publicó y cero negativos.**
`docs/S100_TEST1_FULL_AB.md:16-33`: 256 de los 272 pares son de seis volcanes; Llaima 0, Copahue 1,
Villarrica 2, NdC 3. El criterio "justo" (sólo records comunes) se escribió después de detectar que
los dos brazos habían bajado gránulos distintos (líneas 8-14), así que no es pre-registrado. Lo que
pasó después ya lo sabe el proyecto (A100, D19, S143) pero la fila de la adopción no lo dice.

### 3.2 Los que apagan 4

- **H-05** (S135, brazo B sin `keep_peak`): 0 noches perdidas de 260, 100 % del artefacto quitado, y
  rechazado por paridad agregada 0,692 contra 0,708 (`experiments/_s135_ab_d1d2/RESULTADO_FINAL.md:15-25`).
  Esa paridad es la que A100 mostró accidental y V-12 mostró compensada entre volcanes.
- **H-09** (banda 22, S133): el criterio que falló era de invariancia ON/OFF, no de paridad
  (`docs/audit_s139/VERIFICADOR.md:30-32`). Dos volcanes, un mes, con la compuerta puesta.
- **H-14** (F70): ya rebajado por V-04; agrego que corrió con M260.
- **H-17 / H-A07** (S112): ver sección 4.
- **H-22** (D9, co-validación): reabierta por V-01. Mi aporte es una SOSPECHA de instrumento: la
  evidencia de S70 se leyó de `diag_n_dnti_ctx_path` cinco días después de que ese contador pasara a
  ser sólo diagnóstico (`pipeline/process_viirs.py:1235-1237`). No la verifiqué corriendo nada.

### 3.3 Los que apagan 3

H-02, H-03 (las otras dos versiones NTI del Test 1, mismo defecto de criterio que H-01), H-08 (área:
veredicto declarado parcial, chunk 1), H-10 (D18: régimen correcto, unidad equivocada), H-12 (corona:
contó como daño perder 8 detecciones de 0,021 a 0,042 MW), H-15 (D12), H-18 (fondo local de magnitud
en MODIS: misma familia que D25, medida con banda 21 y sin referencia), H-20 y H-21 (la justificación
de `ctxpeak`, que `docs/MISSION_GATE_S136_TEST1_CONTEXTUAL.md:78-84` ya declara sin respaldo), H-24
(A19 Tupungatito: medido un día antes de descubrir que el ancla apuntaba al flanco equivocado), H-36
(A82), H-A03 (kernel por volcán), H-A08 (máscara apagada).

### 3.4 Instrumentos perdidos

| fila | qué se perdió | quién lo encontró |
|---|---|---|
| H-15 | artefactos del A/B de D12; el script no carga referencia | V-09 (hoy) |
| H-19 | `scratchpad/probe_ctx_cluster_s117.py` (A84) | B-09 (hoy) |
| H-35 | script del AUC 0,859 de A83 (queda un JSON) | B-08, V-03 (hoy) |
| (D9) | el script del "207 de 214" | V-01 (hoy) |
| todos los A/B de `_archive/` | **SOSPECHA**: los artefactos de GitHub Actions de los runs de abril a junio caducan a los 90 días. Si las salidas por brazo no se commitearon a `data/` o a `experiments/`, los brazos de H-01, H-02, H-03, H-20 y H-21 no se pueden re-evaluar sin re-correr. No lo comprobé contra la API de GitHub | este frente |

Instrumentos que **sí existen** (comprobado con `ls`, no corridos): `experiments/51_p31_ab/DELTA_REPORT.md`,
`52_aveni_tir_poc.py`, `41_DIAGNOSIS_FINAL_S21.md`, `50_factor_42_clustering_test.py`,
`100_aggregation_strategies_offline.py`, `101_background_variants_offline.py`,
`98_calibrate_te_villarrica.py`, `104_s60_*.md`, `105_s61_*.py`, `120_audit_tif_vrp_sumable/`,
`122_r2_chaiten/`, `125_r2_pcc/`, `127_path_d_tbg_calibration/`, `130_r3_*/`, `131_r2_*/`,
`76_audit_independent.py`, `88_audit_s47_fps_distribution.py`, `scripts/verify_reproc.py`,
`docs/DRIFTS_S17.md`, `_s118_c2ab/`, `_s121_d12_ab/`, `_s124_f70/`, `_s125_magnitud/02_veredicto_ab.py`,
`_s126_cloudmask/02_veredicto.py`, `_s126_corona/01_veredicto.py`, `_s129_suma/02_radio_de_suma.py`,
`_s130_d18/`, `_s133/resultado_ab_b22.json`, `_s135_ab_d1d2/evaluar_ab.py`, `_s99_audit/ab_test1_fair.py`,
`_s112_test1_lowmag/audit_t1lm_ab.py`, `_s107_modis_localmag/`, `_s109_modis_mag/`, `_s111_d11/`.

## 4. Adopciones medidas con un criterio que hoy se sabe defectuoso

Perfil efectivo de hoy (`VRP_PROFILE=mirova_equivalent`, leído de `pipeline.profile`): 28 flags en
True. Cada uno es una adopción. Las que pude fechar con `git log -S` sobre `mirova_equivalent.yaml`:
Test 1 y dual-ROI BT 2026-05-01; agrupamiento anclado al cráter y filtro de distancia por píxel
2026-05-12; fondo global del Test 1 por volcán 2026-05-13; primer y segundo pase 2026-05-16; kernel
local 2026-05-18; píxel único sub-MW y compuerta TIR 2026-05-24; `ctxpeak` 2026-06-04; ancla honesta
2026-06-11; núcleo focal MODIS 2026-06-15. **Todas son anteriores a #535 y todas menos las tres
últimas son anteriores al nadir fijo.**

| fila | adopción | defecto del criterio | qué dice hoy la medición |
|---|---|---|---|
| **H-A07** | anillo intermedio y prioridad al cúmulo débil (S112), por volcán | **se adoptó contra su propio pre-registro.** El A/B midió inflación en pasadas RUTINA y dio 24 (control) contra 54 (`docs/S112_TEST1_LOWMAG_AB_RESULTS.md:37-48`). Se adoptó el mismo día por evidencia externa (Sentinel-2) y "recall sobre precisión" (líneas 3-16) | es la única adopción cuyo A/B vio duplicarse la sobre-publicación. Sigue en True. Bajo la regla S143 es candidata directa a mudarse al perfil experimental. Está gateada por volcán, que la misión prohíbe |
| **H-A01** | Test 1 integrado | acierto circular (contaba su propio disparo), FP sólo `far`, detección de abril ya reemplazada | sin él siguen seguras 71 de 75 noches (FASE1) |
| **H-A04** | `ctxpeak` / `keep_peak` | sólo positivos; nevados con 0 a 3 pares; criterio escrito tras ver un confusor | A100, D19, S143: toda la baja de publicación en negativos viene de apagarlo |
| **H-A08** | máscara apagada | "21 de 286 detecciones nuevas caen en noches que MIROVA confirma" leído como costo chico (`docs/S126_CLOUDMASK_RESULTADO.md:63`) | 265 de 286 son publicaciones donde MIROVA no alertó. La decisión es correcta por fidelidad; el costo está mal dimensionado |
| **H-A03** | kernel de fondo por volcán | Villarrica con n = 2; por volcán; "N de records summit baja 65 %" nunca leído como efecto sobre negativos | D25 propone lo mismo, uniforme |
| **H-A02** | primer y segundo pase (S46) | la ganancia medida son 3 records MODIS; FP invariante | defendible por fidelidad, no por la medición |
| **H-A06** | núcleo focal MODIS (S109) | C2 de 71 % contra 85 % pre-registrado, reinterpretado después como "métrica de maximizar" (`docs/AUDIT_S109_MODIS_FOCAL_VEREDICTO.md:30-33`); sin referencia fuera de Láscar | el plan definitivo dice que MODIS publica igual con alerta (11,5 %) que sin ella (10,2 %) |
| H-A05 | nadir fijo | bien medido para lo que es (fórmula). MODIS con n = 1 fuera de Láscar | sigue valiendo; no leer 0,78 como paridad sana |
| H-A09, H-A10 | pisos, cercas, y las de mayo | no abrí los audits: SIN DATO | |

Patrón común, en una línea: **hasta S139 ninguna adopción midió qué pasa donde MIROVA mira y no ve
nada**, salvo S112, que lo midió, vio que empeoraba y adoptó igual.

## 5. Cosas que vale la pena probar, que nunca se probaron o se probaron bajo condiciones que ya no existen

Ordenadas por lo que pueden mover por unidad de costo. Ninguna toca `pipeline/` en su primer paso.
Donde la puerta de la misión tiene algo que decir, lo digo.

**P1. La curva de dosis del Test 1 integrado: cuánta sobre-publicación y cuántas noches se van a cada umbral k.**
- Qué es: hoy dispara a 3 sigmas. `test1_k_observed` está persistido en todos los records de los tres
  sensores (`FASE1_SUSTRATO:56`). Se tabula, por volcán y sensor, cuántos negativos limpios T1_SOLO y
  cuántas noches positivas quedan a k = 3, 4, 5, 6, 8.
- Por qué podría funcionar: el frente F mostró hoy que el recorte `max(0, ...)` hace que el ruido puro
  sume positivo (F-01, `docs/audit_s146/FRENTE_F_FIDELIDAD_VIIRS.md:124-140`), o sea que 3 sigmas
  nominales valen menos. Y el recall casi no depende de él (71 de 75 noches siguen sin Test 1), así
  que el umbral no necesita discriminar: basta con que deje de disparar.
- Qué lo sugiere: H-01 (a k = 2,0 con fondo local los disparos ya caían a la mitad sin perder
  noches); `docs/MIROVA_DIVERGENCES.md:1435` ("k_sigma REFUTADO offline": se juzgó sólo por posición,
  "el gatillo no mueve el centroide").
- Costo del sustrato: minutos, sobre lo persistido, con el banco de S145.
- Riesgo de recall: las 4 noches SIN DATO de `FASE1_SUSTRATO:103` (Isluga 09-19, Lastarria 09-01,
  NdC 09-18, Villarrica 09-16). Listarlas una por una.
- Misión: es un umbral de un detector propio. No es literal; es la versión graduada de la Fase 2b
  (mudar el Test 1 al experimental) y sirve para saber cuánto cuesta esa mudanza.

**P2. Re-evaluar, sin re-correr, las salidas de S135 (brazo B) y S143 con criterio por volcán y en pasadas.**
- Qué es: los evaluadores y sus JSON están en `experiments/_s135_ab_d1d2/` y `experiments/_s143_evaluador/`.
  Cambiar el criterio 3 de paridad agregada por razón estratificada por volcán con n declarado.
- Por qué: el brazo B perdió por 0,016 de una métrica que premiaba un píxel a ~3 km del cráter (A100).
- Costo: horas, sin CI. Riesgo de recall: ninguno nuevo (0 de 260 noches en S135).
- Límite: S144 dejó "no habilitado apagar `keep_peak`" porque no se separa relieve tibio de fuente
  permanente. Esto no lo resuelve; sólo quita un criterio malo de encima del veredicto.

**P3. El Test 1 con fondo local sobre NTI (H-01), corrido hoy y medido con el banco de paridad.**
- Por qué físicamente: es la única cura de A69 que el proyecto diseñó y que además baja los disparos
  del Test 1 en los nevados (Villarrica, Llaima, Tupungatito), que en la tabla por volcán de la Fase 1
  son justo donde T1_SOLO manda (Villarrica 27 de 40, Llaima 26 de 45, Copahue 39 de 48).
- Costo del sustrato: **no se puede medir sobre lo persistido** (cambia el fondo del Test 1). Pide un
  probe de sólo lectura tipo A75 o un A/B en Actions con los perfiles archivados. Antes, comprobar si
  los artefactos de los runs 27275241269 y 27276651420 siguen vivos (SOSPECHA: caducaron).
- Riesgo de recall: en junio, con otro régimen, Villarrica perdía el disparo en 5 de 7 noches de lava
  en VIIRS 375 (design, líneas 254-270). Hay que ver si esas noches se siguen publicando por el camino
  contextual: es exactamente lo que no se midió.
- Misión: mejora un detector propio. Si la Fase 2 decide mudar el Test 1 al experimental, P3 pasa a
  ser una mejora del experimental, no del clon.

**P4. Mudar al experimental el anillo intermedio de S112 (H-A07), midiendo antes cuánto sostiene.**
- Qué es: `ENABLE_TEST1_INTERMEDIATE_BG` y `ENABLE_TEST1_PRIORITY_WEAK_CLUSTER`, gateados por volcán
  en Láscar, NdC y Lastarria.
- Sustrato: en la Fase 1, NdC tiene 26 T1_SOLO de 44 negativos publicados y Lastarria 13 de 21
  (`FASE1_SUSTRATO:135-139`). Cuántos dependen del anillo intermedio no sale de lo persistido: SIN DATO,
  pide probe. Costo: un probe chico (tres volcanes).
- Riesgo de recall: las alertas de 0,02 a 0,06 MW de NdC, que son reales (Sentinel-2) y que MIROVA sí
  publica. Por eso es mudanza y no borrado.

**P5. La caja de 5 km del ROI1 (D18), re-evaluada en pasadas con negativo limpio.**
- Por qué: en PCC el radio interno es de 20 km; con la caja del paper casi todo el lacolito pasa a
  umbrales de escena (C1 = 0,010, C2 = 10). PCC concentra 31 de las 50 publicaciones MODIS en negativo
  limpio, 28 por el camino del paper (`FASE1_SUSTRATO:175, 187`). El A/B de S130 ya cambió el 17,98 %
  de los records de PCC (`docs/s130/VEREDICTO_AB_D18.md:12-14`) y nadie miró si eso eran negativos.
- Costo: si las salidas de `_s130_d18_*` siguen en el repo o en artefactos, horas; si no, un A/B.
  No lo comprobé. Es uniforme y literal: pasa la puerta de la misión por la pregunta 1.
- Riesgo de recall: bajo (0 a 0,8 % de detecciones perdidas en S130), pero PCC tiene 12 noches
  positivas en la ventana actual y son AMBOS o CTX: mirarlas una por una.

**P6. La regla de preferencia entre banda I y banda M (F-07 del frente F), que nadie midió.**
- Qué es: Coppola 2026 retiene la de 750 m cuando coinciden. Nosotros publicamos las dos.
- Por qué importa acá: VIIRS 375 publica en 86,3 % de los negativos y VIIRS 750 en 21,4 %. Y podría
  ser en parte un artefacto del cruce (una fila de MIROVA contra dos records nuestros).
- Costo: minutos. Salvedad A105: es la regla del archivo OSF, no necesariamente del NRT.

**P7. El fondo por vecinos (D25) junto con el conteo de píxeles, en VIIRS 375, para la magnitud.**
- Lo sugieren F-03 y F-05 del frente F, `docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md:45-64`
  y el probe v2 de S142. Ya se probó la mitad (S143: D25 mueve la magnitud de 0,75 a 0,94 y empuja la
  publicación +0,052). Lo que **nunca se corrió** es la suma de escena como brazo de reproceso
  (`docs/s129/RADIO_DE_SUMA.md:69-80` la dejó "como brazo" y ahí quedó) ni el cúmulo de VRP máximo,
  que offline gana en 8 de 11 volcanes (0,83 contra 0,71, `docs/S124_SELECCION_CLUSTER_MAX_VS_VENT.md:34-47`,
  ventana que cruza #535 y sólo sobre noches donde MIROVA publicó).
- Riesgo: es de magnitud, no de alerta; y S124 avisa que el máximo puede reintroducir el robo de
  cúmulo. S118 midió después 0 robos en 214 noches, pero con las cercas recién apagadas y M260.

**P8. El brazo fiel de geometría: bow tie más remuestreo centrado en `get_grid_center`.**
- Ya está en la Fase 4 del plan. Lo anoto porque es el caso más limpio de "refutado lo que no era":
  D16 refutó el regrid F70 (mal centrado, sin bow tie, con M260), y el A/B del área (H-08) tiene
  veredicto sólo del chunk 1. Sustrato: minutos (razón por bin de cenit, sólo código posterior a #535).

**P9. El Test 1 sin el recorte a cero, o con el nulo de ruido descontado.**
- Sale de F-01. Nunca se probó nada parecido: todos los A/B del Test 1 tocaron el fondo, el filtro o
  el ancla, nunca el estadístico. Es la corrección mínima a un detector propio. Costo: el nulo ya lo
  midió el frente F (`experiments/_s146_auditoria/frente_F/`); falta pasarlo a pasadas publicadas.

**Lo que NO propongo, y por qué**: un piso de intensidad (H-37: cortaría alertas reales de 0,02 MW y
no es del NRT); un discriminante por record contra la etiqueta de MIROVA (H-35, prohibido y además
paradoja de Simpson); radios o umbrales por volcán (la suma con radio por volcán de S129, el inner de
PCC); la compuerta de campo difuso de S93 y la supresión de cirrus en display (parches de display para
artefactos, A72); una compuerta por `t_bg` (anti-MIROVA). El máximo diario de Laiolo 2026 tampoco: es
el procesamiento del estudio de Stromboli, igual que el filtro de intensidad.

## 6. Verificado limpio: se midió bien y no hay que repetirlo

- **H-04 (S143)** y **H-07 (probes de S141/S142)**: corridos con el código de hoy, con pre-registro,
  verificador antes y después, negativos limpios y cobertura contada. La atribución de S143 (todo el
  descenso viene de `keep_peak`; D22 y D25 empujan en contra en VIIRS 375) no hay que repetirla.
- **H-11**: el GAP #A no tiene sustrato en volcanes sin lava expuesta. Dos mediciones independientes
  (S130 y la Fase 1 de hoy: `diag_n_nti_path > 0` en 5 de 954 pasadas).
- **H-31, H-40 y el brazo "sin test de temperatura de brillo"**: ese camino está apagado desde S40 y
  su contador es cero en toda la ventana actual. Nada que correr.
- **H-32**: el k de 18,0 y la no adopción de la Ec. 9 de Aveni. Son de fórmula.
- **H-34**: las hipótesis de infraestructura de S17 y NOAA-21.
- **H-37**: el filtro de intensidad, descartado por dos vías y releído por el verificador de S141.
- **H-25 y H-26**: el radio de PCC y el percentil de anillo. No por bien medidos, sino porque la
  puerta de la misión los rechaza igual y D25 dice otra cosa.
- **H-42**: la batería del Apéndice A corre con el código de hoy. Sirve para fidelidad MODIS, no para
  la sobre-publicación.
- **H-A05**: el nadir fijo como fórmula.

## 7. Límites de este informe

- Ningún script se corrió. "Existe" es `ls`; "mide tal cosa" es lectura del código en las dos filas A
  donde lo abrí, y lectura del documento en el resto.
- La fecha de código de cada A/B la deduje del commit de su flag, de su perfil o de sus datos. No
  consulté la API de GitHub para la fecha de cada run.
- Los A/B de mayo (S38 a S44, S72 a S73) están agrupados con sólo existencia y ventana.
- No cubrí los bloques de arranque ni las notas de cierre de `tasks/`. Ahí puede haber ideas anotadas
  que esta lista no tiene.
- La columna "trabajo que apaga" (0 a 5) es mi juicio, no una medición.
- Todo esto es hallazgo del que midió. Falta el verificador con contexto limpio.

## Apéndice A. Las 66 entradas de `HYPOTHESIS_LOG.md` y dónde quedaron

| entradas | destino |
|---|---|
| H_S118_C2_GATES_NO_THEFT | H-16 |
| H_S70_PATH_D_CIRRUS_FP | H-22 |
| H_S70_R2_RETROACTIVO_4VOLS, H_S69_R2_RETROACTIVO_LASTARRIA, H_S70_TIF_VRP_SUMABILITY | H-A03 (validación R2 de un caso por volcán); confirmadas, no son descartes |
| H_S69_MODIS_OUTLIERS_05_17, H_S68_TIF_ARCHIVE_NOT_STOPPED, H_S68_ANTIPATRONES_AUDIT, H_S67_DASHBOARD_AUDIT_FINDINGS | confirmadas, fuera del censo (diagnósticos y display) |
| H_S66, H_S64 (Tupungatito, ancla) | contexto de H-24; verificadas limpias por el frente A |
| H_S62_LASTARRIA_TUPUNGATITO_AB_RESULTS | H-24 y H-A03 |
| H_S62_PCC_INNER_REPROC | H-25 |
| H_S61_LASTARRIA, H_S61_PLANCHON, H_S60_KERNEL_BG, H_S58 (dos), H_S57 | H-A03. **H_S61_PLANCHON_KERNEL_BG sigue con el estado sin llenar** ("<CONFIRMADA / REFUTADA> tras Task 3", líneas 501-502) |
| H_S61_MIROVA_DIST_FIXED_VILLARRICA | refutada en S124 (A13); el frente A ya lo marcó (A-14) |
| H_S61_AUDIT_FIELD_FIX | confirmada (A10), verificada por el frente B |
| H_S61_PCC_INFLATION_NOT_KERNEL, H_S61_TUPUNGATITO_KERNEL_BG_REVIEW | refutadas por S63 y S62. La segunda decía "Test 1 sobre-detecta, 70 a 470 píxeles" y se cerró como "especulativa": hoy D30 y la Fase 1 le dan la razón en lo esencial. Es un descarte que el tiempo revirtió |
| H1, H2, H3, H5, H7, H8, H9 | H-34 |
| H4, H6, H10, H15, H12, H18, H_S21_11, H_S47 | confirmadas y resueltas (infraestructura, esquema, NOAA-21, media aritmética) |
| H17 | H-33 y H-34 (H17a descartada por inspección visual de Nicolás: NUNCA medida) |
| H_S21_10 | H-33 |
| H11 | activa, de display |
| H13 | H-31 |
| H14, H16, H_S24_AVENI_NEGATIVE, H_S24_DIBELLA_OUT_OF_OSF | H-32 |
| H_S23_FACTOR42 | confirmada (agregación) |
| H_S23_LOCAL_ROI | H-40 |
| H_S24_P31_VALIDATED | adopción de mayo, PRE46: dentro de H-A10 |
| H_S49, H_S48 (dos) | H-A01 (el arreglo de auditoría de S48 es el origen del acierto circular: cuenta TP por `test1 + summit` aunque `pc.vrp` sea 0, líneas 920-923) |
| H_S56, H_S55, H_S54, H_S53 | H-26, H-27, H-28 y fila de Eq.16 en `docs/MISSION.md:183` |
| H_S52, H_S51, H_S48_PCC_COORD | confirmadas (ancla de PCC) |
| H_S137 (tres), H_S141 (dos), H_S143, H_S144 | H-42, H-07, H-04, H-06. Las tres de S137 siguen "active" sin resolución |

## Apéndice B. Hallazgos numerados

- **H-01 a H-43 y H-A01 a H-A10**: las filas de la tabla.
- **H-44. La máscara de 260 K era código, no perfil, y sólo de VIIRS 375** (sección 0, hecho 1). Todo
  A/B de VIIRS 375 del 5 de abril al 28 de agosto corrió con ella aunque su perfil dijera 0.
- **H-45. Corrección a A-13 del frente A**: D18 no corrió en el régimen viejo (sección 0, hecho 2).
- **H-46. Hasta S139 ningún A/B tiene negativos limpios, salvo S112** (sección 4).
- **H-47. `H_S61_PLANCHON_KERNEL_BG` quedó con el veredicto sin escribir** y tres hipótesis de S137
  siguen "active" (apéndice A).
- **H-48. Un descarte que el tiempo revirtió**: `H_S61_TUPUNGATITO_KERNEL_BG_REVIEW` ("el Test 1
  acepta demasiados píxeles") se cerró en S68 como especulativa (`docs/HYPOTHESIS_LOG.md:451`).
