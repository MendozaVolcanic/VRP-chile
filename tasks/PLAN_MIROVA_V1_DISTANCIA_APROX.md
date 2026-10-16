# Distancia aproximada en Mirova-v1: plan de implementación

> **Para el agente que lo ejecute:** sub-skill obligatoria `executing-plans` (o `subagent-driven-development`), y
> `test-driven-development` en cada tarea. Pasos con casillas `- [ ]`. Escrito en la vuelta 63 del loop
> (2026-10-15 ~18:50 UTC). Nicolás aprobó implementarlo si el verificador salía bien; salió **SÍ, con seis cambios**.

**Objetivo:** que cada fila VIIRS 375 de `registro_vrp_ocr.csv` lleve una distancia aproximada, con su rango y su
método, leída en una `Dist.png` posterior, sin tocar `Distancia_km`.

**Por qué:** la `Dist.png` de MIROVA es una serie de tiempo de unos 30 días, y cada pasada sigue dibujada en las
imágenes que vienen después. El OCR de hoy sólo lee la estrella, que es la pasada de la cabecera, y por eso deja sin
distancia las filas cuya imagen ya era de otra pasada. Además, entre el 13 de junio y el 8 de octubre la distancia
que el OCR sí midió discrepa más de 2 km en cerca del 24 % de las pasadas. En las filas que sólo trae el OCR, casi
siempre es la distancia de otra pasada. En las filas que también están en la tabla, es un sesgo geométrico del OCR
(PCC y Tupungatito). La distancia decide si una alerta es del cráter o lejana, así que el error llega a la referencia
de VRP Chile.

**Fuentes (en el repo VRP Chile, rama `loop/activo`):** `experiments/_s151_distancia_ocr/INFORME.md` (estudio; §7
es la recomendación), `experiments/_s151_distancia_ocr/verificador/VERIFICADOR.md` (verificador limpio; §6 trae los
seis cambios), y los scripts que se portan, en `experiments/_s151_distancia_ocr/scripts/` (`dist_png.py`,
`control_dist.py`, `decision.py`, `aplicar.py`).

**Arquitectura:** un módulo nuevo en Mirova-v1, `dist_serie.py`, lee el panel y decide; un script,
`backfill_distancia_aprox.py`, agrega seis columnas al CSV. Las `Dist.png` **no se vuelven a archivar**: el poller de
`mirova-tif-archive` ya las guarda desde el 2026-05-09 (`data/png/<Volcan>/<fecha>_<hora>_<Sensor>_Dist.png`, con su
índice `index_png.csv` y el md5). Se leen por `raw.githubusercontent.com`, archivo por archivo. **Prohibido** hacer
pull o clone de ese repo (17 GB). Duplicar el archivo en Mirova-v1 sería un segundo canal que se puede desfasar. Si
Nicolás prefiere tener la copia en Mirova-v1, se agrega una tarea; está anotado como decisión en §Decisiones.

**Stack:** Python 3.11 (el de Mirova-v1), numpy, Pillow, scipy (`correlate2d`), pandas y pytest.

---

## Decisiones tomadas en el plan (se informan, no se preguntan)

- **Archivo de las imágenes:** reusar `mirova-tif-archive` (ver Arquitectura). Si Nicolás quiere una copia en
  Mirova-v1, se agrega una tarea 9.
- **Sólo VIIRS 375** (cambio 5). En VIIRS 750 y MODIS no hay muestra de control, así que esas filas quedan con
  `Distancia_aprox_metodo = "sin_control"` y el resto de las columnas vacías.
- **`Distancia_km` no se toca nunca.** Lo vigila un test que compara la columna byte a byte antes y después.

## Columnas nuevas (al final del CSV, aditivas, como las UTC de Mirova-v1#24)

| columna | contenido |
|---|---|
| `Distancia_aprox_km` | valor puntual sólo en el caso «único»; vacío en los demás |
| `Distancia_aprox_min_km`, `Distancia_aprox_max_km` | intervalo; en «único», los dos iguales al valor |
| `Distancia_aprox_metodo` | `unico`, `ambiguo`, `solapado`, `sin_marcador` (posible a más de 25 km), `pendiente` (no hay imagen de 1 a 25 días), `calado_debil`, `sin_control` |
| `Distancia_aprox_pareos` | coincidencias del calado del eje de tiempo en la imagen usada |
| `Distancia_aprox_imagen` | `png_path` de la imagen usada (trazabilidad) |

## Tarea 1: portar el lector del panel

**HECHA (vuelta 65, 2026-10-15):** commits locales `2a3e7121` y `cb72ac51` en `feat/distancia-aprox` (worktree
`Mirova-v1-distaprox`; el push por git se corta, subir por la API al abrir el PR). OpenCV en vez de scipy, desempate
de picos al centro de la meseta y re-control del estudio en `experiments/_s151_distancia_ocr/recontrol/`. Suite de
Mirova-v1: 88 en verde.

**Archivos:** crear `dist_serie.py` (copiar `dist_png.py` del estudio entero, sin cambios de lógica) y
`tests/test_dist_serie.py`. Fixture: bajar por raw dos `Dist.png` de VIIRS 375 del índice: la de Chillán que usa
`salidas/zoom_chillan_0518.png` y la de Villarrica del 2026-10-15. Guardarlas en `tests/fixtures/dist/`.

- [ ] Paso 1: escribir el test. Con la fixture de Chillán, `leer_panel(ruta)` devuelve el techo y el eje con una
  separación igual a la medida en el estudio, y al menos un marcador entre 0,4 y 1,5 km en la columna del 2026-10-15
  (valores del informe §5). Correrlo y verlo fallar porque el módulo no existe.
- [ ] Paso 2: copiar el código y correr el test hasta que pase.
- [ ] Paso 3: commit.

## Tarea 2: calado del eje de tiempo, sólo con la tabla (cambio 1)

**HECHA (vuelta 66):** commit local `45d8105c`. `calibrar`, `marcadores_t`, `pareos`, `solo_tabla`. Corrección al
texto de abajo: la fixture de Chillán NO cala en +0,48 a +0,53 (eso es la mediana por mes) sino en +0,76, uno de los 7
de 429 calados en el borde de la búsqueda; el test exige reproducir el calado del estudio. El test de las filas OCR se
comprobó fallando con el filtro quitado. Suite de Mirova-v1: 90 en verde. Para la tarea 5: decidir con el control si un
calado en el borde (>= +0,76) cuenta como débil.

**Archivos:** `dist_serie.py` (portar `calibrar_imagen`, `marcadores_t` y `pareos` de `control_dist.py`) y el test.

- [ ] Paso 1: test. `calibrar(imagen, conocidas)` recibe sólo filas de `latest.php` (la tabla) y devuelve
  `(fecha_primera_marca, desfase_dias, n_pareos)`. Con la fixture de Chillán, el desfase cae entre +0,48 y +0,53 días
  (informe §3). Un segundo test le pasa una fila OCR entre las conocidas y exige que sea ignorada, porque la función
  filtra por `Tipo_Registro` de la tabla.
- [ ] Paso 2: implementar y correr.
- [ ] Paso 3: commit.

## Tarea 3: eliminación sólo con la tabla (cambio 1)

**HECHA (vuelta 67):** commit local `7b14c37d`. `otras_de` y `eliminar` (devuelve dict). Cinco tests, incluido el de
OCR, comprobado fallando sin el filtro. Suite de Mirova-v1: 95 en verde.

**Archivos:** `dist_serie.py` (portar `eliminar` y `otras_de`) y el test.

- [ ] Paso 1: tests sintéticos con marcadores dados (sin imagen): (a) un marcador sobrante da `unico`; (b) dos
  sobrantes dan `ambiguo` con [mín, máx]; (c) ninguno da `solapado` si hay un marcador conocido en la columna y
  `sin_marcador` si la columna está vacía; (d) una distancia OCR en `otras` **no descuenta** ningún marcador.
- [ ] Paso 2: implementar y correr.
- [ ] Paso 3: commit.

## Tarea 4: elección de la imagen, de 1 a 25 días (cambio 2)

**Archivos:** `dist_serie.py` (portar `imagen_para`, que usa `index_png.csv`) y el test.

- [ ] Paso 1: tests con un índice sintético: con una imagen de 0,3 días y otra de 3 días gana la de 3; si sólo hay
  una de 0,3, el resultado es `pendiente`; si sólo hay una de 26, también. Las imágenes con md5 repetido cuentan una
  vez (A106: MIROVA a veces vuelve a servir una imagen vieja).
- [ ] Paso 2: implementar, eligiendo la **más reciente dentro de 1 a 25 días** (la recomendación del §7, que el
  verificador midió sin cambio de error).
- [ ] Paso 3: commit.

## Tarea 5: umbral de calado débil, medido contra el control (cambio 3)

**Archivos:** `scripts/umbral_pareos.py` en Mirova-v1. Lee `control_variantes.csv` (del verificador; copiarlo a
`tests/fixtures/dist/`) y calcula el error de decisión según `n_pareos`.

- [ ] Paso 1: script que imprime, por cada umbral de 4 a 20, el error de decisión y la fracción decidida.
- [ ] Paso 2: fijar en `dist_serie.PAREOS_MINIMOS` el menor umbral cuyo error no supere el error global del control
  (4,5 %). Dejar la salida del script en el docstring de la constante. El valor sale del dato, no se elige (A115).
- [ ] Paso 3: test. Con menos pareos que el umbral, el método es `calado_debil` y no se escribe ningún valor.
- [ ] Paso 4: commit.

## Tarea 6: decisión cerca o lejos

**Archivos:** `dist_serie.py` (portar `decision.py`) y el test.

- [ ] Paso 1: tests. Si todo el intervalo está bajo el límite menos 0,6 km, es `cerca`; si está sobre el límite
  más 0,6 km, es `lejos`; si no, `indecidible`. `sin_marcador` da `posible >25 km`, nunca `cerca`. Los límites por
  volcán son los del informe §4 (Lastarria y Planchón Peteroa 3 km, Copahue 4, Tupungatito 7, PCC 20, el resto 5),
  y se leen de `volcanes.py`, no se copian.
- [ ] Paso 2: implementar y correr.
- [ ] Paso 3: commit. La decisión **no se escribe** en el CSV; queda como función para quien lo consuma.

## Tarea 7: script de backfill y columnas (cambios 5 y 6)

**Archivos:** `backfill_distancia_aprox.py` y `tests/test_backfill_distancia_aprox.py`.

- [ ] Paso 1: tests. (a) `Distancia_km` queda byte a byte igual en todas las filas; (b) las seis columnas se
  agregan al final y las filas VIIRS 750 y MODIS llevan `sin_control`; (c) también se llenan las filas que ya tienen
  `Distancia_km` > 0 (las 451 medidas); (d) correrlo dos veces da el mismo archivo (idempotente); (e) el CSV se
  escribe con LF, como en Mirova-v1#24.
- [ ] Paso 2: implementar con caché local de imágenes en `~/.cache/mirova_dist/` (no en el repo).
- [ ] Paso 3: correrlo sobre una copia del CSV real y comparar contra las salidas del estudio: las 15 filas sin
  geometría y el reparto 163 / 48 / 34 / 35 del informe §7.3. Las diferencias se explican una por una, porque el
  estudio usaba distancias OCR al eliminar y este código no.
- [ ] Paso 4: commit.

## Tarea 8: cron, documentación y PR

- [ ] Paso 1: un paso nuevo en `.github/workflows/ocr_workflow.yml`, después del OCR, que corre el backfill sólo
  sobre filas de los últimos 26 días y con un `timeout-minutes` medido. No necesita credenciales: el repo de imágenes
  es público.
- [ ] Paso 2: README de Mirova-v1. Qué es cada columna; el error **por población** (cambio 4): en ALERTA, 4,9 % de
  cerca leído como lejos; lejos leído como cerca no tiene muestra bajo 25 km; en el control ninguna ALERTA era lejana.
  Además, que `Distancia_aprox_*` vale desde el 2026-04-14 (el archivo empieza el 05-09 y el panel cubre 30 días), y
  que la distancia OCR del 06-13 al 10-08 discrepa en cerca del 24 %.
- [ ] Paso 3: suite completa de Mirova-v1 y PR con CI. **El merge espera a Nicolás**, porque Mirova-v1 es
  producción (como D-2).
- [ ] Paso 4: hito nuevo en `scripts/calidad_referencia_mirova.py` de VRP Chile, con la fecha del merge y la fuente.

## Después del merge (para VRP Chile, decisión de Nicolás)

Si la referencia unificada de VRP Chile debe usar `Distancia_aprox_*` en vez de `Distancia_km` para clasificar
cráter o lejana en las filas OCR del 06-13 al 10-08, se mide antes cuántas alertas protegidas cambian de lado (lectura
A, 439 pasadas). No se cambia sin esa medición.
