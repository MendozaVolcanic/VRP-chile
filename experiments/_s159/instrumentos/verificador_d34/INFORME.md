# Verificador con contexto limpio del diff 63e310af5..c44709e27 (D-30, D-32 y D-34 del evaluador de D25)

## 1. Encabezado

- Fecha y hora del servidor al abrir: Thu, 22 Oct 2026 04:53:09 GMT (header `Date` de `gh api repos/MendozaVolcanic/VRP-chile`);
  al escribir este encabezado: Thu, 22 Oct 2026 05:09:24 GMT.
- Commit medido: `c44709e2755a5e6f6eb464bf83a997142a0d6378`, rama `s159-evaluador-d25`, worktree `C:\vrp-trabajo\s159-evaluador`.
  El remoto `refs/heads/s159-evaluador-d25` apunta al mismo sha (`gh api .../branches/s159-evaluador-d25 --jq .commit.sha`).
  `git status` del repo antes de medir: sólo `?? experiments/_s159/instrumentos/verificador_d34/` (mi carpeta). Los
  directorios `experiments/_s159_mut_cmp_NN/` que aparecen mientras corre `mutar_comparador.py` son suyos y los borra.
- Modelo y esfuerzo: Claude Fable 5.1, esfuerzo medio (el que trae la sesión por defecto).
- CARPETA: `C:\vrp-trabajo\s159-evaluador\experiments\_s159\instrumentos\verificador_d34\`. Todo lo escrito en esta
  sesión está ahí: `caminos.md` (sellado antes de abrir archivos, sha256 al pie), scripts, salidas, este informe y
  `hallazgos.csv`. No se tocó ningún archivo fuera de la carpeta; no hubo commit, checkout ni stash.
- Qué NO miré: el veredicto de D25 ni ningún dato real del A/B (no corrí `evaluar_d25.py` con `--raiz`, `--logs`,
  `--repeticion` ni `--combinar` sobre brazos reales; no bajé artefactos de runs; no abrí `D:\vrp-trabajo\temporales\`).
  No re-auditi la implementación de D-28 (`b4258040c`), salvo donde el diff la toca. No leí el informe del verificador
  anterior más allá de la lista de guardas (grep de `H3` y `guarda`). No miré `probar_evaluar_d25.py` línea por línea:
  lo corrí y comparé su resumen. No verifiqué la frontera lógica de `etiquetas_regla` (SN contra original), que es de
  F/K y no cambia en el diff.
- Única lectura de datos no sintéticos: `calib_dprima_1000.py` lee `verificador_comparador/pares_k.json`, pares reales
  de K contra MIROVA (sin brazo D; el D es sintético). Lo corrí porque la tarea lo nombra y porque los pares de K no
  llevan el veredicto; lo digo para que nadie lo lea como «sólo sintéticos».

## 2. En una pantalla

1. Las ocho afirmaciones se CONFIRMAN en el código: las reglas de D-30, D-32 y D-34 están escritas tal como las adendas
   las sellan, incluido el signo de P2 (errores de D menos errores de K; una alerta bajo 1 MW que D publica y K no RESTA).
2. Pruebas reproducidas: 11 de 11 rojas por aserción sobre `7cbee245a`, 31 de 31 verdes hoy, 17 de 17 mutaciones del
   implementador atrapadas por aserción (0 caídas), `probar_evaluar_d25` 31 de 31, suite completa 2.373 passed,
   29 skipped, 1 xfailed con `git status` idéntico antes y después, `calib_dprima_1000` reproducido número por número.
3. Hallazgo propio más serio (V34-01, gravedad 3): la regla nueva de P2 no tiene calibración y, con el sustrato mínimo
   que la adenda permite (3 noches), decide en falso en 24,8 % de los nulos con signo común por noche (n = 2.000), y
   6,5 a 8,7 % en nulos iid con 3 a 12 noches; con 12 noches correlacionadas sí queda en 4,0 %. M tiene su nulo; P2 no.
4. Bajo un nulo verdadero la variante BLOQUEA apaga CUMPLE en 37 a 48 % de los conjuntos sintéticos (V34-02): es lo que
   la adenda pide, pero conviene saberlo antes de leer el veredicto.
5. De 23 mutaciones propias, la batería deja pasar las que cambian la semilla o el número de remuestreos de P2 y el
   borde `lo >= 0` de PIERDE (V34-03): esas tres partes de la adenda se sostienen sólo por lectura del código.

## 3. Veredicto por afirmación

Vara: `experiments/_s157_prereg_d25/PREREGISTRO.md` §5 (fila «P2 suma bajo 1 MW», l. 165, TEXTO), `ADENDA_PLACEBO.md`
§5 (l. 67 a 154, TEXTO, agregado en `7cbee245a`), `ADENDA_GEMELO.md` (79 líneas, TEXTO, agregada en `c44709e27`),
`ADENDA_CALIBRACION.md` l. 3 a 8 (TEXTO) y las filas D-28, D-30, D-32, D-33 y D-34 de `tasks/LOOP_OBJETIVOS.md` §5
(l. 527 a 533, TEXTO). Código: `experiments/_s157_prereg_d25/evaluar_d25.py` en `c44709e27` (las líneas citadas son
las de hoy).

### Afirmación 1. D-30 (1): d MEJORA + calibración de d′ fallida = INDECIDIBLE. CONFIRMADO.

- `evaluar_d25.py:516-522`: `if comparador and modo_calib == "simetrica" and modo != "informa": ... if r_dec ==
  "MEJORA" and not detalle["calibrada_dprima"]: r_dec = "INDECIDIBLE"`, con la nota `NOTA_CALIB_DPRIMA` (l. 116). La
  rama NEUTRO (`elif r_dec == "MEJORA" and not detalle["dprima_da_mejora"]`, l. 523) queda después, así que el orden es
  el de la adenda: primero la calibración, después el comparador.
- Vara: ADENDA_PLACEBO.md §5.1 punto 1 (TEXTO): «**Si d da MEJORA y la calibración de d′ falla, el estrato queda
  INDECIDIBLE**, no NEUTRO».
- Caminos descartados (caminos.md 1.a a 1.f): el literal se asigna en la rama correcta (1.a); el predicado es
  `calibrada_dprima`, que desde D-30 es sólo la cola de MEJORA (1.b, ver afirmación 2); el veredicto vive en un solo
  campo `r_dec` y el detalle lleva `calibrada_dprima` y `nota` (1.c); la prueba `test_si_d_mejora_y_la_calibracion_de_
  dprima_falla_queda_indecidible` fuerza la calibración de d′ con monkeypatch de la semilla `SEMILLA + 3` y exige
  `regla == "MEJORA"` como guarda de poder (1.d); «sin sustrato» y «comparador apagado» se evalúan antes, en `evaluar_m`
  l. 547 y en la condición de la l. 515, y no pisan el INDECIDIBLE (1.e). Camino 1.f: cuando d NO da MEJORA y la
  calibración de d′ falla, el estrato sigue con la regla sobre d (NEUTRO o EMPEORA): la adenda sólo manda INDECIDIBLE
  «si d da MEJORA», así que es lo correcto; mi mutación m22 (INDECIDIBLE también sin MEJORA) mide si la batería vigila
  ese sobre-alcance (resultado en §5).
- Reproducción: `pytest -q tests/test_evaluar_d25_placebo_s159.py -k indecidible` (verde hoy) y la misma prueba
  sobre la copia de `63e310af5` en `raiz_falsa/experiments/pre_d30` da `AssertionError: falla la calibración de d′ y el
  estrato da NEUTRO` (`rojo_placebo_pre_d30.xml`, clasificado con `clasificar_junit.py`).

### Afirmación 2. D-30 (2): la calibración de d′ exige sólo la cola de mejora. CONFIRMADO.

- `evaluar_d25.py:287-290`: `f_mej, f_emp, poder = calibrar_simetrico(dp, W, bloques, n_rep=N_CALIB_DPRIMA,
  semilla=SEMILLA_CALIB_DPRIMA)` y `calibrada = f_mej <= MAX_FALSOS_CALIB`; `f_emp` se devuelve en
  `falsos_empeora_dprima` (l. 302) y no decide. Antes (`63e310af5`) era `f_mej <= MAX_FALSOS_CALIB and f_emp <=
  MAX_FALSOS_CALIB` (diff, l. 288 vieja).
- Vara: ADENDA_PLACEBO.md §5.1 punto 2 (TEXTO): «**La calibración de d′ exige sólo la cola de MEJORA** ... La cola
  EMPEORA de d′ se informa y no decide.»
- Signo (caminos 2.a y 2.e): `calibrar_simetrico` cuenta «MEJORA» cuando `regla_m` da `hi < 0` sobre `±|d′|` (l.
  242-251), y d′ = |log10(D/M)| − |log10(ĝK/M)| (l. 278), así que MEJORA de d′ es «D más cerca de MIROVA que la ganancia
  uniforme», la misma dirección que MEJORA de d. La cola exigida es la que decide. La prueba
  `test_la_calibracion_de_dprima_solo_mira_la_cola_de_mejora` fuerza `f_emp = 0,5` y exige MEJORA: distingue «sólo
  mejora» de «ambas» (camino 2.c). No hay parámetro de colas (2.b). El tope se aplica a la cola de mejora sola (2.d).
- Mutación del implementador «D-30.2: ... exige también la cola EMPEORA» atrapada por aserción (`mutaciones_rerun.txt`).
  Mi mutación m19 (exigir la cola EMPEORA en vez de la de MEJORA): resultado en §5.

### Afirmación 3. D-30: con `--calibracion sellada` el comparador queda apagado y el JSON lo marca. CONFIRMADO.

- Apagado: `decidir_estrato` l. 515 `if comparador and modo_calib == "simetrica" and modo != "informa":` es la única
  entrada a `comparar_con_ganancia`; con `sellada` no se calcula d′ (y por eso tampoco puede dar INDECIDIBLE por d′,
  camino 3.f: ese modo decide con la regla de d sola, que es lo que la adenda dice que «aprobaría un placebo»).
- Marca: `validez_calibracion` l. 699-708 devuelve `vale_para_decidir: False` y `motivo_validez` para todo lo que no
  sea `"simetrica"`; `evaluar` lo mete al JSON (l. 747 `res.update(validez_calibracion(a.calibracion))`), lo agrega al
  estado (l. 893-894) y `combinar` lo arrastra (l. 974-975). `res["placebo"]["comparador"] = a.calibracion ==
  "simetrica"` (l. 748) es una segunda marca coherente (camino 3.c).
- Vara: ADENDA_PLACEBO.md §5.1 punto 4 (TEXTO): «**Con `--calibracion sellada` el comparador queda apagado**, y el JSON
  de salida marca ese veredicto con `vale_para_decidir: false`; `--combinar` arrastra la marca.»
- Default (camino 3.d): `CALIB_MODO = "simetrica"` (l. 87), `argparse choices=("sellada", "simetrica")` (l. 989): no
  hay forma de pasar «Sellada» ni espacios. El flag se lee en `a.calibracion` y llega a `contar(..., a.calibracion, ...)`
  l. 849 como `modo_calib` (camino 3.a trazado por el caller, A6).
- Pruebas: `test_un_veredicto_con_la_calibracion_sellada_no_vale_para_decidir` (unidad: función y combinar) y el caso
  `sellada_marca` de `probar_evaluar_d25.py` (extremo a extremo: `vale_para_decidir is False` y «NO VALE PARA DECIDIR»
  en `estado`). Mi mutación m20 mide si la batería unitaria vigila la línea del estado (resultado en §5).

### Afirmación 4. D-32: 1.000 repeticiones, tope 5 % por cola proporcional, semilla fija, escritos en §5. CONFIRMADO.

- `evaluar_d25.py:113-114`: `SEMILLA_CALIB_DPRIMA = SEMILLA + 3` (= 160 con `SEMILLA = 157`, l. 71) y `N_CALIB_DPRIMA
  = 1000`; se usan en la l. 287. El tope es `MAX_FALSOS_CALIB = 0.05` (l. 73) comparado con la FRACCIÓN `f_mej`
  (`falsos["MEJORA"] / n_rep`, l. 251), así que es proporcional al número de repeticiones (50 de 1.000, 10 de 200;
  camino 4.d descartado) y es «a lo más» (`<=`, camino 4.c: 50 de 1.000 pasa; `50/1000` y `0.05` son el mismo double).
  La calibración de d (D-27) sigue en `N_CALIB = 200` (l. 73, 242).
- Vara: ADENDA_PLACEBO.md §5.3 (TEXTO): «la calibración de d′ corre con **1.000 repeticiones** (`N_CALIB_DPRIMA` en
  `evaluar_d25.py`) y la **semilla 160** (`SEMILLA_CALIB_DPRIMA`, que es `SEMILLA + 3` ...). El tope sigue siendo el
  5 % de la cola de MEJORA: **50 de 1.000**.» Número y semilla coinciden con el código (camino 4.e descartado).
- Script del implementador re-corrido: `calib_dprima_1000_rerun.txt` reproduce las 8 filas de
  `calib_dprima_1000_salida.txt` número por número (V2 VIIRS 750 z<=40: 10 y 11 de 200, 29 y 31 de 1.000; el `diff`
  sólo difiere en CRLF). La semilla alcanza porque `calibrar_simetrico` usa un solo `default_rng(semilla)` (camino 4.f).
  El script lee pares REALES de K (sin D): ver el encabezado.
- Prueba: `test_la_calibracion_de_dprima_usa_la_semilla_y_las_repeticiones_selladas` (roja por aserción sobre
  `63e310af5`: «el número de repeticiones de la calibración de d′ no es una constante»). Mutaciones del implementador
  «D-32: vuelve a 200» atrapada; mis m16 (tope 10 %), m17 (999) y m18 (semilla + 4): resultado en §5.
- Observación (no es desviación): el nombre «tope por cola» en la fila D-32 de LOOP_OBJETIVOS y el «50 de 1.000» de
  la adenda hablan de la cola de MEJORA, la única exigida desde D-30 (2); la cola EMPEORA se imprime pero no tiene tope.

### Afirmación 5. D-34: P2 se decide como M. CONFIRMADO, con las propiedades de la regla medidas en V34-01 y V34-02.

Frase por frase de ADENDA_GEMELO.md §5 contra `evaluar_d25.py:405-472` y `contar` l. 618-631:

| adenda §5 | código | veredicto |
|---|---|---|
| 1. unidad: pasadas en que K y D difieren en la suma de P2 (error en uno y no en el otro) | `contribuciones_p2` l. 418-420: `eK ^ eD` sobre `E.errores_por_pasada` de cada lado, mismo `prot, lect, cfg, s, excluir` que `suma_errores` | CONFIRMADO; `errores_por_pasada` (evaluar_fk.py:357-367) usa la misma definición que `suma_errores` (l. 338-354): alerta `pos` no protegida que no se publica, o `neg_limpio` publicado |
| 2. signo: neto = errores de D menos errores de K, +1 sólo D, −1 sólo K, positivo malo para D | l. 419 `"c": 1 if k in eD else -1` sobre la diferencia simétrica; `neto = int(round(c.sum()))` l. 430; `imprimir` l. 914 «neto D menos K %+d»; `neto_igual_a_suma_D_menos_suma_K` l. 627 como autocontrol | CONFIRMADO (ver afirmación 8) |
| 3. intervalo: bootstrap 95 % por bloques noche-volcán, `pesos_bloque`, 10.000, semilla 157 | l. 436 `W = pesos_bloque(bl_p2)` con defaults `N_BOOT=10000, SEMILLA=157` (l. 71, 160); bloque `volcán|fecha[:10]` l. 420; `sumas = W @ c`, percentiles 2,5 y 97,5 (l. 437-438) | CONFIRMADO; es la misma matriz de pesos que usa M (`decidir_estrato` l. 483) |
| 4. GANA si entero bajo 0; PIERDE si entero sobre 0; EMPATE si cruza | l. 440-446: `hi < 0` GANA, `lo > 0` PIERDE, resto EMPATE | CONFIRMADO; bordes estrictos como en `regla_m` |
| 5. variante: neto puntual sobre 0 sin PIERDE = BLOQUEA, bloquea CUMPLE, ventana DECIDE NICOLAS con el motivo | l. 444-445 `elif neto > 0: return "BLOQUEA"`; `global_ventana` l. 690-695 pone DECIDE NICOLAS con el sensor y `empeora = True`; `combinar` l. 962 «M empeora o P2 bloquea» | CONFIRMADO |
| 6. SIN SUSTRATO con menos de 5 discordantes o menos de 3 noches-volcán (mínimos de M) | l. 435 `len(c) < N_MIN_PARES or len(set(bl_p2)) < N_MIN_NOCHES` con `5, 3` (l. 72); no bloquea (`global_ventana` sólo mira PIERDE, INDECIDIBLE y BLOQUEA) | CONFIRMADO |
| 7. lista de discordantes siempre, con volcán, sensor, hora, publica K/D, clase y VRP de MIROVA, pc.vrp_mw de cada brazo, de quién es el error y la contribución | `lista_p2` l. 449-461, en `info["P2|s"]["discordantes"]` l. 629 y en pantalla l. 920-923 | CONFIRMADO; el JSON de salida persiste `info` entero (`res["por_regla"][regla]["info"]`, l. 851, `json.dumps(res)` l. 900) |
| 8. lo que habrían dado (a) gemelo y (b) D-33 se informa sin decidir | l. 620 `v_a` (regla vieja intacta, con `ruido` del gemelo o de `--ruido-de` en V2), l. 464-469 `regla_b_d33(v_a, margen)` con margen ≤ 2; ambos en `info` l. 628 y en pantalla l. 918 | CONFIRMADO; `ver["P2|s"]` toma sólo `v_` de D-34 (l. 624) |
| «por sensor ... lectura A, reglas original y SN, manda la más estricta, en V1 sin las sólo OCR de Suomi NPP» | `contar` corre por `s in SENS` y por regla (`evaluar` l. 846-856, `peor` y `any(empeora)`); `excluir` es el mismo de `suma_errores` | CONFIRMADO |

Caminos descartados: 5.b (el neto es sobre discordantes, no sobre todas las pasadas: las concordantes no entran a `c`
ni a los bloques); 5.g (las listas (a) y (b) no deciden: `ver` lleva `v_`); 5.i (el predicado «publica» es el `pub` de
la tabla que arma `armar_tabla.py` con node, F/K, sin cambio en el diff); 5.j (regla SN y original por el bucle de
`evaluar`); 5.k (las protegidas no entran: `not prot[k][lectura]` en `errores_por_pasada`).

Dos observaciones sobre la vara, no sobre el código: (i) la fila D-34 de LOOP_OBJETIVOS (l. 527, TEXTO) dice «sobre las
pasadas donde K y D publican distinto», y la adenda §5.1 restringe a las que difieren «en la suma de P2 (una cuenta
como error en un brazo y no en el otro)»; una pasada con etiqueta `sin_info` o `far_ref`, o una protegida, puede
publicar distinto sin ser error y no entra. El código sigue a la adenda, que es la sellada. (ii) La misma fila habla de
«alertas bajo 1 MW recuperadas menos publicaciones de más» (positivo bueno) y la adenda §5.2 de errores (positivo
malo): son la misma cantidad con el signo cambiado y los veredictos coinciden; el código sigue la adenda y el
pre-registro (errores).

### Afirmación 6. Las tres guardas pedidas están puestas. CONFIRMADO.

- Lo pedido (sólo de `verificador_comparador/INFORME.md` l. 103 «H3. Dos piezas del §2.3 de D-28 no tienen ninguna
  prueba» y del mensaje de `7cbee245a`: «Guardas de H3 del verificador (opción A sobre d′, calibración de d′, opción A
  contada con d′)»).
- Puestas, en `tests/test_evaluar_d25_placebo_s159.py`: `test_la_opcion_a_se_aplica_sobre_dprima_y_no_sobre_d` (l. 258)
  cubre la opción A sobre d′ y que se cuente con d′ y no con d (exige `volcanes_con_dprima_negativa == 1` y NEUTRO con
  `regla_dprima == "MEJORA"`); `test_si_d_mejora_y_la_calibracion_de_dprima_falla_queda_indecidible` (l. 241) y
  `test_la_calibracion_de_dprima_solo_mira_la_cola_de_mejora` (l. 250) cubren la calibración de d′. Son pruebas de
  pytest (aserciones), no `assert` del módulo ni `warnings` (camino 6.c), y se ejecutan en la suite (`testpaths =
  tests`, `pytest.ini` l. 6; camino 6.b).
- Las tres mutaciones «H3» del implementador (`mutar_comparador.py` l. 59-67) quedan atrapadas por aserción
  (`mutaciones_rerun.txt`). Nota: `test_la_opcion_a_se_aplica_sobre_dprima_y_no_sobre_d` PASA también sobre
  `63e310af5` (`rojo_placebo_pre_d30.xml`: 4 fallas, 1 pasa), lo que es correcto: el verificador anterior dijo que el
  código ya hacía lo correcto y faltaba la guarda. No es una prueba «roja antes», es un candado contra regresión.

### Afirmación 7. Pruebas: roja 11/11 por aserción, verde 31/31, probar 31/31, mutaciones 17/17, suite 2.373. CONFIRMADO (las cinco cifras re-corridas y reproducidas).

- Roja: `tests/test_evaluar_d25_p2_s159.py` contra el evaluador de `7cbee245a` (copia en
  `raiz_falsa/experiments/pre_d34/`, con `D25_EVALUADOR_DIR`): 11 fallas, las 11 `AssertionError: falta
  decidir_p2_bloques (D-34)` (`rojo_p2_pre_d34.xml`, clasificado con `clasificar_junit.py`: `{'AssertionError': 11}`,
  0 de otro tipo, 0 errores de colección). El `_tiene()` de la l. 45 del archivo de pruebas convierte la ausencia en
  aserción antes de cualquier `AttributeError` (camino 7.a descartado). Primera corrida mía con la copia en una carpeta
  de otra profundidad dio `ModuleNotFoundError: evaluar_fk` (`RAIZ = AQUI.parents[1]`, `evaluar_d25.py:44`): por eso
  las copias viven en `raiz_falsa/experiments/<x>/` con junctions a `scripts/`, `frontend/` y los `experiments/` que
  importa. Eso es un detalle de mi instrumento, no del evaluador.
- Verde: `pruebas_verde_rerun.txt`: `31 passed in 208.22s` (11 de P2 + 20 del placebo, camino 7.b).
- `probar_evaluar_d25.py`: `probar_rerun.txt`: 31 de 31 OK, los 31 veredictos por caso iguales a la salida sellada (§4).
- Mutaciones: `mutaciones_rerun.txt`: 17 de 17 atrapadas por aserción, control sin mutar en verde (§4). El corredor distingue aserción de caída leyendo el
  JUnit XML (`mutar_comparador.py` l. 119-128) y tiene control sin mutar (l. 141-147). Observación: `atrapada =
  bool(por_asercion) and not errores` (l. 151) cuenta como atrapada una mutación que haga fallar una prueba por
  aserción y otra por excepción (`otras` no entra a la condición); las imprime aparte, así que se ve. En la salida
  sellada del implementador y en mi re-corrida ninguna mutación tiene «otra falla», así que hoy no cambia el conteo.
- Suite: `suite_rerun.txt`: 2373 passed, 29 skipped, 1 xfailed, sobre el árbol quieto (§4). Igual que `comparador_suite.txt`.

### Afirmación 8 (agregada por quien orquesta). Signo del término de alertas en P2. CONFIRMADO.

- Vara: PREREGISTRO.md §5 fila «P2 suma bajo 1 MW» (l. 165, TEXTO): «alertas Muy Bajo que el brazo no publica +
  publicaciones en negativos limpios» es lo que cuenta; «GANA si la suma de D es menor que la de K». O sea P2 cuenta
  errores y menos es mejor. ADENDA_GEMELO.md §5.2 (TEXTO): «una alerta bajo 1 MW que D publica y K no **resta** (D
  comete un error menos), una que K publica y D no **suma**».
- Código: `errores_por_pasada` (evaluar_fk.py:364-366) mete la pasada al conjunto del lado cuando `x["lab"] == "pos"
  and not prot[k][lectura] and not x["pub"]` (alerta bajo 1 MW NO publicada por ese brazo) o `x["lab"] == "neg_limpio"
  and x["pub"]`. Una alerta bajo 1 MW que D publica y K no: está en `eK`, no en `eD`, cae en `eK ^ eD` con `c = -1`
  (l. 419): RESTA a D. Una que K publica y D no: en `eD` sola, `c = +1`: SUMA. Un negativo limpio que D publica y K no:
  `eD` sola, `+1`. El consumidor no vuelve a aplicar signo: `decidir_p2_bloques` usa `c` tal cual y GANA es `hi < 0`
  (camino 8.b y 8.c descartados). Las alertas que no deciden (protegidas, `prot[k][lectura]` True) no entran (8.e); con
  la regla SN la etiqueta de las de 0,05 MW o menos la fija `etiquetas_regla` antes de `contar` (F/K, fuera del diff).
- Prueba: `test_contar_usa_el_signo_de_errores_y_trae_la_lista` arma 5 alertas que D publica y K no, y 1 negativo
  limpio que D publica y K no, y exige `neto == -5 + 1` (asimétrico, camino 8.d descartado) y `error_de == "D"` con
  `contribucion 1` en el negativo. La mutación del implementador «signo invertido» y mi m10 (etiqueta `error_de`
  invertida) quedan atrapadas por aserción.
- Coincide con el texto sellado y no con un encargo al revés: el único lugar donde el signo podría venir invertido
  (`"c": 1 if k in eD else -1`) está en la dirección de la adenda.

## 4. Re-corridas de los instrumentos del implementador (se completa al terminar cada una)

| instrumento | salida del implementador | mi re-corrida | igual |
|---|---|---|---|
| pruebas unitarias (31) | `p2_y_comparador_verde_d34.txt`: 31 passed | `pruebas_verde_rerun.txt`: 31 passed in 208 s | sí |
| roja de P2 (11) | `p2_rojo_d34.txt`: 11 failed, 22 líneas AssertionError, 0 de otro tipo | `rojo_p2_pre_d34.xml`: 11 AssertionError | sí |
| `calib_dprima_1000.py` | `calib_dprima_1000_salida.txt` | `calib_dprima_1000_rerun.txt`: 8 filas idénticas | sí |
| `mutar_comparador.py` (17) | `comparador_mutaciones_d34.txt`: 4/4, 2/2, 7/7, 4/4 | `mutaciones_rerun.txt`: control 31 passed; 4/4, 2/2, 7/7, 4/4 ATRAPADA por aserción; 0 «otra falla», 0 errores de colección | sí |
| `probar_evaluar_d25.py` (31) | `probar_evaluar_d25_salida_d34.txt`: 31 de 31 OK | `probar_rerun.txt`: 31 de 31 OK; las 31 líneas «caso OK» coinciden (el `diff` sólo agrega las líneas de aviso de `calidad_referencia_mirova` que la salida sellada no capturó); TMP en `tmp_probar/` (527 MB, dentro de mi carpeta) | sí |
| suite completa | `comparador_suite.txt`: 2373 passed, 29 skipped, 1 xfailed | `suite_rerun.txt`: 2373 passed, 29 skipped, 1 xfailed, 50 warnings in 311 s; `suite_status_antes.txt` y `_despues.txt` idénticos (árbol quieto, sin editar nada durante la corrida) | sí |

## 5. Mutaciones propias (`mutaciones_propias.py`, salidas `mutaciones_propias_salida.txt` y `_2.txt`)

Control m00 (copia sin mutar, las dos pruebas): 31 passed, 0 fallas. Las mutaciones m01 a m15 son sólo de P2 y corren
sólo `test_evaluar_d25_p2_s159.py` (las del placebo no tocan P2); m16 a m23 corren los dos archivos.

| id | mutación | regla | resultado |
|---|---|---|---|
| m01 | BLOQUEA con el lado invertido | D-34 5.5 | ATRAPADA (2 pruebas) |
| m02 | SIN SUSTRATO con 4 pasadas | D-34 5.6 | ATRAPADA |
| m03 | SIN SUSTRATO con 2 noches | D-34 5.6 | ATRAPADA |
| m04 | noches contadas como pasadas | D-34 5.6 | ATRAPADA |
| m05 | otra semilla en el bootstrap de P2 | D-34 5.3 | **NO ATRAPADA** |
| m06 | 1.000 remuestreos en vez de 10.000 | D-34 5.3 | **NO ATRAPADA** |
| m07 | GANA con borde `hi <= 0` | D-34 5.4 | ATRAPADA |
| m08 | PIERDE con borde `lo >= 0` | D-34 5.4 | **NO ATRAPADA** |
| m09 | unión en vez de diferencia simétrica | D-34 5.1 | ATRAPADA |
| m10 | `error_de` al brazo equivocado | D-34 5.7 | ATRAPADA |
| m11 | BLOQUEA sin marcar `empeora` | D-34 5.5 | ATRAPADA |
| m12 | SIN SUSTRATO bloquea | D-34 5.6 | ATRAPADA |
| m13 | bloque por volcán solo (sin la noche) | D-34 5.3 | ATRAPADA |
| m14 | regla (b) D-33 con margen 3 | D-34 5.8 | ATRAPADA |
| m15 | intervalo de P2 al 90 % (percentiles 5 y 95) | D-34 5.3 | **NO ATRAPADA** |
| m16 | tope de la calibración de d′ al 10 % (en la comparación, no en la constante) | D-32 | **NO ATRAPADA** |
| m17 | 999 repeticiones en d′ | D-32 | ATRAPADA |
| m18 | semilla de d′ = SEMILLA + 4 | D-32 | ATRAPADA (2 pruebas) |
| m19 | la calibración de d′ exige la cola EMPEORA en vez de la de MEJORA | D-30.2 | ATRAPADA (2 pruebas) |
| m20 | la marca NO VALE PARA DECIDIR no llega al `estado` (sólo al JSON) | D-30.4 | **NO ATRAPADA** por la batería unitaria; la atrapa el caso `sellada_marca` de `probar_evaluar_d25.py` (exige «NO VALE PARA DECIDIR» en `estado`), que el corredor de mutaciones no corre |
| m22 | INDECIDIBLE por d′ aunque d no dé MEJORA (sobre-alcance) | D-30.1 | **NO ATRAPADA** |
| m23 | NEUTRO donde va INDECIDIBLE | D-30.1 | ATRAPADA |

Total: 16 de 23 atrapadas por aserción (m00 control en verde, 0 caídas; m21 ATRAPADA). Las 7 no atrapadas son dos
familias: (i) los números del intervalo de P2 que la adenda fija y que ninguna prueba mira (semilla 157, 10.000
remuestreos, nivel 95 %, borde `lo > 0` de PIERDE: m05, m06, m08, m15); (ii) el tope de 5 % de d′ en la comparación
(m16), el texto del estado con `--calibracion sellada` (m20, cubierta por `probar_evaluar_d25.py`) y el sobre-alcance
de INDECIDIBLE (m22). Ver V34-03.

## 6. Cobertura del intervalo de P2 con sinteticos propios (`cobertura_p2.py`; salidas `cobertura_p2_salida.txt`, `_2000.txt`, `_borde.txt`)

Cada conjunto sintético decide con la función real `decidir_p2_bloques` (10.000 remuestreos, semilla 157). Denominador
n por escenario; semillas 0..n−1 del generador propio. «Decide en falso» = GANA + PIERDE bajo un nulo verdadero.

| escenario | n | GANA+PIERDE | BLOQUEA | por PASADA (control del instrumento) |
|---|---|---|---|---|
| A nulo iid, 12 noches × 3 pasadas | 2.000 | **0,065** | 0,40 | 0,029 |
| B nulo con signo común por noche, 12 × 4 | 2.000 | 0,040 | 0,37 | 0,385 |
| B2 signo común por noche, 6 × 6 | 400 | 0,048 | 0,36 | 0,297 |
| B3 nulo iid, noches desiguales (10 + 9 × 1) | 2.000 | **0,087** | 0,47 | 0,064 |
| B4 nulo iid en el borde (3 noches: 2+2+1) | 2.000 | **0,065** | 0,48 | |
| B5 signo común por noche en el borde (3 × 2) | 2.000 | **0,248** | 0,38 | |
| B6 signo común por noche (4 × 2) | 2.000 | **0,130** | 0,25 | |
| B7 signo común por noche (5 × 2) | 2.000 | **0,065** | 0,48 | |
| B8 signo común por noche (8 × 2) | 2.000 | **0,070** | 0,34 | |
| C efecto grande a favor (p(−1) = 0,85, 12 × 3) | 400 | GANA 0,99 | 0 | |
| C2 efecto grande en contra (p(+1) = 0,85, 12 × 3) | 400 | PIERDE 0,998 | 0,003 | |
| D efecto moderado (p(−1) = 0,70, 20 × 2) | 400 | GANA 0,69 | | |
| E efecto por noche (noche entera a favor p = 0,8, 10 × 4) | 400 | GANA 0,35 | | |

Lectura: el bootstrap por bloques absorbe la correlación intra-noche cuando hay noches suficientes (B: 4,0 % contra
38,5 % si se remuestreara por pasada; eso es el control positivo del instrumento: ve la diferencia bloque/pasada). Con
pocas noches la regla es anticonservadora: el mecanismo es simple, con B noches todas del mismo lado (probabilidad
2^(1−B) bajo un nulo correlacionado por noche) todo remuestreo cae de ese lado y el intervalo no puede cruzar 0: 3 noches
24,8 %, 4 noches 13,0 %, 5 noches 6,5 %. El efecto grande se decide (C, C2); el poder cae a 35 % cuando el efecto es por
noche con 10 noches (E). Ver V34-01 y V34-02.

## 7. Hallazgos propios (ordenados por gravedad; también en `hallazgos.csv`)

### V34-01
- TÍTULO: La regla nueva de P2 no tiene calibración y con pocas noches decide en falso muy por encima del 5 % (24,8 % con el sustrato mínimo de 3 noches correlacionadas)
- SCRIPT:SALIDA: `cobertura_p2.py` : `cobertura_p2_salida_borde.txt` (B5 a B8), `cobertura_p2_salida_2000.txt` (A, B, B3, B4), `cobertura_p2_salida.txt` (todos, n = 400). Código: `experiments/_s157_prereg_d25/evaluar_d25.py:423-446` (`decidir_p2_bloques`); vara: ADENDA_GEMELO.md §5.3 a 5.6.
- QUÉ PASA: las pasadas de una misma noche comparten volcán y atmósfera, por eso el intervalo es por bloques noche-volcán; pero con B noches discordantes todas del mismo lado (probabilidad 2^(1−B) bajo un nulo donde el signo es de la noche) ningún remuestreo de bloques puede cruzar 0 y la regla decide GANA o PIERDE sin que haya efecto. Medido con la función real (10.000 remuestreos, semilla 157), n = 2.000 conjuntos por escenario: signo común por noche con 3 noches 24,8 %, 4 noches 13,0 %, 5 noches 6,5 %, 8 noches 7,0 %, 12 noches 4,0 %; nulo iid con 12 noches × 3 pasadas 6,5 %, noches desiguales 8,7 %, borde de 3 noches 6,5 %. M tiene su nulo que puede fallar (pre-registro §5, D-27) y deja INDECIDIBLE un estrato mal calibrado; P2 con D-34 adopta los mínimos de M (5 pasadas, 3 noches) sin la calibración de M. El código hace exactamente lo que la adenda sella: el defecto es de la regla sellada, no del código.
- CÓMO SE VE EN EL DASHBOARD: invisible (es el evaluador del A/B). Lo que tuerce es la decisión de adoptar D25: un GANA o PIERDE de P2 con 3 a 5 noches discordantes tiene entre 6,5 y 25 % de probabilidad de ser azar.
- CÓMO REPRODUCIRLO: `cd C:\vrp-trabajo\s159-evaluador && python experiments/_s159/instrumentos/verificador_d34/cobertura_p2.py 2000 B5,B6,B7,B8` (datos sintéticos; no hay volcán ni pasada real).
- CONFIANZA: CONFIRMADO (medido).
- GRAVEDAD: 3.

### V34-02
- TÍTULO: Bajo un nulo verdadero la variante BLOQUEA apaga CUMPLE en 37 a 48 % de los conjuntos
- SCRIPT:SALIDA: `cobertura_p2.py` : `cobertura_p2_salida_2000.txt` y `_borde.txt`, columna BLOQUEA. Código: `evaluar_d25.py:444-445` y `global_ventana` l. 690-695.
- QUÉ PASA: la variante bloquea cuando el neto puntual queda sobre 0 y el intervalo cruza 0. Sin efecto, el neto cae sobre 0 en casi la mitad de los conjuntos, así que la mitad de los nulos termina en DECIDE NICOLAS por P2 (A 40 %, B 37 %, B3 47 %, B4 48 %, B5 38 %). Es lo que la adenda pide (§5.5 «un neto en contra de D (estimación puntual sobre 0) que no alcance PIERDE da **BLOQUEA**») y Nicolás eligió la variante; lo anoto porque al leer el veredicto un BLOQUEA se puede leer como señal en contra de D cuando bajo el nulo es la moneda.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python experiments/_s159/instrumentos/verificador_d34/cobertura_p2.py 2000 A,B,B3,B4`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### V34-03
- TÍTULO: La batería no vigila los números del intervalo de P2 (semilla, remuestreos, nivel 95 %, borde de PIERDE), el tope del 5 % de d′ en la comparación ni el alcance del INDECIDIBLE
- SCRIPT:SALIDA: `mutaciones_propias.py` : `mutaciones_propias_salida.txt` (m01 a m12) y `mutaciones_propias_salida_2.txt` (m13 a m23). Código: `evaluar_d25.py:436-438, 442, 290, 516`.
- QUÉ PASA: siete de 23 mutaciones propias pasan la batería en verde: m05 (semilla de P2 distinta de la de M), m06 (1.000 remuestreos), m15 (percentiles 5 y 95), m08 (`lo >= 0`), m16 (`f_mej <= 2 * MAX_FALSOS_CALIB`: tope 10 % en d′; la prueba de D-32 mira la constante, no la comparación, y las que fuerzan la calibración usan 0,5, que supera cualquier tope), m22 (INDECIDIBLE por d′ aunque d no dé MEJORA), m20 (la marca de validez no llega al `estado`; ésta sí la atrapa `probar_evaluar_d25.py`, caso `sellada_marca`, que el corredor de mutaciones no corre). Hoy el código cumple la adenda en los siete puntos (leído, afirmaciones 3, 4 y 5); lo que falta es el candado.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python experiments/_s159/instrumentos/verificador_d34/mutaciones_propias.py` (control + 23; unos 40 min) o `... m15` para reanudar desde una.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### V34-04
- TÍTULO: `mutar_comparador.py` cuenta como ATRAPADA una mutación que falla por aserción en una prueba y por otra excepción en otra
- ARCHIVO:LÍNEA: `experiments/_s159/instrumentos/mutar_comparador.py:151` (`atrapada = bool(por_asercion) and not errores`; la lista `otras` no entra a la condición).
- QUÉ PASA: una mutación que rompa una prueba por aserción y cinco por `KeyError` se cuenta igual que una atrapada limpia; las «otras fallas» se imprimen aparte (l. 166-167), así que se ven, pero el RESUMEN no las descuenta. En la salida sellada y en mi re-corrida hay 0 «otra falla» y 0 errores en las 17, así que hoy no cambia ningún conteo.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: leer la línea; `grep -c "otra falla" experiments/_s159/instrumentos/verificador_d34/mutaciones_rerun.txt` da 0.
- CONFIANZA: CONFIRMADO (leído).
- GRAVEDAD: 1.

### V34-05
- TÍTULO: La fila D-34 de LOOP_OBJETIVOS define la unidad de P2 como «pasadas donde K y D publican distinto» y la adenda sellada como «error en un brazo y no en el otro»; el código sigue a la adenda
- ARCHIVO:LÍNEA: `tasks/LOOP_OBJETIVOS.md:527` contra `experiments/_s157_prereg_d25/ADENDA_GEMELO.md:52-53` y `evaluar_d25.py:418-420`.
- QUÉ PASA: una pasada con etiqueta `sin_info` o `far_ref`, o una alerta protegida, puede publicar distinto en K y D sin ser error de P2, y no entra al neto ni a la lista. La adenda la excluye a propósito («Las pasadas en que los dos aciertan o los dos se equivocan no entran»); la fila del loop es la paráfrasis del coordinador. No es desviación del código; es una diferencia entre las dos redacciones de la vara que conviene dejar dicha antes del tag.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: leer las tres citas.
- CONFIANZA: CONFIRMADO (leído).
- GRAVEDAD: 1.

## 8. SEGUIMIENTOS (fuera de mi eje)

- S-1. La clave de bloque «noche-volcán» es `volcán|fecha UTC[:10]` tanto en M (`evaluar_d25.py:642`) como en P2 (l. 420):
  misma maquinaria, como pide la adenda. Pero una «noche» chilena cruza la medianoche UTC (las pasadas nocturnas de VIIRS
  sobre Chile caen entre las 03 y las 08 UTC, así que casi siempre quedan en una sola fecha UTC; una pasada de las 23 UTC
  del día anterior quedaría en otro bloque). Viene de D-27 (pre-registro §5), no del diff. CONFIANZA: CONFIRMADO que la
  clave es la fecha UTC; SOSPECHA que alguna noche real se parta. Gravedad 1.

## 9. VERIFICADO LIMPIO (qué miré, con qué comando y contra qué vara)

- Signo de P2 (afirmación 8): `evaluar_fk.py:357-367` + `evaluar_d25.py:418-420`, contra PREREGISTRO.md l. 165 y ADENDA_GEMELO.md §5.2; prueba `test_contar_usa_el_signo_de_errores_y_trae_la_lista` (asimétrica, 5 contra 1); mutaciones «signo invertido» (implementador) y m10 atrapadas.
- Misma maquinaria que M: `pesos_bloque` con defaults `N_BOOT=10000, SEMILLA=157` en M (l. 483) y P2 (l. 436); clave de bloque idéntica (l. 420 y 642). Vara: ADENDA_GEMELO.md §5.3.
- `neto == suma_D − suma_K` por construcción (diferencia simétrica sobre la misma definición que `suma_errores`), y el JSON lo autocontrola en `neto_igual_a_suma_D_menos_suma_K` (l. 627).
- GANA/PIERDE/EMPATE/BLOQUEA/SIN SUSTRATO: l. 435-446 contra §5.4 a 5.6; `global_ventana` l. 666-695 y `combinar` l. 962 contra §5.5; pruebas de P2 y mutaciones m01 a m04, m07, m09, m11 a m14 atrapadas.
- Listas informativas (a) y (b): l. 620, 464-469, 628; no deciden (`ver` toma `v_`, l. 624). Vara §5.8.
- D-30 (1), (2), (4) y D-32: l. 113-114, 287-290, 516-524, 699-708, 747, 893-894, 974-975 contra ADENDA_PLACEBO.md §5.1 y §5.3; las 11 mutaciones de la segunda vuelta y D-34 del implementador atrapadas; m17, m18, m19, m21, m23 atrapadas.
- Las tres guardas de H3 existen como pruebas de pytest en `tests/test_evaluar_d25_placebo_s159.py` l. 241, 250, 258 y se recogen en la suite (`pytest.ini` l. 6 `testpaths = tests`).
- Rojo antes: 11 de 11 por `AssertionError` (`rojo_p2_pre_d34.xml`); el guard de la opción A pasa también sobre `63e310af5` (candado, no prueba roja), lo que concuerda con «lo que falta es la guarda» (`verificador_comparador/INFORME.md:115`, TEXTO).
- Reproducibilidad de la calibración de d′: `calib_dprima_1000_rerun.txt` igual a la salida sellada en las 8 filas.
- Default `CALIB_MODO = "simetrica"` (l. 87) y `choices=("sellada", "simetrica")` (l. 989): no hay forma de pasar el flag mal escrito.
- El corredor de mutaciones distingue aserción de caída por el JUnit XML y tiene control sin mutar (l. 119-147); en 17 de 17 no hubo caídas.
- Nada escrito fuera de `verificador_d34/`; `git status` del repo igual antes y después de la suite; sin commit, checkout ni stash; disco C: 13 GB y D: 9,4 GB libres al cierre (sobre el límite de 3 GB).

## 10. SIN DATO

- Cuántas pasadas discordantes y cuántas noches tiene P2 en V1, V2a y V2b (si cae en SIN SUSTRATO, en el borde de 3 a 5 noches donde V34-01 pesa, o con noches suficientes): sale de los datos reales del A/B, prohibidos para mí.
- La curva de poder del comparador (ADENDA_PLACEBO.md §5.2) se midió con 200 repeticiones y la propia adenda dice que con 1.000 «**no se volvió a medir**»: queda declarado, no medido.
- Si los pares reales de K en `pares_k.json` (verificador anterior) siguen siendo los mismos que vería el evaluador hoy: no lo verifiqué; sólo reproduje el número que sale de ese archivo.
- Poder de P2 con efectos reales: sólo sintéticos (C, C2, D, E).

## 11. FUERA DE ALCANCE

- La implementación de D-28 (`b4258040c`): verificada PARCIAL por otro; sólo miré lo que el diff toca.
- `etiquetas_regla`, `armar_tabla.py` (predicado «publica» con node), `suma_errores` y `errores_por_pasada`: F/K, sin cambio en el diff; los usé como vara leída, no los auditi.
- El texto no normativo de las adendas (§1 a §4 de ADENDA_GEMELO.md: gemelo bit a bit, ruido entre máquinas de F/K): no es código.
- El veredicto de D25 y cualquier dato real del A/B.

## 12. Cierre

Hora del servidor al cerrar: Thu, 22 Oct 2026 05:51:57 GMT. Archivos de esta sesión en la CARPETA: `caminos.md` (sellado,
sha256 al pie), `INFORME.md`, `hallazgos.csv`, `_cerrar_informe.py`, `clasificar_junit.py`, `cobertura_p2.py` (+ 3 salidas),
`mutaciones_propias.py` (+ 2 salidas), re-corridas `pruebas_verde_rerun.txt/.xml`, `rojo_p2_pre_d34.txt/.xml`,
`rojo_placebo_pre_d30.txt/.xml`, `mutaciones_rerun.txt`, `probar_rerun.txt` (+ `tmp_probar/`, 527 MB),
`calib_dprima_1000_rerun.txt`, `suite_rerun.txt`, `suite_status_antes.txt`, `suite_status_despues.txt`, y
`raiz_falsa/` (junctions a `scripts/`, `frontend/` y tres `experiments/`, copia de `volcanoes.yaml`, copias de
`evaluar_d25.py` en `7cbee245a` y `63e310af5`).
