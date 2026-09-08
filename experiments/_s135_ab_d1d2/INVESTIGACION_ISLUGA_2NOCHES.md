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

---

## Segundo tramo: por qué el primer pase no ve ese cráter (1 de julio, 05:42)

Los diagnósticos que el propio registro persiste alcanzan para llegar bastante lejos sin volver
a bajar el granule.

| diagnóstico | valor |
|---|---|
| píxeles del primer pase (Tests 2 ∧ 3) | **0** |
| píxeles recapturados por el segundo pase | 1 (el del cráter, a 0,945 km, 270,43 K) |
| Test 1 integrado | **dispara**, 89 píxeles, k observado 6,09 |
| fondo global | 267,72 K |
| NTI máximo menos NTI del fondo | 0,009 |
| μ y σ del dNTI de la escena | −1,4·10⁻⁶ y 8,2·10⁻⁴ |
| umbral efectivo del Test 2 | 0,003 |
| umbral efectivo del Test 3 | 0,0026 |

**El píxel del cráter existe y está caliente**: 270,43 K contra un fondo de 267,72, casi tres
grados por encima, y el índice normalizado de la escena se despega nueve milésimas del fondo.
Lo que no alcanza es el **contraste contra sus ocho vecinos**, que es lo que miden los Tests 2 y
3. En un cráter cuya anomalía es más ancha que un píxel de 375 metros, los vecinos ya están
tibios y la diferencia local se diluye: el píxel no es anómalo respecto de su entorno inmediato
aunque el conjunto sí lo sea respecto de la escena. Por eso el primer pase entrega cero.

**Y sin embargo el Test 1 sí dispara.** Ese es el camino que integra la energía sobre todo el
disco en vez de mirar píxel contra vecino, y es justamente el que sirve para una fuente débil y
extendida como ésta. Dispara con holgura, 6,09 veces la desviación del fondo.

Entonces la pregunta se corre de lugar: **el problema no es que no detectemos, es que lo que
detecta el Test 1 no llega a publicarse.** El filtro contextual de S99 intersecta la máscara del
Test 1 con la máscara de anomalía contra vecinos, que en esta pasada está vacía, y el resultado
es vacío. Con `keep_peak` encendido queda el pico —que en los nevados suele ser el borde, D19—;
apagado, no queda nada.

Ese filtro no viene de Coppola. El Test 1 integrado del paper no se intersecta con la máscara
contextual: son dos caminos de detección, no uno filtrado por el otro. La intersección se
introdujo como candidato en S99 para cortar el halo nival, y `keep_peak` se agregó encima como
guarda contra el falso negativo del cráter. Este caso muestra las dos caras del arreglo: la
guarda evita perder el cráter, pero lo hace publicando el píxel equivocado.

**Hipótesis para la próxima investigación, no para implementar acá:** que el camino correcto no
sea elegir entre `keep_peak` encendido o apagado, sino revisar si el Test 1 integrado debe estar
sujeto al filtro contextual. Es una pregunta de fidelidad y pasa por las tres preguntas de
MISSION antes que por cualquier A/B. Queda anotada, con este caso como evidencia de una pasada
donde MIROVA publica, el Test 1 dispara, y aun así no publicamos nada por la intersección.

**Lo que este tramo no prueba.** Es una pasada. No se midió cuántas veces se repite el patrón
(Test 1 dispara, primer pase en cero, intersección vacía) ni si MIROVA llegó a esa detección por
su Test 1 o por sus Tests 2 y 3, que no podemos observar. Y el valor de 0,009 es el índice
absoluto contra el fondo de escena, no el contraste local que evalúan los tests: sirve para
decir que hay señal, no para decir que los tests deberían haberla marcado.

---

## Tercer tramo: cuántas veces se repite el patrón (cierra la limitación declarada arriba)

`frecuencia_patron_test1.py` → `frecuencia_patron_test1.json`. Universo: los 4.571 records de
VIIRS 375 m de los 11 Tier A entre el 2026-06-01 y el 2026-09-07, con las alertas de pasadas
diurnas excluidas (98).

| | | |
|---|---|---|
| records del universo | 4.571 | |
| con el patrón (Test 1 dispara, primer pase en cero) | **2.315** | 50,6 % del universo |
| de ellos, publicados como *summit* | 2.036 | 87,9 % del patrón |
| de ellos, con alerta de MIROVA esa noche | 606 | 26,2 % |
| **y además el mismo objeto** (cota ≤ 0,55 km) | **118** | 5,1 % |

**El patrón es la mitad del sensor, no una rareza.** En una de cada dos pasadas de VIIRS 375 m
el Test 1 integrado dispara y el contraste contra vecinos no marca nada. Es el régimen normal de
un volcán tranquilo con anomalía difusa, no una excepción.

**Y 118 de esas pasadas son detecciones reales confirmadas.** En ellas MIROVA publica, nosotros
publicamos, y las dos fuentes son plausiblemente el mismo objeto. Todas dependen de `keep_peak`
o del segundo pase suelto, porque el primer pase no marcó nada. Se concentran en Lastarria (35),
Isluga (33), Chaitén (24), Planchón-Peteroa (12) y Nevados de Chillán (7).

Eso es la tensión A83/A84 medida: **hay 118 pasadas confirmadas que hoy sobreviven gracias a los
dos mecanismos que el A/B está poniendo en cuestión.** No implica que se pierdan 118 noches —el
criterio es por noche y otra pasada de la misma noche puede salvarla, que es justamente lo que
el A/B mide— pero fija el tamaño del riesgo.

### Un matiz que corrige la lectura de D19

Los ejemplos traen una sorpresa útil. En Copahue, el 27 de julio, nuestro cúmulo está a 2,9 km
del cráter y **MIROVA reporta 2,7 km esa misma pasada** (cota 0,21 km: el mismo objeto). Lo
mismo a las 06:00 y a las 06:36.

O sea: **un cúmulo a casi tres kilómetros del cráter no es automáticamente el artefacto del
borde**. En algunos volcanes MIROVA también pone su fuente ahí. La distancia por sí sola no
separa el artefacto de la señal, igual que no lo hacía ninguno de los discriminantes físicos que
S116 barrió. Lo que separa es la coincidencia con lo que MIROVA ve, que es información externa,
no una propiedad del record.

Esto no invalida D19 —el mecanismo existe y publica píxeles más fríos que su fondo sin que nadie
confirme nada— pero sí obliga a decirlo con cuidado: el anillo de 2,5 a 3 km contiene artefacto
**y** señal real, y en Copahue lo que hay es señal.

---

## Cuarto tramo: la cota A93 estaba mal aplicada, por tercera vez en la sesión

Al correr la evaluación parcial con tres volcanes, Láscar quedó con **4 noches confirmadas de
39 candidatas**: el 90 % descartado como «objetos distintos». Para un volcán focal con el cráter
caliente y bien localizado, eso no tenía sentido.

La causa: comparaba el radio que reporta MIROVA, medido **desde su centro de grilla**, contra
`centroid_dist_km`, que mide **desde el cráter**. Son dos orígenes distintos, y la separación
entre ellos no es despreciable:

| volcán | separación cráter ↔ centro de grilla |
|---|---|
| Puyehue-Cordón Caulle | 7,569 km |
| Tupungatito | 4,855 km |
| Planchón-Peteroa | 2,021 km |
| Láscar | 0,833 km |
| Lastarria | 0,115 km |

Con el umbral en 0,55 km, un desplazamiento de origen de 0,83 km ya basta para declarar
«objetos distintos» a dos mediciones de la misma cosa; en Puyehue y Tupungatito el error del
método supera al umbral por un orden de magnitud.

Corregido: nuestro radio se recalcula desde el centro de grilla de MIROVA usando el centroide
del cúmulo, de modo que los dos salen del mismo punto. Láscar pasa de 4 a **26** noches
confirmadas. Los veredictos de los cinco brazos no cambiaron, pero eso es suerte, no una defensa
del error: el universo sobre el que se juzgaban era otro.

Es la **tercera** aparición de A93 en esta sesión: primero al comparar el pico con la distancia
de MIROVA en el paso 0, después al descartar coincidencias de fecha, y ahora acá. Las tres veces
el error tuvo la misma forma —restar dos radios sin preguntar desde dónde mide cada uno— y las
tres veces pasó desapercibido hasta que un número quedó absurdo. Lo que lo delató no fue una
revisión del método sino que Láscar, un volcán focal, apareciera con el 90 % de sus noches
descartadas.
