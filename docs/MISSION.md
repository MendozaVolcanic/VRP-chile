# Misión VRP Chile — Clon literal MIROVA + extensión volcánica documentada

> **Documento vinculante.** Leer al inicio de cada sesión. Aplica las 3
> preguntas antes de proponer o implementar cualquier cosa que toque el
> pipeline algorítmico.

> ⚠️ **S153: el detector de la réplica cambió (adopción de K; marca A113).** Desde el merge del PR de adopción,
> `mirova_equivalent` corre (1) **sin el Test 1 integrado en el ROI** (D30: no está en el paper y hacía publicar en
> 85 a 88 % de los negativos limpios de VIIRS 375), (2) con la **conectiva `max`** de la prosa de Coppola 2016a en los
> Tests 2 y 3 (hacen falta las dos condiciones, D26) y (3) con la **banda 22 primaria en MODIS** (D21). La regla de
> decisión se escribió y aprobó antes del resultado (`experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md`, #848) y la
> evidencia está en `experiments/_s153_fk_v2/README.md`: con la lectura A, CUMPLE en las dos ventanas, 0 protegidas
> perdidas que decidan, negativos limpios publicados de 88,2 y 85,4 % a 2,5 y 3,7 % en VIIRS 375. Toda frase de
> este documento que describa el detector con el Test 1 integrado, con `min` o con la banda 21 describe el estado
> previo a S153; se conserva por historia. El laboratorio (`experimental`) sigue con el detector anterior y es la
> sombra (§4.9 de la regla). Toda comparación con MIROVA que cruce la fecha de adopción se estratifica por régimen
> (A104). Reversión: `git revert` del PR de adopción (tag `pre-s153-adopcion-k`). Ficha: `docs/FICHA_SDA_VRP_CHILE.md` v1.9.
>
> ⚠️ **S160, la frontera de la marca S157 que sigue ya no separa detectores** (A113; hallazgo 281 de
> `experiments/_s160_audit/f4/INFORME.md` §3, CONFIRMADO EN PARTE en `experiments/_s160_audit/v4/INFORME.md` §3).
> El punto (b) de abajo avisaba que «la frontera se moverá más atrás cuando se aplique el reproceso histórico con K».
> Eso ya pasó: #883 (`8471add46`, 2026-10-21) reprocesó con K el histórico de los 11 Tier A, puso
> `DATOS_K_DESDE_UTC` en 2025-02-15 (`frontend/cambio_detector.js:32`) y apartó los records C0 que quedaban en
> `data/_c0_residuales/`. En main `d516b9d8c`, del 2025-02-15 al 2026-09-17 hay 68.072 records K y 0 sin marca de
> régimen (`experiments/_s160_audit/v4/v_281_regimen_por_mes_salida.txt`; control: los 90 residuos salen C0). Una
> ventana «C0 antes del 2026-09-18» compara K contra K. El punto (c) sobre la reversión no lo midió S160.
>
> ⚠️ **S157, lo que la marca de arriba no dice** (propagación de K, `docs/AUDIT_S155.md` §2 y arreglo 5; frente 1 en
> `experiments/_s155_audit/frente_1_verif/INFORME.md`, F1-01 y V1-01). (a) El PR de adopción es **#850**, squash
> `34cea39e`, mergeado el 2026-10-18 09:57:30 UTC. (b) **Los datos no cambian de detector en esa hora sino en la fecha
> de observación 2026-09-18**: los 30 días previos al merge se reescribieron con K (commits `data(backfill)` del
> 2026-10-18, por ejemplo `5783192c1`), salvo 26 records MODIS Terra; la marca del tablero va ahí desde #860, y la
> frontera se moverá más atrás cuando se aplique el reproceso histórico con K. (c) **La reversión ya no es un
> `git revert` limpio**: simulado sobre `main` del 2026-10-20, choca en `frontend/cambio_detector.js`,
> `tests/test_cambio_detector_s153.py` y `scripts/auto_audit_weekly.py`, aunque el perfil sí vuelve a C0
> (`experiments/_s157_propagar_k/simular_revert.sh`; conflictos en `revert_hoy.out`, flags del árbol revertido en
> `revert_hoy_control.out`); y un revert no toca los records ya
> reescritos con K. El procedimiento de la reversión pre-autorizada tiene que resolver esos conflictos y esos datos;
> esta marca no lo decide.

## Misión (objetivos simultáneos, post-S86)

VRP Chile cumple dos objetivos que comparten la misma infraestructura de
detección pero se reportan distinto:

**Objetivo (1) — Clon literal MIROVA NRT** (PRIMARIO algorítmico).
Reproducir lo más fielmente posible el comportamiento de MIROVA NRT sobre
volcanes chilenos, usando **únicamente** la metodología documentada en
papers core MIROVA. El objetivo no es "mejor que MIROVA" — es "igual que
MIROVA, en infraestructura propia para SERNAGEOMIN, con dashboard limpio".
Si encontramos que MIROVA tiene un comportamiento que no queremos (FPs en
lagos, sub-detección sub-pixel, etc.), eso queda como hallazgo documentado
pero **NO** es licencia para divergir metodológicamente.

⚠️ **Rebajada S147 a S151, el objetivo (2) y el párrafo «Importante» que lo sigue** (decisiones de
Nicolás del 2026-09-21 y del 2026-10-13; marca agregada en S151 por la regla A113, fuente
`docs/audit_s150/meta/VERIFICADOR_DOCUMENTOS.md` P2): la réplica `mirova_equivalent` publica lo que
MIROVA publica y calla donde MIROVA calla (`docs/AUDIT_S149.md` §0). Lo que MIROVA no publica ya no
vive en la réplica clasificado por `pc.classification`: va al perfil `experimental`, congelado en la
producción del 2026-10-09 (PR #771, `docs/AUDIT_S150.md` §8). Cómo se pesan una alerta perdida y una
publicación de más ya no está abierto: lo fija la sección «Criterio de victoria de la réplica», más
abajo. Texto original conservado por historia:

**Objetivo (2) — Extensión volcánica documentada** (SECUNDARIO reporte).
Reportar las detecciones que el algoritmo Coppola 2016a captura pero que
MIROVA NRT no publica por scope operacional (sub-complejos volcánicos,
cráteres secundarios, lava lakes sub-pixel, lacolitos difusos, fumarolas
crónicas catalogadas Smithsonian GVP). El hallazgo S86 (auditoría
profunda) mostró empíricamente que **95.4% de las "FPs" del cruce estricto
contra MIROVA son anomalías térmicas físicamente reales** — 49.1%
publicaciones MIROVA que el cruce nuestro perdió por bugs del loader local
+ 46.3% features volcánicas reales no publicadas por MIROVA. Solo 4.6%
son artefactos espurios. Reportar (2) honestamente como valor agregado
SERNAGEOMIN — no eliminarlo.

**Importante**: el algoritmo de detección es ÚNICO (el de papers MIROVA
core). La distinción (1) vs (2) vive en el campo derivado `pc.classification`
(diseño S87 Bloque 3) + en el frontend que separa visualmente las
categorías. No se introducen gates adicionales para "limpiar" (2).

## Criterio de victoria de la réplica (decidido por Nicolás el 2026-10-13)

> Agregado en S151 (tarea 0.3 del loop; la decisión está en `tasks/LOOP_OBJETIVOS.md` §1, regla 2).
> Manda sobre toda frase anterior que diga cómo pesar una alerta perdida contra una publicación de
> más, incluido el glosario de `CLAUDE.md` («priorizamos recall sobre precision»).

**Por qué.** El operador de OVDAS lee la réplica como leería a MIROVA. Una alerta con energía que
MIROVA publicó y nosotros no es un evento que el operador no ve; una publicación donde MIROVA calló es
una falsa alarma que le enseña a desconfiar. Las dos fallas cuestan, pero no igual en todo el rango de
energía: arriba de 1 MW perder una alerta no tiene compensación posible.

1. **En la réplica no se acepta ningún cambio que pierda una alerta protegida.** Nicolás lo dijo como
   «una alerta que MIROVA clasifique de Bajo para arriba»; el corte de 1 MW es la operacionalización
   hecha en la tarea 0.2 (PR #780), sostenida por el banner de MIROVA de hoy (ningún VERY LOW llega a
   1 MW, ningún LOW queda bajo 1 MW) y **no por el paper**, cuya figura 11 se contradice con su pie.
   ⚠️ **S160, sobre el 439 y el 992 de este punto** (hallazgo 283 de `experiments/_s160_audit/f4/INFORME.md`,
   CONFIRMADO EN PARTE en `experiments/_s160_audit/v4/INFORME.md` §3): los dos números se reproducen exactos
   sobre la unión de la referencia del 2026-10-14 (`03c44eed7`); sobre la de main `d516b9d8c` dan 478 y 1.055, de
   las cuales 437 y 993 son hasta el 2026-10-13 (corpus vivo, A90; `experiments/_s160_audit/v4/v_283_d4_en_su_fecha.txt`).
   Lo que decide es la definición, no el número. Ojo: `scripts/clase_mirova.py` cuenta las protegidas siempre
   sobre la unión, aunque se le pase `--cons` o `--ocr` (V4-03).
   **Rige la lectura A, decidida por Nicolás el 2026-10-14 (D-4, issue #782 cerrado)**: una pasada
   de la referencia es **alerta protegida** si es alerta (`ALERTA_TERMICA` del consolidado o
   `ALERTA_TERMICA_OCR`) y su VRP de la pasada es de **1 MW o más**, recalculado desde el VRP y nunca
   leído de la columna `Clasificacion Mirova`, que la escribe el scraper de Mirova-v1 y no MIROVA (439
   pasadas en la unión histórica). La lectura B (toda pasada en que MIROVA ve 1 MW o más, a cualquier
   distancia, 992 pasadas) quedó descartada; los evaluadores que ya la calculan la siguen imprimiendo
   como dato informativo, pero no decide. Definición, control y denominadores:
   `docs/S151_CRITERIO_CLASE_MIROVA.md` §2, §3 y §5.
2. ⚠️ **Precisada por D-9 (2026-10-15, punto 5)**: «Muy Bajo» empieza arriba de 0,05 MW en VIIRS 375; las
   alertas del scraper de 0,05 MW o menos son pasadas que el banner llama NONE y cuentan como «MIROVA no vio
   nada». Texto original:
   **Dentro de «Muy Bajo»** (alertas bajo 1 MW, VERY LOW en el banner de MIROVA), **una alerta perdida
   y una publicación de más pesan igual**: se minimiza la suma de los dos errores.
3. **Se mide en las dos direcciones, por sensor y por tramo de calidad de la referencia (A119)**, con
   tres métricas: recall de las alertas de MIROVA, publicación en negativos limpios (pasadas donde
   MIROVA miró y no vio nada) y razón de magnitud contra MIROVA.
4. Los umbrales de cada prueba salen de los datos de MIROVA, no se eligen (A115).
5. ⚠️ **Agregado por D-9, decidida por Nicolás el 2026-10-15 (issue #811): las alertas mínimas cuentan
   como «MIROVA no vio nada» (regla SN).** El scraper llama ALERTA a todo VRP mayor que cero, pero en
   VIIRS 375 el banner de MIROVA dice NONE en las 14 pasadas observadas de 0,04 MW o menos y VERY LOW en
   las de 0,06 MW o más; en 0,05 exacto sale de los dos lados (`experiments/_s151_alertas_minimas/README.md`
   §2). Una pasada de VIIRS 375 cuyas alertas del scraper tienen todas **0,05 MW o menos** (sin ninguna otra
   alerta por encima de eso a menos de 120 s, así que una protegida nunca se toca) no es «Muy Bajo»:
   cuenta como pasada en que MIROVA no vio nada, y si la noche no tiene otra alerta es negativo limpio
   (regla 3). Las protegidas no cambian. Como Nicolás pidió probar todas las opciones, cada evaluación
   informa además SE (estrato aparte), la regla original y la variante con 0,05 exacto como alerta
   (umbral 0,04), y dice si algún veredicto cambia. Un pre-registro sellado antes de D-9 decide con la
   regla que tenía e informa las otras. Función única: `scripts/clase_mirova.py::aplicar_regla_minimas`.
   Detalle: `docs/S151_CRITERIO_CLASE_MIROVA.md` (nota D-9) y
   `experiments/_s151_alertas_minimas/veredictos_tres_reglas.md`.

## Las 3 preguntas vinculantes

**Antes de implementar cualquier feature, fix, threshold, exclusion, path,
filtro, agregación o transformación en el pipeline, responder en orden**:

1. **¿Está documentado en papers MIROVA core?** Lista oficial (**11 papers**):
   ⚠️ **S158**: además de los papers existe ahora el **código operacional de VIIRS 750** publicado por MIROVA (OSF zm62w,
   2026-07-24, MIT; `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md`). En 3 puntos el paper y el código no dicen lo mismo (media de 8 vecinos contra 3 × 3 con el
   central, fondo del VRP, piso de -0,1). Si el código prevalece sobre el texto del paper lo decide Nicolás; mientras
   tanto, toda respuesta a esta pregunta para VIIRS 750 cita también el código. **Decisión de Nicolás, 2026-10-21**: a
   la recomendación del §7 del informe («el código es la autoridad sobre el paper para VIIRS 750») respondió
   «continua con todo lo que recomiendes». Para VIIRS 750, cuando el paper y el código difieren, manda el código; para
   MODIS y VIIRS 375 manda el paper hasta tener su código o una medición.
   - Coppola 2016a SP 426.5 (Test 1 + NTI; Tabla 1 N·σ summit/scene, dual-ROI, dNTI 8-vec).
     ✅ **S128: «Coppola 2015» y «Coppola 2016a» eran la MISMA entrada, no dos papers.**
     El `Test 1` está dentro de `documentacion/sp426_5.txt` (`NTIPIX > K1 (Test 1)`, línea
     300), y el único Coppola realmente de 2015 que hay en el repo —Vanuatu, JVGR
     `10.1016/j.jvolgeores.2015.11.005`— no menciona NTI ni Test 1 ni K1 ni una vez.
     El «2015» era la fecha de publicación online de SP426.5; el «2016», la del volumen
     impreso (ya documentado en `documentacion/BIBLIOGRAPHY_SYNTHESIS.md:23-26`).
     **No volver a desdoblarla.**
   - Coppola 2020 Frontiers (review sistema MIROVA).
   - Coppola 2024 cap Springer (review pedagógico).
   - Coppola 2025 Fernandina (NRT moderno).
   - Coppola 2022 Sabancaya (k VIIRS I4).
   - Campus 2022 / Campus 2024 Vulcano (k VIIRS).
   - Aveni 2024 RSE TIRVolcH (Stefan-Boltzmann TIR).
   - Laiolo 2026 Stromboli (sin cloud filter automático). ✅ **S128: verificado verbatim**
     contra `documentacion/s00445-025-01932-y.pdf` (Bull. Volcanol. 88:11, p. 4). El PDF
     estaba en el repo nombrado por DOI — buscarlo por «laiolo» daba cero (A89).
   - Massimetti 2024 Stromboli + 2020 Sentinel-2.

   Lista de papers **NO MIROVA** (no usar como autoridad): Di Bella 2024,
   Torrisi 2022/2025, Cariello, Corradino, Amato, Marchese, Pergola,
   Genzano, Filizzola, Falconieri. Ver `~memory/reference_papers_mirova_canonical.md`.

   **Si SÍ está en papers core → puede implementarse.**

   **⚠️ Regla de verificación verbatim (S99, raíz de la confusión Eq.16):**
   responder "SÍ está en papers" exige una **cita verbatim del paper** (archivo +
   línea) que muestre que el **sistema MIROVA NRT automático APLICA** ese mecanismo —
   NO basta que el paper lo *mencione* o lo *discuta*. Distinguir SIEMPRE:
   - *"el sistema MIROVA computes/applies automatically X"* (verbo activo, sistema) →
     SÍ, parte del clon.
   - *"X can be estimated / was applied to volcano Y / requires calibration"* (voz
     pasiva, sección "Applications", caso de estudio manual) → NO es el pipeline NRT;
     va a `BEYOND_MIROVA_EXTENSIONS.md`, no a `pipeline/`.
   - Las afirmaciones de **design docs internos sobre "qué hace MIROVA" NO son
     autoritativas** hasta cotejarse contra la fuente primaria verbatim. La confusión
     Eq.16 (S53→S99) nació de tomar la interpretación de un design doc como hecho.

   **Hecho canónico (verificado S99):** MIROVA NRT = **UN algoritmo por SENSOR**
   (MODIS / VIIRS750 / VIIRS375), **uniforme entre volcanes**. La única variación
   por-objetivo es (a) geometría ROI/summit (centro GVP) y (b) sensor (bandas + α +
   umbrales). **NO conmuta de método por volcán ni por régimen térmico.** Cualquier fix
   de magnitud fiel debe ser uniforme por sensor (Coppola 2016a §98-119, §431-441,
   §689-695; Coppola 2024 §1148-1155).

   ⚠️ **S157, propagación de K**: la conmutación por volcán de la nota que sigue pasa por
   `enable_test1_lbg_global`, que fija el fondo con que se recalcula el VRP del **Test 1 integrado**; con K ese camino
   no corre (#850, D30), así que la conmutación probablemente ya no actúa en producción. SOSPECHA: no se trazó la
   cadena entera (`experiments/_s155_audit/frente_1/INFORME.md` F1-14). Texto conservado por historia.

   ⚠️ **Nota de realidad (S125)**: el principio es correcto como norte, pero el
   operacional **hoy sí conmuta por volcán**: `enable_test1_lbg_global` está gateado por
   `lbg_global_compatible` en `volcanoes.yaml` (Láscar, NdC y Lastarria usan fondo global;
   los otros 8, local), decisión tomada en S38 ("queda como mejora per-volcano"). No es
   una licencia para agregar más conmutación — es deuda declarada, para que nadie use este
   párrafo creyendo que describe el estado actual. Ver `docs/AUDIT_S125_PROFUNDA.md` §1 F2.

2. **Si NO está en papers**, ¿cierra una divergencia ya documentada en
   `docs/MIROVA_DIVERGENCES.md`?**
   **El catálogo VIVO es el doc — esta lista es resumen (actualizada S105, AUDIT_S105):**
   - ⚠️ **S160, sobre los números de la marca S151 que sigue** (hallazgo 282 de
     `experiments/_s160_audit/f4/INFORME.md`, CONFIRMADO EN PARTE en `experiments/_s160_audit/v4/INFORME.md` §3):
     el 65.705, el 1.565 y el 343 se reproducen exactos en el corpus de su fecha (`88e97d84e`, 2026-10-14) y no en
     el de hoy, porque #883 reemplazó el histórico con K (A90). En main `d516b9d8c` (74.811 records) hay 9 cúmulos
     con `pc.vrp_mw` = 5,0, los 9 con `primary_cluster.d9_capped`, y 183 sobre 5 MW
     (`experiments/_s160_audit/v4/v_282_d9_capped_salida.txt`): bajo K el tope casi no actúa, y la cara de
     co-validación del path D se midió con el detector anterior.
   - ⚠️ **S151, sobre el «se confirma el tope de 5 MW» del ítem que sigue**
     (`docs/audit_s150/meta/VERIFICADOR_DOCUMENTOS.md` P5): «se confirma» sólo quiere decir que el
     tope recorta. No está medido que lo recortado sea artefacto (`docs/AUDIT_S146.md` C-02: el
     «no es parche» del tope no lo sostiene el paper). Corpus al 2026-10-14 (65.705 records): 1.565
     cúmulos topados en 5,0 exacto (277 `summit`), los 1.565 con `primary_cluster.d9_capped`, y 343
     cúmulos **sobre** 5 MW (110 `summit`); el «0 records sobre 5 MW» de A23 vale sólo para la
     población de S113. Script: `experiments/_s150_meta_audit/verif_docs/contar_topados_d9.py`.
   - ⚠️ **S151: D8' ya no está resuelta** (`docs/MIROVA_DIVERGENCES.md`, marca bajo el encabezado de
     D8'): Nicolás decidió el 2026-10-09 que la réplica elija la anomalía MAYOR de la escena, como
     MIROVA (`docs/AUDIT_S150.md` §8), y la entrada D8' de la lista de «Resueltas» de más abajo dice
     lo contrario. Producción sigue con el cúmulo más cercano al cráter hasta el A/B pre-registrado.
     ⚠️ **Matiz S151 (tarea 1.4 del loop, PR #809, dos verificadores con contexto limpio):** sobre los
     GeoTIFF de MIROVA, MIROVA informa el foco lejano cuando es fuerte (15 de 15 con z ≥ 30) y el cráter
     cuando el lejano es débil; la fuerza del lejano y el calor del cráter pesan los dos, y «la mayor»
     contra «la suma» **no está demostrado**. Además, cuando informa el cráter, su VRP es el del cráter
     solo, sin el foco lejano débil que nosotros sí alertamos (causa candidata: la conectiva `min`,
     SOSPECHA). El diseño del brazo que elija la mayor espera el A/B de F y K
     (`experiments/_s151_seleccion_mirova/README.md`). ⚠️ **S153: el A/B de F y K ya está hecho y K
     se adoptó** (producción con `max`; marca del inicio de este documento); el brazo que elija la mayor
     se diseña ahora sobre K.
   - ⚠️ **REBAJADA S146: esta lista de «Resueltas» se lee primero y varias entradas ya
     cayeron dentro del propio proyecto** (`docs/AUDIT_S146.md` §2, V-13, V-01, V-06). **D9 no
     está cerrada**: el «207 de 214 confirmados» no se reproduce con ninguna definición en que
     «confirmado» signifique que MIROVA publicó una alerta (máximo **80 de 214, 37,4 %**; el
     rango 201 a 211 sólo aparece contando cualquier fila de la referencia, incluidas las
     RUTINA), y el «0 fuga» es circular porque el dashboard oculta todo `far` por construcción;
     lo que sí se confirma es el tope de 5 MW y los denominadores 199 `far` / 214 `summit`
     (V-01). **D4** se apoya en el Test 1 integrado en el ROI, que es un **detector propio**: en
     `sp426.5.pdf` p. 6 el Test 1 es por píxel contra K1, y la cita «Coppola 2015, Bull.
     Volcanol. 77:55» corresponde a Heap et al. sobre mecánica de rocas en andesita (DOI
     10.1007/s00445-015-0938-7; Crossref y OpenAlex dan 0 artículos de Coppola en esa revista en
     2015, con control de consulta) (V-06). **D8** sigue vigente por la vía del fondo de anillo
     (D25 en el catálogo). **D5 tampoco está resuelta**: el catálogo la tiene desde S125 como
     «abierta pendiente de re-medición», con el signo opuesto (sub-reporte cerca de 0,75 y no
     sobre-reporte de 1,35), y sus dos patas están rebajadas (nadir fijo no es el remuestreo,
     A66; `keep_peak` daba paridad por accidente, A100) (AUDIT_S146 §2 y E-06). Lo que sigue se
     conserva por historia.
   - ⚠️ **S157, D4 se queda sin su mecanismo** (propagación de K, `experiments/_s155_audit/frente_1_verif/INFORME.md`
     F1-09): el «D4 recall sub-pixel (S27)» de la línea que sigue se cerró con el Test 1 integrado, que con K no corre
     (marca del inicio de este documento). Y K deja de publicar justo alertas débiles de VIIRS 375: 16 de 194 alertas
     Muy Bajo en V1 y 26 de 388 en V2, contra 0 con el detector anterior (`experiments/_s153_fk_v2/v1.log:91` y
     `v2.log:148`). La regla de adopción pesó ese costo; si D4 se reabre lo decide Nicolás.
   - ⚠️ **S158 R2** (docs/AUDIT_S158_R2.md, marca A113; `experiments/_s158_audit_r2/a113/INFORME.md` n 5 y 13), dos
     entradas más de la línea que sigue, contra el código de VIIRS 750: el tope de 5 MW de **D9** (cap C) es mecanismo
     nuestro, MIROVA no topa ni compuerta por fondo (`MIROVA_VIIRS750_VRP.m` l. 83 a 91); y el fondo de **D8** no es
     «Coppola 2024 L1129 literal»: esa frase es del modelo de dos componentes (libro p. impresa 337, renderizada) y en
     VIIRS 750 MIROVA aparta los vecinos e interpola (`MIROVA_VIIRS750_VRP.m` l. 63 a 81).
   - Resueltas (no justifican features nuevas): D1 granularidad, D4 recall sub-pixel
     (S27), D5 magnitud (nadir S102/103 + ctxpeak D10 S100), D8/D8' cluster selection
     (S38/S62), sec³ off-nadir (S102/103), fix del ancla de detección (S98),
     **D9 path-D cirrus** (cap C S71 + magnitud curada por nadir/focal S102-S109;
     verificado S113: 0 fuga al dashboard + mediana 0.53×; t_bg-gate descartado anti-MIROVA/trap A68).
   - **Abiertas**: (⚠️ S131: esta enumeración quedó congelada en S105 y omitía D13, D17 y D18. **El catálogo `docs/MIROVA_DIVERGENCES.md` es la lista viva; esta sección no la duplica** — para el estado de hoy, leer los encabezados de cada D en ese archivo. Lo que sigue se conserva por historia.) D2 cobertura CSV ground truth · D3 FP explícito MIROVA ·
     **D11 sesgo topográfico de paths MIR-absolutos (A69, S104)** — (⚠️ **S157, la condición del cierre ya se
     cumplió en producción** (propagación de K, `experiments/_s155_audit/frente_1_verif/INFORME.md` F1-04): S138 dejó
     el «irreducible a 1 km» valiendo sólo bajo banda 21 primaria, y desde K la réplica corre con la banda 22. K midió
     MODIS en los 11 volcanes: fuera de Láscar publica en negativos limpios 7 de 825 (V1) y 18 de 2.173 (V2), contra 107
     y 242 con el detector anterior (`experiments/_s153_fk_v2/v1.log:178`, `v2.log:233`; de los 242, 158 son de PCC).
     El cierre queda sin el respaldo con que se escribió. Qué hacer con D11 (reabrirla, re-cerrarla como resuelta por
     K o medir sólo la cara de posición) no lo decide esta marca.) (⚠️ **REBAJADA S146**
     (AUDIT_S146 V-02): «irreducible» y «todos los ejes agotados» quedan rebajados acá igual que
     en A82 de `CLAUDE.md`, porque el número que sostiene el cierre no tiene tasa base. Con
     negativos limpios hay cúmulo con magnitud dentro del inner en **89,1 %** de las pasadas
     MODIS contra **93,7 %** cuando MIROVA alertó, menos de 5 puntos de contraste, y 144 de 158
     positivas son de Láscar (ventana 2026-01-29 a 2026-08-28; después de #535, 86,0 % de 500
     negativos y sólo 2 positivos). El texto que sigue se conserva por historia.) cara MODIS far→summit
     **CERRADA S114** (irreducible a 1 km; detección fiel a Coppola verificada file:line;
     todos los ejes agotados — A82, `docs/AUDIT_S114_PARITY_BY_SENSOR.md`); queda abierta solo
     la cara POSICIÓN del ancla en nevados (~1-1.5 km N, A70, costo residual no de recall) ·
     D2 N·σ Tabla 1 ya implementado (dual-ROI 5/10, S114); (⚠️ **ese 5/10 no está en la Tabla 1,
     verificado S146 (AUDIT_S146 V-08)**: en la Tabla 1 el C2 multiplica la desviación del dNTI y
     del dETI, y el paper no tiene ningún test de temperatura de brillo. El camino de BT está
     apagado hoy (`ENABLE_BT_PATH_HOT = False`); lo que cae es la atribución a la Tabla 1, ver
     D31 en el catálogo.) (⚠️ **FALSO, GAP #A
     REABIERTO S128 y confirmado S146** (AUDIT_S146 §2): está abierto en
     `docs/MIROVA_DIVERGENCES.md` con guard `tests/test_guard_gap_a_pool_musigma_s128.py`. La
     frase que sigue se conserva por historia.) GAP #A (§298-300 retiro Test1 K1) fue
     **RESUELTO S115 = mislabel, NO es gap** (DIVERGENCES:1292) — NO reabrir · VIIRS750 disperso
     glaciar (Tupun/PP, ctxpeak S102§2) ·
     (⚠️ **NO es un gap abierto, verificado S146 (AUDIT_S146 V-05)**:
     `ENABLE_UNSUITABLE_FILTERS_267_273` está en True desde S72 y los tres procesadores lo
     consumen en las dos ramas (path D contextual y primer paso de los Tests 2 y 3). Lo único que
     sigue apagado de ese párrafo del paper es el retiro de los píxeles del Test 1, o sea el
     GAP #A. Un A/B contra un control que ya tiene el filtro no mediría nada.)
     NEW-8 gaps 2-4 (pool estadístico m,σ).
   - **Resuelto S118**: gates intra-radio S84/S85 → **OFF** (A/B real run 28312968093:
     0 robos de cluster en 214 noches focales; PR #474, tag `pre-s118-c2-flip`;
     verificación post-flip verde `docs/AUDIT_S119.md` §1). El operacional volvió a
     clon-literal sin cercas; la separación clon/beyond vive en el display.

   Cerrar divergencia = alinear comportamiento con MIROVA, no agregar
   funcionalidad nueva. **Si SÍ cierra divergencia → puede implementarse.**

3. **Si NO está en papers y NO cierra divergencia documentada**, ¿es
   alineación interna no-metodológica?**
   Ejemplos válidos: render del frontend, infra A/B, tests, scripts de
   evaluación, documentación, persistencia de memoria.

   **Si SÍ es alineación interna → puede implementarse.**

**Si las 3 son NO → NO IMPLEMENTAR.** Anotar en `tasks/backlog_*.md` con la
razón "no cumple regla MIROVA literal" y seguir.

## Anti-patrones a evitar (lecciones acumuladas)

Estas fueron las desviaciones históricas. Nunca repetir.

| Parche histórico | Razón rechazo | Estado |
|---|---|---|
| `MAX_SIGMA_COMPONENT_K=7K` cap eruption | No en papers; anula 5σ/10σ MIROVA | ⚠️ **Neutralizado por VALOR, no removido del código (S125).** El bloque corre en cada pasada; el perfil operacional lo pone en `999.0`, pero el **default del código es `7.0`** — un perfil que omita la clave resucita el parche en silencio. |
| Vent-path entero | (⚠️ **S157**: el «sub-pixel debe ir por Test 1» describe el detector previo a K; desde #850 el Test 1 integrado no corre en la réplica. La razón primera, «no en papers», no cae. `experiments/_s155_audit/frente_1_verif/INFORME.md` F1-09. Texto original:) No en papers; sub-pixel debe ir por Test 1 (Coppola 2016a SP426.5) | Removido S27 |
| `exclude_zones` (Salar, lagos) | ⚠️ **S158 R2** (docs/AUDIT_S158_R2.md, marca A113; `experiments/_s158_audit_r2/a113/INFORME.md` n 3): «MIROVA no usa máscaras geográficas» cae en su forma absoluta para VIIRS 750. Su código admite píxeles excluidos (NaN en `BOX`) y dice que las ROI se adaptan por volcán, incluso para excluir volcanes vecinos u otras fuentes térmicas persistentes (`MIROVA_VIIRS750_hotspot_detection.m` l. 25 a 29 y 120 a 128). Si lo aplica en Chile es SIN DATO; «no en papers» no lo revisé. Un salar o un lago no son «fuente térmica persistente» por definición: reponer `exclude_zones` sigue pidiendo pasar las 3 preguntas, ahora con el código como respaldo posible y no como veto. Texto original: No en papers; MIROVA no usa máscaras geográficas | Removido S27 |
| Regla D vent-priority | Parche de clasificación visual, no en papers | Removido S27 |
| Regla D Test 1-priority | Parche de composición de paths, no en papers | ⚠️ **SIGUE ACTIVA (corregido S125).** La fila decía "Removido S27" y es falsa: el bloque está vivo en los 3 procesadores (`process_viirs.py:1642-1710`, `process_modis.py:1196-1230`, `process_viirs_mod.py:1069`; líneas actualizadas S131) y está **parcialmente gateado**: la rama de clúster rival débil depende de `ENABLE_TEST1_PRIORITY_WEAK_CLUSTER` (`process_viirs.py:1695`), el resto no tiene flag y además se **amplió** después de S27 — port a MODIS en S30, y ajustes en S44 y S111. Ver `docs/AUDIT_S125_PROFUNDA.md` §1 F1. |
| Cloud mask BT<260K | ✅ **verificado verbatim S128** contra `documentacion/s00445-025-01932-y.pdf` p. 4: *"Importantly, no atmospheric correction or cloud-contamination automatic filtering is applied to the dataset"*. D14 CERRADA. ⚠️ Pero el mismo párrafo dice que MIROVA **sí filtra por distancia e intensidad y por doble conteo entre detectores**, quedándose con el 12 % (9.712 de 82.329), y que su mitigación de nube es tomar el **máximo diario** — eso último sigue sin implementarse. | ✅ **RETIRADA S126 (PR #535).** El umbral sale del perfil (`process_viirs.py:786`: `CLOUD_BT_THRESHOLD = CLOUD_MASK_BT_K`) y `cloud_mask_bt_k` vale `0.0`, así que la máscara está apagada en los tres sensores; el cambio de una línea que esta fila pedía ya se hizo. Texto anterior, por historia: ⚠️ ~~SIGUE ACTIVA en VIIRS 375 (corregido S125)~~. La perilla del perfil existe y está neutra (`CLOUD_MASK_BT_K = 0.0`, que apaga la máscara en MODIS y V750), pero `process_viirs.py:674` tenía `CLOUD_BT_THRESHOLD = 260.0` **hardcodeado**, ignorando la perilla, y en `:678-681` lo aplica a `roi_mask` **y** `bg_mask`. Ciega ~23 % de las pasadas del sensor que hoy carga el recall, y a 260 K no distingue tope de nube de cumbre nevada. Retirarla es cambiar el literal por la constante del perfil (una línea, requiere A45). Ver `docs/AUDIT_S125_PROFUNDA.md` §1 F3. |
| Pisos VRP por sensor | Coppola 2023 dice "floor ~1 MW" genérico, no por sensor | ✅ **RETIRADOS S130** (PR #571, ciclo A45 completo): los tres pisos valen `0.0` en `mirova_equivalent.yaml`; el helper `_apply_vrp_floor` (`pipeline/store.py:72-103`) sigue existiendo y se llama en `store.py:489`, pero con piso 0 no actúa. Medido al retirarlo: 0 noches MIROVA-confirmadas perdidas, VIIRS750 recall 82,52 → 84,55 %, 582 records invisibles → 0; el piso de MODIS nunca actuó (0 de 11.717). Texto anterior, por historia: ⚠️ ~~SIGUEN ACTIVOS~~ (corregido S124). La fila decía "Removido S27" y era falsa: `pipeline/store.py:459-468` aplica `MIN_VRP_MW_VIIRS375=0.02`, `_VIIRS750=0.15`, `_MODIS=0.05` desde `mirova_equivalent.yaml:64-71`, y marca el record con `diag_vrp_floor_mw`. Alcance medido S124: **1564 de 23990 records summit (6,5%)**. Reintroducir un piso NO requiere pasar las 3 preguntas porque el piso ya está ahí — lo que hace falta es decidir si se retira. |
| Path C NTI relativo (default ON) | No en papers | Default OFF mantenido |
| Subir `inner_radius_km` ad-hoc | Parche para recuperar recall; no es metodológico MIROVA | Rechazado S27 |
| N·σ Di Bella 2024 (12σ noche VIIRS) | Di Bella es INGV Catania, NO MIROVA | Identificado S26 |
| **Gate intra-radio por path** (S83-S85 PRs #224, #229) | No en papers; el frontend `mirovaEqVrp` ya hacía exactamente eso desde S33 → adopciones redundantes | **Removido S118** (A/B 0 robos de cluster, PR #474) |
| **Eq.16 lava lake / Eq.25 crater lake POR-VOLCÁN** (design S53, casi adoptado S99) | El capítulo Coppola 2024 las presenta en sección "Applications" como productos de 2º nivel MANUALES y calibrados caso por caso ("requires specific calibrations", "valid only within the limits of the assumptions") — **NO el pipeline NRT automático**. MIROVA NRT es UN algoritmo por SENSOR uniforme (Coppola 2016a: "completely autonomous", "self-adapting thresholds independent of local conditions"). Conmutar de método por volcán es un drift. | Identificado S99 — movido a beyond-MIROVA (`docs/BEYOND_MIROVA_EXTENSIONS.md` EXT-11). Citas verbatim: `experiments/_s99_audit/dormant/papers_per_sensor.md` |

**El patrón común**: cada parche resolvía el síntoma de un drift previo, no la
causa raíz. Cuando se acumulaban, anulaban la diferenciación summit/scene de
MIROVA. Volver a literal puro es la forma de detener el ciclo.

**Familia "gate intra-radio" (S86)**: las adopciones S83-S85 (path D
restringido a intra-radio + second pass restringido a intra-radio)
pasaron las 3 preguntas solo por puerta 3 GRIS "alineación infraestructural",
pero la auditoría S86 reveló que el gate intra-radio ya existía en el
frontend desde S33 — eran adopciones redundantes que además, si se
hubieran combinado con G1 (`sensor != VIIRS_M_750`) propuesto S86,
habrían suprimido categoría (b) "features volcánicas reales no publicadas
por MIROVA". **Cualquier PR futuro que proponga otro gate "intra-radio por
path" requiere primero**: (a) verificar que el frontend no hace ya esa
supresión, (b) clasificar la categoría físicamente (E S86) de los
records que el gate filtraría, (c) confirmar que ninguno pertenece a (b).

⚠️ **S151, sobre el párrafo que sigue** (`docs/audit_s150/meta/VERIFICADOR_DOCUMENTOS.md` P4): habla
de **cercas** alrededor de la selección, no de la regla de selección, y eso sigue en pie. Pero mide el
éxito como «0 robos de cluster», y bajo la regla de la anomalía mayor (decidida por Nicolás el
2026-10-09, A/B pendiente, `docs/AUDIT_S150.md` §8) que un cúmulo lejano más fuerte gane es
fidelidad a MIROVA, no robo: «0 robos» deja de ser la vara de ese A/B. Texto original:

**Cierre de la familia (S118)**: el A/B real con reproc (run 28312968093,
criterio pre-registrado "robo de cluster espacial") demostró que las cercas
no protegían nada — 0 robos en 214 noches focales MIROVA-confirmadas; la
selección de cluster vent-anchored es robusta a los píxeles extra-radio por
sí sola. Ambos gates se flipearon a OFF (PR #474) y el post-flip se verificó
verde en S119. La lección quedó destilada como regla A85 en CLAUDE.md: medir
el robo real ANTES de cercar.

## Cuándo SÍ se puede divergir

**Solo en estos casos** documentados explícitamente:
- **Datos / infraestructura**: NOAA-21 integration, A_pix nadir + scan-angle,
  cap top-100 anomaly_pixels (anti-bloat), gitignore de snapshots locales.
- **Render frontend**: visualización 1 marker/record alineado con MIROVA NRT
  (S27).
- ⚠️ **S158 (F2-H1, confirmado por V2)**: MIROVA cuenta píxeles y suma todos los alertados, sin agrupar
  (`MIROVA_VIIRS750_VRP.m` l. 61 y 83 a 85). El ítem que sigue describe algo que el código de MIROVA no hace. Ver
  `docs/AUDIT_S158.md`.
- **Cluster aggregation** (S27): alineación con `n_hotspots` MIROVA via
  `scipy.ndimage.label` 8-conn — explícitamente Coppola 2016a "neighbor
  pixels" connectivity.
- **Tests** que validan comportamiento contra papers.
- **Scripts evaluación / forense** que comparan vs CSV consolidado MIROVA NRT.

Cualquier otra divergencia requiere actualizar este documento primero,
justificando contra papers MIROVA core.

## Si encontrás que el literal puro pierde recall

⚠️ **Rebajada S147 y S149, marca agregada en S151** (`docs/audit_s150/meta/VERIFICADOR_DOCUMENTOS.md`
P3): el A/B de S27 midió contra un perfil `_mirova_literal` (commit `db602040b`, 2026-04-29) que no
tenía ni el ETI ni el Test 1; los Tests 2 y 3 con ETI entraron al código el 2026-05-15 (`958a7a189`),
según `git log -S` (`docs/AUDIT_S149.md` §0). Y el «recall 50 a 80 %» que cerró D4 quedó SIN
EVIDENCIA y circular (`docs/audit_s147/VERIFICADOR_H_A01.md`; marca de S147 dentro de D30 en
`docs/MIROVA_DIVERGENCES.md`). O sea: **«el literal pierde recall» no está medido**, y no sirve para
defender el Test 1 integrado, que es un detector propio (D30). Texto original por historia:

⚠️ **S153**: el Test 1 integrado ya no corre en la réplica (adopción de K, marca del inicio de este
documento y marca S153 de D30); esta sección se conserva para el día en que una pérdida de recall
medida vuelva a plantear la pregunta, y la respuesta sigue siendo la de abajo: investigar, no parchar.

Esa es señal de que MIROVA usa un mecanismo que no replicamos todavía. La
respuesta correcta NO es agregar parche — es **investigar qué mecanismo
documentado en papers MIROVA core estamos pasando por alto**.

Hipótesis abiertas (S28+, ver `~memory/project_s27_mirova_literal_negativo.md`):
- H_S27_1 (⚠️ **cita falsa, S146 V-06, marca agregada S151**: `sp426.5.pdf` no tiene §2.2, su Ec. 1
  es el NTI y el Test 1 es por píxel contra K1, p. 6; ver `docs/MIROVA_DIVERGENCES.md` H_S27_1 y D30.
  Texto original:) Test 1 summit-only más agresivo (Coppola 2016a SP426.5 §2.2 Eq.1).
- H_S27_2: dNTI con C1 negativo (cooling) además de positivo.
- H_S27_3: path TIR-only Aveni 2024 RSE TIRVolcH.
- H_S27_4: composición paths cascada vs OR (cómo MIROVA combina internamente).
- H_S27_5: subir `inner_radius_km` — **RECHAZADA** como parche.

## Auditoría obligatoria al cierre de cada sesión

Antes de marcar una sesión como completa, responder explícitamente:
1. ¿Qué cambios hice en `pipeline/` esta sesión?
2. Por cada uno: ¿pasa las 3 preguntas?
3. Si alguno NO pasa: revertirlo o documentar excepción explícita en este
   archivo.

## Referencias

- Divergencias actuales: `docs/MIROVA_DIVERGENCES.md`
- Papers MIROVA canonical: `~memory/reference_papers_mirova_canonical.md`
- Parches no-MIROVA inventario: `~memory/project_s26_parches_no_mirova.md`
- ⚠️ **SIN EVIDENCIA desde S147, marca agregada S151** (ver la marca bajo el título de la sección del
  literal puro, más arriba). Texto original: A/B literal puro NO APROBADO: `~memory/project_s27_mirova_literal_negativo.md`

---

## R2 retroactivo — referencia operacional

Para aplicar el método R2 retroactivo a un vol nuevo (validación de adopción metodológica
post-S70), seguir el patrón documentado en `docs/R2_GATES_BY_REGIME.md`. Las bandas
gates son **régimen-dependientes** (Tier A Alto, Tier A Muy Bajo simple, Tier A Muy
Bajo complejo, No focal). Aplicar gates Lastarria-style a cualquier vol sin clasificar
régimen primero introduce FAIL marginales sistemáticos que ocultan que la adopción de
hecho funciona en agregado.
