# Verificador limpio de la lectura V375-E (retrospectiva y lejanas), S168

- Objeto: `experiments/_s168/v375e_lectura_lejana/` (lectura hecha con el lector sellado sobre el tag `s168-v375e-cuerpo-sellado`, commit `444d5d888`).
- Commit medido: `7a548be11` (rama `claude/s168-v375e-sello`), árbol limpio salvo esta carpeta.
- Hora de servidor: inicio 2026-10-29 20:58:58 UTC; fin 2026-10-30 00:09 UTC (la re-corrida quedó pausada un par de horas en el reloj de pared por la suspensión del equipo; el proceso siguió y terminó solo).
- Modelo: Sonnet 5.5, contexto limpio. No edité nada del repo; los únicos archivos que escribí aquí son este informe y `CAMINOS_PREVIOS.md` (escrito antes de abrir la salida, 2026-10-29 20:59:44 UTC). Temporales en `D:\vrp-trabajo\temporales\s168_ver_lectura\`.

## Caminos previos (escritos antes de abrir `lectura_salida.txt` y `lectura.json`)

Tras leer el pre-registro completo y los metadatos de la corrida (`hora_inicio.txt`, `exit.txt`). Sólo vi, de pasada, las 5 primeras líneas de `stdout.txt` (procedencia y C3) en el mismo comando del diff de procedencia. Texto completo en `CAMINOS_PREVIOS.md`; resumen:

1. Procedencia: la lectura corrió sobre el árbol de trabajo, no sobre el tag; el commit podía diferir del tag en código.
2. Los cuatro artefactos de run no están versionados y pudieron cambiar.
3. Azar sin semilla (prueba de signos por sorteos, remuestreos de `evaluador_comun`, IC de `curva_cenit`).
4. Salida 0 con C3 caído o con un control en 0 de 0 (VA168-01 y VA168-07).
5. Veto y regla N-3: mala aplicación; pérdida común mezclada con pérdida que depende de la posición.
6. Marca A104 del paso 6: qué tramos cuentan (T, O1, O2); una discordancia en T podría o no disparar la marca.
7. Pesos (bajo 1 MW ~5, negativo limpio ~2), qué cuenta como error de posición, «P1 que veta» contra «P1 de evaluar.py».
8. M: pares con magnitud mayor que 0 en ambos, A104 de M («otro estado de (c)» ambiguo).
9. Tabla del §9.7: filas no previstas (SE QUEDA RADIANTE con marca, ELEGIDO con criterio que no cumple, DECIDE NICOLAS combinado con NO CUMPLE).
10. Equivalencia (salida 4 contra 0, vara vieja informativa).
11. Interpretación posterior: lo que haga falta para decir qué significa la salida y no esté escrito.

## Veredicto: CONFIRMADA CON RESERVAS

La lectura es la que el pre-registro manda, con el código sellado, y se reproduce idéntica. Todo número que pude recalcular cuadra. El resultado («ELEGIDO CERCANO», paquete «CUMPLE (falta la sombra)») sale de las reglas escritas. Las reservas (todas de gravedad 2 o menos) son que ese resultado cuelga de dos pasadas, que hay evidencia informativa en contra que el texto no sabe pesar, y que algunos rótulos de la salida inducen a leer de más. Ningún hallazgo de gravedad 3.

## Procedencia (punto 1)

- `git diff --name-only s168-v375e-cuerpo-sellado HEAD` sólo lista archivos de `experiments/_s168/v375e_lectura_lejana/` (los de la lectura). Cero diferencias en `experiments/_s162_v375/`, `scripts/`, `pipeline/`. Entre `e6675da85` y el tag sólo cambian `PREREGISTRO_E.md` y el informe del verificador de la adenda 3: el código es el que midió ese verificador.
- `git status --short` limpio antes de mi corrida. `evaluar.py` con fin de línea LF: sha256 `2126b743…` (C4 de la salida lo confirma); blob de `mirova_v750_codigo.py` `a9c00eaf…` (el de #921).
- Listas: `objetivos_far_v375.json` `a8528424…`, `objetivos_run_far_v375.json` `28468a14…` (coinciden con §8.4), las tres versionadas. El run FAR trae 329 `far_tabla`, 1 `far_ocr` y 20 de control de vida (350); `sin_granulo_far_v375.json` vacío.
- Cronología: sello 16:56:56 -0300 (19:56:56 UTC), tag 16:57:06, lectura iniciada 19:57:37 UTC (`hora_inicio.txt`): se leyó después de sellar.

## Re-corrida (punto 2)

Mismo comando (§8.9), `python -I`, desde la raíz del worktree, con `--salida` y `--json` en D:. Salió con `exit=0`.

- `salida.txt` contra `lectura_salida.txt`: **idénticas** (ignorando CR). `stdout.txt` idéntico. `lectura.json` idéntico (mismo sha256 sobre contenido LF, `a74b44eb…`).
- No hay azar sin semilla en el camino: `prueba_signos` usa semilla 162 (`evaluar.py` l. 57 y 120), `evaluador_comun` 157 y derivadas (l. 405 a 416), `curva_cenit` 162. El único insumo externo son los cuatro directorios de run; no cambiaron (resultado idéntico).

## Reglas aplicadas como están escritas (punto 3)

Todo lo siguiente lo comprobé contra la salida y contra `lectura.json`, con scripts propios sobre `objetivos_v375_bc.json`, `b2/objetivos_v375_b2.json` y `experiments/_s159/portes/objetivos_portes.json`.

- **Controles** (salida, bloque «== controles»): C2 `[True, False, True]`; C8 2362 de 2362; C1 174 de 174; C5 667 de 667; C6 distintas 0; equivalencia: máscara distinta 0, publicación distinta 0 en los tres brazos, VRP 667 de 667 (vara vieja, que informa: 491 de 667); C7 20 de 20 re-medidas, 20 iguales a S162, 16 con píxeles; K re-corrido igual a lo publicado 2342 de 2342; C9 x1,2 NEUTRO y x0,8 EMPEORA (ninguno MEJORA). Ningún `AVISO` de SIN DATO (`grep -c AVISO` da 0). Sale 0, coherente con `codigo_salida`.
- **Cobertura A108**: S159 149, S162 709, S162b 1.200 (2.058, como §9.2), FAR 330, control de vida 20. SIN DATO: 46, todas `neg_resto` (2,8 % de 1.645), 0 `far_tabla`. Conteos del marco: 80 protegidas (39+41) y 200 bajo 1 MW (45+155), como el conteo de diseño del §9.
- **Pesos** (§9.2): recalculé N_h / n_ok_h para las 91 claves de `pesos` restando las 46 SIN DATO de la salida: 0 difieren. Las lejanas pesan 1,0.
- **Veto y N-3**: recalculé desde las listas de pérdidas (`vara1[a].lecturas.P1.lista`) más sensor, canal y fecha de los objetivos. Radiante y pico pierden 10 protegidas; 7 las publica K; de esas, 5 son SNPP sólo OCR anteriores al 2026-10-09 (N-3) y 2 no: Isluga 2026-06-17 05:06 (NOAA-21, OCR, 1,64 MW, z 58°, tramo O1) y Lascar 2026-10-01 05:18 (NOAA-21, OCR, 1,2 MW, z 32°, tramo O2). Cercano pierde 6; 3 las publica K y son N-3; las otras 3 (Lascar 08-22, Tupungatito 09-28 y 09-29) no las publica K. Las 2 que vetan a radiante y pico son exactamente las que cercano publica (lista de cambios contra radiante). `veto` = `{radiante: 2, cercano: 0, pico: 2}` se sigue de eso. Las 8 «informadas aparte» de la RP son las 8 protegidas N-3 que K publica (recalculadas: 8).
- **Cambios contra radiante**: cercano 8 (4 protegidas, 4 bajo 1 MW), pico 0. La diferencia de P2 contra K entre radiante y cercano (-70,468 menos -51,114 = -19,354) es exactamente la suma de los pesos de las 4 alertas bajo 1 MW (4,833 + 4,75 + 4,9375 + 4,833 = 19,354). Recall bajo 187 a 191 de 200; B 107 a 103; M n 251 a 259 y «salen por publicar uno solo» 22 a 14: todo cuadra.
- **Vara 2**: radiante 13, pico 13, cercano 104, K 121 de 329 (con alertado 323). P2-L radiante neto -108 = 121 - 13; cercano neto -17 = 121 - 104; cercano usa prueba exacta (B 19, p 20/524288, GANA).
- **Marca A104 de la RP** (§8.5 paso 6): por tramo, T da `SE QUEDA RADIANTE`, O1 y O2 dan `ELEGIDO CERCANO`. El código compara sólo O1 y O2 con la unión (`for tr in ("O1", "O2")`, `leer_posicion_v375e.py` l. 787), como dice el texto («Si O1 u O2…»); O1 y O2 coinciden con la unión, así que **la marca no salta**, como el texto manda. Que T dé otro resultado es el hallazgo VL168-02. T no tiene ninguna protegida vetable (las dos que vetan son del 17 de junio y del 1 de octubre; el OCR anterior al 2026-06-13 no entra al marco, A119), por eso en T queda radiante.
- **Magnitud M** (§9.5): los tres brazos MEJORA en la unión; por tramo T, O1 y O2 MEJORA en cada uno, así que no hay marca A104 de M y `estado_c` = CUMPLE. d′ MEJORA con IC [-0,122; -0,082] (cercano). No pude recalcular d ni d′ (los pares no están en el JSON): SIN VERIFICAR a mano, lo tomo del evaluador común.
- **Curva** (§9.6): K y los tres brazos SIN SUSTRATO, nulo de 5 noches (el máximo que predijo el conteo de diseño); informa; (d) queda INFORMA.
- **Tabla del §9.7**: (a) cercano CUMPLE (0 que veten); (b) CUMPLE (P2 GANA, silencio ACOTADO BAJO K, P2-L GANA); (c) CUMPLE; (d) INFORMA; retrospectiva «CUMPLE (falta la sombra)». ELEGIDO sin marca A104 devuelve el estado del brazo. Radiante y pico: (a) NO CUMPLE por las 2. Todo coincide con `criterios_retro` y `regla_adopcion`.

## Punto 5 (§9.12)

C3 dio OK, así que VA168-01 (leer el marco con C3 caído) no se activó. VA168-07: C8 entró con **2362 pasadas** con K re-corrido (2342 del marco y lejanas más 20 del control de vida), 2362 de 2362 iguales: no es 0 de 0.

## Hallazgos

**VL168-01 (gravedad 2). La elección de «cercano» cuelga de dos pasadas y el texto no permite pesar lo que la contradice.** Con el veto sellado (todas las protegidas, lectura A, salvo N-3), radiante y pico caen por 2 pasadas, ambas sólo OCR de NOAA-21 (1,64 y 1,2 MW), una por tramo (O1 y O2). Con el veto contado sólo sobre protegidas de la tabla (línea «informa» del §8.5; `perdidas_tabla` = 0 en los tres brazos) el resultado es `SE QUEDA RADIANTE`. Costo de cercano que la RP no mide porque, con un solo brazo vivo, no hay comparación por pares: publica en 104 de 329 pasadas en que MIROVA publicó una fuente lejana, contra 13 de radiante y pico (y 121 de K). Cuenta mía con los números impresos (no la imprime el lector): cercano gana 4 protegidas y 19,35 de peso en alertas bajo 1 MW, y pierde 91 pasadas lejanas, o sea unos 67 puntos de error de posición ponderado a favor de radiante. El resultado cumple el texto sellado; lo que no está escrito es qué hacer cuando las lecturas que informan (veto con la tabla sola, vara 3, cuenta de lejanas) contradicen la elección que sale del veto.

**VL168-02 (gravedad 2). La marca A104 no cubre T y T discrepa.** Por tramo: T = `SE QUEDA RADIANTE`, O1 y O2 = `ELEGIDO CERCANO`. Por el texto (§8.5 paso 6 y §9.5 hablan de «O1 u O2») la marca no salta, y el código hace lo mismo. Pero el texto dice que la regla «se corre dentro de T, O1 y O2» y no explica por qué T no cuenta; la razón (T, anterior al 2026-06-13, no tiene protegidas OCR vetables) es mía. Cercano en T no cambia ninguna alerta contra radiante (los 8 cambios son de O1 y O2) y publica 43 lejanas contra 6. O1 y O2 eligen cercano cada uno por una sola protegida. Al reportar hay que decir que la elección sale de las ventanas posteriores al 2026-06-13 y que en T queda radiante.

**VL168-03 (gravedad 2). La vara 3, que el texto dice que «sirve para descartar un brazo», desfavorece a cercano y no hay regla para usarla.** Mediana de la diferencia de radios en `far_tabla`: radiante 0,284, pico 0,287, cercano 0,532; a una celda: 238, 252 y 145 de 323. En alertas de la tabla (231), a una celda: pico 155, radiante 142, cercano 121. Es diferencia de radios y no de posición (A93), y en una `far_tabla` la fila de MIROVA es la de la fuente lejana, así que parte de la diferencia es esperable. Aun así el §8.5 no dice cuánto pesa.

**VL168-04 (gravedad 2). El criterio (b) mide «no peor que K» en las lejanas, no «no publica ahí».** P2-L de cercano contra K da GANA con 19 bloques discordantes y -17 netos: cercano se comporta casi como K en esas escenas (104 contra 121). Eso cumple (b) tal como está escrito (§8.5 y §9.7: no PIERDE ni BLOQUEA), pero la premisa del §8.10 es que lo correcto es no publicar, y el criterio no lo exige. Al reportar «CUMPLE» conviene decir que en lejanas cercano publica un tercio de las pasadas.

**VL168-05 (gravedad 2, de comunicación). «CUMPLE (falta la sombra)» no significa «sin protegidas perdidas».** Cercano pierde 6 de 80 protegidas (3 que K publica y N-3 deja fuera de (a), 3 que K tampoco publica); la línea MISSION dice `PIERDE PROTEGIDA` para los tres brazos y el texto manda que MISSION informe y no decida (§9.7). El cumplimiento de (a) depende de la regla N-3 (sin ella cercano perdería 3 que K publica).

**VL168-06 (gravedad 1). Rótulos que inducen a error.** (i) «pérdidas comunes a los tres brazos: []» oculta 3 pérdidas realmente comunes (Tupungatito 08-01, Isluga 09-09, Tupungatito 09-14), porque N-3 las saca antes de calcular la lista. (ii) «informadas aparte por §8.13» tiene 8 entradas en la RP (todas las N-3 que K publica, incluidas 3 de Chillán que los brazos sí publican) y 5 o 3 en la línea por brazo (las que ese brazo calla): dos definiciones con el mismo rótulo.

**VL168-07 (gravedad 1). C9 no comprueba «d′ = 0».** El comparador sólo degrada MEJORA a NEUTRO (`scripts/evaluador_comun.py` l. 552 a 560); con x0,8 sale EMPEORA con comparador. C9 exige «no MEJORA», que es lo escrito en §9.4; el «d′ = 0 por construcción» del §5.2 no se verifica directamente (no vi el d′ del placebo).

**VL168-08 (gravedad 1). C8 no dice cuántas de sus 2362 pasadas publican.** Pasa con 2362 de 2362, pero 20 son del control de vida y no se informa cuántas tienen a K publicando; si el predicado no dependiera de la magnitud, C8 pasaría igual. No cambia nada (VA168-07 pedía sólo que no fuera 0 de 0).

## Lo que no pude comprobar

- d y d′ de M, los IC de la curva y las pruebas de signos por par: dependen de datos por pasada que `lectura.json` no guarda (sólo vi los agregados). Sí verifiqué que los netos de P2 y P2-L se reconcilian con conteos y pesos.
- La comparación por pares radiante contra cercano no se corrió (queda un solo brazo vivo), por eso el «67 puntos» de VL168-01 es una cuenta mía con los números impresos.
- La batería (165) y el nulo de mutaciones del lector: no los re-corrí (no eran lo pedido).
- Que el run FAR tenga sus 14 trabajos en verde: leí sus artefactos (350 pasadas, 0 sin gránulo) pero no su log de GitHub Actions.
