# Acercar el visualizador de VRP Chile al de MIROVA: auditoría y plan

Fecha: 2026-11-08 (S176). Estado: **PLAN para decisión de Nicolás; nada implementado.** Auditado en navegador real (panel interno de la app; Claude in Chrome no estaba conectado) sobre
`https://www.mirovaweb.it/NRT/` y `https://mendozavolcanic.github.io/VRP-chile/`. Tocar `frontend/` pide tag y sí de Nicolás (A45) y un cambio de vista se replica en `index.html`, `diario.html` y `mosaico.html` (S92).

## Por qué

Un operador compara las dos páginas con la misma pregunta: ¿qué pasó en este volcán, con qué sensor y dónde está el calor? MIROVA lo contesta en tres pasos cortos. La nuestra lo contesta con mucho más texto, separa satélites que para el volcán son el mismo instrumento, y no deja bajar lo que muestra. El objetivo es que quien venga de MIROVA reconozca la página. Lo que hacemos mejor sigue, pero fuera del camino principal.

## Cómo está organizada cada una

| Pregunta del operador | MIROVA | VRP Chile hoy |
|---|---|---|
| ¿Qué pasó recién en toda la red? | `latest.php`: tabla de pasadas, 528 filas, hora, volcán, VRP, distancia, sensor, y la fecha de la última pasada por sensor; fila en verde si hay alerta | «Últimas detecciones NRT», sólo detecciones y **no las pasadas sin nada**; la frescura está repartida en cada tarjeta |
| ¿Cómo voy a un volcán? | `volcanoes.php`: mapa y lista, 176 volcanes | 45 tarjetas con un promedio de 333 caracteres en las que tienen datos |
| ¿Qué muestra un volcán? | Pestañas por sensor (MODIS, VIIRS750, VIIRS375, Combinado MIR, MSI, OLI, Slideshow) y subvistas: últimas 10 imágenes, Log VRP, VRP lineal, Distancia máxima, Explorar mapa | Una sola vista con todos los sensores superpuestos, 7 pares de interruptores y tres gráficos |
| ¿Dónde están los píxeles? | `volcanoMap.php`: GeoTIFF de la última pasada sobre mapa, por sensor, con paleta, opacidad, rango, **leer el valor de un píxel, bajar GeoTIFF y KMZ** | Marcadores de los píxeles alertados y exportación CSV. La galería «Imágenes MIROVA» no sirve al público |
| ¿Qué se separa? | Sólo por sensor: VIIRS 375 es uno | Gráficos por satélite: SNPP, NOAA-20 y NOAA-21 en series distintas, en cada resolución (`frontend/index.html` l. 3012, 3196 a 3210, 3445) |

## Hallazgos

1. **La galería «Imágenes MIROVA» está muerta en el sitio público.** Muestra «TIFs georef (179)» y «KMZs (179)» en Chillán, pero apuntan a un archivo que sólo existe en tu computador (`archiveAvailable()`, `frontend/index.html` l. 1950). El índice es del 2026-05-30 y su último TIF del 05-20: promete algo que no entrega y está seis meses atrasado. Además, «PNGs mirovaweb (0)» en Chillán.
2. **No hay ninguna liga a MIROVA por volcán.** Sólo a la portada. MIROVA permite ligar directo (`volcanoDetails_VIR375.php?volcano_id=357070`, `volcanoMap.php?volcano=ChillanNevadosde&sensor=VIIRS375`). El `volcano_id` es el de GVP: comprobado en Chillán y Puyehue-Cordón Caulle contra `gvp_id` de `volcanoes.yaml`; los nombres de MIROVA son distintos a los nuestros (`ChillanNevadosde`) y están leídos para los 11.
3. **Las tarjetas traen demasiado.** La de Chillán: clase, VRP, sensores, distancia, píxeles, T máxima, fondo, ΔT, percentil, múltiplo de mediana, marca de MIROVA, conteos a 90 días, última detección, en dos husos, y estado. Lo que el operador usa para decidir cabe en cuatro.
4. **Las vistas se relacionan a medias.** `mosaico.html` liga a un volcán en `index.html?volcano=`, pero `diario.html` no lleva a su volcán, `comparacion.html` sólo tiene «volver», y al cambiar de vista no se conserva el volcán ni el periodo en todos los casos.
5. **Los 34 dicen «no monitoreado»** aunque se procesan (ver `experiments/_s176_preguntas/RESPUESTAS.md`).
6. **Lo que no sabemos dar hoy es la imagen.** El pipeline guarda los píxeles alertados (`lat`, `lon`, `dist_km`, `bt_k`, `fila`, `col`), no la escena. Un GeoTIFF como el de MIROVA requiere guardar la grilla, y eso toca `pipeline/`.

## Plan, por fases

**Fase 1: reconocible como MIROVA, sólo `frontend/`, sin tocar datos.** Tag `pre-s17x-visualizador`.
- Agrupar por sensor: MODIS, VIIRS 375 y VIIRS 750, sin separar satélites en gráficos ni pills. El satélite queda en el detalle de cada pasada.
- Tarjeta mínima: nombre, clase, VRP con sensor, y hace cuánto la última pasada. El resto pasa al detalle del volcán.
- Vista nueva `pasadas.html`, como `latest.php`: **todas** las pasadas de los 11, también las sin anomalía, con hora, volcán, VRP, distancia y sensor, filtro por volcán y sensor, y arriba la última pasada de cada sensor.
- Detalle de volcán por pestañas: MODIS, VIIRS 750, VIIRS 375, Combinado; y subvistas VRP, VRP log, Distancia, Mapa.
- Ligas directas a MIROVA para el mismo volcán y sensor.
- Sacar o rotular la galería muerta, y cambiar «no monitoreado» por «procesado, no publicado».
- Lo propio de VRP Chile (percentil, comparación con MIROVA, F5) se conserva en una sección plegada.
- Verificación: navegador real sobre la rama servida, con los mismos conteos de lo publicado antes y después (ningún cambio en `mirovaEqVrp` ni en qué se publica).

**Fase 2: bajar los píxeles, sin tocar `pipeline/`.** Botones KMZ, GeoJSON y CSV de los píxeles alertados de una pasada, armados en el navegador con el footprint nominal de cada sensor. Da «dónde están los píxeles» para Google Earth o QGIS. Límite que se rotula: son los píxeles alertados, no la escena, y los de la vía no traen VRP por píxel.

**Fase 3: GeoTIFF real, como MIROVA.** La vía guarda en el NRT la grilla de la última pasada por volcán y sensor, y el mapa la muestra con paleta, rango y lectura de píxel, usando las mismas bibliotecas abiertas que MIROVA (`geotiff.js`, `georaster-layer-for-leaflet`). Toca `pipeline/`, así que va después de los encendidos. Decisión necesaria: **dónde vive**. Sobrescribir archivos en el repo engorda el historial en cada corrida; un almacén externo o una rama aparte evita eso, pero es infraestructura nueva y su costo está SIN MEDIR.

## Lo que no se hará

Copiar la marca, el aspecto ni los textos de MIROVA: es la organización de la información lo que se calca. Los productos MSI y OLI quedan fuera. Tampoco se abren aquí los 34 volcanes: se decide aparte.

## Decisiones para Nicolás

| # | Pregunta | Recomendación |
|---|---|---|
| 1 | ¿Fase 1 antes o después del encendido de VIIRS? | Después de PR A y #965: no chocan en datos, pero tocan `cambio_detector.js` y el mapa |
| 2 | ¿Las tarjetas mínimas tienen esos cuatro datos? | Sí |
| 3 | Fase 3: ¿vale la infraestructura? | Decidir tras usar la Fase 2 |
