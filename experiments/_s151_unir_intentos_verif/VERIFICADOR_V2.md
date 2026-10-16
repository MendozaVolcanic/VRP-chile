# Verificador, segunda vuelta: PR #841 en `dd4cae1dd`

El worktree `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\agent-a9001c0df75a6eea6\`
está en `dd4cae1dd`, sin cambios locales. No edité el repo. Scripts y salidas: `v2_a7_*`, `v2_a8_*`, `v2_a9_*`,
`v2_cobertura.*`, en `C:\Users\nmend\AppData\Local\Temp\claude\verif_841\`.

## Veredicto: MERGEABLE CON ARREGLOS (queda un bloqueante, de arreglo chico)

## 1. Lo que se cumple, medido

- **Las uniones del autor se reproducen.** Rehíce la unión con el código de `dd4cae1dd`
  (`v2_a7_reunir.py`): los 22 archivos dan `ok`, los records son idénticos a los de
  `...\scratchpad\union_v2a\`, 21 en modo intento entero y sólo Chaitén del brazo sin Test 1 en mezcla (592
  comunes `igual`).
- **La cobertura de las uniones queda pareja.** `contar_pasadas.py --control <union>\_s146_ab_control --brazo
  <union>\_s149_ab_sin_test1_b22_max --inicio 2026-03-01 --fin 2026-04-20` da 5.876 pasadas en el control y
  5.876 en el brazo, 0 faltan y 0 sobran, «COBERTURA PAREJA», salida con código 0 (`v2_cobertura.txt`).
- **La clave sin gránulo no fusiona pasadas legítimas.** `(sensor, datetime_utc[:16])` es exactamente la clave
  con que el propio pipeline deduplica al guardar (`pipeline/store.py:650-653`, `(datetime_utc, sensor)`). Un
  archivo de salida no puede tener dos records con esa clave. Los 11.746 `datetime_utc` de V2a miden 16
  caracteres (al minuto), así que el recorte `[:16]` no cambia nada. NOAA-20, NOAA-21 y Suomi NPP llevan nombres
  de sensor distintos (`VIIRS_NOAA20`, `VIIRS_NOAA21`, `VIIRS_SNPP`, más sus `_750`), y dos gránulos de un mismo
  satélite no empiezan en el mismo minuto. El caso que sí cae en la misma clave (NOAA-20 v2 contra v2.1, o NRT
  contra estándar) es la misma pasada, y el store ya la colapsa. Agruparlas es correcto.
- **El mecanismo está bien descrito ahora** (docstring, sección 2: empates en el top-100 de
  `process_modis.py:1085`).
- **Mutaciones** (`v2_a8_mutar.py`, test de 31 casos): de 17 mutantes mueren 16, incluidas las tres que
  sobrevivían en la vuelta 1 (ignorar el predicado, gránulo en la clave, `abs_tol`) y las del modo entero
  (intento parcial, último completo, `docs[0]`, modo desactivado). El único que sobrevive es quitar
  `len(set(ks)) == len(ks)` en el modo entero. Es menor: por `store.py:650` un intento no puede traer duplicados.

## 2. Bloqueante: en modo intento entero una diferencia REAL sólo se informa

`unir()` (`unir_intentos.py`, bloque `if entero is not None:`) devuelve `ok = True` antes de mirar
`distintos`, y antes de correr el predicado sobre los records de borde. `v2_a9_entero_permisivo.py` toma Láscar
control de V2a y cambia **un** record común del intento 2 (el que se entrega entero). Con `triggered_test1`
invertido, `distance_class = summit`, `vrp_mw = 99` o `product_version = nrt`, en los cuatro casos da
`ok=True, modo=intento_entero`, y la diferencia queda sólo en `distintos_informados`. Los tests lo fijan como
comportamiento deseado: `test_misma_pasada_otro_granulo_no_sale_dos_veces` exige `ok` con `vrp_mw` 5 contra 99,
y `test_intento_que_cubre_todo_se_usa_entero_e_informa` hace lo mismo con `sensor_zenith_deg`.

**Por qué no es aceptable.** Que el intento entero sea consistente por sí solo resuelve la mezcla, no la pregunta
que justifica comparar los comunes: ¿los dos intentos son el mismo código y el pipeline es determinista en lo
que decide? Si dos corridas del mismo commit discrepan en un campo de decisión más allá del ruido, hay dos
lecturas. O los intentos no son del mismo código, y entonces el A/B mezcla versiones entre brazos. O el pipeline
es no determinista en ese campo, y entonces la diferencia entre brazos ya no se puede atribuir al flag. En
cualquiera de las dos el veredicto F/K pierde sentido, y nadie lo ve, porque `evaluar_fk.py` no lee
`_union_intentos`. Un `product_version` o `granule` distinto en un común es A108: hay que repetir el job, no
elegir en silencio. Es bloqueante porque D-13 automatiza esta herramienta para todos los A/B largos.

**Regla propuesta, la misma en los dos modos:**
1. Los comunes se clasifican siempre con `comparar` y el predicado se corre sobre los de borde.
2. Cualquier `distinto` que sobreviva bloquea, también en modo entero. Sólo cambia qué se entrega cuando no hay
   distintos: el intento entero si uno cubre todo, la mezcla si no.
3. Para que los dos residuales no bloqueen sin motivo: `sensor_zenith_deg` cuenta como derivado cuando el
   sensor no es VIIRS 375. Su único lector en la cadena F/K es `banco_paridad.py:464-469`
   (`cenital_neg_v375`, filtra `VIIRS375`). `evaluar_fk.py` no lee `z`.

Lo probé como mutante (`mut\unir_propuesta.py`, generado por `v2_a7_reunir.py`): sobre V2a **sigue uniendo 22
de 22**. Los dos residuales pasan a borde con el predicado igual (Isluga 3, Chillán 5), y la salida es la misma
que hoy. Con la regla propuesta mueren 4 tests del PR (`v2_a8`, mutante «entero bloquea si hay distintos»), y
son justo los que fijan el comportamiento permisivo: hay que reescribirlos. Un `vrp_mw` 5 contra 99, un gránulo
o una versión distinta deben dar `ok = False`, y `sensor_zenith_deg` en MODIS debe quedar admitido como borde.

## 3. Menores

- Falta un test que mate «entero sin chequeo de duplicados» (o se puede quitar la condición, citando `store.py:650`).
- Sigue pendiente, fuera de este PR, el G3 posicional de `evaluar_diurno.py:386-401` (vuelta 1, sección 6).
