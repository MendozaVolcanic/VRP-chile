# Tarea 1.8: lo que se declara ANTES de mirar el resultado

> Escrito 2026-10-14 por el loop (tarea 1.8 de `tasks/LOOP_OBJETIVOS.md`), antes de correr ninguna comparación
> contra MIROVA. Va en su propio commit para que el orden quede en la historia. Lo único que se miró antes es la
> factibilidad de aislar los píxeles del cúmulo (una sonda de exploración en el directorio temporal, sin
> referencia de MIROVA): con el centroide sin ponderar de `cluster_hotspots` (`pipeline/clustering.py`) se
> identifica exacto el conjunto de píxeles de la mayoría de los cúmulos de 1 a 3 píxeles, y el resto tiene
> píxeles de VRP 0 que `anomaly_pixels` no guarda.

## 1. Qué se reconstruye y cómo

Para cada record con `primary_cluster` de **1 a 3 píxeles** se buscan, entre `anomaly_pixels` y
`discarded_anomaly_pixels`, `n_pixels` píxeles cuyo promedio simple de lat y lon reproduzca el centroide
persistido dentro de 2e-5 grados (el centroide se redondea a 5 decimales). Si existe, el cúmulo queda
**identificado exacto** y de ahí salen el pico (`max`) y la suma. Si no existe, el record queda **no
reconstruible** y se informa aparte: no se le inventa una suma.

El valor de entrada del modo ("pre") no siempre es la suma del cúmulo:
- sin magnitud focal: pre = suma del cúmulo;
- con `focal_magnitude` y `focal_degraded = true`: pre = el pico (el foco quedó en el píxel pico solo);
- con `focal_magnitude` y `focal_degraded = false`: pre está entre el pico y la suma, y el record no dice cuál
  (no guarda qué píxeles son contextuales). Se evalúa en los dos extremos y se informa si cambia la conclusión.

Los cúmulos de más de 3 píxeles no los toca ninguna variante: conservan el `pc.vrp_mw` persistido.

## 2. Control de la reconstrucción (antes de comparar variantes)

Tolerancia fijada ahora: **|regla actual reconstruida menos `pc.vrp_mw` persistido| <= 0,0015 MW** (los píxeles
se guardan con 4 decimales y el cúmulo con 3). El control **pasa** si se cumple en al menos el **99 %** de los
records identificados exacto con modo activo y más de un píxel (los de un píxel cumplen por construcción y se
cuentan aparte). Control negativo: la misma comparación usando la SUMA en lugar del máximo debe fallar en la
mayoría de esos records; si no falla, el control no distingue nada. Se informan también la tasa de
identificación y los records que fallan, con sus marcas (`focal_magnitude`, `d9_capped`).

## 3. Variantes (declaradas ahora)

| id | regla para cúmulos de 1 a 3 píxeles |
|---|---|
| A | actual: pico si pre < 5 MW, si no pre |
| B_off | el flag apagado: pre (en MODIS con magnitud focal NO es la suma) |
| B_sum | suma de todos los píxeles del cúmulo, ignore el foco |
| C | umbral 1 MW: pico si pre < 1 MW, si no pre |
| D | umbral sobre el pico: pico si el pico < 1 MW, si no la suma del cúmulo |

D se declara porque el fenómeno sugiere que lo que distingue la erupción del reposo es que haya un píxel fuerte
(el borde de un flujo o un cráter incandescente llena el píxel), no que la suma de vecinos marginales pase un
número. Además se informa, sólo como curva descriptiva y no como candidata, el barrido del umbral de C en 0,25,
0,5, 1, 2, 3, 5 y sin tope: un umbral elegido de esa curva no gana nada aquí, se confirma en un A/B (A115).

## 4. Métricas y regla de decisión (fijadas ahora)

- Magnitud publicada = predicado del tablero ejecutado con node (`scripts/banco_paridad.py`), con el
  `pc.vrp_mw` de cada variante. En VIIRS 375 el tablero publica el núcleo F5' (`f5_core_vrp_mw`), que no pasa
  por el modo: ahí se espera que ninguna variante cambie nada, y se mide.
- Pares: pasada nuestra publicada con fila de ALERTA de MIROVA a +-2 min (etiquetas de `banco_paridad`); VRP
  de MIROVA = el del consolidado si la pasada tiene fila ahí, si no el del OCR. Razón = nuestra / MIROVA.
- Regímenes: **erupción** = Nevados de Chillán desde el 2026-09-28; **reposo** = todo lo demás. Chillán en
  erupción se mide en producción y, aparte, en el brazo de control (C0) del run 38560317428.
- Tramos A119: 2026-03-01 a 2026-06-12 (decide la tabla; el OCR aparte) y 2026-06-13 en adelante (tabla y OCR);
  VIIRS desde el 2026-04-01.
- Por variante, sensor, régimen y volcán: n, mediana de la razón con intervalo de 95 % (bootstrap por noche de
  volcán, 2.000 remuestreos), cuartiles, fracción bajo 0,5 y sobre 2, mediana de |log10 razón|.
- **Una variante gana con claridad** sobre A si, sobre todos los pares, la media de la diferencia pareada
  |log10 razón variante| menos |log10 razón A| tiene intervalo de 95 % entero bajo 0, **en reposo y en erupción
  por separado** (o en erupción sin intervalo entero sobre 0 si n < 10), y en ningún sensor con 10 pares o más
  el intervalo queda entero sobre 0. Además no puede cambiar ninguna publicación de una alerta protegida
  (`docs/S151_CRITERIO_CLASE_MIROVA.md`, lecturas A y B).
- Negativos limpios: se informa la magnitud publicada (mediana y suma) y cuántas publicaciones cambian.
- Publicaciones: se cuentan las pasadas cuyo predicado `publica` cambia contra A (tope D9 de 5 MW y regla de
  cirrus de 10 MW incluidos, porque los aplica el tablero o el pipeline antes del modo).
