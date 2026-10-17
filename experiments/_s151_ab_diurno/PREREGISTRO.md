# Pre-registro del A/B diurno de VIIRS (D-10, issue #813)

Estado: **completo, espera el verificador con contexto limpio y la aprobación de Nicolás** (2026-10-15).
El workflow, los dos perfiles de brazo y el evaluador con su autoprueba existen (sección 7, todo en
verde); faltan el token vigente y el «si» del candado. El criterio (secciones 4 a 6) **no cambió**
respecto del borrador revisado tras el verificador del PR #821: lo que la implementación dejó como duda
está en la sección 9, como pregunta, sin arreglarlo a escondidas. Este documento fija qué se mide y con
qué vara ANTES de mirar un solo dato del A/B. Todo número de acá sale de
`experiments/_s151_ab_diurno/sustrato.py` (salida en `sustrato_salida.txt` y `sustrato.json`) o del
estudio `experiments/_s151_alertas_diurnas/`; ninguno se transcribe a mano de memoria.

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

| brazo | perfil | diferencia con `mirova_equivalent` |
|---|---|---|
| control | `pipeline/profiles/_s151_ab_diurno_control.yaml` | ninguna (sólo `data_subdir` propio, A47) |
| diurno | `pipeline/profiles/_s151_ab_diurno_on.yaml` | `enable_daytime_viirs: true` (sección `paths:`, de donde la lee `pipeline/profile.py`, A89) y nada más |

El brazo diurno corre **sin** `--no-night-filter`: lo que se prueba es que el flag abre por sí solo
las cinco compuertas (A118; en S92 el A/B diurno de MODIS abrió una y midió cero).

Comprobado con `pipeline.profile` en un proceso limpio por perfil, no con el YAML
(`comprobar_perfiles.py`, salida en `comprobar_perfiles_salida.txt`): `ENABLE_DAYTIME_VIIRS` y
`diurno.flag_viirs_diurno()` dan True sólo en el brazo diurno; el filtro nocturno de `fetch.py` y de
`run_pipeline.py` (`diurno.aplica_filtro_nocturno`) se abre para VIIRS 375 y 750 y no para MODIS; la
regla de store deja de descartar la pasada diurna de Láscar del 2026-06-15 17:24 sólo en VIIRS; y cada
brazo difiere de producción en todas las constantes de `pipeline.profile` sólo en `PROFILE_NAME`,
`DATA_SUBDIR` y, el diurno, `ENABLE_DAYTIME_VIIRS`.

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
2. ⚠️ **Precisado por las desviaciones D1 y D2 (§11)**: «idénticos campo a campo» se lee hoy como
   «cada par nocturno clasificado por `unir_intentos.comparar` más el predicado del tablero, sin
   ningún par `distinto`»; `orden`, `borde` y `hotspot_escena` se admiten y se informan aparte. Texto
   original conservado:
   **Las noches no cambian**: los records nocturnos de los dos brazos tienen que ser idénticos campo a
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
- **G3, noches intactas**: nulo 2 sin diferencias (desde D2, §11: ningún par nocturno `distinto`).
- Veredicto: G1, G2 y G3 → **ADOPTAR** (con R2 por píxel y verificador independiente antes del flip,
  reglas S33 y A45; y con el frontend corregido, sección 8). G1 y G3 sin G2 → **DECIDE NICOLÁS** con
  M4: cuántas alertas protegidas recupera contra cuántas publicaciones agrega en negativos diurnos
  limpios. La tasa de cambio entre una alerta protegida recuperada y una publicación de más no sale
  de los datos (el criterio de victoria dice que las protegidas no se pueden perder y que bajo 1 MW
  una pérdida y una publicación de más pesan igual, pero no cuánto vale una protegida contra una
  publicación) y no se inventa acá (A115). M5 acompaña la cuenta como contexto, nunca como vara.
- Cualquier mejora de más de 30 % en una métrica exige auditoría independiente antes de aceptarla
  (regla de skills del proyecto).

## 7. Requisitos antes de despachar (candado) y su estado

Estado al 2026-10-15: los puntos 1 a 3 están hechos (cada uno con su línea **Hecho**); quedan el 4 y el 5.
El texto de cada requisito es el del borrador y se conserva.

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

   **Hecho.** Copia de `reproc-s151-ab-caja.yml` con lo mínimo cambiado: grupo `s151-ab-diurno`,
   `max-parallel: 3`, candado, sólo `EARTHDATA_TOKEN` con falla inmediata si viene vacío, `"on":` entre
   comillas, artefactos `s151diurno-*`, rama `s151-ab-diurno/<run_id>` y salidas en
   `experiments/_s151_ab_diurno/salidas/<run_id>/`. La línea `FLAGS_BRAZO` trae `ENABLE_DAYTIME_VIIRS` y
   `ENABLE_DAYTIME_MODIS`; el paso «El brazo LEE lo que declara» además falla si el flag diurno no es el
   que corresponde al nombre del brazo. `run_pipeline.py` corre sin `--no-night-filter` y con
   `nighttime_only` en su valor por defecto (True): es `diurno.aplica_filtro_nocturno(True, plataforma)`
   el que abre VIIRS en `fetch.py` (filtro previo a la descarga) y en `run_pipeline.py` (salto del
   gránulo), así que el workflow no anula el flag. El log entero va al artefacto. Un cambio que no estaba
   en el borrador: el paso `recolectar` cuenta la cobertura con `contar_pasadas_noche.py` y no con
   `experiments/_s146_ab_sin_test1/contar_pasadas.py`, porque éste exige las mismas pasadas en los dos
   brazos y el brazo diurno tiene por diseño las de día (saldría siempre «despareja»). El nuevo compara
   SÓLO las noches, en las dos direcciones, y controla el día aparte (control sin día, brazo diurno con
   VIIRS diurno y sin MODIS diurno; nulos 1 y 3). `timeout-minutes` 330 por job y 300 por paso, como la
   caja; la regla de partir W2 a W6 si W1 tarda más de 1,5 h sigue en pie.
2. **Perfiles de brazo** de la sección 2, con `data_subdir` propio.

   **Hecho**, comprobado con `pipeline.profile` (sección 2).
3. **Evaluador diurno** (`experiments/_s151_ab_diurno/evaluar.py`), con sus controles corridos en
   verde antes del primer despacho: el nulo barajado del punto 5.5, la clasificación de cobertura del
   punto 5.4, el control contra sí mismo (debe dar M2 = M3 = 0 y nulo 2 sin diferencias) y un caso
   sintético que debe fallar. OJO (A118): el evaluador no puede filtrar la referencia con
   `es_pasada_diurna_descartada` bajo el perfil operacional, porque esa función sigue al flag y con el
   flag apagado tira justamente las pasadas diurnas que se quieren medir; y M5 no puede calcularse
   bajo el perfil del brazo diurno (§4). Etiqueta día y noche por elevación solar explícita.

   **Hecho**, con el nombre `evaluar_diurno.py` (no `evaluar.py`) y su autoprueba
   `probar_evaluar_diurno.py` (salida en `probar_salida.txt`: **51 de 51** comprobaciones en verde tras
   los arreglos del verificador del PR #822; eran 36 y dejaban pasar 4 de 7 mutaciones, ver §9).
   Cómo cumple lo pedido:
   - las poblaciones salen de `sustrato.universo`, la misma función que contó el sustrato (se extrajo
     de `sustrato.main` sin cambiar su salida, comprobado con `diff` contra `sustrato_salida.txt`), y el
     evaluador exige que la referencia que lee reproduzca `sustrato.json` ventana por ventana;
   - la referencia se indexa con `banco_paridad.indexar_referencia` con la rama diurna encendida en
     `pipeline.profile` SÓLO mientras indexa, y el evaluador mide las dos caras de la trampa A118: con el
     flag encendido el índice ve las 5.095 pasadas del universo, con el flag apagado ve cero filas VIIRS
     diurnas (caso 12 de la autoprueba: 0 de 1.201 en W2);
   - «publica» es el predicado del dashboard ejecutado con node (`banco_paridad.correr_node`, A97);
     día y noche de cada record por `pipeline.diurno.pasada_es_diurna` (elevación solar explícita);
   - M5 se calcula sobre los records nocturnos del CONTROL, etiquetados con el flag apagado;
   - el nulo barajado (5.5) se muestrea con la hipergeométrica por estrato volcán × sensor, que es
     exactamente el barajado de etiquetas (ver el docstring del evaluador), y sus dos controles corren en
     cada evaluación (ver §9, pregunta 2);
   - la cobertura diurna (5.4) clasifica cada positivo y cada pasada diurna de la tabla en no procesada,
     procesada sin publicar o publicada, con el motivo del log cuando lo hay;
   - el control contra sí mismo (caso 7) da cero publicaciones diurnas, noches idénticas e INDECIDIBLE
     por el nulo 1; el caso que debe fallar por G2 (caso 2) falla;
   - el cableado se prueba desde el log: la línea `FLAGS_BRAZO` y la ausencia, en el brazo diurno, de
     las dos huellas de una compuerta cerrada para VIIRS («SKIP daytime» de `run_pipeline.py` y
     «kept N of M granules (night filter)» de `fetch.py`).
   La regla D-9 de alertas mínimas decide con «original» (este pre-registro no dice otra cosa). En
   `main` todavía no existe `clase_mirova.aplicar_regla_minimas` (PR #820 sin mergear): la sección 12
   del evaluador queda **PENDIENTE** y, cuando el PR se mergee, informa SN y SE aparte sin tocar lo que
   decide (caso 13 de la autoprueba, con una regla neutra inyectada).
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

## 9. Preguntas para el verificador (huecos que dejó la implementación, sin arreglar a escondidas)

Cada una dice qué hace hoy el evaluador. Ninguna cambia un umbral de la sección 6.

**Actualización tras el verificador con contexto limpio del PR #822** (veredicto PARCIAL: perfiles, flag,
workflow, G1 y G2 confirmados; el control del nulo no podía fallar y la autoprueba dejaba pasar 4 de 7
mutaciones). Se marcan abajo los puntos que cambiaron; el texto anterior queda como historia. Además:
- **Nulo 1 por sensor** (§5.1): el evaluador y `contar_pasadas_noche.py` aceptaban VIIRS 375 **o** VIIRS
  750, así que una compuerta de 750 cerrada pasaba sin aviso. Hoy se exige cada sensor que tiene pasadas
  diurnas de la tabla en la ventana (los dos en las seis; caso 19 de la autoprueba).
- **Mutaciones**: `mutar_evaluador.py` (equivalente en el repo del `mutar.py` del verificador, mismas
  siete mutaciones) corre la autoprueba contra el evaluador roto a propósito; salida en
  `mutaciones_salida.txt`. Los casos 15 a 21 de la autoprueba nacieron para atrapar las cuatro que
  sobrevivían.

1. **G3 compara también sin `first_processed_utc`.** El nulo 2 excluye `updated`, `processed_utc` y
   `regimen`; los records traen además `first_processed_utc`, la hora en que store guardó el record por
   primera vez, que difiere siempre entre dos jobs. Con la lista literal, G3 fallaría en toda corrida
   real. El evaluador lo excluye (`VOLATILES`) y lo imprime. ¿Hay otro campo volátil que deba entrar?
   **Confirmado por el verificador, con un faltante ya resuelto:** `granule` trae la hora de producción
   de NASA; si cambia entre los dos jobs (gránulo reprocesado) G3 lo llamaba «defecto del cableado». Hoy
   cuenta como cobertura, igual que la versión de producto y que en `contar_pasadas_noche.py` (caso 18).
   El caso 17 comprueba que `processed_utc` y `first_processed_utc` distintos no hacen fallar G3.
2. ⚠️ **Rebajado por el verificador del PR #822: el control descrito abajo era tautológico.** Comparaba
   muestras de `nulo_barajado` contra el p95 de esa misma función, nunca tocaba el código que calcula D,
   y con el nulo roto a propósito (×0,3 o corrido en −0,5) seguía dando «OK». **Hoy** el control (a)
   permuta de verdad las etiquetas pos/neg dentro de cada estrato sobre la tabla de clases del run,
   calcula D con la misma función que usa G1 (`d_de`), 1.000 veces, y cuenta cuántas superan el p95 de
   G1. Esa fracción tiene que coincidir, dentro de 3 errores estándar, con la que el propio nulo pone
   sobre su p95: es 5 % cuando D es continuo y menos cuando D toma pocos valores y hay empates en el p95
   (con un 5 % fijo, un brazo con pocas publicaciones haría fallar el control sin que el nulo esté mal;
   en el caso 1 la del nulo es 3,0 % y la de las permutaciones 3,2 %). Con el nulo ×0,3 la fracción sube
   a 0,51 y con el nulo corrido a 1,00: el control FALLA, que es lo que tiene que hacer (caso 21). La comparación «D supera el p95» se
   lee con una holgura de 1e-12 (`EPS_D`), igualdad numérica y no umbral: cuando el nulo es degenerado
   (un brazo que publica todo un estrato y nada en los demás, caso 15) cada muestra del nulo ES el D
   observado. Texto anterior, como historia:
   **El control del nulo barajado.** §5.5 pide que, con etiquetas ya barajadas, «el percentil 95 quede
   alrededor de cero». Con estratos volcán × sensor de tasas distintas el centro del nulo **no** es
   cero (en el caso 1 de la autoprueba la mediana del nulo W2 a W6 es +0,025; corregir eso es para lo
   que se estratifica). El evaluador controla otra cosa, que es la propiedad que importa: 1.000 brazos
   que publican al azar dentro de cada estrato (la misma cuenta por estrato que el brazo real) tienen
   que pasar G1 en no más de 5 % + 3 errores estándar (7,1 %; tolerancia elegida), y un brazo que
   publica sólo en los positivos tiene que pasarlo. ¿Es aceptable ese reemplazo?
3. **G2 y el veredicto por sensor.** El flag es uno para VIIRS 375 y 750, así que no se puede adoptar
   un sensor sin el otro. El evaluador pide G2 en los dos para ADOPTAR; si falla en uno, el veredicto es
   «DECIDE NICOLAS CON M4». ¿Correcto? **Confirmado por el verificador**; el caso 16 (G2 cumple en 375 y
   falla en 750) lo fija en la autoprueba.
4. **Qué hace G3 cuando falla.** §5.2 dice que una diferencia nocturna «se resuelve antes de mirar M1 a
   M4». El evaluador da INDECIDIBLE y separa: pasadas que faltan o sobran, o versión de producto
   distinta, «COBERTURA NOCTURNA DESPAREJA (repetir el job)»; mismos records con campos distintos,
   «FALLA (defecto del cableado)». Desde el verificador del PR #822 el gránulo distinto también cuenta
   como cobertura (punto 1).
5. **La referencia no está congelada.** El evaluador lee por defecto el snapshot del repo, que
   `sync-mirova-csv.yml` actualiza cada hora, y exige que reproduzca `sustrato.json` ventana por
   ventana (positivos, negativos, pasadas y alertas por sensor, los 37 y la parsimonia 13/2.511 y
   2/2.483); si no, INDECIDIBLE. Hoy la reproduce (caso 1). Los sha256 (fin de línea LF) de los cuatro
   archivos con que se contó, para recuperarlos con `git show <commit>:<ruta>` y pasarlos con `--cons`,
   `--ocr`, `--respaldo` y `--historico` si el snapshot cambia:
   - `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv` 9f8542374de2ea5051349938da7c6598500561c4bd0013a81a364332106c2353
   - `data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv` a2e8cb67df34ed4899418cefacea78594e7abfa33f829e7251e29f66f760c11b
   - `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado_respaldo_20260408.csv` 183aff7f38c6ca9ef93c8e0951f8190dd12be2690d54dbacb7d7acabaaa93568
   - `data/mirova_reference/union_historica/consolidado_filas_perdidas.csv` 5a68bd7fb4c386044422934239c5c857e2f00488a8c6ea21e1a754f7966e3abd

   ¿Se congela antes de despachar (patrón `experiments/_s151_prereg_fk_11/congelar.py`)? Congelar desde
   el remoto de Mirova-v1 podría no reproducir `sustrato.json` y obligaría a recontar el sustrato.

   **Commits de recuperación, comprobados en esta sesión** (`git log` de cada archivo y sha256 LF de
   `git show <commit>:<ruta>`, los cuatro iguales a los de arriba): el OCR en **7b74435** (sync del
   2026-10-14 22:17 UTC); el consolidado y la capa histórica en **f3b4142** (auditoría semanal del
   2026-10-14 11:53 UTC); el respaldo del 2026-04-08 en **068773f** (#653, no cambió desde entonces).
   **Y el control ya no compara sólo conteos** (verificador, hueco 4): `sustrato.json` guarda ahora, por
   ventana y sensor, la huella sha256 de la lista ordenada de negativos, de pasadas de la tabla y de
   pasadas con alerta (`sustrato.huella`), y el evaluador exige las mismas huellas: el mismo conteo con
   otras pasadas también es otra referencia. Agregar las huellas no cambió ninguna otra cifra de
   `sustrato.json` ni de `sustrato_salida.txt` (comprobado campo a campo).
6. ⚠️ **Cerrado tras el verificador del PR #822, que lo dio por no aceptable.** Hoy la misma regla del 10 %
   de §5.4 se aplica también a las pasadas de la tabla, por ventana y por sensor, ANTES de G2: si más del
   10 % de las pasadas diurnas de la tabla de un sensor en una ventana quedan sin procesar, la ventana se
   repite, y si ya se repitió sale del veredicto como cobertura insuficiente (caso 20). **Esto extiende
   el alcance de la regla de §5.4 (de los positivos a la tabla) sin tocar su umbral**; se dice acá para
   que no pase por un detalle de implementación. Texto anterior, como historia:
   **El 10 % de §5.4 sólo mira positivos.** Las pasadas de la tabla no procesadas salen de los
   denominadores de M2 y M3 (y del `n` de G2) sin regla de repetición. Si los cortes de NASA no son al
   azar (por ejemplo, un día entero), M2 y G2 se miden sobre una muestra sesgada. Hoy sólo se informa.
7. **«Depende del OCR» y G2.** Si G1 pasa sólo con W2, el veredicto es «DEPENDE DEL OCR, DECIDE
   NICOLAS» y se imprime G2 por sensor al lado; G2 no lo cambia.
8. **Avisos que no deciden**: q_neg de 0,80 o más se marca como banda de saturación (A114, 80 a 92 %),
   y un M1 de 0,30 o más exige auditoría independiente (la mejora es contra un M1 de 0 en el control).
   Los dos son informativos; ¿alguno debería decidir?
9. **La regla D-9 en SN y SE recalcula `p_MIROVA`** sobre la referencia modificada (en SN una alerta
   mínima pasa a RUTINA y sale del numerador). Es sólo informativo; la regla original usa 13/2.511 y
   2/2.483 fijos.
10. **No procesada es «sin record a 120 s»**, sin distinguir búsqueda vacía, descarga fallida o un
    procesador que devolvió None (por ejemplo, el volcán fuera del barrido). El log no nombra cada
    gránulo procesado, así que el motivo sólo aparece cuando hay una línea «SKIP daytime», «ERROR
    processing» o «No geolocation match»; el resto sale como «sin rastro en el log».
11. **Pareo por volcán, sensor (375 o 750) y 120 s, no por plataforma.** Igual que `banco_paridad`.
    Si dos plataformas del mismo sensor pasaran a menos de 120 s una de otra, se toma el record más
    cercano.

## 10. Comandos de despacho y de evaluación

El workflow sólo se puede despachar desde `main` (limitación de `workflow_dispatch`), así que primero
se mergea este PR. **Una ventana por despacho, y la siguiente recién cuando la anterior empezó a
correr**: el grupo `s151-ab-diurno` guarda un solo run pendiente y un tercer despacho desplazaría al
que espera. Mejor todavía, despachar cuando el A/B de F/K haya terminado (§7.1).

**Costo estimado, SIN VERIFICAR** (verificador del PR #822, de una sola corrida comparable): con ~3,2
minutos de runner por día y brazo (run 38679191229) y el brazo diurno estimado al doble del control, las
seis ventanas (W1 de 20 días con Láscar; W2 a W6 con 11 volcanes y 18, 12, 19, 20 y 14 días) suman del
orden de **130 a 150 h de runner** y **~2 días de reloj con `max-parallel: 3`**. No se midió el brazo
diurno: el job corto de W1 es el que lo mide, y si tarda más de 1,5 h se parten W2 a W6 (§7.1).

```
# W1 primero: job corto (Láscar, 2 jobs) para medir la duración del brazo diurno.
gh workflow run reproc-s151-ab-diurno.yml --ref main -f preregistro_aprobado=si -f start=2026-03-01 -f end=2026-03-20 -f vols='["Lascar"]'

# W2 a W6, 11 Tier A (22 jobs cada una). Si W1 tardó más de 1,5 h, partir cada una en dos mitades.
V='["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]'
gh workflow run reproc-s151-ab-diurno.yml --ref main -f preregistro_aprobado=si -f start=2026-06-13 -f end=2026-06-30 -f vols="$V"
gh workflow run reproc-s151-ab-diurno.yml --ref main -f preregistro_aprobado=si -f start=2026-07-20 -f end=2026-07-31 -f vols="$V"
gh workflow run reproc-s151-ab-diurno.yml --ref main -f preregistro_aprobado=si -f start=2026-08-13 -f end=2026-08-31 -f vols="$V"
gh workflow run reproc-s151-ab-diurno.yml --ref main -f preregistro_aprobado=si -f start=2026-09-01 -f end=2026-09-20 -f vols="$V"
gh workflow run reproc-s151-ab-diurno.yml --ref main -f preregistro_aprobado=si -f start=2026-10-01 -f end=2026-10-14 -f vols="$V"
```

Antes de mirar cualquier resultado: leer `cobertura.txt` de cada corrida (paso `recolectar`, A108). Si
falta una noche o un volcán, repetir ese job con la lista corta de `vols` y el mismo código.

Evaluación, con las seis corridas juntas (cada salida vive en la rama `s151-ab-diurno/<run_id>`, bajo
`experiments/_s151_ab_diurno/salidas/<run_id>/`):

```
python experiments/_s151_ab_diurno/evaluar_diurno.py \
  --raiz experiments/_s151_ab_diurno/salidas/<run_W1> --raiz experiments/_s151_ab_diurno/salidas/<run_W2> \
  --raiz experiments/_s151_ab_diurno/salidas/<run_W3> --raiz experiments/_s151_ab_diurno/salidas/<run_W4> \
  --raiz experiments/_s151_ab_diurno/salidas/<run_W5> --raiz experiments/_s151_ab_diurno/salidas/<run_W6> \
  --out experiments/_s151_ab_diurno/resultado.json > experiments/_s151_ab_diurno/resultado_salida.txt
```

Una repetición por cobertura (§5.4) se agrega como otra `--raiz` DESPUÉS de la original (si una pasada
está en las dos, gana la última). Si la ventana ya se repitió y siguen faltando positivos, se agrega
`--repetidas W<n>` para que salga del veredicto como cobertura insuficiente. Antes de la
evaluación real, volver a correr `python experiments/_s151_ab_diurno/probar_evaluar_diurno.py`: tiene
que seguir dando todas sus comprobaciones en verde sobre el mismo código.

## 11. Desviaciones registradas DESPUÉS de ver datos

**D1 (2026-10-16, vuelta 70 del loop): tolerancia numérica en G3.** W1 (run 38723828037, sólo informa) dio G3 FALLA:
`diag_mu_deti` (179 noches) y `diag_sd_deti` (170) distintos entre control y brazo diurno, y ningún otro campo, ni
anidado. Mecanismo reproducido por un verificador con contexto limpio: `np.polyfit` pasa por LAPACK de OpenBLAS, que
elige el kernel por CPU, y el último bit de la regresión del ETI cambia entre runners; MODIS también difiere y no lee
`ENABLE_DAYTIME_VIIRS`. Por eso G3 compara floats con tolerancia relativa 1e-9 más un piso absoluto 1e-14 (μ del dETI
es casi cero: la diferencia relativa a μ llegó a 1,4e-11, pero contra σ del dETI no pasó de 5,4e-14; el umbral físico
más fino, C1, es 3e-3), y enteros, bools, None y strings exactos, recursivo en listas y dicts. Es un cambio del
instrumento hecho después de ver datos; el motivo es mecánico y no depende del resultado (W1 sigue INDECIDIBLE).
Lo fijan la autoprueba (casos 22 a 22g, 57 de 57) y las mutaciones: 8 de 8 sobre la comparación nueva y 7 de 7 sobre
las de siempre. Informe del verificador: `C:\Users\nmend\AppData\Local\Temp\claude\verif_g3\VERIFICADOR.md`.

**D2 (2026-10-17, rama `loop/diurno-g3-comparar`): G3 por par, con la regla de `unir_intentos`.** Motivo mecánico,
no del resultado. (1) Los brazos corren en runners distintos y MODIS no es determinista bit a bit: el recorte top-100
de `np.argsort(-per_pixel_vrp_mw)` (`pipeline/process_modis.py:1085-1099`) desempata distinto según la CPU, lo que
cambia el orden y a veces el conjunto de `anomaly_pixels`, y a veces el hotspot de escena, y con él el rescate por
cúmulo (`pipeline/store.py:390-422`) y el `vrp_mw` del record (D-16). (2) Las ventanas se arman uniendo intentos
(D-13) y el G3, que comparaba el record crudo con las listas por posición, dependía del orden de la unión: en W2a
Copahue 2026-06-18 07:30, 9 campos distintos con el orden (2,1) y ninguno con (1,2) (verificador del PR #843,
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s151_unir_intentos_verif\VERIFICADOR_843.md`
§3, sin versionar, que recomienda esta regla). Medido sobre W2 (W2a run 38853230521 unido con `unir_intentos.py` en
los dos órdenes, más W2b run 38853273752): el G3 viejo da FALLA en los dos órdenes, con campos sólo de las listas de
píxeles y sus derivados (hotspot, ancla final, geometría de visión, `vrp_mir_mw`, `discarded_n_pixels`) y, en el
orden (2,1), además el rescate (`final_hotspot_source`, `discarded_reason`, `vrp_mw`, en 1 noche). Regla nueva: cada par nocturno control/diurno con
el mismo gránulo y versión se clasifica con `unir_intentos.comparar` (sin VOLATILES; misma tolerancia que D1, y el
evaluador exige al importar que las dos tolerancias y las dos listas de campos de proceso coincidan); los pares
`borde` y `hotspot_escena` pasan además por el predicado del tablero con node (`unir_intentos._predicado`, por
volcán), y si el tablero da distinto, o no se pudo correr, el par es `distinto`. G3 FALLA con cualquier `distinto`;
`orden`, `borde` y `hotspot_escena` se informan aparte, par por par. La cobertura (A108) no cambia. Resultado sobre
W2, mismo veredicto en los dos órdenes, CUMPLE con 0 distintos sobre 2.154 pares nocturnos (orden (1,2): igual
1.108, tolerancia 1.017, orden 15, borde 13, hotspot_escena 1; orden (2,1): 909, 1.216, 17, 10 y 2). Las
categorías cambian con el orden porque cambia qué intento conservó la unión; el veredicto no. Salidas en
`C:\Users\nmend\AppData\Local\Temp\claude\g3_s151\g3_w2_{12,21}.{txt,json}`, con `g3_solo.py` (corre sólo el G3, sin
mirar G1 ni G2). Lo fijan la autoprueba (casos 23 a 25: 67 de 67), `tests/test_g3_diurno_comparar_s151.py` y seis
mutaciones `g3_*` de `mutar_evaluador.py`, una por categoría admitida, la que admite `distinto` y la que se salta
el predicado (13 de 13 atrapadas, `mutaciones_salida.txt`). En la primera corrida cuatro `g3_*` daban «atrapada» sólo
porque el evaluador mutado se caía (KeyError), no por el veredicto: se arregló el conteo y desde ahora
`mutar_evaluador.py` informa una caída como «SE CAE» y no la cuenta como atrapada. La mutación
`volatiles` la para desde ahora la guarda de coherencia al importar (el caso 17 ya no puede verla, porque `comparar`
excluye sus campos de proceso por su cuenta). Lo que esta regla hereda de `comparar` y no acota (VERIFICADOR_843.md §4,
LAX1 a LAX7) sigue sin acotar: el `vrp_mw` y la distancia del hotspot del lado no rescatado.

**Nota de procedimiento (W1):** cada intento del brazo diurno perdió pasadas nocturnas distintas por descarga. Se
unieron los dos intentos con `unir_intentos.py` (se niega si un gránulo común difiere; 325 comunes idénticos), lo que
equivale a pasar las dos raíces como dice el párrafo de arriba. La evaluación de W1 usó `--repetidas W1` sin necesidad
(no faltaban positivos); como W1 sólo informa, no cambia nada, y en W2 a W6 no se usa salvo en el caso que describe
este documento.
