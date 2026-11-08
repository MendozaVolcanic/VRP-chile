# Auditoría S175: el sistema corriendo después de la S160

> **Estado: COMPLETA (cinco de cinco frentes, cada uno con su verificador), con los agregados del 2026-11-08 en el §11**
> (VX sobre 302, 108, 111 y 256; F4t, el token, con su verificador V4T; F5b, las láminas, con su verificador V5B; V33A y
> V33B sobre los 33 restantes). Ya no queda ningún hallazgo de auditor sin verificador. La conclusión central (302)
> quedó confirmada sólo en parte: ver §1, punto 1. F1 se adelantó al 2026-11-07 por decisión de Nicolás; el audit semanal
> del 2026-11-09 queda como anexo (§10), todavía sin escribir porque ese audit aún no existe, y no cambia los veredictos.
> Primera versión el 2026-11-07 17:44 GMT; cierre con F1 y V1 el 2026-11-07 (hora del servidor al cerrar en §10).
> Orquestador: Opus 5.5.

## 0. Encabezado

- **Plan sellado**: `docs/PLAN_AUDITORIA_S175.md`, SHA_PLAN = `a325ac8ff8c480fc88fe91d07b1b52046d0c0997` (segundo sello,
  aprobado por Nicolás en la sesión de auditoría). Los criterios del §3 no cambiaron después del sello.
- **Base de medición**: `origin/main` = `752d348bc67190e53b610989877e2405d238a1bc`, fijada en la ola 0 (Sat, 07 Nov 2026
  04:10:15 GMT). Referencia: `mirova_v1_snapshot/registro_vrp_consolidado.csv` sha256 `f833bfde...`, OCR `577a336e...`,
  `latest_consolidado.csv` `dee76837...` (registro completo en
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\REGISTRO_AGENTES.md`).
- **Frentes**: F0 (pendientes de S160 sin eje), F2 (VIIRS 375 en producción), F3 (decisiones y cierres S160 a S174), F5
  (identidad del pareo con MIROVA, pedido de Nicolás) y F1 (MODIS con la vía «código MIROVA»). Recortados del plan: VIIRS 750 con ROI B4 (lo vigila
  la sombra de #945) y F4, vencimientos simulando la ausencia (sus pendientes pasaron a F0 con fecha; la parte del token se
  hizo después como F4t, §11.3).
- **Sólo veredictos de verificador.** Cada hallazgo de la tabla del §3 lleva el veredicto y la gravedad del verificador,
  no los del auditor. Los que no pasaron el corte del verificador van en el §6 con su conteo.

### Limitaciones que el lector tiene que saber

1. **El esfuerzo: pedido high y enviado high; el número que ven los agentes es otra cosa.** La sonda de la ola 0 (Fable,
   `effort: high` del Agent tool) declaró `reasoning_effort 25`, los cuatro auditores 15 y V5 leyó 10 en su prompt de
   sistema (V0, V2 y V3: SIN DATO). Corrección del 2026-11-07, medida en los transcriptos de las sesiones
   (`C:\Users\nmend\.claude\projects\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile--claude-worktrees-relaxed-almeida-d17378\*.jsonl`
   y el de la sonda en `...\9f1d2725-...\subagents\agent-a3aa92e33a9a75d12.jsonl`): cada pedido a la API lleva
   `"output_config":{"effort":"high"}`, `"perTurnEffort":"high"` y pensamiento `adaptive`, en la sonda (2 de 2) y en
   las sesiones medidas (por ejemplo 110 pedidos con `output_config` high en una de ellas, ninguno distinto). El
   `reasoning_effort` que el agente lee en su contexto no es el nivel del pedido: varía por modelo (25 en Fable, 15 en
   Opus, 10 en Sonnet) con el mismo «high». Qué mide ese número es SIN DATO. La limitación de S172 y S174 («el effort no
   llega») queda rebajada a SOSPECHA sin evidencia: se leyó el número del contexto como si fuera el nivel.
   Contrapeso que no depende de esto: los cuatro auditores reprodujeron todas sus líneas base rojas (§5), comprobaron
   sha256, usaron controles positivos y declararon lo que no miraron.
2. **Modelos.** El plan pedía Fable como auditor y Opus como verificador. Una sesión sólo puede abrir otras de su modelo o
   más baratas, así que los auditores corrieron en Opus 5.5 y los verificadores en Sonnet 5.5. La regla «verifica otro
   modelo» se cumplió; el auditor no fue el previsto.
3. **F2 lanzó su propio verificador** (subagente, carpeta `experiments\_s175_audit\f2\verificador\`), fuera del plan. No
   cuenta como verificación; la de F2 es la de V2.
4. **F1 y V1 corrieron como subagentes** (Fable y Opus), después de comprobar que el esfuerzo sí llega: sus
   transcriptos dan `"output_config":{"effort":"high"}` en 27 de 27 y 76 de 76 pedidos. Ese es el modelo que pedía el plan.
   F1 midió con los datos de `origin/main` = `e75a7d52d` (SHA_CAMPO, 2026-11-07 20:04 GMT) y el código de la base.

## 1. En una pantalla

1. ⚠️ S175 VX (marca A113, texto anterior en el §11.2). **Los aciertos contra MIROVA no chocan en distancia con nuestros
   píxeles, pero que sean el mismo foco no está medido.** Las anomalías de estos volcanes se apiñan a 1 o 2 km del centro,
   así que casi cualquier radio de MIROVA cabe en el rango radial de casi cualquier pasada nuestra; la prueba compara
   radios, no posiciones (A107), y por eso distingue poco. De los 715 aciertos publicados por misma pasada que traen
   distancia de la tabla, 714 son compatibles (99,86 %), pero al barajar las distancias de MIROVA entre pares del mismo
   volcán y sensor sigue saliendo compatible el 93,2 % (302, confirmado en parte; VX-01). Lo sostenible es una cota: con
   la distancia de la tabla ningún acierto es incompatible a más de 2 píxeles nominales (3 km en MODIS), salvo Chillán
   VIIRS 375 2026-10-18 06:48, que excede por 0,099 km y cambia de lado con el origen (VX-02). Donde MIROVA sólo trae la
   distancia del OCR la pregunta queda abierta: de 29 pares de clase iii, 25 salen «fuera», y esa distancia difiere de la
   de la tabla en el 19 % de las pasadas que traen las dos (301, en parte); además el banco compara radios desde orígenes
   distintos (303). Las láminas de MIROVA posteriores al 2026-09-22 tampoco lo cierran (F5b con V5B, §11.4): sirven para
   georreferenciar, pero el selector de píxel de F5b borra la mancha saturada (V5B-01) y su clase de coincidencia sale
   73 y 77 % con nuestro punto de otra pasada, contra 95 y 94 % observado (V5B-04).
2. **El recall por noche se infla frente al recall por pasada.** Cuenta como acierto una pasada distinta en otro lugar
   (caso real: Cordón Caulle VIIRS 750, 2026-10-10). Con misma pasada el recall baja unos 2 puntos en VIIRS (304).
3. **VIIRS 375 no pierde protegidas de la tabla de MIROVA.** Las 5 pasadas protegidas no publicadas son todas filas sólo OCR
   sin geometría confiable o de Suomi NPP antes de Mirova-v1#20; con fila de la tabla se pierde 0 de 115 (V2-01, que
   matiza F2-201 y F2-202).
4. **La sobre-publicación de Lastarria es en dos tercios la regla D-9.** Sin las alertas mínimas reetiquetadas, Lastarria
   publica en negativos limpios el 11,6 % de sus pasadas, en la línea de Puyehue con la misma base, 42 de 355, 11,8 %
   (V2-03 sobre F2-203).
5. **El criterio de victoria tiene poco poder fuera de Chillán**: «ninguna protegida perdida» no tiene casos en 5 de 11
   volcanes (6 de 11 con los 60 días del audit semanal), y hay 42 protegidas diurnas fuera del criterio por diseño (309;
   308, confirmado por V33B).
6. **Documentos rectores desfasados**: `SINTOMAS.md` describe el MODIS de producción como K y con `_interp_geo`, cuando
   98 de 98 records MODIS desde el 2026-11-02 son de la vía (251, gravedad 3).
7. **La vía MODIS publica lo que dice producir** (F1, sin verificar como conteo: 140 de 140 records coherentes, 0 records
   de K escritos después del encendido, el tablero coincide en todos). Lo que falla es la vigilancia alrededor: es ciega
   por volcán a una caída a K (151, 152) y la regla de reversión supone que el NRT reescribe 8 días, cosa que el almacén
   no hace; la FICHA CPLT pública repite esa premisa (154, V1-02).
8. **Pendientes de S160 que siguen abiertos con gravedad 3**: VIIRS 750 en cumbre (101, 102), el veto de D18 colgado de
   una alerta de 1,00 MW truncada (103) y el token (107: rotar antes del 2026-11-27).
9. **Un token mal pegado deja el NRT verde sin datos** (F4t con V4T, §11.3; 381, 385 y V4T-01, gravedad 3 y 4). Si el token
   vence y nadie lo rota, el NRT queda rojo: ese rechazo sí se reconoce. Si NASA rechaza el token con otro texto (basura,
   revocado, de otra cuenta) o el secreto queda con un salto de línea final, el NRT termina verde con 0 archivos, y el
   primer aviso llega por staleness a las 48 a 72 h, a un repositorio con 0 suscriptores. Importa antes de la rotación del
   punto 8.
10. **Con el botón «Todos los pixels», el mapa de detalle deja de dibujar sin avisar** (V33A-01, gravedad 2, reproducido en
    navegador). Los píxeles de la vía MODIS no traen energía por píxel (161) y `frontend/index.html:3157` lanza un TypeError
    al pedirla; se pierden los records posteriores de la ventana. En Nevados de Chillán son 39 records de 5 días, los más
    recientes del volcán en erupción. Con el modo por defecto, «Solo principal», no ocurre.
11. **El lector que decidirá la adopción de V375-E no está en main** (F2-209, gravedad 2): vive en un tag y en ramas, y
    ningún workflow de main lo corre.

## 2. Lo que esto dice de si llegamos a los objetivos

El objetivo es reproducir lo que MIROVA publica (`docs/MISSION.md`): no perder ninguna protegida y callar donde MIROVA
calla. ⚠️ S175 VX (marca A113, texto anterior en el §11.2): esta auditoría se propuso medir por primera vez si el
«acierto» es la misma anomalía, y lo que logró medir es menos que eso. Con la distancia de la tabla ningún acierto queda
lejos de nuestros píxeles salvo un borde de 0,1 km (punto 1), pero la misma prueba da 93 % con las distancias barajadas:
la identidad del foco sigue SIN MEDIR. Las métricas que hoy publica el sistema tienen tres sesgos medidos:

- el recall por noche acepta otra pasada como acierto (304, V2-02);
- el tablero marca «MIROVA confirmó» con ±60 min y sin D-9, y su texto dice «en esta pasada» (F2-204 y V2-04, en 0 records
  cambia hoy la publicación);
- el veredicto depende de qué volcán: casi todas las protegidas son de Chillán y en 5 volcanes no hay ninguna (309, 308).

Ninguno muestra una protegida de la tabla perdida. Lo que se ve es que la vara mide algo más ancho de lo que dice.

## 3. Hallazgos verificados

Gravedad del verificador (1 a 5). Veredicto: C = CONFIRMADO, P = CONFIRMADO EN PARTE. Uno solo REFUTADO en parte (155, su consecuencia).

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
| 254 | F3 | ⚠️ S175 VPR955-01 (marca A113): #952 está mergeado en main desde el 2026-11-07 15:55 GMT (`36a191d45`), después de la base de medición; si ese merge cura este hallazgo es SIN DATO, porque nadie volvió a correr `leer_retro.py` con insumo vacío. Texto de la base: «Sí, arréglalos» (falsos verdes de cenit) no está en main; con el código de la base, insumo vacío y alertas sin cenit salen SIN SUSTRATO y se rotulan OK | C | 2 |
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
| 151 | F1 | La vigilancia de la guardia no comprueba que el record de producción sea de la vía (`prod_via` se calcula y no se usa en el lado prospectivo); una caída a K que calle dispara REVERSION_CANDIDATA contra la vía. Consecuencia práctica de baja probabilidad | C | 2 |
| 152 | F1 | Vigilante ciego por volcán: si la vía cae a K en un solo volcán, VERDE; si deja de escribir, sí sale VIGILANCIA_CIEGA a los 4 días | P | 2 |
| 153 | F1 | El descarte de borde de la vía no deja rastro en el log ni en la cobertura; caso Villarrica MODIS Aqua 2026-11-04 07:10 (guardia sí, producción no); la vigilancia lo cuenta por semana | P | 2 |
| 154 | F1 | §4.1 y §4.7 de la regla de reversión suponen que el NRT reescribe 8 días; no lo hace (primera observación de la vía 19 h antes del encendido) | C | 2 |
| 155 | F1 | Los TIF de MIROVA dejaron de capturarse el 2026-09-22; la consecuencia para §4.3 no se sostiene porque la regla pide la cabecera del PNG, que se sigue capturando | REFUTADO en la consecuencia | 1 |
| 156 | F1 | El audit deja de dar flag por las protegidas MODIS que K no publicó cuando la vía tiene records; hay aviso «sin juzgar» y siguen listadas | C | 1 |
| 157 | F1 | El recall de VIA_MODIS no da flag hasta 15 noches, mitigado: una protegida que la vía calla da flag de inmediato | C | 1 |
| 158 | F1 | El encendido se cuelga del primer record; sólo un `--overwrite` masivo lo mueve | P | 1 |

**Hallazgos propios de los verificadores**: V2-01 (las 5 protegidas no publicadas son del estrato OCR sin geometría, g2),
V2-02 («111 de 111 noches» acepta cualquier pasada, g2), V2-03 (dos tercios del exceso de Lastarria es D-9, g2), V2-04 (el
texto del tablero dice «en esta pasada» y la lógica busca ±60 min, g2), V2-05 (sombra V375-E y snapshot congelado se
componen mal, SOSPECHA, g2), V3-01 (cita de 258 mezcla dos decisiones, g1), V3-02 (518 records MODIS de enero a junio de los
34 volcanes fuera del cron sin `processed_utc` ni `regimen`, g1), V5-01 (la regex de I8 deja fuera 20 de 63 notas de
truncado, g1), V5-02 (el origen de 303 también torna dudosa la clase summit/far de Tupungatito y Puyehue, SOSPECHA, g2),
V0-01 (la «fracción 19 %» de 101 depende de la ventana, g1), V0-02 (`f0_cadencias.py` emite una advertencia de sintaxis, g1),
V1-01 (el plazo de 29 protegidas de la vigilancia cuenta pasadas K contra K, misma raíz que 151, g2), **V1-02 (la FICHA
CPLT pública v1.18, l. 7 y 25, dice que la vía rige «hasta unos 8 días antes»; los datos dicen 19 h, g2)**, V1-03 (la caída
`sin_mxd03` es inalcanzable desde el NRT, `run_pipeline.py` l. 247 a 250, g1), V1-04 (falta el JSON de la guardia de un
volcán y la vigilancia declara ciegos los once; va en la dirección segura, g1). Los propios de los verificadores
posteriores están en el §11: VX-01 a 05 (§11.1), V4T-01 y 02 (§11.3), V5B-01 a 05 (§11.4), V33A-01 y V33B-01 a 03 (§11.5).

**Verificados después de cerrar esta tabla**: 302, 108, 111 y 256 (VX, §11.1), 381 a 390 (F4t con V4T, §11.3), 351 a 355 (F5b
con V5B, §11.4) y los 33 del §6 (V33A y V33B), con el veredicto y la gravedad de sus verificadores.

## 4. Informes de cada agente

| agente | archivo |
|---|---|
| F0 | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f0\INFORME.md` |
| F2 | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f2\INFORME.md` |
| F3 | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f3\INFORME.md` |
| F5 | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f5\INFORME.md` |
| F1 | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f1\INFORME.md` |
| V0, V1, V2, V3, V5 | `...\experiments\_s175_audit\v0\VERIFICACION.md` (y `v1`, `v2`, `v3`, `v5`), cada una con su `caminos.md` sellado antes de abrir archivos |
| VX | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\vx\VERIFICACION.md` |
| F4t | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f4t\INFORME.md` |
| V4T | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v4t\VERIFICACION.md` |
| F5b | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f5b\INFORME.md` |
| V5B | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v5b\VERIFICACION.md` |
| V33A | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v33a\VERIFICACION.md` |
| V33B | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v33b\VERIFICACION.md` |

## 5. Líneas base rojas (regla B: el instrumento tiene que ver lo que ya sabemos)

Todas se reencontraron.

| frente | línea base roja | resultado |
|---|---|---|
| F5 | misma pasada a ±120 s en el audit del 2026-11-02 | 125/194, 32/42, 14/16, exacto |
| F5 | acierto sintético por otra fuente, par desfasado 3 min, port contra node forzado, fila truncada de Chillán, hueco de un satélite | las ocho, vistas |
| F2 | 201 de S160 (C1 de escena: 4 de 2.452) sobre `d516b9d8c`; caída de Chillán con el cenit; lector de la sombra sin datos | las tres, vistas (el lector da NO LEGIBLE) |
| F3 | nota A85 desfasada en `77e54e8e0^`; hallazgo 281 en `d516b9d8c` | vistas con un instrumento nuevo; el censo S145 no ve ninguna (257) |
| F1 | records `sin_grilla`/`sin_mxd03` después del encendido (con control sintético que el censo ve); 0 records de la vía en `79f410697` | las dos, vistas (0 de 14.855 MODIS en `79f410697`) |
| F0 | decisión 1 resuelta (`0d73f2a4e`, #891); decisión 6 abierta; Suomi NPP sin records después del 2026-11-02 13:00 UTC | las tres, vistas |

## 6. Hallazgos que no pasaron el corte del §3 del plan

⚠️ S175 V33A y V33B (marca A113, texto anterior en el §11.2 y el §11.5): eran 37 hasta VX y 33 hasta estos dos verificadores.
Hoy los 80 hallazgos de auditor de los cinco frentes tienen verificador. De estos 33: **27 CONFIRMADOS, 6 CONFIRMADOS EN PARTE,
0 refutados, 0 SIN DATO**. Ninguno de los 18 de V33A se arregló entre la base y main de hoy. Lo verificado no cambia hoy
ninguna alerta publicada: son efectos de etiqueta, gobernanza, documentos y medición, salvo V33A-01 (§1, punto 10).

| id | qué | veredicto | gravedad | verificador |
|---|---|---|---|---|
| F2-209 | El lector de la sombra V375-E no está en la base ni en main (decisión 20) | C | 2 | V33B |
| 255 | La cola de decisiones de `tasks/LOOP_OBJETIVOS.md` lleva cinco filas desfasadas (D-1, D-19, D-23, D-37, D-39) | C | 2 | V33B |
| F2-211 | 18 pasadas sin geometría de 1 MW o más fuera del denominador protegido, 14 de Chillán y 2 no publicadas; es decisión documentada, lo nuevo es su tamaño | C | 2 | V33B |
| F2-213 | C-04 sigue abierto: la distancia del OCR de Tupungatito 2026-09-28 05:18 es la misma, con la misma nota, que la de las 05:36 | C | 2 | V33B |
| 308 | «Ninguna protegida perdida» es vacuo en 5 de 11 volcanes (2026-09-01 a 2026-11-07); 6 de 11 con los 60 días del audit, 3 de 11 desde marzo | C | 2 | V33B |
| 116 | El popup dice «Distancia al cráter» y mide desde el centro: hasta 7,58 km en Cordón Caulle | C | 2 | V33A |
| 117 | La VRE del tablero suma 6 h fijas por record, con 9 a 12 records por noche; MIROVA integra por trapecios (cita TEXTO, sin render) | C | 2 | V33A |
| 119 | El mínimo de cumbre 0,003 gobierna también el umbral del dETI | C | 2 | V33A |
| 121 | La regla con que se adoptó K sigue igual y la vigilancia de la sombra usa su paso 9 | C | 2 | V33A |
| 161 | Los píxeles de la vía no traen `vrp_mw` por píxel; origen de V33A-01 (sube de 1 a 2) | C | 2 | V33A |
| 112 | Una plataforma muda da código 0 también en modo estricto; decisión escrita en el código | C | 2 | V33A |
| 122 | Inventario S160 de VIIRS y unidades sin cambio (F2-210 y F2-212 en gravedad 2, el resto en 1) | C | 2 | V33A |
| 123 | Inventario S160 de dependencias sin cambio (251: lo externo SIN DATO); el healthcheck con cron de las 12:00 corre con 4,97 h de atraso mediano (255 y 252 en gravedad 2; 249, 251 y 254 en 1) | C | 2 | V33A |
| 124, 125, 127, 128, 129, 159, 160 | 124 y 125 son decisiones documentadas en el código; 127 el placebo del 1 % nunca entró al evaluador; 128 datos de adopción de K no encontrados en `_s153_fk_v2/`; 129 pendientes de F1b sin arreglo en código; 159 y 160 son avisos del vigilante | C | 1 | V33A |
| 118, 120, 126 | 118 latente (el fenómeno no ha ocurrido); 120 la fila falta, pero la misma noche tiene otra alerta VIIRS en la tabla; 126 afirma el silencio de Suomi NPP «en nuestros records y en MIROVA» y V33A sólo sostiene lo segundo de forma indirecta. Se cuenta como P, igual que el resumen de V33A; su encabezado y su CSV dicen CONFIRMADO para el resto de la afirmación | P | 1 | V33A |
| F2-208, 259, 260, 262, 263, 264, 310 | 208 la parada de la sombra llega el 2026-12-02 si no falta noche (3 noches y 9 alertas con la tabla de la vara; 4 y 26 con la tabla raíz); 259 y 260 decisiones de segunda mano; 262 radio max(4 km, inner); 263 cambio de una línea al sellar; 264 CI rojo en rama (causa SOSPECHA); 310 cambio de banda de Lastarria por 0,036 | C | 1 | V33B |
| F2-210, 261, 265 | 210 las dos protegidas de marzo son filas sólo OCR, anteriores al hito del 2026-06-11; 261 #895 lo mergeó la cuenta `MendozaVolcanic` (si es la de Nicolás: SOSPECHA); 265 #945 se corrigió después de la auditoría, #950 y #951 siguen sin nombrar | P | 1 | V33B |

## 7. Pruebas de campo (lo que sólo se cierra mirando)

- Las tres alertas MODIS de Láscar posteriores al congelamiento de los TIF (2026-09-25 08:00, 2026-10-08 08:00, 2026-10-26
  07:55 UTC): mirar las láminas PNG de MIROVA de esas pasadas.
- Chillán VIIRS NOAA-21 2026-10-18 06:48 UTC (25,79 MW). ⚠️ S175 VX (marca A113, texto anterior en el §11.2): es el único
  acierto con distancia de la tabla que excede la tolerancia, por 0,099 km desde `mirova_center`, y desde el vent queda
  compatible (VX-02); ese borde está dentro del error de la vara. Lo que sí pide mirar: el alcance de nuestro cúmulo
  VIIRS 375 es 1,56 km desde `mirova_center` y MIROVA alerta a 1,88 km, con 25,79 MW contra 8,93 MW publicados. Si es el
  mismo campo de lava o un foco distinto sigue SIN DATO: F5b no lo resolvió (su control de distancia falló en esa pasada) y
  su selector de píxel tiene el defecto V5B-01. Falta mirar la lámina PNG a ojo.
- Cordón Caulle VIIRS 750 2026-10-10: la noche que el recall da por vista con una pasada de las 04:54 a 18,5 km, mientras la
  protegida de las 05:54 está en `PERDIDAS_ACEPTADAS` (304).
- C-04 (Tupungatito VIIRS 375 2026-09-28 05:18) y C-06 (Suomi NPP, respondido por el issue #943): actualizar la cola de
  campo, que no se toca desde S160 (108, confirmado en el §11.1; C-05 también tiene respuesta parcial que nadie anotó).

## 8. Decisiones para Nicolás

| # | decisión | recomendación |
|---|---|---|
| 1 | Rotar `EARTHDATA_TOKEN` (107) | sí, antes del 2026-11-27; sólo tú puedes hacerlo. Al rotar, pega el token sin espacio ni salto de línea final, despacha el NRT de un volcán y comprueba que escribió records (§11.3): hoy un token mal pegado no da error |
| 2 | Corregir `SINTOMAS.md` (251, 252): marca S172 en l. 25 y 127 y la nota A85 | sí, PR de documentación sin riesgo; es lo que se lee antes de proponer una palanca |
| 3 | Mergear #952, los falsos verdes de cenit (254) | ⚠️ S175 VPR955-01 (marca A113): CERRADA, #952 se mergeó el 2026-11-07 15:55 GMT (`36a191d45`). Si cura 254 es SIN DATO: nadie corrió `leer_retro.py` con insumo vacío después del merge. Texto anterior: «sí, después de su verificador y con CI verde» |
| 4 | Implementar la decisión 3 de S174 (253) | sí; ya la aprobaste, falta hacerla |
| 5 | Publicar el recall por pasada al lado del recall por noche (304, V2-02) | sí, en el audit semanal; no cambia la detección |
| 6 | Medir la posición de MIROVA con la tabla y con origen común, no con el OCR (301, 303) | sí, en el banco y el audit |
| 7 | «MIROVA confirmó» del tablero (F2-204, V2-04) | alinear la lógica a la pasada a ±120 s con D-9, o cambiar el texto; recomiendo la lógica, porque el operador lee «en esta pasada» |
| 8 | VIIRS 750 en cumbre (101, 102) | darle un camino nuevo dentro del programa de V750 (D25 no se adoptó), medido contra la tabla; ninguna alerta perdida es protegida, así que no es urgente |
| 9 | La lectura del truncado de MODIS (103, 307) | **Respondida por Nicolás y medida por el orquestador (2026-11-07, copias de la base en `C:\Users\nmend\vrp-temporales\s175_audit\insumos\`):** el truncado es del OCR, no de la tabla. Alertas son las filas con `Tipo_Registro` que empieza en `ALERTA_TERMICA`; sin ese filtro los denominadores cambian. Script y salida: `experiments/_s175_audit/dec9_truncado.py` y `dec9_truncado_salida.txt` (`latest_consolidado.csv` no está en el repo: sha256 `dee76837...`, en §0). En la tabla (`latest_consolidado.csv`) 141 de 142 alertas MODIS traen decimales; en el OCR las 48 alertas MODIS y las 95 de VIIRS 750 son enteras (VIIRS 375 sí trae decimales, 896 de 897). Misma pasada, Chillán MODIS 2026-10-30 08:55: tabla 14,39 MW, OCR 14,0. La protegida perdida de Chillán MODIS 2026-10-30 07:15 (1,0 MW) existe sólo en el OCR. Recomendación: en MODIS y VIIRS 750 usar siempre el VRP de la tabla y tratar el del OCR como piso, entre v y v+1; el veto de D18 se relee con eso |
| 10 | `.gitignore` y los `hallazgos.csv` (114) | agregar una excepción para `experiments/_s*_audit/**/hallazgos.csv` |
| 11 | Vigilancia de la guardia por volcán y por detector (151, 152, V1-01) | sí: que mire por volcán si el record de producción es de la vía; hoy la probabilidad es baja, pero es la red que sostiene la reversión pre-autorizada |
| 12 | Corregir la FICHA CPLT y la regla de reversión §4.1 y §4.7 (154, V1-02) | sí: la ficha es pública (Resolución CPLT N°372) y repite una premisa que los datos refutan |
| 13 | Esfuerzo de los agentes (limitación 1) | medirlo desde ahora en el transcripto (`output_config.effort` de cada pedido), no en lo que el agente declara; volver a Fable como subagente con `effort: high` cuando se quiera ese modelo, porque el pedido sí llega |
| 14 | Arreglar el clasificador de credencial muerta (381, 382, V4T-02) | sí, antes de rotar: toca `pipeline/fetch.py`, así que necesita tag y tu sí (A45), con una prueba que arme el `DownloadFailure` real y un 401 de cuerpo neutro |
| 15 | Que `nrt.yml` exija que la corrida escribió algo (385, V4T-01) | sí, con un revisor como el de la guardia; hoy es lo que vuelve silencioso cualquier rechazo que no sea vencimiento |
| 16 | Canal de aviso (383, 384) | que los avisos te lleguen sin depender de un run rojo; hoy el run rojo del defecto 384 es el único aviso empujado cuando el NRT queda verde |
| 17 | Medir la identidad del foco en dos dimensiones (302, VX-01, V5B-01, V5B-04) | sí, pero la lámina sola no alcanza: decide si F5b se re-corre con la máscara corregida, conservando la mancha saturada, y con un nulo al lado. Mientras tanto no se publica ninguna posición de MIROVA en Chillán como medición |
| 18 | Mantener lo que se envejeció (108, 111, 256) | actualizar `docs/COLA_CAMPO.md` (C-05, C-06), medir la fracción MODIS NRT en el audit semanal y corregir la nota de memoria del MxD03 |
| 19 | Arreglar el mapa con «Todos los pixels» (V33A-01, 161) | sí: `frontend/index.html:3157` y `:3068` tienen que tolerar píxeles sin `vrp_mw`, porque el error corta el dibujo de los días más recientes sin aviso. Toca `frontend/`, así que necesita tu sí (A45); replicar donde haya copia de esa lógica |
| 20 | Llevar a main el lector de V375-E (F2-209, V33B-03) | sí, antes de la parada de la sombra (2026-12-02 si no falta noche), envuelto en `tests/` para que corra en CI (regla de S174), o declarar que la lectura de la ventana P se hace desde el tag |

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
| F1 | Fable 5.1 (subagente) | high en 27 de 27 pedidos (transcripto); él declaró SIN DATO | 11 (151 a 161), 373 mil tokens, 25 min | 2 de 2 |
| V1 | Opus 5.5 (subagente) | high en 76 de 76 pedidos (transcripto) | 8 verificados, 4 propios, 275 mil tokens, 16 min | |
| VX | Fable 5.1 (subagente) | SIN DATO (declarado) | 4 verificados, 5 propios (VX-01 a VX-05) | |
| F4t | Fable 5.1 (subagente) | SIN DATO (declarado) | 10 (381 a 390) | 2 de 2 |
| V4T | Opus 5.5 | SIN DATO (declarado) | 10 verificados, 2 propios (V4T-01 y V4T-02) | |
| F5b | Fable 5.1 (subagente) | SIN DATO (declarado; su contexto dice `reasoning_effort 25`) | 5 (351 a 355) | |
| V5B | Opus 5.5 | SIN DATO (declarado) | 5 verificados, 5 propios (V5B-01 a V5B-05) | |
| V33A | Fable 5.1 | SIN DATO (declarado) | 18 verificados, 1 propio (V33A-01) | |
| V33B | Fable 5.1 | SIN DATO (declarado) | 15 verificados, 3 propios (V33B-01 a V33B-03) | |

Uso del plan semanal: 78 % antes de la ola 0 y 79 % después de F5 y F2.

## 10. Anexo pendiente: audit semanal del 2026-11-09

F1 corrió un sustituto del audit sobre la base: VERDE, recall de VIA_MODIS 100 % en 2 noches, 3 protegidas de la vía
publicadas, sin flags (sin verificar). El audit real del lunes 2026-11-09 09:00 UTC se agrega aquí con su lectura contra
la regla §4 de reversión; no cambia los veredictos de arriba.

**Pendiente explícito al 2026-11-08:** ese audit todavía no ha corrido y este anexo no está escrito. Lo de arriba es el
sustituto de F1, no el audit.

## 11. Agregado del 2026-11-08: VX, F4t con V4T, F5b con V5B, V33A y V33B

Base de todo lo que sigue: `752d348bc` (la misma de la auditoría). Valen los veredictos y las gravedades del verificador;
las del auditor van sólo donde cambian. Veredicto: C = CONFIRMADO, P = CONFIRMADO EN PARTE. Traspaso de la sesión:
`docs/S175_AUDITORIA_RESULTADOS.md`.

### 11.1 VX: los cuatro sin verificar que sostenían conclusiones

| id | qué | veredicto | gravedad |
|---|---|---|---|
| 302 | Con la distancia de la tabla, 714 de 715 aciertos por misma pasada son compatibles en radio con nuestros píxeles; la identidad del foco no está medida | P | 2 |
| 108 | Las 10 filas de `docs/COLA_CAMPO.md` siguen abiertas (último commit 2026-10-22, S160), aunque C-06 ya tiene respuesta en el issue #943; el título exagera la cobertura del clasificador (7 filas, no «C-02 a C-10») | C | 2 |
| 111 | Nadie mide la fracción NRT de MODIS. La fecha de decomiso de la colección 6.1 (2026-09-30, cita del repo; vigencia externa SOSPECHA) ya pasó y no se ejecutó: 867 records con colección `061` desde el 2026-10-01. Noviembre: 14 de 143 records MODIS son NRT (9,8 %); de abril a octubre, 0 % | C | 2 |
| 256 | La memoria dice que el MxD03 «se baja y se ignora»; la vía lo usa: 120 de 120 records MODIS de los 11 Tier A procesados desde el 2026-11-02T20:11:43Z llevan `via_codigo_mirova: true`. La frase sigue siendo cierta para la guardia K y para los records que caigan a K (0 en la base) | C | 2 |

Hallazgos propios de VX:

| id | qué | confianza | gravedad |
|---|---|---|---|
| VX-01 | La prueba de extensión de 302 casi no distingue: con las distancias de MIROVA barajadas, el 93 % igual sale «mismo cúmulo» | C | 2 |
| VX-02 | El «al borde» de Chillán 2026-10-18 06:48 cambia de lado con el origen y la tolerancia; la vara «distancia desde `mirova_center`» reproduce la tabla en 5 de 8 TIF | C la sensibilidad; SOSPECHA qué origen usa MIROVA | 2 |
| VX-03 | Sin tolerancia, la distancia de la tabla cae fuera del rango radial de nuestros píxeles en 519 de 715 aciertos: hay un desfase sistemático que la tolerancia tapa | número medido; causa SOSPECHA | 2 |
| VX-04 | Un record MODIS NRT del 2026-11-02 01:15 (Planchón-Peteroa, Terra) lleva 5 días sin subir a Standard y quedó procesado por K antes del merge de la vía; es el mecanismo que 243 teme para el decomiso | C el hecho; SOSPECHA la causa | 2 |
| VX-05 | Ningún record MODIS declara qué geolocalización se usó (`geo_fuente` no se persiste) | C | 1 |

### 11.2 Cómo leer 302 (la conclusión central) y qué texto se reemplazó

**Por qué la prueba no alcanza.** Pregunta si la distancia de MIROVA al centro cabe en el rango de distancias de nuestros
píxeles, más una tolerancia. Es un radio: un píxel al otro lado del cráter, a la misma distancia, pasa igual (A107). Como
el calor de estos volcanes se concentra a 1 o 2 km del centro, casi cualquier distancia cabe. El nulo por permutación lo
muestra (300 barajados de la distancia de MIROVA entre pares CONS del mismo volcán y sensor):

| sensor | n | observado | nulo (mediana) |
|---|---|---|---|
| VIIRS 375 | 560 | 99,8 % | 92,5 % |
| VIIRS 750 | 120 | 100 % | 95,0 % |
| MODIS | 35 | 100 % | 100 % (con tolerancia de 3 km la prueba no puede fallar) |
| todos | 715 | 99,86 % | 93,15 % (91,3 a 95,0 %) |

El observado supera al nulo, así que algo de señal hay, pero poca. La prueba sí ve un foco a varios kilómetros: los 29
pares OCR de clase iii dan 25 «fuera» y 4 «mismo cúmulo» (Tupungatito a 4,8 a 5,4 km, Cordón Caulle a 7,3 a 7,9 km).

**Lo que se puede decir.** Con la distancia de la tabla ningún acierto es incompatible a más de 2 píxeles nominales
(3 km en MODIS), con una excepción: Chillán V375 2026-10-18 06:48, que excede por 0,099 km desde `mirova_center`. Es una
cota, no una identidad.

**Lo que no se puede decir.** Que sean el mismo foco o el mismo cúmulo. Tampoco que el caso Chillán sea un borde firme: desde
el vent queda compatible (margen -0,065 km) y en cambio salen «fuera» otros tres entre los 54 de clase iii (Láscar 2026-06-25
05:12, Chillán VIIRS_SNPP 2026-10-30 07:00, protegida, y Cordón Caulle VIIRS_NOAA20 2026-10-29 05:54, protegida). Con la mitad
de la tolerancia desde `mirova_center` salen 15 de 54 (5 protegidas de Chillán). La vara tiene una incertidumbre del orden de
1 km, diez veces ese margen.

**Texto anterior, conservado (A113).**
- §1, punto 1: «Los aciertos contra MIROVA son la misma anomalía, medidos con la vara correcta. Con la distancia de la tabla
  de MIROVA y un origen común, de 881 aciertos publicados por misma pasada sólo 1 cae fuera de nuestros píxeles, y por 0,1 km
  (302, publicado por el auditor, sin verificar). Lo que parecía «otra fuente» era el instrumento: la distancia del OCR
  difiere de la de la tabla en el 19 % de las pasadas que traen las dos (301, en parte) y el banco compara radios desde
  orígenes distintos (303).»
- §2: «Esta auditoría midió por primera vez si el «acierto» es la misma anomalía, y la respuesta es sí cuando se usa la
  distancia de la tabla (punto 1).»
- §6: «F5 302, 308 y 310 (3)»; «F3 255, 256 y 259 a 265 (9)»; «F0 108, 111, 112 y 116 a 129 (17)»; «En total 37 de 80
  hallazgos de auditor. Los más útiles para la próxima sesión: 302 (los aciertos por misma pasada son el mismo foco, la
  respuesta directa a la pregunta de Nicolás), 108 (la cola de campo no se tocó desde S160), 256 (la memoria dice que el
  MxD03 se ignora; la vía lo usa) y 111 (nadie mide la fracción MODIS NRT).»
- §7: «la única protegida cuyo punto de MIROVA cae fuera de nuestros píxeles con la distancia de la tabla (302, sin
  verificar).»

Propagado con la misma marca a `docs/INDEX.md` y al §2 y al hallazgo 302 de
`experiments/_s175_audit/f5/INFORME.md`. El plan sellado (`docs/PLAN_AUDITORIA_S175.md`) nombra «mismo foco» como clase con
una tolerancia definida; no se toca, y ese nombre debe leerse como esa tolerancia.

### 11.3 F4t con V4T: el día que `EARTHDATA_TOKEN` se rompa

**Qué pasa.** Un token rechazado por NASA es una falla permanente hasta que alguien lo rote, y el código debería detenerse
y quedar en rojo. Lo hace sólo si reconoce el texto del error. Con el vencimiento natural («Token ... has expired») lo
reconoce y el NRT queda rojo. Con cualquier otro rechazo cae al `WARN`, 0 archivos, exit 0, y el run sale verde: el tablero
deja de avanzar y nadie recibe aviso hasta el staleness, a las 48 a 72 h. Eso se comprobó con earthaccess real, 0.17 y 0.19,
y con la red interceptada (V4T, sin red a NASA).

| id | qué | veredicto V4T | gravedad V4T (auditor) |
|---|---|---|---|
| 381 | El clasificador intenta leer el status pero `a or b` descarta el `Response` de un 401 (es falso en Python); todo depende del regex. 401 con otro texto: exit 0 con 0 archivos | C | 4 (5) |
| 383 | Avisos a un repositorio sin lectores: 0 suscriptores, sin asignados. No es «ningún otro canal»: un run rojo sí manda correo de Actions; si llega y se lee es SIN DATO | P | 4 (5) |
| 385 | `nrt.yml` no exige que la corrida escriba algo. Refutado «único productor con cron»: `experimental-diario.yml` tampoco, pero ese es laboratorio | P | 4 (4) |
| 382 | Un 401 o 403 de descarga llega como `DownloadFailure` sin `response` ni texto reconocible; WARN y exit 0. Baja porque CMR rechaza primero: sólo se ve si CMR acepta y LAADS no (probabilidad SIN DATO) | C | 3 (4) |
| 387 | Token «desconocido» no abre issue; el caso silencioso es el no JWT con el NRT verde | C | 3 (3) |
| 384 | `gh label create` sin `--force` deja el healthcheck en rojo tras crear el issue; hoy ese run rojo es el único canal empujado en el caso verde de 381 | C | 2 (3) |
| 386 | 21 workflows de despacho con el par y sin guarda. Mecanismo distinto al del auditor: con token vacío el par va por HTTP Basic a `/profile`; sólo ocurre por despacho manual con el secreto borrado | P | 2 (3) |
| 388 | El pipeline nunca mira `exp` del JWT; el único lector es `token_edad.py` | C | 2 (2) |
| 389 | earthaccess sin pin. Refutado «el CI instala 0.19.0»: instala 0.17.0 (Python 3.11; 0.18 y 0.19 piden 3.12 o más). Resultados idénticos en 0.17 y 0.19 | P | 1 (2) |
| 390 | Primer aviso de renovar el 2026-11-28 12:00 UTC si `exp` cae después de las 12:00 del 2026-12-07; si cae antes, el 27. La hora exacta de `exp` es SIN DATO | C condicionado | 1 (1) |

Hallazgos propios de V4T:

| id | qué | confianza | gravedad |
|---|---|---|---|
| V4T-01 | Token con espacio o salto de línea final: `token_edad` dice «ok», requests lanza `InvalidHeader` antes de salir, NRT verde sin datos, y el mensaje de error lleva el token al log de un repo público (enmascarado de GitHub: SIN DATO) | C en el código y la simulación; SOSPECHA que GitHub conserve el salto final | 3 |
| V4T-02 | La réplica de error de los tests S123/S124 no tiene `__cause__` ni usa `DownloadFailure` real; por eso 381 y 382 siguen verdes en la suite | C | 3 |

**Para la rotación del 2026-11-27.** Mitigación sin tocar código: tras rotar, despachar el NRT de un volcán y comprobar que
escribió records. El arreglo de `_is_credential_dead` toca `pipeline/fetch.py` (A45, decisión 14). F4t propuso que F0
herede esta rebaja en 124 («resuelto salvo un borde», gravedad 1): con 381 el borde «no JWT» ya no es inocuo. V33A confirma
124 con gravedad 1, como decisión documentada en el código y sin mirar el cruce con 381; ese cruce sigue abierto.

**Lo que quedó sin medir (V4T, parada por disco y sin red a NASA).** El texto real de CMR y LAADS ante un token basura,
revocado o de otra cuenta; la hora de `exp`; la re-corrida de `f4t_03_pipeline_simulado.py` y de
`f4t_02_guarda_token_vacio_shell.py`. El verde a nivel de `run_pipeline` completo es medición de F4t; V4T lo midió hasta
`fetch_for_volcano` más `informar_cobertura`.

### 11.4 F5b con V5B: la lámina de MIROVA como vara de posición después del 2026-09-22

**Por qué se intentó.** Desde el 2026-09-22 el archivo no tiene TIF de MIROVA, y la lámina Latest10NTI es la única huella de
dónde marcó el foco. F5b la georreferenció y comparó el píxel más claro con el punto que publicamos.

**Qué sobrevive.** La lámina VIIRS sirve para georreferenciar. Fuera de muestra, en 41 casos nuevos elegidos sin mirar, valida
en VIIRS 375 20 de 25 (17 de 17 cuando el máximo del TIF reproduce la tabla) y en VIIRS 750 9 de 16 (2 de 2); correlación
panel contra TIF, mediana 0,96 y 0,92. La salvedad es V5B-03: la regla se ajustó y se validó sobre los mismos 4 casos, y esos 41
no ejercitan la máscara.

**Qué no sobrevive.** El selector de píxel falla justo en la erupción: en un foco saturado la mancha se ve blanca, el código
la toma por «sin dato», la borra y elige un píxel del borde (V5B-01: 35 de 303 láminas; Chillán VIIRS 750 17 de 55, MODIS 12
de 22). Por eso la conclusión de 351 no se sostiene en ninguna de sus cuatro protegidas de Chillán: las tres VIIRS 750 son ese
artefacto (conservando la mancha, nuestro punto cae a 0,14, 0,106 y 0,292 km de su celda más cercana), y la VIIRS 375 del
2026-10-18 05:06 es un empate entre saturados de una misma mancha (V5B-02).

**Las clases de F5b no miden identidad del foco, y sus conteos no se publican aquí como medición.** Con nuestro punto de otra
pasada la clase de coincidencia sigue saliendo 73 % en VIIRS 375 y 77 % en VIIRS 750, contra 95 % y 94 % observado (V5B-04; n 116 y
50, 2026-09-22 a 2026-11-06): dice «no está en otro lado del inner», no «mismo foco esta noche». Es la misma lección de VX-01.

Lo único que queda de 351 es radial y sale de la tabla, sin la lámina: la `Distancia_km` VIIRS 750 de MIROVA (2,12 a 2,37 km)
contra V375 1,06 a 1,19 km en esa misma pasada, según la propia tabla de MIROVA. Su distancia VIIRS 750 no es una posición
estable. Hipótesis: SOSPECHA, sin medir píxel a píxel. El origen de esa distancia en Chillán: SIN DATO (ningún offset único
lo explica).

| id | qué | veredicto V5B | gravedad V5B (auditor) |
|---|---|---|---|
| 351 | Cuatro protegidas VIIRS de Chillán: publicamos en las cuatro y las filas son de la tabla, pero la conclusión de posición no se sostiene | P | 2 (3) |
| 352 | El control de distancia falla en 30 protegidas de Chillán (22 V375, 8 V750), «por poco» en 26; la mitad del problema es V5B-01 (conservando la mancha pasa en 18 de 30); la disyuntiva origen o píxel sigue abierta | P | 2 (2) |
| 353 | Sin láminas MODIS 12 de 46 días (23 a 30-sep y 8 a 11-oct) y VIIRS 2 a 3 días; irrecuperable. Causa (poller o MIROVA): SIN DATO | C | 2 (3) |
| 354 | La lámina MODIS no sirve de vara con el píxel más claro (5 de 7 a 3,6 a 5,8 km; casos débiles); la vara TIF MODIS es dudosa | C | 2 (2) |
| 355 | La lámina redondea el VRP a entero también en VIIRS 750; el marco gris V750 sigue un corte de VRP, no marca sin alerta | C | 1 (1) |
| V5B-01 | El selector borra la mancha caliente saturada como si fuera «sin dato» | C | 3 |
| V5B-02 | En una mancha saturada el «píxel más claro» es el primero en orden de barrido | C | 2 |
| V5B-03 | Regla ajustada y validada sobre los mismos 4 casos; fuera de muestra la georreferencia aguanta y el máximo del TIF no siempre | C | 2 |
| V5B-04 | La clase de coincidencia casi no separa pasadas (nulo 73 y 77 %) | C | 2 |
| V5B-05 | El control sintético de `p8` no pasó y su docstring dice lo contrario | C | 2 |

Qué no se miró: las láminas fuera de Latest10NTI, el poller de `mirova-tif-archive` y la posición dentro de la mancha, que sólo
la tabla acota. Ninguna imagen de MIROVA entra a este repositorio (carpetas `f5b` y `v5b` sin imágenes).

### 11.5 V33A y V33B: los 33 que faltaban

El resultado por hallazgo está en el §6. Del hallazgo nuevo V33A-01 se reprodujo el TypeError en el navegador con el tablero
en local (`frontend/index.html:3157`; 217 marcadores en «Solo principal», 651 en «Todos los pixels», 39 records de Chillán sin
dibujar, 2026-11-02 a 11-06). Texto anterior del §6 (A113): «F5 308 y 310 (2); F2 F2-208 a F2-211 y F2-213 (5); F3 255 y 259 a 265
(8); F0 112 y 116 a 129 (15); F1 159 a 161 (3). En total 33 de los 80 hallazgos de auditor de los cinco frentes.»

Hallazgos propios de V33B:

| id | qué | confianza | gravedad |
|---|---|---|---|
| V33B-01 | Las filas OCR de Tupungatito 2026-09-28 05:18 y 05:36 comparten `Distancia_aprox_imagen` de una imagen del 2026-10-22, método «ambiguo»; alimenta a F2-213 y C-04 | C | 1 |
| V33B-02 | `alerta_protegida` acepta filas sólo OCR anteriores al hito del 2026-06-11, cuando el OCR estaba mal calibrado (A119); el recall de marzo se mediría contra una referencia dudosa, raíz del «en parte» de F2-210 | SOSPECHA (no se leyó si el banco las excluye) | 2 |
| V33B-03 | El lector de la sombra V375-E no corre desde un árbol suelto: exige resolver `origin/loop/activo` con git y el árbol entero del tag; toca la decisión 20 | C | 1 |

### 11.6 Pendiente

El anexo del §10 (audit semanal del lunes 2026-11-09 09:00 UTC contra la regla §4 de reversión) no está escrito: ese audit
todavía no existe.
