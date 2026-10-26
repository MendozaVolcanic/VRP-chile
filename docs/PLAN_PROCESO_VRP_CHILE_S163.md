# Plan para mostrar el proceso de VRP Chile (S163, 2026-10-26)

**Para qué sirve.** Es la base común de tres piezas: el paper (sesión «Paper VRP Chile: estado,
estructura y riesgos de la IA»), las dos charlas del XVII Congreso Geológico Chileno (sesión
«Presentaciones del Congreso Geológico 2026») y la memoria del proyecto. Propone una estructura,
dice qué evidencia sostiene cada parte, qué figura o tabla sale de qué script y qué falta medir.
**No es todavía el relato**: es el mapa para escribirlo sin depender de recuerdos.

**Regla del documento.** Cada afirmación lleva su fuente (archivo y línea, commit, PR o script).
Los estados son VERIFICADO (lo leí o lo medí en esta sesión), EN PARTE, SIN VERIFICAR y POR MEDIR.
Las rutas de `experiments/` y `docs/` son relativas a la raíz del repositorio
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\`. `CLAUDE.md` es el del
proyecto. `LOOP_OBJETIVOS.md` se lee en la rama del loop:
`git show origin/loop/activo:tasks/LOOP_OBJETIVOS.md` (las líneas citadas son del commit
`67e912b3dc1c`, 5.231 líneas).

Scripts nuevos de esta sesión, en `experiments/_s163_plan_proceso/` (cada uno con su `.out`):

| script | qué mide |
|---|---|
| `medir_transcripts.py` | tokens por modelo y por mes en los transcripts locales de Claude Code |
| `costo_equivalente_api.py` | costo equivalente a precio de API de esos tokens, en rango |
| `medir_tiempo.py` | horas activas, días con actividad y mensajes de texto a las sesiones |
| `actividad_repo.py` | commits humanos y de bots, días con commit humano y PR por mes |
| `reglas_A.py` | sesión de origen de cada regla A y si lleva marca posterior de auditoría |

---

## 0. Lo que el encargo daba por hecho y no se sostiene

Antes del plan, siete premisas del encargo que la evidencia corrige. Si alguna pieza ya las usa,
hay que cambiarlas.

| premisa | lo que dice la evidencia | fuente |
|---|---|---|
| «Coppola no respondió» | **El correo nunca se envió.** No hay respuesta que esperar. Hay un borrador desde S139 y la decisión de no enviarlo todavía | `docs/audit_s139/BORRADOR_CORREO_COPPOLA.md`; `docs/AUDIT_S158_R2.md:6`; `LOOP_OBJETIVOS.md` l. 804-805 y 907 |
| «Sin ayuda de Coppola» | Sin contacto directo, sí. Pero desde el 2026-07-24 hay código de MIROVA publicado por el propio Coppola (OSF zm62w, MIT), y la réplica de VIIRS 750 se apoya en él. Decir «sin contacto con el autor, con su material público» | `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md:11-12` |
| Sobre-publicación «de 85-88 % a 1-3 %» | **De 88,2 y 85,4 % a 2,5 y 3,7 %** en negativos limpios de VIIRS 375. V1, del 2026-08-29 al 10-08: C0 publica 734 de 832 y K 21 de 832. V2, del 2026-03-01 al 06-12 (VIIRS desde abril): C0 863 de 1.010, K 37 de 1.010 | `experiments/_s153_fk_v2/v1.log:151,153`; `v2.log:225-226` |
| Recall por noche «ventana de 60 días» | Los números son correctos (VIIRS 375 96,8 % con n 93; VIIRS 750 73,3 % con n 30; MODIS 66,7 % con n 12), pero la ventana va del 2026-08-20 al 10-19 (61 días) y el archivo se sobrescribe cada semana. Hay que citar el commit `2e1bc0e31`. Con n 12, el 66,7 % de MODIS es frágil | `data/audit_continuous/latest.json` l. 3-6, 19, 30-44 en `2e1bc0e31` |
| Magnitud baja de Chillán y Tupungatito «con causa principal D17» | **No está medido.** El issue #864 dice «causa sin medir». La bitácora dice que la dependencia con el ángulo no es D17 y que lo que empeora es nuestro fondo. En Tupungatito la atribución es «fondo del anillo (parte D17)», PARCIAL | issue #864; `LOOP_OBJETIVOS.md` l. 261 y 428-430; `experiments/_s161_estado_864/INFORME.md` l. 165-177 (rama loop) |
| Coeficientes «con error ≤0,17 %» | El 0,17 % es el error de la fórmula de Di Bella para VIIRS 750. El coeficiente adoptado (11.081.250) coincide con la mediana del OSF con error casi cero. Y no es un ajuste: es **reconstruir** el coeficiente desde 48.360 filas publicadas y compararlo con las fórmulas | `experiments/21_results.json` l. 5-6, 57, 62, 69, 81 |
| «Drifts D1-D7 en S17» y «parches S22-S26» | S17 encontró 5 divergencias; D6 y D7 llegaron en S20 y S23, y la lista D1-D7 es una consolidación de S80. Además hay **dos numeraciones D distintas** (`DRIFTS_S17.md` y `MIROVA_DIVERGENCES.md`). Los parches retirados en S27 vienen de S6 a S26 | `docs/DRIFTS_S17.md:9`; `docs/SESSION_INDEX.md:18,23`; memoria `project_s26_parches_no_mirova.md` |

Dos más que no venían en el encargo pero que cualquier pieza puede repetir:

- **«Código abierto».** El repositorio es público pero **no tiene licencia** (`gh api repos/MendozaVolcanic/VRP-chile`:
  `license: null`, consultado hoy). Mientras no haya licencia, decir «código público», no «abierto».
- **«Recall 50 → 80 % en S27».** Desde S147 está **SIN INSTRUMENTO**: era circular, y el único A/B limpio dio 6
  contra 6 (`docs/audit_s147/VERIFICADOR_H_A01.md:23`; `docs/MISSION.md:386-391`). No usarlo como logro.

---

## 1. Números de escala (medidos hoy)

| qué | valor | de dónde sale |
|---|---|---|
| Inicio | 2026-04-04, commit `de88fdcfe` | `git log --reverse origin/main` |
| Sesiones numeradas | S1 a S163; ritmo muy desigual: S1 a S80 en siete semanas (al 2026-05-26), S80 a S163 en cinco meses | mensajes de commit; la cuenta de sesiones reales (no números) está POR MEDIR (§6) |
| PR | 867 en total, 856 mergeados, el primero el 2026-05-10 (antes se commiteaba directo) | `actividad_repo.out` |
| Commits en `main` | 12.299: 2.096 humanos o de Claude a nombre de Nicolás, 10.203 de bots (NRT, sincronización con Mirova-v1) | `actividad_repo.out` |
| Días con commit humano | 120 de 206 días calendario | `actividad_repo.out` |
| Tokens (ventana en disco: 2026-05-20 a 10-26) | 48.143 respuestas del modelo, 59 % de subagentes. Salida 27,6 M; lectura de caché 14.697 M; escritura de caché 436 M | `medir_transcripts.out` |
| Costo equivalente a API de esa ventana | **USD 6.754 a 9.572** (rango por los supuestos de precio de caché) | `costo_equivalente_api.out` |
| Horas activas en esa ventana | 217 a 288 horas de reloj; 256 a 344 horas-sesión (las sesiones en paralelo suman) | `medir_tiempo.out` |
| Reglas de método | 104 reglas A con párrafo propio (A1 a A119; 15 números sin párrafo); al menos 18 llevan una marca posterior de que cayeron, se rebajaron o se matizaron | `reglas_A.out` (el 18 es un piso: el patrón no reconoce todas las formas de marca) |

**Cómo leer el costo.** No es lo que pagó Nicolás: si usa suscripción, pagó la cuota. Es lo que costaría el
mismo tráfico por la API, con la tabla de precios de la skill `claude-api` (cacheada el 2026-10-06). El rango
sale de dos supuestos declarados en el script: escritura de caché a 1,25 o 2 veces el precio de entrada, y
lectura de caché al precio publicado o, cuando la tabla no lo da, entre 0,05 y 0,1 veces la entrada. La lectura
de caché domina (casi 15 mil millones de tokens), que es lo esperable en sesiones largas que releen el mismo
contexto. **Lo que falta**: de S1 a ~S62 (2026-04-04 a 05-19, 37 días con commit humano) no hay transcripts en
disco, porque Claude Code los borra; ese tramo está POR MEDIR (§6).

---

## 2. Estructura propuesta: ocho capítulos

Cada capítulo dice su mensaje, la evidencia que lo sostiene, la figura o tabla con su script, y desde qué
perspectiva habla (C = científica, I = ingeniería, G = gestión del trabajo con IA, O = operador de OVDAS).

### Capítulo 1. La trayectoria: de construir un detector a demostrar que es el de MIROVA (C, I)

**Mensaje.** El proyecto cambió tres veces de pregunta: primero «¿detectamos lo que MIROVA detecta?», después
«¿nuestros números de cierre son ciertos?» y al final «¿somos el mismo detector que MIROVA, por sensor?». Cada
cambio llegó porque la pregunta anterior se agotó o resultó mal planteada.

| etapa | sesiones y fechas | qué se buscaba | qué se logró | qué se abandonó y por qué |
|---|---|---|---|---|
| 1 | S1-S16, 04-04 a 04-23 | pipeline VIIRS y MODIS para 11 volcanes | calibración contra OSF v2.5 en S14 (`docs/SESSION_INDEX.md:13`, commit `5478bce66`) | el sigma-gating de S12 bajó el recall de Tupungatito de 0,977 a 0,5 (`SESSION_INDEX.md:11,15`) |
| 2 | S17-S26, 04-23 a 04-29 | contrastar código con papers | NOAA-21 faltante (Láscar 0,52 a 0,86); se descubre que Di Bella no es MIROVA y que hay 9 parches sin paper (`SESSION_INDEX.md:17,20`) | en S27 se retiran vent-path, `exclude_zones` y Regla D (`MISSION.md:323-325`); tres retiros eran parciales (`:322,326,328`) |
| 3 | S27-S80, 04-29 a 05-26 | «MIROVA literal» y calibración por volcán | Test 1 integrado; kernel local; consolidación de S80 | el «50 a 80 %» de S27 quedó sin instrumento en S147; el Test 1 integrado resultó ser un detector propio (D30) |
| 4 | S81-S100, 05-26 a 06-03 | explicar la precisión de 0,024 | S86: 95,4 % de 3.687 «falsos positivos» son anomalías reales o fallas del cruce (`docs/AUDIT_S86.md:12-21`) | gates intra-radio S83-S85 retirados en S118 (#474) por redundantes |
| 5 | S101-S123, 06-05 a 08-09 | magnitud y posición | nadir fijo: Láscar MODIS 2,87 a 1,38 veces; VIIRS 375 global 2,27 a 0,78 (`docs/S102_...`, `docs/S103_...`); sesgo topográfico (S104) | D11 «irreducible» (S114) se rebajó tres veces (`MIROVA_DIVERGENCES.md:1547-1570`) |
| 6 | S124-S146, 08-26 a 09-20 | ¿los cierres se sostienen? | S139: la brecha es sobre-publicación, no recall (A98); S146: de 50 cierres sin respaldo, 27 se verifican, 5 en parte, 7 se refutan, 1 queda sin evidencia y 10 no eran cierres (`docs/AUDIT_S146.md:31-40`) | cayeron o se reabrieron D8, D11, D16, D26 y GAP #A |
| 7 | S147-S153, 09-20 a 10-18 | fijar el criterio y adoptar un detector | criterio de victoria (Nicolás, 2026-10-13, `MISSION.md:81-95`); regla de adopción escrita antes del resultado (#848); K a producción (#850, 2026-10-18 09:57:30 UTC) | se apaga el Test 1 integrado |
| 8 | S154-S163, 10-18 a 10-26 | propagar K y compararse con el código real | histórico reprocesado con K (#883, 68.072 records); código de MIROVA en OSF (S158); programa por sensor; regla del fondo de MATLAB en los tres sensores | D25 leído y no adoptado (D-48) |

Fuente de la tabla: informe del subagente de trayectoria, con cada fila anclada a archivo o commit; las celdas que
no traen ruta acá la tienen en ese informe y deben copiarse al relato.

**Figura 1.1.** Línea de tiempo: sesiones contra fecha, con las ocho etapas y los hitos (K, código de MIROVA,
MATLAB). **Script POR HACER**: `linea_tiempo.py`, desde `git log` (fechas de los commits propios de cada sesión,
no la etiqueta «SNN», que aparece en commits automáticos durante meses) y los encabezados de `docs/AUDIT_S*.md`.
**Figura 1.2.** Actividad por mes: commits humanos, PR y días con commit (`actividad_repo.out`, ya existe).

**Ojo con las fechas.** `docs/SESSION_INDEX.md:7` dice «S1-S8 2026-01 a 2026-03», pero el primer commit es del
2026-04-04; y S14 figura del 18 al 20 de abril con commit del 21. No resuelto: decidir antes de publicar.

### Capítulo 2. Lo logrado sin contacto con el autor de MIROVA (C)

**Mensaje.** Sin hablar con Coppola, sólo con lo que MIROVA publica (papers, la base OSF v2.5, la tabla y las
imágenes del sitio, y desde julio su código de VIIRS 750), se llegó a reproducir piezas de MIROVA a nivel de
máquina. Hay que separar con cuidado lo que está probado de lo que no.

| logro | estado | evidencia |
|---|---|---|
| Coeficientes VRP reconstruidos desde 48.360 filas del OSF; los adoptados coinciden con la mediana con error casi cero | VERIFICADO (con el matiz del §0) | `experiments/21_results.json` |
| Lectura del código de MIROVA para VIIRS 750: de 13 puntos del detector, 3 iguales y 10 distintos | VERIFICADO | `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md:19-20` |
| Port del código validado contra Octave en 791 de 791 escenas; reproduce su magnitud a ±1 a 3 % | SIN VERIFICAR en esta sesión (lo cita la sesión del congreso) | «spec por sensor §1», `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` |
| Regla exacta del fondo `fillmissing2` de MATLAB: 166 de 166 escenas (VIIRS 750), 404 de 404 filas en 191 escenas (MODIS), 422 de 422 escenas (VIIRS 375), contra MATLAB real | VERIFICADO | `LOOP_OBJETIVOS.md` l. 584-598 y 758 |
| Detector K en producción con regla de adopción previa: 0 alertas protegidas perdidas que decidan, negativos de 88,2/85,4 % a 2,5/3,7 % | VERIFICADO | `experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md`; `v1.log`, `v2.log`; `MISSION.md:7-17` |

**Lo que sigue abierto** (decirlo en la misma lámina o párrafo):
- La regla de MATLAB reproduce a MATLAB; no está probado que reproduzca lo que MIROVA publicó en alertas de un
  píxel (6 pasadas, el intervalo cruza cero; harían falta 50 a 100). Y no hay dato de que MIROVA use ese `.m`
  para MODIS (`LOOP_OBJETIVOS.md` l. 596). MATLAB deja NaN fuera de la envolvente convexa (l. 588-589).
- Sólo hay código de MIROVA para VIIRS 750; MODIS y VIIRS 375 se infieren de papers y datos.
- Magnitud baja en Chillán y Tupungatito: causa sin medir (§0).
- El recall de VIIRS 750 (73,3 %) y de MODIS (66,7 %) está lejos del de VIIRS 375 (96,8 %), con n chicos.

**Tabla 2.1** «verificado contra qué»: cada pieza, contra qué referencia (OSF, Octave, MATLAB, tabla del sitio,
TIF) y con qué n. **Script POR HACER**, pero sólo de compilación: los números ya existen en las fuentes de arriba.
**Figura 2.1** sobre-publicación C0 contra K por ventana (V1, V2): sale de `v1.log` y `v2.log`.

### Capítulo 3. Cómo mejoraron las auditorías (C, G)

**Mensaje.** La auditoría pasó de comparar un número con otro a preguntar si el instrumento puede medir lo que
dice medir. Cada fase nació de un error concreto, y las reglas A son el registro de esa historia.

| fase | desde | qué agrega | caso que la motivó | registro |
|---|---|---|---|---|
| F0 número contra número | S33 a S124 | reimplementar la métrica; ningún número transcrito a mano | S33: la métrica se confirmaba a sí misma, el recall bajó 18,6 puntos y una adopción de 1 h costó más de 6 h | `docs/PROCESS_RULES_S33.md:24,66-76,208-210`; memoria `feedback_s91_no_transcribir_numeros.md` |
| F1 verificador con contexto limpio | S120 a S134 | un agente que no vio la conversación revisa | en S134 refutó 5 enunciados y encontró algo propio en 4 de 4 frentes | A93 (`CLAUDE.md:1315-1332`) |
| F2 control con nulo medido | S144 | un control vale si su nulo se midió donde no hay nada | cuatro controles «obvios» rotos; el punto reflejado daba +0,1014 sin nada que detectar | A110 (`CLAUDE.md:1447-1465`), A116 |
| F3 mutaciones | S152, S156 | romper el código a propósito y exigir que el test falle por aserción | cuatro mutaciones «atrapadas» sólo porque el evaluador se caía | memoria `feedback_s152_mutacion_que_cae.md`, `feedback_s156_...md`; sin regla A |
| F4 pre-registro sellado | S151, S153 | la regla de decisión se escribe y se aprueba antes de ver el resultado | sin regla previa el resultado se interpretaba después de verlo (A95, A111) | `experiments/_s151_prereg_fk_11/PREREGISTRO.md:3-6`, `REGLA_ADOPCION.md:1-24`; sin regla A |
| F5 cobertura contra la referencia | S135 a S162 | contar las pasadas de cada brazo y la calidad de la referencia por mes | un brazo con 149 pasadas contra 203: sus «pérdidas» eran días que nunca miró | A108, A119 |
| F6 auditor de otro modelo | S121 a S162 | el que verifica es otro modelo que el que encontró | en V750-B, cada vuelta del verificador encontró un defecto grave en la regla de decisión | `GUIA_MAESTRA_AUDITORIAS.md` l. 319 y 412; memoria `feedback_s162_lecciones.md:21-23`; sin regla A |

Fuente: informe del subagente de método. **Hallazgo para destacar**: según
`docs/PROTOCOLO_AUDITORIA_PROFUNDA.md:226-248` (S128), lo que rinde es el **eje de comparación nuevo**, no la
profundidad: las auditorías con menos de 20 % de eje nuevo sólo produjeron deuda documental, y las de 50 % o
más produjeron todos los cambios del pipeline.

**Figura 3.1.** Reglas A por tramo de 20 sesiones, marcando cuáles cayeron después
(`reglas_A.out`: S1-S20 4, S21-S40 5, S41-S60 3, S61-S80 27, S81-S100 5, S101-S120 22, S121-S140 17,
S141-S160 21). **POR MEDIR**: clasificar a mano las marcas (el script da un piso de 18), y anotar qué fase
del método nació en cada tramo. Tres fases (mutaciones, pre-registro, otro modelo) no tienen regla A: decidir si
se registran o si el relato lo dice como hueco del propio registro.

### Capítulo 4. Los prompts y la forma de trabajar con la IA (G)

**Mensaje.** Lo que funcionó no fueron prompts ingeniosos, sino **estructura**: reglas escritas que se vuelven
tests, un dueño único por loop, y verificadores que no heredan el contexto del que encontró.

**Funcionó** (con su fuente):
- Verificador limpio como segundo buscador, no como sello (S134; S154, memoria `feedback_s154_duracion_sesion.md:18-19`).
- Convertir reglas en tests: en S129 una regla escrita se violó igual; el test que la reemplazó encontró el mismo
  bug en otro workflow al primer intento (memoria `feedback_s129_no_heredar_afirmaciones.md:34-49`).
- Worktree por subagente (A44) y persistir en el momento, no al cierre (M2, `docs/META_RULES_S80.md:35-49`).
- Loop con reglas de juego explícitas: máximo 5 agentes y 2 A/B, verificador obligatorio, el loop no toca
  producción y deja la decisión en un issue (`LOOP_OBJETIVOS.md` l. 25-51).
- Bloques de arranque y `/retomar` que verifican contra el remoto antes de creerle al traspaso.

**Falló o costó**:
- Briefs con premisas heredadas: tres premisas falsas pasadas a agentes en S129; un plan de otra sesión con 6 de
  11 tareas rotas (S140). **Este mismo encargo traía siete premisas que no se sostienen (§0)**: es un caso vivo.
- Subagente tomado como fuente de verdad (A48, A74).
- Fan-out de 27 agentes en S120, detenido por Nicolás a los ~10 min por consumo.
- Dos sesiones sobre el mismo loop (S153): una corrida de mutaciones de más de una hora quedó inválida.
- Sesiones hijas con loop (S162): una rama vivió 12 h sólo en disco; una hija editó archivos de producción sin el
  sí de Nicolás (memoria `feedback_s162_a45_antes_del_primer_edit.md`); una aprobación reenviada entre sesiones no vale.
- Sesiones largas: pasados ~45 intercambios hubo 3 errores; se acordó cerrar a ~30 (memoria `feedback_s154_duracion_sesion.md:11-19`).
- 65 PR en tres sesiones (S76-S78) llevaron al tope de PR por sesión (A53).

**Guías.** `GUIA_MAESTRA_AUDITORIAS.md` (preámbulo anti-fabricación, plantilla del verificador l. 315-340) sí es
evidencia del proyecto. Las `GUIA_PROMPTING_*.md` son pautas oficiales de prompting, no registro de lo que pasó:
citarlas como «lo que se adoptó», no como resultado. La propia guía marca como SIN DATO cómo responde el modelo
actual (l. 417-418).

**Tabla 4.1** «estructura, para qué, cuándo falló, regla que la corrige». Compilación desde las fuentes de arriba;
no necesita script nuevo. **POR MEDIR**: cuántas sesiones usaron subagentes y cuántos subagentes por sesión (los
transcripts lo tienen: 59 % de las respuestas del modelo son de subagentes, `medir_transcripts.out`), y qué
fracción de los hallazgos de cada auditoría vino del verificador y no del buscador.

### Capítulo 5. Errores que se pudieron evitar (C, I, G)

**Mensaje.** La IA no se equivoca al azar: se equivoca con confianza, de forma plausible y en lo que nadie vuelve
a mirar (una cita, un denominador, una convención, un cierre). En todos los casos la frenó algo externo a ella: el
PDF renderizado, el script re-corrido, un verificador sin su contexto, MATLAB real, o el geólogo que sabía que el
número no podía ser ese. (Formulación de la sesión del congreso, `PROPUESTA_REVISION_2026-10-26.md` §4; se
sostiene con la tabla que sigue.)

| caso | sesión | costo según el documento | regla que lo evita hoy |
|---|---|---|---|
| Di Bella (INGV Catania) citado como MIROVA | S26 | ~10 sesiones (`CLAUDE.md:278-280`) | A9 |
| Cita corrupta de Coppola 2023 §2.5 («5 %», «aleatorios») | escrita S110, detectada S146 | no registrado | marca en A76; A95(a), leer la página renderizada |
| «482 píxeles» que ningún campo reproduce | S123, detectado S146 | no registrado; queda SIN VERIFICAR | A87 |
| 2.527 a 9.196 con la tasa plana (cambió el denominador) | S130 | una discrepancia «bloqueante» pasó a nota al pie | A90 |
| Cuatro cierres caídos el mismo día | S145 | «un cierre falso apagaba tres frentes»; 50 de 89 cierres sin respaldo | A111 |
| D11 «irreducible» | S114, cayó en S124, S138, S146 | «cuesta sesiones enteras»; dos horas de PDF hallaron lo que 23 sesiones de documentos derivados no | A95, A113 |
| Rebaja sin propagar a `MISSION.md` | S146 | no registrado | A113 |
| Regex inventada por un subagente | S77 | conclusión #1 del PR #196 inválida (corregida en #197) | A48 |
| Parches contra la misión (orígenes S6 a S26) | demolidos S27 | 10 sesiones midiendo «MIROVA con parches» | las 3 preguntas de `MISSION.md` |
| JSON corrupto por reprocesos en paralelo | S77 | no registrado | A47 |
| `return` borrado al insertar código | S79-S80 | 1 sesión sin detectar | A49, A50 |
| `stash pop` de un stash ajeno | S137, repetido S161 | archivos ajenos reaplicados | A96 |
| Suite corriendo mientras se edita | S145 | en S153, una corrida de más de 1 h inválida | A112 |
| Merge con el CI en rojo (#676) | S142 | `main` con un test fallando | enmienda S142 de A39 |
| Bloqueo de la cuenta Earthdata | S104, S146 | 10 min cada vez; en S146, 9 jobs reintentando | A71 |
| `timeout` copiado de un template | S129 | 8 de 15 jobs muertos, 6 h de CI | guard `test_guard_timeout_vs_ventana_s129.py` |
| Datos viejos tomados como problema | S25 | ~4 h en un Test 1 redundante | A8 |
| Métrica que se confirmaba a sí misma | S32-S33 | más de 6 h | R1, R3, R7 de `PROCESS_RULES_S33.md` |
| Creencia vieja: «MIROVA no publica código» | publicado 07-24, sabido 10-21 | tres meses, y un resumen enviado que dice «código cerrado» | sin regla A: **POR DECIDIR** (vigilar fuentes externas con fecha) |

Fuente principal: informe del subagente de método, con cada costo tal como lo registra el documento. **La mitad
de los casos no tiene costo registrado**: el relato debe decirlo así y no estimarlo por encima.

**Figura 5.1.** Para cada error: cuándo se cometió y cuándo se detectó (barras de «vida» del error, en
sesiones). **Script POR HACER**: `vida_de_errores.py`, con las sesiones de la tabla (escritas una vez, desde las
marcas de `CLAUDE.md`). Da la idea más fuerte del capítulo: los errores de cita y de cierre vivieron decenas de
sesiones; los de código, una o dos.

### Capítulo 6. El rol de Nicolás (G, O)

**Mensaje.** La IA hizo casi todo el trabajo de máquina; las decisiones de qué medir, contra qué y cuándo parar
fueron de Nicolás, y su conocimiento de los volcanes corrigió a la IA donde los números parecían bien.

**Decisiones.** El loop numeró sus decisiones de D-1 a D-48, de mediados de octubre al 2026-10-24 (D-48) (`LOOP_OBJETIVOS.md` §5,
l. 516-568; D-46 a D-48 en la bitácora, l. 1305-1308, 1470-1471 y 1500). Antes del loop: criterio de victoria
(2026-10-13, `MISSION.md:81`), regla de la anomalía mayor (2026-10-09, `MISSION.md:221`), «para VIIRS 750 manda el
código» (2026-10-21). Las de más peso: D-4 (qué es una alerta protegida), D-9 (alertas mínimas), D-13 (repetir y
unir intentos aunque tome más tiempo, contra la recomendación del loop), D-20 y D-21 (regla y merge de K), D-48
(«sobre las decisiones mías haz lo que tú recomiendes», aplicada a 14 decisiones).

**Donde corrigió a la IA** (`CLAUDE.md`): A38 (S73, lo paró antes de un borrado masivo), A45 (S75, «¿no tienes que
salvar la configuración actual antes?»), A62 (S97, insistió en Tupungatito hasta que se cavó hondo), A68 (S103,
«hay demasiado» en el mapa), A72 (S104, ocultar en el tablero un artefacto que no se debía generar), A77 (S112,
NdC: insistió cinco veces y tenía razón), A115 (S147, un umbral inventado que el dato ya respondía), y el freno al
fan-out de S120. **Corrección al encargo**: A97 no menciona a Nicolás. **Caso inverso**: D-33, la IA mostró que la
opción que Nicolás había elegido era peor y él la reemplazó por D-34 el mismo día (l. 531-532).

**Lo que no se habría hecho sin él**: el criterio de victoria (es una decisión de valor sobre qué error es peor en
monitoreo volcánico), las lecturas físicas que separan artefacto de señal real (A54, A72), y los sellos de cada
pre-registro, que por diseño el agente no puede poner (`LOOP_OBJETIVOS.md` l. 46-48).

**Tabla 6.1** decisiones D por fecha y tipo (sello, merge a producción, criterio, alcance). **Script POR HACER**:
`decisiones_D.py`, que lea la tabla del §5 y la bitácora. **POR MEDIR**: cuánto tiempo pasó entre que una decisión
quedó lista y Nicolás respondió (es el cuello de botella real del loop), y cuántos mensajes escribió él
(`medir_tiempo.out` da 581, pero es un techo: incluye encargos entre sesiones como este).

**Perspectiva del operador de OVDAS.** Ninguna fuente del repo mide todavía la experiencia del operador. Lo que sí
se puede decir con datos: con K, publicar en 2,5 a 3,7 % de las pasadas donde MIROVA miró y no vio nada, contra
85 a 88 % antes (§0). **POR MEDIR**: traducirlo a falsas alertas por volcán y por semana en el tablero, y una
prueba con un operador real (cuánto tarda en leer una alerta, cuántas descarta).

### Capítulo 7. Tiempo y costo (G)

**Mensaje.** Fue barato en dinero y caro en atención. El costo equivalente a API de la ventana medida
(USD 6.754 a 9.572) es chico frente al tiempo que costó revisar; las 217 a 288 horas de reloj de sesiones activas no
son horas de Nicolás frente a la pantalla, pero sí el tiempo durante el cual hubo trabajo que él debía revisar.

| medida | valor | estado |
|---|---|---|
| Tokens y costo, 2026-05-20 a 10-26 | arriba, §1 | VERIFICADO (script) |
| Tokens por mes | la salida pasa de 1,6 M (fin de mayo) a 14,0 M (octubre) | VERIFICADO (`medir_transcripts.out`) |
| Costo de S1 a ~S62 | sin transcripts | POR MEDIR |
| Horas de Nicolás | no se separan de las de la sesión | POR MEDIR |

**Método propuesto para el tramo sin transcripts.** Dos cotas, y decir las dos: (a) cota baja, cero costo extra
(si se quiere hablar sólo de lo medido); (b) cota alta, el costo por día activo de la primera ventana medida
(fines de mayo) por los 37 días con commit humano antes del 2026-05-20. Si Nicolás tiene el registro de
facturación o de uso de su cuenta, eso reemplaza la estimación. Nunca dar un número único.

**Figura 7.1.** Tokens de salida por mes y por modelo (`medir_transcripts.out`). Se ve el salto de octubre:
sesiones paralelas, loops y verificadores de otro modelo.

### Capítulo 8. Qué haría distinto si empezara hoy (C, I, G, O)

Propuesta de contenido (cada punto con su caso):
1. **Escribir el criterio de victoria el primer día**, en las dos direcciones (recall y publicación en
   negativos). Se escribió entre S147 y S151 (2026-10-13), y recién en S139 se vio que la brecha real no era el recall
   sino la sobre-publicación (A98).
2. **Leer el paper renderizado y vigilar las fuentes del autor desde el inicio**: citas del grupo equivocado
   (A9), citas corruptas (A76) y el código de MIROVA descubierto con tres meses de atraso.
3. **Un cierre sólo con script y nulo medido**: el censo de S145 y S146 encontró 50 de 89 cierres sin respaldo.
4. **Pre-registro desde el primer A/B**, no desde el S151.
5. **Una sola sesión dueña de cada loop y de cada rama**, con worktree propio desde el principio (A44, A47, S153).
6. **Licencia y declaración de uso de IA** desde el primer commit público.
7. **Guardar los transcripts** (subir `cleanupPeriodDays` o exportarlos): sin ellos, el costo de los dos primeros
   meses no se puede medir.
8. **Hablar con el autor temprano**: el borrador del correo existe desde S139 y no se envió.

---

## 3. Qué pieza usa qué

| capítulo | paper (Volcanica) | charlas del congreso | memoria |
|---|---|---|---|
| 1 trayectoria | breve, en métodos o suplemento | una lámina de línea de tiempo | completo |
| 2 sin contacto con el autor | núcleo de validación, con lo abierto | lámina central de AT8.7 | completo |
| 3 auditorías | suplemento «cómo se verificó» | una lámina | completo |
| 4 trabajo con IA | declaración de uso de IA (lo piden las guías: herramienta, para qué, cómo se supervisó) | lámina de AT3.6 | completo |
| 5 errores evitables | dos o tres casos en la declaración | dos láminas (buenos y malos) | completo |
| 6 rol de Nicolás | contribución de autores | una lámina | completo |
| 7 tiempo y costo | declaración de uso de IA | una cifra con su rango | completo |
| 8 qué haría distinto | discusión | cierre | completo |

La sesión del congreso ya tiene casos buenos y malos con fuente
(`congreso geologico 2026\2_PRESENTACIONES\PROPUESTA_REVISION_2026-10-26.md` §4) que coinciden con los capítulos
2, 3 y 5: usar esa lista y no duplicarla.

---

## 4. Riesgos de contarlo mal

- Repetir las premisas del §0 (sobre todo «Coppola no respondió», «1-3 %», «D17» y «código abierto»).
- Mostrar recall sin su contrapeso de publicación en negativos limpios (la sesión del congreso encontró que el
  99 % de los mazos no lo tenía, y que `docs/paper/sec6_validation.md` argumenta no reportar precisión, a
  contrapelo del criterio del 2026-10-13).
- Citar números de `data/audit_continuous/latest.json` sin el commit: el archivo cambia cada semana.
- Presentar la regla de MATLAB como «reproducimos a MIROVA»: reproduce a MATLAB.
- Atribuir a la IA decisiones de Nicolás, o al revés (D-33 y D-34).
- Dar un costo único: siempre rango, y decir que no es lo pagado.

## 5. Coordinación

Este documento se comparte con las sesiones del paper y del congreso. Lo que cada una necesita de acá: el §0
(correcciones), el §1 (números de escala con su script) y la tabla del §3. Lo que este plan toma de ellas: la
lista de casos de la propuesta del congreso (§4 de ese archivo) y el estado del manuscrito
(`docs/paper/README.md`).

## 6. Qué falta medir, en orden

1. **Fechar cada sesión** desde sus commits propios (`linea_tiempo.py`) y contar sesiones reales, no números
   (hubo hijas, relevos y sesiones paralelas).
2. **Costo de S1 a ~S62** con el método del capítulo 7, o con el registro de uso de la cuenta.
3. **Clasificar a mano las marcas de las reglas A** (el script da un piso de 18) y fechar qué fase del método
   nació en cada tramo.
4. **Separar mensajes de Nicolás** de los encargos entre sesiones (`medir_tiempo.py` hoy da un techo de 581).
5. **Latencia de decisiones**: tiempo entre «lista para Nicolás» y su respuesta (`decisiones_D.py`).
6. **Falsas alertas por volcán y por semana con K**, para la perspectiva del operador.
7. **Vida de cada error** (`vida_de_errores.py`) para la figura 5.1.
8. **Fracción de hallazgos que trae el verificador** frente al buscador, en las auditorías S134 a S162.
9. Resolver las fechas contradictorias de `docs/SESSION_INDEX.md` (S1-S8 y S14).
