# Verificador con contexto limpio: PR #841 (`unir_intentos.py`, tolerancia y píxel de borde)

Rama `loop/unir-intentos-tolerancia`, commit `78195b031`, worktree
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\agent-a9001c0df75a6eea6\`.
CI del PR: `CLEAN`, 1 check `SUCCESS` (`gh pr view 841`). No edité el repo.

## Veredicto: MERGEABLE CON ARREGLOS

La tolerancia está bien calibrada y sobre V2a sólo deja pasar ruido de máquina. La lista de campos de decisión
está completa para los cinco consumidores. Pero hay un hueco permisivo en la clave (heredado de la vuelta 68, y
que el PR lleva a `main` por primera vez), el mecanismo del «píxel de borde» está mal descrito, y la red de
seguridad principal (el predicado del tablero) no tiene ningún test que muera si se la desconecta.

## 1. Reproducción

`C:\Users\nmend\AppData\Local\Temp\claude\verif_841\a1_reproducir.py` (salida en `a1_resumen.json`): sobre los
22 archivos de V2a, unen 20 y no unen Isluga y Nevados de Chillán control, igual que el autor. Se admiten 8
records por borde, todos de Copahue control; en Isluga y Chillán quedan 2 y 4 de borde más 1 bloqueado cada uno.

Campos que difieren en los 4.209 records `tolerancia`/`orden` (todos los campos, recursivo, fuera de las listas
de píxeles): sólo `diag_mu_deti` (4.207, máx. 5,1e-10 relativo), `diag_sd_deti` (4.157, máx. 4,0e-12) y
`final_hotspot_lat` (2, 1,9e-16, un ulp). La tolerancia no deja pasar nada que no sea ruido. Margen: el ruido
observado está a un factor 2 de `REL_TOL = 1e-9`; si otro runner da 1,5e-9, la unión falla, en la dirección segura.

## 2. Campos de decisión (ataque 1)

Barrí los 61 campos del record (más los anidados de `primary_cluster`) contra `scripts/banco_paridad.py`,
`experiments/_s146_ab_sin_test1/evaluar.py`, `experiments/_s151_prereg_fk_11/evaluar_fk.py`,
`experiments/_s151_ab_diurno/evaluar_diurno.py`, `experiments/_s149_prereg_invierno/armar_tabla.py`,
`experiments/_s146_ab_sin_test1/contar_pasadas.py` y `scripts/clase_mirova.py`, y leí cómo los lee cada uno
(A89). **No falta ninguno.** Todo lo que se lee está en `CAMPOS_DECISION`, en la clave o dentro de
`primary_cluster` (que se compara entero, incluidos `geo_class`, `focal_magnitude`, `single_pixel_mode`). El
predicado del tablero sólo ve el recorte `CAMPOS_JS` (`banco_paridad.py:136`), así que lo que el JS lee fuera de
ahí (`t_bg_k`, `final_hotspot_dist_km` en paneles) no decide.

Observación de diseño: `CAMPOS_DECISION` y `DERIVADOS_DEL_BORDE` son disjuntos, así que
`c in CAMPOS_DECISION or c not in DERIVADOS_DEL_BORDE` (`unir_intentos.py:161`) equivale a
`c not in DERIVADOS_DEL_BORDE`. Quien bloquea de verdad es la lista cerrada de derivados; `CAMPOS_DECISION` es
documentación. Por eso la mutación «sacar `sensor_zenith_deg` de CAMPOS_DECISION» sobrevive (sección 6). No es
un defecto, pero conviene decirlo en el docstring para que nadie crea que agregar un campo a CAMPOS_DECISION
cambia algo.

`sensor_zenith_deg` está sobreincluido para MODIS: `evaluar_fk.py` nunca lee la clave `z` que le entrega
`armar_tabla.py:45` (grep: 0 usos), y el único lector en la cadena es `banco_paridad.py:464-469`
(`cenital_neg_v375`), que filtra `r["b"] == "VIIRS375"` y es informativo. El de
`experiments/_s149_prereg_invierno/medir_predicciones.py:31` es de otro pre-registro.

## 3. El mecanismo NO es un píxel en el borde del umbral (corrige el docstring, l. 20-24 y 57-60)

`a3_empates.py` (salida `a3_salida.txt`): en los 16 records con conjunto distinto la lista
`anomaly_pixels + discarded_anomaly_pixels` mide **exactamente 100**, con `n_anomalous_pixels` de 273 a 789, y
**todo píxel que entra o sale tiene el mismo `vrp_mw` que el mínimo de la lista**, valor que comparten de 1 a 45
píxeles. Es el corte TOP-100 de `pipeline/process_modis.py:1085`, `np.argsort(-per_pixel_vrp_mw)[:100]`, que no es
estable: entre píxeles empatados el orden depende de la implementación del sort. La máscara de detección es la
misma en los dos intentos (`n_anomalous_pixels` y `primary_cluster` idénticos en los 16). Luego
`pipeline/store.py:285-301` reparte esa lista por distancia y recalcula `vrp_mir_mw` y `hotspot_*`, y de ahí salen
los derivados distintos. SOSPECHA no verificada: que el orden de los empates cambie con la CPU por el despacho
SIMD del sort de numpy (mismo patrón que OpenBLAS en el ETI).

Consecuencias para el texto: (a) «un píxel en el borde del umbral entra o sale con el ruido de la regresión» es
falso: ningún píxel cruza un umbral; (b) «0 a 2 píxeles» es la diferencia de conteos, pero se intercambian hasta
8 píxeles por lado (Copahue MODIS_TERRA 2026-04-18 01:45); (c) «campos difusos de 56 a 90 píxeles» son los
tamaños de la lista recortada, los campos tienen 273 a 789.

Los dos residuales tienen además un **empate en el máximo**: Isluga MODIS_TERRA 2026-03-28 01:15 tiene dos
píxeles con 3,3930 MW y Chillán MODIS_AQUA 2026-04-17 07:30 dos con 2,6865 MW. El que el sort deja primero pasa a
`final_hotspot` (`process_modis.py:1097` y `1307`), y con él la geometría evaluada ahí
(`process_modis.py:1568-1572`, «NO entran en detección ni magnitud», l. 268-271). No es que el borde cambie el
píxel más caliente: hay dos igual de calientes.

## 4. Hueco permisivo de la clave (bloqueante para el uso general, no afecta a V2a)

`clave()` (`unir_intentos.py:106-107`) incluye `granule`. Los evaluadores agrupan por pasada sin granule:
`evaluar.py:109-110` (`vol, b, minuto`), `evaluar_diurno.py:253` (`vol, sensor, minuto`), `evaluar_fk.py:145`. Si el
intento 2 trae la misma pasada con otro gránulo (NRT contra estándar, o un reproceso de NASA entre intentos), la
unión los trata como pasadas distintas y entrega **las dos**. `a6_residuales_y_granulo.py`: misma pasada, otro
`granule`, `product_version = nrt` y `vrp_mw = 99` en el intento 2: `ok = True`, unión de 2 records, 0 comunes.
Aguas abajo `armar_tabla.py:43` (`tabla.setdefault(...)[rol] = ...`) se queda con el último, que por el orden
estable de `unir_intentos.py:240` es el del intento 2: se viola en silencio «se conserva el record del primer
intento», y `evaluar.py::cargar_brazo` lo cuenta dos veces. En V2a hay 0 colisiones (`a1_reproducir.py`), así que
el resultado de hoy no cambia. Arreglo mínimo: indexar también por `(sensor, datetime_utc)` y, si en un intento
posterior aparece la misma pasada con otro `granule` o `product_version`, bloquear (o informarla como cobertura,
igual que `evaluar_diurno.py:415-420`), con un test.

## 5. Los 2 archivos residuales (ataque 3)

Bloquear no es incorrecto (es la dirección segura), pero no hace falta decidir nada sobre esos records:

* **El predicado del tablero da lo mismo** con los dos records de cada par (`a6_salida.txt`: diferencias `[]`).
* **El intento 2 solo ya cubre la unión entera** en esos dos archivos: Isluga 457 / 457 / 457 claves y Chillán
  547 (i1) / 550 (i2) / 550 (unión). Más aún: en 21 de los 22 archivos el intento 2 por sí solo tiene todas las
  claves de la unión. El único que necesita mezclar de verdad es Chaitén del brazo sin Test 1 (598 / 595 / 601),
  y ahí los 592 comunes son `igual` exacto: la regla estricta de la vuelta 68 bastaba.

Opciones y su efecto en la cobertura:

| opción | cobertura | qué mezcla | comentario |
|---|---|---|---|
| **A. Usar el intento completo entero** cuando uno solo cubre todas las claves de la unión (el primero en el orden de la línea de comandos que lo haga); comparar los comunes igual, sólo para informar | igual a la unión (Isluga 457, Chillán 550) | nada | **recomendada**: no hay records de dos corridas en un mismo archivo; los 8 de borde de Copahue tampoco haría falta admitirlos (i2 de Copahue control también está completo) |
| B. Conservar el primer intento e informarlo: tratar `sensor_zenith_deg` (y los otros tres ángulos) como derivado cuando el sensor no es VIIRS 375, igual que la condición de `anomaly_pixels` | igual a la unión | 2 records | defendible porque ningún veredicto de F/K lee la zona en MODIS; exige un test que fije la condición |
| C. Excluir la pasada de los dos brazos | pierde 1 pasada MODIS en Isluga y 1 en Chillán | nada | peor: hay que coordinar la exclusión entre brazos y cambia el denominador; sin beneficio |

`evaluar_fk.py` no usa la zona del barrido para nada que entre en el veredicto (sección 2).

## 6. G3 de `evaluar_diurno.py:420` (ataque 4)

Sí: G3 compara las listas **posicionalmente** (`evaluar_diurno.py:386-401`), así que vería como diferencia no sólo
los records de borde sino también los de orden. `a4_g3.py` simulando el record del intento 2 como si fuera el del
otro brazo: G3 marca diferencia en 8 de 8 `orden`, 14 de 14 `borde` y 2 de 2 bloqueados, y en 0 de los 4.201
`tolerancia`. Los campos: `anomaly_pixels` (22), `discarded_anomaly_pixels` (15), `discarded_n_pixels` (7),
`vrp_mir_mw` (7), `hotspot_*` (1). No lo crea la unión: entre los dos brazos, que son jobs distintos, el mismo
empate del sort puede dar FALLA de G3 (falso «defecto del cableado», dirección segura: INDECIDIBLE). Pero la unión
y G3 quedan con estándares incoherentes: lo que la unión declara «mismo pipeline» G3 lo declara cableado roto.
Para F/K no aplica: `evaluar_fk.py` no tiene G3 campo a campo, su determinismo compara sólo `pub`
(`evaluar_fk.py:516`). Recomendación aparte (otro PR): que G3 compare las listas de píxeles como multiconjunto
y acepte el intercambio de empates con la misma regla.

## 7. Mutaciones (ataque 5, A116)

`a5_mutar.py` (salida `a5_salida.txt`) escribe cada mutante en `verif_841\mut\` y corre una copia del test del PR
contra él. Control sin mutación: 20 pasan (node disponible, ningún test saltado).

| mutación | resultado |
|---|---|
| quitar el chequeo VIIRS 375 sin núcleo | muere |
| quitar el chequeo de `vrp_mir_mw` sin cúmulo | muere |
| abrir la lista cerrada (sólo CAMPOS_DECISION bloquea) | muere |
| conservar el ÚLTIMO intento | muere |
| orden cuenta como borde | muere |
| un `distinto` con conjunto igual pasa a unir | muere |
| **ignorar el resultado del predicado (`malos = []`)** | **sobrevive** |
| **sacar `granule` de la clave** | **sobrevive** (no hay test del caso de la sección 4) |
| quitar la condición «campo presente en un intento y ausente en el otro» | sobrevive (sólo pierde el caso None contra ausente) |
| quitar `abs_tol` de `math.isclose` | sobrevive (ningún test ejercita el piso absoluto) |
| `bool` comparado con `==` en vez de `is` | sobrevive |
| el multiconjunto reutiliza elementos | sobrevive |
| sacar `sensor_zenith_deg` de CAMPOS_DECISION / pasar `triggered_test1` a derivados | sobreviven, equivalentes (sección 2) |

La importante es la primera: el chequeo (d), que el docstring presenta como la red de seguridad, no tiene un test
que muera si `unir()` ignora lo que devuelve el predicado. `test_el_predicado_puede_dar_distinto` prueba
`_predicado` suelto y `test_sin_predicado_un_record_de_borde_no_une` sólo la rama de la excepción. Basta un test
con `monkeypatch` de `_predicado` que devuelva `[0]` y exija `ok = False`.

## Arreglos pedidos antes de mergear

1. Clave: detectar la misma pasada `(sensor, datetime_utc)` con otro `granule` o `product_version` y bloquear o
   informarla como cobertura, con test (sección 4).
2. Test que mate «ignorar el predicado» (sección 7).
3. Corregir el mecanismo en el docstring y en el test (l. 6 del test dice «un pixel en el borde del umbral»):
   empates en el corte TOP-100 de `process_modis.py:1085` (sección 3).
4. Opcional y barato: tests del piso absoluto y de None contra ausente.

Para los 2 residuales: opción A (intento completo entero). Si se prefiere mantener la unión record a record,
opción B con su test.

## Scripts y salidas

`C:\Users\nmend\AppData\Local\Temp\claude\verif_841\`: `a1_reproducir.py` + `a1_resumen.json`, `a2_borde.py` +
`a2_salida.txt`, `a3_empates.py` + `a3_salida.txt`, `a4_g3.py` + `a4_salida.txt`, `a5_mutar.py` + `a5_salida.txt`
+ `mut\`, `a6_residuales_y_granulo.py` + `a6_salida.txt`.
