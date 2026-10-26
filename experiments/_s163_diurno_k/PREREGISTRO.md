# Pre-registro del A/B diurno de VIIRS sobre K (tarea 1.32, decisión D-10, issue #813)

Estado: **v3.1, corregida con tres verificaciones limpias** (la tercera, acotada al diff de la v2 a la v3, §14) (Sonnet 5.5; la primera, `verificador/INFORME.md`, 13
hallazgos, §12; la segunda, `verificador_v2/INFORME.md`, 9 hallazgos nuevos y los arreglos de la primera confirmados, §13).
La v3 cambió poco de la regla (umbral del placebo c, VIIRS 750 no adopta solo, una variante más de robustez) y la
tercera mirada no encontró ningún camino nuevo a un ADOPTAR indebido. La v3.1 cierra sus hallazgos con dos cambios más
estrictos (la variante d incluye los FALSO_POSITIVO diurnos; el placebo c tiene tope propio de GANA) que **no tienen
verificador limpio propio**, sólo pruebas y mutaciones (§14). Después, el sello (2026-10-26, S163, sesión
`diurno-k-prereg`). Nada de esto se despacha sin el sello y el candado `preregistro_aprobado=si` del workflow. Todo
número de este documento sale de un `*_salida.txt` de esta carpeta; ninguno se transcribe de memoria.

## 0. Relación con lo que ya está sellado (leer primero)

El A/B diurno ya tiene dos documentos en `experiments/_s151_ab_diurno/`: el pre-registro original (sobre el detector
anterior, C0, que dio NO ADOPTAR) y la `ADENDA_K.md`, que Nicolás selló el 2026-10-18 (D-25) para repetirlo sobre K
con la regla G1 (discrimina contra un nulo barajado), G2 (tan callada como MIROVA de día, binomial) y G3 (noches
intactas). Ese sello sigue vigente y su candado (`evaluar_diurno.py`, 72 mutaciones atrapadas) también.

Este pre-registro **propone reemplazar la regla de decisión de la adenda** por el criterio de victoria de la réplica
medido con el evaluador común de `main` (`scripts/evaluador_comun.py`, #903 a #905). Por qué:

1. **El criterio de victoria es la vara del proyecto** (`docs/MISSION.md`, decidido el 2026-10-13; manda sobre toda
   otra forma de pesar una alerta perdida contra una publicación de más). G1 y G2 eran una aproximación: G1 mide si
   el brazo separa alertas de negativos mejor que el azar, no si comete menos errores; G2 compara contra la tasa de
   alerta de MIROVA, no contra los negativos limpios donde MIROVA calla.
2. **La cobertura contra la referencia** (T1 y T2 del evaluador común) no existía cuando se selló la adenda. Nació del
   caso de Chillán del 2026-10-12: a los tres brazos de un A/B les faltaba una protegida de 8,44 MW y nadie lo vio,
   porque la cobertura comparaba brazos entre sí. De día el control no tiene records, así que comparar brazos ni
   siquiera es posible: hace falta una vara externa (§5, I4).
3. **El código operacional de MIROVA para VIIRS 750** (OSF zm62w, publicado el 2026-07-24, leído en S158) trae una
   rama diurna con un número distinto de la Tabla 1 y un filtro de reflejo solar que nuestra rama no tiene (§2.2). La
   adenda no lo conocía.

Lo que este pre-registro **conserva** de lo sellado: las ventanas W1 a W6 (iguales, para leer el resultado al lado del
de C0), los perfiles `_s154_ab_diurno_k_control` y `_s154_ab_diurno_k_on`, el workflow
`reproc-s151-ab-diurno.yml`, el despacho desde un tag fijo, el cableado de K por log y por record (H2a de la adenda) y
la regla de la adenda §3.2 en su espíritu: cuando el resultado depende del OCR, decide Nicolás (§6.4).

Si Nicolás (o la coordinadora bajo D-48) no aprueba el reemplazo, rige la adenda tal cual y esta carpeta queda como
lectura adicional informativa sobre la misma corrida.

## 1. El fenómeno y la pregunta

De día el canal de infrarrojo medio (3,7 a 4 µm) suma a la emisión térmica la luz solar reflejada. Una nube, un salar
o una ladera clara levantan píxeles sin nada caliente debajo, y el NTI y el ETI de toda la escena se vuelven más
variables. MIROVA no deja de mirar: procesa VIIRS de día con umbrales más altos y, con esa vara alta, es muy callada.
En las ventanas de abajo su tabla alerta en VIIRS 375 en 13 de 2.522 pasadas diurnas y en VIIRS 750 en 2 de 2.494,
pero con el OCR suma 26 pasadas diurnas protegidas de VIIRS 375 y 6 de VIIRS 750 (§3).

La réplica descarta todo VIIRS diurno, así que pierde por construcción esas alertas. Desde #821 la rama diurna está
cableada y apagada (`ENABLE_DAYTIME_VIIRS`, `pipeline/diurno.py`, tag `pre-s151-rama-diurna-viirs`).

El A/B sobre C0 no sirve para K: de día el Test 1 integrado disparaba en 2.000 de las 2.077 publicaciones en
negativos de VIIRS 375, y K no tiene Test 1 (#850). Con K de día quedan los Tests 2 y 3 con la conectiva `max` y la
prueba de NTI absoluto por píxel contra K1, todos con la columna diurna de la Tabla 1.

**Pregunta:** encendida la rama diurna sobre K, ¿la réplica comete menos errores que hoy según el criterio de
victoria, sin perder ninguna alerta protegida?

## 2. Brazos y umbrales

### 2.1 Brazos

| brazo | perfil | diferencia con `mirova_equivalent` |
|---|---|---|
| control | `pipeline/profiles/_s154_ab_diurno_k_control.yaml` | ninguna (sólo `data_subdir` propio, A47) |
| diurno | `pipeline/profiles/_s154_ab_diurno_k_on.yaml` | `enable_daytime_viirs: true` y nada más |

`tests/test_perfiles_diurno_k_s154.py` resuelve todas las constantes de `pipeline.profile` y comprueba que el control
es producción salvo nombre y directorio y que el diurno difiere sólo en la palanca: **3 pruebas en verde el
2026-10-26 sobre `047bd5692`**. Se vuelve a correr sobre el commit del tag antes de despachar (§8). Ninguno de los dos
perfiles es nuevo: no se toca `pipeline/`.

El brazo diurno corre **sin** `--no-night-filter`: lo que se prueba es que el flag abre por sí solo las compuertas de
`fetch.py`, `run_pipeline.py`, los procesadores y `store.py` (A118; en S92 un A/B diurno de MODIS abrió una sola y
midió cero).

### 2.2 Umbrales diurnos: lo que usa la rama y lo que usa MIROVA

**Coppola et al. 2016a** (`documentacion/sp426.5.pdf`), **PDF p. 7, Tabla 1** («Parameters used in the MIROVA
algorithm»), columna derecha, **verificada renderizando la página a imagen a 300 dpi** (A95; el render no se commitea,
regla S158): de noche K1 = -0,8 en las dos ROI, C1 = 0,003 (ROI1) y 0,01 (ROI2), C2 = 5 y 10; **de día ROI1 = ROI2:
K1 = -0,6, C1 = 0,02, C2 = 15**. El texto de la misma página dice que los parámetros se separan de noche y de día
porque los efectos solares amplifican la variabilidad del NTI y del ETI. Es lo que usa la rama diurna
(`pipeline/diurno.py::umbrales_viirs`). La Tabla 1 es del MIROVA de MODIS: aplicarla a VIIRS es la misma analogía que
la réplica ya hace de noche.

**El código operacional de MIROVA para VIIRS 750** (`experiments/_s158_d17_diseno/osf_codigo_mirova/MIROVA_VIIRS750_hotspot_detection.m`)
difiere en dos puntos del día, que este A/B **no** cambia y declara:

- **K1 diurno -0,5** (l. 189; la Tabla 1 dice -0,6). El resto coincide: multiplicador de σ 15 en las dos ROI (l. 191 y
  192), mínimos de dNTI y dETI 0,02 (l. 194 a 198).
- **Filtro de reflejo especular** (l. 83 a 89, la condición en l. 87): si el ángulo de reflejo especular de la escena
  es menor que 12°, MIROVA descarta la detección entera. Nuestra rama no lo tiene. **Los records sí guardan los cuatro
  ángulos** (cenit y acimut del sensor y del Sol, `sensor_zenith_deg` y compañía, escritos por `observation_geometry`
  de `process_viirs.py` y `process_viirs_mod.py` en el punto reportado: el hotspot final o, si no hay, el cráter;
  corregido por el verificador, V4, la v1 decía SIN DATO). Con la fórmula del README de MIROVA (l. 32 a 36) el
  evaluador calcula el ángulo y da una **variante informativa con el filtro de 12°** (§7). No es exactamente el escalar
  de MIROVA (el de MIROVA es de la escena; el nuestro, del punto reportado, que a 25 km del cráter cambia poco:
  SOSPECHA, no medido).

Para VIIRS 375 no hay código de MIROVA en `main`, y ningún paper da números diurnos de VIIRS: la Tabla 1 es la única
fuente citable. **Para VIIRS 750, en cambio, manda el código** (`docs/MISSION.md`, decisión de Nicolás del 2026-10-21:
«cuando el paper y el código difieren, manda el código»). La rama diurna usa la Tabla 1, así que lo que este A/B mida en
VIIRS 750 de día no es la configuración de MIROVA: por eso un ADOPTAR de VIIRS 750 no se adopta solo (§6.3; verificador
v2, V-N7). Si VIIRS 750 sale con publicaciones de más, el candidato a probar es el K1 de -0,5, en el programa de VIIRS
750 (V750-B). El filtro de 12° probablemente no explica nada: en la muestra real de C0 no apaga ninguna publicación y la
marca S158 de `CLAUDE.md` dice que ninguna de 17.859 pasadas diurnas del OSF tiene reflejo bajo 10° (verificador v2,
V-N8).

## 3. Ventanas y sustrato

Salida: `sustrato_k_salida.txt` y `sustrato_k.json` (script `sustrato_k.py`). Referencia: la unión del árbol `047bd5692`
(45.355 filas, 2026-01-10 a 2026-10-25), canal unión, regla de mínimas SN (D-9). Clases por pasada diurna VIIRS (§4).

| ventana | fechas (incl.) | volcanes | VIIRS 375: protegidas / alertas < 1 MW / negativos (bloques) / diurnas | VIIRS 750: protegidas / alertas < 1 MW / negativos (bloques) / diurnas | etiqueta que decide (A119) |
|---|---|---|---|---|---|
| W1 | 2026-03-01 a 03-20 | Láscar | 6 / 2 / 17 (9) / 39 | 0 / 0 / 40 (20) / 40 | sólo la tabla (se informa aparte) |
| W2 | 2026-06-13 a 06-30 | 11 Tier A | 11 / 1 / 485 (165) / 585 | 1 / 0 / 608 (195) / 617 | tabla y OCR |
| W3 | 2026-07-20 a 07-31 | 11 Tier A | 1 / 2 / 386 (122) / 425 | 0 / 0 / 405 (131) / 410 | tabla y OCR |
| W4 | 2026-08-13 a 08-31 | 11 Tier A | 5 / 4 / 490 (189) / 546 | 2 / 0 / 509 (204) / 525 | tabla y OCR |
| W5 | 2026-09-01 a 09-20 | 11 Tier A | 4 / 2 / 525 (203) / 579 | 1 / 0 / 529 (213) / 550 | tabla y OCR |
| W6 | 2026-10-01 a 10-14 | 11 Tier A | 5 / 1 / 360 (126) / 412 | 2 / 0 / 382 (139) / 397 | tabla y OCR |
| **W2 a W6** | | | **26 / 10 / 2.246 / 2.547** | **6 / 0 / 2.433 / 2.499** | |

Con la tabla sola, W2 a W6: VIIRS 375, 6 protegidas, 7 alertas bajo 1 MW, 2.271 negativos; VIIRS 750, 2 protegidas, 0
alertas bajo 1 MW, 2.439 negativos. Quedan como «otra» 265 pasadas diurnas de VIIRS 375 y 60 de VIIRS 750 (días con
alerta o FALSO_POSITIVO diurno, sólo OCR sin alerta, sin geometría). **En W2 la tabla no tiene ninguna alerta
diurna**: sus 13 positivos (12 de VIIRS 375 y 1 de VIIRS 750) son sólo del OCR, del tramo en que el OCR recién
empezaba a medir la distancia (A119, hito del 2026-06-13).

Notas que pesan:
- **Por qué no hay W7.** La tabla de MIROVA del árbol se corta el 2026-10-19 (desde el 10-20 sólo hay filas del OCR).
  Dentro de W2 a W6 también hay días parciales (verificador V7, `verificador/v_huecos2.py`): el 2026-10-12 sólo tiene
  noche, el 10-13 sólo día, y una decena de días tiene un tercio de las pasadas de un periodo. Con la definición de
  negativo por periodo (§4) un día al que le falta la noche ya no convierte sus RUTINA diurnas en negativos dudosos; una
  pasada que la tabla no lista simplemente no entra a ninguna cuenta. Es el problema de Mirova-v1 que
  investiga otra sesión (D-39). Una ventana nueva espera a que esa referencia esté reparada.
- W1 es anterior al 2026-04-01 (A119: la tabla exponía menos gránulos VIIRS por noche; su tasa por pasada no se suma)
  y sólo trae Láscar. Se corre primero, como job corto para medir la duración (§8), y se informa aparte.
- **Sustrato del criterio bajo 1 MW, de día: casi nada.** Hay 10 alertas diurnas bajo 1 MW en VIIRS 375 y ninguna en
  VIIRS 750, contra 2.246 y 2.433 negativos. El lado «alertas bajo 1 MW» del criterio apenas puede pesar; lo que
  decide en la práctica es cuántas protegidas recupera el brazo contra cuántas publicaciones agrega (§6, caso e).
  Se dice ahora para que nadie lo descubra en el resultado.
- El pareo es por volcán, sensor y hora (±120 s, `clase_mirova.VENTANA_S`), **nunca** por la distancia del OCR.

**Contexto de la noche de producción, no vara** (`nulo_estructural_salida.txt`, líneas «control»; producción es K en
todo el histórico desde #883 y ahí hace de control, con las funciones del mismo evaluador): en las mismas ventanas, de
noche, producción publica en el **3,67 %** (de 1.606) de los negativos limpios nocturnos de VIIRS 375 y en el **0,93 %**
(de 2.375) de los de VIIRS 750. Ese es el orden de magnitud de Q_n que la opción e-i usaría como vara; la vara que decide es la del control del A/B.

## 4. Unidad, clases y métricas

Unidad: la **pasada** de MIROVA (`clase_mirova.resumir_pasadas`). «Publica» = el predicado del tablero
(`isValidDetection` de `frontend/index.html`) corrido con node (`banco_paridad.correr_node`), nunca uno reconstruido
(A97). Día = elevación solar mayor que 0 sobre el volcán a la hora de la pasada (`pipeline.store._solar_elevation`,
la misma regla del pipeline). La tabla por pasada es la de `evaluador_comun.tabla_por_pasada`; «día con alerta» y «día
con FALSO_POSITIVO» se recalculan **por periodo** (`banderas_por_periodo`): una pasada diurna mira sólo las diurnas de
su volcán, sensor y día UTC, y una nocturna sólo las nocturnas (que es lo que ya hace el evaluador común, que sólo ve
noches). Por qué (verificador V2): en la v1 el día UTC entero dejaba 789 RUTINA diurnas fuera de los negativos sólo
porque la madrugada del mismo día UTC había alertado, y las publicaciones del brazo ahí no entraban a ninguna regla. De
día MIROVA usa otros umbrales y su pasada es una mirada aparte: si al mediodía dijo RUTINA, calló.

Clases de una pasada (las de `evaluador_comun.clase_p2`, con la protegida aparte):
- **protegida**: alerta de 1 MW o más (lectura A, D-4);
- **alerta_mb**: alerta bajo 1 MW (con SN, las de 0,05 MW o menos de VIIRS 375 cuentan como RUTINA, D-9);
- **negativo**: pasada de la TABLA, RUTINA, en un volcán, sensor, día UTC y periodo sin ninguna alerta ni
  FALSO_POSITIVO de MIROVA;
- **otra**: el resto (FALSO_POSITIVO, RUTINA en un periodo con alerta o FALSO_POSITIVO, sólo OCR sin alerta, sin
  geometría). No entra al criterio; las publicaciones del brazo ahí se informan (265 pasadas diurnas en VIIRS 375 y 60
  en VIIRS 750: lo que el brazo publique ahí queda a la vista en M4, no en la regla).

El control no publica de día por construcción (`store.py` rechaza el VIIRS diurno con el flag apagado). En cada
pasada diurna que el brazo observó, el estado del control se toma como «observado, no publica», **sólo después** de
comprobar que el control trae cero records VIIRS diurnos (compuerta I2). Así el evaluador común puede contar
discordancias sin inventar un record.

Métricas, por sensor (VIIRS 375 y 750):
- **P**: protegidas diurnas que el brazo publica, sobre las observadas. «Recuperar» es publicar, con cualquier
  magnitud (verificador V8): así lo define el criterio, que separa recall y razón de magnitud. Se informa aparte cuántas
  se publican con 1 MW o más (`P_1mw`).
- **neto** y resultado de **P2 diurno**: el criterio bajo 1 MW. Cada pasada diurna discordante aporta +1 si el error es
  sólo del brazo (publica en un negativo) y -1 si es sólo del control (el brazo publica una alerta_mb que el control,
  que no mira el día, pierde). Prueba de signos por bloque volcán-día (D-45, `evaluador_comun.decidir_p2`: exacta con
  20 bloques o menos, si no 10.000 sorteos con semilla 162; GANA o PIERDE con p de 5 % o menos; SIN SUSTRATO con 4
  bloques o menos).
- **Q_d**: publicaciones del brazo en negativos diurnos limpios / negativos diurnos observados.
- **Q_n**: publicaciones del **control** en negativos **nocturnos** limpios / observados, mismas ventanas y volcanes:
  el punto de operación nocturno de K.
- **M4**, la cuenta que lee Nicolás si decide él: protegidas recuperadas contra publicaciones agregadas en negativos,
  por sensor y ventana, con la lista de pasadas de cada lado; además las publicaciones de 1 MW o más en negativos
  (una alerta clase Bajo que MIROVA no hizo, el P1b «arriba» de día) y las publicaciones en pasadas «otra».
- **Magnitud** (informativa): mediana de la razón brazo / MIROVA en las alertas diurnas recuperadas, al lado de la del
  control de noche. El comparador d′ del evaluador común (D-28) **no se aplica de día**: compara la magnitud del brazo
  contra la del control en los mismos pares, y de día el control no tiene magnitud. De noche la magnitud de los dos
  brazos tiene que ser idéntica (compuerta I5), así que M nocturno no tiene nada que medir.

## 5. Compuertas de instrumento (el nulo medido, A110)

Cualquiera de I1 a I4 que falle: **INVÁLIDO POR INSTRUMENTO**, no se lee ningún veredicto. I5 o I6 que fallen:
**INDECIDIBLE**. El remedio de una falla de cobertura es repetir el job desde el mismo tag y unir los intentos (D-13,
`experiments/_s153_fk_v2/unir_ventana.py`).

- **I1, cableado de K.** (a) Por log, cuando las raíces traen `logs/`: la línea `FLAGS_BRAZO` de cada job dice su
  perfil y directorio, `ENABLE_TEST1_PATH` falso, `ENABLE_TESTS_23_PROSE_BRANCH` verdadero,
  `ENABLE_MODIS_B22_PRIMARY` verdadero y `ENABLE_DAYTIME_MODIS` falso en los dos brazos, y `ENABLE_DAYTIME_VIIRS`
  falso en el control y verdadero en el diurno. (b) Por record, siempre (H2a de la adenda, porque `unir_ventana.py`
  no copia logs): cero records con `triggered_test1` verdadero o con `final_hotspot_source` en `test1` o `test1_roi`,
  y `regimen.codigo_sha` igual al commit del tag de despacho, los 40 caracteres, en todos los records de la ventana.
- **I2, la palanca actuó** (A116). El brazo diurno trae records VIIRS diurnos con `diag_umbrales_diurnos` en cada
  ventana y sensor con pasadas diurnas de MIROVA; el control trae **cero** records VIIRS diurnos; ningún record
  nocturno del brazo trae `diag_umbrales_diurnos`.
- **I3, cobertura nocturna contra la referencia**: `evaluador_comun.cobertura` sobre las pasadas nocturnas de los tres
  sensores y **sólo con los records nocturnos**, control contra brazo, da COBERTURA OK (verificador v2, V-N6: con los
  records de día, un record diurno del brazo tapaba un día sin ningún record nocturno).
- **I4, cobertura diurna contra la referencia.** De día el control no sirve de vara; la vara es la noche de producción.
  (a) Toda alerta diurna VIIRS de MIROVA (protegida o bajo 1 MW) tiene record del brazo (verificador V10: la v1 vigilaba
  sólo las protegidas, y perder unas pocas de las 10 alertas bajo 1 MW achicaba D y el neto en silencio). (b) Ningún volcán, sensor y día con pasadas diurnas de MIROVA
  queda con cero records diurnos del brazo. (c) Si X de las N pasadas diurnas de MIROVA (W2 a W6) no tienen record del
  brazo, falla cuando P(Bin(N, p_sup) ≥ X) < 0,05, con p_sup la cota superior de Clopper-Pearson al 95 % (una cola)
  de la tasa nocturna de producción del sustrato: VIIRS 375, 0 de 2.715 (p_sup = 0,0011); VIIRS 750, 9 de 2.650
  (p_sup = 0,0059). El umbral sale del dato (A115), no se elige. Con N = 2.547 y 2.499 eso falla desde 7 pasadas sin
  record en VIIRS 375 y desde 22 en VIIRS 750 (verificador V10); la tasa diurna propia del brazo no se conoce antes de
  correr (SIN DATO), por eso la vara es la noche.
- **I5, noches intactas** (la G3 de la adenda). Los dos brazos tienen **los mismos records nocturnos** (verificador V6:
  la v1 sólo comparaba los que estaban en los dos y un record faltante pasaba sin marca) y, en cada uno, la misma
  publicación y la misma magnitud publicada (con eso no hay cruces de 1 MW en ninguna dirección). La G3 de la adenda
  pedía el record entero; aquí decide lo que lee el criterio (publicación y magnitud) y las diferencias en otros campos
  (posición, cúmulo, diagnósticos) se **informan** con su lista (`huella` del record sin los campos volátiles), porque un
  desempate que depende de la CPU (S152, D-16, D-22) cambia campos que no deciden y haría INDECIDIBLE el A/B por nada
  (verificador v2, V-N5: es una protección menor que la G3, y se dice). La huella deja fuera los campos volátiles
  (`updated`, `processed_utc`, `first_processed_utc`, `regimen`) y los `diag_*`, que difieren entre dos corridas del
  mismo código por punto flotante. En la prueba de humo sobre C0 quedan así 4 de 725 records nocturnos distintos,
  todos MODIS (el desempate del top-100 que depende de la CPU, D-16): es lo que este informativo tiene que mostrar. Una discordancia da
  INDECIDIBLE con la lista; se repiten esos volcanes en los dos brazos desde el mismo tag. Si reaparece en el mismo
  record, es cableado (INVÁLIDO); si cambia entre intentos, es un desempate que depende de la CPU (S152, D-16, D-22) y
  se usa el intento sin discordancia, declarado como desviación.
- **I6, el criterio puede ver lo que mide.** Los placebos de D-44 (`evaluador_comun.placebo_p2`), armados sobre el
  brazo diurno en las pasadas diurnas de cada sensor: (a) apagar la mitad de sus publicaciones en negativos diurnos
  tiene que dar GANA cuando eso toca 5 bloques o más (si toca menos se informa SIN SUSTRATO); (c) el simétrico por
  bloque, fracción 1, con 40 semillas (161 a 200), no puede dar GANA o PIERDE en 8 o más de 40. Cada sorteo es falso si
  da GANA **o** PIERDE, dos pruebas de una cola al 5 %, y además no puede dar GANA en 5 o más de 40
  (P(Bin(40; 0,05) ≥ 5) = 0,048; verificador v3, V3-4: lo que lleva a adoptar es el lado GANA, y la suma sola dejaba
  pasar 7 GANA y 0 PIERDE). Para la suma: la tasa nominal por sorteo es de hasta 10 % (el verificador v2
  midió 7,2 a 8,3 % con la estructura real, `verificador_v2/medidas4_salida.txt`), y P(Bin(40; 0,10) ≥ 8) = 0,042. La
  v1 y la v2 usaban 5 de 40 con la tasa de una sola cola, y con un brazo ruidoso caían en INDECIDIBLE 16 a 23 % de las
  veces por nada (V-N3). Este placebo es además **lo único que mide el tamaño real de la prueba de signos**: el nulo
  del §5.1 (i) no puede, porque un brazo al azar casi siempre suma +1 y nunca puede dar GANA. (b), apagar la mitad de sus alertas bajo 1 MW publicadas, se informa: con 10 alertas en VIIRS
  375 y ninguna en 750 casi nunca tendrá sustrato. Además, antes de despachar, el nulo de P2 se midió sobre la
  estructura real de bloques de W2 a W6 con un brazo sintético que publica al azar (§5.1). **Límite declarado**
  (verificador V9): con un brazo callado, que es justo el caso en que se adopta, el placebo a toca menos de 5 bloques y
  da SIN SUSTRATO, y cuando sí toca 5 o más, da GANA casi por aritmética de la prueba de signos. I6 comprueba que la
  prueba de signos ve un cambio en estos datos, no que el brazo sea bueno; la protección del resultado está en I4, I5,
  D y el nulo del §5.1.

### 5.1 Nulo medido antes de despachar

`nulo_estructural.py` (salida en `nulo_estructural_salida.txt`) arma la tabla real de pasadas de W2 a W6 (referencia
congelada; los records nocturnos de producción, que es K desde #883, hacen de control) y le pone encima brazos
diurnos sintéticos que publican cada pasada diurna VIIRS al azar con probabilidad q, sin mirar si es alerta o
negativo, para q de 0,5 %, 2 %, 5 % y 20 %, 200 repeticiones cada una. Lo que tiene que pasar: (i) P2 diurno da GANA
en no más del 5 % de las repeticiones; (ii) el veredicto por sensor da ADOPTAR en no más del 5 %, con e-i y con e-ii;
(iii) control positivo: un brazo que publica exactamente las alertas diurnas de MIROVA y nada más da ADOPTAR en los dos
sensores **por sensor** (en el veredicto global da DECIDE NICOLÁS desde la v3, por la regla de VIIRS 750 del §6.3;
verificador v3, V3-3); (iv) control negativo: un brazo que publica todas las pasadas diurnas da NO ADOPTAR en los dos. Si (i), (iii)
o (iv) fallan, el instrumento no sirve; (ii) por encima de 5 % se informa como debilidad de la regla antes del sello.

**Resultado de la v2 (2026-10-26, `nulo_estructural_salida.txt`, con el negativo por periodo):** (i) GANA en 0 de 200
en las ocho combinaciones de tasa y sensor. (ii) **Con e-ii, la opción recomendada, ADOPTAR en 0 de 200 en todas.**
Con e-i, en VIIRS 375 3 de 200 a 0,5 % y 7 de 200 a 2 % (3,5 %), 0 a 5 % y a 20 %; en VIIRS 750 **10 de 200 a 0,5 %
(5,0 %, justo en el límite)**, 0 en las demás: con D el falso ADOPTAR de e-i queda en el nivel de la prueba D, y en
VIIRS 750, con 6 protegidas y Q_d de 0,5 %, recuperar una sola por azar ya pasa D. (iii) El control positivo da GANA y
ADOPTAR en VIIRS 375 (neto -10, 26 de 26 protegidas) y SIN SUSTRATO con ADOPTAR por el caso b en VIIRS 750 (6 de 6).
(iv) El control negativo da PIERDE y NO ADOPTAR en los dos (D no cumple). Producción, de control, da Q_n de 3,67 % (de
1.606 negativos nocturnos) en VIIRS 375 y 0,93 % (de 2.375) en VIIRS 750. (La v1, con el negativo del día UTC entero,
daba lo mismo salvo e-i en VIIRS 375: 4 y 4 de 200, y Q_n de 3,51 % y 0,94 %.)

### 5.2 Batería, mutaciones y prueba de humo

- **Batería** (`test_evaluar_diurno_k.py`, 80 pruebas desde la v3.1; 78 en la v3, 65 en la v2): cada caso a a e del §6.2, el §6.3, el §6.4, cada compuerta I1
  a I6 con un escenario que la hace fallar, la definición de negativo, el control sintético, R1, Q_n del control, la
  prueba D, el borde de 1 MW, la lectura de los logs y, desde la v2, el negativo por periodo, la exclusión que no
  vuelve negativas a las vecinas, la alerta bajo 1 MW sin record, los records nocturnos en un solo brazo, el ángulo de
  reflejo y el M4 por ventana. Se escribió antes del evaluador: contra un stub fallaron las 53
  que había entonces (`probar_salida_roja.txt`).
- **Mutaciones** (`mutaciones.json`, corredor `experiments/_s162_instrumento/mutar.py`, que cuenta como atrapada sólo
  la que falla por aserción según el JUnit, nunca por excepción): **60 de 60 atrapadas por aserción en la v3**
  (`mutaciones_salida.txt`; la salida dice «60 de 61» porque cuenta la de control, que tiene que quedar fuera); entre
  ellas las 7 que el verificador v2 escribió sobre `main()` y el cargador (X1 a X7), que en la v2 sobrevivían, y 5 sobre
  lo nuevo de la v3. En la v2 fueron 48 de 48. Después de esa corrida se ajustó la huella nocturna (fuera los `diag_*`
  y `first_processed_utc`, ver I5); ese ajuste tiene su prueba y sus mutaciones (3 de 3 atrapadas,
  `mutaciones_huella_salida.txt`), y las dos nuevas quedan en `mutaciones.json` para la próxima corrida completa. En la
  v1 fueron 41 de 41 tras cerrar con aserciones nuevas las cuatro que la primera corrida dejó vivas o caídas (borde de
  la cola de I4c, sha abreviado que fallaba por excepción, P2 diurno que contaba la noche, P que contaba alertas bajo
  1 MW); la v2 agrega 7 mutaciones sobre lo nuevo (negativo por periodo, exclusión después de las banderas, I4a de toda
  alerta, I5 de records, filtro y fórmula del reflejo). La mutación de control
  `C-CAIDA` (el evaluador lanza una excepción) sale como CAÍDA y no como atrapada, que es lo que tiene que pasar.
- **Prueba de humo sobre datos reales** (`humo_c0_W6b_salida.txt`): el evaluador corrido sobre una corrida real del
  A/B sobre C0 (W6b, run 39097155412) con `--recorte`. Sale INVÁLIDO POR INSTRUMENTO por I1 (los flags y los records son
  de C0, con Test 1), que es lo correcto, y con métricas distintas de cero: con el negativo por periodo, de día C0
  publicaba en 158 de 174 negativos de VIIRS 375 (94 de 207 en VIIRS 750) y recuperaba 5 de 5 alertas, con D sin
  cumplir (no discrimina): caso d, NO ADOPTAR en los dos sensores, que es el resultado conocido de esa corrida. Muestra que la carga, el predicado del tablero y
  la referencia congelada funcionan de punta a punta.

## 6. Regla de decisión (escrita antes de ver un solo dato de los brazos)

Ventanas W2 a W6, canal unión, regla de mínimas SN. Por sensor s (VIIRS 375 y VIIRS 750).

### 6.1 Ninguna protegida perdida (criterio, punto 1)

**R1**: pasadas protegidas, de noche y de día, de cualquier sensor, observadas por los dos brazos, en que el control
publica y el diurno no. Con las compuertas en verde R1 se cumple por construcción: de día el control no publica nada y
de noche I5 exige que los dos brazos sean idénticos record a record. Por eso una pérdida de R1 con I5 en verde no se
lee como resultado del brazo sino como **defecto del evaluador: INVÁLIDO POR INSTRUMENTO**. Si la noche cambió, manda
I5 (INDECIDIBLE, repetir); si tras repetir el mismo record sigue distinto, la rama diurna toca la noche, es un
defecto del cableado de #821 (INVÁLIDO) y, si es una protegida, también una pérdida que el criterio no acepta.

### 6.2 Veredicto por sensor

Con neto y resultado de P2 diurno, P (protegidas diurnas recuperadas), Q_d y Q_n del §4, y la prueba **D**:

**D, el brazo discrimina.** X alertas diurnas de MIROVA recuperadas (protegidas y bajo 1 MW) de las n observadas; D
cumple si P(Bin(n, Q_d) ≥ X) < 0,05, o sea si recupera más alertas que las que daría publicar al azar con la misma
probabilidad con que publica en negativos diurnos limpios (con Q_d = 0 y X ≥ 1, cumple). Es la pregunta de G1 de la
adenda, binomial exacta y sin barajado. Límite declarado (verificador V11): trata las pasadas como independientes,
y las alertas se agrupan (las 36 de VIIRS 375 caen en 30 volcán-días; Láscar y Lastarria traen 13 de las 26
protegidas), así que D es algo menos exigente que lo nominal. **Por qué hace falta**: sin D, un brazo que publica al azar a una tasa baja
saldría ADOPTAR en el caso e-i cada vez que atrapa una protegida por suerte: con 26 protegidas diurnas en VIIRS 375 y
una tasa de 0,5 %, la probabilidad de atrapar al menos una es 1 - 0,995^26 = 12 % (cálculo directo). Con D, el nulo
del §5.1 mide cuánto queda.

| caso | condición | veredicto del sensor |
|---|---|---|
| a | P2 da GANA | ADOPTAR |
| b | neto ≤ 0, P ≥ 1 y D cumple | ADOPTAR (no empeora bajo 1 MW y recupera protegidas más allá del azar) |
| c | neto ≤ 0 y (P = 0 o D no cumple) | SIN CAMBIO si el brazo no publica ninguna pasada diurna del sensor; si publica alguna, NO ADOPTAR (sin beneficio demostrado) |
| d | neto > 0 y (P = 0 o D no cumple) | NO ADOPTAR |
| e | neto > 0, P ≥ 1 y D cumple | **opción del sello**, §6.5: e-ii (recomendada desde la v2) DECIDE NICOLÁS CON M4 siempre; e-i ADOPTAR si Q_d ≤ Q_n y DECIDE NICOLÁS CON M4 si no |

El caso e es el probable (§3: 10 alertas diurnas bajo 1 MW contra 2.246 negativos en VIIRS 375). El criterio de
victoria dice que una protegida perdida no tiene compensación y que bajo 1 MW los dos errores pesan igual, pero **no
dice cuánto vale una protegida recuperada contra una publicación de más**, y eso no se inventa (A115). La v1 creía que
la opción e-i no inventaba una tasa; el verificador mostró que sí la fija de hecho (§6.5, V1).

### 6.3 Veredicto global

La rama diurna abre los dos sensores con un solo flag, así que el veredicto global combina los dos:
- cualquier compuerta I1 a I4 falla: **INVÁLIDO POR INSTRUMENTO**; I5 o I6 fallan: **INDECIDIBLE**;
- R1 encuentra una pérdida con las compuertas en verde: **INVÁLIDO POR INSTRUMENTO** (§6.1);
- algún sensor DECIDE NICOLÁS: **DECIDE NICOLÁS CON M4**;
- un sensor ADOPTAR y el otro NO ADOPTAR: **DECIDE NICOLÁS** (adoptar uno solo pide un flag por sensor, un parche en
  `pipeline/` que va con A45);
- VIIRS 750 en ADOPTAR (y ninguno de los casos anteriores): **DECIDE NICOLÁS**, porque para VIIRS 750 manda el código
  de MIROVA y la rama diurna no lo sigue (§2.2; verificador v2, V-N7). Adoptarlo pide antes llevar la rama de VIIRS 750
  al código (K1 de -0,5; parche en `pipeline/`, A45) o separar el flag por sensor;
- los dos en ADOPTAR o SIN CAMBIO, con al menos un ADOPTAR y VIIRS 750 en SIN CAMBIO: **ADOPTAR**. O sea que el A/B
  sólo llega solo a ADOPTAR global si el brazo no publica nada de día en VIIRS 750; **un brazo perfecto (que publica
  exactamente las alertas de MIROVA en los dos sensores) da DECIDE NICOLÁS** (verificador v3, V3-3, medido sobre la
  referencia completa). Es la consecuencia buscada de que para VIIRS 750 mande el código, y es sub-adopción, no
  sobre-adopción;
- los dos en NO ADOPTAR o SIN CAMBIO: **NO ADOPTAR**.

### 6.4 Robustez (cuándo el resultado depende de algo frágil)

El veredicto global se recalcula en cuatro variantes: (a) **tabla sola**; (b) **sin W2**, la ventana cuyos positivos son
todos del OCR; (c) **sin las protegidas diurnas de reflejo probable** según el estudio 1.13 (`experiments/_s151_alertas_diurnas/real_o_reflejo_filas.json`,
clase desproporcionada o aislada: 17 pasadas de W2 a W6, 13 de VIIRS 375 y 4 de VIIRS 750). Las pasadas excluidas
salen **después** de marcar los días con alerta (verificador V5: en la v1 salían antes y 12 pasadas vecinas pasaban de
«otra» a «negativo»); (d) **«otra» como negativo**: toda RUTINA diurna de la tabla cuenta como negativo aunque su
periodo tenga una alerta o un FALSO_POSITIVO, y también las pasadas FALSO_POSITIVO diurnas de la tabla (MIROVA no
alertó en el radio), para que lo que el brazo publique en esas 265 y 60 pasadas pese (verificador v2, V-N4: sin esta
variante el caso b adoptaba un brazo con 60 publicaciones ahí; verificador v3, V3-1: la v3 dejaba fuera los
FALSO_POSITIVO propios, que eran justo los de ese escenario). Si el veredicto principal es ADOPTAR o NO ADOPTAR y alguna variante da otro
veredicto global, el resultado es **DECIDE NICOLÁS**, informando cuál cambió y por qué. Es la regla §3.2 de la adenda
sellada, extendida: cuando el resultado depende del OCR o del reflejo, no se resuelve solo. Las variantes de la regla
de mínimas que pide `docs/MISSION.md` (criterio, punto 5: SE, la original y SN con 0,05 exacto como alerta, umbral
0,04) se calculan y se informan sin decidir, y la salida dice si alguna cambia el veredicto (verificador V3: la v1 las
prometía y el evaluador no las tenía).

Si D-41 (qué alertas sólo OCR entran al criterio) se decide antes del sello, la variante que D-41 elija pasa a ser el
canal principal y la unión queda como variante.

### 6.5 Opción del sello para el caso e

- **e-ii (recomendada desde la v2): DECIDE NICOLÁS CON M4 siempre.** Es lo que la regla sellada hace hoy en el caso
  análogo (G1 y G3 sin G2). Nicolás decide con M4 por sensor y por ventana, con la lista de pasadas de cada lado, la
  cuenta de publicaciones de 1 MW o más en negativos, las variantes del §6.4 y la informativa con el filtro de 12°.
- **e-i: ADOPTAR si Q_d ≤ Q_n; si no, DECIDE NICOLÁS CON M4.** La v1 la recomendaba con este argumento: un pre-registro
  cuyo caso más probable termina en «decide Nicolás después de ver los datos» es justo lo que el pre-registro quiere
  evitar, y Q_n (el control, mismas ventanas y volcanes; con producción como anticipo, 3,51 % en VIIRS 375 y 0,94 % en
  VIIRS 750 en la v1; 3,67 % y 0,93 % con el negativo por periodo) es una vara ya aceptada al adoptar K. **El verificador lo refutó (V1, gravedad 4)**: con la estructura real
  de W2 a W6, e-i da ADOPTAR con P2 en PIERDE (p de 0,0001) para un brazo que recupera 4 alertas de VIIRS 375 y publica
  en unos 50 negativos, o que recupera 1 protegida de VIIRS 750 (que puede ser reflejo: 4 de las 6 lo son según 1.13)
  y publica en 18 a 20 (`verificador/v_region_ei.py`). O sea que fija de hecho una tasa (una protegida vale hasta unas
  50 o 20 publicaciones de más) que el criterio no da. Y la G2 sellada de la adenda mandaba a DECIDE NICOLÁS desde 20
  publicaciones en VIIRS 375 y 6 en VIIRS 750. Por eso se recomienda e-ii; e-i queda como opción, con esa región a la
  vista.

ADOPTAR en este A/B **no enciende nada**: abre el ciclo de adopción (tag defensivo, R2 por píxel contra MIROVA,
verificador independiente, el frontend corregido para records diurnos según las notas de `pipeline/diurno.py`, y el
sí de Nicolás; reglas S33 y A45). Cualquier mejora de más de 30 % en una métrica exige auditoría independiente antes
de aceptarla.

## 7. El reflejo solar (A76): cómo se cuenta

- **Las alertas diurnas de MIROVA cuentan como lo que son** (la vara de la réplica es lo que MIROVA publica, A115),
  también las que probablemente son reflejo: el 760,6 MW de Láscar del 2026-06-15 (A76) es positivo. Su NRT no está
  supervisado a mano (A105). Separar reflejo de calor es tarea del perfil `experimental` (S143), no de la réplica.
- **Nuestras publicaciones diurnas en negativos limpios cuentan como error** sean reflejo o no.
- La dependencia del reflejo se mide con la variante (c) del §6.4: si el veredicto cambia al sacar las protegidas de
  reflejo probable, decide Nicolás.
- Informativo (el evaluador lo imprime desde la v2): las publicaciones del brazo en negativos diurnos por elevación
  solar (0 a 30°, 30 a 60°, más de 60°); la clase según el instrumento a) del estudio 1.13 aplicado a lo nuestro
  (magnitud diurna contra la mayor publicación nocturna del brazo, mismo volcán y sensor, ±72 h; desproporcionada sobre
  T = 3,16, el umbral de ese estudio; aislada si no hay ninguna nocturna); y una **variante con el filtro de reflejo
  especular de MIROVA**: las publicaciones diurnas del brazo con ángulo menor que 12° (fórmula del README de MIROVA,
  ángulos del record, §2.2) quedan sin publicar, y se informa el veredicto que saldría. Es lo que haría la rama diurna
  con el filtro de MIROVA puesto, sin tocar `pipeline/`; no decide, porque no es lo que el brazo hace.

## 8. Despacho (lo que hace la coordinadora después del sello)

- **Workflow**: `.github/workflows/reproc-s151-ab-diurno.yml`, sin cambios. **Ojo (verificador V13)**: sus valores
  por defecto de `brazos` y `control` son los de C0 (`_s151_ab_diurno_*`) y la descripción del candado apunta al
  pre-registro de `_s151_ab_diurno`. Un despacho que omita las entradas corre C0 durante horas; el evaluador lo
  atraparía (I1, por flags y por sha), pero tarde. Las entradas se pasan siempre explícitas (abajo). Cumple lo exigido: `"on":` entre comillas
  (A43), sólo `EARTHDATA_TOKEN` con falla inmediata si viene vacío (A71), candado `preregistro_aprobado=si`, grupo de
  concurrencia propio con un solo pendiente, un volcán y un brazo por job en su `data_subdir` (A47), timeout de 300
  min por paso contra un máximo medido de 66 min por media ventana y volcán en la corrida sobre C0 (4,5 veces, A15),
  y salidas en una rama propia `s151-ab-diurno/<run_id>` (no toca `main`).
- **Tag**: `s163-diurno-k-codigo` sobre `main` después del merge de esta carpeta, y su commit completo con
  `git rev-parse s163-diurno-k-codigo^{commit}` (40 caracteres; el evaluador se niega con uno abreviado). Antes de
  despachar, en ese commit: `python -m pytest -q tests/test_perfiles_diurno_k_s154.py` en verde.
- **Entradas**: `brazos=["_s154_ab_diurno_k_control","_s154_ab_diurno_k_on"]`, `control=_s154_ab_diurno_k_control`,
  `--ref s163-diurno-k-codigo`.
- **Orden**: W1 primero (Láscar, 20 días, 2 jobs) para medir la duración del brazo diurno sobre K. W1 dura lo mismo
  que la ventana más larga (W5, 20 días), pero Láscar puede no ser el volcán más lento: en la corrida sobre C0 los
  jobs diurnos de una misma media ventana iban de 40 a 58 min (1,45 veces). Si la duración del job diurno de W1 × 1,45
  × 1,3 cabe en 300 min, W2 a W6 van enteras (5 despachos de 22 jobs); si no, en las mismas diez mitades de la corrida
  sobre C0 (W2a a W6b, 10 despachos de 22 jobs). Esta regla es operativa: no cambia el criterio. Uno por
  despacho, y el siguiente recién cuando el anterior empezó (el grupo guarda un solo pendiente).
- **Cupo**: el workflow corre con `max-parallel: 3`. Con el NRT (11) quedan 6 de los 20 para otros. Subirlo a 6 es una
  línea del workflow, pero cambia el árbol del tag: si la coordinadora lo quiere, se hace antes del tag y se dice.
- **Costo estimado** (con la corrida sobre C0, la única medida: control 15 a 24 min y diurno 40 a 58 min, máximo 66,
  por media ventana y volcán; sin el Test 1 puede bajar, no está medido): W2 a W6 son 83 días; unos 11 volcanes × 83
  días × (2,2 + 5,5) min por volcán-día ≈ 117 h de runner (los minutos por volcán-día son el medio de los rangos
  divididos por unos 9 días por media ventana; con 8,3 días de promedio los extremos van de 1,8 a 2,9 y de 4,8 a 7,0,
  verificador v2, V-N9), es decir **unas 39 h de reloj con `max-parallel: 3`** (unas 20
  con 6), más W1 (menos de 1 h).
- **Cobertura**: leer `cobertura.txt` de cada corrida antes de mirar nada; un job corto se repite con el mismo tag y se
  une (D-13).
- **Objetivos y sus sha256**: `objetivos_sha256.txt` (los blobs de git de cada archivo del que depende el despacho y la
  evaluación; desde la v3 también el predicado del tablero `frontend/index.html`, `pipeline/store.py` (define día),
  `volcanoes.yaml` (coordenadas), la clasificación del estudio 1.13 y el corredor de mutaciones: verificador v2, V-N1;
  desde la v3.1, los siete que el verificador v3 encontró con un gancho de auditoría de Python, entre ellos
  `pipeline/mirova_csv_loader.py`, que normaliza sensor y volcán de la referencia, y `scripts/auto_audit_weekly.py`, que
  da las coordenadas con que se decide el día: V3-2).
  **La evaluación se corre desde un `git archive` del commit sellado**, no desde el árbol de trabajo: el predicado del
  tablero se lee de `frontend/index.html`, que cambió cinco veces desde K y que habrá que corregir para los records
  diurnos antes de cualquier flip. Quien sella, sella esos contenidos; el verificador y la coordinadora comprueban con
  `git diff --stat <commit del sello> <tag> -- $(grep -v '^#' experiments/_s163_diurno_k/objetivos_sha256.txt | awk '{print $2}')`
  (vacío) que nada de lo sellado cambió antes del tag (V3-2: la v3 listaba sólo tres rutas). Los sha256 son de los blobs de git (`git
  show <commit>:<ruta> | sha256sum`): en un árbol de Windows con CRLF el archivo da otro sha sin haber cambiado.
- **Referencia congelada**: `congelar_referencia.py --commit 047bd5692 --salida <carpeta>` extrae los 4 CSV de ese
  commit; el evaluador exige que sus sha256 sean los de `sustrato_k.json`.

Evaluación:

```bash
python -I experiments/_s163_diurno_k/evaluar_diurno_k.py --raiz <W2> ... --raiz <W6> --w1 <W1> \
  --ref <carpeta congelada> --sha-codigo <40 caracteres> --opcion-e <la sellada: e-ii o e-i>
```

## 9. Lo que este A/B no decide

- Encender la rama diurna en producción (ver §6.5).
- El K1 de -0,5 y el filtro de reflejo de 12° del código de MIROVA de VIIRS 750 (§2.2).
- MODIS de día (`ENABLE_DAYTIME_MODIS`, flag propio, apagado en los dos brazos).
- El resultado sobre C0, que queda como medido.

## 10. Qué tiene que sellar Nicolás

1. Que este pre-registro **reemplaza la regla G1/G2 de la `ADENDA_K.md`** sellada (D-25), conservando ventanas,
   perfiles, workflow, tag y cableado (§0).
2. La **opción del caso e**: e-ii (recomendada desde la v2: decide él con M4) o e-i (ADOPTAR si Q_d ≤ Q_n, con la
   región que mostró el verificador a la vista) (§6.5).
3. Que la regla de robustez del §6.4 (tabla sola, sin W2, sin reflejo probable, «otra» como negativo) mande a DECIDE
   NICOLÁS.
4. Que el negativo diurno se mire **por periodo** (§4): una RUTINA del mediodía es negativo aunque la madrugada del
   mismo día UTC haya alertado. Es una definición nueva respecto del evaluador común aplicado al día entero.
5. Que no haya W7 hasta que la referencia de MIROVA esté reparada (§3).
6. Que un ADOPTAR de VIIRS 750 pase a DECIDE NICOLÁS mientras la rama diurna de VIIRS 750 no siga el código de MIROVA
   (§2.2, §6.3).

## 11. Desviaciones registradas después de ver datos

(ninguna; no hay datos de los brazos)

## 12. Verificación limpia de la v1 y qué cambió (2026-10-26)

Verificador con contexto limpio, otro modelo (Sonnet 5.5), sobre el commit `ce20f9cf` (objetos en `3a98abfad`);
informe y scripts en `verificador/`. Escribió su lista de caminos antes de abrir el evaluador (`CAMINOS_PREVIOS.md`,
sha256 en el informe). Re-corrió la batería (58 de 58), las pruebas de perfiles y el nulo (salida idéntica); no re-corrió
las mutaciones (el corredor modifica archivos del repo).

| ID | gravedad | hallazgo | qué se hizo |
|---|---|---|---|
| V1 | 4 | e-i da ADOPTAR con P2 en PIERDE, hasta ~50 publicaciones de más en V375 y 18 a 20 en V750 por muy pocas alertas | la recomendación pasa a e-ii; e-i queda como opción con la región escrita (§6.5) |
| V2 | 3 | las publicaciones en «otra» no entraban a ninguna regla; 789 RUTINA diurnas eran «otra» sólo por una alerta nocturna del mismo día UTC | negativo por periodo (§4, `banderas_por_periodo`); «otra» baja de 1.024 a 265 en V375 y de 270 a 60 en V750 |
| V3 | 3 | faltaban las variantes de mínimas que pide MISSION, M4 por ventana, elevación solar, el instrumento 1.13 sobre lo nuestro | implementadas como informativas (§6.4, §7); M4 por ventana y `P_1mw` en la salida |
| V4 | 3 | «SIN DATO» de la geometría de reflejo es falso: los records traen los cuatro ángulos | corregido (§2.2); variante informativa con el filtro de 12° (§7) |
| V5 | 2 | la variante sin reflejo volvía negativas a 12 pasadas vecinas | las excluidas salen después de marcar los días (§6.4) |
| V6 | 2 | I5 no exigía los mismos records nocturnos | I5 los exige (§5) |
| V7 | 2 | más días parciales en la tabla que los declarados; 78 negativos de W6 sin noche | declarado (§3); con el negativo por periodo dejan de depender de la noche |
| V8 | 2 | recuperar es publicar con cualquier magnitud | declarado (§4) y `P_1mw` informado |
| V9 | 2 | I6 e I2 casi no pueden fallar en el caso en que se adopta | declarado como límite (§5, I6) |
| V10 | 2 | I4c tolera 6 y 21 pasadas sin record y no vigila las alertas bajo 1 MW una a una | I4a vigila toda alerta diurna; tolerancia escrita (§5) |
| V11 | 1 | D supone independencia y las alertas se agrupan | declarado como límite (§6.2) |
| V12 | 1 | líneas del `.m` corridas en uno; «12 positivos» eran 13; «41 de 41» frente a «41 de 42» en la salida | corregido (§2.2, §3, §5.2) |
| V13 | 1 | valores por defecto del workflow son los de C0; los sha256 son de los blobs, no del árbol con CRLF | declarado (§8) |

Como la regla cambió (opción recomendada, definición de negativo, I4a, I5), la v2 **necesita su propia verificación
limpia** antes del sello (lección S162: una regla corregida se re-verifica).


## 13. Segunda verificación limpia (de la v2) y qué cambió en la v3 (2026-10-26)

Otra instancia de Sonnet 5.5, sin la conversación ni el informe de la primera hasta después de escribir su lista de
caminos (`verificador_v2/CAMINOS.md`); commit verificado `bf8e24dd`. Resultado: los arreglos del §12 hacen lo que dicen
(11 CONFIRMADO, 2 CONFIRMADO EN PARTE: V3, que no decía si las mínimas cambiaban el veredicto, y V7); el nulo se
reproduce idéntico; 48 de 48 mutaciones atrapadas en una copia aparte; batería 65 de 65; sha256 de los blobs 16 de 16;
cifras del §3 y la Tabla 1 renderizada, confirmadas. **No encontró un camino por el que un brazo al azar o callado salga
ADOPTAR**: con tasas de 0,01 % a 0,5 % un brazo al azar adopta como máximo 0,42 % de las veces (VIIRS 375) y 0,09 %
(VIIRS 750). Hallazgos nuevos y qué se hizo:

| ID | gravedad | hallazgo | qué se hizo |
|---|---|---|---|
| V-N1 | 3 | el predicado «publica» (`frontend/index.html`) y otras dependencias no estaban sellados | sellados en `objetivos_sha256.txt`; la evaluación corre desde un `git archive` del commit sellado (§8) |
| V-N2 | 3 | `main()`, las variantes, la vara de cobertura y el cargador no tenían prueba: 7 mutaciones suyas sobrevivían | `main()` partido en `evaluar_completo`, `p_sup_de_vara` y `pasadas_de`; 12 pruebas nuevas; las 7 mutaciones del verificador entran a `mutaciones.json` |
| V-N3 | 2 | el placebo c contaba dos colas con el umbral de una: INDECIDIBLE 16 a 23 % de las veces | umbral a 8 de 40 con la tasa de dos colas (§5, I6) |
| V-N4 | 2 | el caso b adoptaba con 60 publicaciones en «otra» | variante (d) «otra como negativo» en la robustez (§6.4) |
| V-N5 | 2 | I5 compara menos que la G3 que reemplaza | decide con publicación y magnitud; el record entero se informa (§5, I5) |
| V-N6 | 2 | I3 se tapaba con un record diurno | I3 cuenta sólo records nocturnos (§5) |
| V-N7 | 2 | para VIIRS 750 manda el código de MIROVA y la rama diurna usa la Tabla 1 | un ADOPTAR de VIIRS 750 pasa a DECIDE NICOLÁS (§2.2, §6.3) |
| V-N8 | 1 | el filtro de 12° probablemente no cambia nada | declarado (§2.2); la variante informativa se mantiene |
| V-N9 | 1 | la salida no decía si las mínimas cambian el veredicto; el costo no se deriva de sus cifras; 10 de 200 no certifica 5 % | la salida lo dice; el costo explica su derivación (§8); e-i ya no es la recomendada |

Esta v3 cambia tres cosas de la regla (umbral del placebo c, VIIRS 750, variante d), todas en la dirección de no adoptar
de más. Están cubiertas por pruebas y mutaciones (§5.2) y se le pide a un tercer verificador limpio que mire sólo ese
diff contra la v2 (`verificador_v3/`).


## 14. Tercera verificación limpia (del diff de la v2 a la v3) y la v3.1 (2026-10-26)

Otra instancia de Sonnet 5.5, acotada al diff `bf8e24dd..987a7601`, con su lista de caminos escrita antes de abrir el
diff (`verificador_v3/CAMINOS.md`). **No encontró ningún camino por el que la v3 adopte algo que la v2 no adoptaba**;
`main()` refactorizado da la misma salida que el de la v2 en dos corridas completas, salvo lo declarado; el umbral del
placebo c está bien calibrado; la matriz de 16 pares de §6.3 coincide; 78 de 78 pruebas y 62 de 62 mutaciones
atrapadas en una copia del commit. Hallazgos (0 de gravedad 3 o más):

| ID | gravedad | hallazgo | qué se hizo en la v3.1 |
|---|---|---|---|
| V3-1 | 2 | la variante d no incluía las pasadas FALSO_POSITIVO diurnas propias | las incluye (§6.4); prueba con el escenario del verificador v2 y mutación M57 |
| V3-2 | 2 | siete archivos que el evaluador lee no estaban sellados; el `git diff` del §8 cubría tres rutas | sellados (29 rutas en `objetivos_sha256.txt`); el `git diff` del §8 recorre todas |
| V3-3 | 2 | el brazo perfecto da DECIDE NICOLÁS global por la regla de VIIRS 750 | declarado en §5.1 (iii) y §6.3 |
| V3-4 | 1 | el placebo c permitía 7 GANA y 0 PIERDE | tope propio de GANA, 5 de 40 (§5, I6); mutaciones M58 y M59 |
| V3-5 | 1 | `main()` sin prueba directa (argumentos, impresión, W1) | declarado: la lógica que decide está en `evaluar_completo`, probada; lo que queda es lectura de argumentos e impresión, y la sección de W1, que no decide |
| V3-6 | 1 | (menores del informe) | sin cambio |

Batería de la v3.1: 80 pruebas en verde. Mutaciones nuevas de la v3.1: 3 de 3 atrapadas (`mutaciones_v31_salida.txt`)
y agregadas a `mutaciones.json`; la corrida completa sobre la v3.1 no se repitió (la del verificador v3 sobre la v3
dio 62 de 62).

**Incidente de máquina:** el verificador v3 cuenta que, al buscar sus procesos para detenerlos, terminó por error tres
procesos de Python con `evaluar_diurno_k.py` en la línea de comandos; eran los suyos, pero no descarta que alguno fuera
de otra sesión.
