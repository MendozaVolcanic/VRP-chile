# Verificador con contexto limpio: PR #843 (`unir_intentos.py`, categoría `hotspot_escena`, D-16 a)

Rama `loop/unir-intentos-hotspot-escena`, commit `5a1ddae93`. Diff contra la base: sólo
`experiments/_s151_ab_diurno/unir_intentos.py` y `tests/test_unir_intentos_hotspot_escena_s151.py`
(los JSON de `data/` que aparecen contra `origin/main` son commits NRT de main, no del PR). CI `pytest` verde.

## Veredicto: MERGEABLE CON ARREGLOS

Ningún bloqueante para F/K. Dos arreglos baratos antes de mergear (tests faltantes y tres
consistencias geométricas), y una condición previa antes de evaluar el A/B diurno (el G3).

## 1. Premisa del autor (argsort, no nanargmax): CONFIRMADA

* Código: `pipeline/process_modis.py:1085` `np.argsort(-per_pixel_vrp_mw)[:100]`, `:1097-1099` el hotspot es
  `anomaly_pixels[0]`; `:1218-1220` el `nanargmax` sólo alimenta `diag_t_max_dist_km`; `:1399` reemplaza
  `anomaly_pixels` por los del Test 1, así que la lista de la primera pasada no queda guardada.
* Datos (`mutaciones.py`): Llaima C0 09-24 02:05, `diag_t_max_dist_km` 24,06 en los dos intentos y
  `hotspot_dist_km` 24,06 contra 7,1; 10-06 01:45, `diag_t_max_dist_km` 20,17 en los dos y hotspot 19,35
  contra el rescatado. `t_max_k`, `n_anomalous_pixels`, cúmulo y `distance_class` iguales.
* El empate de VRP por píxel como causa sigue siendo SOSPECHA (el autor lo dice); es coherente con radiancia
  cuantizada de L1B, pero no se puede verificar sin la lista de la primera pasada.

## 2. Cadena de P3 en F/K: CONFIRMADA

`evaluar_fk.py:386-388` usa `disp`; `armar_tabla.py` lo copia de `evaluar.cargar_brazo` (`evaluar.py:104-105`,
4.ª salida de node); `banco_paridad.py:129` `disp = mirovaEqVrpDisplay`; `frontend/index.html:1146-1166`
devuelve `pc.vrp_mw` cuando hay cúmulo y `:1289` deja a MODIS en la base. Otros lectores en la cadena:
`evaluar_fk.py` importa de `ev` sólo `cargar_referencia_unificada` y `_hav`, de `bp` `etiquetar`, `parear`,
`indexar_referencia`, `bucket`, `es_alerta`, `_coords_por_volcan`; ninguno lee `vrp_mw`, `hotspot_*` ni
`final_hotspot_*` del record. `fuente` y `z` viajan en `cargar_brazo` pero `evaluar_fk.py` no los lee (grep
de `"z"` y `fuente`: sólo el manifiesto). `control_positivo_control` (`evaluar.py:498`) sí compara `fuente`,
pero no lo llama `evaluar_fk`.
Prueba empírica (`fk_invariancia.py`): uniendo Llaima C0 en orden (1,3) y (3,1), las 461 filas de
`cargar_brazo` difieren sólo en `fuente` (10-06 01:45, escena) y `z` (08-29 01:35, borde de #841, previo).
`disp`, `pub`, `pc_*`, `dc`, `t1`, `n_px`, `granule` idénticos.

## 3. G3 del diurno: la dependencia del orden es real, y ya existía

`g3_orden.py` rehace Copahue `_s151_ab_diurno_on` W2a con el código del PR en los dos órdenes y corre el
`noches_identicas` real contra el control unido. Orden (1,2): entrega entero el intento 1, G3 sin campos
distintos. Orden (2,1): entrega entero el intento 2 y el G3 ve 9 campos en 06-18 07:30 (los de la escena) y
además `anomaly_pixels`/`discarded_*`/`vrp_mir_mw` en 4 noches de borde (06-13, 06-19, 06-21, Terra 06-13),
que es el defecto posicional ya documentado en #841. G3 FALLA lleva a INDECIDIBLE
(`evaluar_diurno.py:750-751`): el error posible es el conservador. No pido bloquear la unión.
**Regla mínima recomendada (en el evaluador, no aquí):** el G3 clasifica cada par nocturno control/diurno con
`unir_intentos.comparar` más el predicado de node; `distinto` hace FALLA; `orden`, `borde` y `hotspot_escena`
se cuentan e informan aparte. Arregla a la vez el orden de la unión y el empate entre jobs de los dos brazos.
Es desviación del pre-registro y va registrada. Hasta entonces no evaluar el diurno sobre uniones con
`hotspot_escena` o `borde`.

## 4. Condiciones de admisión: mutaciones (`mutaciones.py`, 31 casos)

Bloquean bien (24 de 24): VIIRS 375 y 750, `t_max_k` +0,01 K, None o ausente, sin cúmulo, `pc.vrp_mw` +1 %,
`distance_class`, `n_anomalous_pixels`, `diag_t_max_dist_km`, campo nuevo, `granule`, `triggered_test1`,
rescate con `vrp_mw` distinto del cúmulo, con otra etiqueta o sin etiqueta, dos rescates, lado no rescatado
con etiqueta, cambio de fuente sin rescate, `vrp_mw` distinto sin rescate.
Admite y un instrumento estricto bloquearía (7):
* LAX4/LAX5: cambia sólo `solar_zenith_deg` o `sensor_zenith_deg` sin que se mueva el hotspot.
* LAX6: cambia `final_hotspot_*` con fuente `test1` en los dos (el centroide del Test 1 no depende del hotspot).
* LAX7: hotspot a 200 km; LAX3: lado no rescatado con hotspot a 30 km sin rescate (incoherente con `store.py:389`).
* LAX1/LAX2: `vrp_mw` del lado no rescatado x100 o 0. No hay campo que guarde la suma de escena del lado
  rescatado, así que esto no se puede acotar desde el record: sólo el predicado (que lo lee en
  `isValidDetection`, `index.html:1587, 1596`).
Ninguna toca un campo que lea F/K, pero el G3 lee todos. **Arreglo propuesto:** (i) geometría y
`final_hotspot_*` sólo pueden diferir si difiere `hotspot_lat/lon`; (ii) `final_hotspot_*` sólo con rescate, o
con fuente igual y `final == hotspot` en los dos lados; (iii) en el lado rescatado `hotspot_*` igual al
centroide del cúmulo (`store.py:398-400`; se cumple en el caso real: -38,68689 / -71,72522 / 0,657). Los dos
casos reales de V1 y el de Copahue siguen entrando con esa regla.

## 5. Unión de V1: REPRODUCIDA

`union/` (44 de 44 unen) es idéntica a `v1_38639658446\union_d16\` en records y `_union_intentos`
(`comparar_uniones.py`: 0 de 44 distintos). Casos admitidos: Llaima C0 Terra 09-24 02:05 (sólo `hotspot_*`) y
10-06 01:45 (rescate, `vrp_mw` 4,281 contra 3,568 = `pc.vrp_mw`). `contar_pasadas.py` ventana 2026-08-29 a
2026-10-08: 4.820 pasadas en los cuatro brazos, 0 faltan, 0 sobran (`cobertura.json`). Copahue W2a: 1 caso.

## 6. Tests (A116)

77 pasan. Mutaciones propias del código contra el archivo del PR (`plug\mutplug.py`):
* m1 quitar `otro.get("discarded_reason") is None`: **sobrevive** (35 passed).
* m2 quitar `r.get("discarded_reason") == _RESCATE`: **sobrevive**.
* m3 filtro de `escena` con índice equivocado tras el predicado: sobrevive (sólo afecta el informe, porque
  un distinto ya bloquea la unión).
* m4, m5, m6: atrapadas.
El docstring del test dice que cada condición tiene su caso; dos condiciones de `_rescate_coherente` no lo
tienen. Arreglo: dos casos (rescate sin etiqueta o con otra; lado no rescatado con etiqueta) y sus mutaciones
en `MUTACIONES`. Los tests con datos reales leen rutas de `Temp` y se saltan en CI.

## ¿Sirve ya la unión de V1 para F/K?

Sí. Los registros admitidos son idénticos en todo lo que lee `evaluar_fk` (comprobado por la cadena y
cambiando el orden de los intentos), y la cobertura es pareja. Los arreglos de arriba no cambian esta unión.

Scripts: `C:\Users\nmend\AppData\Local\Temp\claude\verif_843\{comparar_uniones.py, mutaciones.py, g3_orden.py,
fk_invariancia.py, plug\mutplug.py}`.
