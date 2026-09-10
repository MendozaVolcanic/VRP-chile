# El cabo suelto de S133, resuelto: por qué bajar el ruido no mueve la detección

> Cierra por aritmética dos candidatos (la banda 22 y el remuestreo) sin gastar un run de CI, y
> responde la pregunta que el A/B de B22 dejó explícitamente abierta en S133.

## La pregunta que quedó abierta

`docs/s133/AB_B22_VEREDICTO.md` cerró con un enigma declarado:

> *"la detección casi no se movió y eso es sospechoso. Si el sigma baja un 30 %, los umbrales
> contextuales N·σ deberían bajar con él y la detección debería volverse más sensible. Que no se
> mueva merece entenderse antes de tocar producción."*

El razonamiento era correcto y la observación también. Faltaba un dato que no existía entonces.

## La respuesta

El umbral efectivo de los Tests 2 y 3 es `min(C1, μ + C2·σ)`, y está medido (S136,
`que_rama_manda.py`) que **el piso C1 gobierna el 100 % de los records de MODIS** y el 99,9 % de
VIIRS. Cuando el piso manda, el umbral **no depende de σ en absoluto**. Bajar el ruido del fondo un
30 % deja el umbral exactamente donde estaba, así que la detección no se mueve. No era sospechoso:
era la consecuencia necesaria.

Los números, sobre 11.953 records nocturnos de MODIS (verificado: el pipeline es night-only, cero
pasadas diurnas en los tres sensores):

| | |
|---|---|
| σ del dNTI | 0,00697 |
| μ + 5σ (el contraste, cumbre) | 0,03487 |
| piso C1 (Tabla 1, cumbre) | 0,003 |
| el contraste está | **11,6 veces por encima del piso** |

## Y eso descarta dos candidatos por aritmética

Para que el contraste pase a gobernar, σ tendría que bajar a 0,000596, o sea **caer 11,7 veces**.

- **La banda 22 en vez de la 21.** S133 midió que el sigma del fondo cae entre 23 y 43 %, o sea un
  factor de 1,3 a 1,8. Muy lejos de 11,7. **La banda 22 no puede mover la detección de MODIS**, por
  mucho que mejore el instrumento. Sigue siendo un frente de **magnitud** (allí el efecto es grande:
  la magnitud cae a una décima parte en Láscar y a una cuarta en Villarrica), pero no de detección.
  Los dos frentes quedan desacoplados, y eso simplifica la decisión pendiente sobre ese A/B.
- **Remuestrear a grilla regular.** El promediado baja el ruido como la raíz del número de píxeles,
  así que un factor 11,7 exigiría promediar unos **137 píxeles**, una ventana de más de 12 km de
  lado. El ROI1 del paper mide 5 km. La hipótesis del remuestreo que quedó abierta al descartar el
  filtro de intensidad **no alcanza tampoco**, ni de cerca.

## La observación que originó esto, y que sí quedó verificada

MODIS tiene un dNTI **5,10 veces más rugoso** que VIIRS 375 m, teniendo el píxel casi tres veces
más grande, lo que está al revés de lo que predice el promediado. El control descartó las dos
explicaciones fáciles: no es contaminación solar (cero pasadas diurnas) y no es composición de
volcanes ni fondo de altura (los mismos cuatro volcanes dominan ambos sensores, con el mismo
patrón: Villarrica 4,8x, Chaitén 5,7x, Llaima 4,7x, Copahue 4,8x).

La causa está identificada y no es nueva: es el ruido de cuantización de la banda 21 en el extremo
frío de su escala, que S133 ya diagnosticó y midió. Lo nuevo es que **ese ruido no es la palanca de
la sobre-detección**, porque la sobre-detección la decide un número fijo.

## Dónde queda el frente

Si ninguna mejora del ruido puede mover la detección de MODIS mientras el piso gobierne, y la
conectiva ya se descartó en sus dos lecturas, y el filtro de intensidad no es del pipeline, entonces
lo que queda es una pregunta más incómoda y más interesante: **¿por qué el mismo piso de 0,003 no
sobre-detecta en manos de MIROVA?**

Las opciones que sobreviven, ninguna verificada:

1. Su dNTI no está en nuestra escala **por definición**, no por ruido: quizá lo normaliza de otro
   modo, o lo calcula sobre un objeto distinto.
2. Los filtros de píxeles inadecuados podrían quitar el difuso no sólo del cálculo de μ y σ, sino
   también de los candidatos a activo. Hoy los aplicamos al pool.
3. El "resampling" del paper podría no ser un promediado, y entonces la aritmética de arriba no
   aplica a él.

Conviene atacarlas con contexto fresco. Las tres son de lectura de paper antes que de cómputo, que
es donde esta sesión rindió mejor.
