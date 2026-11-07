# Plan de auditoría S175: el sistema corriendo después de la S160

> 2026-11-06, orquestador Opus 5.5 (sesión hija de la coordinadora S174). Regla A51 y
> `C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_AUDITORIAS.md` (leída entera al abrir esta sesión).
> **Estado: BORRADOR, sin sellar.** Se sella con el commit que Nicolás apruebe; ese hash es «SHA_PLAN» y cada
> verificador comprueba con `git diff «SHA_PLAN» -- docs/PLAN_AUDITORIA_S175.md` que los criterios del §3 no cambiaron.

## 0. En una pantalla

- **Base fija**: `origin/main` = `ba77c1f6dc072d1f11394e44394f6cde8b2fdba9` (hora del servidor al fijarla: Fri, 06 Nov
  2026 13:42:31 GMT). Aparte, rotulado: `origin/loop/activo` = `06de6876a878fa672b684ca9793a0f4f1fc0e4ba` (bitácora y
  traspasos; el encargo decía `dd7467218`, que es ancestro: la rama avanzó tres commits de bitácora) y el PR #945 en
  `106db89414b9286848e723153a2feb5cf631ba0f` (borrador, rama `claude/s173-vpr939-03`).
- **Cinco frentes, cinco verificadores** (tope de la regla S154): F1 MODIS con la vía «código MIROVA» corriendo; F2 VIIRS
  375 en producción (K desde #850) medido sobre el sistema corriendo; F3 censo de decisiones y cierres S160 a S174; F5
  identidad del pareo con MIROVA en los tres sensores; F0 la puerta de entrada (pendientes de S160 que no caen en ningún eje).
- **Recorte (2026-11-06, pedido de Nicolás vía la coordinadora S174)**: el eje VIIRS 750 con ROI B4 (#939) sale del plan
  para que entre VIIRS 375, el sensor con más pasadas y alertas, que la primera versión dejaba fuera porque elegía ejes
  por el código cambiado desde S160. B4 queda mirado por la sombra de V750-A (#945); sus pendientes de S160 pasan a F0
  (§1). Texto del eje recortado: commit `08d1b9ead`, §2 y §3 «F2. VIIRS 750 con ROI B4».
- **Segundo recorte (2026-11-06, pedido de Nicolás vía S174)**: entra F5, identidad del pareo, y sale F4
  (vencimientos simulando la ausencia), que era el primero en la fila de recorte porque repetía el eje de S160 F3.
  Sus pendientes pasan a F0 con fecha; lo que se pierde es la simulación de la ausencia. Texto: commit `a39d3c751`.
- **Eje nuevo**: F1 y F2 son nuevos (F1 es un detector que no existía en S160; F2 nunca se auditó como sistema corriendo
  contra MIROVA en las dos direcciones, por volcán y por cenit; F5
  pregunta si lo que el audit cuenta como acierto es la misma anomalía que alertó MIROVA). F3 es nuevo a medias (las decisiones
  del dueño contra el código nunca se auditaron; los cierres sí, en S160 F4). F5 es nuevo (pedido de Nicolás, 2026-11-06).
  Orden de recorte si hay que achicar: F3.
- **Cuándo**: nada se lanza antes del reinicio del plan semanal (2026-11-08 12:00 UTC). F2, F3, F5 y F0 desde ese
  momento; F1 después del audit semanal del lunes 2026-11-09 09:00 UTC, que es su prueba de campo.
- **Costo estimado** (§7): unos 4 millones de tokens y 6 a 7 horas de reloj, medido sobre el registro real de S160.

## 1. Puerta de entrada: los pendientes de S160 (regla C)

Fuente: `docs/AUDIT_S160.md` §5 y la fila D-43 de `tasks/LOOP_OBJETIVOS.md` en `loop/activo` (`06de6876a`, l. 522).
Según D-43 (re-verificada por un subagente Sonnet en S171 contra `478d9c086`): resueltas 1, 3, 5 y 7; en parte 2, 4 y 8;
abiertas 6 (C-10, Láscar MODIS 2026-03-27, antes de dar D18 por vetada) y 9 (K1 -0,7 y tope D9). Esa re-verificación
la hizo un solo agente y tiene cinco días: es una hipótesis con fecha (guía §2 regla 9), no un hecho.

Reparto (guía §4: cada pendiente va al frente de su eje; los que no caen en ninguno forman F0):

| pendiente de S160 | va a | por qué |
|---|---|---|
| 241, 242, C-06 (cese de Suomi NPP), 243 (decomiso MODIS 6.1), 245 (copia que se encoge), 247 (token), V3-01 a V3-04 | F0 | vencimientos: su eje salió del plan para que entre F5 (§0); F0 los clasifica con fecha, sin simular la ausencia |
| 203 (cúmulos V750 de cumbre en 0,0 MW), C-08, F1-H6 (D32), V2-09 a V2-13, C-02, C-03 | F0 | son VIIRS 750; su eje salió del plan (§0, recorte) |
| 201 (C1 de escena casi no toca lo publicado: 4 de 2.452 publicaciones V375), C-04 (Tupungatito VIIRS 375) | F2 | son VIIRS 375 |
| 281 a 297 sin aplicar, 287, 288, U12 (memoria), V4-01 a V4-03, decisión 8 (cola de campo) | F3 | son cierres y su propagación |
| decisiones 2, 6 y 9 (P2 tolerancia 0, C-10 y D18, K1 y tope D9), V0b-01 a V0b-03, V1a-01 en adelante, V1b-01, V0a-01, C-07, C-09, C-10, y el inventario sin verificar de S160 (F1a 3, F2 9, F3 6, F4 5, F1b 12) que no caiga en otro frente | F0 | no son de ningún eje de esta auditoría |

C-05 (geolocalización MODIS a más de 40° de cenit) queda en la cola de campo sin frente; lo mira F1 sólo si la vía cambió la geolocalización (SOSPECHA, no se sabe).

## 2. Los ejes, con su porqué

**F1. MODIS de producción con la vía «código MIROVA» corriendo en el NRT (nuevo).** Desde #934 (`499935c37`,
2026-11-02 17:18 UTC) el detector MODIS que publica no es K. Lo que se adoptó se midió en experimentos; lo que corre
es otra cosa: records reales, el predicado del tablero, la guardia K al lado y una regla de reversión que sólo vale si
su vigilante ve. Quien sufre un defecto aquí es el operador que mira un MODIS que cambió de detector hace cuatro días.
Dos datos de partida que el auditor no hereda, sólo comprueba: (a) `data/audit_continuous/guardia_modis_latest.json`
en la base dice `encendido_modis_utc: 2026-11-02 20:11:43` y `primera_observacion_via: 2026-11-02 01:15`, una
observación de la vía 19 horas antes del encendido (SOSPECHA: puede ser hora de pasada contra hora de proceso); (b) la
decisión 3 del bloque S174 (records `sin_grilla` o `sin_mxd03` tratados como K con aviso, VPR940b-04) está «NO
IMPLEMENTADO» (`loop/activo` `tasks/LOOP_OBJETIVOS.md` l. 657).

**F2. VIIRS 375 en producción, sobre el sistema corriendo (nuevo).** Es el sensor con más pasadas y alertas, corre K
desde #850 y es el que más mira el operador. La primera versión de este plan lo dejaba fuera porque elegía ejes por el
código cambiado desde S160; esa vara excluye justo lo que más publica. Se mide con records reales del NRT y el
predicado literal del tablero contra MIROVA en las dos direcciones (criterio de victoria, `docs/MISSION.md`):
ninguna protegida perdida, y cuánto publicamos en negativos limpios (A98: la brecha es sobre-publicación, no recall).
Estratificado por volcán y por cenit, porque Chillán cae con el cenit y el mecanismo está SIN ATRIBUIR (memoria S154).
Incluye el estado de la sombra V375-E y de su lector re-sellado en S172 (tag `s172-v375e-lector-resellado` =
`12b49057f`; la parada la mandan las noches, cerca del 2026-12-02).

**F3. Censo de decisiones y cierres S160 a S174 (nuevo a medias).** En la bitácora de `loop/activo` hay 308 entradas de
S160 a S174 (conteo de encabezados por sesión, `grep -c "^### .*S1NN[):,]"`), y entre `d516b9d8c` y la base hay 1.024
commits no automáticos. Las decisiones de Nicolás («Sí, a todo», frases selladas) nunca se auditaron contra el código:
una decisión aprobada y no implementada, o implementada distinto, es un defecto que ningún test ve. Los cierres sí se
auditaron en S160; aquí sólo el delta desde `d516b9d8c`.

**F5. Identidad del pareo con MIROVA (nuevo, pregunta de Nicolás del 2026-11-06).** Todo lo que el programa dice de
paridad (recall, protegidas, magnitud) descansa en un pareo que nunca se auditó como instrumento: el recall del audit
semanal es por noche y por círculo, no por pasada ni por foco, y lo calcula un port en Python del predicado y no el
tablero. Si un acierto puede ser otra fuente dentro del círculo, el recall alto no prueba que vemos lo que MIROVA ve. F5
mide eso en los tres sensores, sin auditar sus detectores. Entra en lugar de F4 (vencimientos), que era el primero en
la fila de recorte porque repetía el eje de S160 F3; sus pendientes quedan en F0 con fecha.

**F0. Pendientes de S160 sin eje.** Ver §1. Su pregunta es una sola: cada pendiente, ¿sigue abierto contra el código de
hoy, ya se resolvió, o nunca fue lo que decía?

**Qué no se audita**: el código del scraper Mirova-v1 (otro repo; sólo su salida), el perfil `experimental`, VIIRS 750 con ROI B4 y la simulación de vencimientos (recortados, §0), la integridad de #945 como PR (lo hace S174).

## 3. Los frentes (pre-registro: esto es lo que el sello congela)

Para cada frente: pregunta, qué cuenta como hallazgo, vara, tolerancia, **línea base roja** (defectos ya conocidos de su
eje que su instrumento tiene que volver a encontrar antes de que su cero valga) y entregable de campo.

### F1. La vía MODIS en el NRT

- **Pregunta**: lo que publica MODIS desde el encendido, ¿es lo que la vía «código MIROVA» dice que produce, lo ve el
  tablero con su predicado literal, y la guardia y la regla de reversión verían una regresión si ocurriera?
- **Hallazgo**: (a) un record MODIS posterior al encendido cuyo detector efectivo no es el que declara (`via_codigo_mirova`
  contra lo que realmente corrió); (b) una diferencia entre lo que la vía guarda y lo que el predicado del tablero
  publica; (c) un camino por el que la vigilancia de la guardia o el audit semanal dan VERDE con una regresión real
  (vigilante ciego, guía §3); (d) un criterio de la regla de reversión §4 que no se puede evaluar con lo que el sistema
  produce.
- **Vara**: el predicado del tablero ejecutado con node (`scripts/banco_paridad.py::correr_node`, l. 156 en la base) y
  la regla §4 de `experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md` tal como está en la base.
- **Línea base roja**: (1) su censo de records tiene que encontrar records `sin_grilla` o `sin_mxd03` posteriores al
  encendido (o mostrar que no hay ninguno con un control que sí los encontraría, por ejemplo un record sintético); hoy
  caen a K sin aviso (VPR940b-04); (2) corrido sobre los datos de `79f410697` (2026-11-02), su clasificación por
  detector tiene que dar 0 records de la vía, que es por qué #915 y #936 juzgaron MODIS con K (bloque S175, fila 1).
- **Insumos**: además de la base, «SHA_CAMPO» = `origin/main` en el momento de lanzar F1 (después del audit del
  2026-11-09), declarado en su encabezado; los records posteriores a la base se leen con `git show «SHA_CAMPO»:<ruta>`.
- **Campo**: el resultado del audit semanal del 2026-11-09 contra la regla §4; uno o más casos MODIS de la vía para la
  cola, con pasada UTC y lámina de MIROVA que mirar.

### F2. VIIRS 375 en producción

- **Pregunta**: en los records reales del NRT, ¿publicamos todo lo que MIROVA alerta en VIIRS 375 y cuánto publicamos
  donde MIROVA no vio nada, por volcán y por cenit? ¿Y la sombra V375-E y su lector miden lo que dicen medir?
- **Hallazgo**: una protegida (1 MW o más, lectura A) que no publicamos; un estrato de volcán o de cenit donde la
  sobre-publicación en negativos limpios o la pérdida se concentra y el agregado la esconde (Simpson, guía §3b fila 13);
  una regla del tablero o del etiquetado que trata distinto lo que D-9 dice (alertas de 0,05 MW o menos cuentan como
  «MIROVA no vio nada»); un camino por el que la sombra V375-E o su lector dan CUMPLE o VERDE sin datos (cobertura
  pareja, guía §3b fila 2), o una fecha de parada que no se sigue de las noches acumuladas.
- **Vara**: el predicado del tablero con node; `etiquetar` y `clase_mirova.py` en la base para alerta, protegida y
  negativo limpio; el cenit, del campo que guarda cada record (el auditor declara cuál). Para la sombra, su
  pre-registro (`experiments/_s165_v375_via/PREREGISTRO_IMPL_V375E.md`) y el lector en el tag
  `s172-v375e-lector-resellado` (`12b49057f`); el auditor comprueba que el lector de la base es el del tag.
- **Ventana**: desde la frontera de régimen de K en la fecha de los datos (guía §3b fila 10; el histórico se reprocesó
  con K en #883), hasta la base; por tramo si la cruza otro cambio, y con la calidad de la referencia por mes (A119).
- **Línea base roja**: (1) sobre los datos de `d516b9d8c`, su conteo tiene que reproducir el 201 de S160 (4 de 2.452
  publicaciones VIIRS 375 tocadas por el C1 de escena) o explicar con números por qué no; (2) estratificado por cenit,
  Nevados de Chillán tiene que mostrar la caída con el cenit de la memoria S154; si su estratificación no la ve, está
  ciega. Si el lector de la sombra corrido sobre una noche sintética sin datos da algo distinto de SIN DATO, eso también
  es hallazgo.
- **Campo**: una protegida perdida o un negativo limpio publicado de alto VRP, con pasada UTC y lámina de MIROVA; la
  fecha de parada de la sombra (cerca del 2026-12-02) como ítem con fecha; C-04 actualizado.

### F3. Decisiones y cierres S160 a S174

- **Pregunta**: cada decisión aprobada por Nicolás y cada cierre escrito desde S160, ¿está en el código de hoy como se
  aprobó, y sus rebajas llegaron a todo lo que las cita (A113)?
- **Hallazgo**: decisión aprobada sin implementar o implementada distinto; implementada sin frase de Nicolás registrada
  (aprobación reenviada, guía §6 paso 6); cierre sin respaldo citable; rebaja no propagada a CLAUDE.md, `MISSION.md`,
  `MIROVA_DIVERGENCES.md`, `SINTOMAS.md` o la memoria. Veredicto por ítem: verificado, en parte, refutado, SIN EVIDENCIA
  o «no era un cierre».
- **Vara**: la bitácora de `loop/activo` en `06de6876a` (`tasks/LOOP_OBJETIVOS.md` §6) y los bloques de arranque S161 a
  S175 de esa rama; el código y los documentos de la base. Instrumento de partida (es un piso):
  `experiments/_s145_censo_cierres/censo.py`.
- **Línea base roja**: (1) sobre `77e54e8e0^`, tiene que marcar la nota S153 de A85 como desfasada de los datos (la
  corrigió #950); (2) sobre `d516b9d8c`, tiene que encontrar el hallazgo 281 de S160 («C0 antes del 2026-09-18» en los
  documentos rectores).
- **Campo**: decisiones de Nicolás que sólo se cierran mirando el tablero.

### F5. Identidad del pareo con MIROVA (los tres sensores)

- **Pregunta**: lo que el audit semanal y el banco cuentan como «MIROVA vio y nosotros también», ¿es la misma pasada, el
  mismo foco y una magnitud comparable, o puede ser otra pasada u otra fuente dentro del círculo? Y lo que queda sin par,
  ¿queda fuera por una convención de tiempo y no por la física?
- **Por qué** (leído en `origin/main` `752d348bc`, a verificar por el auditor, no a heredar): el recall titular
  (`scripts/auto_audit_weekly.py`, `recall_por_sensor`, l. 363) es por (volcán, familia de sensor, noche) y cuenta acierto
  con `pc.vrp_mw > 0` y centroide dentro de `inner_radius_km` (3 a 20 km); VIIRS 375 junta SNPP, NOAA-20 y NOAA-21. Lo
  calcula con un port en Python del criterio (l. 14 a 15, armado en l. 658 a 690), mientras el banco usa el predicado de
  `frontend/index.html` con node (l. 214). El banco sí parea por pasada a ±120 s (`clase_mirova.VENTANA_S`, l. 112), pero
  la distancia de MIROVA (`dist_ref`) sólo la usa en filas FALSO_POSITIVO (`banco_paridad.py`, l. 339 y 450).
- **Seis preguntas** (cada una con numerador, denominador y ventana, A111, estratificadas por volcán y sensor):
  - **I1 pasada**: recall por pasada contra recall por noche; en los aciertos sin misma pasada, si la nuestra fue antes o
    después y de qué satélite.
  - **I2 posición**: en las alertas pareadas por pasada, nuestra `final_hotspot_dist_km` contra la `Distancia_km` del
    OCR; |Δdist| sirve para descartar, no para identificar (A93, A107), así que la identidad se decide con lat/lon
    contra el píxel del TIF de MIROVA donde exista. Clases por acierto: (i) misma pasada y mismo foco; (ii) otra
    pasada, mismo foco; (iii) otra fuente dentro del círculo; (iv) SIN DATO de posición. Primero Lastarria (hacia
    Lazufre), Tupungatito (anillo glaciar, A19), Cordón Caulle (inner de 20 km, ROI B4 en VIIRS 750 desde #939) e Isluga,
    como hipótesis y no como hecho.
  - **I3 predicado**: en las mismas noches, el port de Python del audit contra el predicado del tablero con node;
    cuántas noches difieren y en qué sentido (A97; VIIRS 375 publica `f5_core_vrp_mw`).
  - **I4 magnitud**: el ratio de magnitud del audit compara el máximo de la noche de cada uno, que puede venir de pasadas
    distintas, y nuestra `pc.vrp_mw` contra la suma de todos los píxeles alertados de MIROVA (D32); el ratio restringido
    a la misma pasada, y cuánto cambia.
  - **I5 etiqueta**: Mirova-v1#20 (V31, mergeado 2026-10-09 14:01 UTC) dejó de crear filas con la distancia de otra
    pasada; antes de esa fecha la distancia del OCR puede ser ajena (A119). I2 se mide desde esa hora y lo anterior va en
    un estrato aparte.
  - **I6 tiempo**: la distribución de |Δt| de los pares; cuántas alertas de MIROVA quedan sin par con un record nuestro
    a 2 a 10 min (SOSPECHA de que una convención distinta, inicio del gránulo contra hora del píxel, mande pares reales a
    `sin_info`, fuera del denominador sin aviso).
- **Hallazgo**: un volcán o estrato donde la clase (iii) es una fracción no despreciable de los aciertos, y en especial
  cualquier protegida (1 MW o más) cuyo acierto sea (iii): ahí el recall dice que vimos lo que MIROVA vio y no es así;
  una diferencia port contra node que cambie el recall publicado; un ratio de magnitud que cambie de banda al
  restringirlo a la misma pasada; pares reales perdidos por la ventana de tiempo.
- **Vara de posición**: el TIF de MIROVA archivado en `MendozaVolcanic/mirova-tif-archive`, leído por la API o por archivo
  suelto, nunca con `pull` (17 GB, memoria S143). Los TIF están congelados desde el 2026-09-22 (memoria
  `reference_mirova_tif_congelados_20260922`): después de esa fecha la clase sale (iv) salvo otra posición citable, y
  la distancia del OCR sola no basta.
- **Tolerancia** (en unidades del objeto, A91, fijada aquí): mismo foco = nuestro punto a no más de 2 píxeles nominales
  del sensor del píxel de MIROVA (750 m en VIIRS 375, 1,5 km en VIIRS 750) y 3 km en MODIS por su desplazamiento
  conocido de 1 a 3 km hacia el nadir (memoria `project_modis_geo_interp_offset`). Sin TIF, (ii) contra (iii) se decide
  sólo si nuestra distancia al cráter difiere en más de esa tolerancia de la pasada que sí coincide esa noche; si no
  hay ninguna, (iv).
- **Línea base roja**: (1) sobre `data/audit_continuous/latest.json` del 2026-11-02, I1 tiene que reproducir las noches
  comunes con misma pasada a ±120 s (125 de 194 en VIIRS 375, 32 de 42 en VIIRS 750, 14 de 16 en MODIS, conteo de la
  coordinadora sin verificar) o explicar la diferencia; (2) un acierto sintético por otra fuente (copia de un record real
  de Cordón Caulle con su punto movido 15 km del cráter, misma noche) tiene que salir (iii), uno de misma pasada y mismo
  píxel (i), y uno sin TIF ni pasada coincidente (iv); (3) un par desfasado 3 min a propósito tiene que aparecer en I6;
  (4) una noche donde port y node difieren a propósito (un record con `distance_class` fuera de summit) tiene que
  aparecer en I3.
- **Alcance**: el pareo y el conteo, no los detectores (MODIS es F1, VIIRS 375 es F2, VIIRS 750 lo mira la sombra de
  #945). Lee records; no reprocesa.
- **Campo**: dos o tres aciertos de clase (iii) o (iv), con pasada UTC, para mirar contra la lámina de MIROVA.

### F0. Pendientes sin eje

- **Hallazgo**: un pendiente de §1 (fila F0) clasificado contra el código de hoy como abierto, resuelto (con el commit
  que lo resolvió) o «nunca fue lo que decía».
- **Vara**: el código y los datos de la base; para C-07 y V0b-01, el port del código de MIROVA V750 que ya existe.
- **Línea base roja**: (1) la decisión 1 de S160 (#891) tiene que salir resuelta, con su commit; (2) la decisión 6
  (C-10) tiene que salir abierta. Si el clasificador da lo mismo para las dos, no clasifica.
- **Campo**: C-07, C-09, C-10 actualizados; C-06 (Suomi NPP después del 2026-11-02 13:00 UTC, mirado en los records)
  y la rotación de `EARTHDATA_TOKEN` antes del 2026-11-27 (vence el 2026-12-07 18:03 UTC) como ítems con fecha.

### Corte del verificador (fijado antes de lanzar)

Pasan al verificador: todo hallazgo de gravedad 3 o más; todo hallazgo de cualquier gravedad sobre un instrumento que
sostiene una decisión vigente (la regla de reversión de MODIS, la sombra de V750-A, el audit semanal, la guardia); y toda
línea base roja que el auditor no pudo reencontrar. Lo demás se publica con su conteo y es la puerta de S176.

## 4. Verificadores y síntesis

- Un verificador por frente (V0, V1, V2, V3 y V5), del otro modelo: los auditores son Fable a `high`, los verificadores Opus a `high`
  (guía §5). Reciben título, archivo:línea o script:salida y gravedad; no abren el informe del auditor (bloque del
  verificador de `docs/_prompts/PREAMBULO-AUDITOR.md`). `caminos.md` con su sha256 y hora del servidor antes de abrir
  nada; el orquestador guarda el hash.
- Síntesis del orquestador en `docs/AUDIT_S175.md`, sólo con veredictos de verificador: los tres números de la regla C,
  guarda y su rojo por confirmado, lista de pruebas de campo, decisiones de Nicolás con recomendación y el registro de
  agentes (modelo, **esfuerzo declarado por el agente**, duración, tokens).

## 5. Dónde corre y con qué recursos

- **Worktree exclusivo** de esta auditoría: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378`,
  rama `claude/relaxed-almeida-d17378`, en la base y sin `pull` mientras corren los auditores. Declarado a S174 en la
  carpeta de notas compartidas. Informes y scripts: `experiments/_s175_audit/<agente>/` dentro de este worktree.
- **Temporales grandes**, una carpeta por agente con su nombre: `C:\Users\nmend\vrp-temporales\s175_audit\<agente>\`
  (C: tenía 19 GB libres a las 13:4x UTC; D: 4,9 GB, no se usa). Nada en las carpetas de S174 (`D:\vrp-trabajo\temporales\s174-*`).
- **Instantánea**: `git archive ba77c1f6d pipeline scripts frontend .github tests docs experiments/_s160_audit
  experiments/_s171_modd_adopcion CLAUDE.md README.md volcanoes.yaml | tar -x -C C:\Users\nmend\vrp-temporales\s175_audit\main\`
  (con rutas, guía §0; trae la configuración de la raíz, lección S160 §7 punto 4). Los datos se leen de este worktree
  sólo si `git diff --quiet ba77c1f6d -- data latest_consolidado.csv` sale con 0; si no, con `git show`.
- **Insumos de GitHub**, una vez, por el orquestador en la ola 0: `gh api rate_limit`, últimas 50 corridas de `nrt.yml`,
  `audit-weekly.yml`, `guardia-k-modis.yml`, `vigilancia-guardia-modis.yml`, `sync-mirova-csv.yml` y
  `nrt-healthcheck.yml`, últimos commits de `MendozaVolcanic/Mirova-v1` y `gh secret list` (nombres y fechas, sin
  valores), con la hora del servidor, a `C:\Users\nmend\vrp-temporales\s175_audit\insumos\`.

| recurso | tope | parada |
|---|---|---|
| disco C: | 2 GB por auditor, 0,5 GB por verificador | cualquiera se detiene si C: baja de 3 GB; el orquestador mide `du` en cada notificación |
| procesos pesados locales | 2 a la vez en total (contando los de S174) | el orquestador no lanza un tercero |
| API de GitHub | 10 llamadas por auditor, 5 por verificador, leyendo antes los insumos | ninguna si `rate_limit` baja de 200 |
| workflows | ninguno | despachar uno es parada |
| credenciales | ninguna | usar una es parada |

**Olas**: 1) F2, F3, F5, F0 desde el 2026-11-08 12:00 UTC (4 en paralelo, ninguno pesado salvo F2 si reprocesa; si
reprocesa, cuenta como pesado); 2) V2, V3, V5, V0 a medida que terminan; F1 desde el 2026-11-09 09:30 UTC, después
de la corrida del audit semanal; 3) V1 y síntesis. Esperas y verificadores en primer plano.

## 6. Prompts

Cada prompt es, en este orden: el bloque `<preambulo_auditor>` de `docs/_prompts/PREAMBULO-AUDITOR.md` **entero**, tal
como está en la base (sha256 del bloque entre `<preambulo_auditor>` y `</preambulo_auditor>`, extraído con
`sed -n '/^```text$/,/^```$/p' | awk '/<preambulo_auditor>/,/<\/preambulo_auditor>/'`: `36a55c66d016afb3a28b2cdca446f19c32065c8c5b9e6affdfa1e31bb2cb6c1b`),
con los huecos llenos; la `<tarea>` del frente; y el bloque `<autonomia>` del mismo archivo. Revisado el bloque al
abrir este plan: no trae carpetas ni reglas viejas; la frase «doce veces al día» del contexto queda como SOSPECHA (el NRT
lo dispara un cron externo y no se midió cuántas corridas hace hoy; lo cuenta F0 con los insumos de la ola 0). Antes de lanzar,
`grep -nE "«[A-Z_]+»"` sobre cada prompt armado da cero líneas.

### 6.1 Huecos comunes

```text
«DEFINICIONES_DE_LA_VARA» =
- «publica»: lo que da el predicado del tablero ejecutado con node por scripts/banco_paridad.py::correr_node (l. 156)
  sobre frontend/index.html del commit ba77c1f6d (regla A97). Nunca una reconstrucción a mano.
- «alerta de MIROVA», «protegida» y «negativo limpio»: lo que devuelve scripts/banco_paridad.py::etiquetar (l. 317) en
  ba77c1f6d, con la regla D-9 de scripts/clase_mirova.py. Protegida es alerta de 1 MW o más (lectura A, D-4).
- pareo de una fila de MIROVA con una pasada nuestra: TOL_S de scripts/banco_paridad.py l. 78 en ba77c1f6d.
- la referencia: la copia del repo en ba77c1f6d, latest_consolidado.csv (sha256 c54bec14b290b3040df065a1887bb7cc444a725bc5297e16e34ac194e59d618e)
  y data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv (sha256 cb18f9cd695940d5960b48cf322622c1fc2491f2920cef604da88f046b6b16af),
  no la remota viva.
- «detector efectivo» de un record MODIS: la vía si via_codigo_mirova es true, K en otro caso (scripts/auto_audit_weekly.py
  l. 446 a 456 en ba77c1f6d). F1 audita esta definición: para F1 es objeto, no vara.
- documentos de loop/activo: en 06de6876a. PR #945: en 106db8941, rotulado «fuera de main».
«LIMITES_DE_RECURSOS» = Esta tarea no nombra ningún workflow ni credencial. Hasta 10 llamadas a la API de GitHub
(verificador: 5), después de leer C:\Users\nmend\vrp-temporales\s175_audit\insumos\. Disco: tu carpeta temporal, tope
2 GB (verificador 0,5 GB). Como mucho un proceso pesado tuyo a la vez. En el encabezado declara el esfuerzo con que
realmente corres (en S172 y S174 agentes pedidos a high informaron 10 a 15): si no lo sabes, escribe «SIN DATO».
```

| agente | «CARPETA» | temporal | «RANGO» |
|---|---|---|---|
| F0 | `...\relaxed-almeida-d17378\experiments\_s175_audit\f0\` | `C:\Users\nmend\vrp-temporales\s175_audit\f0\` | 101 a 149 |
| F1 | `...\_s175_audit\f1\` | `...\s175_audit\f1\` | 151 a 199 |
| F2 | `...\_s175_audit\f2\` | `...\s175_audit\f2\` | 201 a 249 |
| F3 | `...\_s175_audit\f3\` | `...\s175_audit\f3\` | 251 a 299 |
| F5 | `...\_s175_audit\f5\` | `...\s175_audit\f5\` | 301 a 349 |
| Vn | `...\_s175_audit\vn\` | `...\s175_audit\vn\` | Vn-01 en adelante |

(`...` es `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378`;
en el prompt armado va la ruta entera.)

### 6.2 Tareas (objetivo y límites, no checklist)

Cada `<tarea>` es el texto de su frente en §3 (pregunta, hallazgo, vara, línea base roja, campo) más estas líneas:

```text
Empieza por la línea base roja de tu frente: corre tu instrumento sobre el commit indicado y guarda el rojo en tu
CARPETA antes de medir la base. Si no lo reencuentras, eso es tu primer hallazgo (el instrumento está ciego o el
defecto nunca fue como se escribió) y lo dices antes de seguir. Mide en la base ba77c1f6d salvo donde tu frente
diga otro commit, y nombra el commit en cada número. Lo que viva fuera de main va rotulado «fuera de main».
No toques las ramas ni las carpetas de la sesión S174 (claude/s173-vpr939-03, claude/s174-*, D:\vrp-trabajo\temporales\s174-*).
```

F1 agrega: «SHA_CAMPO» = el `origin/main` que el orquestador anote al lanzarte, y la ruta de su copia de los insumos.
F3 agrega: el inventario de decisiones lo armas tú desde la bitácora; declara el comando que lo arma, para que la
cobertura sea auditable. F0 agrega la lista de §1 fila F0, tal cual.

### 6.3 Verificadores

Preámbulo entero con los huecos del verificador, el bloque `<verificador>` del mismo archivo, la lista que arma el
orquestador desde `hallazgos.csv` (título, archivo:línea o script:salida, gravedad; sin el razonamiento del auditor,
tampoco en celdas) y el bloque `<autonomia>`.

## 7. Costo estimado

Base medida, no adivinada: `experiments/_s160_audit/REGISTRO_AGENTES.md`. Auditores Fable de S160: 384.716 a 503.001
tokens y 24 a 48 minutos; verificadores Opus: 316.650 a 384.714 tokens y 16 a 37 minutos.

| | agentes | tokens estimados | reloj |
|---|---|---|---|
| auditores (Fable high) | 5 | 2,0 a 2,5 millones | 25 a 50 min cada uno |
| verificadores (Opus high) | 5 | 1,6 a 1,9 millones | 15 a 40 min cada uno |
| orquestador (ola 0, listas, síntesis) | 1 | 0,3 a 0,5 millones | 1,5 h |
| **total** | 11 | **3,9 a 4,9 millones** | 6 a 7 h en tres olas |

Riesgo de subestimar: F1 y F2 leen records reales (VIIRS 375 es el sensor con más records) y pueden reprocesar; F3
barre 308 entradas. F5 lee records de los tres sensores y los TIF ya archivados, sin reprocesar; reemplaza a F4 y no
cambia el total. Si el plan semanal tras el reinicio no deja margen para 5 millones, recortar F3 (§0).

## 8. Lo que el plan no hace, y lo que decide Nicolás antes de lanzar

No hace: ningún arreglo; nada en `pipeline/`, `data/` ni `frontend/` (A45); ningún merge; ningún workflow despachado;
ningún reproceso en Actions; no audita #945 como PR ni el código de Mirova-v1.

| # | decisión | recomendación |
|---|---|---|
| 1 | Los cinco frentes, o recortar | los cinco: VIIRS 375 en lugar de VIIRS 750 B4 y la identidad del pareo (F5) en lugar de los vencimientos (F4), los dos por tus preguntas; si el uso no alcanza, F3. Alternativa: seis frentes con F4 de vuelta, más de lo que permite la regla S154 (5 + 5) y unos 0,9 millones más |
| 2 | F1 espera al audit del 2026-11-09 | sí: sin esa corrida, F1 audita un sistema sin su primer veredicto semanal |
| 3 | Fable como auditor y Opus como verificador | sí (guía §5); la alternativa barata, Sonnet auditor, no tiene medición propia en este proyecto |
| 4 | Sellar este plan | con tu sí, commit y hash como «SHA_PLAN» antes de la ola 1 |
| 5 | Tolerancia de «mismo foco» en F5 (I2): 2 píxeles nominales en VIIRS, 3 km en MODIS | sí, como criterio propuesto y no medido; en MODIS se agranda porque su geolocalización ya tiene un desplazamiento conocido de 1 a 3 km hacia el nadir (memoria `project_modis_geo_interp_offset`), que con 2 km fabricaría «otra fuente» falsa; si prefieres otra, se cambia antes de sellar |
