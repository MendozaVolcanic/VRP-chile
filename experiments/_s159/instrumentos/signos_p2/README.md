# P2 con la prueba de signos por bloque (D-45): implementación, candados, placebos y mediciones

Vara: `experiments/_s157_prereg_d25/ADENDA_SIGNOS_P2.md` (quinta adenda, sellada por Nicolás el 2026-10-22, commit
`c13cf5808`). Todo con datos sintéticos o con brazos armados desde producción (`sustrato_k.unir_k`); nada del A/B: no
se corrió el evaluador sobre V1, V2a, V2b, el brazo del 17 al 19 ni ningún artefacto de esos runs. El veredicto de D25
no se leyó. Todas las rutas de abajo son relativas a esta carpeta,
`C:\vrp-trabajo\s159-evaluador\experiments\_s159\instrumentos\signos_p2\`, salvo que digan otra cosa.

## Estado

1. Pruebas nuevas, rojas contra `c13cf5808`: hecho (commit `da5e895c7`).
2. Implementación: hecha (commit `c8a000602`).
3. Candados: ver «Mutaciones».
4. Verdes con el árbol quieto: ver «Verdes».
5. Placebos: hechos (commit `625235ffe`).
6. Mediciones sintéticas: hechas (commit `2538e6e87`).

El computador se reinició el 2026-10-23 a las 13:21 UTC con los placebos y las mutaciones corriendo. Los placebos se
reanudaron leyendo las semillas ya escritas en cada JSONL (ver «Placebos»); las mutaciones, que hasta ese momento sólo
guardaban su resultado al final, se re-corrieron con un corredor que anota cada mutación al terminarla.

## Qué cambió en `experiments/_s157_prereg_d25/evaluar_d25.py`

- Constantes selladas, con su origen en el comentario: `SEMILLA_P2_SIGNOS = SEMILLA + 5` (162), `N_SORTEOS_P2_SIGNOS =
  10000`, `MAX_B_EXACTO_P2 = 20`, `MAX_B_SIN_SUSTRATO_P2 = 4`, `TOPE_P2_DEN = 20` (el 5 % como 1/20, para comparar en
  enteros) y `REGLA_P2` (el texto de la regla que decide, con «D-45»).
- `prueba_signos_p2(sumas, neto, n_sorteos, semilla)`: §2.3 a §2.5. Con B de 20 o menos cuenta los 2^B repartos
  agrupados por su suma (convolución con enteros de Python: cada bloque duplica los repartos, uno con +s y otro con -s,
  así que el conteo es exactamente el de la enumeración; las pruebas lo comparan con una enumeración bit a bit hecha
  aparte). Con B de 21 o más, 10.000 sorteos de signos por bloque, en el orden de la clave del bloque, con
  `np.random.default_rng(162).choice((-1, 1), size=(10000, B))`, y valor-p (1 + m) / 10.001. Devuelve cada valor-p como
  fracción de enteros, el método, el p mínimo y la semilla y los sorteos que se usaron de verdad.
- `regla_signos_p2(neto, B, pr)`: §2.6 y §2.7, con la comparación en enteros (`20 * k <= denominador`).
- `informar_d34_d42(c, bl_p2, neto, ok_ctrl)`: §3. Lo que antes decidía (intervalo de D-34 y su calibración de D-42) se
  sigue calculando con la misma semilla, sorteos y tope, y se informa: `resultado_sin_calibrar` e `ic95` (D-34),
  `resultado_d42` (lo que D-42 habría decidido) y los campos de D-42 §2.7.
- `decidir_p2_bloques`: arma las sumas por bloque noche-volcán (la misma clave de `contribuciones_p2`; B cuenta también
  los bloques de suma 0), llama a la prueba y a la regla, devuelve INDECIDIBLE sólo con los controles caídos (§2.8), y
  deja en el detalle lo de §4: `neto`, `B`, `bloques_suma_no_nula`, `sumas_bloque` (ordenadas), `p_gana`, `p_pierde`,
  `p_dos_colas` (y cada uno como `*_fraccion` en enteros), `metodo`, `p_minimo` (y `p_minimo_fraccion`),
  `semilla_signos`, `n_sorteos_signos`, `tope_p2`, `regla`, más lo de §3. La lista de discordantes no cambia.
- `imprimir`: la línea de P2 dice «D-45, prueba de signos por bloque» con valores-p, método, p mínimo, semilla y
  sorteos; una línea con las sumas de bloque y otra con D-34 y D-42 («informan, no deciden»).
- `contar`, `global_ventana` y `combinar` no cambian (§2.9).
- La mutación equivalente «5 % o menos» contra «menos del 5 %» (§5) se declara en el docstring de `regla_signos_p2`.

## LECTURAS (lo que la adenda no fija y el código tuvo que decidir)

1. **D-34 y D-42 se informan con su PROPIO mínimo** (D-34 §5.6: menos de 5 pasadas o menos de 3 noches, SIN
   SUSTRATO), no con el de D-45, porque §3 pide informarlas para ver «si el cambio de regla cambia el veredicto», y eso
   es lo que cada una habría dado. Ejemplo: 3 noches de 4 pasadas son SIN SUSTRATO para D-45 (B = 3), pero D-34 da
   PIERDE y D-42 INDECIDIBLE, y así se informa. Con los controles caídos no se calculan (como en D-42).
2. **Los campos de la prueba de signos se calculan siempre**, también con SIN SUSTRATO y con los controles caídos
   («Siempre que P2 se calcule», §4); ahí no deciden.
3. **El p mínimo con sorteos** se informa como 1 / 10.001 (el que deja el +1); §4 sólo lo nombra para el exacto.
4. **El valor-p a dos colas** (informa, no decide) es la fracción de repartos con |suma| >= |neto|; por sorteos,
   (1 + m) / 10.001 con el mismo criterio.
5. **El placebo (c), «(todas se apagan o todas se encienden)»**: lo que fija el nulo de §2.3 es el SIGNO común de la
   noche, y una noche con signo +1 puede apagar una alerta y encender un negativo a la vez. Se siguió el signo. Para que
   el nulo del placebo sea exactamente el de §2.3, el tamaño de lo que se toca en una noche se fija ANTES de tirar su
   moneda y tiene que poder salir con los dos signos: una noche es elegible si tiene pasadas de los dos lados; se toca
   t = min(lado +1, lado -1, lo que falta para el objetivo); el objetivo de pasadas es el de D-44 (round(2 p M)). Con K
   el lado -1 es escaso, así que casi todas las noches tocadas tienen t = 1 y faltan pasadas para el objetivo en
   algunos puntos (ver «Placebos»).
6. **«Supera el 5 % en una cola» en (c)** (§6): la adenda no dice si se mira por punto y sensor, por punto o sobre todo
   (c). Se informan los tres niveles; ver «Placebos». No lo decido yo.

## Pruebas rojas

`rojo_signos_p2.py` copia el evaluador de `c13cf5808` (idéntico al de `bcfdc7c76`, que nombra la adenda: `c13cf5808`
sólo agrega la adenda) a `experiments/_mut_rojo/`, corre `tests/test_evaluar_d25_signos_p2_s161.py` con
`D25_EVALUADOR_DIR` apuntando ahí y clasifica cada falla leyendo el XML de JUnit. Las pruebas no se editaron después de
la roja. Salida: `rojo_signos_p2.txt` y `rojo_signos_p2.xml`.

**31 pruebas, 31 fallan, las 31 por `AssertionError`, 0 por otra excepción, 0 errores.** Casi todas fallan en la misma
primera aserción (el detalle no trae `B`, o falta la constante o la función): la roja prueba que miran algo que no
existía; qué miran de verdad lo dicen las mutaciones. Ninguna prueba nueva pasa en rojo.

Las 31 (`tests/test_evaluar_d25_signos_p2_s161.py`): constantes; 7 noches del mismo lado deciden con p = 1/128 (dos
direcciones); 6 contra 1 no deciden (8/128, dos direcciones); 5 noches deciden a una cola (1/32, dos direcciones); la
dirección de cada cola contra una enumeración; 4 noches SIN SUSTRATO (dos signos); B con los bloques de suma 0; signo
por bloque en el exacto; B = 20 exacto contra la enumeración bit a bit; B = 21 contra el sorteo repetido con 162 y
10.000; la semilla y los sorteos que se usaron (monkeypatch); signo por bloque en los sorteos; neto 0 es EMPATE;
BLOQUEA con neto 2 (386/1024); 12 noches deciden en las dos direcciones; controles caídos; la regla dice D-45; D-34 y
D-42 informados contra un oráculo de D-34; D-42 calibrada informa; D-34 y D-42 con su propio mínimo (dos casos); el
multiconjunto de sumas; `contar` publica D-45 y la ventana lo lee; `contar` no publica D-34; `imprimir`; dos de punta
a punta sobre brazos desde producción (Láscar y Villarrica, 2026-10-01 a 10-12, D con todas las publicaciones de
VIIRS 375 de K apagadas).

## Candados de D-42 re-apuntados (`tests/test_evaluar_d25_calib_p2_s160.py`)

Con D-45 la calibración de D-42 deja de decidir; estas cuatro pruebas miraban sólo la DECISIÓN de D-42 y fallaban con
el código nuevo. Ninguna se retiró: se re-apuntaron al campo que ahora la informa (`resultado_d42`) y fijan aparte lo
que decide D-45. Una por una:

1. `test_el_sorteo_es_por_bloque_y_no_por_pasada`: pedía P2 INDECIDIBLE con 3 noches de 4 pasadas. Ahora pide
   `resultado_d42 == INDECIDIBLE` y P2 SIN SUSTRATO (B = 3). Además pregunta si los falsos de D-42 vienen antes de
   compararlos (sin eso, la mutación s12c caía por `TypeError` en vez de aserción; cambio hecho después del primer
   tramo de mutaciones, ver «Mutaciones»).
2. `test_el_tope_es_5_por_ciento_en_cada_cola` (5 casos): pedía GANA o INDECIDIBLE según la calibración forzada. Ahora
   lo pide en `resultado_d42`, y P2 GANA siempre (12 noches, p = 1/4096).
3. `test_si_la_calibracion_falla_queda_indecidible_sea_cual_sea_el_resultado` (4 casos): pedía INDECIDIBLE. Ahora lo
   pide en `resultado_d42`, y P2 igual a lo que da D-45 (en estos cuatro conjuntos coincide con D-34 sin calibrar).
4. `test_contar_publica_el_veredicto_calibrado_y_no_el_sin_calibrar`: pedía que `contar` publicara el INDECIDIBLE de
   D-42. Ahora pide `resultado_d42 == INDECIDIBLE` en el detalle, que `contar` publique SIN SUSTRATO (D-45) y que la
   ventana no quede INDECIDIBLE por P2. El candado de V42-02 para la regla nueva vive en las dos pruebas de `contar` del
   archivo de S161.

Dos más, que seguían pasando, ganaron una aserción sobre `resultado_d42` (`test_bloquea_no_se_calibra...` y
`test_con_muchas_noches...`). Las demás de D-42 (semilla, sorteos, oráculo, tope en `calibrada`, el detalle de V42-04,
sin sustrato y controles caídos) no cambiaron: siguen vigilando lo que se informa.
`test_global_ventana_con_p2_indecidible` y la lectura pendiente de V42-03 no cambian (§2.9).

## Mutaciones

MUTACIONES_PENDIENTE

## Verdes

VERDES_PENDIENTE

## Placebos (§6)

Brazos desde producción con `sustrato_k.unir_k`, como en D-44; el evaluador sin M (`evaluar_sin_m.py`, copia sin
cambios del de D-44: P2 se decide antes que M y no lee nada de M). `placebo_signos.py` es la copia de `placebo_d44.py`
con (c) por noche (LECTURA 5) y el detalle de D-45 en cada fila. Celda = semilla × sensor; original y SN dieron lo mismo
en todas las filas (las clases se eligen iguales en las dos reglas). Resumen: `resumir_signos.py` → `resumen_signos.txt`.
Filas crudas: `placebo_<a|b|c>_<V1|V2>.jsonl` (salida de cada corrida en `placebo_*_salida.txt`).

- **Semillas, fijadas antes de correr y sin ampliar**: (a) y (b) con las de D-44 (0 a 19 por punto, una sola corrida
  con el 100 %), fracciones 10, 25, 50 y 100 % en V1 y V2; (c) con 40 por punto (0 a 39), fracciones 25 y 50 % en V1 y
  V2. En total 404 corridas válidas, no 480: (c) son 40 × 2 puntos × 2 ventanas = 160; (a) y (b) no son 20 × 4 × 2 =
  160 cada uno porque en el punto del 100 % todas las semillas apagan exactamente lo mismo (todo el pozo), así que, igual
  que en D-44 (`placebo_d44.py`: «con el 100 % todas las semillas apagan lo mismo: una sola corrida»), ese punto lleva
  una sola corrida (semilla 0): (20 × 3 + 1) × 2 ventanas = 122 en (a) y 122 en (b), y 160 + 122 + 122 = 404. Las 404
  están en los JSONL (`resumen_signos.txt`: 20, 20, 20 y 1 semillas por punto en (a) y (b); 40 y 40 en (c)). Con la misma semilla, (a) y (b) apagaron exactamente lo mismo que en D-44 en todas
  sus filas (mismo número y misma clase, «mismas apagadas pedidas» en `resumen_signos.txt`).
- **Reanudación**: el reinicio cortó las seis tandas; `placebo_signos.py` lee el JSONL, salta las semillas que ya tienen
  fila completa y vuelve a correr las caídas (cada semilla tiene su propio generador, `random.Random(10000 f + s)`, así
  que saltar una no cambia las demás). Dos corridas habían quedado caídas por el corte (V1 (a) 50 % semilla 8; V1 (c)
  50 % semilla 3); se re-corrieron con su misma semilla y el resumen cuenta la completa. Horas: `placebos_inicio.txt` y
  `placebos_reanudacion_inicio.txt`.
- **(a) y (b) se re-corrieron, no se re-decidieron**: los JSONL de D-44 guardan neto, pasadas y noches, pero no las
  sumas de bloque, y el valor-p de D-45 depende de ellas.
- En las 404, todo lo tocado llegó a la tabla y ninguna otra pasada cambió.

### (a) poder: GANA donde hay sustrato

Con sustrato (B >= 5): **GANA en todas las celdas**, 0 en la dirección equivocada. V1: 50 % VIIRS 375 y 750 (20 de 20
cada uno) y 100 % los dos sensores. V2: 25 % VIIRS 375 (20 de 20), 50 % VIIRS 375 y 750 (20 de 20 cada uno) y 100 % los
dos. Lo que cambia contra D-42: en V2 50 % D-42 dejaba INDECIDIBLE 9 de 20 en VIIRS 375 y 5 de 20 en VIIRS 750, y en V1
100 % VIIRS 375; D-45 decide GANA en todas. Sin sustrato (B <= 4, SIN SUSTRATO): V1 10 % y 25 %, V2 10 %, V2 25 %
VIIRS 750.

### (b) dirección: PIERDE donde hay sustrato

Con sustrato: **PIERDE en todas las celdas**, 0 GANA. V1: VIIRS 375 en 10, 25, 50 y 100 %; VIIRS 750 en 100 % (B = 7,
donde D-42 daba INDECIDIBLE). V2: los dos sensores en 10, 25, 50 y 100 %. D-42 dejaba INDECIDIBLE 4 de 20 en V1 10 % y
1 de 20 en V1 25 % (VIIRS 375). Sin sustrato: V1 VIIRS 750 en 10, 25 y 50 %.

### (c) simétrico por noche: falsos por cola

Las noches tocadas tienen casi todas t = 1 (en V2, todas; en V1, 18 de 662 con t = 2 al 25 % y 40 de 920 al 50 %),
porque con K el lado -1 es escaso por noche. Faltaron pasadas para el objetivo en V1 50 % (40 en VIIRS 375 y 400 en
VIIRS 750, sumadas sobre las 40 semillas), V2 25 % VIIRS 750 (120) y V2 50 % (240 y 880): se acabaron las noches
elegibles. La media del neto queda cerca de 0 en los ocho casos (de -0,65 a +0,60, con desvíos de 2,5 a 5,2). Todas las
celdas tienen B >= 5. «Esperado» es la tasa EXACTA bajo el nulo de §2.3 para las magnitudes de bloque de esas celdas,
sin el ruido de los signos.

| punto | sensor | GANA | PIERDE | esperado por cola |
|---|---|---|---|---|
| V1 25 % | VIIRS 375 | 1/40 (2,5 % [0,4; 12,9]) | 0/40 | 1,1 % |
| V1 25 % | VIIRS 750 | 0/40 | 0/40 | 1,1 % |
| V1 50 % | VIIRS 375 | 0/40 | 0/40 | 1,7 % |
| V1 50 % | VIIRS 750 | 2/40 (5,0 % [1,4; 16,5]) | 0/40 | 3,3 % |
| V2 25 % | VIIRS 375 | 1/40 (2,5 %) | 0/40 | 1,8 % |
| V2 25 % | VIIRS 750 | 0/40 | 0/40 | 2,5 % |
| V2 50 % | VIIRS 375 | **3/40 (7,5 % [2,6; 19,9])** | 2/40 (5,0 % [1,4; 16,5]) | 3,2 % (aproximado: B = 24, sorteos) |
| V2 50 % | VIIRS 750 | 1/40 (2,5 %) | 2/40 (5,0 % [1,4; 16,5]) | 2,5 % |

Por punto, los dos sensores juntos: V1 25 % GANA 1/80 (1,2 %), PIERDE 0/80; V1 50 % 2/80 (2,5 %) y 0/80; V2 25 % 1/80 y
0/80; **V2 50 % 4/80 (5,0 % [2,0; 12,2]) y 4/80 (5,0 %)**. **Total de (c): GANA 8/320 (2,5 % [1,3; 4,9]), PIERDE 4/320
(1,2 % [0,5; 3,2])**; esperado exacto 2,1 % por cola.

**Lo que hay que decidir (LECTURA 6).** Sobre todo (c) y por punto, ninguna cola pasa del 5 %. En **un** punto y sensor
(V2 50 % VIIRS 375) la estimación puntual de GANA es 7,5 % (3 de 40), con un intervalo que contiene el 5 % y una tasa
exacta esperada para esas magnitudes de 3,2 %; ver 3 o más de 40 con esa tasa tiene probabilidad 0,136 (binomial,
`binomial_v2_50.txt`), compatible con ruido de 40 semillas, que no se ampliaron (V42-22). **Si la vara se lee por punto y
sensor, (c) supera el 5 % en una cola, y la adenda manda devolverlo a Nicolás antes del tag.**

## Mediciones sintéticas (§7), con la función real

`medir_signos_p2.py`, salidas `medir_*.txt`.

**Tasa exacta de falsos por cola con bloques de suma ±1, B de 5 a 20** (`medir_bpm.txt`): todas en 5 % o menos. B = 5:
1/32; 6: 1/64; 7: 1/128 (0,78 %); 8: 9/256 (3,5 %); 9: 1,95 %; 10: 1,07 %; 11: 3,27 %; 12: 1,93 %; 13: 4,61 %; 14:
2,87 %; 15: 1,76 %; 16: 3,84 %; 17: 2,45 %; 18: **4,81 %** (la más alta); 19: 3,18 %; 20: 2,07 %. Las dos colas dan lo
mismo en cada B. Control: para B de 5 a 14 se recorrieron además los 2^B repartos uno por uno y el conteo dio IGUAL en
los diez. La columna de D-34 sin calibrar reproduce el 6,25 % de B = 7 (V42-20).

**El caso de V42-20** (`medir_v4220.txt`): 7 noches de +1, D-45 PIERDE con p = 1/128 (D-34 PIERDE, D-42 INDECIDIBLE); 7
de -1, GANA con 1/128; 6 contra 1, BLOQUEA o EMPATE con p = 1/16 (= 8/128; D-34 decidía PIERDE o GANA, D-42
INDECIDIBLE).

**Nulos enumerables** (`medir_enumerables.txt`, todas las combinaciones): D-45 cumple 5 % por cola en los siete. B2
1,56 %; B7 3,12 %; B8 3,52 %; B9 0,10 %; B4, B5 y B6 son SIN SUSTRATO (3 y 4 noches), donde D-42 daba INDECIDIBLE
(25 %, 100 % y 100 %) y D-34 sin calibrar 3,1 %, 12,5 % y 6,25 % por cola.

**Escenarios de V34-01 y de `calib_p2/cobertura_p2_calibrada.py`** (500 conjuntos, semillas 0 a 499,
`medir_escenarios_*.txt`), D-45 al lado de D-42; «esperado» de `medir_esperado_escenarios.txt`:

| escenario | D-45 GANA | D-45 PIERDE | D-42 GANA | D-42 PIERDE | D-42 INDECIDIBLE | D-45 esperado por cola |
|---|---|---|---|---|---|---|
| A nulo iid, 12 × 3 | 3,0 % | 6,0 % [4,2; 8,4] | 2,0 % | 5,4 % | 5,0 % | 3,7 % |
| B nulo por noche, 12 × 4 | 1,2 % | 2,6 % | 1,2 % | 2,6 % | 0 | 1,9 % |
| B2 por noche, 6 × 6 | 1,2 % | 3,4 % | 1,2 % | 3,4 % | 0 | 1,6 % |
| B3 iid, noches desiguales | 3,8 % | 4,8 % | 1,8 % | 2,0 % | 32,4 % | 3,9 % |
| B4 iid, 3 noches | SIN SUSTRATO 100 % | | 0 | 0 | 27,6 % | 0 |
| B5 por noche, 3 × 2 | SIN SUSTRATO 100 % | | 0 | 0 | 100 % | 0 |
| B6 por noche, 4 × 2 | SIN SUSTRATO 100 % | | 0 | 0 | 100 % | 0 |
| B7 por noche, 5 × 2 | 2,6 % | 6,0 % [4,2; 8,4] | 2,6 % | 6,0 % | 0 | 3,1 % |
| B8 por noche, 8 × 2 | 1,8 % | 6,6 % [4,7; 9,1] | 1,8 % | 6,6 % | 2,6 % | 3,5 % |
| C efecto grande a favor | GANA 99,4 % | | 98,8 % | | 0,4 % | |
| C2 efecto grande en contra | | PIERDE 99,8 % | | 99,8 % | 0 | |
| D efecto moderado a favor | GANA 70,6 % | | 68,0 % | | 0,4 % | |
| E efecto por noche | GANA 33,0 % | | 33,0 % | | 0 | |
| F efecto grande, 4 noches × 3 | SIN SUSTRATO 100 % | | 0 | | 100 % | |
| F2 efecto total, 5 noches × 2 | GANA 100 % | | 100 % | | 0 | |

Las tres celdas sobre 5 % en una cola (A, B7 y B8 PIERDE) son de la muestra de semillas 0 a 499, no de la regla: para
las magnitudes de esos mismos 500 conjuntos la tasa exacta es 3,7 %, 3,1 % y 3,5 % por cola, y B7 y B8 enumerados dan
3,12 % y 3,52 %. Es el mismo exceso de PIERDE que ya tenía esa muestra con D-42 (README de `calib_p2`, V42-05).

**Poder (§7, último párrafo).** No cae a 0 en el efecto grande: C 99,4 %, C2 99,8 %, F2 100 %, D 70,6 %. Donde es 0 es
F (4 noches): con B <= 4 D-45 da SIN SUSTRATO por regla (§2.7, aceptado a sabiendas en la adenda); antes D-42 lo dejaba
INDECIDIBLE en el 100 %. E (efecto por noche, 10 noches) queda en 33 %, igual que D-42.

## Lo que no hice

- No corrí el evaluador sobre ningún brazo del A/B ni abrí sus resultados; no toqué `pipeline/`, `data/`, `frontend/`
  ni las adendas; no creé ramas, tags ni PRs; no despaché workflows.
- Falta el verificador con contexto limpio antes del tag de lectura (§5).
- Un tropiezo propio, ya limpio: al lanzar las mediciones la primera vez, los procesos en segundo plano corrieron en el
  directorio del checkout principal (`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\`), no
  encontraron el script y dejaron ahí siete archivos `medir_*.txt` con el error; los borré (eran sólo esos, sin
  seguimiento en git) y re-corrí con rutas absolutas.
