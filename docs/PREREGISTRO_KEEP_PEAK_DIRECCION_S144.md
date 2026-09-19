# Pre-registro: ¿el píxel de `keep_peak` es el objeto que MIROVA vio? (medida con dirección, S144)

> **Estado: v1 del 2026-09-19, escrita ANTES de medir.** Pendiente: revisión de un verificador con
> contexto limpio (se agrega como `PREREGISTRO_KEEP_PEAK_DIRECCION_S144_VERIFICADOR.md`) y, si corrige
> algo, una v2. Recién después se escribe el script y se corre.
>
> Origen: decisión 1 del traspaso `tasks/BLOQUE_ARRANQUE_S144.md` (Nicolás eligió medir con dirección el
> 2026-09-19). Conteo de la muestra: `experiments/_s144_conteo_tif/` (`RESULTADO.md`, generado por script).
> A/B que motiva la medida: `experiments/_s143_evaluador/RESULTADO_AB_S143.md` y `VERIFICADOR_VEREDICTO.md`.
> Instrumento heredado: `experiments/_s142_ndc/RESULTADOS.md` §0 (semilla de exceso local en el TIF).

## 1. El fenómeno y la pregunta

En un cono nevado de noche, la radiancia MIR sigue la altitud: dentro del disco de 3 km del Test 1 el píxel
más tibio suele ser el borde de cota baja, no el cráter (A69). `keep_peak` conserva ese píxel aunque no sea
contextual, y el record lo publica como un cúmulo de un solo píxel a 2 o 3 km del cráter (D19). Apagar
`keep_peak` es lo único que baja la sobre-publicación en el A/B de S143. Pero la regla de cero pérdidas le
cobró 5 noches donde MIROVA alertó y el control "coincidía" porque ese píxel caía dentro de la cota de
distancia. Esa cota compara radios sin acimut (A93, A107): un píxel a 2,4 km al sur y un objeto a 2,4 km al
norte "coinciden".

**Pregunta**: cuando publicamos ese píxel lejano, ¿MIROVA vio algo en ese mismo lugar, o su objeto estaba en
otro lado (el cráter, o un foco distinto)? El TIF que MIROVA publica por pasada es su campo de radiancia MIR
(W/m² sr µm, leyenda de su página de mapa, S142 §0). En ese TIF se puede ubicar dónde estaba el calor en
dos dimensiones, que es justo lo que la distancia escalar no da.

**Qué NO decide esta medida**: si hay que apagar `keep_peak`. Decide si las 5 "pérdidas" del A/B eran
reales o eran coincidencias de radio. Con eso, Nicolás decide si reabre la regla de cota con dirección, en
un pre-registro nuevo y antes de ver un A/B.

## 2. Por qué sirven los TIF geográficos (y la condición)

La grilla UTM nativa de 375 m existió sólo entre el 2026-09-14 06:36 y el 2026-09-15 06:24 (S144, A106
corregida). El resto del archivo (desde mayo) es EPSG:4326 a ~375 m. Una grilla geográfica no sirve para
contar celdas (S141, S142), pero para ubicar un objeto a kilómetros del cráter basta, **si la georreferencia
es correcta**. Por eso el control G de §5 va primero y es una compuerta: si falla, la medida se detiene y el
resultado es INCONCLUSO.

## 3. Entradas (todas fijadas por sha, que queda en la salida)

- Índice y TIF de `MendozaVolcanic/mirova-tif-archive` leídos por la API, sin pull ni clone (17 GB).
- CONS y OCR de `Mirova-v1` por sha (como `experiments/_s144_conteo_tif/conteo_tif.py`).
- Parte A (las 5 noches): records del brazo **control** del A/B S143, bajados con
  `experiments/_s143_evaluador/bajar_tramos.py`. Son los records que el evaluador usó para declarar las
  pérdidas. No se usan los de producción, porque los de junio y julio se generaron con otro código.
- Partes B y C: records de producción `data/mirova_equivalent/<Volcan>.json` en un sha de `origin/main`.
- Cráter: `vent_lat`/`vent_lon` de `volcanoes.yaml`. Radio de búsqueda: centro `mirova_center` del mismo
  archivo.

## 4. Unidades y definiciones

**TIF usable** (se exigen todas; cada exclusión se cuenta por motivo y por volcán):
1. `size_bytes > 0` y `acquisition_utc` no vacío, a ±120 s de la pasada de MIROVA (Parte A y B) o de la
   nuestra (Parte C).
2. Imagen propia: el md5 no aparece bajo una adquisición anterior del mismo volcán (S144).
3. Latencia: la primera captura de ese md5 ocurre como máximo 8 h después de la adquisición (S142 §2.6: los
   archivos escritos ~17 h después eran escenas diurnas).
4. Contenido nocturno: la mediana del raster es menor que 0,2 W/m² sr µm (criterio de S142 §0). Si un
   volcán pierde más de la mitad de sus TIF por este criterio, se informa y ese volcán queda como SIN DATO,
   no se relaja el corte.
5. CRS legible con rasterio (EPSG:4326 o UTM). La celda de un punto se obtiene con `ds.index()` después de
   transformar lat/lon al CRS del archivo.

**Exceso local** de una celda: ΔL0 = L menos la media de sus 8 vecinas (S142 §0). **z** = ΔL0 dividido por
el σ robusto (1,4826 × MAD) de ΔL0 en todo el raster.

**Objeto de MIROVA en una pasada con alerta (semilla)**: la celda de mayor ΔL0 dentro de un disco de radio
R alrededor de `mirova_center`, con R = máx(4 km, `Distancia_km` de la alerta + 1 km). Los 4 km cubren el
disco de 3 km del Test 1 más una celda de margen, así que la búsqueda incluye al cráter y a nuestro píxel
lejano por igual, sin favorecer a ninguno. Variante secundaria (se informa, no decide): la celda de mayor
ΔL0 dentro del anillo |r − `Distancia_km`| ≤ 0,6 km, que usa el radio de MIROVA y deja que el TIF ponga el
acimut.

**Candidatos nuestros** en la misma noche (Parte A) o la misma pasada (Parte B):
- **P**: el centroide del cúmulo primario de un solo píxel (el píxel de `keep_peak`).
- **F**: `final_hotspot` del mismo record. En records `test1_roi` es el cráter.

**Clasificación de la semilla** (tolerancia de mismo objeto T = 0,75 km: unas dos celdas de ~0,4 km; cubre
el desajuste entre nuestra grilla L1B y el remuestreo de MIROVA):
- `P` si d(semilla, P) ≤ T y d(semilla, F) > T;
- `F` si d(semilla, F) ≤ T y d(semilla, P) > T;
- `ambos` si las dos distancias son ≤ T (candidatos demasiado juntos: no clasificable);
- `otro` si ninguna es ≤ T.

Clasificables = `P` + `F` + `otro`.

## 5. Controles (se corren y se leen antes que las Partes A a C)

**G, georreferencia (compuerta).** Pasadas con alerta de MIROVA con VRP ≥ 0,3 MW en Láscar y Villarrica
(cráteres activos y focales, donde el objeto de MIROVA está en el cráter) y TIF usable. Pasa si hay al menos
8 pasadas, la semilla cae a ≤ 0,75 km del cráter en al menos el 80 %, y la mediana de esa distancia es
≤ 0,5 km. Se informa por separado para los TIF UTM y los geográficos, y el desplazamiento medio en
norte-sur y este-oeste (un sesgo sistemático de una celda se vería ahí). **Si G falla, la medida termina
INCONCLUSA** y se informa sólo G.

**H, alineación con nuestra grilla.** Pasadas con alerta de MIROVA donde nuestro record de la misma pasada
es `ctx_cluster` con 2 o más píxeles dentro del `inner_radius_km`: la semilla debe caer a ≤ 0,75 km de
nuestro centroide en la mayoría. Si no pasa, se informa. No es compuerta, pero rebaja cualquier veredicto a
SOSPECHA.

**Placebo de instrumento.** Se repite la clasificación de las Partes A y B con el TIF de otra pasada
nocturna del mismo volcán, elegida al azar (semilla aleatoria fija 144) entre las de más de 3 días de
distancia. Si el placebo da `P` con una frecuencia parecida a la real, el instrumento no discrimina y el
veredicto es INCONCLUSO.

**Predicado.** "Publicado" es el predicado del dashboard ejecutado con node (A97), con control de identidad
antes de usarlo.

## 6. Partes de la medida

**Parte A: las 5 noches de S143** (Isluga 2026-06-16, Láscar 2026-06-13, Lastarria 2026-06-07, 2026-06-14
y 2026-07-25). Unidad: la noche, como en el criterio 1 del A/B. Para cada noche:
- el objeto de MIROVA es la semilla del TIF de **su pasada con alerta** (si hay varias, cada una);
- nuestros candidatos son los records publicados del brazo control esa noche con el patrón de un píxel
  separado (P a más de 0,5 km de F), sean `test1_roi` o `ctx_cluster`;
- se clasifica cada par (semilla, record) y se informa todo.

Isluga 2026-06-16 no tiene TIF en sus pasadas con alerta (05:24 y 06:00): queda SIN DATO, no se reemplaza por
otra pasada. **Veredicto de la Parte A**: con al menos 3 noches clasificables, "azar" si en ninguna la
semilla es `P`; "es el objeto" si la mayoría de las noches clasificables dan `P`; si no, INCONCLUSO.

**Parte B: generalización, misma pasada.** Pasadas con alerta de MIROVA y TIF usable donde nuestro record de
esa misma pasada (±120 s, mismo satélite) tiene el patrón de un píxel separado (P a más de 0,5 km de F,
cualquier `final_hotspot_source`). Se informa por volcán. **Lastarria va aparte**: su foco real está corrido
al norte (campo fumarólico Lazufre), así que ahí un P lejano puede ser real. **Veredicto de la Parte B**, con
al menos 10 pasadas clasificables fuera de Lastarria: si la fracción `P` es ≤ 1/3, el píxel lejano casi nunca
es el objeto de MIROVA; si es ≥ 2/3, casi siempre lo es; en medio, INCONCLUSO. Lastarria recibe el mismo
veredicto por separado, con el mismo umbral de n.

**Parte C: especificidad en negativos limpios.** Pasadas nuestras publicadas con el patrón, etiqueta
`neg_limpio` de `banco_paridad.etiquetar` (MIROVA miró y dijo RUTINA con VRP 0) y TIF usable de esa misma
pasada. Se mide z en la celda de P, en la de F y en la de P' (el reflejo de P a través del cráter: misma
distancia, dirección opuesta). Se informa la fracción con z ≥ 3 en cada una. Lectura: si z(P) ≈ z(P'),
MIROVA no tiene en ese lugar un exceso mayor que en cualquier punto a la misma distancia del cráter. Parte C
sólo informa, no tiene veredicto.

## 7. Qué se hace con el resultado

| Parte A | Parte B (fuera de Lastarria) | Lectura | Siguiente paso propuesto |
|---|---|---|---|
| azar | ≤ 1/3 | la coincidencia de S143 fue de radio; el píxel lejano no es el objeto de MIROVA | pre-registrar una cota con dirección y re-evaluar el A/B S143 con ella, sin re-correrlo |
| es el objeto | ≥ 2/3 | `keep_peak` ve lo que MIROVA ve | no apagar `keep_peak`; buscar por qué el píxel es el objeto (¿MIROVA también ve el borde tibio?) |
| cualquier otra combinación | | INCONCLUSO | informar y no mover nada |

En ningún caso esta medida toca `pipeline/` ni perfiles.

## 8. Límites conocidos

- La semilla es el mayor exceso local, no el cúmulo que MIROVA sumó (S142 no logró reconstruirlo). Un objeto
  extenso puede tener la semilla en un borde. La tolerancia T y la Parte C lo acotan, pero no lo eliminan.
- La Parte A tiene como máximo 4 noches con TIF. Por sí sola es descriptiva; la B es la que tiene n.
- Los TIF geográficos son un remuestreo de MIROVA con un método no documentado. G lo controla en cráteres
  focales, no en bordes de disco.
- La hora de adquisición del índice puede no ser la de la imagen (A106). Los criterios 2 a 4 del TIF usable
  apuntan a eso, pero no lo prueban imagen por imagen.
