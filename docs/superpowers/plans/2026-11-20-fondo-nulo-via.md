# Fondo nulo en la vía «código MIROVA»: plan de implementación (S192)

> **Para agentes:** ejecutar tarea por tarea con `executing-plans`; los pasos usan casillas (`- [ ]`).

**Objetivo:** que la vía deje de publicar como VRP la radiancia entera de un píxel cuando no pudo estimar su fondo:
en MODIS esa escena pasa a «no medida»; en VIIRS 375 y 750 se conserva la detección (MIROVA hace lo mismo) y el record
lo marca.

**Decisión:** Nicolás, 2026-11-20, respuesta «Sí, opción (a)» a «¿Apruebas la opción (a) del fondo nulo, extendida a los
34?» (S192). La opción (a) es la de F4-101 §6 y de `D:\codex-vrp\_salida\ronda2\PROPUESTA_F2_PARA_NICOLAS.md` §1:
MODIS escena no medida, VIIRS sólo marca. Tag A45: `pre-s192-fondo-nulo` (sobre `ab28719d3`).

**Por qué (fenómeno):** el VRP es el exceso de radiancia del píxel caliente sobre la del suelo que tendría sin la
anomalía. El código de MIROVA estima ese suelo interpolando vecinos tras sacar un halo; si el alertado está junto a un
hueco de datos (borde del barrido o del gránulo), el halo se come los vecinos útiles y el fondo queda vacío
(`fillmissing2` no extrapola). El `.m` lo suma con `omitnan`, o sea como cero: el VRP publicado es la radiancia total. En
una alerta chica el suelo explica de 0,68 a 0,80 de esa radiancia (verificador del frente 2). En MODIS, MIROVA no tiene
ninguna detección con fondo 0 en 262.455 del OSF v2.5; el fondo 0 nace de correr el código de VIIRS 750 con bandas MODIS
(D36), y el único caso cotejable (Cordón Caulle 2026-03-16 03:10 MODIS Terra, 2,535 MW) MIROVA lo listó sin alerta. En
VIIRS el OSF sí tiene fondo 0 (501 en 375 y 464 en 750): ahí la vía es fiel y no se toca la cifra.

**Arquitectura:** `vrp_mirova` sigue siendo el port literal del `.m` (sólo agrega el conteo de alertados sin fondo, que
no cambia ningún valor). La decisión vive en `procesar_grilla`, que ya decide la forma del record: con `familia ==
"MODIS"` y todos los alertados sin fondo, el record sale por la rama vacía con `motivo_vacio = "fondo_no_estimado"`
(los consumidores ya tratan cualquier `motivo_vacio` como escena no medida: tablero S183, `banco_paridad.py`,
`comparacion_via_k.py`). En todos los sensores el diag gana `alertados_sin_fondo`, y `t_bg_k` se calcula sólo con los
alertados que tienen fondo (nulo si ninguno).

**Archivos:**
- Modificar: `pipeline/mirova_v750_codigo.py` (`vrp_mirova`, `procesar_grilla`, cabecera FICHA).
- Crear: `tests/test_via_fondo_nulo_s192.py`.
- Modificar: `docs/MIROVA_DIVERGENCES.md` (D36: nueva diferencia decidida, MODIS sin fondo = no medida).
- La fila de la ficha SDA va en la descripción del PR (se numera al mergear, regla S185).

### Tarea 1: prueba roja

- [ ] Escribir `tests/test_via_fondo_nulo_s192.py` con la pasada real 3933 (Cordón Caulle 2026-03-16 03:10, grilla
  en `tests/datos_s164_modis/`): MODIS da `vrp_mw == 0.0`, `motivo_vacio == "fondo_no_estimado"`, sin píxeles ni
  cúmulo, y conserva `L_hot` y `alertados_sin_fondo == 1` en el diag; la misma grilla como VIIRS 750 conserva el VRP
  (radiancia × coeficiente de V750), `alertados_sin_fondo == 1` y `t_bg_k is None`; una pasada MODIS normal (1611,
  Láscar 2026-04-25 07:35, 1,112 MW) no cambia y trae `alertados_sin_fondo == 0`; `vrp_mirova` sigue igual al `.m`.
- [ ] Correr: `python -m pytest -q tests/test_via_fondo_nulo_s192.py`. Esperado: rojas las que piden el cambio.

### Tarea 2: implementación mínima

- [ ] `vrp_mirova`: agregar `"n_sin_fondo": int(np.isnan(fondo[mascara]).sum())` al dict (0 en la rama sin alertados).
- [ ] `procesar_grilla`: calcular `sin_fondo_total = familia == "MODIS" and v["npix"] > 0 and v["n_sin_fondo"] ==
  v["npix"]`; si es cierto, `motivo_vacio = "fondo_no_estimado"`, `n_anomalous_pixels = 0` y salir por la rama vacía
  (que ya pone 0 MW y nulos); diag `alertados_sin_fondo`; `t_bg_k` con `L_bk / (npix - n_sin_fondo)` o nulo.
- [ ] Comentario POR QUÉ en el bloque y línea en la cabecera FICHA.
- [ ] Correr la prueba nueva (verde) y `tests/test_mirova_modis_codigo_s164.py`, `test_mirova_v750_codigo_s162.py`,
  `test_mirova_v375_codigo_s165.py`, `test_guard_regla_posicion_radiante_s186.py`, `test_techo_bt_por_sensor_s190.py`,
  `test_vecinos_sombra_34_s173.py`.

### Tarea 3: control del instrumento y suite

- [ ] Mutaciones en copia: quitar la condición de familia, cambiar `==` por `>`, dejar `t_bg_k` con `npix`; cada una
  debe caer por aserción (no por error).
- [ ] Suite completa en segundo plano; comparar con la línea base de `main` (A112).
- [ ] Verificador Claude de contexto limpio sobre el diff (sin mi conclusión).

### Tarea 4: documentos y PR

- [ ] D36 en `docs/MIROVA_DIVERGENCES.md`.
- [ ] PR con la fila de ficha propuesta, la evidencia, y el plan de reemplazo de datos: los 6 records MODIS de los 11
  principales y los MODIS de la historia de los 34 con `L_bk = 0` se reescriben después del merge reprocesando esas
  pasadas con `--overwrite` (los VIIRS no cambian de valor; ganan la marca sólo al reprocesarse).
