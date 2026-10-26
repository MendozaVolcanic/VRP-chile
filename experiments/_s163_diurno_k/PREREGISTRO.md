# Pre-registro del A/B diurno de VIIRS sobre K (tarea 1.32, decisión D-10, issue #813)

Estado: **BORRADOR v1, espera el verificador con contexto limpio y el sello** (2026-10-26, S163, sesión
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

- **K1 diurno -0,5** (l. 190; la Tabla 1 dice -0,6). El resto coincide: multiplicador de σ 15 en las dos ROI, mínimos
  de dNTI y dETI 0,02 (l. 192 a 199).
- **Filtro de reflejo especular** (l. 83 a 89): si el ángulo de reflejo especular de la escena es menor que 12°, MIROVA
  descarta la detección entera. Nuestra rama no lo tiene y los records no guardan la geometría de visión necesaria
  para calcularlo (SIN DATO). Parche propuesto, fuera de este A/B: calcular ese ángulo en `process_viirs_mod.py` y
  `process_viirs.py` con los ángulos solares y de sensor del archivo de geolocalización que el pipeline ya baja (A45:
  tag, TDD, sí de Nicolás).

Para VIIRS 375 no hay código de MIROVA en `main`, y ningún paper da números diurnos de VIIRS: la Tabla 1 es la única
fuente citable. Si el resultado de VIIRS 750 sale con publicaciones de más, el primer candidato a probar es el filtro
de 12° y el K1 de -0,5, en el programa de VIIRS 750 (V750-B), no aquí.

## 3. Ventanas y sustrato

Salida: `sustrato_k_salida.txt` y `sustrato_k.json` (script `sustrato_k.py`). Referencia: la unión del árbol `047bd5692`
(45.355 filas, 2026-01-10 a 2026-10-25), canal unión, regla de mínimas SN (D-9). Clases por pasada diurna VIIRS (§4).

| ventana | fechas (incl.) | volcanes | VIIRS 375: protegidas / alertas < 1 MW / negativos (bloques) / diurnas | VIIRS 750: protegidas / alertas < 1 MW / negativos (bloques) / diurnas | etiqueta que decide (A119) |
|---|---|---|---|---|---|
| W1 | 2026-03-01 a 03-20 | Láscar | 6 / 2 / 0 (0) / 39 | 0 / 0 / 5 (2) / 40 | sólo la tabla (se informa aparte) |
| W2 | 2026-06-13 a 06-30 | 11 Tier A | 11 / 1 / 336 (111) / 585 | 1 / 0 / 543 (172) / 617 | tabla y OCR |
| W3 | 2026-07-20 a 07-31 | 11 Tier A | 1 / 2 / 281 (85) / 425 | 0 / 0 / 385 (124) / 410 | tabla y OCR |
| W4 | 2026-08-13 a 08-31 | 11 Tier A | 5 / 4 / 310 (117) / 546 | 2 / 0 / 459 (183) / 525 | tabla y OCR |
| W5 | 2026-09-01 a 09-20 | 11 Tier A | 4 / 2 / 315 (120) / 579 | 1 / 0 / 484 (195) / 550 | tabla y OCR |
| W6 | 2026-10-01 a 10-14 | 11 Tier A | 5 / 1 / 245 (83) / 412 | 2 / 0 / 352 (127) / 397 | tabla y OCR |
| **W2 a W6** | | | **26 / 10 / 1.487 / 2.547** | **6 / 0 / 2.223 / 2.499** | |

Con la tabla sola, W2 a W6: VIIRS 375, 6 protegidas, 7 alertas bajo 1 MW, 1.539 negativos; VIIRS 750, 2 protegidas, 0
alertas bajo 1 MW, 2.229 negativos. **En W2 la tabla no tiene ninguna alerta diurna**: sus 12 positivos son sólo del
OCR, del tramo en que el OCR recién empezaba a medir la distancia (A119, hito del 2026-06-13).

Notas que pesan:
- **Por qué no hay W7.** La tabla de MIROVA del árbol se corta el 2026-10-19 y tiene huecos el 12 y el 13 de octubre
  (`sustrato_k_salida.txt` no los muestra; se vieron contando pasadas por día). Es el problema de Mirova-v1 que
  investiga otra sesión (D-39). Una ventana nueva espera a que esa referencia esté reparada.
- W1 es anterior al 2026-04-01 (A119: la tabla exponía menos gránulos VIIRS por noche; su tasa por pasada no se suma)
  y sólo trae Láscar. Se corre primero, como job corto para medir la duración (§8), y se informa aparte.
- **Sustrato del criterio bajo 1 MW, de día: casi nada.** Hay 10 alertas diurnas bajo 1 MW en VIIRS 375 y ninguna en
  VIIRS 750, contra 1.487 y 2.223 negativos. El lado «alertas bajo 1 MW» del criterio apenas puede pesar; lo que
  decide en la práctica es cuántas protegidas recupera el brazo contra cuántas publicaciones agrega (§6, caso e).
  Se dice ahora para que nadie lo descubra en el resultado.
- El pareo es por volcán, sensor y hora (±120 s, `clase_mirova.VENTANA_S`), **nunca** por la distancia del OCR.

**Contexto de la noche de producción, no vara** (`nulo_estructural_salida.txt`, líneas «control»; producción es K en
todo el histórico desde #883 y ahí hace de control, con las funciones del mismo evaluador): en las mismas ventanas, de
noche, producción publica en el **3,51 %** de los negativos limpios de VIIRS 375 y en el **0,94 %** de los de VIIRS
750. Ese es el orden de magnitud de Q_n que la opción e-i usará como vara; la vara que decide es la del control del
A/B.

## 4. Unidad, clases y métricas

Unidad: la **pasada** de MIROVA (`clase_mirova.resumir_pasadas`). «Publica» = el predicado del tablero
(`isValidDetection` de `frontend/index.html`) corrido con node (`banco_paridad.correr_node`), nunca uno reconstruido
(A97). Día = elevación solar mayor que 0 sobre el volcán a la hora de la pasada (`pipeline.store._solar_elevation`,
la misma regla del pipeline). La tabla por pasada es la de `evaluador_comun.tabla_por_pasada`, armada con las pasadas
de noche y de día juntas, para que «día con alerta» mire el día UTC entero.

Clases de una pasada (las de `evaluador_comun.clase_p2`, con la protegida aparte):
- **protegida**: alerta de 1 MW o más (lectura A, D-4);
- **alerta_mb**: alerta bajo 1 MW (con SN, las de 0,05 MW o menos de VIIRS 375 cuentan como RUTINA, D-9);
- **negativo**: pasada de la TABLA, RUTINA, en un volcán, sensor y día UTC sin ninguna alerta ni FALSO_POSITIVO de
  MIROVA (de noche o de día);
- **otra**: el resto (FALSO_POSITIVO, RUTINA en un día con alerta, sólo OCR sin alerta, sin geometría). No entra al
  criterio; las publicaciones del brazo ahí se informan.

El control no publica de día por construcción (`store.py` rechaza el VIIRS diurno con el flag apagado). En cada
pasada diurna que el brazo observó, el estado del control se toma como «observado, no publica», **sólo después** de
comprobar que el control trae cero records VIIRS diurnos (compuerta I2). Así el evaluador común puede contar
discordancias sin inventar un record.

Métricas, por sensor (VIIRS 375 y 750):
- **P**: protegidas diurnas que el brazo publica, sobre las observadas.
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
  sensores, control contra brazo, da COBERTURA OK.
- **I4, cobertura diurna contra la referencia.** De día el control no sirve de vara; la vara es la noche de producción.
  (a) Toda protegida diurna VIIRS tiene record del brazo. (b) Ningún volcán, sensor y día con pasadas diurnas de MIROVA
  queda con cero records diurnos del brazo. (c) Si X de las N pasadas diurnas de MIROVA (W2 a W6) no tienen record del
  brazo, falla cuando P(Bin(N, p_sup) ≥ X) < 0,05, con p_sup la cota superior de Clopper-Pearson al 95 % (una cola)
  de la tasa nocturna de producción del sustrato: VIIRS 375, 0 de 2.715 (p_sup = 0,0011); VIIRS 750, 9 de 2.650
  (p_sup = 0,0059). El umbral sale del dato (A115), no se elige.
- **I5, noches intactas** (la G3 de la adenda). Sobre las pasadas nocturnas de los tres sensores observadas por los dos
  brazos: cero discordancias de publicación y cero cruces de 1 MW en las dos direcciones (P1b). Una discordancia da
  INDECIDIBLE con la lista; se repiten esos volcanes en los dos brazos desde el mismo tag. Si reaparece en el mismo
  record, es cableado (INVÁLIDO); si cambia entre intentos, es un desempate que depende de la CPU (S152, D-16, D-22) y
  se usa el intento sin discordancia, declarado como desviación.
- **I6, el criterio puede ver lo que mide.** Los placebos de D-44 (`evaluador_comun.placebo_p2`), armados sobre el
  brazo diurno en las pasadas diurnas de cada sensor: (a) apagar la mitad de sus publicaciones en negativos diurnos
  tiene que dar GANA cuando eso toca 5 bloques o más (si toca menos se informa SIN SUSTRATO); (c) el simétrico por
  bloque, fracción 1, con 40 semillas (161 a 200), no puede dar GANA o PIERDE en 5 o más de 40 (P(Bin(40; 0,05) ≥ 5)
  = 0,048, `binom.sf`). (b), apagar la mitad de sus alertas bajo 1 MW publicadas, se informa: con 10 alertas en VIIRS
  375 y ninguna en 750 casi nunca tendrá sustrato. Además, antes de despachar, el nulo de P2 se midió sobre la
  estructura real de bloques de W2 a W6 con un brazo sintético que publica al azar (§5.1).

### 5.1 Nulo medido antes de despachar

`nulo_estructural.py` (salida en `nulo_estructural_salida.txt`) arma la tabla real de pasadas de W2 a W6 (referencia
congelada; los records nocturnos de producción, que es K desde #883, hacen de control) y le pone encima brazos
diurnos sintéticos que publican cada pasada diurna VIIRS al azar con probabilidad q, sin mirar si es alerta o
negativo, para q de 0,5 %, 2 %, 5 % y 20 %, 200 repeticiones cada una. Lo que tiene que pasar: (i) P2 diurno da GANA
en no más del 5 % de las repeticiones; (ii) el veredicto por sensor da ADOPTAR en no más del 5 %, con e-i y con e-ii;
(iii) control positivo: un brazo que publica exactamente las alertas diurnas de MIROVA y nada más da ADOPTAR en los dos
sensores; (iv) control negativo: un brazo que publica todas las pasadas diurnas da NO ADOPTAR en los dos. Si (i), (iii)
o (iv) fallan, el instrumento no sirve; (ii) por encima de 5 % se informa como debilidad de la regla antes del sello.

**Resultado (2026-10-26, `nulo_estructural_salida.txt`):** (i) GANA en 0 de 200 en las ocho combinaciones de tasa y
sensor. (ii) ADOPTAR con e-ii en 0 de 200 en todas; con e-i, en VIIRS 375 4 de 200 a 0,5 % y a 2 % (2 %), 0 a 5 % y a
20 %; en VIIRS 750 **10 de 200 a 0,5 % (5,0 %, justo en el límite)**, 0 en las demás. Es lo esperable: con D el falso
ADOPTAR queda en el nivel de la prueba D (5 %), y en VIIRS 750, con 6 protegidas y Q_d de 0,5 %, recuperar una sola por
azar ya pasa D. Se declara: **con e-i, un brazo que no discrimina y publica poco puede salir ADOPTAR hasta en 5 % de
las veces**, y ADOPTAR sólo abre el ciclo de adopción (§6.5), donde la R2 por píxel lo vería. (iii) El control
positivo da GANA y ADOPTAR en VIIRS 375 (neto -10, 26 de 26 protegidas) y SIN SUSTRATO con ADOPTAR por el caso b en
VIIRS 750 (6 de 6). (iv) El control negativo da PIERDE y NO ADOPTAR en los dos (D no cumple). Producción, de control,
da Q_n de 3,51 % (de 1.482 negativos nocturnos) en VIIRS 375 y 0,94 % (de 2.335) en VIIRS 750.

### 5.2 Batería, mutaciones y prueba de humo

- **Batería** (`test_evaluar_diurno_k.py`, 58 pruebas): cada caso a a e del §6.2, el §6.3, el §6.4, cada compuerta I1
  a I6 con un escenario que la hace fallar, la definición de negativo, el control sintético, R1, Q_n del control, la
  prueba D, el borde de 1 MW y la lectura de los logs. Se escribió antes del evaluador: contra un stub fallaron las 53
  que había entonces (`probar_salida_roja.txt`).
- **Mutaciones** (`mutaciones.json`, corredor `experiments/_s162_instrumento/mutar.py`, que cuenta como atrapada sólo
  la que falla por aserción según el JUnit, nunca por excepción): **41 de 41 atrapadas por aserción** (`mutaciones_salida.txt`, segunda corrida; la primera dio 37 de 41 y las cuatro
  vivas o caídas se cerraron con aserciones nuevas: borde de la cola de I4c, sha abreviado que fallaba por excepción, P2
  diurno que contaba la noche, P que contaba alertas bajo 1 MW). La mutación de control
  `C-CAIDA` (el evaluador lanza una excepción) sale como CAÍDA y no como atrapada, que es lo que tiene que pasar.
- **Prueba de humo sobre datos reales** (`humo_c0_W6b_salida.txt`): el evaluador corrido sobre una corrida real del
  A/B sobre C0 (W6b, run 39097155412) con `--recorte`. Sale INVÁLIDO POR INSTRUMENTO por I1 (los flags y los records son
  de C0, con Test 1), que es lo correcto, y con métricas distintas de cero: de día C0 publicaba en 109 de 121
  negativos de VIIRS 375 y recuperaba 5 de 5 alertas, con D sin cumplir (no discrimina), que es el resultado conocido
  de esa corrida. Muestra que la carga, el predicado del tablero y
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
adenda, binomial exacta y sin barajado. **Por qué hace falta**: sin D, un brazo que publica al azar a una tasa baja
saldría ADOPTAR en el caso e-i cada vez que atrapa una protegida por suerte: con 26 protegidas diurnas en VIIRS 375 y
una tasa de 0,5 %, la probabilidad de atrapar al menos una es 1 - 0,995^26 = 12 % (cálculo directo). Con D, el nulo
del §5.1 mide cuánto queda.

| caso | condición | veredicto del sensor |
|---|---|---|
| a | P2 da GANA | ADOPTAR |
| b | neto ≤ 0, P ≥ 1 y D cumple | ADOPTAR (no empeora bajo 1 MW y recupera protegidas más allá del azar) |
| c | neto ≤ 0 y (P = 0 o D no cumple) | SIN CAMBIO si el brazo no publica ninguna pasada diurna del sensor; si publica alguna, NO ADOPTAR (sin beneficio demostrado) |
| d | neto > 0 y (P = 0 o D no cumple) | NO ADOPTAR |
| e | neto > 0, P ≥ 1 y D cumple | **opción del sello**, §6.5: e-i (recomendada) ADOPTAR si Q_d ≤ Q_n y DECIDE NICOLÁS CON M4 si no; e-ii DECIDE NICOLÁS CON M4 siempre |

El caso e es el probable (§3: 10 alertas diurnas bajo 1 MW contra 1.487 negativos en VIIRS 375). El criterio de
victoria dice que una protegida perdida no tiene compensación y que bajo 1 MW los dos errores pesan igual, pero **no
dice cuánto vale una protegida recuperada contra una publicación de más**, y eso no se inventa (A115). La opción e-i
no inventa una tasa: pide que el día no publique de más en mayor proporción que la noche de K que ya se aceptó (S153,
adopción de K con la regla sellada de antes del resultado).

### 6.3 Veredicto global

La rama diurna abre los dos sensores con un solo flag, así que el veredicto global combina los dos:
- cualquier compuerta I1 a I4 falla: **INVÁLIDO POR INSTRUMENTO**; I5 o I6 fallan: **INDECIDIBLE**;
- R1 encuentra una pérdida con las compuertas en verde: **INVÁLIDO POR INSTRUMENTO** (§6.1);
- algún sensor DECIDE NICOLÁS: **DECIDE NICOLÁS CON M4**;
- un sensor ADOPTAR y el otro NO ADOPTAR: **DECIDE NICOLÁS** (adoptar uno solo pide un flag por sensor, un parche en
  `pipeline/` que va con A45);
- los dos en ADOPTAR o SIN CAMBIO, con al menos un ADOPTAR: **ADOPTAR**;
- los dos en NO ADOPTAR o SIN CAMBIO: **NO ADOPTAR**.

### 6.4 Robustez (cuándo el resultado depende de algo frágil)

El veredicto global se recalcula en tres variantes: (a) **tabla sola**; (b) **sin W2**, la ventana cuyos positivos son
todos del OCR; (c) **sin las protegidas diurnas de reflejo probable** según el estudio 1.13 (`experiments/_s151_alertas_diurnas/real_o_reflejo_filas.json`,
clase desproporcionada o aislada). Si el veredicto principal es ADOPTAR o NO ADOPTAR y alguna variante da otro
veredicto global, el resultado es **DECIDE NICOLÁS**, informando cuál cambió y por qué. Es la regla §3.2 de la adenda
sellada, extendida: cuando el resultado depende del OCR o del reflejo, no se resuelve solo. Las variantes de la regla
de mínimas (SE y original, D-9) se informan sin decidir.

Si D-41 (qué alertas sólo OCR entran al criterio) se decide antes del sello, la variante que D-41 elija pasa a ser el
canal principal y la unión queda como variante.

### 6.5 Opción del sello para el caso e

- **e-i (recomendada): ADOPTAR si Q_d ≤ Q_n; si no, DECIDE NICOLÁS CON M4.** Un pre-registro que en su caso más
  probable termina en «decide Nicolás después de ver los datos» es justo lo que el pre-registro quiere evitar. Q_n es
  una vara medida en la misma corrida (el control, mismas ventanas y volcanes) y ya aceptada al adoptar K. Con
  producción como anticipo: 3,51 % en VIIRS 375 y 0,94 % en VIIRS 750 (§3).
- **e-ii: DECIDE NICOLÁS CON M4 siempre.** Es lo que la regla sellada hace hoy en el caso análogo (G1 y G3 sin G2).

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
- Informativo: las publicaciones diurnas del brazo por elevación solar (0 a 30°, 30 a 60°, más de 60°) y la fracción
  desproporcionada según el instrumento a) del estudio 1.13 aplicado a lo nuestro (magnitud diurna contra la mayor
  publicación nocturna del brazo, mismo volcán y sensor, ±72 h; desproporcionada sobre T = 3,16, el umbral de ese
  estudio).
- El filtro de reflejo especular de MIROVA (12°, §2.2) no se puede reproducir sin la geometría de visión: SIN DATO.

## 8. Despacho (lo que hace la coordinadora después del sello)

- **Workflow**: `.github/workflows/reproc-s151-ab-diurno.yml`, sin cambios. Cumple lo exigido: `"on":` entre comillas
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
  días × (2,2 + 5,5) min por volcán-día ≈ 117 h de runner, es decir **unas 39 h de reloj con `max-parallel: 3`** (unas 20
  con 6), más W1 (menos de 1 h).
- **Cobertura**: leer `cobertura.txt` de cada corrida antes de mirar nada; un job corto se repite con el mismo tag y se
  une (D-13).
- **Objetivos y sus sha256**: `objetivos_sha256.txt` (los blobs de git de cada archivo del que depende el despacho y la
  evaluación). Quien sella, sella esos contenidos; el verificador y la coordinadora comprueban con
  `git diff <commit del sello> -- experiments/_s163_diurno_k/ pipeline/profiles/_s154_ab_diurno_k_*.yaml
  .github/workflows/reproc-s151-ab-diurno.yml` que nada cambió antes del tag.
- **Referencia congelada**: `congelar_referencia.py --commit 047bd5692 --salida <carpeta>` extrae los 4 CSV de ese
  commit; el evaluador exige que sus sha256 sean los de `sustrato_k.json`.

Evaluación:

```bash
python -I experiments/_s163_diurno_k/evaluar_diurno_k.py --raiz <W2> ... --raiz <W6> --w1 <W1> \
  --ref <carpeta congelada> --sha-codigo <40 caracteres> --opcion-e e-i
```

## 9. Lo que este A/B no decide

- Encender la rama diurna en producción (ver §6.5).
- El K1 de -0,5 y el filtro de reflejo de 12° del código de MIROVA de VIIRS 750 (§2.2).
- MODIS de día (`ENABLE_DAYTIME_MODIS`, flag propio, apagado en los dos brazos).
- El resultado sobre C0, que queda como medido.

## 10. Qué tiene que sellar Nicolás

1. Que este pre-registro **reemplaza la regla G1/G2 de la `ADENDA_K.md`** sellada (D-25), conservando ventanas,
   perfiles, workflow, tag y cableado (§0).
2. La **opción del caso e**: e-i (recomendada) o e-ii (§6.5).
3. Que la regla de robustez del §6.4 (tabla sola, sin W2, sin reflejo probable) mande a DECIDE NICOLÁS.
4. Que no haya W7 hasta que la referencia de MIROVA esté reparada (§3).

## 11. Desviaciones registradas después de ver datos

(ninguna)
