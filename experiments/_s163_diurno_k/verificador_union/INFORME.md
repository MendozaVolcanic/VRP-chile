# Informe del verificador: script de unión de la adenda 1 (evaluar_con_exclusion.py)

- Hora del servidor al empezar (gh api, Date): Mon, 26 Oct 2026 19:14:50 GMT.
- Commit medido: a1604e25346e2374ed814cd0301a3019cbbba121 (rama claude/s163-diurno-k-prereg-5c4f44). Árbol limpio al empezar.
- Modelo: Sonnet 5.5 (claude-sonnet-5-5). Esfuerzo: el del subagente por defecto, no declaro uno más alto.
- Caminos de ruptura escritos antes de abrir el diff: `CAMINOS.md` de esta carpeta, sha256 52c42fec49480807740fcd4c2b04783591f8f713b09890cac54fab716f6939f4 (calculado antes de añadirle la última línea con ese sha y la hora, 19:14:50 GMT).
- Alcance: el diff 867cb1ec8..a1604e253 de `evaluar_con_exclusion.py`, `test_evaluar_con_exclusion.py`, `mutaciones_exclusion.json`, `PREREGISTRO.md` (§11 puntos 7 a 9) y `objetivos_adenda1_sha256.txt`.

## Aviso sobre las mutaciones (PARADA POR DISCO)

La coordinadora ordenó parar por disco (C: con 2,9 GB libres) y declarar las mutaciones SIN DATO. Las había corrido antes de que llegara el mensaje, en una copia `git archive` fuera del worktree. Las dejo escritas en V1 con esa advertencia, para que la coordinadora decida si las usa o las descarta. No corrí nada después del mensaje. Mi uso de disco: unos 21 MB en las carpetas listadas al final; el disco bajo no viene de mí. El estado del repo es el original: `git status` sólo muestra esta carpeta nueva.

## Hallazgos (ordenados por gravedad)

### V1 · `main()` de la unión no tiene ninguna prueba que lo ejecute · GRAVEDAD 3 · CONFIRMADO
- ARCHIVO: `evaluar_con_exclusion.py:56-102` (main) y `test_evaluar_con_exclusion.py` completo.
- QUÉ PASA: las 4 pruebas ejercen `quitar_dias`, `lo_que_sale` y la consulta a CMR. Ninguna llama a `main()`, que es lo que corre en el despacho. Si `main()` dejara de aplicar la lista (por ejemplo `filas_x, recs_x = filas, recs`), el resultado sería el del evaluador sin excluir y la suite seguiría verde.
- CÓMO SE VERÍA: I4 fallaría en W2 a W6 por el hueco de NASA, que es justo lo que la adenda quería evitar, y el resultado saldría INVÁLIDO POR INSTRUMENTO sin que nadie sepa que la unión no excluyó. El camino contrario (ignorar sólo los logs, o fijar la opción e) cambiaría un veredicto sin aviso.
- CÓMO REPRODUCIRLO (hecho antes de la parada, en copia de `git archive a1604e25` bajo el scratchpad, script `vu_mut.py`, salida `vu_mut_salida.txt`): línea base verde (rc=0). Mutaciones propias NO atrapadas (rc=0): P1 `main()` no aplica la exclusión; P2 `main()` ignora la lista (`dias = []`); P3 `main()` no revisa los logs I1a; P4 `main()` no comprueba el sha de la referencia; P5 `main()` fija la opción e en `e-i`; P7 frontera `>= 1.0` cambiada a `> 1.0` en `lo_que_sale`; P9 `main()` no imprime el veredicto. Atrapadas por aserción: P6 y P8 (filtros invertidos en `quitar_dias`). Las 5 mutaciones sellas (G1 a G5) también salen atrapadas por aserción y el control C-CAIDA sale CAÍDA, tal como dice `mutaciones_exclusion_salida.txt` (5 de 5 más el control; el texto del §11 punto 7 dice "5 de 5", correcto).
- NOTA: las 5 mutaciones sellas sólo tocan `quitar_dias`, `lo_que_sale` y la consulta a CMR. Por eso el "5 de 5 atrapadas" no dice nada de `main()`.

### V2 · El comando nuevo pierde informativos que el §7 y el §8 sí pedían · GRAVEDAD 2 · CONFIRMADO (por lectura)
- ARCHIVO: `evaluar_con_exclusion.py:56-102` contra `evaluar_diurno_k.py:618-688` (main sellado; idéntico en 68687d2d4 y HEAD, `git diff --quiet` rc=0).
- QUÉ PASA: el main sellado imprime y calcula, y la unión no: la evaluación informativa de W1 (`--w1`, línea 622), `reflejo_sin_pareo`, la línea "¿alguna variante de mínimas cambia el veredicto principal?", el bloque del filtro de reflejo de 12° (apagadas, sin ángulos y el veredicto por sensor con el filtro), la clase "desproporcionada o aislada" del instrumento a) de 1.13 (`desproporcion`) y `noche_records_distintos_en_otros_campos`. El JSON de salida tampoco guarda `reflejo12`. El §7 dice de esas tres últimas "Informativo (el evaluador lo imprime desde la v2)" y el §8 las daba por parte de la evaluación.
- El §11 punto 7 dice que el script "carga lo mismo que el `main()` sellado... y llama a la misma `evaluar_completo`", y eso es cierto, pero no avisa de que el comando pasa a producir menos informativos.
- CÓMO SE VERÍA: no cambia ningún veredicto (todo lo omitido es informativo, no decide). Sí queda sin informe lo que el §7 prometía sobre dependencia del reflejo.
- CÓMO REPRODUCIRLO: comparar las líneas impresas de los dos `main()` con `vu_main.py` (fase `vacia`). Ese run falló con `ArrayMemoryError` (memoria del equipo casi llena), así que la comparación de salida por ejecución es SIN DATO; la diferencia está establecida por lectura del código.

### V3 · La lista de días no se valida · GRAVEDAD 2 · CONFIRMADO (por lectura), efecto SIN DATO
- ARCHIVO: `evaluar_con_exclusion.py:77-78` y `quitar_dias` (línea 36-41).
- QUÉ PASA: `dias = list(exc["excluir_dias"])` se usa tal cual. Un día mal escrito ("2026-3-10"), una lista generada con `--w1` (días de marzo, fuera de W2 a W6), o la lista de otra corrida, no excluye nada y no da error. El único aviso es visible sólo si alguien mira: el diccionario de `lo_que_sale` sale vacío para ese día. El json trae la clave `ventanas` y `consulta_cmr_utc` (los comprobé en `w1/dias_excluidos_w1.json`) y la unión no los cruza con la evaluación.
- CÓMO SE VERÍA: I4 falla por el hueco no excluido (INVÁLIDO), la dirección segura. No hay camino para que un veredicto equivocado salga por esto, sólo para uno inválido evitable.

### V4 · No se informa cuántos records de cada brazo salen · GRAVEDAD 1 · CONFIRMADO
- ARCHIVO: `evaluar_con_exclusion.py:88`.
- QUÉ PASA: se imprime cuántas pasadas de MIROVA salen por día, no cuántos records del control y del brazo. Un denominador que se achica en los records no queda a la vista (el de pasadas sí).

### V5 · El sello es de blobs y casi todo el árbol de trabajo está en CRLF · GRAVEDAD 1 · CONFIRMADO
- ARCHIVO: `objetivos_adenda1_sha256.txt`.
- QUÉ PASA: los 7 sha256 coinciden con los blobs de 038c6904b (ver "Verificado limpio"), pero en el disco de este worktree 6 de los 7 archivos están en CRLF (`git ls-files --eol`: `w/crlf`; sólo `evaluar_con_exclusion.py` está en `w/lf`), así que un `sha256sum` directo da otro valor en 6 de 7. El encabezado del sello lo dice ("git show ... | sha256sum") y el §8 lo avisa para el sello original; el §11 punto 8 no lo repite.
- CÓMO REPRODUCIRLO: `sha256sum experiments/_s163_diurno_k/dias_excluidos_nasa.py` da 4af2a68667..., y el sello dice 912c9d7c20....

### V6 · El conteo "reflejo probable" de la unión difiere del que daría `excluir_dias` · GRAVEDAD 1 · CONFIRMADO
- ARCHIVO: `evaluar_con_exclusion.py:90-93`.
- QUÉ PASA: `evaluar_completo` calcula `reflejo` sobre las pasadas ya sin los días excluidos, así que el número impreso es menor que el que saldría si se aplicara `excluir_dias` dentro de `evaluar` (en ese caso `claves_reflejo` ve también las pasadas del día excluido). Es la única llave que difiere entre las dos semánticas en mis 9 casos (ver abajo). No decide nada: la variante `sin_reflejo` excluye claves que ya no están y da lo mismo.

### V7 · Cobertura de la afirmación "equivale a excluir_dias" más angosta que el texto · GRAVEDAD 1 · CONFIRMADO EN PARTE
- El §11 punto 7 la apoya en W1 (`verificador_adenda1/va_glue.py`, un volcán, una ventana, `evaluar` solo, no `evaluar_completo`). Yo la extendí a `evaluar_completo` (todas las variantes e informativos) sobre W2 a W6, con la referencia real congelada y records sintéticos (ver más abajo). Se sostiene en los 9 casos, con la excepción de V6. Pero el volumen es de dos volcanes y no incluye el predicado real del tablero de un record real: los records son míos y sintéticos.

## Verificado limpio (y contra qué vara)

1. **Camino C1 (el script carga lo mismo que el `main()` sellado)**, por lectura línea a línea contra `main()` de `evaluar_diurno_k.py` en 68687d2d4 (`git show`): misma comprobación de sha de la referencia (con `return 3`), misma lista `ventanas` de `sk.VENTANAS` filtrada por `sk.DECIDEN`, mismo `p_sup_de_vara`, mismo `inner_desde_html`, mismo `cargar_brazo` para los dos lados, mismos `problemas_de_logs`, misma llamada `evaluar_completo(..., ev._filas_1_13())`. Las diferencias son: sin `--w1`, sin `--recorte`, prints omitidos (V2). `git diff --quiet 68687d2d4 HEAD` sobre `evaluar_diurno_k.py`, `scripts/` y `sustrato_k.py` da rc=0: el evaluador sellado no cambió.
2. **Camino C2, medianoche UTC y filas sin fecha**, sobre la referencia real congelada (`congelar_referencia.py --commit 047bd5692`, los 4 sha256 salieron OK) con `vu_medianoche.py` (salida `vu_medianoche_salida.txt`): 45.355 filas, todas con `fecha_utc` de 19 caracteres, 0 fechas vacías; 0 pares consecutivos del mismo volcán y sensor a 120 s o menos con día UTC distinto; 0 filas a ±5 min de medianoche UTC. Horas UTC con filas: VIIRS 4 a 7 y 17 a 20; MODIS 0 a 3, 6 a 9, 12 a 14, 19 a 22. Entonces quitar filas por `fecha_utc[:10]` y quitar pasadas por `instante` dan los mismos grupos en esta referencia. Vara: el criterio de agrupación de `cm.resumir_pasadas` (`clase_mirova.py:240-276`, ±120 s desde la primera fila) y de `aplicar_regla_minimas` (`:130-171`, vecinas a ±120 s).
3. **Equivalencia con `excluir_dias` del evaluador sellado**: `vu_oraculo.py` (salidas `vu_oraculo_salida.txt` y `vu_oraculo_salida2.txt`) parchea `ev.evaluar` para inyectar `excluir_dias` (semántica sellada) y compara `principal` (sin `T`), `variantes`, `final`, `motivo`, `info`, `reflejo12` con el camino de la unión (`quitar_dias` + `evaluar_completo`). Datos: referencia real filtrada a Láscar e Isluga, records sintéticos míos (un record por pasada de MIROVA, uno diurno sólo en el brazo, 7.300 y 12.346 en total; con el filtro quedan 1.210 y 2.059). 9 casos: lista vacía; un día fuera de ventana; primer día de W2; último de W6; 2026-10-13; el día con más protegidas VIIRS (2026-06-24); tres días con protegidas; 5 aleatorios; 15 aleatorios. Resultado: idénticos en todas las llaves excepto `reflejo` (V6) en 3 de 9. Veredicto en todos: DECIDE NICOLÁS CON M4 (los records sintéticos no discriminan veredictos, pero `principal` completo, con compuertas, cobertura y métricas por sensor, es igual).
4. **Sello (C6)**: para cada una de las 7 rutas de `objetivos_adenda1_sha256.txt`, `git show 038c6904b8f481ec9b82da8df0e92cecd9fc1947:<ruta> | sha256sum` coincide con el valor del sello (7 de 7, 10 primeros caracteres comparados en pantalla: 912c9d7c20, b556b079ff, d25ec245fe, 0a20e4d51e, c18a56f85f, c8544620cd, 42ee48f761); y los blobs en a1604e253 son los mismos. El commit 038c6904b existe (`git cat-file -t` = commit).
5. **Pruebas**: `python -m pytest -q -p no:cacheprovider experiments/_s163_diurno_k/test_evaluar_con_exclusion.py` en el worktree: 4 passed en 2,80 s (en la copia de `git archive`, 4 passed en 9,61 s). La prueba de equivalencia no es vacía: termina afirmando que, sin el 26 de julio, `P_obs` de VIIRS 375 es 1, y las mutaciones G1, G2, P6 y P8 caen por aserción.
6. **Texto de los puntos 7 a 9 contra el script**: el comando que da el punto 7 coincide con los argumentos del `argparse` (`--raiz`, `--ref`, `--sha-codigo`, `--opcion-e`, `--excluidos` todos requeridos; `--salida` opcional). Las claves que lee la unión (`excluir_dias`, `consulta_cmr_utc`, `evidencia`, `informativo_regla_b`) existen en `w1/dias_excluidos_w1.json`. "5 de 5 mutaciones atrapadas" coincide con `mutaciones_exclusion_salida.txt`.
7. **Camino C9 (efectos laterales)**: el script sólo importa `evaluar_diurno_k` y no parchea nada; no modifica estado global del módulo sellado.

## SIN DATO

- **`main()` de punta a punta**: lo intenté con `vu_main.py` (sellado contra unión con lista vacía, y unión con lista contra sellado con `excluir_dias` inyectado). Falló con `numpy ArrayMemoryError` por memoria casi llena del equipo y llegó la parada por disco antes de reintentar. Quedó SIN DATO que el `main()` de la unión produzca el mismo JSON que el sellado con lista vacía, y que `--salida` guarde lo esperado. La equivalencia de las piezas (`quitar_dias` + `evaluar_completo`) sí está medida (limpio 3); el cableado de `main()` sólo está leído.
- **Comparación pasada a pasada sobre la referencia completa** (`vu_pasadas.py`): se cortó por tiempo (la salida no llegó a imprimir resultados). Vale lo medido en limpio 2 y 3.
- **Records reales de W2 a W6**: no existen todavía. El comportamiento con records reales cerca de medianoche UTC queda SIN DATO (los de VIIRS no tienen pasadas entre las 21 y las 3 UTC en la referencia).
- **Punto 9 del §11** ("el 2026-10-13 Suomi NPP no tiene gránulos de noche... no debería tocar I3 ni I4 (inferido, no medido)"): no lo medí; sigue siendo inferencia.
- **Que `test_evaluar_diurno_k.py` (del que importa `test_evaluar_con_exclusion.py`) esté sellado en `objetivos_sha256.txt`**: no lo comprobé.
- **Mutaciones**: ver el aviso del comienzo. Su valor, si se descartan, es SIN DATO.

## QUÉ NO MIRÉ

- `dias_excluidos_nasa.py` y su batería, más allá de las claves de su salida y de que el sello cubre sus blobs (otro verificador, `verificador_adenda1`, ya lo revisó).
- El fondo de la regla (a y b'), la adenda 1 completa fuera de los puntos 7 a 9, y los puntos 1 a 6 del §11.
- El evaluador sellado, el criterio de victoria, las compuertas I1 a I6 y la regla del §6: fuera de alcance (sólo los usé como oráculo).
- Que el CMR devuelva lo que dice (no consulté CMR).
- Ejecución en GitHub Actions, `pipeline/`, `data/`, `frontend/`.

## Carpetas y archivos temporales míos (no los borré)

- `C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile--claude-worktrees-s163-diurno-k-prereg-5c4f44\d4808e35-4a6a-4e99-80bf-6928d55b754c\scratchpad\ref_union` (11 MB, referencia congelada)
- `...\scratchpad\vu_raiz` (6,7 MB, records sintéticos)
- `...\scratchpad\vu_arch` (3,7 MB, copia `git archive` de a1604e25 para las mutaciones)
- `...\scratchpad\vu_main_tmp` (2 KB)
- En esta carpeta (`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s163-diurno-k-prereg-5c4f44\experiments\_s163_diurno_k\verificador_union\`): `CAMINOS.md`, `vu_pasadas.py`, `vu_fixture.py`, `vu_oraculo.py`, `vu_main.py`, `vu_medianoche.py`, `vu_mut.py` y sus salidas `vu_*_salida*.txt`.
- Dejé un proceso mío (`vu_pasadas.py`, PID 39476) y lo terminé por ese PID cuando vi que llevaba horas. No terminé ningún otro proceso (hay otros de otras sesiones corriendo, que no toqué). Al final no queda ningún proceso `vu_*` en marcha.

## Conclusión

CONFORME CON REPAROS. Con la referencia real y records sintéticos, la unión da lo mismo que `excluir_dias` en todo lo que decide, y el sello coincide con los blobs. Los reparos: `main()` no tiene prueba (V1, gravedad 3) y el comando nuevo pierde informativos del §7 y el W1 informativo (V2, gravedad 2); recomiendo cubrirlos antes de usar la unión en W2 a W6.
