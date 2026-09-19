# S144: conteo versionado de pasadas VIIRS 375 con TIF UTM de MIROVA

## Por qué existe

La decisión 1 del traspaso S144 (frente `keep_peak` con dirección) se apoya en un conteo exploratorio
hecho después del cierre de S143 cuyo script no quedó en el repo: 290 pasadas nocturnas, 122 con TIF
UTM, 58 con alerta de MIROVA (23 con TIF), 81 con el patrón de `keep_peak` separado (34 con TIF) y sólo
**2** con patrón, alerta y TIF a la vez. Con 2 casos la prueba directa no decide nada, y la
recomendación fue medir sobre las pasadas con patrón y TIF, con y sin alerta. Antes de diseñar esa
medida, los números tienen que salir de un script versionado, con las entradas fijadas por sha.

**El fenómeno.** En un cono nevado, el píxel más tibio del disco del Test 1 suele ser el borde de
cota baja, no el cráter (A69). `keep_peak` conserva ese píxel y el ancla lo publica en el cráter a
0,0 km (D19). En el record queda así: `final_hotspot_source = test1_roi` en el vent y un cúmulo
primario de un solo píxel en otro lugar. Desde el 2026-09-14 MIROVA publica sus GeoTIFF VIIRS 375 en
su grilla UTM nativa de 375 m (A106). Así se puede ver **dónde** estaba el calor que MIROVA vio y
compararlo con ese píxel, en vez de comparar radios sin acimut (A93, A107).

## Definiciones (escritas antes de correr el script)

Todas las entradas se fijan por sha y el sha queda en la salida:

- **Records**: `git show <sha>:data/mirova_equivalent/<Volcan>.json` de los 11 Tier A. Por defecto
  el sha de `origin/main` al correr.
- **Índice de TIF**: `index.csv` de `MendozaVolcanic/mirova-tif-archive`, fijado al último commit
  que lo tocó. Se lee por la API. **Nunca se hace pull ni clone de ese repo** (17 GB).
- **Referencia MIROVA**: CONS y OCR de `Mirova-v1` fijados por sha
  (`referencia_mirova_unificada.bajar_remoto`).

Unidades y conjuntos:

1. **Pasada nocturna VIIRS 375**: record con `banco_paridad.bucket(sensor) == "VIIRS375"`, que no
   descarta `es_pasada_diurna_descartada` (la definición del auto-audit y del banco) y con hora
   `>= 2026-09-14 06:36 UTC`. Esa hora es el primer TIF VIIRS 375 del índice con `acquisition_utc`
   (se comprueba en la corrida y se informa).
2. **Con TIF UTM**: en el índice hay una fila del mismo volcán con `sensor == VIIRS375`,
   `size_bytes > 0` y `acquisition_utc` no vacío, a **±15 min** de la hora del record. Si hay
   varias, cuenta la más cercana. Se usa la hora de adquisición, nunca la del nombre del archivo
   (A106).
3. **Con alerta de MIROVA**: `evaluar.fila_mirova` de S143 no nulo sobre las filas de
   `banco_paridad.parear` a ±120 s. Es decir, una ALERTA con VRP > 0, CONS antes que OCR.
   También se informa la etiqueta de `banco_paridad.etiquetar` (`pos` / `neg_limpio` / `far_ref` /
   `sin_info`), porque la medida siguiente necesita negativos limpios (A98).
4. **Patrón `keep_peak` separado**: `final_hotspot_source == "test1_roi"`,
   `primary_cluster.n_pixels == 1` y el centroide del cúmulo a **más de 0,5 km** de
   `final_hotspot` (haversine).
5. **Publicada**: el predicado del dashboard ejecutado con node (`banco_paridad.correr_node`, A97).
   Sólo informa. No entra en ningún otro conjunto.

Salida: las tablas de cruce de los conjuntos 2, 3 y 4 (con y sin publicación), por volcán, y la
lista de las pasadas con patrón y TIF. Esa lista es la muestra de la medida siguiente.

## Las dos preguntas del instrumento

- **P1: si el emparejamiento de TIF estuviera roto, ¿se vería?** Hay dos controles:
  - **Placebo**: correr el mismo emparejamiento con las horas del record corridas +6 h debe dar
    casi 0 TIF. Si da muchos, la tolerancia está emparejando cualquier cosa.
  - **Lectura directa**: se bajan los TIF emparejados (pesan KB cada uno, uno por uno por la API) y
    se comprueba con rasterio que su CRS sea UTM y que el píxel mida unos 375 m. Un TIF que no
    cumpla no cuenta como "TIF UTM", y se informa cuántos hubo.
- **P2: ¿el instrumento está vivo?** `banco_paridad.control_identidad_predicado()` tiene que pasar
  antes de usar el predicado. Además se informa la distribución de |Δt| de los emparejamientos:
  si todos dieran 0 s o todos cayeran justo en 15 min, algo está mal.

## Contra qué se compara

Se comparan los seis números exploratorios (290 / 122 / 58 / 23 / 81 / 34 / 2) con los de la
corrida. La data creció después (el NRT siguió corriendo), así que se espera que suban. **Si alguno
baja**, la definición exploratoria era distinta, y se informa cuál.

## Enmienda tras la primera corrida (2026-09-19, posterior a ver los datos)

Esta sección se escribió **después** de la primera corrida, y lo que agrega es post-hoc. Los números
están en `RESULTADO.md`, que genera el script.

1. **La premisa de la definición 1 era falsa.** El índice tiene `acquisition_utc` desde mayo, no desde
   el 14-sep, así que "la primera adquisición" no marca el inicio de la grilla UTM. El control P1 de
   lectura directa lo detectó: casi todos los TIF leídos son EPSG:4326, y los UTM de 375 m existen
   **sólo en ocho adquisiciones, entre el 2026-09-14 06:36 y el 2026-09-15 06:24**. Desde la tarde del
   15-sep MIROVA volvió a publicar en grilla geográfica. S142 vio el comienzo de la grilla UTM
   (`experiments/_s142_ndc/RESULTADOS.md` §2.1), pero no alcanzó a ver que terminaba. La regla A106
   queda corregida en `CLAUDE.md`.
2. **El conteo exploratorio contó como "TIF UTM" todo TIF posterior al 14-sep, sin leer su CRS.** Con
   "TIF de cualquier grilla" se reproducen exactamente sus cuatro conteos con TIF. Sus otros tres
   números (pasadas, alertas, patrón) salen idénticos si las pasadas se cuentan desde el
   2026-09-14 00:00 en vez de las 06:36. Esto se comprobó aparte y no está en el script. Todos los
   números exploratorios quedan explicados: no había error, eran otra ventana y otra definición.
3. **Se agregan tres niveles de TIF y dos ventanas.** Los niveles son: `tif_cualquiera` (definición 2
   sin exigir UTM), `tif_propia` (además, la imagen no es repetición de otra adquisición: MIROVA a veces
   vuelve a servir una imagen vieja bajo una hora nueva, y entonces la imagen es "propia" sólo de la
   primera adquisición en que aparece su md5) y `tif_utm_375` (la definición original). Las ventanas
   son `historia` (desde la primera adquisición del índice) y `desde_2026-09-14_0636`. Todas las
   entradas quedan fijadas por sha con `--sha-records`, `--sha-indice`, `--sha-cons` y `--sha-ocr`.

**Consecuencia para la decisión 1 (hipótesis, sin verificar todavía).** El traspaso decía que las 5
noches perdidas de junio y julio no tenían TIF. Sí tienen: en grilla geográfica de ~375 m, no UTM. Para
decidir si un píxel a 2 o 3 km del cráter es el objeto que MIROVA vio, una grilla geográfica alcanza,
**si su georreferencia es correcta**. Eso no está verificado. Antes de usarlo hace falta un control de
georreferencia: en pasadas con alerta fuerte y foco conocido (lago de lava de Villarrica), el máximo del
TIF tiene que caer en el cráter.

**Dos límites que la medida siguiente debe resolver en su propio pre-registro.**

- La definición 4 (patrón) sólo ve records `test1_roi`. Según el verificador de S143, en las 5 noches
  la "coincidencia" venía de records `ctx_cluster` con un cúmulo de un píxel a 2,2-2,8 km. Ese grupo
  (`ctx_cluster`, un píxel, separado del `final_hotspot`) existe y no es chico, pero no está en este
  conteo.
- `tif_propia` no garantiza que la imagen sea de esa pasada: sólo descarta repeticiones. S142 encontró
  TIF rotulados de madrugada con niveles de escena diurna, escritos 17 h después. La medida siguiente
  necesita además un control de contenido nocturno.

## Uso

```
python experiments/_s144_conteo_tif/conteo_tif.py --sha-records beba9b3d16a45ff9b94941eb2df2670cad0897b0 \
    --sha-indice da4fe36e8920ab7d36c9bf466998cf015348d348 \
    --sha-cons 3b18c772f65ab08c5c12ea97afe3d0e5cf6a9842 --sha-ocr 7e3438046ca1e65eb80f20ae8b11c67e0ce5a453
# escribe resultado.json y RESULTADO.md; los TIF quedan en _dl_tif/ (ignorado por git, ~320 MB)
python -m pytest tests/test_conteo_tif_s144.py -q
```
