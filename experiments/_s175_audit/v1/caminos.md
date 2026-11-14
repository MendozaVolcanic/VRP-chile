# Caminos por los que cada afirmación del frente F1 podría estar mal

Verificador V1, S175. Escrito antes de abrir ningún archivo citado. Sólo conozco el título, el
archivo:línea, la gravedad y el comando de cada afirmación. No se vuelve a editar después del sha256.

## 151. La vigilancia no comprueba que el record de producción sea de la vía (gravedad 4)

1. Flag leído de otro lado: la vigilancia podría filtrar por `via_codigo_mirova` o por `detector`
   en una función distinta de las líneas 200-203 o 171 (helper importado, prefiltro al cargar).
2. El caller transforma el argumento: quien llama a la comparación podría pasar ya sólo records de
   la vía (por ejemplo, cargando desde un subdirectorio o filtrando por `processed_utc`).
3. La mutación M6 podría medir otra cosa: si el script del auditor fabrica un record K sin el campo
   que la vigilancia sí mira, la "caída que calla" sería un artefacto del montaje, no del código.
4. La consecuencia ("dispara la reversión pre-autorizada") depende del texto de la regla en el
   borrador l. 189: la regla podría pedir confirmación humana o un segundo criterio antes de revertir,
   y entonces el disparo automático no existe.
5. Un segundo camino: `scripts/revisar_errores_modis_nrt.py` u otro vigilante podría avisar la caída
   a K por separado, y la ausencia en este script no implicaría ceguera del sistema.
6. La copia local (root_base) podría estar atrasada respecto de 752d348bc o main de hoy.
7. Que el record caiga a K "en silencio" podría no ser posible: si al caer a K el pipeline marca
   `via_codigo_mirova: false` con motivo (`sin_grilla`, `sin_mxd03`), la vigilancia podría verlo
   por otro campo.

## 152. Vigilante ciego por volcán (gravedad 4)

1. Agregado vs por volcán: la vigilancia podría tener una comprobación por volcán en otra función
   (no en 345-358 ni 304), por ejemplo un conteo por volcán al construir el informe.
2. El contraste con `vigilancia_sombra.py:362-365` podría no ser equivalente (otro objetivo, otro
   insumo), y entonces "contraste" no prueba omisión.
3. M2 y M2c podrían borrar los records de un volcán de un modo que también rompe otra cosa (por
   ejemplo dejar el archivo vacío con otro esquema) y lo que se ve verde sería otro efecto.
4. Ventana: si el volcán mutado no tiene noches en la ventana de la vigilancia, el VERDE sería
   correcto (no había nada que vigilar), no ceguera.
5. La vigilancia podría avisar por otro canal (exit code, issue, archivo de estado) que el script
   del auditor no lee.

## 153. El descarte de borde de la vía (171-01) no deja rastro (gravedad 3)

1. El rastro podría estar en otro lugar: log de nivel DEBUG, un campo del record de la pasada
   siguiente, un JSON de diagnóstico, el log de Actions con otro texto.
2. La pasada Villarrica MODIS_AQUA 2026-11-04 07:10 UTC podría faltar por otra causa (sin gránulo,
   caída de red, gránulo diurno, fuera de ROI) y no por el descarte de borde.
3. La comparación de claves guardia_k vs mirova_equivalent en e75a7d52d puede tener formatos de
   datetime distintos (con y sin segundos, Z vs +00:00) y dar falsas ausencias.
4. La guardia K podría correr con otra geometría y generar pasadas que la vía nunca tendría, sin que
   eso sea "descarte" (diferencia esperada).
5. El job 41812405190 podría ser de otro volcán u otra pasada.
6. `revisar_errores_modis_nrt.py` podría sí ver el descarte por otro patrón.
7. Que la vía devuelva None podría hacer caer a K en vez de descartar; entonces sí habría record.

## 154. §4.1 y §4.7 suponen re-escritura de 8 días que el almacén no hace (gravedad 3)

1. La re-escritura podría estar fuera de store.py: en `nrt.yml` con un paso de reproceso de
   ventana, en `run_pipeline.py` con `--overwrite` por defecto en NRT, o en otro workflow.
2. La lectura del texto de la regla (l. 162, 318) podría no suponer re-escritura sino sólo
   re-lectura de 8 días.
3. El upgrade NRT a estándar (store.py) sí re-escribe dentro de la ventana de llegada de los
   productos estándar; si esa ventana ronda 8 días, el supuesto de la regla sería válido.
4. El censo con `processed_utc` podría no distinguir re-escritura de primera escritura.
5. Copia de datos e75a7d52d atrasada respecto de hoy.

## 155. §4.3 pide confirmar en mirova-tif-archive pero los TIF dejaron de capturarse el 2026-09-22 (gravedad 2)

1. El índice tif_index.csv en insumos podría estar atrasado respecto del repo remoto.
2. El máximo de `captured_at_utc` podría reflejar el md5 congelado (MIROVA sirve el mismo TIF) y no
   que el capturador se detuvo; la diferencia importa para el arreglo, no para el hallazgo.
3. §4.3 podría aceptar PNG como alternativa.
4. Formatos de fecha mezclados en la columna podrían hacer que max() lexicográfico mienta.

## 156. El audit semanal deja de dar flag por las protegidas MODIS que K no publicó en cuanto la vía tiene records (gravedad 2)

1. Podría ser diseño explícito y anunciado (el flag pasa a VIA_MODIS u otra sección), y entonces no
   hay pérdida de vigilancia sino traspaso.
2. La condición podría ser por record y no por presencia global de la vía.
3. El script podría no correr en root_base (dependencias), y su salida no sostendría nada.
4. El flag nuevo de la vía podría cubrir las mismas protegidas.

## 157. El recall de VIA_MODIS no puede dar flag hasta 15 noches con alerta (gravedad 2)

1. El mínimo de 15 podría ser para otra métrica y el recall usar otro umbral.
2. Las "2 noches en 5 días" dependen de la ventana y del corpus vivo (A90): proporción y ventana.
3. Podría existir otra alarma que sí da flag antes (por ejemplo pérdida individual de protegida).
4. Un mínimo de muestra puede ser deliberado y correcto estadísticamente; el hallazgo sería de
   diseño, no de bug.

## 158. El encendido se cuelga de un solo record y un reproceso con --overwrite lo movería (gravedad 2)

1. `encendido_desde_datos` podría usar un mínimo sobre varios records o una fecha fija de respaldo.
2. store.py:541 podría preservar `processed_utc` original al sobre-escribir.
3. Un reproceso con --overwrite podría no tocar los records de la vía (otro data_subdir).
4. Mover el encendido hacia adelante podría no cambiar nada operativo (sólo la ventana del audit).

## Caminos transversales

- La vara del frente F1 es la definición de "detector efectivo"; no puedo usarla como vara.
- Copias locales (root_base, datos/e75a7d52d) vs 752d348bc: verificar sha o diff antes de creer.
- Scripts del auditor que "atrapan" por caída y no por aserción (S152).

---
sha256 del contenido anterior a este pie: f4748bb21903f66d2cfcf420f8e4438f84f2952ff2f55cece0a9baa9f5ea8f9c
Hora del servidor (GitHub, header Date: Sat, 07 Nov 2026 20:31:12 GMT)
