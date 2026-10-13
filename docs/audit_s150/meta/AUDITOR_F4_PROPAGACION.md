# Meta-auditoría S150, frente F4: ¿bajó lo aprendido en S147 a S150 a las puertas de entrada?

> Auditor F4, solo lectura (2026-10-09). Nada de esto modificó el repositorio fuera de
> `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s150_meta_audit\F4\`
> (cinco scripts y sus salidas `.txt`). Cada afirmación cita una línea que leí en esta sesión o un número
> que produjo un script mío. Lo que viene de un informe anterior y no recomprobé dice **heredado**.

## 0. En una pantalla

**El hallazgo central es el mismo de S146, repetido.** Las dos auditorías integrales de este tramo
(AUDIT_S149, PR #750, y AUDIT_S150, PR #760) tocaron, entre las siete puertas, **sólo una fila de
`docs/INDEX.md`** cada una (`git show --stat d46b7ec59` y `a254f6a48`). La Fase 0 de AUDIT_S149
(`docs/AUDIT_S149.md:123-125`) mandaba propagar a `CLAUDE.md`, `docs/MISSION.md` y el bloque de arranque
seis cierres caídos y las decisiones de Nicolás; ninguno de los seis tiene marca hoy. El último cambio del
catálogo de divergencias que viene de este tramo es de S148 (#734, D18). Nada de S149 ni de S150 entró al
catálogo (`grep -n "S149\|S150" docs/MIROVA_DIVERGENCES.md` da cero líneas).

| clase | n | qué es |
|---|---|---|
| MARCADA | 13 | la cita vieja lleva advertencia y puntero |
| SIN MARCAR | 27 | texto viejo que sigue afirmando lo caído |
| AUSENTE | 6 | lo nuevo (hallazgo o decisión) no está en ninguna puerta que lo necesita |
| CONTRADICTORIA | 11 | dos puertas, o dos lugares de la misma puerta, dicen cosas distintas hoy |

Lo que más daño puede hacer a una sesión fría, en orden: (1) la sesión fría no se entera de S150 (Chillán
en erupción, prueba aprobada para el 2026-10-13, decisiones de Nicolás); (2) `MISSION.md` y el glosario de
`CLAUDE.md` contradicen la decisión de paridad en los dos sentidos, que es lo que habilita adoptar `max`;
(3) el veredicto de S27 que fundó el Test 1 sigue en pie en `MISSION.md` y en la memoria principal;
(4) el catálogo da por resuelta la selección del cúmulo más cercano (D8'), contra la decisión de Nicolás
de la anomalía mayor.

## 1. Método y las dos preguntas del instrumento

**Puertas revisadas**, en el orden en que se leen: `CLAUDE.md` del proyecto, `docs/MISSION.md`,
`docs/MIROVA_DIVERGENCES.md` (encabezado de cada D y el cuerpo cuando hacía falta), `tasks/BLOQUE_ARRANQUE_S150.md`
(último por `sort -V`), `docs/INDEX.md`, `docs/FICHA_SDA_VRP_CHILE.md`, `MEMORY.md` de la memoria y los dos
`feedback_*` que el índice marca como regla principal.

**Fuentes de lo que cambió**: `docs/AUDIT_S149.md`, `docs/AUDIT_S150.md`, `docs/S150_*.md`, `docs/audit_s147` a
`docs/audit_s150` (por búsqueda dirigida, no leídos enteros), reglas A114 a A119, y
`project_s147_estado.md` a `project_s150_estado.md` de la memoria.

**Patrones de búsqueda declarados** (en `propagacion_grep.py`, 25 ítems): `literal puro`, `S27 Test1 cierra D4`,
`NO APROB`, `recall cae 27`, `resultado empírico de S27`, `priorizamos recall`, `cobertura completa de lo que
MIROVA publica`, `No se introducen gates adicionales`, `no eliminarlo`, `946`, `enero no se usa`, `86 % en`,
`dependen del OCR`, `12 veces/día`, `cron cada 2h`, `2026-10-03`, `tope de magnitud ya está adoptado y funciona`,
`tope de 5 MW`, `RESUELTO S38`, `vent-anchored es robusta`, `process_viirs.py:1313`, `Arreglarlo toca`, `#738`,
`SIN MERGEAR`, `NO ADOPTAR porque apagarlo`, `D22/D25 ... NO ADOPTAR`, `TOKEN EARTHDATA VENCIDO`, `5 perdidas
fuertes`, `Versión:** v1.4`, `suma únicamente los píxeles`, `físicamente indistinguibles`, `laboratorio es
**idéntico`, `devuelve lo de LAADS`. Además, a mano: `anomal.a mayor`, `vrp_max`, `vent_anchored`,
`dos sentidos`, `tabla de terminado`, `2026-09-14`, `erupci`, `Chill.n`, `conectiva`, `compens`, `D18`, `D21`,
`D22`, `D25`, `S149`, `S150`, `NOAA-21`, `Suomi|SNPP`, `otra pasada|Last Update`, `congel`.

**Medición 1, `propagacion_grep.py` (salida `propagacion_grep.txt`).**
1. ¿Vería una cita sin marca? Sí, si la cita usa las palabras del patrón. No ve paráfrasis: es un piso.
2. ¿Vería que está muerto? Controles positivos: A10 (rebajada en S147, `CLAUDE.md:228`) y A118 (arreglo de
   S149, `CLAUDE.md:1466`) salen con marca. **Limitación medida**: su etiqueta «MARCADA?» se dispara con
   cualquier advertencia o «S147..S150» a seis líneas, y eso da falsos «marcada» cuando la propia regla nace
   en ese tramo (A117, A119) o cuando la línea de memoria es de S14x. Por eso **cada clasificación de este
   informe la hice leyendo la línea**; el script sólo encuentra candidatos.

Las otras cuatro mediciones llevan su encabezado en la sección donde se usan.

## 2. Hallazgos, lo peor primero

### F4-01. La sesión fría no se entera de S150: Chillán en erupción, la prueba del 13-oct y cinco decisiones de Nicolás
- **ARCHIVO:LÍNEA**: `tasks/BLOQUE_ARRANQUE_S150.md:3` (estado de S149, 2026-09-21), `:67` y `:121` («el token vence
  el 2026-10-03»), `:136-137` («hoy los dos perfiles son idénticos»); `MEMORY.md:31` (línea de S150 escrita el
  10-03/04: «TOKEN EARTHDATA VENCIDO, NRT caido», «5 perdidas fuertes ... (mirar imagenes MIROVA)», «Abril espera
  Chaiten»); `MEMORY.md:33` («Cableado de la caja en PR #738 ... ESPERA el si de Nicolas», «Pre-registro v2 ...
  SIN despachar»). `grep -n -i "erupci\|Chill.n\|anomal.a mayor\|congel"` sobre `MEMORY.md` y el bloque: cero
  líneas sobre la erupción, la prueba o las decisiones.
- **QUÉ PASA**: Nevados de Chillán está en erupción desde el 2026-09-28 (AUDIT_S150 §0) y la prueba que separa
  detector, tope y etiqueta MODIS está **aprobada por Nicolás para despacharse desde el 2026-10-13**
  (`project_s150_estado.md`, «Respuestas de Nicolas 2026-10-08», punto 1). Esa fecha, la decisión de la anomalía
  mayor, la reapertura de las metas, el reproceso de la historia el día de la adopción y el experimental congelado
  viven sólo en `docs/AUDIT_S150.md:150-164` y en la memoria de detalle. El último bloque de arranque es el de
  S149, y la línea de S150 del índice de memoria (que se carga sola en cada sesión) describe el sistema caído y
  cinco pérdidas que ya se resolvieron (#764, #774: filas del OCR con la imagen de otra pasada;
  `docs/S150_IMAGENES_SNPP.md:7-13`). #738 está mergeado (`gh pr view 738`: MERGED 2026-09-21T12:27:52Z).
- **CÓMO SE VE EN EL DASHBOARD**: mientras la prueba no corra, el tablero de Chillán sigue con la pasada MODIS
  del 2026-10-01 08:35 oculta como `far` (medido: `final_hotspot_dist_km` 32,86, cúmulo a 0,854 km, 2,29 MW,
  `distance_class` far; MIROVA 5,18 MW según AUDIT_S150 §2, heredado) y con el tope D9 rotulando 5,00 como
  «probablemente artefacto» (`frontend/index.html:1108-1110`).
- **CÓMO REPRODUCIRLO**: `sed -n 29,33p` del `MEMORY.md`; `sed -n 1,7p tasks/BLOQUE_ARRANQUE_S150.md`;
  `python -c "import json; ..."` sobre `data/mirova_equivalent/NevadosDeChillan.json`, pasada 2026-10-01 08:35 MODIS_AQUA.
- **CONFIANZA**: CONFIRMADO (lectura de las líneas y del record).
- **GRAVEDAD**: 4. Una prueba con fecha, sobre un volcán en erupción, depende de que alguien la recuerde.

### F4-02. CONTRADICTORIA: la decisión «paridad en los dos sentidos» contra `MISSION.md` y el glosario de `CLAUDE.md`
- **ARCHIVO:LÍNEA**: `docs/MISSION.md:21-36` (Objetivo 2: reportar las detecciones que MIROVA no publica «no
  eliminarlo»; «el algoritmo de detección es ÚNICO»; «No se introducen gates adicionales para limpiar (2)»);
  `CLAUDE.md:1619` («Para `mirova_equivalent` priorizamos recall sobre precision»);
  `feedback_s143_primero_igualar_a_mirova.md:17` («cobertura completa de lo que MIROVA publica primero») y `:27`
  («La sobre-publicación y la magnitud se optimizan **después**»), con su línea de índice `MEMORY.md:100`.
  Del otro lado: `feedback_mirova_equivalent_priorities.md:66-71` («Decision S149: PARIDAD EN LOS DOS SENTIDOS»,
  que ya nombra la contradicción con el glosario) y `docs/AUDIT_S149.md:12-14` («callar donde calla; lo extra va al
  experimental»).
- **QUÉ PASA**: Nicolás decidió en S149 que la réplica calle donde MIROVA calla y que lo que MIROVA no publica vaya
  al perfil experimental, que desde #771 es otro perfil con su propia configuración congelada
  (`pipeline/profiles/experimental.yaml:63`). Las dos puertas que se leen primero dicen lo contrario: que la
  detección es una sola y que no se filtra lo que MIROVA no publica, y que el recall manda sobre la precisión.
  Ninguna lleva marca. El AUDIT_S149 lo detectó (`:43`) y lo puso en la Fase 0 (`:123`); no se hizo.
- **CÓMO SE VE EN EL DASHBOARD**: invisible hoy. Decide si se adopta `max`, la palanca que en VIIRS 375 baja la
  publicación en negativos limpios de 35,7 a 2,7 % (abril a agosto, `docs/AUDIT_S150.md` y `project_s150_estado`,
  heredado): una sesión que aplique las 3 preguntas de MISSION puede frenarla por «suprimir categoría (b)».
- **CÓMO REPRODUCIRLO**: `sed -n 21,36p docs/MISSION.md`; `sed -n 1618,1619p CLAUDE.md`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 4. Tuerce el criterio con que se adopta lo que el operador verá publicado.

### F4-03. SIN MARCAR y CONTRADICTORIA: el veredicto de S27 que fundó el Test 1 sigue en pie en las puertas
- **ARCHIVO:LÍNEA**: `docs/MISSION.md:225-236` («Si encontrás que el literal puro pierde recall ...») y `:251`
  («A/B literal puro NO APROBADO»); `MEMORY.md:65` («S27 Test1 cierra D4 (recall 50→80 %)»);
  `feedback_mision_clon_mirova.md:34-40` (marcada en el índice como «REGLA TOP»: «El A/B literal puro NO APROBÓ
  ... recall cae 27.6 pp ... la metodología literal es correcta»); en el catálogo, las marcas S146 de
  `docs/MIROVA_DIVERGENCES.md:795` y `:840` («lo que cae es el respaldo bibliográfico, no el resultado empírico de
  S27») contra la marca S147 de `:2817-2826` del mismo archivo («La frase que sigue CAYÓ en S147 ... el "50 a
  80 %" no tiene instrumento ... SIN EVIDENCIA»).
- **QUÉ PASA**: dos cosas cayeron. S147 dejó el «50 a 80 %» sin evidencia y circular (marcado sólo en D30). S149
  (`docs/AUDIT_S149.md:31-35`) mostró que el «literal» contra el que S27 midió no tenía los Tests 2 y 3 del paper.
  **Lo comprobé**: el perfil `_mirova_literal` es de `db602040b` (2026-04-29) y la primera aparición de `def
  first_pass_tests_2_and_3` en `pipeline/` es `958a7a189` (2026-05-15), según `git log -S`. Ninguna de las dos
  caídas bajó a MISSION, al índice de memoria ni a la regla principal; y el catálogo se contradice consigo mismo.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. El Test 1 integrado sostiene la mayor parte de lo publicado en VIIRS
  375 (88,9 % según AUDIT_S149 §3, heredado; 77,89 % de los records según D30, `:2810`, heredado). Una sesión fría
  lee «el literal pierde recall» y defiende el detector propio con un resultado que no existe.
- **CÓMO REPRODUCIRLO**: `git log --format="%h %ad" --date=short -S "def first_pass_tests_2_and_3" -- pipeline | tail -1`;
  `git log -1 --format="%h %ad" --date=short db602040b`; `sed -n 786,797p docs/MIROVA_DIVERGENCES.md`.
- **CONFIANZA**: CONFIRMADO (fechas y líneas).
- **GRAVEDAD**: 3.

### F4-04. CONTRADICTORIA: el catálogo y `CLAUDE.md` dan por resuelto el cúmulo más cercano; Nicolás decidió la anomalía mayor
- **ARCHIVO:LÍNEA**: `docs/MIROVA_DIVERGENCES.md:1367` (encabezado «D8' Cluster selection Puyehue (S35)» seguido de «RESUELTO S38», separados en el original por un guion largo) y
  `:1374` («implementado `enable_vent_anchored_clustering` que selecciona el cluster más cercano al vent»);
  `CLAUDE.md:1081` (A85: «La selección de cluster vent-anchored es robusta»), `CLAUDE.md:158-161` («Fuera → far
  ... No se filtran, se clasifican»), `docs/MISSION.md:203-204`. Del otro lado: `docs/AUDIT_S150.md:152-158`
  («Regla de selección en la réplica: gana la anomalía MAYOR de la escena»).
- **QUÉ PASA**: MIROVA elige la anomalía térmica más energética de la escena, aunque a veces sea un incendio, y
  publicó 858 detecciones a una mediana de 20 km desde marzo (AUDIT_S150 §8, heredado). Producción elige el cúmulo
  más cercano al cráter: `ENABLE_VENT_ANCHORED_CLUSTERING = True` (leído con `pipeline.profile`); la alternativa
  existe (`pipeline/clustering.py:40` y `:55`, `strategy="vrp_max"`). La decisión no está en ninguna puerta salvo
  AUDIT_S150, y el documento de S124 que ya la planteaba (`docs/S124_SELECCION_CLUSTER_MAX_VS_VENT.md`) no lo cita
  ninguna puerta (`grep` sobre las siete: cero).
- **CÓMO SE VE EN EL DASHBOARD**: hoy, en el 29 % de los records con varios cúmulos el publicado es el más cercano y
  no el más energético (AUDIT_S150 §3, C-05, heredado).
- **CÓMO REPRODUCIRLO**: `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.ENABLE_VENT_ANCHORED_CLUSTERING)"`; `sed -n 1367,1375p docs/MIROVA_DIVERGENCES.md`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 3 (el A/B está pendiente; mientras tanto el catálogo dice «no hay nada que decidir»).

### F4-05. SIN MARCAR: el tope D9 de 5 MW «funciona», en cuatro lugares, y el tablero lo llama artefacto en una erupción
- **ARCHIVO:LÍNEA**: `CLAUDE.md:357` («el tope de magnitud ya está adoptado y funciona») y `:363` («el tope de 5 MW sí
  funciona (0 records sobre 5 MW)»); `CLAUDE.md:1785` y `docs/MISSION.md:105` («sólo el tope de 5 MW se confirma»);
  `docs/MIROVA_DIVERGENCES.md:222` (D9 sin estado en el encabezado y sin nada de S150);
  `frontend/index.html:1108-1110` («≥ 5, magnitud desconocida, probablemente artefacto»).
- **QUÉ PASA**: el tope se diseñó para cirrus frío y se arma con sólo tener el fondo bajo 270 K, sin que ningún píxel
  pase por temperatura ni por NTI (`PATH_D_ONLY_CAP_MW = 5.0`, `PATH_D_ONLY_CAP_TBG_MAX_K = 270.0`, leídos con
  `pipeline.profile`). S150 encontró que en Chillán ya recortó magnitudes de la erupción (AUDITOR_C C-01, **no pasó
  por el verificador**; AUDIT_S150 §2: «todavía no recortó ninguna alerta de MIROVA»).
  **Medición 2, `tope_d9_conteo.py`**: (1) si el tope recortara, lo vería por `primary_cluster.d9_capped` con
  `vrp_mw == 5.0`; no ve cuánto se cortó, porque el record no guarda el valor previo. (2) Control: el conteo es
  distinto de cero, así que la clave existe. Resultado sobre todo el corpus (65.206 records): **1.548 records con el
  tope, los 1.548 en 5,0 exacto**, casi todos MODIS; desde el 2026-09-28, 5 de Chillán, todos `far`. La frase «0
  records sobre 5 MW» es literalmente cierta (el tope los deja en 5,0) y no prueba que el tope sea inocuo.
- **CÓMO SE VE EN EL DASHBOARD**: con «Incluir lejanas», un valor de erupción recortado a 5,00 y rotulado
  «probablemente artefacto».
- **CÓMO REPRODUCIRLO**: `python experiments/_s150_meta_audit/F4/tope_d9_conteo.py`.
- **CONFIANZA**: CONFIRMADO que las puertas no tienen marca y el conteo; SOSPECHA heredada que lo recortado sea erupción.
- **GRAVEDAD**: 3.

### F4-06. SIN MARCAR y AUSENTE: lo que S147 a S150 midió de la conectiva, D21, D22, D25 y D12 no está en el catálogo
- **ARCHIVO:LÍNEA**: `docs/MIROVA_DIVERGENCES.md`, encabezados `:2526` (D21), `:2551` (D22), `:2602` (D25), `:1588`
  (D12); `grep -n "PROSE_BRANCH\|28,7\|86,1\|compens\|S149\|S150"` sobre el catálogo: la conectiva aparece sólo como
  «pieza» dentro de D26 (`:2663`), nunca como divergencia propia; los demás, cero.
- **QUÉ PASA**: lo que no bajó:
  - **Conectiva** (AUSENTE): es la palanca más grande medida en el proyecto (VIIRS 375, negativos limpios 29,8 a
    2,7 % en septiembre y 35,7 a 2,7 % de abril a agosto, heredado) y no tiene D. Producción usa `min`
    (`ENABLE_TESTS_23_PROSE_BRANCH = False`, leído con `pipeline.profile`).
  - **D21**: con banda 21, `max` apaga el detector MODIS (S147, `project_s147_estado`); con banda 22, en Láscar,
    MODIS separa: J 68 de 73 contra 11 de 96, K 67 de 73 contra 2 de 96 (`docs/S150_RESULTADO_MESES.md:55-56`,
    confirmado por `docs/audit_s150/VERIFICADOR_RESULTADO_MESES.md:57`).
  - **D22**: la compuerta de 3 K y el segundo pase sin condicionar se compensan, «se tocan juntas o no se tocan»
    (S148 H3, `project_s148_estado`); el A/B de D22 quedó SUSPENDIDO (#773); 15 de las 46 alertas débiles que `max`
    pierde las bloquea D22 (`project_s150_estado`, heredado de `docs/S150_ALERTAS_DEBILES_MAX.md`, sin verificador).
    La regla operativa «no condicionar el segundo pase sin sacar D22» vive sólo en la memoria de S148.
  - **D25**: sus dos veredictos de apagado cayeron (`docs/audit_s149/plan_final/FRENTE_D_VEREDICTOS_VIEJOS.md:169`,
    filas 20 y 23 de su tabla); el cuerpo de D25 sigue con el «premio cero en noches» de S145 y `MEMORY.md:42` y
    `:57` con «A/B D22/D25 ... NO ADOPTAR», sin marca.
  - **D12**: la etiqueta `far` no es la palanca en MODIS (78 % de los negativos limpios tienen la misma condición,
    AUDIT_S149 §3) y la erupción de Chillán lo repite (destapar la etiqueta destapa 22 de 28 pasadas de reposo,
    AUDIT_S150 §2). D12 sigue «CONGELADA EN S106/S108».
- **CÓMO SE VE EN EL DASHBOARD**: invisible hasta que alguien adopte algo. El riesgo concreto: adoptar `max` en los
  tres sensores (apaga MODIS con banda 21), o condicionar el segundo pase solo (cuesta 30 de 124 positivas V375,
  S148, heredado).
- **CÓMO REPRODUCIRLO**: `grep -n "S149\|S150\|PROSE_BRANCH" docs/MIROVA_DIVERGENCES.md`.
- **CONFIANZA**: CONFIRMADO para la ausencia; los números son heredados con su fuente.
- **GRAVEDAD**: 3.

### F4-07. CONTRADICTORIA y AUSENTE: la ficha de transparencia no describe lo que corre hoy
- **ARCHIVO:LÍNEA**: `docs/FICHA_SDA_VRP_CHILE.md:7` («Versión: v1.4», fechada 2026-08-30) contra su propio historial
  `:48` (v1.6, 2026-09-17); `:25` («La cuantificación de magnitud suma únicamente los píxeles del foco» y «se estima
  la temperatura de fondo local») contra su propia fila v1.6 `:48` («en lugar de un anillo regional de 5 a 25 km»,
  que es lo que corre) y contra `pipeline/single_pixel_mode.py:5-6` («reporta vrp_mw = max(per_pixel_vrp) ... en vez
  de la suma»), con `ENABLE_SINGLE_PIXEL_SUB_MW_MODE = True`, `SUB_MW_REGIME_THRESHOLD_MW = 5.0` y `SINGLE_PIXEL_MAX_CLUSTER_PIXELS = 3` (leídos con `pipeline.profile`); `:33` («un foco sub-píxel
  débil y el gradiente topográfico difuso son físicamente indistinguibles» a 1 km) contra la banda 22 que separa
  en Láscar (F4-06). `git log -- docs/FICHA_SDA_VRP_CHILE.md`: último cambio 2026-09-17 (#683).
- **QUÉ PASA**: desde v1.6 entraron, apagados, el fondo por vecinos en VIIRS 750 (#709), el Test 1 con estadístico
  corregido (S147) y la caja en el segundo pase (#738); en producción no cambió la detección, pero AUDIT_S149
  (`:114`, `:132`) pidió ponerla al día y no se hizo. Además falta lo que el operador y el público sí ven: que la
  magnitud bajo 5 MW es el píxel más fuerte y sobre 5 MW la suma (S150 C-03, **CONFIRMADO gravedad 4 por el
  verificador**, `docs/audit_s150/VERIFICADOR_AUDITORIA.md:18`: en Chillán VIIRS 750 se publicó 2,66, 11,08 y
  2,49 MW en 54 minutos), que el tope D9 censura en 5,0, y que el Test 1 integrado es un detector propio (D30 lo dejó
  pendiente para la ficha, `docs/MIROVA_DIVERGENCES.md:2838-2840`). Y la cabecera del módulo dice las dos cosas a la
  vez: `pipeline/test1_integrated.py:7` «Regla determinista (Coppola 2015 Eq.1)» y `:12` «DETECTOR PROPIO del
  proyecto, no del paper».
- **CÓMO SE VE EN EL DASHBOARD**: el salto de magnitud de C-03 sí se ve; la ficha publicable lo describe como suma.
- **CÓMO REPRODUCIRLO**: `sed -n 7p docs/FICHA_SDA_VRP_CHILE.md`; `sed -n 25p`; `grep -n "max(per_pixel" pipeline/single_pixel_mode.py`;
  `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.ENABLE_SINGLE_PIXEL_SUB_MW_MODE)"`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 3 (no tuerce una alerta; deja al SDA declarando una lógica que no es la que corre, Res. CPLT 372).

### F4-08. CONTRADICTORIA: A119 dice que ninguna alerta MODIS depende del OCR; hay cuatro
- **ARCHIVO:LÍNEA**: `CLAUDE.md:1494` («0 alertas MODIS dependen del OCR, medido S149») contra `docs/AUDIT_S149.md:50`
  («hay 2 de Láscar en marzo»). Mismo bloque: `CLAUDE.md:1492` y `:1502` («86 % en enero», «enero no se usa»),
  que AUDIT_S149 (`:45`) mandó rebajar porque el 86 % era Tupungatito ausente en el denominador (heredado del frente
  B). Y `scripts/calidad_referencia_mirova.py:18-27`: la lista HITOS no tiene la entrada de NOAA-21 en la tabla
  (2026-04-09, AUDIT_S149 §2), ni el defecto del OCR con la imagen de otra pasada (S150), ni el cambio de régimen del
  OCR por Mirova-v1#20, mergeado el 2026-10-09 14:01 UTC (`project_s150_estado`).
- **QUÉ PASA**: **Medición 3, `modis_alertas_solo_ocr.py`**: (1) cruza cada alerta MODIS nocturna del OCR contra
  alertas de la tabla del mismo volcán y sensor a ±30 min; si el OCR aportara alertas, las vería. (2) Control
  positivo: en VIIRS 375 da 261 de 751 (34,8 %) solo OCR, dentro del 20 a 39 % que la propia A119 declara; un
  instrumento muerto daría 0 o 100 %. Resultado: **4 de 33 alertas MODIS nocturnas del OCR no tienen alerta de tabla**
  (Láscar 2026-02-14, 03-04, 03-19, 04-18; VRP 2,0 a 3,0 MW redondeados, distancia 0,0 porque el OCR no la medía
  antes del 2026-06-13). Ventana: tabla 2026-01-10 a 2026-10-09, OCR 2026-01-20 a 2026-10-09 (snapshot local).
  Dos caen en el sustrato MODIS de la banda 22 (Láscar, marzo a junio).
- **CÓMO SE VE EN EL DASHBOARD**: invisible; afecta qué cuenta como positivo MODIS en los A/B.
- **CÓMO REPRODUCIRLO**: `python experiments/_s150_meta_audit/F4/modis_alertas_solo_ocr.py`.
- **CONFIANZA**: CONFIRMADO (medido). El «enero» es heredado.
- **GRAVEDAD**: 2 (A119 a) ya hace decidir a la tabla sola antes del 2026-06-13, lo que excluye las cuatro si se
  cumple; el riesgo es para quien confíe en «MODIS sin reparos»).

### F4-09. CONTRADICTORIA: D18 dice que arreglar el cableado de la caja requiere A45; `CLAUDE.md` y el código dicen que ya se arregló
- **ARCHIVO:LÍNEA**: `docs/MIROVA_DIVERGENCES.md:2258-2266` (marca S148: cita `pipeline/process_viirs.py:1313` y
  «Arreglarlo toca `pipeline/process_*.py` (A45: tag y confirmación de Nicolás)»); `CLAUDE.md:1466` («arreglado en
  S149»); código hoy: `pipeline/process_viirs.py:1320`, `pipeline/process_modis.py:930` con
  `roi1_summit_mask(vent_dist_per_pixel, inner_radius_km, _roi1_mask)`; guarda
  `tests/test_guard_caja_llega_al_segundo_pase_s149.py`; commit `0227dd7ac` (#738).
- **QUÉ PASA**: la marca de S148 envejeció: el encabezado de D18 sigue «NO ADOPTAR, prioridad baja», con la marca que
  dice que nunca se midió, pero nadie anotó que desde S149 ya **se puede** medir. Una sesión que lea sólo el catálogo
  puede reabrir el cableado.
- **CÓMO SE VE EN EL DASHBOARD**: invisible (flag apagado, `ENABLE_ROI1_BOX_PAPER = False`).
- **CÓMO REPRODUCIRLO**: `grep -n roi1_summit_mask pipeline/process_*.py`; `sed -n 2258,2266p docs/MIROVA_DIVERGENCES.md`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2.

### F4-10. SIN MARCAR: el cron «corre 12 veces al día»; entrega 4,83
- **ARCHIVO:LÍNEA**: `CLAUDE.md:570` (A45: «NRT cron corre 12 veces/día ... se replica a 132+ records»), `:607`,
  `:1546`, `:1687` («cron cada 2h»); `.github/workflows/nrt.yml:12` (`cron: "0 */2 * * *"`).
- **QUÉ PASA**: **Medición 4, `cron_entregado.py`**: (1) cuenta corridas `schedule` por día UTC; si GitHub entregara
  menos de 12, lo vería. (2) Control: la muestra trae además 5 `workflow_dispatch` contadas aparte; si `gh` no
  devolviera nada, el script dice SIN DATO. Resultado: del 2026-09-10 al 2026-10-02, **23 días, 111 corridas, 4,83
  por día**. Coincide con V-3 de AUDIT_S150 (`:125`). El remedio (cron externo `10 1-12 * * *`) está pendiente con
  Nicolás y no figura en ninguna puerta.
- **CÓMO SE VE EN EL DASHBOARD**: datos con 4 a 5 h de hueco en vez de 2 h; un operador que lea la documentación
  espera otra frescura.
- **CÓMO REPRODUCIRLO**: `python experiments/_s150_meta_audit/F4/cron_entregado.py`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2.

### F4-11. CONTRADICTORIA: la fecha del token en `CLAUDE.md` contra el registro de credenciales
- **ARCHIVO:LÍNEA**: `CLAUDE.md:1674-1675` («vence el 2026-10-03, se rota cada 50 días»); `tasks/BLOQUE_ARRANQUE_S150.md:67`, `:121`;
  `MEMORY.md:31` y `:36`. Del otro lado: `C:\Users\nmend\OneDrive\Escritorio\claude\REGISTRO_CREDENCIALES.md:28`
  («rotado ... 2026-10-08 18:07 UTC; vence 2026-12-07 18:03 UTC»).
- **QUÉ PASA**: el token se rotó; la puerta principal tiene la fecha vieja y sin marca.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. El hook nuevo de sesión avisa los días restantes (`project_s150_estado`).
- **CÓMO REPRODUCIRLO**: `sed -n 1674,1675p CLAUDE.md`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2.

### F4-12. SIN MARCAR: A94 «una noche sobre 946»
- **ARCHIVO:LÍNEA**: `CLAUDE.md:1226`; `MEMORY.md:110`.
- **QUÉ PASA**: AUDIT_S149 (`:48`) mostró que la unidad «noche, todos los sensores» escondía que en MODIS, por pasada,
  la etiqueta `far` oculta 68 de 77 alertas, y pidió marcarlo (`:124`). La lección de A94 (un caso no prioriza) sigue;
  el número, sin marca, sigue apagando MODIS como frente.
- **CÓMO SE VE EN EL DASHBOARD**: las pasadas MODIS ocultas como `far` (F4-01 trae un caso de Chillán).
- **CÓMO REPRODUCIRLO**: `sed -n 1221,1228p CLAUDE.md`.
- **CONFIANZA**: CONFIRMADO para la falta de marca; el 68 de 77 es heredado.
- **GRAVEDAD**: 2.

### F4-13. SIN MARCAR: A64 dice que el corte por host «devuelve lo de LAADS»
- **ARCHIVO:LÍNEA**: `CLAUDE.md:767`; código `pipeline/fetch.py:711-714` (`_DOWN_DOWNLOAD_HOSTS.update(hosts)` marca
  caídos todos los hosts del lote).
- **QUÉ PASA**: si un lote mezcla el L1B de LANCE con el GEO de LAADS y LANCE no responde, queda vetado también LAADS
  para el resto de la corrida (AUDIT_S150 A-13; a Llaima le faltaron las pasadas VIIRS del 2026-10-08 con el job
  verde, heredado). La regla dice lo contrario.
- **CÓMO SE VE EN EL DASHBOARD**: pasadas que faltan sin aviso hasta la corrida siguiente.
- **CÓMO REPRODUCIRLO**: `sed -n 696,716p pipeline/fetch.py`.
- **CONFIANZA**: CONFIRMADO (código leído).
- **GRAVEDAD**: 2.

### F4-14. AUSENTE: doce documentos de S147 a S150 no están en `docs/INDEX.md`
- **SCRIPT:SALIDA**: **Medición 5, `indice_cobertura.py`**: (1) busca el nombre de archivo de cada `.md` agregado en
  `docs/` desde el 2026-09-20; un doc citado con otro nombre cuenta como ausente (sesgo declarado). (2) Control
  positivo: AUDIT_S149.md y AUDIT_S150.md salen presentes. Resultado: **41 agregados, 2 en el índice, 39 ausentes**;
  de ellos 12 en la raíz de `docs/` (entre otros `S147_RESULTADO_AB_SIN_TEST1.md`, `S148_RESULTADO_AB_CONECTIVA.md`,
  `S149_COSTO_OCULTO_MAX.md`, `S150_RESULTADO_MESES.md`, `S150_ALERTAS_DEBILES_MAX.md`, `DISENO_SENSIBILIDAD_POR_ZONA_S147.md`,
  `PLAN_AUDITORIA_S150.md`). Los 27 de las subcarpetas se alcanzan desde AUDIT_S149 y AUDIT_S150; los de S147 y S148,
  que no tienen auditoría integral, sólo desde reglas sueltas de `CLAUDE.md`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2.

### F4-15. SIN MARCAR, menores
| cita | qué cambió | gravedad |
|---|---|---|
| `CLAUDE.md:1459` (A117: «Hoy el laboratorio es **idéntico** al operacional salvo el directorio») | #771 lo congeló con valores propios (`pipeline/profiles/experimental.yaml:63-69`, `tests/test_experimental_congelado_s150.py`); y `data/experimental_v2/` nunca se había commiteado (`project_s150_estado`) | 2 |
| `docs/MIROVA_DIVERGENCES.md:2156` (D17) | S147 midió que el remuestreo de MIROVA es interpolado y no borra picos reales (`docs/audit_s147/INFORME_TIF_QUE_VE_MIROVA.md:44-49`, «Toca D15, D17 y D18», `:106`); S150 lo propone como causa de lo que `max` pierde (hipótesis) | 2 |
| `docs/MIROVA_DIVERGENCES.md:2834-2836` (D30: «el brazo sin Test 1 ... va primero ... ABIERTA, descrita, sin decisión») y `MEMORY.md:36` («NO ADOPTAR porque apagarlo mueve el cumulo») | el A/B se corrió (S147, 86,1 a 28,7 %) y su NO ADOPTAR cayó (AUDIT_S149 §3, `:72-77`) | 3 |
| `docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md:75-95` («CONGELADA el 2026-09-14»), usada por `scripts/auto_audit_weekly.py:148` | Nicolás reabrió las metas (`docs/AUDIT_S150.md:161-163`) | 2 |
| `docs/AUDIT_S149.md:20-25` y `:89` («MODIS no discrimina, 11,7 % contra 11,5 %») | el verificador de S150 lo dejó MATIZADO: en Láscar producción publica 1 de 96 negativos (`docs/audit_s150/VERIFICADOR_RESULTADO_MESES.md:59` y `:21-22`) | 2 |
| `docs/AUDIT_S131.md:68` («111 FN, todos reales y sub-umbral») | AUDIT_S149 frente A H3: cerrados contra la regla de VIIRS del dueño | 2 |
| `MEMORY.md:141` («catálogo vivo (abiertas D2, D3, cara-posición D11, D12 congelada)») | hoy hay D13 a D32 abiertas; anterior al tramo pero en una puerta | 2 |
| `MEMORY.md` mide 143 líneas contra su propio tope de 140 | regla del índice | 1 |

## 3. Decisiones de Nicolás de S147 a S150, y dónde las leería una sesión fría

| decisión (fuente) | CLAUDE.md | MISSION | catálogo | último bloque | INDEX | MEMORY.md |
|---|---|---|---|---|---|---|
| La réplica se MIDE contra la base de MIROVA (S147) | sí, A115 `:1429` | no | no | sí, `:110-111` | no | sí, `:36` |
| Paridad en los dos sentidos (S149) | **contradice** `:1619` | **contradice** `:21-36` | no | no | sí (fila AUDIT_S149) | sólo en el archivo de detalle |
| VIIRS captura todo; el corte de 0,5 MW es sólo MODIS (S149) | no | no | no | no | no | sí, `:72` |
| Metas de la tabla del 2026-09-14 reabiertas (S150) | no | no | no | no | no | no |
| Reprocesar desde el 2026-01-29 y marcar el régimen el día de la adopción (S150) | no | no | no | no | no | no |
| Réplica con la anomalía MAYOR (S150) | **contradice** A85 `:1081` | **contradice** `:203-204` | **contradice** D8' `:1367` | no | no | no |
| Experimental congelado en la producción de hoy (S150, #771) | desactualizado A117 `:1459` | no | no | desactualizado `:136` | no | no |
| Prueba de Chillán, despachar desde el 2026-10-13 (S150) | no | no | no | no | sí (fila AUDIT_S150) | no |
| Línea de MIROVA del tablero con OCR (S150, #767) | sí, cita G8 `:243` | no aplica | no aplica | no | sí (fila AUDIT_S150) | no |

## 4. MARCADA (lo que sí se propagó, para no volver a mirarlo)

1. `CLAUDE.md:228` A10 rebajada en S147, con puntero a D32 y al verificador.
2. `CLAUDE.md:1466` A118, «arreglado en S149», con guarda citada.
3. `CLAUDE.md:243` cita de `isValidDetection` remapeada a la l. 1473 tras #767.
4. `CLAUDE.md:1403-1418` A114: deja escrito que S130 midió la caja con el Test 1 encendido.
5. `docs/MIROVA_DIVERGENCES.md:2254-2266` D18, marca S148 sobre el NO ADOPTAR de S130 (envejecida, F4-09).
6. `docs/MIROVA_DIVERGENCES.md:2817-2826` D30, marca S147 sobre el «50 a 80 %».
7. `docs/MIROVA_DIVERGENCES.md:873` tabla sin instrumento, S147.
8. `docs/MIROVA_DIVERGENCES.md:2904` D32 registrada en S147.
9. `tasks/BLOQUE_ARRANQUE_S150.md:30-42`: #738 mergeado y test con fuga resuelto, «manda sobre lo de abajo».
10. `tasks/BLOQUE_ARRANQUE_S150.md:9-28`: A119 y pre-registro v3, «manda sobre todo lo de abajo».
11. `docs/S150_RESULTADO_MESES.md:42`, `:124`, `:132` y `docs/S150_IMAGENES_SNPP.md:7-13`: corrección de las cinco de Suomi NPP.
12. `docs/AUDIT_S150.md:47`, `:50`, `:96`: «HECHO S150» en las familias 1 y 4.
13. `MEMORY.md:72`: la regla de VIIRS del dueño, corregida tras S149.

## 5. Lo que este frente no cubrió

- Los informes de `docs/audit_s147` a `docs/audit_s150` se leyeron por búsqueda dirigida, no enteros.
- No verifiqué los números heredados de AUDIT_S149 y AUDIT_S150 salvo los que digo «medido»: el 88,9 % del Test 1, el
  68 de 77, el 78 %, el 29 % de C-05, el 22 de 28 y la causa de los recortes del tope son de esos informes.
- No miré `docs/META_RULES_S80.md`, `docs/HYPOTHESIS_LOG.md` ni los `project_sNN_estado.md` anteriores a S147.
- No abrí el tablero en un navegador.
- El buscador por patrón no ve paráfrasis: los conteos de la sección 0 son un piso.

## 6. VERIFICADO LIMPIO

| qué | cómo se confirma |
|---|---|
| La caja de 5 × 5 km llega a los dos pases en los tres procesadores (el arreglo de A118 existe en el código) | `grep -n roi1_summit_mask pipeline/process_*.py` (VIIRS `:1180`, `:1320`; MODIS `:791`, `:930`) y `gh pr view 738 --json state` (MERGED) |
| Los flags que la ficha nombra como apagados lo están en producción | `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.ENABLE_TEST1_NTI_INTEGRAL, p.ENABLE_EXCLUDE_ZONES)"` da `False False` |
| Los flags de las alternativas de S142 a S149 siguen apagados en producción | mismo método: `ENABLE_TESTS_23_PROSE_BRANCH`, `ENABLE_MODIS_B22_PRIMARY`, `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375`, `..._VIIRS750`, `ENABLE_TEST1_NULL_CORRECTED`, `ENABLE_ROI1_BOX_PAPER`, `ENABLE_TESTS_23_NO_BT_GATE_VIIRS375`, `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER`: todos `False` |
| El experimental está congelado y tiene su guarda | `pipeline/profiles/experimental.yaml:63-69`; `tests/test_experimental_congelado_s150.py` existe; `VRP_PROFILE=experimental` da `DATA_SUBDIR experimental_v2` y los mismos valores de conectiva, Test 1 y banda |
| `nrt.yml` fijado en `ubuntu-24.04` (decisión 4 de AUDIT_S150) | `grep -n runs-on .github/workflows/nrt.yml` |
| La corrección de Suomi NPP está marcada en sus dos documentos fuente | `sed -n 1,13p docs/S150_IMAGENES_SNPP.md`; `sed -n 120,135p docs/S150_RESULTADO_MESES.md` |
| AUDIT_S149 y AUDIT_S150 están en `docs/INDEX.md` y la fila de S150 nombra la erupción y la prueba | `sed -n 21,22p docs/INDEX.md` |
| A10 y A118 en `CLAUDE.md` llevan su marca | `python experiments/_s150_meta_audit/F4/propagacion_grep.py` (controles positivos) |
| `REGISTRO_CREDENCIALES.md` tiene la fecha nueva del token | `sed -n 28p C:\Users\nmend\OneDrive\Escritorio\claude\REGISTRO_CREDENCIALES.md` |
