# Auditoría S175: el sistema corriendo después de la S160

> **Estado: SÍNTESIS PARCIAL (cuatro de cinco frentes).** F1 (MODIS con la vía «código MIROVA») corre el lunes
> 2026-11-09 desde las 09:30 UTC, después del audit semanal, y se agrega a este documento con su verificador.
> Escrita el 2026-11-07 (hora del servidor Sat, 07 Nov 2026 17:44:29 GMT) por el orquestador (Opus 5.5).

## 0. Encabezado

- **Plan sellado**: `docs/PLAN_AUDITORIA_S175.md`, SHA_PLAN = `a325ac8ff8c480fc88fe91d07b1b52046d0c0997` (segundo sello,
  aprobado por Nicolás en la sesión de auditoría). Los criterios del §3 no cambiaron después del sello.
- **Base de medición**: `origin/main` = `752d348bc67190e53b610989877e2405d238a1bc`, fijada en la ola 0 (Sat, 07 Nov 2026
  04:10:15 GMT). Referencia: `mirova_v1_snapshot/registro_vrp_consolidado.csv` sha256 `f833bfde...`, OCR `577a336e...`,
  `latest_consolidado.csv` `dee76837...` (registro completo en
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\REGISTRO_AGENTES.md`).
- **Frentes**: F0 (pendientes de S160 sin eje), F2 (VIIRS 375 en producción), F3 (decisiones y cierres S160 a S174), F5
  (identidad del pareo con MIROVA, pedido de Nicolás). F1 pendiente. Recortados del plan: VIIRS 750 con ROI B4 (lo vigila
  la sombra de #945) y F4, vencimientos simulando la ausencia (sus pendientes pasaron a F0 con fecha).
- **Sólo veredictos de verificador.** Cada hallazgo de la tabla del §3 lleva el veredicto y la gravedad del verificador,
  no los del auditor. Los que no pasaron el corte del verificador van en el §6 con su conteo.

### Limitaciones que el lector tiene que saber

1. **El esfuerzo pedido no llegó.** La sonda de la ola 0 (Fable, `effort: high` del Agent tool) declaró
   `reasoning_effort 25`. Por eso los auditores se lanzaron como sesiones con el esfuerzo fijado en high por la app, y aun
   así los cuatro declararon `reasoning_effort 15` en su encabezado. De los verificadores, V5 leyó 10 en su prompt de
   sistema y V0, V2 y V3 declararon SIN DATO. No sabemos si ese número es la misma escala que el «high» de la app.
   Contrapeso observado: los cuatro auditores reprodujeron todas sus líneas base rojas (§5), comprobaron sha256,
   usaron controles positivos y declararon lo que no miraron.
2. **Modelos.** El plan pedía Fable como auditor y Opus como verificador. Una sesión sólo puede abrir otras de su modelo o
   más baratas, así que los auditores corrieron en Opus 5.5 y los verificadores en Sonnet 5.5. La regla «verifica otro
   modelo» se cumplió; el auditor no fue el previsto.
3. **F2 lanzó su propio verificador** (subagente, carpeta `experiments\_s175_audit\f2\verificador\`), fuera del plan. No
   cuenta como verificación; la de F2 es la de V2.
4. **F1 no está.** Todo lo que este documento dice de MODIS sale de F0, F3 y F5, no del frente que audita la vía.

## 1. En una pantalla

1. **Los aciertos contra MIROVA son la misma anomalía, medidos con la vara correcta.** Con la distancia de la tabla de
   MIROVA y un origen común, de 881 aciertos publicados por misma pasada sólo 1 cae fuera de nuestros píxeles, y por 0,1 km
   (302, publicado por el auditor, sin verificar). Lo que parecía «otra fuente» era el instrumento: la distancia del OCR
   difiere de la de la tabla en el 19 % de las pasadas que traen las dos (301, en parte) y el banco compara radios desde
   orígenes distintos (303).
2. **El recall por noche se infla frente al recall por pasada.** Cuenta como acierto una pasada distinta en otro lugar
   (caso real: Cordón Caulle VIIRS 750, 2026-10-10). Con misma pasada el recall baja unos 2 puntos en VIIRS (304).
3. **VIIRS 375 no pierde protegidas de la tabla de MIROVA.** Las 5 pasadas protegidas no publicadas son todas filas sólo OCR
   sin geometría confiable o de Suomi NPP antes de Mirova-v1#20; con fila de la tabla se pierde 0 de 115 (V2-01, que
   matiza F2-201 y F2-202).
4. **La sobre-publicación de Lastarria es en dos tercios la regla D-9.** Sin las alertas mínimas reetiquetadas, Lastarria
   publica en negativos limpios el 11,6 % de sus pasadas, igual que Puyehue (V2-03 sobre F2-203).
5. **El criterio de victoria tiene poco poder fuera de Chillán**: «ninguna protegida perdida» no tiene casos en 5 de 11
   volcanes, y hay 42 protegidas diurnas fuera del criterio por diseño (309; 308 sin verificar).
6. **Documentos rectores desfasados**: `SINTOMAS.md` describe el MODIS de producción como K y con `_interp_geo`, cuando
   98 de 98 records MODIS desde el 2026-11-02 son de la vía (251, gravedad 3).
7. **Pendientes de S160 que siguen abiertos con gravedad 3**: VIIRS 750 en cumbre (101, 102), el veto de D18 colgado de
   una alerta de 1,00 MW truncada (103) y el token (107: rotar antes del 2026-11-27).

## 2. Lo que esto dice de si llegamos a los objetivos

El objetivo es reproducir lo que MIROVA publica (`docs/MISSION.md`): no perder ninguna protegida y callar donde MIROVA
calla. Esta auditoría midió por primera vez si el «acierto» es la misma anomalía, y la respuesta es sí cuando se usa la
distancia de la tabla (punto 1). Las métricas que hoy publica el sistema tienen tres sesgos medidos:

- el recall por noche acepta otra pasada como acierto (304, V2-02);
- el tablero marca «MIROVA confirmó» con ±60 min y sin D-9, y su texto dice «en esta pasada» (F2-204 y V2-04, en 0 records
  cambia hoy la publicación);
- el veredicto depende de qué volcán: casi todas las protegidas son de Chillán y en 5 volcanes no hay ninguna (309, 308).

Ninguno muestra una protegida de la tabla perdida. Lo que se ve es que la vara mide algo más ancho de lo que dice.

## 3. Hallazgos verificados

Gravedad del verificador (1 a 5). Veredicto: C = CONFIRMADO, P = CONFIRMADO EN PARTE. Ninguno REFUTADO.

| id | frente | qué | veredicto | gravedad |
|---|---|---|---|---|
| 251 | F3 | `SINTOMAS.md` describe el MODIS de producción como K y con `_interp_geo` (l. 127 pleno; l. 25 sólo para MODIS) | P | 3 |
| 101 | F0 | 203 sigue abierto: cúmulos de cumbre VIIRS 750 en 0,0 MW que el tablero no publica (30 de 97, 7 con alerta, ninguna protegida); «sin camino» es exagerado | P | 3 |
| 102 | F0 | D32 abierta: publicamos el cúmulo y MIROVA suma todos los píxeles alertados | C | 3 |
| 103 | F0 | Decisión 6 de S160 y C-10: el veto de D18 cuelga de una alerta MODIS de Láscar de 1,00 MW truncada | C | 3 |
| 107 | F0 | Rotar `EARTHDATA_TOKEN` antes del 2026-11-27 (vence el 2026-12-07 18:03 UTC) | C | 3 |
| 301 | F5 | La distancia del OCR discrepa de la tabla en el 19 % de las pasadas con ambas; casi todos los aciertos «de otra fuente» se apoyan en ella | P | 2 |
| 303 | F5 | Comparar nuestro radio con el de MIROVA mezcla orígenes (vent contra centro de MIROVA); lo hace `banco_paridad.py:450` | C | 2 |
| 304 | F5 | El recall por noche cuenta una pasada distinta en otro lugar; con misma pasada baja unos 2 puntos en VIIRS | C | 2 |
| 305 | F5 | La tabla de MIROVA no lista la mayoría de las pasadas de Suomi NPP; el denominador de negativos se mueve por satélite y mes | C | 2 |
| 309 | F5 | 42 protegidas diurnas fuera del criterio; las 36 de Chillán tienen protegida nocturna a menos de 12 h | C | 2 |
| F2-201 | F2 | 5 de 171 pasadas protegidas V375 no publicadas (todas sólo OCR sin geometría o Suomi NPP previo a V31) | P | 2 |
| F2-202 | F2 | Pérdidas concentradas en cenit de 50° o más y en Suomi NPP (misma capa que 201) | P | 2 |
| F2-203 | F2 | Sobre-publicación en negativos limpios: 3,9 % agregado, Lastarria 25,6 % (dos tercios por D-9) | P | 2 |
| F2-204 | F2 | «MIROVA confirmó» del tablero: ±60 min, sin distancia ni D-9; 647 de 2.225 publicados sin alerta de su pasada | P | 2 |
| F2-205 | F2 | La regla sellada de la sombra V375-E da CUMPLE en (b) sin negativos | P | 2 |
| F2-206 | F2 | El lector de la sombra sella el `index.html` del 2026-11-02, no el de la base | P | 2 |
| F2-207 | F2 | La tabla de MIROVA del snapshot termina el 2026-11-02: sin negativos limpios desde el 03 | C | 2 |
| F2-212 | F2 | `banco_paridad.main` y `clasificacion_referencia` usan la etiqueta original y no D-9 | C | 2 |
| 252 | F3 | La nota A85 corregida por #950 en `CLAUDE.md` sigue sin marca en `SINTOMAS.md` | C | 2 |
| 254 | F3 | «Sí, arréglalos» (falsos verdes de cenit) no está en main; con el código de la base, insumo vacío y alertas sin cenit salen SIN SUSTRATO y se rotulan OK | C | 2 |
| 257 | F3 | El censo S145 no ve las dos líneas base rojas ni los cierres desde S160 (65 coincidencias fuera de `censo.DOCS`) | C | 2 |
| 258 | F3 | Parámetros del lector sellado de V750-A fijados sin frase de Nicolás (declarados); una cita mezcla dos decisiones (V3-01) | P | 2 |
| 104 | F0 | Decisión 9, V0b-01 y C-07: K1 sigue en -0,8 y el tope D9 acoplado a K1 | P | 2 |
| 105 | F0 | C-09: la fila OCR de Lastarria del 2026-04-18 sigue contando como protegida | P | 2 |
| 106 | F0 | V2-09: umbrales de cumbre hasta `inner_radius`; «MIROVA usa 7 × 7 píxeles» no se sostiene tal cual | P | 2 |
| 109 | F0 | 49 pasadas MODIS nocturnas que MIROVA lista y no tenemos desde el 2026-09-14 (ninguna con alerta) | P | 2 |
| 113 | F0 | V3-02: el medidor de cadencia ignora el disparador externo, que da casi 13 de 16 corridas diarias | C | 2 |
| 114 | F0 | Los `hallazgos.csv` de las auditorías no entran a git (`.gitignore:40 *.csv`); ya corregido para S175 a mano | P | 2 |
| 115 | F0 | 166: las bandas `RECALL_MIN` del audit siguen calibradas sobre C0 y juzgan a K y a la vía | P | 2 |
| 253 | F3 | Decisión 3 de S174 (`sin_grilla`/`sin_mxd03` como K con aviso) no implementada; la aprobación consta sólo en el registro de la coordinadora | P | 1 |
| 306 | F5 | Snapshot del consolidado semanal y OCR horario: entre audits el banco ve alertas OCR sin RUTINA | C | 1 |
| 307 | F5 | Nueve alertas OCR de 1,0 MW con nota de truncado; sólo 1 decide una pasada entre septiembre y noviembre | P | 1 |
| 311 | F5 | Las tres copias de `mirovaEqVrp` difieren y el guard de tres vistas sólo compara `isValidDetection` | C | 1 |
| 312 | F5 | `n_misma_pasada` del audit compara máximo contra máximo, no noches con acierto en la misma pasada | C | 1 |
| 110 | F0 | `noches_sin_datos` y el recall son ciegos a un satélite callado (el vigilante por plataforma lo cubre a 72 h) | C | 1 |

**Hallazgos propios de los verificadores**: V2-01 (las 5 protegidas no publicadas son del estrato OCR sin geometría, g2),
V2-02 («111 de 111 noches» acepta cualquier pasada, g2), V2-03 (dos tercios del exceso de Lastarria es D-9, g2), V2-04 (el
texto del tablero dice «en esta pasada» y la lógica busca ±60 min, g2), V2-05 (sombra V375-E y snapshot congelado se
componen mal, SOSPECHA, g2), V3-01 (cita de 258 mezcla dos decisiones, g1), V3-02 (518 records MODIS de enero a junio de los
34 volcanes fuera del cron sin `processed_utc` ni `regimen`, g1), V5-01 (la regex de I8 deja fuera 20 de 63 notas de
truncado, g1), V5-02 (el origen de 303 también torna dudosa la clase summit/far de Tupungatito y Puyehue, SOSPECHA, g2),
V0-01 (la «fracción 19 %» de 101 depende de la ventana, g1), V0-02 (`f0_cadencias.py` emite una advertencia de sintaxis, g1).

## 4. Informes de cada agente

| agente | archivo |
|---|---|
| F0 | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f0\INFORME.md` |
| F2 | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f2\INFORME.md` |
| F3 | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f3\INFORME.md` |
| F5 | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f5\INFORME.md` |
| V0, V2, V3, V5 | `...\experiments\_s175_audit\v0\VERIFICACION.md` (y `v2`, `v3`, `v5`), cada una con su `caminos.md` sellado antes de abrir archivos |

## 5. Líneas base rojas (regla B: el instrumento tiene que ver lo que ya sabemos)

Todas se reencontraron.

| frente | línea base roja | resultado |
|---|---|---|
| F5 | misma pasada a ±120 s en el audit del 2026-11-02 | 125/194, 32/42, 14/16, exacto |
| F5 | acierto sintético por otra fuente, par desfasado 3 min, port contra node forzado, fila truncada de Chillán, hueco de un satélite | las ocho, vistas |
| F2 | 201 de S160 (C1 de escena: 4 de 2.452) sobre `d516b9d8c`; caída de Chillán con el cenit; lector de la sombra sin datos | las tres, vistas (el lector da NO LEGIBLE) |
| F3 | nota A85 desfasada en `77e54e8e0^`; hallazgo 281 en `d516b9d8c` | vistas con un instrumento nuevo; el censo S145 no ve ninguna (257) |
| F0 | decisión 1 resuelta (`0d73f2a4e`, #891); decisión 6 abierta; Suomi NPP sin records después del 2026-11-02 13:00 UTC | las tres, vistas |

## 6. Hallazgos sin verificar (no pasaron el corte del §3 del plan)

Se publican con su conteo y son la puerta de S176: F5 302, 308 y 310 (3); F2 F2-208 a F2-211 y F2-213 (5); F3 255, 256 y 259 a 265 (9);
F0 108, 111, 112 y 116 a 129 (17). En total 34 de 69 hallazgos de auditor. Los más útiles para la próxima sesión: 302 (los
aciertos por misma pasada son el mismo foco, la respuesta directa a la pregunta de Nicolás), 108 (la cola de campo no se
tocó desde S160), 256 (la memoria dice que el MxD03 se ignora; la vía lo usa) y 111 (nadie mide la fracción MODIS NRT).

## 7. Pruebas de campo (lo que sólo se cierra mirando)

- Las tres alertas MODIS de Láscar posteriores al congelamiento de los TIF (2026-09-25 08:00, 2026-10-08 08:00, 2026-10-26
  07:55 UTC): mirar las láminas PNG de MIROVA de esas pasadas.
- Chillán VIIRS NOAA-21 2026-10-18 06:48 UTC (25,79 MW): la única protegida cuyo punto de MIROVA cae fuera de nuestros
  píxeles con la distancia de la tabla (302, sin verificar).
- Cordón Caulle VIIRS 750 2026-10-10: la noche que el recall da por vista con una pasada de las 04:54 a 18,5 km, mientras la
  protegida de las 05:54 está en `PERDIDAS_ACEPTADAS` (304).
- C-04 (Tupungatito VIIRS 375 2026-09-28 05:18) y C-06 (Suomi NPP, respondido por el issue #943): actualizar la cola de
  campo, que no se toca desde S160 (108).

## 8. Decisiones para Nicolás

| # | decisión | recomendación |
|---|---|---|
| 1 | Rotar `EARTHDATA_TOKEN` (107) | sí, antes del 2026-11-27; sólo tú puedes hacerlo |
| 2 | Corregir `SINTOMAS.md` (251, 252): marca S172 en l. 25 y 127 y la nota A85 | sí, PR de documentación sin riesgo; es lo que se lee antes de proponer una palanca |
| 3 | Mergear #952, los falsos verdes de cenit (254) | sí, después de su verificador y con CI verde |
| 4 | Implementar la decisión 3 de S174 (253) | sí; ya la aprobaste, falta hacerla |
| 5 | Publicar el recall por pasada al lado del recall por noche (304, V2-02) | sí, en el audit semanal; no cambia la detección |
| 6 | Medir la posición de MIROVA con la tabla y con origen común, no con el OCR (301, 303) | sí, en el banco y el audit |
| 7 | «MIROVA confirmó» del tablero (F2-204, V2-04) | alinear la lógica a la pasada a ±120 s con D-9, o cambiar el texto; recomiendo la lógica, porque el operador lee «en esta pasada» |
| 8 | VIIRS 750 en cumbre (101, 102) | darle un camino nuevo dentro del programa de V750 (D25 no se adoptó), medido contra la tabla; ninguna alerta perdida es protegida, así que no es urgente |
| 9 | La lectura del truncado de MODIS (103, 307) | decidir si una alerta escrita 1,00 MW se lee como 1 o como «entre 1 y 2»; de eso cuelga el veto de D18 |
| 10 | `.gitignore` y los `hallazgos.csv` (114) | agregar una excepción para `experiments/_s*_audit/**/hallazgos.csv` |
| 11 | Esfuerzo de los agentes (limitación 1) | aceptar esta auditoría con la limitación escrita y, antes de la próxima, averiguar qué significa el 15 en la escala de la app |

## 9. Registro de agentes

| agente | modelo | esfuerzo declarado | hallazgos | líneas base |
|---|---|---|---|---|
| sonda | Fable (subagente) | 25 | | |
| F5 | Opus 5.5 (sesión) | 15 | 12 (301 a 312) | 8 de 8 |
| F2 | Opus 5.5 (sesión) | 15 | 13 (F2-201 a F2-213) | 3 de 3 |
| F3 | Opus 5.5 (sesión) | 15 | 15 (251 a 265) | 2 de 2 |
| F0 | Opus 5.5 (sesión) | 15 | 29 (101 a 129) | 3 de 3 |
| V5 | Sonnet 5.5 (sesión) | 10 (prompt de sistema) | 9 verificados, 2 propios | |
| V2 | Sonnet 5.5 (sesión) | SIN DATO | 8 verificados, 5 propios | |
| V3 | Sonnet 5.5 (sesión) | SIN DATO | 6 verificados, 2 propios | |
| V0 | Sonnet 5.5 (sesión) | SIN DATO | 12 verificados, 2 propios | |

Uso del plan semanal: 78 % antes de la ola 0 y 79 % después de F5 y F2.
