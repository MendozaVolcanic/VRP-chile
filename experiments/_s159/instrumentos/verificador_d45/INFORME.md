# Verificador de D-45 (quinta adenda, prueba de signos por bloque): informe

## 1. Encabezado

- Hora del servidor al empezar: `Fri, 23 Oct 2026 18:29:26 GMT` (`gh api -i repos/MendozaVolcanic/VRP-chile`, header Date).
  La hora de cierre va al final del informe.
- Commit medido: `7eb91eb5e` (worktree `C:\vrp-trabajo\s159-evaluador`, rama `s159-evaluador-d25`, arbol limpio al empezar;
  `git status --short` solo mostro las carpetas sin seguimiento de otras sesiones y, durante la medicion, mi carpeta y la
  copia temporal `experiments/_mut_*` del corredor de mutaciones).
- Vara: `experiments/_s157_prereg_d25/ADENDA_SIGNOS_P2.md`, sha256 `28eea84cf77b860a2aad12088e6ad6795c8ce3d1395a71890dabe0b3fba900c3`
  (coincide con el sellado; medido con `sha256sum`), mas `NOTA_D46.md`. El evaluador de `c13cf5808` es identico al de
  `bcfdc7c76` (`git diff --stat bcfdc7c76 c13cf5808 -- experiments/_s157_prereg_d25/evaluar_d25.py` vacio), asi que las
  rojas contra `c13cf5808` valen como rojas contra `bcfdc7c76` (adenda §5).
- Modelo y esfuerzo: Claude Fable 5.1, esfuerzo medio, con contexto limpio (sin leer el README del implementador antes de
  los veredictos; `caminos.md` escrito y sellado antes de abrir ningun archivo citado).
- CARPETA: `C:\vrp-trabajo\s159-evaluador\experiments\_s159\instrumentos\verificador_d45\`. Instrumentos y salidas:
  `caminos.md`, `verif_matematica.py` (+ `_salida.txt`), `verif_placebos.py` (+ `_salida.txt`), `mutaciones_propias.py`
  (+ `_salida.txt`, `_salida.json`), `rojo_rerun_verif45.xml`, `verif_extras_salida.txt`, `hallazgos.csv`.
- Lo que NO mire: ningun brazo del A/B (V1, V2a, V2b, el brazo del 17 al 19, run 39756261926, ramas `s146-ab/*`) ni sus
  resultados; `evaluar_fk.py` y `banco_paridad.py` (son vara, no objeto); el README de `signos_p2`, `calib_p2` y
  `placebos_d44` hasta despues de escribir los veredictos (y despues solo para cotejar las lecturas de A9, ver §7);
  la suite entera de pytest (no la re-corri: use los `sha_*`/`status_*` del implementador y comprobe que midieron el
  mismo evaluador que `7eb91eb5e`); los 404 placebos (no los re-corri: re-conte y re-decidi desde los JSONL).

## 2. En una pantalla

1. El evaluador de `7eb91eb5e` decide P2 como manda la adenda §2: enumeracion exacta con B de 20 o menos, 10.000
   sorteos con semilla 162 y el +1 con B de 21 o mas, una cola por direccion al 5 % en enteros, B con los bloques de
   suma 0, SIN SUSTRATO con B de 4 o menos, INDECIDIBLE solo con controles caidos, `global_ventana` sin cambios.
   Lo comprobe con una enumeracion propia por bits (84 conjuntos con ceros y magnitudes desiguales, mas B = 20 con 2^20),
   un generador propio para B = 21 y una tabla de 10 casos de la regla: 0 diferencias. **A1 CONFIRMADO.**
2. Candados, rojas, placebos, mediciones y verdes se sostienen: 31 rojas por asercion re-corridas por mi (31/31, 0 por
   otra excepcion); 58 de 58 mutaciones atrapadas (con la salvedad de que 57 corrieron con las pruebas anteriores a
   `ac6eab47b`, V45-05); 404 corridas re-contadas (320 celdas de (c), GANA 8 y PIERDE 4; (a) GANA y (b) PIERDE en las
   100 % de las celdas con sustrato) y 665 de 665 celdas con B de 20 o menos re-decididas igual con mi enumeracion; la
   tasa exacta por cola la reproduje por mi cuenta (maxima 1577/32768 = 4,81 % en B = 18); los verdes midieron el mismo
   evaluador y las mismas seis baterias que `7eb91eb5e` (sha256 identicos) y la unica falla es la frescura del CSV de la
   rama (fecha maxima 2026-10-21 15:05 UTC, corrida a las 18:20 UTC del 23). Mis 5 mutaciones propias: ver §5.
3. Dos hallazgos sobre la REGLA, ninguno sobre el codigo, ambos de gravedad 2: el parentesis de §6 «(todas se apagan o
   todas se encienden)» describe la accion y no el signo, y el nulo de §2.3 exige signo comun (V45-01); el valor-p por
   sorteos depende del orden de los bloques y la adenda no lo fija (V45-02). Las cinco lecturas de A9 son compatibles con
   el texto; dos (la 1 y la 5) resuelven una ambiguedad real de la adenda y conviene que el dueño las ratifique.
4. Nada de lo encontrado cambia un veredicto de P2 ni toca el pipeline; nada impide el tag de lectura por el lado del
   evaluador. Lo que el dueño tiene que decidir es solo texto de la adenda (V45-01, V45-02).

## 3. Veredicto por afirmacion

| Af. | Veredicto | Gravedad propia | Evidencia de esta sesion |
|---|---|---|---|
| A1 | CONFIRMADO | 5 (vara) | `verif_matematica.py` bloques 1 a 9 (todos OK; control positivo 11 FALLA como debe); lectura de `evaluar_d25.py:515-631` y del diff `c13cf5808..7eb91eb5e` (`global_ventana` sin cambios: `git diff ... \| grep global_ventana` vacio; `contar` y `contribuciones_p2` sin cambios). |
| A2 | CONFIRMADO | 3 | `evaluar_d25.py:620-628` trae neto, B, bloques de suma no nula, `sumas_bloque`, p GANA/PIERDE/dos colas (numero y fraccion), metodo, p minimo, semilla y sorteos (None en exacto), `regla`; `informar_d34_d42` (l. 566-597) trae ic95, D-34, `resultado_d42`, calibrada, falsos, sorteos, semilla 161; `imprimir` (l. 1145-1156) los muestra; D-34/D-42 no entran al retorno (l. 629-631). |
| A3 | CONFIRMADO | 3 | Re-corri `rojo_signos_p2.py c13cf5808 _verif45`: 31 pruebas, 31 por asercion, 0 por otra excepcion, 0 errores (`rojo_rerun_verif45.xml`, parseado por mi). El archivo de pruebas no cambio despues de las rojas (`git log da5e895c7..7eb91eb5e -- tests/test_evaluar_d25_signos_p2_s161.py` vacio). 26 funciones + 5 parametrizadas = 31. |
| A4 | CONFIRMADO EN PARTE | 4 | `mutaciones_salida.json`: control n = 106, 0 fallas; 57 ATRAPADA + s12a2 CAE (TypeError) + q01 NO ATRAPADA (equivalente); `mutaciones_s12a2_salida.json`: s12a2 ATRAPADA con su propio control verde. La parte que no se sostiene literal: las 57 no se re-corrieron con las pruebas finales (V45-05); el efecto posible de la asercion agregada va en una sola direccion (mas fallas por asercion, nunca otra excepcion), asi que el 58 de 58 se sostiene por argumento, no por corrida. La equivalencia de q01 la probe aritmeticamente (bloques 4a y 4b). 58 ids contados por mi en `MUT`. |
| A5 | CONFIRMADO | 2 | Diff de `tests/test_evaluar_d25_calib_p2_s160.py`: las 4 pruebas conservan la asercion sobre `resultado_d42` con el mismo valor que antes vigilaban en `v`, y agregan el valor de D-45 (`SIN SUSTRATO` con 3 noches, `GANA` con 12, `sin_calibrar` en las 4 de la parametrizada, `SIN SUSTRATO` en contar). Las mutaciones m07b («contar publica D-42») y c6/c6b siguen atrapadas, asi que la vigilancia sobre D-42 no se perdio. |
| A6 | CONFIRMADO | 4 | `verif_placebos.py`: 406 filas, 2 caidas re-corridas con la misma semilla, 404 completas; semillas 0..19 en (a) y (b) (solo 0 con 100 %), 0..39 en (c), sin repetidas ni ampliadas; (c) 320 celdas, GANA 8 (2,50 %), PIERDE 4 (1,25 %), 0 celdas con B <= 4; V2 50 % VIIRS 375 GANA 3 de 40; (a) GANA en 20/20 o 1/1 en cada celda con sustrato, (b) PIERDE idem; 0 noches con signos mixtos dentro del mismo sensor (4.502 noches tocadas); tocadas = en tabla en las 404. Brazos de produccion: `sustrato_k.py:75-89` lee `data/_s154_reproc_k_historico` y `data/mirova_equivalent`, nunca `s146-ab`. Fracciones de (c) iguales a D-44 (25 y 50 %, contadas en `placebos_d44/placebo_c_*.jsonl`). |
| A7 | CONFIRMADO | 3 | `verif_matematica.py` bloque 6: mi tabla binomial coincide con `medir_bpm.txt` en los 16 valores (maxima 1577/32768 = 4,8126 % en B = 18); bloque 7: 7 noches deciden (1/128), 6 contra 1 BLOQUEA/EMPATE (8/128). Observacion V45-03 sobre el escenario A. |
| A8 | CONFIRMADO EN PARTE | 3 | `status_antes/despues.txt`: HEAD `8642543ec` (no `7eb91eb5e`), 0 procesos python, 0 copias `_mut_*`, sha256 iguales antes y despues; los 8 sha256 coinciden con los de `7eb91eb5e` medidos por mi, y `git diff --stat 8642543ec 7eb91eb5e` solo trae salidas, NOTA_D46 y README. Suite: 2.447 pasan, 1 falla, 29 skipped, 1 xfailed (`suite_salida.txt`); la falla es `test_csv_max_age_under_48h` y el CSV de la rama tiene fecha maxima 2026-10-21 15:05 UTC (medido), 51 h antes de la corrida: del entorno. probar 31 de 31 (son 31 casos e2e de `RESULTADOS`, otro conjunto que las 31 pruebas). La parte «con el arbol quieto» la sostienen los sha y el conteo de procesos, no una medicion mia. |
| A9 | CONFIRMADO (las 5 compatibles con la adenda; 2 resuelven ambiguedad) | 3 | Ver §7. |

## 4. Hallazgos (lo peor primero)

### V45-01
- TÍTULO: El parentesis de la adenda §6 describe una accion comun por noche, pero el nulo de §2.3 exige un signo comun; el placebo (c) sigue el signo.
- ARCHIVO:LÍNEA: `experiments/_s157_prereg_d25/ADENDA_SIGNOS_P2.md:123-125`; `experiments/_s159/instrumentos/signos_p2/placebo_signos.py:14-16` y `:253-273`.
- QUÉ PASA: una pasada tocada aporta +1 si el error queda solo en D y -1 si queda solo en K; apagar una alerta de K aporta +1 y apagar un negativo de K aporta -1. Si en una noche «todas se apagan», la suma del bloque mezcla signos y su distribucion no es simetrica, asi que cambiar el signo del bloque entero no seria el nulo de §2.3 y el placebo no probaria lo que dice. El codigo fija el tamaño t antes de la moneda y da a todas las pasadas tocadas de la noche el mismo signo (`signo = "+" if rng.random() < 0.5 else "-"`, l. 267; `tomar = rng.sample(sorted(lados[nk][signo]), t)`, l. 268), con lo que la suma del bloque es +t o -t con probabilidad 1/2: ese si es el nulo de §2.3. Medido en los JSONL: 0 noches con signos mixtos dentro del mismo sensor sobre 4.502 noches tocadas (`verif_placebos_salida.txt`). La adenda misma dice «de modo que el nulo del placebo sea el mismo de §2.3» (§6, TEXTO), que es lo que el codigo cumple; el parentesis «(todas se apagan o todas se encienden)» (§6, TEXTO) no.
- CÓMO SE VE EN EL DASHBOARD: invisible (es un control sobre produccion, no un veredicto).
- CÓMO REPRODUCIRLO: `python experiments/_s159/instrumentos/verificador_d45/verif_placebos.py` (ultima linea: «noches con signos mixtos dentro del mismo sensor: 0»); leer las lineas citadas.
- CONFIANZA: CONFIRMADO (texto leido, codigo leido, dato medido).
- GRAVEDAD: 2. Decision del dueño: ratificar la lectura del implementador (signo comun) como la lectura oficial de §6 y, si quiere, corregir el parentesis en una nota (no en la adenda sellada). No pide cambio de codigo ni re-correr nada.

### V45-02
- TÍTULO: El valor-p por sorteos (B de 21 o mas) depende del orden de los bloques; la adenda no lo fija y el JSON guarda las sumas ordenadas, asi que un veredicto con sorteos no se puede re-decidir desde el JSON.
- ARCHIVO:LÍNEA: `experiments/_s157_prereg_d25/evaluar_d25.py:618` (`sumas = [por_bloque[b] for b in sorted(por_bloque)]`), `:542-549` (sorteo `S @ sumas`), `:621` (`"sumas_bloque": sorted(sumas)`); `ADENDA_SIGNOS_P2.md:53-57` (§2.5).
- QUÉ PASA: con 10.000 sorteos de signos, la misma semilla asigna cada columna de signos a un bloque distinto segun el orden de `sumas`; con las 21 sumas del caso de prueba, en orden de clave el numerador de GANA es 651 y en orden inverso 697 (de 10.001; `verif_matematica.py` bloque 3). El codigo es determinista (orden de la clave «volcan|fecha») y mi mutacion vA (orden inverso) queda ATRAPADA por dos pruebas (§5), asi que la reproducibilidad esta cubierta por los candados. Lo que queda abierto: (i) el detalle de P2 guarda `sumas_bloque` como multiconjunto ordenado, de modo que un tercero no puede recomputar el valor-p de una celda con B > 20 desde el JSON (en los placebos, 143 de 808 celdas, el 17,7 %, no se pudieron re-decidir por mi enumeracion: `verif_placebos_salida.txt`); `resumir_signos.py:53-55` lo salva con el valor-p exacto «aproximado» y lo dice. (ii) SOSPECHA: la secuencia de `numpy.random.Generator.choice` esta ligada a la version de numpy; un cambio de version podria mover el numerador sin tocar el codigo. Vale igual para la semilla 161 de D-42 (ya sellada).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python experiments/_s159/instrumentos/verificador_d45/verif_matematica.py` (linea «(informa) B = 21 con las sumas en orden inverso»).
- CONFIANZA: CONFIRMADO en (i); SOSPECHA en (ii).
- GRAVEDAD: 2. Decision del dueño: dejar escrito (nota, no adenda) que el orden es el de la clave del bloque, y pedir que el detalle de P2 guarde las sumas en ese orden ademas del multiconjunto, y la version de numpy, cuando el metodo es sorteos. Hasta entonces, la re-decision solo vale con B de 20 o menos.

### V45-03
- TÍTULO: En el escenario sintetico A (nulo iid, 12 noches x 3 pasadas, 500 semillas) D-45 da PIERDE en 6,0 %, sobre el 5 % nominal y sobre el 3,68 % exacto de esas magnitudes; es la muestra de semillas, no la regla.
- SCRIPT:SALIDA: `experiments/_s159/instrumentos/signos_p2/medir_escenarios_A_B_B2.txt` (D-45 PIERDE 0.060 [0.042, 0.084], GANA 0.030); `medir_esperado_escenarios.txt` (A: 0,0368 por cola); `verificador_d45/verif_extras_salida.txt`.
- QUÉ PASA: P(X >= 30 de 500 | p = 0,0368) = 0,0069; contra la cota del 5 %, P = 0,176. Las tres reglas (D-45, D-42, D-34) dan el mismo exceso sobre las mismas semillas (5,4 a 6,0 %), y la tasa exacta de la regla por B (bloque 6 de `verif_matematica.py`, `medir_bpm.txt`) esta bajo 5 % en los 16 valores: el exceso viene de los conjuntos que generaron las semillas 0..499, no de la regla. El intervalo de Wilson incluye el 5 %. Con 9 escenarios nulos y 2 colas (18 comparaciones), un minimo de 0,0069 no es raro.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python experiments/_s159/instrumentos/signos_p2/medir_signos_p2.py escenarios 500 A` (unos 7 min) y `esperado_escenarios 500 A`.
- CONFIANZA: CONFIRMADO (los numeros son los de los archivos; la atribucion a la muestra se apoya en la tabla exacta y en que las tres reglas coinciden).
- GRAVEDAD: 1. No pide decision; se informa para que nadie lo lea como «la regla pasa del 5 %».

### V45-04
- TÍTULO: Los verdes se midieron sobre `8642543ec`, no sobre `7eb91eb5e`; valen igual porque los archivos medidos son identicos.
- ARCHIVO:LÍNEA: `experiments/_s159/instrumentos/signos_p2/status_antes.txt:2`, `status_despues.txt:2`, `sha_antes.txt`, `sha_despues.txt`.
- QUÉ PASA: `7eb91eb5e` solo agrega las salidas de verdes, `NOTA_D46.md` y el README (`git diff --stat 8642543ec 7eb91eb5e`, 8 archivos). Los sha256 del evaluador, de `probar_evaluar_d25.py` y de las seis baterias en `7eb91eb5e` (medidos por mi) coinciden con los de `sha_antes.txt` y `sha_despues.txt`.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `cd C:\vrp-trabajo\s159-evaluador && sha256sum experiments/_s157_prereg_d25/evaluar_d25.py tests/test_evaluar_d25_signos_p2_s161.py` y comparar con `sha_antes.txt`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### V45-05
- TÍTULO: 57 de las 58 mutaciones corrieron con las pruebas anteriores a `ac6eab47b`; solo s12a2 corrio con las finales.
- ARCHIVO:LÍNEA: `experiments/_s159/instrumentos/signos_p2/mutaciones_salida.json` (commit `a080c9fb7`), `mutaciones_s12a2_salida.json` (commit `ac6eab47b`); diff de `tests/test_evaluar_d25_p2_s159.py` en `ac6eab47b` (dos `assert isinstance(det.get("ic95"), list)` agregados).
- QUÉ PASA: la adenda §5 pide que las baterias «se vuelven a correr» con las pruebas en su version final. La asercion agregada solo puede convertir un TypeError en una falla por asercion (mas ATRAPADA, nunca menos) y no agrega ni quita pruebas (control n = 106 en los dos archivos), asi que el 58 de 58 se sostiene por argumento. El implementador lo declara en A4 («contando s12a2 re-corrida despues de agregar una asercion»).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git show ac6eab47b --stat`; comparar `hora` del control en `mutaciones_parcial.jsonl` con `mutaciones_s12a2_parcial.jsonl`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1. Si el dueño quiere la literalidad de §5, una corrida de `mutar_signos_p2.py` sin `--parcial` previo (unos 60 x 3,5 min en serie, o 4 en paralelo) la cierra; no cambia nada que yo haya visto.

### V45-06
- TÍTULO: El placebo (c) al 50 % no alcanza el objetivo de pasadas tocadas en VIIRS 750 (ni en VIIRS 375 de V2): el punto «50 %» es mas chico de lo que dice su nombre.
- SCRIPT:SALIDA: `verificador_d45/verif_extras_salida.txt` (faltaron, suma sobre 40 semillas: V1 50 % VIIRS375 40, VIIRS750 400; V2 25 % VIIRS750 120; V2 50 % VIIRS375 240, VIIRS750 880); `placebo_signos.py:263-274`.
- QUÉ PASA: las noches elegibles exigen pasadas de los dos lados (l. 260) y cada una aporta como mucho `min(lado +1, lado -1)`; se agotan antes del objetivo `n = round(2 f M)`. No sesga el nulo (el tamaño t se fija antes de la moneda y el estadistico es simetrico igual), y el script lo registra como pide su docstring («faltaron»). Solo cambia B y el poder del punto, que (c) no mide.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: el script de arriba; o `grep simetrico_faltaron placebo_c_V2.jsonl`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### V45-07
- TÍTULO: Dos corridas de placebo cayeron por el reinicio del 2026-10-23 y quedaron en el JSONL junto a su repeticion; los dos recuentos (el del implementador y el mio) las descartan igual.
- ARCHIVO:LÍNEA: `signos_p2/placebo_a_V1.jsonl` (V1 (a) 50 % semilla 8, `caido`), `placebo_c_V1.jsonl` (V1 (c) 50 % semilla 3, `caido` vacio); `resumir_signos.py:93-101`; `verif_placebos_salida.txt`.
- QUÉ PASA: 406 filas con fraccion, 2 con `caido`, 404 completas; las dos semillas caidas tienen una fila completa posterior con la misma semilla (el generador es `random.Random(10000 f + s)`, independiente por semilla, `placebo_signos.py:243`), asi que repetirlas no amplia ni mueve nada.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `verif_placebos.py` (lineas «CAIDA (no cuenta)» y «celdas ... repetidas»).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

## 5. Mutaciones propias (las que el corredor del implementador no tiene)

Corredor: `mutaciones_propias.py` (reusa `una()` de `mutar_signos_p2.py`: misma definicion de ATRAPADA, mismas seis
baterias, control sin mutar antes). Resultado en `mutaciones_propias_salida.txt` y `.json`; el resumen va en §5.1,
escrito al terminar la corrida.

### 5.1 Resultado

(ver al final del archivo, seccion «Anexo: mutaciones propias», agregada cuando termino la corrida)

## 6. Lo que la adenda deja escrito y conviene que el dueño tenga a la vista (no son defectos)

- §2.4: con una cola por direccion al 5 %, bajo el nulo hasta un 10 % de las ventanas deciden algo (GANA o PIERDE); en
  los placebos (c) salio 3,75 % (12 de 320). La adenda lo elige a sabiendas («5 % en cada cola por separado»).
- §2.7: con B de 4 o menos P2 no bloquea aunque el neto sea enorme: 4 noches con 30 errores de D cada una (neto +120)
  dan SIN SUSTRATO (`verif_matematica.py` bloque 8b). La adenda lo acepta («Consecuencia que se acepta a sabiendas»).
- §7 «6 contra 1 con 7 noches no» vale con bloques de magnitud 1; con 6 noches de +2 contra 1 de -1 la regla si decide
  PIERDE (p = 2/128), y es correcto que lo haga.

## 7. Las cinco lecturas de A9 contra el texto de la adenda

1. **D-34 y D-42 se informan con su propio minimo** (`informar_d34_d42`, l. 582-586). §2.7 dice que el SIN SUSTRATO
   nuevo «Reemplaza el minimo de D-34 §5.6» como regla que decide; §3 dice que D-34 y D-42 «Se siguen calculando y se
   informan, sin decidir ... Asi se ve si el cambio de regla cambia el veredicto». Para ver si el cambio de regla cambia
   el veredicto hay que informar lo que D-34 habria dado con su propio minimo. Compatible; resuelve una ambiguedad real
   (la adenda no dice con que minimo se informan). Que el dueño la ratifique.
2. **Los campos de la prueba se calculan siempre** (l. 619-628, antes del `if not ok_ctrl`). §4: «Siempre que P2 se
   calcule». Con controles caidos P2 es INDECIDIBLE y los campos sobran, pero no deciden (l. 629-631). Compatible; mas
   informacion, sin efecto.
3. **p minimo por sorteos 1/10.001**: §4 solo fija el exacto («1 / 2^B con el metodo exacto»); con la formula de §2.5
   el minimo alcanzable es (1 + 0) / 10.001. Correcto por construccion.
4. **Dos colas con |suma| >= |neto|** (l. 537, 547): §2.4 dice que el valor-p a dos colas «se informa al lado y no
   decide» y no lo define. La definicion es la usual y simetrica; con magnitudes desiguales existen otras (2 x la cola
   menor). Compatible, no decide (comprobado en el bloque 5: una cola chica del lado contrario no cruza).
5. **En (c) manda el signo comun y el tamaño se fija antes de la moneda**: es V45-01. La lectura es la unica que hace
   del placebo el nulo de §2.3 que la propia adenda pide; el parentesis de §6 dice otra cosa. Compatible con el
   proposito, no con el parentesis. Que el dueño la ratifique.

## 8. SEGUIMIENTOS (fuera de mi eje, dejados reproducibles)

- `tests/test_evaluar_d25_signos_p2_s161.py:473` (las e2e) lee `data/mirova_equivalent/<vol>.json` de produccion: el
  resultado de esas dos pruebas puede cambiar con el dato vivo (A90). Hoy pasan. Confianza CONFIRMADO (leido), gravedad 1.
- `tests/test_mirova_csv_freshness_f49.py` falla en cualquier rama cuyo `latest_consolidado.csv` tenga mas de 48 h: en
  esta rama la fecha maxima es 2026-10-21 15:05 UTC. Es del entorno y ya esta declarado por el implementador. Gravedad 1.
- SOSPECHA: la secuencia de `numpy.random.Generator.choice` depende de la version de numpy; las semillas 161 (D-42) y
  162 (D-45) no llevan la version registrada en el JSON. Gravedad 1 (V45-02 ii).
- `probar_evaluar_d25.py` tiene 31 casos e2e y la bateria nueva tiene 31 pruebas: son conjuntos distintos; que nadie
  lea «31 de 31» como la misma cosa.

## 9. VERIFICADO LIMPIO (que mire, con que comando, contra que vara)

- `prueba_signos_p2` exacto = enumeracion por bits en 84 conjuntos (B 1..14, con ceros y magnitudes -3..3) y en B = 20
  (2^20 con numpy): `verif_matematica.py` bloques 1 y 2. Vara: adenda §2.3 a §2.5.
- Sorteos con B = 21: metodo, semilla 162, 10.000, denominador 10.001, numerador 1 + m con un generador propio: bloque 3.
  Vara: §2.5.
- Comparacion en enteros: ningun k/2^B vale 1/20 (B 1..30), 10.001 no es multiplo de 20, enteros = flotante en todo
  k de B 5..20: bloque 4. Vara: §2.5 y la equivalencia declarada de §5.
- `regla_signos_p2`: 10 casos (SIN SUSTRATO B = 4; 5 % justo decide; 5 % + 1 no; neto 0 EMPATE; las colas no se
  cruzan; B = 21 con 500/10.001 decide y 501 no): bloque 5. Vara: §2.6 y §2.7.
- Tasa exacta por cola B 5..20 con bloques +-1, por binomial propia: bloque 6, identica a `medir_bpm.txt`. Vara: §7.
- 7 noches deciden, 6 contra 1 no, controles caidos INDECIDIBLE, B <= 4 SIN SUSTRATO con neto +120, lista vacia da
  SIN SUSTRATO con B 0 sin excepcion, B cuenta bloques de suma 0: bloques 7 a 9. Vara: §2.2, §2.7, §2.8, §7.
- D-46: P(alguna de 16 celdas-cola sobre 5 %) = 0,668 (la nota dice 0,67); P(X >= 3 de 40 | 0,032) = 0,1356; Wilson
  8/320 = [1,3; 4,9], 4/320 = [0,5; 3,2], 3/40 = [2,6; 19,9]: bloque 10. Vara: NOTA_D46 puntos 1 a 3.
- Control positivo del instrumento: una mutacion en memoria (cola de GANA = cola de PIERDE) da FALLA en el bloque 1
  (bloque 11). Y el bloque 8c muestra que la medicion no es ciega: con lista vacia da B 0, no revienta.
- Rojas: re-corridas por mi contra `c13cf5808`: 31/31 por asercion (`rojo_rerun_verif45.xml`). Vara: §5.
- Placebos: `verif_placebos.py` (recuento propio y re-decision propia de 665 celdas, 0 distintas). Vara: §6 y D-46.
- Verdes: sha256 de los 8 archivos en `7eb91eb5e` = `sha_antes.txt` = `sha_despues.txt`; 0 procesos python y 0 copias
  `_mut_*` antes y despues. Vara: A112.
- `global_ventana`, `contar` y `contribuciones_p2` sin cambios entre `c13cf5808` y `7eb91eb5e` (diff leido entero).
  Vara: §2.1, §2.2, §2.9.
- Brazos de los placebos: `sustrato_k.py:75-89` lee solo `data/_s154_reproc_k_historico` y `data/mirova_equivalent`.
  Vara: §6 («brazos de produccion») y el limite de la tarea.

## 10. SIN DATO

- Las 143 celdas de placebo con B > 20 (sorteos): comprobe metodo, semilla, sorteos y denominador, no el numerador
  (hace falta el orden de clave de los bloques, que el JSON no guarda; V45-02).
- «Re-decidir da lo mismo que re-correr» sobre los JSONL de D-44 (§6): el implementador re-corrio (a) y (b) en vez de
  re-decidir, lo que §6 permite («si no los guardan, se re-corren»); no comprobe si los JSONL de D-44 guardaban los bloques.
- La suite entera no la re-corri; me apoyo en las fotos del implementador y en los sha.
- Los 404 placebos no los re-corri (la tarea lo pide asi); los re-conte y re-decidi.

## 11. FUERA DE ALCANCE

- Lo que `evaluar_fk.py` y `banco_paridad.py` entienden por publica, alerta, protegida y negativo limpio (vara).
- P1, P1b, M, P4, P5, estrato 203, D-29 (adenda §8).
- Cualquier dato o veredicto del A/B (V1, V2a, V2b, brazo del 17 al 19).

## Anexo: mutaciones propias (resultado, agregado al terminar la corrida)

Corrida en serie el 2026-10-23 de 18:40:33 a 18:58:37 UTC, 1.084 s, con el arbol quieto (solo mi carpeta sin seguimiento);
control sin mutar: 106 pruebas, 0 fallas. Las cinco quedaron ATRAPADAS por asercion, ninguna por otra excepcion:

| id | que rompe | pruebas que lo atrapan |
|---|---|---|
| vA | orden inverso de las sumas de bloque (cambia los sorteos con B >= 21) | 2 (`test_con_b_21_son_10000_sorteos...`, `test_un_sorteo_con_una_noche_grande...`) |
| vE | cola de GANA con menor estricto (exacto) | 9 |
| vF | cola de PIERDE con mayor estricto (exacto) | 8 |
| vG | el +1 solo en GANA (sorteos) | 1 (`test_con_b_21_son_10000_sorteos...`) |
| vH | SIN SUSTRATO sobre los bloques de suma no nula en vez de B | 3 (`test_b_cuenta_los_bloques_de_suma_cero`, `test_el_signo_es_por_bloque...`, `test_un_sorteo...`, mas una de s159) |

Lectura: el orden de los bloques (V45-02) y el «menor o igual» de las dos colas estan vigilados aunque la adenda no
nombre mutaciones para ellos; el +1 esta vigilado por una sola prueba (si esa prueba cambiara, la mutacion vG quedaria
suelta: conviene no tocarla). Salida: `mutaciones_propias_salida.txt` y `.json`.

Hora del servidor al cerrar: `Fri, 23 Oct 2026 18:58:50 GMT`. Temporales de `C:\vrp-trabajo\tmp_s161_verif` borrados;
0 copias `experiments/_mut_*`; disco C: 26 GB libres, D: 8,6 GB (sobre los 3 GB de parada).
