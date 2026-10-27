# S165: regla de posición «más radiante» contra «cercano» en los tres sensores

Pregunta de Nicolás: «Mide primero, sin tocar pipeline/, cuántas pasadas cambian con la regla "cercano" en VIIRS 750,
MODIS y VIIRS 375, contra la distancia de la tabla de MIROVA. Después decido.»

Sólo lectura. Nada de `pipeline/`, `data/`, `frontend/` ni `.github/` se tocó; no hubo commit, push ni workflow.
Scripts y salidas en esta carpeta; temporales y JSON con el detalle completo en
`D:\vrp-trabajo\temporales\s165_regla_posicion\`.

## El fenómeno, en una escena

La regla importa sólo en una configuración: un píxel débil cerca del cráter y una fuente más radiante lejos (otro
foco, borde de nube, incendio). La vía «código MIROVA» toma el cúmulo 8-conexo de la alertada más radiante, mide la
distancia de su centroide al cráter y, si queda fuera del `inner_radius_km`, el record es `far` y el tablero calla. La
regla «cercano» (la de `experiments/_s162_v375/evaluar.py`) mira el alertado más cercano: el mismo record queda
`summit` y el tablero publica el VRP de la suma de todos los alertados, que en esas escenas viene mayormente de la
fuente lejana.

## Cómo se midió

- **Regla de la vía, importada, no reescrita.** `_cumulo_del_mas_radiante` y `procesar_grilla` de `pipeline/mirova_v750_codigo.py`;
  cada script imprime que su texto es idéntico al de `origin/main` (97ef53aa) y que los archivos importados no
  difieren de `origin/main`. La vía mide desde el **centroide** del cúmulo (no desde el píxel pico) y la frontera es
  **inclusiva**: `summit` si `dcen <= inner_km`.
- **Misma máscara para las dos reglas.** Sólo cambia la distancia: `distance_class`, `primary_cluster.centroid_dist_km`
  y `final_hotspot_dist_km` (`comun.variante`). Cada variante pasa por `store.append_record` (como en producción) y por
  el predicado del tablero ejecutado con node (`banco_paridad.correr_node`).
- **Dos versiones de «cercano».** `cerc_cr`: el alertado más cercano medido desde el cráter, o sea la regla puesta en la
  vía sin cambiar nada más. `cerc_ref`: el más cercano medido desde el punto de referencia de MIROVA del censo (X0, Y0),
  que es lo que hace `evaluar.py` y lo que comparó V375-E.
- **Por sensor:**
  - MODIS: la vía (`procesar_grilla`, familia MODIS) corrida sobre las 5.321 grillas 51 x 51 que guardó el censo MOD-D.
  - VIIRS 375: (A) lectura de `equivalencia_v375e.json` de V375-E, sin recalcular; (B) la vía de 375 del worktree de
    V375-E sobre las mismas grillas, porque el cotejo necesita las distancias de todas las pasadas. La familia
    VIIRS375 y `caja_v375` todavía no están en `main`; la regla de posición de ese worktree es idéntica a la de `main`
    (impreso en `v375_salida.txt`).
  - VIIRS 750: el censo del oráculo de S159 no guardó grillas, sólo los alertados de la caja «def» (la que la vía usa
    en los 11 volcanes). La regla se aplica a esa máscara con la función importada y el record se arma con
    `comun.record_desde_pixeles`, que en MODIS (109 de 109) y VIIRS 375 (329 de 329) da el mismo record recortado
    que `procesar_grilla`.

## 1. Cuántas pasadas cambian de publicación

Clases: las de cada censo, etiquetadas con la copia de la referencia con que se selló cada uno. «Publica de más» =
con «cercano» publica y con la vía calla; «calla» = al revés.

### VIIRS 375 (muestra estratificada de V375-B/C, sin pesos; 2026-04-01 05:00 a 2026-10-21 06:48)

| clase | pasadas | cambian con `cerc_ref` (V375-E) | cambian con `cerc_cr` (recálculo) | dirección |
|---|---|---|---|---|
| alerta protegida (1 MW o más) | 80 | 4 | 4 | las 4 publica de más con «cercano» |
| alerta bajo 1 MW | 200 | 4 | 4 | las 4 publica de más con «cercano» |
| negativo limpio | 1.732 | 0 | 0 | |
| resto | 0 | 0 | 0 | |
| **total** | **2.012** | **8** | **8** | ninguna en la dirección «calla» |

El recálculo da las mismas 8 pasadas que V375-E (control cruzado `True`). SIN DATO: 66 pasadas sin resultado `ok`.
Salida: `v375_salida.txt`, `v375_cambios.json`.

### MODIS (censo MOD-D completo; 2026-03-01 01:35 a 2026-10-16 08:15)

| clase | pasadas | cambian con `cerc_cr` | cambian con `cerc_ref` | dirección |
|---|---|---|---|---|
| alerta protegida | 50 | 0 | 0 | |
| alerta bajo 1 MW | 42 | 0 | 0 | |
| negativo limpio | 5.018 | 0 | 0 | |
| resto (`far_ref` y `sin_info`) | 211 | 1 | 1 | publica de más con «cercano» |
| **total** | **5.321** | **1** | **1** | |

La única: Láscar 2026-03-30 07:25, 3 alertados, cúmulo radiante a 26,221 km del cráter y un alertado a 0,255 km. Con
«cercano» el tablero publicaría 11,685 MW como cumbre; MIROVA hoy tiene esa pasada como `FALSO_POSITIVO` de 11,31 MW
a 26,87 km. SIN DATO: 144 pasadas con el volcán fuera del gránulo. Máscara de la vía igual a la del port «fisica» del
censo en 5.321 de 5.321. Salida: `modis_salida.txt`, `modis_cambios.json`.

### VIIRS 750 (censo del oráculo de S159; 2026-04-01 05:00 a 2026-10-21 06:48)

| clase | pasadas | cambian con `cerc_cr` | cambian con `cerc_ref` | dirección |
|---|---|---|---|---|
| alerta protegida | 93 | 0 | 0 | |
| alerta bajo 1 MW | 177 | 1 | 2 | publica de más con «cercano» |
| negativo limpio | 5.370 | 0 | 0 | |
| resto | 0 | 0 | 0 | |
| **total** | **5.640** | **1** | **2** | |

- Láscar 2026-08-26 05:48: cúmulo radiante a 16,489 km del cráter, alertado a 0,478 km; MIROVA (tabla) ALERTA de
  0,37 MW a 1,5 km. Cambia con las dos versiones de «cercano».
- Planchón-Peteroa 2026-08-15 05:06: un solo píxel, a 4,019 km del cráter y a 2,25 km de la celda de referencia
  (inner 3). **No es efecto de la regla** (con un píxel las dos reglas eligen el mismo punto): es el punto desde donde
  se mide. Por eso cambia con `cerc_ref` y no con `cerc_cr`.

SIN DATO: 106 pasadas con el volcán fuera del gránulo. Salida: `v750_salida.txt`, `v750_cambios.json`.

**En los tres sensores ningún cambio va en la dirección «calla».** «Cercano» sólo agrega publicaciones, y sólo en
escenas con un alertado cerca del cráter y otro más radiante lejos.

## 2. Cotejo con la `Distancia_km` de MIROVA

Copia de la referencia usada (bajada hoy por `referencia.py`, procedencia en `referencia_salida.txt`):
consolidado `cb91eb506c37cff0b83164dd602d8a5340277637` (commit 2026-10-27 21:21:07 UTC, posterior al de las 12:41 de
D-39; sha256 `811c4c07…f7ef4`, 45.513 filas) y OCR `cfc57c4d8bc57c5ccd5219ff3a91749dae167b97` (2026-10-27 13:06:30 UTC,
1.160 filas). Pareo a 120 s (`clase_mirova.VENTANA_S`) sobre filas con VRP mayor que 0 y `Distancia_km`.

Para que la comparación sea justa las dos reglas se miden desde el mismo punto, la referencia del censo (MIROVA mide
desde su celda de referencia, D15). Se cuentan sólo las pasadas donde las dos distancias difieren en más de una celda.
Separado por configuración (`cotejo_por_configuracion_salida.txt`):

| sensor | configuración | tabla (decide): más radiante / cercano | OCR (informa): más radiante / cercano |
|---|---|---|---|
| VIIRS 375 | (a) las dos reglas del mismo lado del inner | 38 / 0 | 14 / 5 |
| VIIRS 375 | (b) una dentro y otra fuera (cambia la publicación) | 0 / 1 | 0 / 7 |
| VIIRS 750 | (a) | 3 / 0 | 1 / 0 |
| VIIRS 750 | (b) | 0 / 1 | sin filas |
| MODIS | (a) | sin filas | sin filas |
| MODIS | (b) | 1 / 0 (fila `FALSO_POSITIVO`) | sin filas |

Informa: la alertada más radiante sola contra la más cercana, desde la referencia, en la tabla: VIIRS 375 56 / 3,
VIIRS 750 9 / 1, MODIS 4 / 0 (salidas de cada sensor).

Lectura. Cuando todo está en el cráter (a), la distancia de MIROVA sigue al cúmulo radiante, no al píxel del borde:
38 de 38 en VIIRS 375 en la tabla. En la configuración que decide la publicación (b) hay **3 filas de la tabla en
total**: en dos (Láscar VIIRS 375 2026-06-28 con 1,19 km, Láscar VIIRS 750 2026-08-26 con 1,5 km) MIROVA da una
distancia de cráter, más cerca de «cercano»; en la tercera (Láscar MODIS 2026-03-30) MIROVA ubica la fuente lejana a
26,87 km, como la vía, y la marca `FALSO_POSITIVO`. Las 7 filas OCR de (b) apuntan al cráter, pero son OCR.

## Qué queda CONFIRMADO, SOSPECHA y SIN DATO

**CONFIRMADO** (salidas guardadas):
- Cambian de publicación: VIIRS 375 8 de 2.012 (4 protegidas, 4 bajo 1 MW), MODIS 1 de 5.321 (resto), VIIRS 750 1 de
  5.640 por la regla (2 con `cerc_ref`, uno de ellos por el punto de medida), todas en la dirección «publica de más
  con cercano».
- La reconstrucción de la regla coincide con `procesar_grilla` en 109 de 109 (MODIS) y 329 de 329 (VIIRS 375); el
  almacén no cambió la `distance_class` de ninguna variante; el predicado responde a `distance_class` (control
  `[True, False]`).
- Con las dos reglas dentro del inner, la distancia de la tabla de MIROVA sigue al cúmulo radiante (38 de 38 en VIIRS
  375, 3 de 3 en VIIRS 750).

**SOSPECHA**:
- La regla V-2 de S159 («MIROVA informa el píxel cercano aunque haya uno lejano más brillante») se sostiene en 2 de 3
  filas de la tabla de la configuración (b) y en 7 de 7 del OCR, y cae en la tercera (MODIS, donde MIROVA ubica la
  fuente lejana). Con 3 filas de la tabla no se puede decidir cuál es la regla de MIROVA. Una posibilidad que encaja
  con las tres, sin verificar: que MIROVA ubique el punto más radiante **dentro de su límite del volcán** y, si no
  hay ninguno, informe el lejano como `FALSO_POSITIVO`. En el caso MODIS eso exigiría que MIROVA no viera el píxel a
  1 km, lo que no se puede comprobar sin su imagen.
- Las 7 filas OCR de (b) pueden traer la distancia de otra pasada (memoria S150, `reference_ocr_imagen_de_otra_pasada`).

**SIN DATO**:
- VIIRS 750 sin grilla: no se corrió `procesar_grilla`; la máscara es la del oráculo de S159, que V750-A mostró igual
  a la de la vía (`experiments/_s162_v750a/equivalencia_v750a_salida.txt`), y el record es la reconstrucción validada
  en los otros dos sensores.
- VIIRS 375 es una muestra estratificada (pesos de V375-B/C no aplicados): los 8 no se extrapolan a la población.
- Las clases no se recalcularon con la copia de hoy de la referencia (las 2.648 filas nuevas de D-39 podrían mover
  alguna etiqueta). En las 11 pasadas que cambian, la fila que MIROVA tiene hoy está listada en cada salida y es
  coherente con la clase del censo.
- Los 144 (MODIS), 106 (VIIRS 750) y 66 (VIIRS 375) fuera del gránulo o sin resultado.

## Archivos

- `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s165_regla_posicion\comun.py`
- `...\referencia.py` y `referencia_salida.txt`
- `...\modis.py`, `modis_salida.txt`, `modis_cambios.json`
- `...\v750.py`, `v750_salida.txt`, `v750_cambios.json`
- `...\v375.py`, `v375_salida.txt`, `v375_cambios.json`
- `...\cotejo_por_configuracion.py` y `cotejo_por_configuracion_salida.txt`
- Detalle completo del cotejo: `D:\vrp-trabajo\temporales\s165_regla_posicion\{modis,v750,v375}.json`
