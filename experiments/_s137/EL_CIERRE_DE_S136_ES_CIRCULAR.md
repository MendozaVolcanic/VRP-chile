# S137 · El corolario que cerró tres frentes descansa sobre la lectura que la misma sesión refutó

> Lectura profunda de Coppola 2016a SP426.5 sobre el PDF (PyMuPDF, no el `.txt`, que corrompe los
> operadores: el mayor-que sale como punto y el menor-que como coma). Sin tocar código ni correr CI.

## El problema, en una frase

S136 cerró tres frentes con este corolario: *"mientras el piso mande, todo lo que toque mu o sigma
es irrelevante"*. Eso es cierto **sólo bajo la conectiva `min`**, que es la lectura que la misma
sesión midió y encontró incapaz de reproducir a MIROVA (3 de 3 negativos con falso positivo).

## Los dos brazos, con el detalle caso a caso

De `out_apendice/` y `out_apendice_prosa/`, los dos runs de S136 (34284386094 y 34310522104):

| caso | volcán | el autor publica | brazo `min` (producción) | brazo `max` (prosa) |
|---|---|---|---|---|
| A1 | Bezymianny | detecta | conforme | **falso negativo** |
| A2 | Eyjafjallajokull | detecta | conforme | **falso negativo** |
| A3 | Erta Ale | detecta | conforme | conforme |
| A5 | Ubinas | detecta | conforme | **falso negativo** |
| A6 | Villarrica | detecta | conforme | **falso negativo** |
| A8 | Etna | detecta | conforme | conforme |
| A4 | Dubbi | **no** detecta | **falso positivo** | conforme |
| A7 | Tolbachik | **no** detecta | **falso positivo** | conforme |
| A9 | Stromboli | **no** detecta | **falso positivo** | conforme |

Los dos positivos que `max` conserva son los de señal más fuerte (lago de lava permanente y Etna).
Los cuatro que pierde son los débiles. Esa es la firma de un umbral demasiado alto, no la de un
mecanismo equivocado.

## Por qué el corolario no se sostiene

El umbral efectivo de los Tests 2 y 3 es `combinar(C1, mu + C2 sigma)`.

- Con **`min`**: medido por S136, `mu + 5 sigma` vale 0,03487 y el piso C1 vale 0,003, o sea el
  contraste está 11,6 veces por encima. El menor de los dos es siempre el piso. Sigma no entra.
  De ahí el corolario, y de ahí que S133 viera que bajar el ruido no movía la detección.
- Con **`max`**: el umbral ES `mu + C2 sigma`. Sigma no es que importe, es lo **único** que decide.
  Cualquier reducción del ruido mueve la detección en proporción directa.

La frase de S136 *"la banda 22 no puede mover la detección de MODIS, por mucho que mejore el
instrumento"* es correcta bajo `min` y **falsa bajo `max`**. Y los frentes que ese corolario cerró
sin A/B (el pool de mu y sigma, el retiro de los píxeles del Test 1 de ese pool, ajustar C2) son
justamente los que operan sobre sigma.

El experimento que nadie corrió es la **combinación**: `max` con un sigma menor. S136 corrió `min`
con sigma de hoy, y `max` con sigma de hoy. Nunca `max` con sigma reducido.

## La predicción, y su límite

Bajo `max` el umbral nunca baja de C1, porque el máximo lo garantiza. Entonces con sigma tendiendo a
cero el brazo `max` **converge exactamente al brazo `min` de hoy**: 6 de 6 positivos y 0 de 3
negativos. Reducir sigma sin límite no es la solución, y esto acota el problema por los dos lados:

- sigma de hoy: `max` es demasiado estricto, pierde 4 positivos débiles.
- sigma muy reducido: `max` degenera en el piso y vuelve a aceptar los 3 negativos.

La pregunta empírica es si existe un régimen intermedio donde los 6 positivos sobrevivan y los 3
negativos sigan rechazados. La batería del Apéndice A la responde de forma directa, y es lo que la
convierte en el instrumento correcto para este frente.

## Y esto disuelve la contradicción del paper

S136 estableció que el paper se contradice: la fórmula dice `or` y la prosa describe C1 como mínimo
a superar con el análisis estadístico mandando en escenas variables. Las dos lecturas no pueden ser
ciertas a la vez **en nuestro régimen**, donde los dos umbrales están separados 11,6 veces.

Pero en un régimen donde `C1` y `mu + C2 sigma` estén al mismo nivel, la distinción entre `min` y
`max` es inmaterial: dan casi lo mismo. La contradicción del autor deja de ser un error y pasa a ser
una señal de que **en su sistema los dos brazos están al mismo nivel**, o sea que su sigma del dNTI
es del orden de diez veces menor que el nuestro. Es la hipótesis más simple que explica a la vez la
contradicción del texto y que el mismo piso de 0,003 no le sobre-detecte a él.

## Las tres divergencias literales que inflan nuestro sigma, verificadas hoy en el código

El paper describe tres pasos previos a la detección que no estamos replicando. Los tres actúan sobre
el ruido del dNTI, que es lo que decide bajo `max`.

| # | el paper (verbatim del PDF) | nuestro estado hoy | evidencia |
|---|---|---|---|
| 1 | *"we built a corrected spectral band centred at 3.959 um (band L21ok), by using the L21 or L22 radiance, depending on band 22 saturation (or not)"*, o sea **B22 manda y B21 sólo entra donde B22 satura** | B21 primaria | `ENABLE_MODIS_B22_PRIMARY = False`; el propio `process_modis.py:325` documenta que el ON es el que sigue al paper |
| 2 | *"we cropped and resampled (into an equally spaced 1 km grid)"*, y el motivo explícito: *"because the hotspot detection scheme, described below, requires homogenous pixel scale"* | no remuestreamos | `ENABLE_UTM_REGRID = False`, con el cableado ya hecho en `process_modis.py:502` |
| 3 | *"The georeferred data were also scanned in order to remove the bow-tie effect"* | MODIS no lo trata | sin coincidencias de bow-tie en el camino MODIS; los hits son de VIIRS, que lo agrega a bordo |

Sobre el punto 2, la aritmética de S136 que lo descartó (haría falta promediar 137 píxeles para un
factor 11,7) **trata el remuestreo como promediado de ruido blanco**, y el paper no lo presenta así.
Su función declarada es dar escala de píxel homogénea, porque el kernel de 8 vecinos supone vecinos
equidistantes. Sin remuestrear, el crecimiento del píxel fuera del nadir y el solapamiento del
bow-tie hacen que "vecino" signifique cosas distintas en cada parte de la escena, y eso ensucia el
dNTI de un modo que no se modela como raíz de N. Es la opción 3 que S136 dejó abierta, y el texto
del paper la respalda.

Sobre el punto 1, lo medido por S133 es el sigma del **fondo BT** (cae entre 23 y 43 por ciento),
que no es el sigma del **dNTI** que gobierna los Tests 2 y 3. Nadie midió el segundo. Son objetos
distintos y la propagación entre uno y otro es plausible, no demostrada.

## Lo que NO se afirma acá

- No se afirma que MIROVA implemente `max`. Sigue sin haber cita que lo diga.
- No se afirma que B22 o el remuestreo bajen el sigma del dNTI lo suficiente. No está medido.
- No se afirma que exista el régimen intermedio. Es la pregunta, no la respuesta.

## Lo que corresponde medir, en orden de costo

1. **Sigma del dNTI bajo B22 y bajo remuestreo**, por separado y juntos, sobre escenas ya
   descargadas. Es el número que falta y decide si el frente existe.
2. Si el sigma baja de forma apreciable, la **batería del Apéndice A con los brazos combinados**.
   Un cambio sirve si y sólo si conserva los 6 positivos y cura los 3 negativos.
3. Los frentes que el corolario cerró sin A/B (pool de mu y sigma, retiro de los Test 1 de ese pool,
   C2) vuelven a estar vivos **si y sólo si** la conectiva pasa a ser `max`. Bajo `min` siguen
   cerrados, y el cierre de S136 sigue siendo correcto para esa lectura.
