# El filtro de intensidad de Laiolo 2026 no es del pipeline NRT — y el piso C1 acota el frente

> Descartado por **dos vías independientes**, documental y empírica, antes de escribir una línea
> de código. Cierra el candidato que yo mismo había propuesto al terminar el veredicto de la
> conectiva.

## Vía documental: la cita es del dataset del estudio, no del sistema

El pasaje completo, leído en el PDF con contexto (`s00445-025-01932-y.pdf`, p. 4, líneas 66-73):

> *"**The VRP time series (Fig. 2)** coming from the different sensors/detectors **are combined
> and filtered** in terms of distance and/or intensity of the thermal anomaly to minimize the
> false alerts and the double counting (coming from different detectors acquiring at the same
> time) thus resulting in 9712 data points (ca. 12%; **Online Resource 1**). Importantly, no
> atmospheric correction or cloud-contamination automatic filtering is applied **to the dataset**."*

Tres marcas, y las tres apuntan al mismo lado:

1. **Voz pasiva** con sujeto «the VRP time series (Fig. 2)» — la serie **de este paper**, no el
   sistema.
2. El resultado va al **Online Resource 1**, o sea el material suplementario del estudio.
3. La frase siguiente dice «to **the dataset**», no «the algorithm».

Es la preparación del conjunto de datos del estudio de Stromboli. La regla de verificación
verbatim de MISSION separa exactamente esto: *"the system computes/applies X automatically"* es
parte del clon; una descripción en pasiva del procesamiento de un caso de estudio, no. Aplicarlo al
pipeline sería repetir el drift de la Eq.16 (identificado en S99 y movido a beyond-MIROVA).

## Vía empírica: el canal NRT no muestra ningún piso

Medido sobre las 1.952 alertas con VRP > 0 del ground truth (CONS ∪ OCR, `piso_mirova.py`):

| | |
|---|---|
| mínimo publicado | **0,0100 MW** |
| percentil 1 · 5 · 10 | 0,03 · 0,05 · 0,07 MW |
| alertas bajo 0,1 MW | **358 — 18,3 %** |
| los doce valores más chicos | 0,01 · 0,02 ×8 · 0,03 ×3 |

No hay salto: la distribución baja de forma continua hasta 0,01 MW. **MIROVA NRT publica alertas
de una centésima de megavatio.** Y los mínimos por sensor —MODIS 0,14 · VIIRS 750 m 0,09 · VIIRS
375 m 0,01— siguen el orden de la resolución, así que son **límite de sensibilidad del
instrumento**, no un corte administrativo.

Queda descartado que MIROVA aplique un filtro de intensidad en el canal que comparamos.

*(El «double counting» de la misma frase es harina de otro costal y **ya está incorporado**: D14
lo registró en S128 como respaldo escrito de nuestra convención de un par por noche.)*

## Lo que el piso C1 acota, y reduce mucho el espacio de búsqueda

Con la conectiva actual el umbral efectivo es `min(C1, μ + C2·σ)`, y está medido que **el piso
gobierna el 100 % de los records de MODIS y el 99,9 % de VIIRS**. De ahí se sigue algo que conviene
tener presente antes de proponer nada:

**mientras el piso mande, todo lo que toque μ o σ es irrelevante.** Eso deja fuera, sin necesidad
de experimento, a tres candidatos que estaban en la lista:

- cambiar el **pool** sobre el que se calculan μ y σ (la «imagen» del paper contra nuestro ROI);
- **retirar los píxeles del Test 1** de ese pool (el GAP #A, hoy con su flag apagado);
- ajustar **C2** (los 5 y 10 de la Tabla 1).

Los tres mueven el término estadístico, que no decide. **Lo único que decide es C1 comparado con
nuestro dNTI.** Y C1 son los valores de la Tabla 1, así que la pregunta que queda es de **escala**:
¿nuestro dNTI vive en la misma escala que el dNTI para el que Coppola calibró 0,003?

Hay un indicio medido de que no: en MODIS la mediana de σ_dNTI es 0,00697, así que **C1 = 0,003
queda a menos de medio sigma del fondo**. Para que C1 fuera «un umbral mínimo que hay que superar»
en escenas homogéneas —lo que el paper dice que es— tendría que estar bastante por encima del ruido
de fondo, no por debajo.

## El candidato que eso sugiere, y que NO está verificado

El paper habla repetidamente de las **«resampled matrices»**: MIROVA remuestrea la escena a su
grilla regular antes del análisis espacial (aparece incluso en la definición de los píxeles
inadecuados, «all the pixels at the edge of the *resampled* matrices»). Un remuestreo **promedia y
suaviza**, y eso baja la textura local, que es justamente lo que el dNTI mide. Nosotros trabajamos
sobre píxeles nativos.

Si el dNTI de MIROVA es más liso que el nuestro, su C1 = 0,003 es un umbral exigente y el nuestro
es permisivo — sin que ninguno de los dos números esté «mal». **Es una hipótesis, no un hallazgo**:
requiere medir el σ_dNTI antes y después de un remuestreo a grilla regular, y compararlo con lo que
C1 supone. Ojo con no confundirlo con D16, que cerró la grilla UTM como explicación del
**sub-reporte de magnitud**: esto es sobre el **ruido del índice**, que es otra cosa.
