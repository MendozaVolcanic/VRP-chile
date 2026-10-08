# Verificador del pre-registro S150 de Nevados de Chillán

Verificador con contexto limpio. Objeto: `experiments/_s150_ndc/PREREGISTRO_NDC.md`, rama `s150-ndc`, commit
`fb4c47cdf` (comprobado con `git branch --show-current` y `git log -1`). No modifiqué nada del repo salvo este
informe. Los scripts propios están en el scratchpad de la sesión (`recuento.py`, `control_positivo.py`,
`simular_e.py`, `leer_tabla.py`); sus salidas se citan abajo.

## Veredicto

**No se puede despachar tal cual.** El pre-registro está bien armado en lo mecánico (los perfiles difieren sólo
en lo declarado, el flag llega al tablero, la referencia está congelada con sha), pero tiene dos defectos de
diseño que hacen que un resultado verde no signifique lo que dice:

1. el brazo E (y KE) **no puede fallar** sus predicciones salvo por un cableado roto, y su costo en falsos, que
   ya se puede medir hoy sin correr nada, es enorme (H1);
2. P4 atribuye a la banda 22 una pérdida que en K la causa la etiqueta, no la banda (H2).

Además faltan el evaluador de P1 a P8 (H4), el sustrato está contado con otra definición que la del evaluador
(H3), el final de la ventana mezcla productos NRT y estándar entre brazos (H5), y el tope D9 de 5 MW, armado en
casi toda la erupción, no aparece en ninguna parte del pre-registro (H14, addendum con los datos del auditor B
verificados). Con las correcciones de H1 a H6 y H14 el resto son cambios menores.

## Lo que se verificó y está bien

- `diff_perfiles_ndc.py` reproduce su salida byte a byte (`diff` vacío). Corrí además el par que faltaba,
  C0 contra B: difieren sólo en `ENABLE_TEST1_PATH` (y directorio).
- `sustrato_ndc.py` reproduce su salida byte a byte. La clave de pasada única evita el doble conteo de S149 y el
  filtro `"chill"` capta la única variante del nombre en los dos CSV (`Nevados de Chillan`, 431 filas CONS y 22
  OCR). Los sha256 del `MANIFIESTO.json` coinciden con los archivos.
- El flag se lee bien: `pipeline/profile.py:636` lo toma de la raíz del YAML y resuelve `True` en E y KE (A89 no
  aplica).
- **A118, cableado del flag**: `derivar_distance_class` se llama en los dos sitios donde se fija la etiqueta MODIS
  (`pipeline/process_modis.py:1328` y `:1495`, la segunda tras el ancla honesta). Aguas abajo, `store.py` sólo
  reescribe `distance_class` en tres lugares: el rescate F47 (l. 385, fuerza `summit`), la regla D de vent
  (l. 446, fuerza `summit`) y el guard A46 (l. 480 a 485, pasa a `far` sólo si el cúmulo está FUERA del inner).
  Ninguno puede deshacer un `summit` que el flag produjo con el cúmulo dentro del inner. El tablero
  (`isSummitDetection`, `frontend/index.html:1480`) lee el mismo campo.
- **Control positivo llevado hasta el predicado**: sobre el record de producción de 2026-10-01 08:35
  (`pc` a 0,883 km, 2,293 MW, `final_hotspot` a 32,84 km) el predicado de node da `PUB 0` con la etiqueta de
  producción y `PUB 1` con la del flag (`control_positivo.py`). O sea que el §4.3 vale también para la
  publicación, no sólo para la etiqueta. Ver H7 para por qué igual no basta.
- Ventana: no cruza #535, empieza después del 2026-06-13 (A119), la tabla y el OCR deciden. Correcto.

## Hallazgos

### H1. El brazo E no puede fallar, y su costo ya está medido: publica casi todo MODIS en reposo. Gravedad 4

**Evidencia.**
- P3 tiene dos cláusulas. La primera ("E publica 08:35") es el control 3 repetido. La segunda ("no publica
  menos alertas MODIS que C0") se cumple **por construcción**: con el flag, `derivar_distance_class` sólo puede
  pasar `far` a `summit` cuando el cúmulo está dentro del inner, y el caso inverso (`summit` a `far` con el
  cúmulo fuera) ya lo hace el guard A46 de `store.py:480` en C0. La única manera de que E publique menos es el
  no determinismo. Lo mismo vale para KE contra K. Con eso, el veredicto "SIGUE A 11 VOLCANES" de E está
  decidido antes de correr, salvo que el cableado esté roto.
- E es una función pura de los records de C0 (el docstring de `process_modis.py:300` y el test
  `test_distance_class_no_se_lee_aguas_arriba_en_modis` garantizan que la etiqueta no se lee aguas arriba), así
  que su efecto se mide hoy sobre producción. `simular_e.py` reetiqueta los MODIS de
  `data/mirova_equivalent/NevadosDeChillan.json` como lo haría E (flag más guard A46) y `armar_tabla.py` contra
  la referencia congelada da:

  | MODIS | n | publica C0 | publica E | de esas, 1 MW o más | en el tope de 5,00 MW |
  |---|---|---|---|---|---|
  | reposo, negativos limpios | 28 | 0 | **22** | 9 | 5 |
  | actividad, negativos limpios | 5 | 0 | 4 | 4 | 3 |
  | actividad, alertas de MIROVA | 3 | 1 | 2 | 2 | 0 |

  MIROVA publica 0 de esas 28 pasadas, y su tasa base de alerta MODIS es 0,5 % (`docs/AUDIT_S149.md:167`). El
  auditor B de esta misma sesión ya lo había medido (`experiments/_s150_audit/B/resumen_salida.txt`: con el flag
  MODIS publica 23 de 27 records de 09-20 a 10-02, 20 en RUTINA, 9 censurados en 5,00).
- Físicamente no cuadra: en reposo E publica MODIS de 1 a 5 MW (por ejemplo 2026-09-22 07:45, 5,00 MW) en
  noches en que VIIRS 375 ve 0,02 a 0,04 MW sobre el mismo cráter (misma tabla del auditor B). Es la cara b de
  A81 en NdC, el volcán donde S113 había clasificado las 73 noches como artefacto A69; esa clasificación quedó
  rebajada en S146, pero estos números no dependen de ella. El pre-registro no menciona nada de esto.

**Corrección.** (a) Medir E y KE offline sobre C0 y K y decidirlos con un criterio de costo **pre-registrado y
medido contra MIROVA** (A115), por ejemplo: vetado si publica en negativos limpios MODIS de reposo más que C0 más
lo que admite la tasa base de 0,5 % (con n = 28, cero pasadas extra). Con los números de hoy E queda vetado sin
correr. (b) Si igual se corren E y KE en Actions, declararlos sólo como **prueba de cableado** (ver H7), no como
candidatos. (c) Quitar de P3 la cláusula "no publica menos": no es una predicción.

### H2. P4 culpa a la banda 22 de una pérdida que en K causa la etiqueta. Gravedad 3

**Evidencia.** P4 exige que **K** publique las 3 alertas MODIS de 1 MW o más (2026-10-01 01:45, 2026-10-01 08:35
y 2026-10-05 07:50) y, si falla, concluye "la banda 22 no generaliza". Pero K no tiene el flag: su etiqueta sale
del píxel más caliente de la escena, igual que C0, B y J. En producción 08:35 se pierde exactamente por eso
(`final_hotspot` a 32,84 km, `far`). Si K la pierde por la misma razón, P4 falla y el veredicto atribuye a la
banda 22 un defecto de etiquetado que ningún brazo sin flag puede evitar.

**Corrección.** La cláusula "publica las 3" se exige sólo a KE (o a todos los brazos MODIS después de aplicarles
offline la misma reetiqueta, que es exacta por H1). La atribución a la banda 22 sale de J contra B y de K contra J,
contando sólo pasadas cuya etiqueta no esté `far` en el control. Escribir explícitamente qué pérdida se atribuye
a qué palanca.

### H3. El sustrato del §3 no está contado con la definición del evaluador. Gravedad 3

**Evidencia.** `sustrato_ndc.py` no filtra pasadas diurnas y cuenta las filas `FALSO_POSITIVO` como "listadas sin
alerta". El evaluador (`banco_paridad.indexar_referencia`, `es_pasada_diurna_descartada`) descarta las diurnas,
etiqueta las FP como `far_ref` y manda las RUTINA de noches con alerta a `sin_info`. Recuento con el cargador y el
filtro del evaluador (`recuento.py`):

| sensor | fase | alertas nocturnas (1 MW o más) | alertas diurnas | FP noche | RUTINA noche | RUTINA día |
|---|---|---|---|---|---|---|
| MODIS | reposo | 0 | 0 | 0 | 28 | 32 |
| MODIS | actividad | 4 (3) | 0 | 1 | 15 | 22 |
| VIIRS 375 | reposo | 3 (0) | 0 | 2 | 41 | 47 |
| VIIRS 375 | actividad | **20 (13)** | 1 | 0 | 17 | 30 |
| VIIRS 750 | reposo | 0 | 0 | 0 | 44 | 45 |
| VIIRS 750 | actividad | **13 (11)** | 1 | 0 | 20 | 26 |

Las "listadas sin alerta" del pre-registro (60/38, 91/47, 90/47) son casi el doble de lo evaluable. Las alertas de
2026-10-01 18:42 (VIIRS 375 2,53 MW, VIIRS 750 3,71 MW) son diurnas: ningún brazo las procesa (MIR sólo
nocturno). Y en actividad los negativos limpios son muy pocos (en producción: MODIS 5, VIIRS 375 6, VIIRS 750 6,
`leer_tabla.py`), porque casi todas las noches tienen alerta.

**Corrección.** Reemplazar la tabla del §3 por el recuento nocturno con el cargador del evaluador, y decir en P5,
P6 y P8 qué etiqueta usa cada una (`neg_limpio`, o `sin_info` con `rutina_pasada` y `noche_con_alerta_sensor`).
Corregir `sustrato_ndc.py` para que use `cargar_referencia_unificada` y `es_pasada_diurna_descartada`.

### H4. No existe el evaluador de P1 a P8. Gravedad 3

**Evidencia.** `evaluar_ventana.py` llama a `medir_predicciones.py`, que mide las predicciones de S149 (tasa en
negativos limpios contra 18 %, razón borde sobre nadir, recall con pérdidas de 0,5 MW o más, estrato de RUTINA,
C8b), un sensor por vez (`medir_predicciones.py:13`, `:39 a 50`). Ninguna de P1 a P8 de este pre-registro está
implementada: ni el umbral de 1 MW, ni la cadena de comparaciones, ni P5 por fase, ni P7 con `pc.vrp_mw` y
`f5_core_vrp_mw`, ni P8. Además `evaluar_ventana.py` compara un par por llamada (servirían seis llamadas, cada
una re-extrae el run), calcula el determinismo **agrupando los tres sensores** (`:87 a 90`) cuando el §4.2 lo
pide por sensor, y descarta el stderr de `armar_tabla.py` (`:60`), que es por donde sale el aviso A119.
`armar_tabla.py` sí maneja un solo volcán (`cargar_brazo` salta los JSON que faltan) y esta ventana; eso lo
comprobé corriéndolo sobre producción (208 pasadas).

**Corrección.** Escribir `medir_ndc.py` antes del despacho, sobre las tablas de `armar_tabla.py`, con P1 a P8
tal como quedan escritas, determinismo por sensor, y probarlo (a) contra producción como control y brazo (cero
pérdidas, cero cambios), (b) con una pérdida inyectada de 1 MW o más (tiene que vetar), (c) reproduciendo los
números del §1. Commitearlo junto con el pre-registro, como pidió el verificador de S149 (H5).

### H5. El final de la ventana mezcla productos NRT y estándar entre brazos. Gravedad 3

**Evidencia.** `pipeline/fetch.py:167 a 170`: se pide el producto estándar ("~3 a 5 días de retraso") y se cae al
NRT si no existe. La ventana termina el 2026-10-07 y el despacho sería el 10-08 o 10-09, con 8 jobs en dos tandas
(`max-parallel: 6`). Un brazo de la segunda tanda puede recibir estándar donde uno de la primera recibió NRT, justo
en 10-03 a 10-07, que es donde están 9 de las 24 alertas VIIRS de 1 MW o más. El record de producción de 08:35 es
`product_version: nrt`; el de C0 probablemente será `standard`. El reproceso ya no es determinista bit a bit
(verificador S150, H6), y el gemelo sólo cubre a B.

**Corrección.** Despachar no antes de que el estándar cubra toda la ventana (del orden del 2026-10-13), o agregar
al control de cobertura que cada pasada tenga el mismo `product_version` en todos los brazos y marcar
INDECIDIBLE la pasada que no.

### H6. La cadena de comparaciones esconde pérdidas contra producción, y el veto de cero no distingue ruido. Gravedad 3

**Evidencia.** P1 compara F sólo contra B. Si B pierde una alerta de 1 MW o más (P2 falla), F puede pasar P1 y aun
así perder algo que hoy el operador ve. El §5 no dice si un brazo construido sobre un brazo vetado hereda el veto.
Y el control de determinismo admite 2 % de pasadas con decisión distinta (§4.2) mientras P1 y P2 vetan con una sola
pérdida en unas 24 oportunidades: una pérdida que también aparezca entre G y B es ruido, no palanca.

**Corrección.** Todo brazo se compara también contra C0 en las alertas de 1 MW o más (el veto es absoluto); la
cadena queda para atribuir. Una pérdida no cuenta para el veto si la misma pasada cambia de decisión entre G y B
(o entre E y C0 en VIIRS, ver H7). En la práctica el sustrato del veto es suficiente: en producción C0 publica las
8 alertas VIIRS 375 y las 6 VIIRS 750 de 1 MW o más hasta el 10-02, y quedan 5 y 5 más hasta el 10-07.

### H7. El control positivo depende de que C0 reproduzca `far` en una sola pasada. Gravedad 2

**Evidencia.** El §4.3 se ensayó sobre el record de producción, que es NRT. En el reproceso C0 puede salir con
otro píxel más caliente, o sin esa pasada, y entonces "E la publica" pasa sin probar el cableado. Hay un control
mejor y gratis: E es C0 más una reetiqueta, así que es exactamente comprobable.

**Corrección.** Control positivo: en cada pasada MODIS donde E y C0 tienen el mismo `primary_cluster`, la etiqueta
de E es igual a `derivar_distance_class(final, pc, inner, True)` aplicada al record de C0 (más el guard A46), y se
exige al menos una pasada con C0 `far` y cúmulo dentro del inner. Y en VIIRS, E contra C0 y KE contra K tienen que
ser idénticos en la decisión de publicar: es el control de determinismo de C0, que hoy no tiene gemelo.

### H8. Los perfiles nuevos no están en main y el workflow no imprime el flag. Gravedad 2

**Evidencia.** `gh api .../contents/pipeline/profiles/_s150_etiqueta_cumulo.yaml?ref=main` da 404; main remoto
está en `327621e2c`. El workflow hace `actions/checkout@v4` sobre la ref del despacho. Despachado sobre main, E y
KE fallan al cargar el perfil (`pipeline/profile.py:36 a 43` lanza error, falla ruidosa pero cuesta un run). El paso
"El brazo LEE lo que declara" (`reproc-s146-ab-sin-test1.yml:114 a 123`) no imprime
`ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER`, así que el log no prueba que E leyó el flag (A116).

**Corrección.** Despachar con `--ref s150-ndc` (el yml está en main, así que se puede) o mergear antes; agregar el
flag a la línea que imprime el paso y al `assert`. Escribir la ref en el §2.

### H9. Los números del §1 no se reproducen con la referencia congelada. Gravedad 2

**Evidencia.** "VIIRS 375 publica las 13 alertas de MIROVA" (2026-09-26 a 10-02): con la referencia congelada y el
evaluador son **11** nocturnas, las 11 publicadas; el auditor B da lo mismo (`alertas_con_record 11`). MODIS 1 de 3 y
VIIRS 750 7 de 8 sí se reproducen. "21 de VIIRS 375 y 14 de VIIRS 750" incluye una alerta diurna en cada sensor (H3).

**Corrección.** Corregir a 11 y decir con qué referencia y qué script salen los números del §1.

### H10. P7 queda censurada en 5 MW. Gravedad 2

**Evidencia.** En la ventana hay records MODIS con `primary_cluster.vrp_mw` exactamente 5,000 (el tope D9; 9 de los
27 MODIS de 09-20 a 10-02 en `tope_d9_en_erupcion_salida.txt`), y el record de 08:35 tiene `vrp_mw` 5,0. MIROVA
publica 6,17 y 5,18 MW en MODIS y hasta 10 MW en VIIRS 750. La razón contra MIROVA queda acotada por arriba en
esas pasadas.

**Corrección.** En P7 informar aparte las pasadas con magnitud igual al tope, y no calcular medianas que las mezclen.

### H11. Falta exigir cobertura de cada alerta de 1 MW o más. Gravedad 2

**Evidencia.** `armar_tabla.py` sólo arma filas para pasadas con record nuestro. Si un corte de NASA deja sin record
a una alerta en todos los brazos, no aparece en ninguna comparación y el veto pasa vacío. El control de cobertura
de `evaluar_ventana.py` sólo compara brazos entre sí.

**Corrección.** Listar en el pre-registro las 27 pasadas nocturnas evaluables de 1 MW o más (3 MODIS, 13 VIIRS 375,
11 VIIRS 750; detalle en la salida de `recuento.py`) y exigir record en todos los brazos para cada una; la que falte
es INDECIDIBLE, no "sin pérdida". `banco_paridad.alertas_sin_record` ya lo cuenta.

### H12. Insumos que se mueven. Gravedad 1

- El NRT está caído desde el 2026-10-02 (último commit de NdC 2026-10-02 12:34 en el remoto; los runs de `nrt.yml`
  del 10-07 y 10-08 fallan; hay uno encolado a las 18:08 UTC del 10-08). Cuando vuelva, su ventana de hoy más 7
  días y la mejora NRT a estándar de `store.py` van a reescribir los records de producción del §1 y del §4.3.
  Corrección: guardar el sha del `NevadosDeChillan.json` usado.
- En la referencia congelada, del 10-04 al 10-07 hay 4 a 5 filas VIIRS por día contra 6 a 9 en los días previos.
  SIN VERIFICAR si es real o si el scraper todavía no completó esos días. Corrección: al evaluar, recongelar y
  reportar la diferencia como información; decide la congelada.
- El predicado se lee de `frontend/index.html` al momento de evaluar. Corrección: registrar su sha en la salida y
  correr `control_identidad_predicado` (lo hace `evaluar.py`, no `armar_tabla.py`).

### H13. Detalles. Gravedad 1

- "Del orden de una hora cada uno": el propio workflow estima 1,5 a 3 h por job (`reproc-s146-ab-sin-test1.yml:28`).
  Cabe en el timeout de 300 min, pero conviene no prometer una hora.
- La cita "AUDIT_S149 §5" de la tasa base apunta a una fila de tabla (`docs/AUDIT_S149.md:167`); poner la línea.

## Addendum: tres datos del auditor B, verificados aquí (no heredados)

El coordinador pasó tres afirmaciones de `docs/audit_s150/AUDITOR_B.md`. Las medí sobre los records de producción
de NdC (`data/mirova_equivalent/NevadosDeChillan.json`, último record 2026-10-02 07:35) con scripts propios.

**(1) El flag recupera una sola alerta y publica pasadas de MIROVA en RUTINA, varias en 5,00 MW. CONFIRMADO.**
En la ventana, E publica 30 pasadas MODIS que C0 no publica: 22 negativos limpios de reposo, 1 `sin_info` de
reposo, 4 negativos limpios y 2 `sin_info` de actividad, y **una sola alerta** (2026-10-01 08:35). La alerta de
2026-09-29 07:20 no se recupera porque el cúmulo está a 5,948 km (fuera del inner de 5 km), y la de 2026-10-05 07:50
no tiene record en producción. De las 30 nuevas, **9 tienen `primary_cluster.d9_capped = true`** (5 en reposo, 4 en
actividad), o sea que el tablero mostraría como magnitud el valor del tope. La alerta recuperada no está topada
(2,293 MW).

**(2) El tope D9 está armado en casi toda la erupción. CONFIRMADO.** El predicado
(`pipeline/process_modis.py:1009 a 1016`) exige tope configurado, `t_bg` bajo `path_d_only_cap_tbg_max_k`, y
`n_bt_path == 0` y `n_nti_path == 0`. `mirova_equivalent.yaml:491 a 492` fija 5,0 MW y 270 K. Con el camino BT
apagado, `diag_n_bt_path` vale 0 en todos los records de la ventana, así que el predicado se reduce a "fondo bajo
270 K y ningún píxel por NTI absoluto". Del 09-20 al 10-02: armado en **21 de 27** MODIS, **44 de 56** VIIRS 375 y
**53 de 55** VIIRS 750 (el auditor da 55 en VIIRS 375; la diferencia es un record). Topados de hecho: **11 de 27**
MODIS (`d9_capped`), ninguno en VIIRS. MIROVA publica en MODIS 6,17 y 5,18 MW, y el tope no existe en MIROVA (es la
opción C de D9, S71, parche propio).

**(3) La etiqueta `far` sale de un píxel que `store.py` ya descartó. CONFIRMADO, pero no cambia ninguna
publicación.** `_filter_pixels_by_distance` (`store.py:225 a 277`) saca los píxeles a más de `radius_km` (25 km en
NdC) y recalcula `hotspot_*`, pero no `final_hotspot_*` ni `distance_class`. En la ventana, **20 de 39** records
MODIS tienen `final_hotspot_dist_km` sobre 25 km (08:35: 32,84 km, contra 19,17 km del hotspot recalculado). En
**0 de esos 20** el hotspot recalculado cae dentro del inner (17 a 25 km), así que corregir sólo esa incoherencia
los deja igual en `far`.

### H14. El pre-registro no dice nada del tope D9, que en erupción decide magnitudes y lo que E dejaría ver. Gravedad 3

**Qué le hace a cada parte.**
- **P3**: se cumple con una sola alerta recuperada (08:35). Sigue siendo un control, no una predicción (H1).
- **P5**: tal como está escrita contaría como "publicaciones" pasadas cuya magnitud es el tope. Hay que informar
  las publicaciones nuevas de E, J, K y KE separadas por `primary_cluster.d9_capped` y por si la etiqueta de C0
  venía de un píxel fuera del geofence.
- **Lectura de E y KE**: hoy la etiqueta `far` esconde, entre otras cosas, 9 pasadas topadas en 5,00 MW sobre
  pasadas que MIROVA lista sin alerta. Encender el flag no sólo "arregla la etiqueta": destapa el tope D9 en un
  volcán nevado con fondo frío. Eso refuerza H1.
- **P7**: con el tope armado en 21 de 27 MODIS, ningún brazo puede dar más de 5 MW en esas pasadas. La razón contra
  MIROVA en MODIS queda censurada por diseño, no por la palanca que se prueba (H10 se queda corto).

**Corrección.**
(a) Agregar una predicción **falsable** sobre el tope: "el tope no cambia ninguna decisión de publicar, sólo la
magnitud". Hoy es lo que sugiere el código (sólo recorta `pc.vrp_mw` y la suma de escena, sin llevarlos a cero), pero
`isSummitDetection` (`frontend/index.html:1484`) mira `vrp_mw` y lo correcto es medirlo.
(b) Agregar un brazo barato **C0 sin tope** (`path_d_only_cap_mw: null`, un job) para medirlo. Sirve para P7 (la
magnitud real en erupción contra MIROVA) y como insumo de D9, reabierta en S146. Si la predicción (a) se cumple, la
diferencia C0 contra este brazo es sólo de magnitud y se lee directo.
(c) En P5 y P7, columnas aparte para `d9_capped`.

### H15. `final_hotspot_*` queda apuntando a un píxel descartado por el geofence. Gravedad 2 (fuera del pre-registro)

**Evidencia.** Ver (3) del addendum: 20 de 39 records MODIS de la ventana. Es la familia A46: dos representaciones
del mismo punto calculadas en etapas distintas. No mueve ninguna publicación en esta ventana, pero cualquier
auditoría espacial que use `final_hotspot_*` (A61, A70) va a ver detecciones a 25 a 35 km que el propio pipeline
descartó. **Corrección**: anotarlo en el pre-registro como salvedad para P8 (posición: usar `primary_cluster`, no
`final_hotspot`) y abrirlo como frente aparte con su propio ciclo A45. No meterlo en este A/B.

## Respuestas a las cinco preguntas

1. **Sustrato**: las pasadas únicas y el nombre están bien; los sensores también ('VIIRS' es 750). Mal: incluye
   diurnas y FP como "sin alerta" (H3). Evaluable: 27 alertas nocturnas de 1 MW o más.
2. **A118**: el flag llega a todos los consumidores de la etiqueta y nada aguas abajo puede deshacer su `summit`.
   El control positivo prueba la publicación sobre el record de producción, pero en el run conviene la identidad
   E igual a reetiqueta de C0 (H7).
3. **¿Pueden fallar?**: P3 no (H1). P4 puede fallar por la razón equivocada (H2). P1 y P2 sí pueden y tienen
   sustrato (unas 24 alertas que hoy se publican), pero deben ir contra C0 y descontar ruido (H6). Un verde de E
   no significa que la etiqueta sirva: publica 22 de 28 negativos limpios de reposo.
4. **Evaluador**: `armar_tabla.py` sirve para un volcán y esta ventana; `evaluar_ventana.py` sirve por pares;
   falta todo lo que mide P1 a P8 (H4).
5. **Lo que faltaba**: criterio de costo para E y KE (H1), identidad de producto NRT o estándar (H5), control de
   determinismo de C0 vía VIIRS de E (H7), cobertura de positivos (H11), tope de 5 MW en P7 (H10), insumos que se
   mueven con el NRT caído (H12), y una predicción más un brazo "C0 sin tope" para el tope D9 (H14).
