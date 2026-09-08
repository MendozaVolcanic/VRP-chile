# Las dos noches que pierde el brazo fiel — Isluga, 30-jun y 1-jul

> Primera investigación bajo el criterio de Nicolás (2026-09-07): *«no debemos perder nada que
> MIROVA esté entregando, ser lo más fiel posible y entender por qué sucede y arreglar cuando
> diferimos»*. Datos parciales del A/B (chunk 1, Isluga completo; los otros cinco volcanes
> todavía corriendo). Todo sale de los artefactos del run 34173711390 y del cargador canónico.

## Qué publicó MIROVA esas noches

| noche | pasada UTC | sensor | VRP | distancia | canal |
|---|---|---|---|---|---|
| 2026-06-30 | 05:18:01 | VIIRS 375 m | 0,09 MW | **0,75 km** | consolidado |
| 2026-07-01 | 05:42:02 | VIIRS 375 m | 0,10 MW | **0,75 km** | consolidado |

Las dos son del canal consolidado, o sea del algoritmo de MIROVA sin intervención humana, y las
dos ponen la fuente **a 0,75 km** de su centro de grilla: en el cráter.

## Qué hizo cada brazo, en la misma pasada

**30 de junio, 05:18, NOAA-20** (la pasada que MIROVA publica):

| brazo | fuente | clase | cúmulo |
|---|---|---|---|
| A control | `test1_roi` | summit | 1 px, 0,072 MW, a **2,769 km** |
| C condicionado | `test1_roi` | summit | 1 px, 0,072 MW, a **2,769 km** |
| B sin keep_peak | `test1_roi` | **far** | 1 px, 0,062 MW, a 18,88 km |
| D ambos | `test1_roi` | **far** | 1 px, 0,062 MW, a 18,88 km |

**1 de julio, 05:42, NOAA-21** (la pasada que MIROVA publica):

| brazo | fuente | clase | cúmulo |
|---|---|---|---|
| A control | `ctx_cluster` | summit | 1 px, 0,083 MW, a **0,945 km** |
| B sin keep_peak | `ctx_cluster` | summit | 1 px, 0,037 MW, a **0,945 km** |
| C condicionado | `test1_roi` | summit | 1 px, 0,083 MW, a **0,945 km** |
| D ambos | `test1_roi` | summit | **sin cúmulo** |

## Las dos noches son casos distintos, y sólo una es una pérdida

**El 30 de junio no es una pérdida: el control acertaba con el objeto equivocado.** MIROVA vio
algo a 0,75 km de su centro; nosotros publicamos un píxel a 2,77 km del cráter. La diferencia de
los dos radios es 2,02 km, y como una diferencia de radios es una cota **inferior** de la
separación entre dos puntos (A93), con un presupuesto de error de 0,55 km eso son objetos
distintos con seguridad. El control «acierta» esa noche sólo porque el cruce se hace por fecha:
es el artefacto del borde del disco (D19) coincidiendo en el calendario con una detección real
del cráter. Que el brazo fiel lo pierda es **correcto**, y contarlo como falso negativo sería
premiar una coincidencia.

**El 1 de julio sí es una pérdida real.** Ahí el control tiene un cúmulo a 0,945 km con
0,083 MW, contra los 0,75 km y 0,10 MW de MIROVA: la cota de separación es 0,195 km, dentro del
presupuesto, y las magnitudes son del mismo orden. Es el mismo objeto. El brazo D lo pierde.

## Por qué se pierde, con el mecanismo

Ese cúmulo del cráter **no lo detecta nuestro primer pase**. Sobrevive por una de dos vías, y
las dos son las que el A/B está poniendo en cuestión:

- en el brazo B lo sostiene el **segundo pase corriendo suelto** (el primer pase da cero
  píxeles y aun así el segundo marca);
- en el brazo C lo sostiene **`keep_peak`** (el filtro contextual no deja nada y el pico se
  conserva igual).

Cuando se arreglan las dos (brazo D), desaparece. Es decir: **el cráter de Isluga esa noche
existe para MIROVA y para nuestras dos vías permisivas, pero no para nuestro primer pase.**

## Qué significa, según la clasificación del pre-registro

Cae en el **caso 1: nos falta algo que MIROVA hace y nosotros no**. No es una pasada diurna
(05:42 UTC es noche cerrada en Chile) ni un problema de entrada: el mismo granule produce el
píxel, sólo que ninguno de nuestros tests literales lo marca. Y como el canal consolidado no
tiene supervisión humana, MIROVA lo detectó **con su algoritmo**. La diferencia es algorítmica y
por lo tanto investigable, que es exactamente el punto de fijar el criterio en cero.

Lo que queda por averiguar es cuál de los tests literales debería haberlo marcado y no lo hizo:
los umbrales de la Tabla 1, el fondo contra el que se comparan, o la región de interés sobre la
que se calcula la estadística. Eso es la investigación siguiente, y necesita el probe por etapa
sobre esa pasada concreta, no el A/B agregado.

## Consecuencia inmediata para el evaluador

El criterio 1, tal como estaba escrito, contaba las dos noches como pérdidas del brazo D. Una lo
es y la otra no. Emparejar por fecha sin mirar **dónde** puso cada sistema su fuente convierte
una coincidencia de calendario en un acierto, y castiga al brazo que deja de producir el
artefacto. El evaluador ahora exige, además de la coincidencia de noche, que la cota de
separación entre el cúmulo del control y la fuente de MIROVA sea compatible con el presupuesto
de 0,55 km; las noches donde el control acertaba con un objeto lejano se reportan aparte, como
lo que son.
