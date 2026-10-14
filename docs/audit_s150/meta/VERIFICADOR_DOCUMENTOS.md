# Verificador con contexto limpio: propagación de S147 a S150 a los documentos de entrada

> 2026-10-09. En las citas textuales, cada guion largo del original va escrito como «[guion largo]». `main` y `origin/main` en `13f5bb0dd`. Solo lectura sobre el repo; los únicos archivos que escribí
> son este informe y tres scripts en
> `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s150_meta_audit\verif_docs\`
> (`contar_topados_d9.py`, `topados_detalle.py`, `alcance_single_pixel.py`). Formé el juicio de P1 a P7 antes de
> abrir `AUDITOR_F4_PROPAGACION.md` y `AUDITOR_F1_PENDIENTES.md`; lo que tomé de ellos después va marcado
> **heredado**. Los flags se leyeron con `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p ..."`,
> nunca del YAML.

## 0. Resumen

| P | veredicto | gravedad mía | una línea |
|---|---|---|---|
| P1 | CONFIRMADO, con un matiz | 4 | el bloque de arranque más nuevo es el escrito en S149; el índice de memoria da el NRT caído y #738 esperando, ambos falsos hoy. El detalle (`project_s150_estado.md`) sí está al día |
| P2 | PARCIAL | 4 (MISSION) / 2 (glosario) | MISSION:21-36 choca de frente y sin marca; el glosario de CLAUDE.md:1619 no está caído sino incompleto (Nicolás el 2026-10-08: «si MIROVA lo lee, nosotros también») |
| P3 | CONFIRMADO | 4 | MISSION:225-251, MEMORY.md:65 y la regla TOP de la memoria sin marca; el «literal» de S27 no tenía ETI ni Test 1; el catálogo se contradice entre :795/:840 y :2817 |
| P4 | CONFIRMADO para D8', PARCIAL para A85 y MISSION:204 | 4 / 2 | D8' «RESUELTO S38» dice que MIROVA NO elige por `vrp_mw`; A85 y MISSION:204 hablan de cercas, no de la regla de selección |
| P5 | CONFIRMADO, y peor en un punto | 3 | 1.548 records topados (todos con `d9_capped`); además «0 records sobre 5 MW» es falso como enunciado general: hay 338 con `pc.vrp_mw > 5` |
| P6 | CONFIRMADO | 3 | v1.4 en la cabecera con historial a v1.6; la l. 25 describe suma y fondo local, y el modo de un píxel está activo en 32.150 de 42.574 records con cúmulo |
| P7 | CONFIRMADO, ruta equivocada | 2 | el archivo es `experiments\_s149_prereg_invierno\evaluar_ventana.py`, no `scripts\`; DEVNULL en l. 60 y 86 se traga el aviso de A119; HITOS sin NOAA-21 ni Suomi NPP |

Hallazgos propios en §8.

---

## P1. Una sesión fría no se entera de S150

**Lo que verifiqué.**

- VERIFICADO: `ls tasks/BLOQUE_ARRANQUE_S*.md | sort -V | tail -1` da `tasks/BLOQUE_ARRANQUE_S150.md`. Su l. 3 dice
  «Estado de S149 (2026-09-21 ...)». Último commit que lo tocó: `65550cf51` del 2026-09-21. No existe un bloque S151.
- VERIFICADO: entre el 2026-10-03 y hoy entraron 17 PR de S150 que no son automáticos (`git log origin/main
  --since=2026-09-22`, de #755 a #775). El bloque no menciona ninguno. Sus l. 67 y 121 dicen «el token vence el
  2026-10-03».
- VERIFICADO: `gh pr view 738` da `MERGED`, 2026-09-21T12:27:52Z, merge `0227dd7ac`.
- VERIFICADO: `gh run list --workflow nrt.yml --limit 6` da las 4 últimas en `success` (la última, 2026-10-09
  12:36 UTC) y dos `failure` el 2026-10-08 (08:26 y 17:11, antes de la rotación del token a las 18:07 según
  `project_s150_estado.md:27`).

**Texto exacto que hoy está** (`C:\Users\nmend\.claude\projects\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\memory\MEMORY.md`):

- l. 29: `## 🔴 Estado vivo: S150 EN CURSO [project_s150_estado]. S149 en [project_s149_estado]`
- l. 31: `**S150 (2026-10-03/04)** [project_s150_estado]: TOKEN EARTHDATA VENCIDO, NRT caido desde 10-03 07:36 UTC. ... 5 perdidas fuertes con firma Suomi NPP+OCR+borde (mirar imagenes MIROVA). ... Abril espera Chaiten (token).`
- l. 33: `... Cableado de la caja en PR #738, CI verde, ESPERA el si de Nicolas (A45). Pre-registro v2 verificado y SIN despachar ...`

Tres afirmaciones de esas líneas cayeron: el token se rotó el 2026-10-08 (vence 2026-12-07, `project_s150_estado.md:27`)
y el NRT está verde; abril quedó evaluado (#761, 2026-10-08); las cinco «pérdidas fuertes» resultaron filas del OCR
con la imagen de otra pasada (#764, #774). Y #738 está mergeado desde el 21 de septiembre.

**Caminos por los que podría estar mal, y qué encontré.**

1. *Que S150 siga en curso*: es así (hay commits de hoy), y por eso no puede haber un bloque S151 todavía. El defecto
   no es que falte el S151, es que el índice que se carga solo describe la mitad de la sesión que ya pasó. Si el loop
   arranca antes de un `/cierre`, lee eso.
2. *Que el detalle lo corrija*: `project_s150_estado.md` (13:47 de hoy) sí trae la rotación, el NRT verde y la prueba
   de Chillán. Una sesión que siga el puntero se entera; una que se quede con el índice, no.
3. *Que un hook lo cubra*: VERIFICADO que `~/.claude/hooks/check_alertas_vrp.py` está registrado en `SessionStart`
   (`~/.claude/settings.json:43`). Cubre el estado del token y del NRT, no las decisiones (anomalía mayor, prueba de
   Chillán del 2026-10-13, experimental congelado).

**Gravedad 4.** Lo que más tuerce no es el NRT (el hook lo corrige al arrancar) sino que la prueba con fecha sobre
un volcán en erupción y las decisiones del dueño no están en ninguna puerta que se cargue sola.

**Propuesta de marca (A113).** En `MEMORY.md`, al inicio de la l. 31: `⚠️ CORREGIDO 2026-10-09 (verificador
docs S150): token ROTADO el 10-08 (vence 2026-12-07), NRT verde; abril evaluado (#761); las 5 "perdidas fuertes"
son filas OCR con imagen de otra pasada (#764, #774). Texto original:`. Al inicio de la l. 33: `⚠️ #738 MERGEADO
2026-09-21 (0227dd7ac). Texto original:`. Y que el `/cierre` de S150 escriba `tasks/BLOQUE_ARRANQUE_S151.md` con la
prueba de Chillán (desde el 2026-10-13) y las decisiones del 2026-10-09 arriba de todo.

---

## P2. La paridad en dos sentidos contra MISSION y el glosario

**Texto exacto que hoy está.**

- `docs/MISSION.md:21-36` (último commit del archivo: `5167951c2`, 2026-09-20, o sea S146; nada de S147 a S150):
  «**Objetivo (2) [guion largo] Extensión volcánica documentada** (SECUNDARIO reporte). Reportar las detecciones que el
  algoritmo Coppola 2016a captura pero que MIROVA NRT no publica ... Reportar (2) honestamente como valor agregado
  SERNAGEOMIN [guion largo] no eliminarlo.» y «**Importante**: el algoritmo de detección es ÚNICO ... La distinción (1) vs (2)
  vive en el campo derivado `pc.classification` ... No se introducen gates adicionales para "limpiar" (2).»
- `CLAUDE.md:1618-1619`: «**Recall** = TP / (TP+FN). De lo real, cuánto detectamos. Baja = perdemos eventos.
  **Para `mirova_equivalent` priorizamos recall sobre precision**.»

VERIFICADO: `grep -n "S14[7-9]\|S150\|experimental" docs/MISSION.md` no da ninguna línea de S147 a S150 ni una sola
mención del perfil experimental.

**Del otro lado.** `feedback_mirova_equivalent_priorities.md:66-71` (memoria) registra la «Decision S149 (2026-09-21):
PARIDAD EN LOS DOS SENTIDOS ... lo extra va al experimental» y nombra la contradicción con el glosario.
`docs/AUDIT_S149.md:13` y `docs/PLAN_AUDITORIA_S150.md:23` la repiten.

**Caminos por los que podría estar mal.**

1. *Que «no se introducen gates» no alcance a lo que se quiere adoptar*: la conectiva `max` no es un gate propio,
   es la lectura literal de la Tabla 1; una sesión podría adoptarla sin chocar con MISSION. Pero la frase
   «la distinción (1) vs (2) vive en `pc.classification`» sí choca: dice que (2) se publica en el mismo perfil
   clasificada, y la decisión dice que (2) va a otro perfil. **El choque es real.**
2. *Que el glosario esté caído*: no lo está del todo. `project_s150_estado.md:35` registra a Nicolás el 2026-10-08:
   «(6) NO acepta perder senales: si MIROVA lo lee, nosotros tambien». Eso es «recall primero» respecto de MIROVA.
   Lo que falta en la l. 1619 es la otra mitad (callar donde MIROVA calla) y el alcance (recall **contra MIROVA**,
   no contra todo lo físicamente real). Y la memoria tiene dos formulaciones que no son iguales: S149 «minimiza la
   suma de los dos errores» y S143 (`feedback_s143_primero_igualar_a_mirova.md:27`) «La sobre-publicación y la
   magnitud se optimizan **después**». **La tensión entre ellas no la resolvió nadie**; la marca tiene que decirlo,
   no elegir.

**Gravedad**: 4 para MISSION (es la puerta de las 3 preguntas: una sesión que la aplique puede frenar `max` por
«suprimir categoría (b)»); 2 para el glosario (incompleto, no falso).

**Propuesta de marca.** Al inicio de `docs/MISSION.md:21` (antes de «**Objetivo (2)**»): `⚠️ **Rebajada S147-S149
(decisión de Nicolás 2026-09-21, registrada en docs/AUDIT_S149.md:13 y en la memoria
feedback_mirova_equivalent_priorities.md): la réplica `mirova_equivalent` publica lo que MIROVA publica y calla
donde MIROVA calla; el objetivo (2) ya no vive en la réplica clasificado por `pc.classification`, sino en el perfil
`experimental` (congelado en la producción del 2026-10-09, PR #771). Sigue en pie, y manda donde choque, que una
alerta que MIROVA publicó y nosotros no abre investigación (Nicolás, 2026-10-08). Texto original conservado por
historia:**`. En `CLAUDE.md:1619`, después de la frase: `⚠️ (S149/S150) recall CONTRA MIROVA, y en los dos
sentidos: callar donde MIROVA calla también es parte de la réplica; perder una alerta de MIROVA no se acepta
(Nicolás 2026-10-08). La forma de combinar los dos errores (suma mínima, S149, o recall primero, S143) no está
decidida.`

---

## P3. El veredicto de S27 sigue en pie

**Lo que verifiqué.**

- VERIFICADO: `git log --reverse -S "first_pass_tests_2_and_3" -- pipeline/` da como primer commit `958a7a189`,
  2026-05-15 07:40 (S46). `git log -S "mirova_literal" -- pipeline/profiles` da `db602040b`, 2026-04-29 00:17
  («S27 T2 [guion largo] profile _mirova_literal»). Diferencia: 16 días.
- VERIFICADO (más fuerte que la afirmación): en el árbol de `db602040b`, `git grep -iE "\beti\b|regres|quadratic"
  -- pipeline/*.py` no encuentra ni el ETI ni su regresión cuadrática, y el perfil `_mirova_literal.yaml` de ese commit
  tiene `enable_test1_path: false` (l. 124). Sí había un dNTI contextual de 8 vecinos (`enable_dnti_contextual_path:
  true`, l. 118, con «median(8 vecinos)» en el comentario de la l. 77) y la compuerta de BT dual-ROI de 5/10 σ
  (l. 128), que S146 V-08 mostró que no está en la Tabla 1. **Matiz**: decir «no tenía los Tests 2 y 3» es
  aproximado; tenía una versión del contraste de NTI sin el ETI, y no tenía el Test 1. En cualquier caso no era el
  literal.

**Texto exacto que hoy está.**

- `docs/MISSION.md:225`: «## Si encontrás que el literal puro pierde recall»; `:231`: «Hipótesis abiertas (S28+,
  ver `~memory/project_s27_mirova_literal_negativo.md`):»; `:232`: «- H_S27_1: Test 1 summit-only más agresivo
  (Coppola 2016a SP426.5 §2.2 Eq.1).»; `:251`: «- A/B literal puro NO APROBADO:
  `~memory/project_s27_mirova_literal_negativo.md`». Sin marca.
- `MEMORY.md:65`: «S75 Aveni · S73 saturation guard · ... · **S27 Test1 cierra D4 (recall 50→80 %)** · ...». Sin marca.
- `feedback_mision_clon_mirova.md:34-38`: «S27 demolió la mayoría de esos parches ... El A/B literal puro NO APROBÓ
  operacionalmente (recall cae 27.6 pp), pero la magnitud calibró perfectamente (70× → 1.35×) [guion largo] señal de que la
  metodología literal es correcta ...». Sin marca, y el índice la llama «REGLA TOP».
- `docs/MIROVA_DIVERGENCES.md:795` (marca S146 de H_S27_1): «... Nada de lo medido en el bloque cambia: lo que cae es
  el respaldo bibliográfico, no el resultado empírico de S27.»; `:840`: «Nada de lo medido abajo cambia: lo que cae
  es el respaldo bibliográfico, no el resultado empírico de S27.»
- Contra eso, `:2817-2828` (marca S147 dentro de D30): «**La frase que sigue CAYÓ en S147** (...
  `docs/audit_s147/VERIFICADOR_H_A01.md` ...): (a) el "50 a 80 %" **no tiene instrumento** ... queda **SIN
  EVIDENCIA** ... (b) la medición **sí es circular** ... (c) el único A/B limpio del Test 1 ... dio **6 contra 6**».

**Caminos por los que podría estar mal.** (1) Que la marca de :2817 cubra a las de :795 y :840: no, está mil líneas
más abajo, en otra D, y las de :795/:840 afirman lo contrario en presente. (2) Que el «recall cae 27,6 pp» de S27 se
refiera a otra cosa que el «50→80 %»: son dos números del mismo A/B; los dos se midieron contra un literal sin ETI ni
Test 1, y el segundo además con una etiqueta circular. (3) Que `project_s27_mirova_literal_negativo.md` lleve marca:
no lo abrí; queda SIN VERIFICAR.

**Gravedad 4** (el auditor puso 3). Una sesión fría lee «el literal pierde recall» en la puerta de las 3 preguntas
y en la regla TOP, y defiende el Test 1 integrado, que es un detector propio (D30) y el camino que más publica en
VIIRS 375, con un resultado que no tiene instrumento.

**Propuesta de marca.** En `docs/MISSION.md:225`, bajo el título: `⚠️ **Rebajada S147/S149**: el A/B de S27 midió
contra un perfil (`db602040b`, 2026-04-29) sin el ETI ni el Test 1; los Tests 2 y 3 con ETI entraron al código el
2026-05-15 (`958a7a189`). El «recall 50 a 80 %» quedó SIN EVIDENCIA y circular (docs/audit_s147/VERIFICADOR_H_A01.md;
docs/MIROVA_DIVERGENCES.md D30). «El literal pierde recall» no está medido. Texto original por historia:`. La misma
marca, abreviada, en `:251`, en `MEMORY.md:65` (tras «recall 50→80 %»: `⚠️ SIN EVIDENCIA, S147`) y al inicio de
`feedback_mision_clon_mirova.md:34`. En `docs/MIROVA_DIVERGENCES.md:795` y `:840`, cambiar el sentido con una marca
encima: `⚠️ S147: también cayó el resultado empírico (ver la marca de D30, l. 2817); esta frase se conserva por
historia.`

---

## P4. La anomalía mayor contra D8', A85 y MISSION:204

**Lo que verifiqué.**

- VERIFICADO: la decisión está sólo en `docs/AUDIT_S150.md` (commit `a9ac28cfa`, PR #772): «**Regla de selección en
  la réplica: gana la anomalía MAYOR de la escena**, como MIROVA ... Producción hoy hace lo contrario:
  `enable_vent_anchored_clustering: true` ... **Pendiente: A/B con pre-registro** (`vent_anchored` contra `vrp_max`)».
- VERIFICADO: `ENABLE_VENT_ANCHORED_CLUSTERING = True` leído de `pipeline.profile`.
- VERIFICADO: `grep -n -i "vrp_max\|anomal.a mayor" docs/MIROVA_DIVERGENCES.md CLAUDE.md docs/MISSION.md` no da
  ninguna línea.

**Texto exacto que hoy está.**

- `docs/MIROVA_DIVERGENCES.md:1367`: encabezado de D8' (Cluster selection Puyehue, S35), «RESUELTO S38».
- `:1371`: «Hipótesis: criterio de selección MIROVA es proximity-al-vent o anomaly-score-relativo, no `vrp_mw desc`
  ni `n_pixels desc` como hacía `pipeline/clustering.py`.»
- `:1373`: «**Resolución S38**: implementado `enable_vent_anchored_clustering` que selecciona el cluster más cercano
  al vent_lat/lon como `primary_cluster`.»
- `docs/MISSION.md:116-117`: «Resueltas (no justifican features nuevas): ... D8/D8' cluster selection (S38/S62)».
  La marca S146 de la l. 99 dice que «**D8** sigue vigente por la vía del fondo de anillo», pero no toca D8'.
- `CLAUDE.md:1081-1083` (A85): «**La selección de cluster vent-anchored es robusta a píxeles extra-radio; una cerca
  geométrica que "protege" la selección es carga sin beneficio** ...».
- `docs/MISSION.md:203-204`: «la selección de cluster vent-anchored es robusta a los píxeles extra-radio por sí sola».

**Caminos por los que podría estar mal.**

1. *Que la decisión no sea adopción*: es cierto, está pendiente de A/B. Por eso la marca no puede decir «cayó D8'»;
   tiene que decir que el criterio de D8' (MIROVA no elige por magnitud) está en duda y que el A/B está decidido.
   Lo que sí cae de D8' es su hipótesis sobre MIROVA, que contradice la observación de S150 (858 detecciones a una
   mediana de 20 km; **heredado**, no lo recomprobé).
2. *Que A85 y MISSION:204 choquen*: sólo en parte. Ambas hablan de **cercas** alrededor de la selección, no de la
   regla de selección. Pero miden el éxito como «0 robos de cluster»: bajo la anomalía mayor, que un cúmulo lejano
   más fuerte gane es fidelidad, no robo. Una sesión que use A85 como vara del A/B lo leería al revés.
3. *Que D8' sea la única puerta*: es la peor, porque está en la lista de «Resueltas (no justifican features
   nuevas)» de MISSION:116 y una sesión que aplique anti-A8 descarta el A/B.

**Gravedad**: 4 para D8' y MISSION:116-117; 2 para A85 y MISSION:204.

**Propuesta de marca.** Encima de `docs/MIROVA_DIVERGENCES.md:1367`: `⚠️ **Reabierta como pregunta S150
(decisión de Nicolás 2026-10-09, docs/AUDIT_S150.md §8)**: la réplica debe elegir la anomalía MAYOR de la escena,
como MIROVA; la hipótesis de esta entrada («MIROVA no elige por vrp_mw») contradice las 858 detecciones lejanas que
MIROVA publicó desde marzo. Producción sigue en vent_anchored hasta el A/B pre-registrado vent_anchored contra
vrp_max (pendiente, después de D22 y Chillán). Texto original por historia:`. En `docs/MISSION.md:117`, después de
«D8/D8' cluster selection (S38/S62)»: `⚠️ D8' reabierta S150, ver el catálogo`. En A85 (`CLAUDE.md:1077`), una
línea: `⚠️ S150: bajo la regla de la anomalía mayor (decidida, A/B pendiente) un cúmulo lejano que gana no es robo;
«0 robos» deja de ser la vara.`

---

## P5. El tope D9 «funciona»

**Medición** (`contar_topados_d9.py` y `topados_detalle.py`). Las dos preguntas del instrumento: (1) si el tope
recortara, el valor quedaría en 5,0 exacto, y lo cuento en `vrp_mw`, `primary_cluster.vrp_mw` y `f5_core_vrp_mw`; un
valor medido que caiga en 5,000000 por azar es despreciable. (2) Control: cruzo con la marca
`primary_cluster.d9_capped`, que el pipeline escribe desde S71 (`84c7d312e`): si el conteo por valor midiera otra
cosa, no coincidiría.

VERIFICADO, sobre `data/mirova_equivalent/*.json`, **65.206 records, ventana 2025-02-15 01:40 a 2026-10-09 08:45**:

| conteo | n |
|---|---|
| `primary_cluster.vrp_mw == 5,0` | **1.548** (MODIS 1.512, VIIRS 750 36, VIIRS 375 0) |
| de ellos con `d9_capped = True` | 1.548 de 1.548 (y no hay ningún `d9_capped` fuera de esos) |
| de ellos `distance_class = summit` | 275 (1.273 `far`) |
| `record.vrp_mw == 5,0` (suma de escena) | 6.524 |
| `f5_core_vrp_mw == 5,0` | 0 |
| **`primary_cluster.vrp_mw > 5,0`** | **338** (105 `summit`; MODIS 256, VIIRS 750 77, VIIRS 375 5) |

**Texto exacto que hoy está.**

- `CLAUDE.md:356-357` (A23): «... el tope de magnitud ya está adoptado y funciona; lo único vivo es la co-validación».
- `CLAUDE.md:363`: «... el tope de 5 MW sí funciona (0 records sobre 5 MW).»
- `CLAUDE.md:1785`: «... sólo el tope de 5 MW se confirma.»
- `docs/MISSION.md:105`: «lo que sí se confirma es el tope de 5 MW y los denominadores 199 `far` / 214 `summit`».
- `frontend/index.html:1108-1110`: «Valor CENSURADO, no medido ... Significa «≥ 5, magnitud desconocida, probablemente
  artefacto», no «5,0 MW medidos».»

**Caminos por los que podría estar mal.**

1. *Que «0 records sobre 5 MW» hable de la población de D9 (214 summit de junio)*: probablemente sí, y en esa
   población es tautológico (el tope deja todo en 5,0). Pero escrito así, sin población ni ventana, una sesión fría
   lo lee como hecho del corpus, y en el corpus de hoy hay 338 cúmulos sobre 5 MW. Es A90.
2. *Que «funciona» esté mal*: el recorte ocurre, eso sí funciona. Lo que no está medido es si lo recortado es
   artefacto. S146 C-02 (`docs/AUDIT_S146.md:90`) ya dejó escrito que el «no es parche» del tope no lo sostiene el
   paper, y eso no bajó a ninguna de las cuatro citas. Y bajo «callar donde MIROVA calla», publicar 275 cúmulos
   summit en 5,00 rotulados «probablemente artefacto» es lo contrario de callar.
3. *Que lo recortado sea erupción de Chillán*: no lo comprobé (SIN VERIFICAR; el auditor lo da como sospecha heredada).

**Gravedad 3.**

**Propuesta de marca.** En `CLAUDE.md:357`, `:363`, `:1785` y `docs/MISSION.md:105`: `⚠️ S150: «funciona» sólo
quiere decir que recorta. No está medido que lo recortado sea artefacto (S146 C-02: el paper no lo sostiene). Corpus
al 2026-10-09: 1.548 cúmulos topados en 5,0 exacto (275 summit, todos con primary_cluster.d9_capped), y 338 cúmulos
SOBRE 5 MW, así que «0 records sobre 5 MW» vale sólo para la población de S113. Script:
experiments/_s150_meta_audit/verif_docs/contar_topados_d9.py.`

---

## P6. La ficha SDA

**Texto exacto que hoy está.**

- `docs/FICHA_SDA_VRP_CHILE.md:7`: «**Identificador interno:** VRP-CL · **Versión:** v1.4 (2026-08-30) · **Estado:**
  producción (NRT)» (en el original el separador de la fecha es un guion largo).
- `:48`: fila `| v1.6 | 2026-09-17 | ...` y `:49` `| v1.5 | 2026-09-02 | ...`. La cabecera quedó dos versiones atrás.
- `:25`: «Sobre cada escena satelital se identifican píxeles "calientes", se estima la temperatura de fondo local y se
  calcula la Potencia Radiada Volcánica ... La cuantificación de magnitud suma únicamente los píxeles del foco térmico
  contextualmente anómalo ...».
- Contra la l. 25, la propia fila v1.6 (`:48`) dice que el fondo de producción es «un anillo regional de 5 a 25 km».

**Lo que verifiqué** (flags de `pipeline.profile`): `BG_INNER_KM = 5.0`, `BG_OUTER_KM = 25.0`,
`ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375 = False`, `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750 = False`,
`ENABLE_SINGLE_PIXEL_SUB_MW_MODE = True`, `SINGLE_PIXEL_MAX_CLUSTER_PIXELS = 3`, `ENABLE_LOCAL_KERNEL_BG = True`.
`pipeline/single_pixel_mode.py:5-6`: «reporta vrp_mw = max(per_pixel_vrp) (pixel mas caliente) en vez de la suma del
cluster». Medido con `alcance_single_pixel.py`: **32.150 de 42.574 records con cúmulo (75,5 %)** llevan
`single_pixel_mode = True`.

**Caminos por los que podría estar mal.**

1. *«Fondo local»*: no es falso del todo. `ENABLE_LOCAL_KERNEL_BG = True` y en `volcanoes.yaml` hay 5 entradas con
   `local_kernel_bg: true` (l. 54, 89, 523, 623, 661; A89 dice que son 5 de los 11 Tier A). En los otros seis el fondo
   es el anillo regional. La ficha generaliza lo de cinco volcanes a todos.
2. *«Suma»*: el modo de un píxel sólo cambia el valor cuando el cúmulo tiene de 2 a 3 píxeles bajo el umbral; en un
   cúmulo de un píxel suma y máximo son lo mismo. Pero está activo en tres de cada cuatro records y, por arriba del
   umbral, vuelve la suma: la magnitud publicada cambia de regla con el valor, y la ficha no lo dice.

**Gravedad 3** (no tuerce una alerta; deja a un SDA bajo la Res. CPLT 372 declarando una lógica que no es la que corre).

**Propuesta de marca.** En `:7`: subir a la versión vigente (v1.6, o v1.7 con esta corrección). En `:25`, al inicio
del pasaje: `⚠️ Corrección pendiente (verificador S150): en producción el fondo de la magnitud es el anillo regional
de 5 a 25 km salvo en los volcanes con kernel local; y bajo el régimen sub-MW la magnitud es la del píxel más caliente
del cúmulo (hasta 3 píxeles), no la suma (modo activo en 75,5 % de los records con cúmulo, 2026-10-09). Texto
original:`.

---

## P7. El aviso de A119 se pierde, y faltan hitos

**Lo que verifiqué.**

- VERIFICADO: `scripts\evaluar_ventana.py` **no existe**; el archivo es
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s149_prereg_invierno\evaluar_ventana.py`.
  En él, la l. 60 (`armar_tabla.py` del brazo) y la l. 86 (`armar_tabla.py` del gemelo) terminan en
  `check=True, stderr=subprocess.DEVNULL)`.
- VERIFICADO que es justo por donde sale el aviso: `armar_tabla.py:25` llama a `bp.indexar_referencia`; el banco
  importa `avisar` (`banco_paridad.py:206-209`) y `scripts/calidad_referencia_mirova.py:44-47` imprime en
  `sys.stderr`. La cadena se corta en el DEVNULL.
- VERIFICADO: la lista `HITOS` (`scripts/calidad_referencia_mirova.py:18-27`) tiene nueve entradas; ninguna nombra
  NOAA-21 ni Suomi NPP.
- La necesidad del hito de Suomi NPP la verifiqué en la memoria y en el commit `9a305c9db` (#774): las filas solo OCR
  de Suomi NPP llevan la distancia y la clase de otra pasada hasta el arreglo de Mirova-v1#20 (2026-10-09 14:01 UTC), y
  tres de las cinco son posteriores al 2026-06-13, así que el hito del 13 de junio no las cubre. La de NOAA-21
  («0 de 1.003 pasadas de enero a marzo», primera el 2026-04-09) es **heredada** de `docs/AUDIT_S149.md:56`: el CSV
  consolidado no trae el satélite en una columna (`Sensor` sólo dice VIIRS, VIIRS375 o MODIS) y no la reconstruí.
- `docs/AUDIT_S149.md:128` ya mandaba arreglar las dos cosas. No se hizo.

**Caminos por los que podría estar mal.** (1) Que el autor del A/B conociera los hitos igual: los conocía (el
pre-registro v3 decide con la tabla sola antes del 13 de junio), así que el daño de hoy es perder el recordatorio, no
un veredicto (SOSPECHA). (2) Que una sesión fría reuse el script para otra ventana: ahí sí el aviso no aparece.

**Gravedad 2.**

**Propuesta.** No es una marca sino dos arreglos chicos: quitar `stderr=subprocess.DEVNULL` en las l. 60 y 86 (o
reenviarlo a `sys.stderr`), y agregar a `HITOS` las dos entradas («2026-04-09, tabla, NOAA-21: antes no hay ninguna
pasada de NOAA-21 en la tabla» y «2026-10-09, ocr, Suomi NPP: antes, en las filas solo OCR la distancia y la clase son
de otra pasada; el VRP sí es de la suya»). Y corregir la ruta en quien cite `scripts\evaluar_ventana.py`.

---

## 8. Hallazgos propios

**V-1. Los comentarios del tablero dicen que el pipeline no marca el tope, y lo marca desde S71.**
`frontend/index.html:1101`: «El pipeline no deja marca en el record, así que se reconoce por el valor»; `:1103`:
«Persistir un flag `diag_d9_capped` en el pipeline sería lo correcto (A72) y queda anotado como pendiente». Lo mismo
en `frontend/diario.html:276` y `frontend/mosaico.html:272`. VERIFICADO: `primary_cluster.d9_capped` existe en 1.548
records, todos `True` y todos en 5,0 exacto; entró en `84c7d312e` (2026-05-20). Y `:1098` dice «1.403 clusters valen
exactamente 5,000 MW»; hoy son 1.548 (A90). Gravedad 2: el reconocimiento por valor funciona igual, pero la nota
manda a implementar algo que ya está.

**V-2. MISSION:232 cita una sección que no existe, sin marca.** «H_S27_1: Test 1 summit-only más agresivo (Coppola
2016a SP426.5 §2.2 Eq.1).» S146 V-06 estableció que en `sp426.5.pdf` no hay §2.2 y que la Ec. 1 es el NTI; la marca
bajó al catálogo (`docs/MIROVA_DIVERGENCES.md:787-795`) y no a esta línea. Hijo no marcado de A113. Gravedad 2.

**V-3. «0 records sobre 5 MW» sin población (CLAUDE.md:363).** Ver P5: hoy hay 338 cúmulos sobre 5 MW, 105 summit.
Es la clase A90 (conteo de un corpus vivo sin ventana). Gravedad 2.

**V-4. La l. 33 del índice dice que el pre-registro v2 está «SIN despachar»**, y el bloque S150 ya registra el v3
despachado y luego evaluado (#761). Va con P1.

## 9. Contraste con los auditores (leído después)

- F4-01 a F4-07 coinciden con mi P1 a P6 en lo sustancial. Diferencias: (a) en P3 pongo gravedad 4 y no 3;
  (b) en P2 matizo el glosario con la respuesta de Nicolás del 2026-10-08, que el auditor no usa; (c) en P5 agrego los
  338 records sobre 5 MW, que el auditor no midió (él dice que «0 records sobre 5 MW» es «literalmente cierta»; lo es
  sólo en la población de S113); (d) en P6 mido el alcance del modo de un píxel (75,5 %) y matizo «fondo local» por
  los 5 volcanes con kernel local.
- F4-08 es la fuente de P7 en su parte de hitos; su ruta del script no la repite, la de P7 venía del orquestador.
- No encontré en ningún informe de auditor los hallazgos V-1 y V-2.
