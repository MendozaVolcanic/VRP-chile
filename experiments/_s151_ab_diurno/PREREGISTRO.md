# Pre-registro del A/B diurno de VIIRS (D-10, issue #813): BORRADOR, NO DESPACHABLE

Estado: **borrador** (2026-10-15, revisado tras el verificador con contexto limpio del PR #821).
**No se puede despachar**: el workflow no existe, los dos perfiles de brazo no existen y el evaluador
diurno no está escrito (sección 7). Este documento fija qué se mide y con qué vara ANTES de mirar un
solo dato del A/B. Todo número de acá sale de `experiments/_s151_ab_diurno/sustrato.py` (salida en
`sustrato_salida.txt` y `sustrato.json`) o del estudio `experiments/_s151_alertas_diurnas/`; ninguno
se transcribe a mano de memoria.

## 1. El fenómeno y la pregunta

De día el canal de infrarrojo medio suma a la emisión térmica la luz solar reflejada: una nube, un
salar o una ladera clara levantan píxeles sin nada caliente debajo, y el índice térmico de toda la
escena se vuelve más ruidoso. MIROVA no deja de mirar: procesa VIIRS de día (Campus et al. 2022,
*Sensors* 22:1713, p. 16 §5 y p. 17 Tabla 4) con la columna diurna de la Tabla 1 de Coppola 2016a
(p. 7: K1 = -0,6, C1 = 0,02, C2 = 15 en las dos ROI), y con esa vara alta es muy callado: alerta en
**21 de 5.071** pasadas VIIRS diurnas de la tabla en las ventanas de abajo (0,41 %).

La réplica descarta todo VIIRS diurno, así que pierde por construcción las alertas diurnas de
MIROVA. Desde el PR #821 la rama diurna está cableada y apagada (`ENABLE_DAYTIME_VIIRS`).

**Pregunta:** con la rama diurna encendida, ¿la réplica recupera las alertas diurnas protegidas de
MIROVA siendo de día tan callada como MIROVA?

La vara de la réplica es MIROVA (A115). La sobre-publicación nocturna de la réplica (A98; A104 cita
87,1 % de publicación en negativos limpios de VIIRS 375 desde #571) es el defecto conocido, **no**
una vara: compararse contra ella aprobaría miles de publicaciones diurnas de más contra una
parsimonia de MIROVA de 0,4 %. Por eso el criterio de abajo no la usa (corrección del verificador).

El riesgo concreto, escrito antes de correr: el Test 1 integrado suma MIR ABSOLUTO sobre un disco de
3 km y no tiene columna diurna en ningún paper (D30); de día el Sol calienta y refleja en todo el
disco. Es el camino con más probabilidad de sobre-publicar (A114: puede saturar la métrica). Si eso
pasa, el A/B lo dice; no se corrige antes de medir.

## 2. Brazos

| brazo | perfil (por crear) | diferencia con `mirova_equivalent` |
|---|---|---|
| control | `_s151_ab_diurno_control` | ninguna (sólo `data_subdir` propio, A47) |
| diurno | `_s151_ab_diurno_on` | `enable_daytime_viirs: true` y nada más |

El brazo diurno corre **sin** `--no-night-filter`: lo que se prueba es que el flag abre por sí solo
las cinco compuertas (A118; en S92 el A/B diurno de MODIS abrió una y midió cero).

## 3. Ventanas (tramos A119) y sustrato medido

Positivos usables bajo A119: **37** pasadas VIIRS diurnas protegidas (lectura A, 1 MW o más; las 40
del estudio menos 3 de MODIS, que la rama de D-10 no toca). Las seis ventanas cubren las 37.

| ventana | fechas (incl.) | volcanes | positivos (V375/V750) | fuente de los positivos | negativos diurnos limpios (V375/V750) | alerta MIROVA / pasadas VIIRS diurnas de tabla (V375; V750) | etiqueta que decide (A119) |
|---|---|---|---|---|---|---|---|
| W1 | 2026-03-01 a 03-20 | Láscar | 5 (5/0) | 5 tabla | 47 (20/27) | 6/37; 0/40 | sólo tabla |
| W2 | 2026-06-13 a 06-30 | 11 Tier A | 12 (11/1) | **12 sólo OCR** | 1.099 (508/591) | 0/573; 0/616 | tabla y OCR |
| W3 | 2026-07-20 a 07-31 | 11 Tier A | 1 (1/0) | OCR | 800 (403/397) | 2/424; 0/410 | tabla y OCR |
| W4 | 2026-08-13 a 08-31 | 11 Tier A | 7 (5/2) | 1 tabla, 6 OCR | 994 (501/493) | 3/540; 0/523 | tabla y OCR |
| W5 | 2026-09-01 a 09-20 | 11 Tier A | 5 (4/1) | OCR | 1.075 (546/529) | 2/575; 0/549 | tabla y OCR |
| W6 | 2026-10-01 a 10-14 | 11 Tier A | 7 (5/2) | 7 tabla | 732 (367/365) | 6/399; 2/385 | tabla y OCR |

**Parsimonia de MIROVA de día (W2 a W6 juntas, vara de G2):** VIIRS 375 alerta en **13 de 2.511**
pasadas diurnas de la tabla (`p_MIROVA` = 0,0052); VIIRS 750 en **2 de 2.483** (0,0008). Contar
también las alertas del OCR no cambia estos números: ninguna alerta OCR diurna cae a 120 s o menos
de una pasada de la tabla (las 24 pasadas positivas sólo OCR son pasadas que la tabla no lista).

Notas que pesan:
- **W2 depende entero del OCR.** Sus 12 positivos (un tercio de los 37) son alertas sólo OCR, y la
  tabla no tiene ni una alerta diurna en W2 (0 de 1.189 pasadas). Bajo A119 desde el 2026-06-13
  decide «tabla y OCR», así que cuentan; pero el OCR de ese tramo tiene tres defectos conocidos que
  la tabla no tiene: la distancia recién se mide desde el 2026-06-13 (el primer día de W2), la
  geometría se calibró recién el 2026-06-11, y en las filas sólo OCR de Suomi NPP la distancia y la
  clase pueden ser de OTRA pasada hasta el arreglo del 2026-10-09 (el VRP sí es suyo). Además W2
  contiene el caso de A76 (Láscar 2026-06-15 17:24, 760,6 MW, reflejo sobre nube según el estudio),
  11 de sus 12 positivos son de Láscar y Lastarria, y 9 de los 12 salen con magnitud
  desproporcionada en el estudio (`experiments/_s151_alertas_diurnas/real_o_reflejo_filas.json`). Consecuencia: **M1 se informa con y sin W2**, y el veredicto de G1 tiene
  que sostenerse también sin W2; si sólo pasa gracias a W2, el resultado es «depende del OCR» y
  decide Nicolás.
- W1 es anterior al 2026-04-01: la tabla exponía menos gránulos VIIRS por noche, así que su tasa
  por pasada **no se suma** con las de W2 a W6 (A119); se informa aparte. Es además la única ventana
  donde todos los positivos tienen fila de tabla, y la parsimonia de Láscar ahí es alta (6 de 37).
- El pareo usa hora, volcán y sensor, **nunca** la distancia del OCR.
- El 760,6 MW cuenta como positivo: la vara de la réplica es lo que MIROVA publica (A115), no si es
  calor real; separar reflejo es tarea del perfil `experimental`.
- Negativo diurno limpio: pasada VIIRS diurna de la TABLA en que todas sus filas son RUTINA y MIROVA
  no alertó ese volcán en todo ese día (ningún sensor ni fuente). Análogo diurno del negativo limpio
  nocturno de `scripts/banco_paridad.py`.

## 4. Métricas

Unidad: la **pasada** (volcán, sensor, hora UTC con tolerancia de 120 s, la de `banco_paridad`).
«Publicamos» = el predicado del dashboard (`isValidDetection` de `frontend/index.html`) ejecutado con
node, nunca uno reconstruido a mano (A97). Todos los denominadores son de pasadas **procesadas** por
el brazo (sección 5, cobertura diurna); las no procesadas se cuentan aparte.

- **M1, recall diurno**: positivos procesados en que el brazo diurno publica / positivos procesados.
  En el control es 0 por construcción (store rechaza el VIIRS diurno). Se informa con y sin W2.
- **M2, publicación en negativos diurnos limpios** (`q_neg`): negativos diurnos limpios procesados
  en que el brazo diurno publica / negativos diurnos limpios procesados.
- **M3, publicación diurna total** (`q_dia`): pasadas VIIRS diurnas de la tabla, procesadas, en que el
  brazo diurno publica / pasadas VIIRS diurnas de la tabla procesadas. Es la cifra comparable con
  `p_MIROVA` (misma población de pasadas).
- **M4, cuenta absoluta** (lo que Nicolás decide si G2 falla): **alertas protegidas recuperadas**
  (numerador de M1) contra **publicaciones agregadas en negativos diurnos limpios** (numerador de M2),
  por sensor y por ventana, con la lista de pasadas de cada lado.
- **M5, referencia nocturna** (informativa, NO entra al criterio): publicación del control en
  negativos limpios nocturnos de la misma ventana y volcanes. **Se calcula bajo el perfil de control**
  o etiquetando día y noche por elevación solar explícita. Nunca bajo el perfil del brazo diurno: con
  el flag encendido `es_pasada_diurna_descartada` deja de descartar pasadas VIIRS diurnas, y la
  definición nocturna de `banco_paridad` metería pasadas diurnas entre los «negativos nocturnos»
  (verificador del PR #821).
- Estratos obligatorios: sensor (V375, V750), ventana, y Láscar contra el resto (Láscar trae 12 de los
  37 positivos y domina el nulo nocturno del estudio).

## 5. Nulo medido (A110)

1. **El instrumento puede dar distinto de cero** (A116): el brazo diurno tiene que traer records
   diurnos con `diag_umbrales_diurnos = True` en cada ventana con pasadas diurnas en la tabla, y el
   control ninguno. Si el brazo diurno trae cero records diurnos, el cableado falló (el caso S92) y el
   A/B es INDECIDIBLE, no un «no mejora».
2. **Las noches no cambian**: los records nocturnos de los dos brazos tienen que ser idénticos campo a
   campo (salvo `updated`, `processed_utc` y `regimen`). El flag no toca la noche por construcción
   (`tests/test_rama_diurna_viirs_s151.py`); una diferencia es un defecto del cableado o una
   diferencia de cobertura de NASA (A108), y se resuelve antes de mirar M1 a M4.
3. **Cobertura nocturna pareja** (A108): pasadas nocturnas por brazo contadas contra el control antes
   de mirar el veredicto; un job corto se repite.
4. **Cobertura diurna** (A108, agregado tras el verificador; el control no tiene pasadas diurnas, así
   que el punto 3 no la cubre). Para cada pasada VIIRS diurna de la tabla y cada positivo, el
   evaluador la clasifica en una de tres clases, contra el log y el JSON del brazo diurno:
   - **no procesada**: el gránulo no se bajó o no llegó al procesador (búsqueda vacía, descarga
     fallida, host caído A64, sin geolocalización). No hay record ni línea de proceso en el log;
   - **procesada sin publicar**: hay record (o el procesador devolvió record y store lo guardó) y el
     predicado del dashboard no lo publica;
   - **procesada y publicada**.
   Las **no procesadas salen de los denominadores de M1, M2 y M3** y se informan aparte, por ventana y
   sensor, contra el total de pasadas de la tabla. Si más del 10 % de los positivos de una ventana
   quedan no procesados, esa ventana se repite (job corto) antes de evaluarla; si siguen faltando, se
   informa como cobertura insuficiente y no entra al veredicto.
5. **Nulo de discriminación**: si el brazo diurno publicara al azar, recuperaría positivos a la misma
   tasa con que publica en negativos (`q_neg`). Se mide barajando 10.000 veces las etiquetas
   positivo/negativo **dentro de cada estrato volcán × sensor** y recalculando `M1 − q_neg`; el
   percentil 95 de esa distribución es el umbral. Antes de usarlo, el barajado se corre sobre un caso
   donde el nulo es conocido (etiquetas ya barajadas: el percentil 95 debe quedar alrededor de cero)
   y sobre uno donde debe fallar (un brazo sintético que publica exactamente en los positivos).
6. **Poder**: con 37 positivos y `q_neg` = 0,3, la desviación de M1 es del orden de 0,075; un recall
   debajo de ~0,45 no se distingue del azar. Si `q_neg` sale cerca de 1 (saturación por el Test 1,
   A114), el A/B no puede decidir nada sobre la Tabla 1 diurna y lo dice.

## 6. Criterio (pre-registrado)

- **G1, discrimina**: `M1 − q_neg` mayor que el percentil 95 del nulo barajado, en W2 a W6 juntas, y
  también en W3 a W6 (sin W2, ver §3). W1 se informa aparte por A119. Si falla en W2 a W6:
  **NO ADOPTAR**. Si pasa sólo con W2: **depende del OCR, decide Nicolás**.
- **G2, tan callada como MIROVA de día**, por sensor, sobre W2 a W6: la cuenta de pasadas diurnas de
  la tabla procesadas en que el brazo diurno publica (numerador de M3) no puede ser mayor que lo que
  explica la parsimonia de MIROVA en esas mismas pasadas. Prueba binomial de una cola: con `n` las
  pasadas procesadas y `p_MIROVA` medido arriba (VIIRS 375: 13/2.511; VIIRS 750: 2/2.483), G2 falla si
  P(X ≥ publicadas | n, p_MIROVA) < 0,05. El umbral sale entero del dato de MIROVA, ninguna
  constante elegida (A115). A cobertura completa eso es publicar en 20 pasadas o más en VIIRS 375 y
  en 6 o más en VIIRS 750 (`scipy.stats.binom`); el evaluador lo recalcula con el `n` procesado real.
  Límite declarado: `p_MIROVA` sale de pocos eventos (13 y 2) y la prueba lo trata como conocido; el
  evaluador informa además el intervalo de Clopper-Pearson de `p_MIROVA`.
- **G3, noches intactas**: nulo 2 sin diferencias.
- Veredicto: G1, G2 y G3 → **ADOPTAR** (con R2 por píxel y verificador independiente antes del flip,
  reglas S33 y A45; y con el frontend corregido, sección 8). G1 y G3 sin G2 → **DECIDE NICOLÁS** con
  M4: cuántas alertas protegidas recupera contra cuántas publicaciones agrega en negativos diurnos
  limpios. La tasa de cambio entre una alerta protegida recuperada y una publicación de más no sale
  de los datos (el criterio de victoria dice que las protegidas no se pueden perder y que bajo 1 MW
  una pérdida y una publicación de más pesan igual, pero no cuánto vale una protegida contra una
  publicación) y no se inventa acá (A115). M5 acompaña la cuenta como contexto, nunca como vara.
- Cualquier mejora de más de 30 % en una métrica exige auditoría independiente antes de aceptarla
  (regla de skills del proyecto).

## 7. Qué falta antes de poder despachar (candado)

1. **Workflow propio** `.github/workflows/reproc-s151-ab-diurno.yml`, con:
   - grupo de concurrencia **propio** `s151-ab-diurno` (`cancel-in-progress: false`). POR QUÉ:
     GitHub guarda **un solo run pendiente por grupo**; un despacho nuevo en el grupo
     `s146-ab-sin-test1` (el workflow `reproc-s146-ab-sin-test1.yml`) **desplazaría** la ventana
     pendiente del A/B de F/K. Por eso este A/B no reusa ese workflow ni su grupo, y tampoco entra al
     grupo `push-main` (no pushea a main). Es el mismo patrón que la caja (D-8, grupo `s151-ab-caja`,
     #818).
   - `max-parallel: 3`. POR QUÉ: el tope es de 20 jobs concurrentes; con el NRT (8) y el A/B de F/K (6)
     corriendo a la vez quedan 6, y 3 deja margen. Mejor todavía: despachar recién cuando la ventana
     de F/K haya terminado, para no repartir la cuota de NASA entre tres corridas.
   - candado `preregistro_aprobado == 'si'` en los jobs (patrón de `reproc-s146-ab-sin-test1.yml`).
   - autenticación **sólo** con `EARTHDATA_TOKEN`, fallando al instante si viene vacío (A71); el
     usuario y la clave de los secretos están vencidos y su reintento bloquea la cuenta.
   - la línea `FLAGS_BRAZO` del log con `ENABLE_DAYTIME_VIIRS`, para comprobar desde el artefacto qué
     leyó cada brazo (A89: leído de `pipeline.profile`, nunca del YAML).
   - `run_pipeline.py` **sin** `--no-night-filter`, y con el log completo de gránulos buscados,
     bajados y procesados (lo necesita la cobertura diurna, nulo 4).
   - `timeout >= 1,3 ×` la duración esperada (A15). El brazo diurno baja y procesa del orden del doble
     de gránulos VIIRS que el control; una ventana de 18 a 20 días por job puede acercarse al tope de
     6 h. Si el job corto de W1 (Láscar, 2 jobs) tarda más de 1,5 h, partir W2 a W6 en mitades.
   - salidas por artefacto y por rama propia (`s151-ab-diurno/<run_id>`), nunca a main.
2. **Perfiles de brazo** de la sección 2, con `data_subdir` propio.
3. **Evaluador diurno** (`experiments/_s151_ab_diurno/evaluar.py`), con sus controles corridos en
   verde antes del primer despacho: el nulo barajado del punto 5.5, la clasificación de cobertura del
   punto 5.4, el control contra sí mismo (debe dar M2 = M3 = 0 y nulo 2 sin diferencias) y un caso
   sintético que debe fallar. OJO (A118): el evaluador no puede filtrar la referencia con
   `es_pasada_diurna_descartada` bajo el perfil operacional, porque esa función sigue al flag y con el
   flag apagado tira justamente las pasadas diurnas que se quieren medir; y M5 no puede calcularse
   bajo el perfil del brazo diurno (§4). Etiqueta día y noche por elevación solar explícita.
4. **Token vigente** en los secretos (se rota cada 50 días).
5. **Aprobación de Nicolás** de este pre-registro y de su verificador con contexto limpio.

## 8. Lo que este A/B no decide

- **El frontend asume que toda pasada es nocturna** (`frontend/index.html` l. 451, el texto «El día»
  del panel de ayuda, y l. 1627 a 1670, el estado de frescura con el «hueco diurno»). No pesa
  mientras el flag esté apagado, pero hay que corregirlo **antes de cualquier flip**; este A/B no lo
  mide ni lo cambia.
- La rama diurna de MODIS: tiene flag propio y dos defectos latentes anotados en D27 (no rebinda el
  C2 de los Tests 2 y 3, y su flag no abre `fetch.py` ni `run_pipeline.py`).
- Si una alerta diurna es calor o Sol: vara del perfil `experimental` (README del estudio, §6).
- Los caminos que de día quedan como de noche porque el paper no da número (Test 1 integrado,
  compuerta de D22, magnitud diurna, tope D9, filtros «unsuitable», consistencia TIR):
  `pipeline/diurno.py`, PREGUNTAS. Si el A/B sale saturado por el Test 1, la pregunta siguiente es
  esa, no los umbrales de la Tabla 1.
