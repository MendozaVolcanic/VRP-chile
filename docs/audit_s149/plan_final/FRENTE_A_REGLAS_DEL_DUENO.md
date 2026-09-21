# Frente A, auditoría S149: censo de las reglas del dueño y su estado

> Auditor del frente A. Fecha 2026-09-21. Sólo lectura sobre el repo; mi único script vive en
> `experiments/_s149_audit/frente_A/censo_propagacion.py` (salida en `censo_propagacion_salida.txt`).
> Eje que estrena: **conocimiento del dueño perdido o deformado al resumirlo**.
> Todo lo que sigue está anclado a un archivo:línea leído en esta sesión o a la salida de ese script.
> Lo que no, va rotulado SOSPECHA o SIN VERIFICAR. No corrí pytest, no toqué git, no despaché nada.
>
> Abreviaturas de ruta: `MEM/` es
> `C:/Users/nmend/.claude/projects/C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile/memory/`.
> Las rutas del repo cuelgan de `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/`.

## 0. Lo que encontré, en un párrafo

El dueño ha dicho cinco veces, con palabras distintas, la misma cosa: la réplica tiene que ser lo más
fiel posible a MIROVA **en los dos sentidos** (S135: "ser lo más fiel posible y entender por qué
sucede y arreglar cuando diferimos"; S148: "no queremos llenarnos de falsos positivos"; S149: paridad
en los dos sentidos). Cada vez, el agente la resumió quedándose con **una mitad**: en S10 con
"precisión", en el glosario con "recall sobre precisión", en S143 con "la prioridad es asimétrica,
cobertura primero". Las mitades quedaron escritas en lugares que se leen antes que la frase original,
y desde ahí entraron a criterios de A/B. La corrección de hoy (paridad en los dos sentidos, y VIIRS
captura todo, sólo MODIS puede perder sub-píxel) **vive en un archivo de memoria y en un plan que no
está commiteado**; no llegó a `CLAUDE.md`, ni a `docs/MISSION.md`, ni al traspaso `BLOQUE_ARRANQUE_S150.md`,
ni a tres de los cuatro pre-registros contaminados. Además existe una **definición de terminado por
sensor congelada por el dueño el 2026-09-14**, con su condición de reapertura escrita, que el plan de
esta auditoría no cita aunque le encarga proponer exactamente eso.

## 1. El instrumento y sus límites

`censo_propagacion.py` cuenta, archivo por archivo, las líneas que calzan con seis formas textuales.

1. Si la propagación estuviera rota, ¿lo vería? Sí: lista dónde vive cada forma y dónde da cero.
2. Si el instrumento estuviera muerto, ¿se vería distinto? Sí: cada patrón lleva un control positivo
   (un archivo donde debe calzar). Los seis controles dieron distinto de cero (2, 3, 1, 2, 2 y 4 líneas).

Denominador: 19 archivos vigentes (listados en el script). Ventana: el árbol de trabajo al 2026-09-21.
Límite: busca por expresión regular y por línea, es un piso (A89). Dos casos que el patrón no vio y
que leí a mano: `docs/audit_s143/BITACORA_S143.md:9-10` (la frase cruza un salto de línea) y
`docs/S147_RESULTADO_AB_SIN_TEST1.md:49-50` (dice "umbral de 0,5 MW", otra forma). Un cero del script
significa "esta forma textual no está", no "la idea no está"; por eso cada cero de los hallazgos se
repitió por un segundo camino.

## 2. Censo de directivas del dueño

Columnas: texto más completo y dónde está; alcance exacto; dónde está resumida y qué le pasó al
resumen; si algo vigente la viola. "Limpio" significa que busqué y no encontré deformación.

| # | directiva (palabras del dueño cuando existen) | fuente más completa | alcance exacto | resúmenes y su estado | violación vigente |
|---|---|---|---|---|---|
| R1 | Regla por sensor: VIIRS 375 y VIIRS 750 capturan TODO lo que MIROVA publica, también 0,03 a 0,50 MW; "no nos importa perder cosas pequeñas" aplica SOLO a MODIS | `MEM/feedback_mirova_equivalent_priorities.md:7-39`; reafirmada con cita S149 en `:57` ("espero que el umbral sea similar al de MIROVA, que publica menos que 0,5 MW en varias ocasiones") | perfil réplica; por sensor; el corte de 0,5 MW sólo MODIS | índice `MEM/MEMORY.md:70` **corregido hoy**. Deformada, sin marca, en: `MEM/reference_paridad_mirova_umbrales.md:16`, `docs/PLAN_PARIDAD_POST_AUDITORIA_S146.md:214`, `docs/s131/agentes/GROUND_TRUTH_ESPACIAL.md:287`, `docs/S147_RESULTADO_AB_SIN_TEST1.md:49-50` | **SÍ**: H2, H3 |
| R2 | Prioridad en la réplica: paridad en los dos sentidos; publicar lo que MIROVA publica y callar donde calla; minimizar la suma de los dos errores; lo extra al experimental | `MEM/feedback_mirova_equivalent_priorities.md:66-72`; `docs/PLAN_AUDITORIA_S149.md:26-27` (sin commitear) | perfil réplica, los tres sensores | contradicha por `CLAUDE.md:1619` ("priorizamos recall sobre precision"), por `MEM/feedback_s143_primero_igualar_a_mirova.md:17,27-28` y por `docs/audit_s143/BITACORA_S143.md:9-10` | **SÍ**: H1, H5 |
| R3 | "no debemos perder nada que MIROVA esté entregando, debemos ser lo más fiel posible y entender por qué sucede y arreglar cuando diferimos" (2026-09-07) | `docs/PREREGISTRO_AB_D1_D2_S135.md:3-7` | réplica; ante una diferencia se investiga el mecanismo, no se descarta | resumida como "criterio cero pérdidas" (`:6`), que conserva sólo la primera mitad de la frase | tensión con los pisos 118 de 143: H6 |
| R4 | "para que nos crean tenemos que al menos tener todo lo que mirova publica"; lo que mejora y MIROVA no tiene queda en el experimental (2026-09-17) | `MEM/feedback_s143_primero_igualar_a_mirova.md:11-13` | réplica contra experimental | la glosa "prioridad asimétrica" (`:17`) y "la sobre-publicación se optimiza después" (`:27-28`) son del agente, no del dueño | H5 |
| R5 | Objetivo: máxima fidelidad a MIROVA en la réplica "(no queremos llenarnos de falsos positivos)", más detecciones con posibles falsos positivos en el experimental; la réplica se mide contra la base de MIROVA, no se elige | `tasks/BLOQUE_ARRANQUE_S148.md:149-151`; `MEM/feedback_s147_pregunta_medible_no_de_gusto.md:14-28` | los dos perfiles; criterios DISTINTOS por perfil | `tasks/BLOQUE_ARRANQUE_S150.md:109-111` y `S149.md:87` **botaron el paréntesis** de los falsos positivos | pérdida de alcance menor, ver H1 |
| R6 | Decisión 1 del plan de paridad: "Manda la paridad por sensor. No se adopta nada que pierda noches que MIROVA publicó. La fidelidad literal al paper decide sólo entre brazos que empatan en paridad. MODIS, sin positivos fuera de Láscar, se juzga por fidelidad" (2026-09-13) | `docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md:13` | por sensor; MODIS aparte | sin resumen en `CLAUDE.md`, `MISSION.md` ni traspasos S149 y S150 (script, patrón `definicion_de_terminado`: cero) | H4 |
| R7 | Definición de terminado por sensor, CONGELADA 2026-09-14: V375 y V750, 0 noches con alerta perdidas, falsas publicaciones por pasada 10 % o menos en focales y 15 % o menos en nevados, magnitud mediana en [0,8 ; 1,25] por volcán con n de 30 o más; MODIS por pasos literales y contraste en Láscar. Única causa de reapertura: que MIROVA no cumpla esas bandas contra sí misma | mismo archivo `:75-95` | por sensor y por estrato focal o nevado | viva en `scripts/auto_audit_weekly.py:148` (`FALSAS_BANDA_TERMINADO`); ausente de todo lo que se lee primero | H4 |
| R8 | Misión: clon literal; las tres preguntas; "en las últimas sesiones hicimos muchas cosas que no necesitábamos" (S27) | `MEM/feedback_mision_clon_mirova.md:24-25`; `docs/MISSION.md:38-164` | todo cambio en `pipeline/` | limpio en `CLAUDE.md` (sección Misión vinculante) | el objetivo (2) de `MISSION.md:21-36` choca con R4 y R5: H8 |
| R9 | "mirova réplica debería detectar el píxel o los píxeles de mayor valor como lo hace MIROVA, mientras que en experimental lo seteamos para un área menor donde sabemos está el cráter activo" (S124); "¿acaso en el operacional nosotros no reportamos la mayor? Deberíamos hacerlo igual aunque en el frontend y en los gráficos haya filtros de distancia" | `docs/S124_OBSERVABILIDAD_PISOS_Y_DISTANCIA.md:66-68`; `docs/S124_SELECCION_CLUSTER_MAX_VS_VENT.md:3-5`; antecedente `tasks/BLOQUE_ARRANQUE_S87.md:67` | selección del cúmulo que se reporta, réplica | sin puntero en catálogo, `CLAUDE.md`, `MISSION.md` ni traspasos S140 a S150 | **SÍ**: H7 |
| R10 | MIROVA en tiempo casi real es 100 % algorítmico; "no hay una persona mirando todo el día y corrigiendo" | `MEM/feedback_mirova_no_human_supervision.md:8-64`; `MEM/feedback_s135_techo_artificial_supervision.md:11-12` | canal NRT; la supervisión manual es de la base v.1 | `CLAUDE.md` A105 limpio; el TÍTULO de A76 sigue diciendo "los limpia por supervisión MANUAL" | H11 |
| R11 | "MIROVA publica todos los sensores"; "MODIS solo ve pocas cosas y solo cuando son grandes; MIROVA reporta cada satélite por separado"; "estamos muy centrados en MODIS, cuando es VIIRS el que más usamos" | `docs/AUDIT_S93_artefactos_sobreestimacion.md:77,109`; `docs/AUDIT_S94_per_sensor_metrics.md:206` | análisis siempre por sensor; VIIRS 375 es el sensor operacional | coherente con R1; sin resumen propio en `CLAUDE.md` (SOSPECHA: sólo busqué las citas, no la idea) | no encontré |
| R12 | La referencia de MIROVA no sirve igual todo el año; los primeros meses tienen defectos de OCR (S149) | `CLAUDE.md:1486-1500` (A119) | toda ventana anterior al 2026-06-13 | puntero en `CLAUDE.md:1709` y en `tasks/BLOQUE_ARRANQUE_S150.md:11-15`. Limpio | es del frente B |
| R13 | El dueño revisa en el tablero, no en el código: "yo reviso poco casi nada, solo cuando las cosas están en el dashboard puedo opinar y ayudarte"; el encendido de un flag en la réplica es su punto de decisión | `MEM/feedback_nicolas_revisa_en_dashboard.md:12-31` | adopciones operacionales | `CLAUDE.md` "Regla de publicación en dashboard" y A39, A45. Limpio | no encontré |
| R14 | Explicar como geólogo, en lenguaje llano: "necesito que me expliques mejor las cosas" (S18) | `MEM/feedback_plain_language.md:11-14`; `CLAUDE.md` global, sección Persona | toda comunicación con él | limpio; el prompt de `BLOQUE_ARRANQUE_S150.md:106-107` la conserva | no encontré |
| R15 | Sin guiones largos ni medios, español de Chile sin voseo, también en los `.md` del repo | `C:/Users/nmend/.claude/CLAUDE.md`, sección Persona | todo documento | limpio en lo escrito desde S146 | los dos `CLAUDE.md` y `MISSION.md` la violan: H12 |
| R16 | "tenemos todo el tiempo del mundo, y tokens para hacer todas las pruebas ... paso a paso, registrando todo, probando y descartando" (S85); "olvida la restricción de tokens" (S70-2) | `MEM/feedback_calidad_paso_a_paso.md:10-12`; `tasks/BLOQUE_ARRANQUE_S71.md:130` | método de trabajo | A26 en `CLAUDE.md`. Limpio | no |
| R17 | Matiz de R16: paró un abanico de 27 agentes por "consumo extremo"; la escala se acuerda antes | `MEM/feedback_s120_fanout_consumo.md:10-27` | auditorías con muchos agentes | `docs/PLAN_AUDITORIA_S149.md:5-6` declara la escala acordada. Limpio | no |
| R18 | No agregar mecanismos sin un problema concreto: "para qué quiero eso? acaso las ecuaciones MIROVA no están claras?" (S19) | `MEM/feedback_no_scope_creep.md:11-14` | propuestas nuevas | limpio | es la pregunta del frente E ("¿nos estamos enredando?") |
| R19 | Si un criterio necesita umbral, se le pregunta a la referencia, no al dueño | `MEM/feedback_s147_pregunta_medible_no_de_gusto.md:11-30`; A115 | criterios de A/B | limpio | el veredicto de recall por tramo queda "mirando esa tabla" (`PREREGISTRO_INVIERNO.md:155-156`): es una decisión de gusto devuelta al dueño. SOSPECHA de choque con R19, gravedad 2 |
| R20 | "probar diferentes alternativas hasta llegar a la réplica de MIROVA" (S70-2) | `docs/MIROVA_DIVERGENCES.md:280` | método ante una divergencia | limpio | no |
| R21 | Al cerrar, prompt para copiar y pegar, y la frase de una línea: "quiero tener claro qué copiar y pegar" | `MEM/feedback_session_close_handoff_prompt.md:18-62` | cierre de sesión | `tasks/BLOQUE_ARRANQUE_S150.md:103-157` cumple el prompt largo. Limpio | no |
| R22 | Toda referencia lleva paper, página y párrafo | `tasks/BLOQUE_ARRANQUE_S142.md:46` | manuscrito y lecturas | `MEM/MEMORY.md` (entrada S141 de citas). Limpio | no verifiqué citas: es de otros frentes |
| R23 | La ficha de transparencia: "dejarla de lado por ahora" (S130) | `tasks/BLOQUE_ARRANQUE_S130.md:94-96` | temporal | choca con el `CLAUDE.md` de Volcanologia, que la declara vinculante | para el frente G |
| R24 | Rotar el token de Earthdata: "NO le interesa" (S97) | `tasks/BLOQUE_ARRANQUE_S97.md:27` | S97; SOSPECHA de que era otro asunto (higiene, no vencimiento) | hoy todos los traspasos piden rotarlo antes del 2026-10-03 | para el frente G |
| R25 | Reprocesos largos partidos por volcán, nunca paralelos sobre el mismo directorio | `MEM/feedback_parallel_runs.md`; A47 | reprocesos | limpio | no |

## 3. Hallazgos, de mayor a menor gravedad

### H1. Las dos decisiones de hoy del dueño no están donde se lee primero, y el texto viejo sigue sin marca
- ARCHIVO:LÍNEA: `CLAUDE.md:1619`; `docs/MISSION.md` (entero, 262 líneas); `tasks/BLOQUE_ARRANQUE_S150.md:109-111,147`;
  `docs/PLAN_AUDITORIA_S149.md:26-27`; SCRIPT: patrones `paridad_dos_sentidos`, `alcance_solo_MODIS` y
  `recall_sobre_precision`.
- QUÉ PASA: el dueño decidió hoy que en la réplica manda la paridad en los dos sentidos y reafirmó que
  en VIIRS no hay pérdida pequeña aceptable. El script encuentra "dos sentidos" sólo en el archivo de
  memoria y en `PLAN_AUDITORIA_S149.md`, que `git status` muestra sin commitear. El glosario del
  proyecto sigue diciendo "Para `mirova_equivalent` priorizamos recall sobre precision", sin marca. El
  prompt de S150 dice "el recall que decide va por PASADA" y no menciona el tramo de magnitud ni la
  paridad. Consumidores vivos del texto viejo: `docs/MIROVA_DIVERGENCES.md:2304` y
  `docs/s130/PREREGISTRO_AB_D18.md:22` (la caja de 5 por 5 km se frenó en parte porque "la dirección
  es menos detecciones" y la réplica "prioriza recall"), `tasks/BLOQUE_ARRANQUE_S130.md:146`,
  `docs/paper/sec4_background.md:255` ("el argumento de recall sobre precisión del paper entero").
- CÓMO SE VE EN EL DASHBOARD: invisible hoy. Se verá como una réplica que sigue publicando de más,
  porque toda palanca que recorta publicaciones carga con un argumento de misión en contra que el
  dueño ya retiró.
- CÓMO REPRODUCIRLO: `python experiments/_s149_audit/frente_A/censo_propagacion.py`; `sed -n 1615,1620p CLAUDE.md`.
- CONFIANZA: CONFIRMADO. GRAVEDAD 4 (es A113: mientras el texto viejo siga sin marca donde se lee
  primero, la regla vieja sigue viva; la próxima sesión hereda "recall sobre precisión").

### H2. El corte de 0,5 MW sigue decidiendo el recall de VIIRS en tres pre-registros, en el evaluador y en un documento de memoria
- ARCHIVO:LÍNEA: `experiments/_s146_ab_sin_test1/PREREGISTRO.md:362-364`;
  `experiments/_s146_ab_sin_test1/parametros.json:20-21,26`; `experiments/_s146_ab_sin_test1/evaluar.py:613-617,897`;
  `experiments/_s147_ab_conectiva/PREREGISTRO.md:109` (P4); `experiments/_s147_ab_conectiva/PREREGISTRO_CAJA.md:116` (Q4);
  `docs/PLAN_PARIDAD_POST_AUDITORIA_S146.md:214`; `docs/S147_RESULTADO_AB_SIN_TEST1.md:49-50`;
  `MEM/reference_paridad_mirova_umbrales.md:16`.
- QUÉ PASA: un foco débil de VIIRS (0,03 a 0,5 MW, que es lo que MIROVA publica casi siempre en Chile)
  puede perderse sin que el criterio lo note, porque la condición dura es "ninguna pérdida de 0,5 MW o
  más, en ningún sensor" y la justificación escrita es "prioridad declarada del perfil". En el código,
  `evaluar.py:615-616` filtra `vrp_mirova_mw >= par["max_vrp_fn_aceptable_mw"]` sin mirar el sensor.
  Sólo `PREREGISTRO_INVIERNO.md:151-156` trae la enmienda. El de la caja recibió una adenda S149
  (`PREREGISTRO_CAJA.md:7`) que **no tocó Q4**, y G y H están por repetirse. El de S146 y su JSON no
  tienen ninguna mención a S149 (conteo de la cadena "S149": 0 y 0).
- CÓMO SE VE EN EL DASHBOARD: un brazo adoptado con este criterio haría desaparecer alertas débiles
  de Chaitén, Planchón Peteroa, Isluga o Villarrica en VIIRS, con veredicto "cumple C1".
- CÓMO REPRODUCIRLO: el script, patrón `corte_0,5_como_criterio` contra `alcance_solo_MODIS`.
- CONFIANZA: CONFIRMADO. GRAVEDAD 4.
- Nota: los veredictos ya emitidos con este criterio son del frente D. El dato que acota el daño:
  `docs/S147_RESULTADO_AB_SIN_TEST1.md:48-50` informa 6 pasadas perdidas, todas bajo 0,15 MW, y las
  dio por buenas por estar bajo el corte.

### H3. S131 cerró 111 alertas perdidas, TODAS de VIIRS, como "el régimen que el proyecto ya declaró aceptable"
- ARCHIVO:LÍNEA: `docs/s131/agentes/GROUND_TRUTH_ESPACIAL.md:272-287,362`; `docs/AUDIT_S131.md:68`.
- QUÉ PASA: de 1.926 alertas nocturnas de MIROVA en pasadas comunes perdimos 111 (5,76 %): 60 de
  VIIRS 375, 51 de VIIRS 750 y **cero de MODIS**, mediana 0,19 MW, 90,1 % bajo 0,5 MW. El informe
  las rotula "señal sub-umbral, no fallas", gravedad baja, apoyado en "FN sub-píxel <0,5 MW". Bajo la
  regla del dueño es al revés: son exactamente las que no se aceptan, y MODIS, el único sensor donde
  se tolerarían, no perdió ninguna. La ventana y el corpus son los de S131 (anteriores a #571 en
  parte): el número de hoy es del frente C.
- CÓMO SE VE EN EL DASHBOARD: noches en que MIROVA muestra una alerta débil de VIIRS y nuestro
  tablero no muestra nada.
- CÓMO REPRODUCIRLO: `sed -n 270,288p docs/s131/agentes/GROUND_TRUTH_ESPACIAL.md`.
- CONFIANZA: CONFIRMADO (el texto y el desglose por sensor). GRAVEDAD 4: es un frente de
  investigación apagado por una regla deformada, con pistas ya medidas (42,3 % con vista sobre 45
  grados, 78,4 % con el NTI en el piso).

### H4. Existe una definición de terminado por sensor congelada por el dueño, y el plan de S149 encarga proponerla de nuevo sin citarla
- ARCHIVO:LÍNEA: `docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md:9-17,75-95,222-225`;
  `scripts/auto_audit_weekly.py:148`; `docs/PLAN_AUDITORIA_S149.md:28-29`; SCRIPT: patrón
  `definicion_de_terminado` da cero en `CLAUDE.md`, `MISSION.md`, `PLAN_AUDITORIA_S149.md`,
  `BLOQUE_ARRANQUE_S150.md` y `MEMORY.md`.
- QUÉ PASA: el 2026-09-14 el dueño congeló metas por sensor (tabla de R7) y dejó escrito lo que no se
  hizo: "la medición de consistencia del propio MIROVA no se corrió", y que ese es "el único" motivo
  para reabrir la tabla. El plan de S149 dice que la meta será "metas por sensor que proponga esta
  auditoría, midiendo la variabilidad de MIROVA contra sí misma". Es la misma tarea, pero planteada
  como hoja en blanco. Consecuencias: (a) el frente C debe partir de esa tabla y tratar su medición
  como la reapertura prevista, no inventar bandas; (b) la tabla mide la detección en **noches** y la
  decisión 1 habla de "noches que MIROVA publicó", mientras S146 pasó la vara a **pasadas** por poder
  estadístico (`PREREGISTRO.md:555`, donde el "sí" es la recomendación del agente; que el dueño lo
  haya aprobado es SIN VERIFICAR); (c) el techo de 0,45 del A/B de S146 (`parametros.json:49`) está
  muy lejos del 10 y 15 % congelado, declarado "para este A/B".
- CÓMO SE VE EN EL DASHBOARD: invisible. El auto-audit semanal sí usa 10 y 15 %.
- CÓMO REPRODUCIRLO: `sed -n 75,95p docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md`.
- CONFIANZA: CONFIRMADO. GRAVEDAD 4 (cambia el plan: hay metas aprobadas y una condición de reapertura).

### H5. "La prioridad es asimétrica, cobertura primero" es una glosa del agente, no una frase del dueño, y contradice su decisión de hoy
- ARCHIVO:LÍNEA: `MEM/feedback_s143_primero_igualar_a_mirova.md:11-13` (la cita) contra `:17-19,27-28`
  (la glosa); `docs/audit_s143/BITACORA_S143.md:7-10`; `tasks/BLOQUE_ARRANQUE_S144.md:65`; índice `MEM/MEMORY.md:98`.
- QUÉ PASA: el dueño dijo "para que nos crean tenemos que al menos tener todo lo que mirova publica".
  El agente agregó "por eso la prioridad es asimétrica", "la sobre-publicación y la magnitud se
  optimizan después" y, en la bitácora, "el criterio 1 (cero pérdidas) manda sobre la sobre-publicación".
  Ninguna de esas tres frases está entre comillas del dueño. La frase de S135 (R3) ya era de dos
  sentidos ("lo más fiel posible ... arreglar cuando diferimos"), y el objetivo de S148 trae "no
  queremos llenarnos de falsos positivos". Ninguno de los dos archivos lleva marca de la decisión S149.
- CÓMO SE VE EN EL DASHBOARD: invisible; sostiene la sobre-publicación (87 % de negativos limpios en
  VIIRS 375 según `plan-definitivo...:82`) como problema de segundo orden.
- CÓMO REPRODUCIRLO: script, patrón `asimetria_recall_primero`; leer `BITACORA_S143.md:7-10`.
- CONFIANZA: CONFIRMADO. GRAVEDAD 3.

### H6. "No perder nada" convive con un piso que tolera perder 23 a 25 pasadas de VIIRS 375
- ARCHIVO:LÍNEA: `docs/PREREGISTRO_AB_D1_D2_S135.md:4-6`; `experiments/_s146_ab_sin_test1/parametros.json:23,26`;
  `experiments/_s146_ab_sin_test1/PREREGISTRO.md:41` (H12); `experiments/_s147_ab_conectiva/PREREGISTRO.md:109`;
  `PREREGISTRO_CAJA.md:116`; `PREREGISTRO_INVIERNO.md:129`.
- QUÉ PASA: el piso de 118 de 143 (o de 141) pasadas nació como cota pesimista de una inferencia,
  no como tolerancia, y el propio pre-registro avisa que "tolera perder hasta 25" y que la red de
  0,5 MW "cubre poco (126 de 143 están bajo ese valor)". Caída esa red (H2), lo único que protege el
  recall de VIIRS es un piso que admite perder 16 a 17 % de lo que MIROVA publica. El pre-registro de
  invierno lo hereda por regla de tres (`ceil(n_B × 118 / 141)`).
- CÓMO SE VE EN EL DASHBOARD: igual que H2.
- CONFIANZA: CONFIRMADO el texto; que el dueño haya aceptado ese piso sabiendo lo que tolera: SIN VERIFICAR.
  GRAVEDAD 3.

### H7. El dueño pidió reportar la anomalía mayor, como MIROVA; la réplica elige la más cercana al cráter, y la medición que lo muestra no tiene puntero
- ARCHIVO:LÍNEA: `docs/S124_SELECCION_CLUSTER_MAX_VS_VENT.md:3-14,56-64`; `tasks/BLOQUE_ARRANQUE_S87.md:67`;
  perfil resuelto: `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.ENABLE_VENT_ANCHORED_CLUSTERING)"` da `True`.
- QUÉ PASA: MIROVA mira toda la escena y publica el foco mayor con su distancia. Nosotros, dentro del
  radio interno, publicamos el cúmulo más cercano al cráter "independiente de `vrp_mw`". El documento
  de S124 contesta "no, no reportamos la mayor" y pide un A/B con criterio pre-registrado. Busqué ese
  documento por nombre y por dos frases en `docs/MIROVA_DIVERGENCES.md`, `CLAUDE.md`, `MISSION.md` y
  los traspasos S140 a S150: cero. Sólo lo citan `docs/audit_s146/FRENTE_H_HIPOTESIS_Y_AB.md:396`
  (como brazo que "nunca se corrió") y dos archivos de memoria archivada.
- CÓMO SE VE EN EL DASHBOARD: magnitud más baja que la de MIROVA en la misma pasada (el documento
  midió 0,62 contra 0,75 en Láscar, ventana que cruza #535: no usar el número, sí la dirección).
- CONFIANZA: CONFIRMADO que la directiva existe, que el flag está encendido y que no hay puntero.
  Si el máximo es lo correcto: SIN VERIFICAR, es del frente E. GRAVEDAD 3.

### H8. `docs/MISSION.md` pone el valor agregado dentro del mismo algoritmo; el dueño lo mandó al perfil experimental con criterios distintos
- ARCHIVO:LÍNEA: `docs/MISSION.md:21-36` contra `MEM/feedback_s143_primero_igualar_a_mirova.md:11-13,24-26`
  y `MEM/feedback_s147_pregunta_medible_no_de_gusto.md:26-28`.
- QUÉ PASA: MISSION (texto de S86) dice que el algoritmo es único y que la separación vive en el campo
  `pc.classification` y en el frontend. El dueño, en S143 y S147, separó por perfil: la réplica se
  mide contra MIROVA, el experimental contra OVDAS y SWIR, "criterios distintos, no los mismos con
  otro umbral". MISSION no menciona el perfil experimental como destino ni la paridad en dos sentidos.
  SOSPECHA heredada, no verificada por mí: `CLAUDE.md` (A111) dice que `pc.classification` no existe
  con ese nombre (existe `geo_class`), y `MEM/MEMORY.md:34` dice que hoy el experimental es idéntico a
  la réplica salvo el directorio. Es materia del frente F.
- CÓMO SE VE EN EL DASHBOARD: la vista operacional mezcla réplica y "extensión"; no hay una vista del experimental.
- CONFIANZA: CONFIRMADO el choque de textos. GRAVEDAD 3.

### H9. Hay una segunda tabla de "umbrales acordados" en la memoria, con recall de 0,60 por volcán para todos los sensores
- ARCHIVO:LÍNEA: `MEM/reference_paridad_mirova_umbrales.md:10-18`, enlazado desde `MEM/MEMORY.md:128`.
- QUÉ PASA: fija como tolerable un recall de 0,60 "porque FNs sub-pixel <0.5 MW aceptables (memoria
  previa)", sin sensor, y una precisión de 0,50. Compite con la tabla congelada de R7 y contradice R1.
  Es de S15 y no lleva marca.
- CONFIANZA: CONFIRMADO. GRAVEDAD 2 (nadie la cita en lo vigente que revisé; es una trampa para quien busque "metas").

### H10. En S24 la misma regla se leyó al revés ("el operacional prioriza precisión") para aceptar perder 25 % de aciertos lejanos
- ARCHIVO:LÍNEA: `MEM/project_s24_p31_ab_validated.md:27-30`.
- QUÉ PASA: cita `mirova_equivalent_priorities` como fuente de "prioriza precision" sin sensor. Es la
  tercera lectura distinta de la misma regla (precisión en S24, recall en el glosario, asimetría en S143).
- CONFIANZA: CONFIRMADO el texto. Si P3.1 sigue activo y en qué sensor: SIN VERIFICAR. GRAVEDAD 2. Para el frente D.

### H11. El título de A76 dice que MIROVA limpia artefactos "por supervisión MANUAL", contra la regla del dueño de S21 y S135
- ARCHIVO:LÍNEA: `CLAUDE.md`, regla A76 (leída en el contexto de esta sesión) contra
  `MEM/feedback_mirova_no_human_supervision.md:8-19` y `MEM/feedback_s135_techo_artificial_supervision.md:11-15`.
- QUÉ PASA: el cuerpo de A76 ya tiene la cita rebajada, pero el título conserva la explicación que el
  dueño corrigió dos veces. El hecho que describe (el consolidado dio cerca de 0 y la imagen por volcán
  mostró 760 MW) admite una explicación algorítmica (la tabla y la imagen son productos distintos).
- CONFIANZA: CONFIRMADO el texto; la explicación alternativa es SOSPECHA. GRAVEDAD 2.

### H12. Los documentos que más se leen violan la regla de estilo del dueño
- SCRIPT:SALIDA (comando en VERIFICADO LIMPIO): líneas con guion largo: `CLAUDE.md` del proyecto 144,
  `docs/MISSION.md` 27, `CLAUDE.md` global 14. Líneas con voseo (patrón acotado): 6, 1 y 6. Control:
  los cuatro documentos escritos desde S146 que medí dan 0 y 0, así que el instrumento distingue.
- QUÉ PASA: el propio archivo que prohíbe el voseo dice "Si dudás, decilo y verificá". No tuerce
  ninguna alerta, pero un documento que sale de esos `.md` hereda los guiones.
- CONFIANZA: CONFIRMADO. GRAVEDAD 1.

### H13. La causa mecánica: el índice obliga a una línea por entrada y nada vigila que el resumen conserve el alcance
- ARCHIVO:LÍNEA: `MEM/MEMORY.md` cabecera ("Cap duro: <140 líneas. Una línea por entrada") contra
  `docs/META_RULES_S80.md:210-224` (M9 dice 500); `MEM/feedback_mirova_equivalent_priorities.md:64`
  ("Al resumir una regla en el indice, no botar su alcance").
- QUÉ PASA: la lección ya está escrita, pero como frase. No existe un guard que compare cada línea del
  índice con el campo `description` de su archivo, que es donde el alcance sí estaba ("MODIS acepta
  perder señales subpixel", `feedback_mirova_equivalent_priorities.md:3`). Tres de los cinco resúmenes
  deformados de este informe botaron un calificador de alcance (sensor, perfil o "al menos").
- CONFIANZA: CONFIRMADO. GRAVEDAD 2. Siguiendo la regla B del protocolo: el guard posible es un test
  que exija que toda línea del índice que resuma una regla por sensor nombre el sensor; no lo escribí
  porque auditar no es arreglar.

## 4. Reglas del dueño que el plan final debe respetar, en sus palabras y con su alcance

1. **Réplica, los tres sensores**: "no debemos perder nada que MIROVA esté entregando, debemos ser lo
   más fiel posible y entender por qué sucede y arreglar cuando diferimos" (S135). Hoy precisada:
   publicar lo que MIROVA publica y callar donde calla; minimizar la suma de los dos errores.
2. **VIIRS 375 y VIIRS 750**: capturan todo lo que MIROVA publica, también lo débil; "espero que el
   umbral sea similar al de MIROVA, que publica menos que 0,5 MW en varias ocasiones". El recall se
   juzga sobre todas las alertas y por tramo de magnitud.
3. **MODIS, y sólo MODIS**: "no nos importa perder cosas pequeñas"; ahí sí vale el corte de 0,5 MW.
   "MODIS solo ve pocas cosas y solo cuando son grandes". Sin positivos fuera de Láscar, "se juzga
   por fidelidad" al paper.
4. **Réplica contra experimental**: "para que nos crean tenemos que al menos tener todo lo que mirova
   publica"; lo que mejora y MIROVA no tiene va al experimental, con más detecciones y posibles
   falsos positivos, separado de la serie operacional. En la réplica "no queremos llenarnos de
   falsos positivos".
5. **Cómo se decide**: la réplica se mide contra la base de MIROVA (CSV, OSF, TIF, km y MW), no se
   elige ni se le pregunta al dueño "cuánto tolera"; el experimental se valida contra actividad
   conocida de OVDAS y SWIR de alta resolución. Esa base no sirve igual todo el año (A119).
6. **Metas**: existe una definición de terminado por sensor congelada el 2026-09-14; se reabre sólo
   si MIROVA no cumple esas bandas contra sí misma. Las metas nuevas parten de ahí. Sin fecha: que quede bien.
7. **Qué se reporta**: "mirova réplica debería detectar el píxel o los píxeles de mayor valor como lo
   hace MIROVA"; los filtros de distancia son del tablero, no de la detección.
8. **Por sensor siempre**: "MIROVA reporta cada satélite por separado"; "es VIIRS el que más usamos".
9. **Sin techos inventados**: "no hay una persona mirando todo el día y corrigiendo"; una diferencia
   con MIROVA en tiempo casi real es algorítmica y se investiga.
10. **Literalidad**: nada entra a `pipeline/` sin pasar las tres preguntas; "hicimos muchas cosas que
    no necesitábamos". La fidelidad literal decide sólo entre brazos que empatan en paridad.
11. **Entrega**: el dueño opina sobre el tablero, no sobre el código; encender un flag en la réplica
    es su decisión, con tag y confirmación (A45).
12. **Forma**: explicar como geólogo (fenómeno, mecanismo, números al final), español de Chile sin
    voseo, sin guiones largos ni medios, rutas completas, prompt de cierre para copiar y pegar, y la
    escala de cualquier abanico de agentes acordada antes.

## 5. VERIFICADO LIMPIO

| qué miré | resultado | comando |
|---|---|---|
| La línea del índice de memoria sobre la regla por sensor | corregida hoy, nombra "SOLO MODIS" | `grep -n "Prioridades mirova_equivalent" MEM/MEMORY.md` (línea 70) |
| El archivo fuente de la regla por sensor conserva el texto de la sesión 10 y las dos decisiones S149 | sí, líneas 7 a 39 y 55 a 72 | lectura completa |
| `PREREGISTRO_INVIERNO.md` trae la enmienda del recall declarada como posterior al resultado | sí, `:151-156` | lectura |
| A119 (calidad de la referencia por mes) propagada a `CLAUDE.md` y al traspaso | sí, `CLAUDE.md:1486` y `:1709`, `BLOQUE_ARRANQUE_S150.md:11-15` | `grep -n A119 CLAUDE.md` |
| El objetivo en palabras del dueño está en los prompts de S148, S149 y S150 | sí (`S148:149-151`, `S149:87`, `S150:109-111`); S149 y S150 perdieron el paréntesis de los falsos positivos | lectura |
| Escala de la auditoría acordada antes (regla S120) | declarada en `docs/PLAN_AUDITORIA_S149.md:5-6` | lectura |
| Regla de MIROVA sin supervisión humana y su corrección A105 | coherentes entre memoria y `CLAUDE.md`, salvo el título de A76 (H11) | lectura de los dos archivos de memoria |
| Documentos escritos desde S146 respetan guiones y voseo | 0 y 0 en `BLOQUE_ARRANQUE_S150.md`, `PREREGISTRO_INVIERNO.md`, `PREREGISTRO.md` de S146 y `PLAN_AUDITORIA_S149.md` | `grep -c` del carácter guion largo (U+2014) y del guion medio (U+2013) sobre cada archivo, y el patrón de voseo de la bitácora de esta sesión |
| `docs/META_RULES_S80.md` y `docs/PROCESS_RULES_S33.md` | son reglas de proceso del agente; no contienen directivas citadas del dueño (2 y 0 menciones) y no las censé una por una | `grep -c -i nicol <archivo>` |
| Las 110 menciones de decisiones o frases del dueño en `docs/`, `tasks/` y `CLAUDE.md` | leídas las de alcance de misión (S87, S93, S94, S124, S135, S143); el resto son decisiones puntuales ya ejecutadas | grep con patrón "Nicol..s" más verbo, guardado en el scratchpad |

## 6. SIN VERIFICAR (para que nadie lo tome por cubierto)

- Si el dueño aprobó a sabiendas la vara por pasada y el piso de 118 de 143 de S146 (H4, H6): el
  documento sólo guarda la recomendación.
- No leí los 53 `feedback_*.md` enteros: leí 16 (los que traen palabras del dueño sobre prioridad,
  pérdidas, perfiles, validación, tablero y comunicación). Los otros 37 son lecciones de método del
  agente según su descripción en el índice; no comprobé que ninguna esconda una directiva.
- No abrí los `project_sNN_estado.md` salvo por búsqueda de cadenas; una directiva dicha sólo ahí se me pasó.
- `MEMORY_ARCHIVE_*`: sólo búsqueda por cadenas (0,5 MW, sólo MODIS, sub-píxel), no lectura.
- Los números de H3 son de S131; los de hoy son del frente C.

## 7. Para otros frentes

- **Frente D**: veredictos que usaron el corte de 0,5 MW o "recall sobre precisión":
  `docs/S147_RESULTADO_AB_SIN_TEST1.md:48-50`; `docs/s130/PREREGISTRO_AB_D18.md:18-26`;
  `docs/MIROVA_DIVERGENCES.md:2298-2305`; `docs/s131/agentes/GROUND_TRUTH_ESPACIAL.md:362` (H7 de S131);
  `MEM/project_s24_p31_ab_validated.md:27-30`.
- **Frente C**: la tabla congelada `docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md:75-95`
  es el punto de partida de las metas, y su condición de reapertura es tu medición.
- **Frente E**: `ENABLE_VENT_ANCHORED_CLUSTERING = True` en la réplica contra la pregunta del dueño en
  `docs/S124_SELECCION_CLUSTER_MAX_VS_VENT.md:3-5`.
- **Frente F**: `docs/MISSION.md:21-36` contra la separación por perfil; la definición del
  experimental que dio el dueño en `docs/S124_OBSERVABILIDAD_PISOS_Y_DISTANCIA.md:66-68` ("un área
  menor donde sabemos está el cráter activo").
- **Frente G**: ficha de transparencia "dejarla de lado por ahora" (`tasks/BLOQUE_ARRANQUE_S130.md:94`);
  token, `tasks/BLOQUE_ARRANQUE_S97.md:27`; el paper apoya su argumento en "recall sobre precisión"
  (`docs/paper/sec4_background.md:255`).
