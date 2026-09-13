# S137 · La batería del Apéndice A con la banda 22: mejor que hoy, y todavía no cumple

> Runs 34745908237 (banda 22, fórmula `min`) y 34745909500 (banda 22, prosa `max`), los dos verdes,
> nueve casos cada uno. Brazos de S136 para comparar: runs 34284386094 y 34310522104. Tabla generada
> por `comparar_brazos_apendice.py` sobre los cuatro `resultado_apendice.json` (regla S91).
> Criterio fijado en S136, no se mueve: **conservar los 6 positivos Y curar los 3 negativos**.

## El resultado

| caso | volcán | el autor | B21 min (hoy) | B21 max | B22 min | B22 max |
|---|---|---|---|---|---|---|
| A1 | Bezymianny | detecta | ok | FN | ok | ok |
| A2 | Eyjafjallajökull | detecta | ok | FN | FN | FN |
| A3 | Erta Ale | detecta | ok | ok | ok | ok |
| A5 | Ubinas | detecta | ok | FN | ok | ok |
| A6 | Villarrica | detecta | ok | FN | FN | FN |
| A8 | Etna | detecta | ok | ok | ok | ok |
| A4 | Dubbi | **no** detecta | FP | ok | FP | ok |
| A7 | Tolbachik | **no** detecta | FP | ok | ok | ok |
| A9 | Stromboli | **no** detecta | FP | ok | ok | ok |
| | **positivos** | | 6/6 | 2/6 | 4/6 | 4/6 |
| | **negativos** | | 0/3 | 3/3 | 2/3 | **3/3** |

**Ningún brazo cumple.** El mejor es banda 22 con la prosa: 7 de 9, cura los tres negativos y pierde
dos positivos. Frente a hoy (6 de 9) gana tres negativos y pierde dos positivos.

Con la banda 22 sola, sin tocar la conectiva, Tolbachik y Stromboli dejan de ser falsos positivos.
Es la primera vez que un cambio **fiel al paper** cura negativos sin tocar la conectiva, y es coherente
con el probe de sigma: la sobre-detección de hoy la carga en buena parte la textura de la banda 21.

## Las dos pérdidas no son del mismo tipo

Los números por pasada salen de los cuatro JSON.

### Eyjafjallajökull, 7 de abril de 2010

| brazo | cúmulos por pasada (VRP y distancia a la cumbre) | píxeles 1er paso |
|---|---|---|
| B21 min | 0,12 a 0,52 MW, a **1,4 a 3,1 km** | 43 a 123 |
| B22 max | 2 a 59 MW, a **7,4 a 10,9 km** | 1 a 3 |

Con la banda 21 la batería lo cuenta como conforme por cúmulos chicos cerca de la cumbre, en escenas
donde el primer paso tiene entre 43 y 123 píxeles, que es el rango de ruido que midió el probe de
sigma. Con la banda 22 esos cúmulos desaparecen, y lo que queda es una anomalía fuerte (NTI de hasta
-0,27, decenas de MW) **fuera de la caja de 5 km** de la batería.

**Hipótesis, no verificada:** en esa fecha la actividad de 2010 era la erupción de flanco de
Fimmvörðuháls, que empezó el 20 de marzo y está entre Eyjafjallajökull y Mýrdalsjökull, lejos de la
coordenada de la cumbre. Si es así, el algoritmo con banda 22 **sí encuentra la anomalía real** y la
batería no la cuenta porque su ROI está centrado en la cumbre del catálogo. Y el "conforme" de hoy
estaría apoyado en ruido cerca de la cumbre, no en la erupción. El pie de figura del paper no ubica la
anomalía, y la batería guarda distancias pero no posiciones, así que hoy no se puede confirmar desde el
repo.

### Villarrica, 24 de junio de 2009

| brazo | cúmulo | píxeles 1er paso |
|---|---|---|
| B21 min | 0,12 y 0,59 MW, a 2,6 y 1,0 km | 9 y 100 |
| B22 min | una pasada sin cúmulo; otra con cúmulo en el cráter (0,8 km) de **0,0 MW** | **0 y 0** |
| B22 max | una pasada sin cúmulo; otra con cúmulo en el cráter (0,4 km) de **0,0 MW** | **0 y 0** |

El control de validez se cumple en los cuatro brazos: el NTI máximo con banda 22 es -0,914 y -0,916,
dentro de ±0,06 del -0,93 que da el paper. Es su escena.

Esto es una pérdida de detección real, y hay que decirlo sin atenuar: el pie de figura del paper dice
que la anomalía de Villarrica *"is easily detected after performing the spatial filtering (dNTI and
dETI)"*. Con la banda 22, nuestros Tests 2 y 3 **no encuentran ningún píxel**, ni siquiera con el piso
de 0,003 de la fórmula. El cúmulo que aparece en el cráter sale por otro camino y con magnitud cero.

O sea que con la banda 22 el dNTI del cráter de Villarrica queda **debajo del piso del autor**, mientras
el autor lo detecta. Algo más sigue distinto entre su dNTI y el nuestro, y no es la banda.

## Lo que esto dice del "6 de 6" de hoy

Los dos positivos que la banda 22 pierde son justamente los dos donde hoy la conformidad descansa en
escenas con 43 a 123 píxeles de primer paso, que es el nivel de ruido medido. No prueba que esos dos
"conforme" sean ruido, pero sí que **el 6 de 6 de hoy no es tan sólido como parece**: puede estar
contando detecciones que no son la anomalía que el autor vio.

## Lo que NO se afirma

- No se afirma que haya que adoptar la banda 22. No cumple el criterio.
- No se afirma la posición de la erupción de 2010. Es hipótesis.
- No se afirma que la pérdida de Villarrica sea aceptable. Es la contraria a lo que describe el paper.

## Lo que queda abierto, en orden

1. **Villarrica con banda 22.** Por qué el dNTI del cráter queda bajo 0,003 cuando el autor lo detecta.
   Candidatos del propio paper: el remuestreo a 1 km (que en el probe de sigma no bajó el ruido, pero
   puede cambiar cómo se reparte la señal de un foco sub-píxel entre píxeles) y el bow tie. Es un probe
   por etapa (A75) sobre una sola escena, barato.
2. **Eyjafjallajökull.** Guardar la posición del cúmulo, no sólo la distancia, y ubicar la anomalía de
   la figura A2. Si es de flanco, el caso mide geometría de la batería y no detección.
3. Recién con esos dos entendidos tiene sentido decidir algo sobre la banda 22.
