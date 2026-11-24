# Diseño: una miniatura por pasada para las «Últimas 10 imágenes» del tablero

Sesión S184 (lado), 2026-11-15. Estado: **IMPLEMENTADO en la rama `claude/s184-diseno-miniaturas-eb819f`** tras el
«avanza con todo» de Nicolás (2026-11-15), con las cuatro recomendaciones de §9 (NTI, escala fija, 256 tonos, los 11
Tier A) y el interruptor por línea de comandos (no toca `mirova_equivalent.yaml`). Tag defensivo `pre-miniaturas`.
Lo que cambió respecto del diseño original está en §10.

## 1. Por qué

Cuando el tablero dice «sin anomalía» en una pasada, el operador no sabe si el volcán estaba tranquilo, si una nube
tapaba el cráter o si la escena quedó a medias en el borde de la franja. Las tres cosas dan VRP 0 y sólo una significa
«no pasa nada». MIROVA lo resuelve con el panel «Latest images»: las 10 últimas pasadas en miniatura, con y sin
anomalía. Con una mirada se ve la nube, la escena cortada o el punto caliente. Nicolás lo pidió explícitamente.

Nosotros no podemos armarlo hoy porque no guardamos ninguna imagen por pasada: los L1B y HDF nunca se commitean y
los records sólo traen números. La grilla que haría falta, sin embargo, ya existe en memoria en cada pasada que procesa
la vía «código MIROVA» (§3): sólo hay que guardarla chica antes de que el proceso termine.

## 2. Qué muestra MIROVA (leído del PNG, 2026-11-15)

Archivo mirado con Claude en Chrome:
`https://www.mirovaweb.it/OUTPUTweb/MIROVA/VIIRS375/VOLCANOES/ChillanNevadosde/ChillanNevadosde_VIIRS375_Latest10NTI.png`
(850 × 600 px, «Last Update 15-Nov-2026 06:18:02»).

- **10 miniaturas en dos filas de 5**, de la más nueva a la más vieja. Cada una mide unos 165 × 150 px dentro de
  su borde (medido en el canvas). Encima, la fecha y hora UTC: **roja** si hubo anomalía, **negra** si no. Debajo,
  «VRP = x MW» o «VRP = NaN MW» y «ZEN = 51° · AZI = -85°N».
- **Borde del color de la clase** de esa pasada (verde, amarillo; gris sin anomalía).
- **Escala de grises azulada**: el color dominante del fondo de la hoja es `113,114,180` y la imagen tiene 1.275
  tonos distintos en una sola miniatura, o sea está suavizada al ampliarla. Es compatible con el mapa de color
  `bone` de MATLAB (SOSPECHA: no está en el código publicado del OSF).
- **El producto es el NTI**, como dice el nombre del archivo. Lo confirma la forma: en las escenas de Chillán la
  cordillera alta y fría sale **oscura** y el punto caliente sale como un punto **blanco**. Al reproducir el NTI
  con grillas reales (§5) se ve el mismo patrón.
- **Píxeles alertados**: no hay una marca de color sistemática sobre los alertados. En la miniatura de las 06:18
  hay 107 píxeles blancos puros (saturados por el estiramiento) y sólo 3 verdes dentro del borde. El foco se
  reconoce porque el NTI lo pone blanco, no porque lo pinten.
- **Sin dato = blanco**. La miniatura del 14-Nov 06:42 tiene la mitad superior en blanco. Ese mismo gránulo en
  nuestro `NevadosDeChillan.json` es `motivo_vacio: "escena_invalida"` con `celdas_sin_dato: 9309` de 17.956
  (134 × 134): es el borde de la franja. El blanco de «sin dato» y el blanco de «muy caliente» son el mismo color
  en MIROVA, una ambigüedad que no conviene copiar (§7).
- **Incluye pasadas diurnas**: 4 de las 10 (14-Nov 18:18 y 19:00, 13-Nov 18:36 y 19:18 UTC) son de tarde en Chile.
  Nosotros no las bajamos (§6.5).
- Dos avisos fijos: «Thermal anomalies may be due to fires or non-volcanic sources» y «may be masked or attenuated
  by clouds».

## 3. Qué banda mostrar: el NTI de la grilla de la vía

**Recomendación: el NTI sobre la grilla de MIROVA del volcán, con escala fija por sensor de noche, sin dato en un
color propio y los alertados marcados encima por el tablero (no quemados en la imagen).**

Por qué el NTI y no la temperatura del infrarrojo térmico (I05, M15, banda 31):

1. **De noche el NTI ya es un mapa de temperatura.** En las 298 escenas nocturnas reales de V750 guardadas en
   `experiments/_s163_o2/entradas_o2.mat` (Chaitén, Chillán, Láscar, Llaima, PCC, Tupungatito, Villarrica, Etna y
   sintéticas), la correlación por escena entre el NTI y la temperatura de brillo de M15 tiene mediana **0,97**
   (p10 0,51). Una nube es fría, así que sale oscura en el NTI igual que en el térmico. Ver las nubes no exige una
   segunda banda.
2. **El NTI además hace saltar el foco.** El punto caliente sube mucho más en el MIR que en el TIR, así que en el NTI
   es un punto blanco sobre un fondo gris parejo; en el TIR es un píxel apenas más tibio.
3. **Es lo que muestra MIROVA**, así que la miniatura nuestra se compara con la suya lado a lado sin traducir.
4. **Es lo que la vía ya calcula**: `detectar_mirova` (`pipeline/mirova_v750_codigo.py`, l. 159 del .m) hace
   `nti = (m13 - m15) / (m13 + m15)` sobre la misma grilla. No hay producto nuevo que validar.

Cuidado con un detalle: el `d["nti"]` que devuelve el detector es `nti_roi`, con las celdas fuera de la caja (`excl`)
puestas en NaN, y con M15 frío (BT ≤ 200 K) también en NaN. La miniatura tiene que mostrar **la grilla entera**, así
que se recalcula el NTI desde `m13g` y `m15g` sin la caja (es una línea).

**Escala.** De noche el fondo del NTI es angosto: en esas 298 escenas el percentil 2 por escena va de -0,965 a
-0,917 (mediana -0,942) y el percentil 98 tiene mediana -0,914 (una escena llega a 0,996).
Los valores del ejemplo de §4.4 (VRP, cenit, azimut, alertadas) son los del record real de Chillán del 15-Nov 06:18.
Propongo **escala fija por sensor y de
noche** (del orden de -0,97 a -0,90 para V750; el rango exacto de cada sensor se mide al implementar, no se adivina),
porque así una noche nublada se ve más oscura que una despejada. Con estiramiento por escena (lo que parece hacer
MIROVA) la textura de la nube se ve igual, pero dos noches no se pueden comparar en brillo. El rango usado va en el
índice, así que el tablero puede traducir el gris a NTI si alguna vez se quiere mostrar el valor.

**Alertados.** El tablero los dibuja encima desde el índice (§4.3), con la lista `[fila, col]` que la vía ya produce
en `anomaly_pixels` (`procesar_grilla`, campos `fila` y `col`). Así la imagen es dato y no gráfico, y el color de la
marca se puede cambiar sin regenerar nada.

## 4. Dónde está la grilla y qué habría que agregar

### 4.1 La grilla ya existe en cada pasada de la vía

`calcular_vrp_granulo` (`pipeline/mirova_v750_codigo.py`) es la única puerta de la vía para los tres sensores
(`familia` = `"VIIRS750"`, `"MODIS"`, `"VIIRS375"`). Ahí, después de leer el gránulo:

```
m13g, m15g = remuestrear_grilla(lat, lon, rad[b_mir], rad[b_tir], g)    # grilla de MIROVA, fila 0 = norte
...
rec = procesar_grilla(m13g, m15g, g, box, dayflag, sg, pos, inner_km, sensor, familia=familia)
rec["diag_codigo_mirova"].update({"dayflag": ..., "sunglint": ..., "celdas_sin_dato": int(np.isnan(m13g).sum())})
```

Tamaños de grilla (`n_celdas`, ±25 km alrededor de X0, Y0): **VIIRS 375 = 134 × 134**, **VIIRS 750 = 67 × 67**,
**MODIS = 51 × 51**. La grilla está en UTM con el norte arriba y el oeste a la izquierda, lista para dibujar.

Los tres procesadores llaman a esa función y devuelven el record tal cual, sólo agregándole `granule`,
`product_version` y `datetime_utc`:

- `pipeline/process_viirs.py` (VIIRS 375), bloque `if ENABLE_V375_CODIGO_MIROVA:`
- `pipeline/process_viirs_mod.py` (VIIRS 750), bloque `if ENABLE_V750_CODIGO_MIROVA:`
- `pipeline/process_modis.py` (MODIS), bloque `if ENABLE_MODIS_CODIGO_MIROVA:`

Como devuelven el diccionario sin tocarlo, **una clave agregada dentro de `calcular_vrp_granulo` llega hasta
`scripts/run_pipeline.py` sin cambiar ningún `process_*.py`**. Ese es el punto del diseño.

### 4.2 Pasadas sin anomalía y escenas inválidas también tienen grilla

`m13g` y `m15g` existen antes de que el detector decida nada. Los tres cortes tempranos de `detectar_mirova`
(`motivo_vacio = "sunglint"`, `"escena_invalida"`, o ninguna alerta) devuelven igual el record, y la grilla sigue en
`calcular_vrp_granulo`. Por eso la miniatura se arma **siempre que hay record de la vía**, haya o no anomalía, que es
justo lo que MIROVA muestra. Las celdas NaN de `m13g` (fuera de la franja) son el «sin dato».

No hay miniatura cuando no hay record: `calcular_vrp_granulo` devuelve `None` si el recorte de 45 km tiene menos de
100 píxeles o si el píxel más cercano al centro queda a más de 5 km (MODIS y VIIRS 375). En ese caso no hay pasada
que mostrar, igual que hoy.

### 4.3 Qué agregar y en qué punto

1. **`pipeline/mirova_v750_codigo.py`**: una función pura nueva, por ejemplo
   `miniatura_nti(m13g, m15g, mascara_filas_cols, familia, dayflag) -> dict`, que devuelve la grilla de NTI cuantizada
   a `uint8` (0 a 254 gris, 255 sin dato), el rango usado y la lista de alertados. Y en `calcular_vrp_granulo`, al
   final, **sólo si un interruptor del módulo está encendido** (por ejemplo `GENERAR_MINIATURA = False` por defecto):
   `rec["_miniatura"] = miniatura_nti(...)`.
   Por qué apagado por defecto: `calculate_vrp` y `calcular_vrp_granulo` los llaman 49 archivos (pruebas,
   experimentos, probes) y `run_pipeline.py` lo invocan 24 workflows. Con el interruptor apagado ninguno ve la clave
   nueva.
2. **`scripts/run_pipeline.py`**: un argumento `--miniaturas` que enciende el interruptor. Justo antes de cada
   `store.append_record(...)` se saca la clave con `rec.pop("_miniatura", None)` y se guarda en una lista en memoria
   con su llave `(datetime_utc, sensor, granule)`. Si alguien olvida el `pop`, `json.dump` del store revienta con
   `TypeError` (un `ndarray` no es serializable): falla ruidosa, no silenciosa, pero igual va una prueba (§6.6).
3. **Al terminar el volcán**, `run_pipeline.py` lee el JSON del store ya guardado, toma por familia de sensor los 10
   records más recientes y para cada uno escribe su PNG si la miniatura de esta corrida tiene **el mismo gránulo**
   que el record guardado. Si no la tiene (NASA no entregó ese gránulo en esta corrida), **conserva el PNG que ya
   había**. Si no hay ninguno, la entrada del índice dice `"miniatura": null`. Los PNG que ya no están entre los 10
   se borran. Escribe además el índice del volcán.
4. **`.github/workflows/nrt.yml`**: agregar `--miniaturas` a la línea del perfil `mirova_equivalent` y un
   `git add -A -- "data/miniaturas/${{ matrix.volcano }}"` en el paso de commit (con `-A` para que entren los
   borrados; un `add` por ruta como pide la nota S120).
5. **`pages-deploy.yml`: no cambia.** Ya copia `data/` entero y ya se dispara con `data/**`.

**No hace falta tocar `process_*.py`, `store.py` ni `mirova_equivalent.yaml`.** Si Nicolás prefiere que el interruptor
viva en el perfil (como los demás `enable_*`, A89) en vez de en la línea de comandos, eso sí toca
`mirova_equivalent.yaml` y entra en A45 (§9).

Por qué la regeneración completa funciona: el NRT procesa en cada corrida el día en curso y los 7 anteriores
(`default_date_window`, `lookback_days = 7`) y no salta los gránulos ya guardados. Las 10 últimas pasadas nocturnas
cubren unos 3,4 días (§5), así que cada corrida vuelve a tener en memoria la grilla de las 10. No hay estado que
llevar entre corridas salvo el de §4.3 punto 3 para cuando NASA falla.

### 4.4 Formato del índice (propuesta)

`data/miniaturas/<Volcan>/indice.json`:

```json
{"volcan": "NevadosDeChillan", "actualizado_utc": "2026-11-15T06:40:00Z",
 "familias": {"VIIRS375": [
   {"datetime_utc": "2026-11-15 06:18", "sensor": "VIIRS_NOAA21", "granule": "VJ202IMG_NRT.A2026319.0618...",
    "product_version": "nrt", "archivo": "VIIRS375/20261115_0618_VIIRS_NOAA21.png",
    "n": 134, "paso_m": 375, "escala_nti": [-0.97, -0.90], "dayflag": 0,
    "vrp_mw": 1.857, "sensor_zenith_deg": 51.39, "sensor_azimuth_deg": -85.4,
    "motivo_vacio": null, "celdas_sin_dato": 0, "alertadas": [[66, 67], [67, 65]],
    "via_codigo_mirova": true}
 ], "VIIRS750": [], "MODIS": []}}
```

Los números del índice se copian del record guardado, no se recalculan, así el tablero y la miniatura nunca dicen dos
cosas distintas. La clase y su color los pone el tablero con su propia tabla, como ya hace.

## 5. Formato y tamaño, medidos

Medí con grillas reales guardadas, sin tocar `data/`: 311 escenas de V750 (M13 y M15, 67 × 67) de
`experiments/_s163_o2/entradas_o2.mat` y 422 de V375 (sólo I4, 134 × 134) de
`experiments/_s162_v375/o2_375/entradas_v375.mat`, con el detector real de la vía importado sin modificarlo. Script
y salidas fuera del repo (scratchpad de la sesión, `medir_miniaturas.py` y `miniaturas/medicion.json`).

PNG en gris de 8 bits, `optimize=True`, estiramiento 2 a 98 % por escena (el peor caso para comprimir):

| Grilla | 256 tonos, mediana (p90) | 64 tonos | 16 tonos |
|---|---|---|---|
| V750 NTI, 67 × 67 | 3,4 KB (3,6) | 2,3 KB (2,5) | 1,4 KB (1,7) |
| V375 I4, 134 × 134 | 12,4 KB (13,9) | 8,1 KB (9,4) | 4,7 KB (6,0) |
| MODIS 51 × 51 (ESTIMADO: NTI de V750 reducido a 51 × 51) | 1,9 KB (2,1) | | |

Otras formas medidas para V750: PNG con paleta y la máscara quemada en rojo 5,2 KB (la paleta de 768 bytes y el modo
P comprimen peor); arreglo en JSON como lista de números 16,5 KB; `uint8` comprimido con zlib en base64 5,7 KB.

Salvedades: el V375 está medido sobre la radiancia I4 y no sobre el NTI, porque el archivo guardado no trae I5. El NTI
es función suave de I4 e I5, así que debería comprimir parecido, pero es estimación. El MODIS también es estimación.

**Recomendación: PNG en gris de 8 bits, un archivo por pasada**, que el tablero lee en un `<canvas>` para pintar el
sin dato y los alertados. Es el formato más chico de los medidos, el navegador lo cachea por archivo y se puede mirar
directo en GitHub. 64 tonos ahorran un 35 % y a esta escala de grises el ojo no lo nota; queda como opción (§9).

**Suma por volcán**: 10 × (12,4 + 3,4 + 1,9) KB ≈ 177 KB de PNG, más el índice (unos 30 registros de ~0,4 KB más los
alertados): **≈ 0,19 MB por volcán**. **11 volcanes ≈ 2,1 MB; 45 volcanes ≈ 8,5 MB.**

### Convivencia con el techo de 1 GB de GitHub Pages

Lo que hoy sale al sitio (medido en este árbol, tamaño real de archivos): `data/` sin las cuatro carpetas excluidas
848 MB, `imagenes/` 10,2 MB, los dos CSV 11,6 MB, `frontend/` 1,3 MB, más los `_recent` que arma
`build_recent_json.py` (unos 27 MB según el comentario del workflow). **Unos 0,9 GB**, comprimido 87 MB (artefacto
`github-pages` del 2026-11-15 11:31 UTC). Las miniaturas suman 2,1 MB (0,2 %) con 11 volcanes y 8,5 MB (0,9 %) con
45. **No son el problema del techo**; el margen se lo comen las carpetas viejas de experimentos que hoy también se
publican (`_s154_reproc_k_historico` 159 MB, `_f70_a` y `_f70_b` 69 MB, `_s129_*` 63 MB y otras), tema ya anotado y
fuera de este diseño.

### Dónde viven y quién las borra

- Ruta: `data/miniaturas/<Volcan>/<FAMILIA>/<AAAAMMDD_HHMM>_<SENSOR>.png` y `data/miniaturas/<Volcan>/indice.json`.
  Fuera de `data/mirova_equivalent/` a propósito, para que `build_recent_json.py` y las pruebas que recorren esos
  JSON no las vean.
- **Las borra el mismo job del NRT** de ese volcán, al reescribir su carpeta (§4.3 punto 3), y el `git add -A` del
  commit sube los borrados. No hay limpiador aparte.
- Las sombras y guardias no generan miniaturas (no llevan `--miniaturas`), así que no aparece ninguna carpeta nueva
  que haya que excluir de Pages.

### Crecimiento de la historia de git

Un PNG rotado sale del árbol pero queda en la historia para siempre. Contado en `data/mirova_equivalent/` del 1 al 14
de noviembre de 2026, los 11 Tier A escriben por día **23,8 pasadas MODIS, 31,9 VIIRS 375 y 33,1 VIIRS 750** (en
Chillán 2,3; 2,9 y 3,0). Eso da 23,8 × 1,9 + 31,9 × 12,4 + 33,1 × 3,4 ≈ **0,55 MB nuevos por día**, hasta el doble si
cada pasada se regenera una vez al llegar el gránulo estándar (§6.3): **0,2 a 0,4 GB por año**. Es chico al lado del
ritmo que ya tiene el repositorio por los JSON (AUDIT_S121 midió unos 30 MB por día) y no justifica una rama huérfana
ni artefactos de Actions, que agregarían una carrera nueva y una pieza que mantener. Si algún día pesa, el arreglo es
mover la carpeta a una rama huérfana con un solo commit; el formato no cambia.

## 6. Riesgos

### 6.1 Tiempo extra por pasada en Actions

Codificar una miniatura de 134 × 134 en PNG con `optimize=True` toma **3,2 ms** (medido, 200 repeticiones, sobre
ruido, que es el peor caso). Por corrida y volcán se procesan unas 8 noches × ~3 pasadas × 3 sensores ≈ 72 pasadas,
o sea **≈ 0,25 s** contra jobs de 20 a 56 minutos. La memoria también es despreciable (72 × 18 KB). Leer el JSON del
store al final para elegir las 10 ya lo hace el paso de verificación del workflow.

### 6.2 Carreras de commit (A47 y `push-main`)

El diseño no abre ninguna carrera nueva: cada job del matrix escribe **sólo la carpeta de su volcán**, en el **mismo
commit** que su JSON, y ese commit ya está protegido por el grupo `push-main` del workflow y por el reintento
`pull --rebase -X theirs` de `nrt.yml`. Dos jobs nunca tocan los mismos archivos. Lo que sí rompería la regla A47 es
correr `--miniaturas` desde un reproceso local mientras corre el NRT sobre el mismo volcán; por eso el argumento va
sólo en `nrt.yml` y nunca en los reprocesos de historia (que además escribirían miniaturas de fechas viejas).

### 6.3 Gránulos NRT reemplazados por los estándar

`store.append_record` deduplica por `(datetime_utc, sensor)` y reemplaza el record NRT cuando llega el estándar
(`is_upgrade`). La miniatura sigue al record: el paso 3 de §4.3 escribe el PNG sólo si su gránulo coincide con el
`granule` del record guardado, así que tras el reemplazo la miniatura pasa a ser la del estándar y el índice lo dice
en `product_version`. En Chillán el reemplazo llega en horas (los gránulos `.021.2026318...` del 14-Nov ya son
estándar ese mismo día), así que casi toda pasada se dibuja dos veces: está contado en el «hasta el doble» de §5.

### 6.4 Pasadas que caen al detector K de guardia

Cuando la vía no puede correr (volcán sin grilla, MODIS sin MxD03 o con geolocalización de otra forma) el record sale
de K y lleva `via_codigo_mirova: "sin_grilla"`, `"sin_mxd03"` o `"geo_distinta"`. K trabaja en la geometría de barrido,
no en la grilla de MIROVA, así que **no hay miniatura** y el índice pone `"miniatura": null` con el motivo; el tablero
muestra la casilla vacía con «sin imagen (detector K)». Medido del 1 al 14 de noviembre en los 11 Tier A: **0 de
1.243 records cayeron a K** (MODIS 333, VIIRS 375 447, VIIRS 750 463, todos con `via_codigo_mirova: true`). Los
perfiles `guardia_k_modis` y `guardia_k_viirs` tienen la vía apagada y no llevan `--miniaturas`.

### 6.5 Divergencias con el panel de MIROVA que hay que decir en el tablero

- **Sólo noches.** `pipeline/fetch.py` filtra los gránulos diurnos antes de bajarlos (`_filter_nighttime_granules`),
  así que nuestras 10 últimas son 10 nocturnas (unos 3,4 días en Chillán) y las de MIROVA mezclan día y noche (10 en
  unas 36 horas). Agregar las diurnas es otra decisión: más descarga y el MIR de día no se usa (regla «MIR sólo
  nocturno»). ⚠️ S198 (merge con main): ya no vale para MODIS. Main abrió el día de MODIS (S193) y el store trae
  pasadas MODIS diurnas (`diag_codigo_mirova.dayflag = 1`; en Villarrica, Láscar y Llaima desde el 2026-11-17, 42 de
  93 records MODIS), así que la pestaña MODIS mezcla día y noche como MIROVA. El panel marca esas tarjetas «de día» y
  el aviso lo dice (`frontend/miniaturas.js`); VIIRS sigue sólo de noche.
- **Un paso partido en dos gránulos.** El 14-Nov NOAA-21 pasó sobre Chillán a las 06:36 y 06:42 UTC: son dos gránulos
  consecutivos de 6 minutos del mismo paso. Nosotros guardamos los dos (06:36 con VRP 25,3 MW y 6.927 celdas sin
  dato; 06:42 escena inválida con 9.309). MIROVA muestra sólo el de 06:42, en blanco a medias, y no muestra el de
  06:36. Lo observado no alcanza para decir por qué; queda como pregunta abierta y no lo arregla este diseño. En el
  tablero conviene marcar dos casillas del mismo satélite separadas por 6 minutos como «mismo paso».

### 6.6 Que la clave privada se escape al JSON

Si `_miniatura` llegara a `store.append_record` sin el `pop`, el `json.dump` falla con `TypeError` y el job queda rojo:
no se pierde nada en silencio, pero se cae el NRT de ese volcán. Va una prueba que corre `run_pipeline` con
`--miniaturas` sobre un gránulo de ejemplo y verifica que el JSON del store no tenga claves que empiecen con `_` y que
el índice tenga 10 entradas por familia o menos.

### 6.7 Transparencia (Resolución CPLT N°372)

Las miniaturas no deciden nada: no cambian la detección, el VRP ni la clase. Son un producto publicado nuevo, así que
la ficha `docs/FICHA_SDA_VRP_CHILE.md` gana una fila al mergear (regla S185, la versión se toma al mergear) y la
función nueva lleva su comentario «POR QUÉ». Desde que el tablero las lea, dejan de ser descartables (A88).

## 7. Cómo se vería en el tablero (boceto en texto)

En la ficha de cada volcán, bajo los gráficos, un bloque **«Últimas 10 pasadas»** con pestañas VIIRS 375, VIIRS 750
y MODIS (la del sensor de la última pasada, abierta):

```
 Últimas 10 pasadas · VIIRS 375 · Nevados de Chillán        [VIIRS 375] [VIIRS 750] [MODIS]
 ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
 │  NTI     │ │  NTI     │ │  NTI     │ │ ░░░░░░░░ │ │  NTI     │   borde = color de la clase
 │   ·■     │ │    ■     │ │    ■     │ │ ░sin dato│ │    ■     │   ■ = alertado (marca encima)
 │          │ │          │ │          │ │  NTI     │ │          │   ░ = sin dato (tramado, no blanco)
 └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
 15-11 03:18   15-11 02:36   15-11 01:42   14-11 03:42   14-11 03:36    hora de Chile (UTC al pasar el mouse)
 1,86 MW       8,05 MW       3,43 MW       sin lectura   25,3 MW        rojo si hubo anomalía, gris si no
 cenit 51°     cenit 19°     cenit 65°     escena        cenit 64°
 NOAA-21 NRT   NOAA-20       NOAA-21       inválida      mismo paso →
 ... segunda fila con las 5 anteriores ...
 Una anomalía puede ser un incendio u otra fuente no volcánica. Una nube puede taparla o atenuarla.
```

- La imagen se lee como dato: el canvas pinta el gris, el **sin dato con tramado** (no blanco, para no confundirlo con
  un foco saturado como pasa en MIROVA), y los alertados del índice con un cuadrito de color encima.
- Debajo, el texto que explica qué es «sin lectura»: «escena inválida» (borde de franja), «sun glint» o «sin
  anomalía». Es lo que el operador no puede saber hoy.
- Al hacer clic, la miniatura grande con la cruz del cráter y el círculo `inner_radius_km`.
- La implementación viene después y no toca el trabajo de la tanda 2 del tablero que va en paralelo en
  `frontend/index.html`.

## 8. Lo que queda abierto (no se resuelve aquí)

1. El rango fijo del NTI por sensor: medirlo sobre las grillas de un mes al implementar (§3).
2. Medir el tamaño del NTI de VIIRS 375 y de MODIS con grillas reales (aquí son estimaciones, §5).
3. El caso del paso partido en dos gránulos y por qué MIROVA muestra sólo uno (§6.5).
4. Si se agregan las pasadas diurnas (§6.5).
5. Los 34 volcanes fuera del NRT: tienen grilla en `pipeline/grillas_mirova.yaml` (45 de 45), pero hoy sólo corren en
   la sombra diaria, que no se publica. Sus miniaturas esperan la decisión de publicar los 34.

## 9. Lo que necesita la confirmación A45 de Nicolás

El diseño evita tocar `pipeline/process_*.py`, `store.py` y `pipeline/profiles/mirova_equivalent.yaml`. Aun así toca el
camino de producción, así que pido confirmación explícita, con tag defensivo `pre-miniaturas` empujado antes del
merge, para:

1. **Editar `pipeline/mirova_v750_codigo.py`**: la función pura `miniatura_nti` y la clave `_miniatura` en
   `calcular_vrp_granulo`, apagada por defecto. No está en la lista literal de A45, pero es el detector de producción de
   los tres sensores desde S172, B1 y B2, y la trato igual.
2. **Editar `scripts/run_pipeline.py`**: el argumento `--miniaturas`, el `pop` antes de `append_record` y el escritor
   de la carpeta del volcán con la rotación de 10.
3. **Editar `.github/workflows/nrt.yml`**: `--miniaturas` en el paso del perfil `mirova_equivalent` y el
   `git add -A` de la carpeta del volcán en el commit.
4. **Sólo si prefieres el interruptor en el perfil** y no en la línea de comandos: agregar `enable_miniaturas` a
   `pipeline/profiles/mirova_equivalent.yaml` (este sí es A45 literal).

Y cuatro decisiones de producto, con mi recomendación:

- **Producto**: NTI (recomendado) o temperatura del térmico.
- **Escala**: fija por sensor de noche (recomendada) o estirada por escena como MIROVA.
- **Tonos**: 256 (recomendado, 0,19 MB por volcán) o 64 (35 % menos).
- **Alcance**: los 11 Tier A ahora; los 34 cuando se decida publicarlos.

## 10. Lo implementado (y en qué se apartó del diseño)

- **Vía** (`pipeline/mirova_v750_codigo.py`): `GENERAR_MINIATURA = False`, `ESCALA_MINIATURA_T_K = (240.0, 290.0)`,
  `escala_nti(familia)` y `miniatura_nti(m13g, m15g, alertadas, familia)`; `calcular_vrp_granulo` agrega
  `rec["_miniatura"]` sólo con el interruptor encendido. La escala fija es el NTI de un cuerpo negro a 240 K y 290 K
  con las longitudes de onda de cada sensor y la Planck del .m: V750 de -0,975 a -0,882; V375 de -0,989 a -0,933; MODIS
  de -0,980 a -0,898. Contiene el fondo nocturno medido en V750 (§3); en V375 y MODIS cada miniatura guarda los
  percentiles 2 y 98 de su NTI para recalibrar con datos de producción.
- **Recolector y rotación** (`pipeline/miniaturas.py`, módulo nuevo): `Recolector.recoger` saca la clave antes del
  store; `escribir_volcan` hace lo de §4.3 punto 3. **Cambio:** el PNG se escribe con la biblioteca estándar
  (zlib, se prueban los cinco filtros PNG y queda el más chico), porque el NRT no instala Pillow. El índice no lleva
  hora de la corrida: sin pasadas nuevas no cambia ningún byte y no hay commit.
- **`scripts/run_pipeline.py`**: `--miniaturas`, `_MINIATURAS.recoger(...)` antes de cada `store.append_record` y
  `escribir_volcan` al terminar cada volcán (una falla ahí se imprime y no tumba el job). **Cambio:** el import va en la
  misma línea que el de `profile` y el recolector se define después de `process_date`, para no correr las líneas 252 y
  262 que cita CLAUDE.md (guard G8).
- **`nrt.yml`**: `--miniaturas` en el paso del perfil `mirova_equivalent` y `git add -A -- "data/miniaturas/<volcan>"`.
- **Tablero** (`frontend/miniaturas.js` nuevo y dos líneas de `frontend/index.html`): el panel de §7 antes de lo
  plegado de la página del volcán, con pestañas por sensor; el VRP de cada casilla es el que el tablero ya calcula para
  ese record (`eqVrp`), así que imagen y gráfico dicen lo mismo. Si el volcán no tiene `indice.json`, el panel no se
  muestra.
- **Pruebas**: `tests/test_miniaturas_por_pasada.py` (imagen sin pérdida y determinista, escala, nube más oscura que
  el suelo, la vía con y sin interruptor en los tres sensores, rotación, conservación sin gránulo, reemplazo NRT a
  estándar, K sin imagen, índice copiado del record, dos corridas iguales sin cambios, y que sólo `nrt.yml` use
  `--miniaturas`).
- **Corrida real** (probe temporal en la rama, runs 43718917391 y 43719887705, Chillán y Villarrica, 12 al 15 de
  noviembre de 2026, ya borrado): 30 imágenes por volcán (10 por sensor), 35 miniaturas generadas por corrida. Tamaño
  real por volcán: unos 134 KB de PNG (VIIRS 375 10,2 a 10,9 KB de mediana, VIIRS 750 2,6 a 2,8 KB, MODIS 1,5 a
  1,6 KB) más 22 a 31 KB de índice: **unos 0,16 MB por volcán, 1,8 MB los 11**, en línea con §5. Con la escala
  240 a 300 K el blanco puro queda en el 0,01 % de las celdas de la escena mediana de VIIRS 375 (con 290 K era 2,7 %):
  queda casi sólo para el foco. La pasada de 06:42 UTC del 14 de noviembre sale a medias con el tramado de sin dato,
  igual que la miniatura en blanco de MIROVA, y la de 06:36 trae la otra mitad con el foco.
