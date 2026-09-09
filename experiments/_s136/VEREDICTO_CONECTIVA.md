# Veredicto: NO ADOPTAR la lectura de la prosa — y ninguna de las dos lecturas es MIROVA

> Brazo de la prosa: run 34310522104 (`APENDICE_PROSA=1`). Brazo de la fórmula: run 34284386094.
> Criterio pre-registrado: un brazo sirve si y sólo si **mantiene los 6 positivos y cura los 3
> negativos**. El flag `ENABLE_TESTS_23_PROSE_BRANCH` queda **OFF**.

## El resultado

| caso | volcán | el paper | fórmula `min` | prosa `max` | fondo | 1er pase `min`→`max` |
|---|---|---|---|---|---|---|
| A1 | Bezymianny | detecta | ok | **FALLA** | 244 K | 327 → **0** |
| A2 | Eyjafjallajökull | detecta | ok | **FALLA** | 268 K | 123 → 1 |
| A3 | Erta Ale | detecta | ok | ok | 309 K | 3 → 2 |
| A5 | Ubinas | detecta | ok | **FALLA** | 268 K | 242 → **0** |
| A6 | Villarrica | detecta | ok | **FALLA** | 275 K | 100 → **0** |
| A8 | Etna | detecta | ok | ok | 273 K | 89 → 1 |
| A4 | Dubbi | **NO** detecta | FALLA | **ok** | 301 K | 35 → **0** |
| A7 | Tolbachik | **NO** detecta | FALLA | **ok** | 263 K | 166 → **0** |
| A9 | Stromboli | **NO** detecta | FALLA | **ok** | 284 K | 75 → **0** |

| | fórmula (producción) | prosa |
|---|---|---|
| positivos conformes | **6 / 6** | 2 / 6 |
| negativos conformes | 0 / 3 | **3 / 3** |

**La prosa cura el artefacto por completo y pierde cuatro positivos, entre ellos Ubinas
(NTI ≈ −0,91) y Villarrica (≈ −0,93)** — precisamente los dos que el pre-registro puso como freno
contra pasarse de estricto. Rechazado por el criterio.

## Por qué falla: no es un ajuste, es un apagón

La columna del primer pase lo dice todo: **327 → 0, 242 → 0, 166 → 0, 100 → 0, 123 → 1, 89 → 1**.
La rama de la prosa no *afina* el contextual, lo **apaga**. Cura los tres negativos por la vía
trivial de no detectar casi nada, y por eso se lleva puestas las anomalías débiles reales.

Los dos que sobreviven son Erta Ale (3 → 2) y Etna (89 → 1), y no hay un patrón limpio de fondo
térmico: Etna a 273 K sobrevive y Villarrica a 275 K no.

## Lo que esto prueba por eliminación, y es el valor real del experimento

**Ninguna de las dos lecturas del paper reproduce a MIROVA.** Con `min` sobre-detectamos en los
tres negativos; con `max` perdemos cuatro positivos. MIROVA consigue **6/6 y 3/3 al mismo tiempo**,
así que su comportamiento **no es ninguno de los dos extremos de esa conectiva**.

Eso cierra la conectiva como frente: el problema no está ahí. La contradicción entre la fórmula y
la prosa del paper es real y queda documentada, pero **resolverla en cualquiera de los dos sentidos
no nos acerca a MIROVA**. Y de paso queda respondida, con datos, la pregunta que S110 dejó abierta
sobre qué rama gobierna: la gobierna el piso, y forzar la otra no arregla nada.

## Dónde queda el frente ahora

Si el algoritmo de detección no puede dar 6/6 y 3/3 con ninguna de las dos conectivas, entonces
**MIROVA descarta después de detectar**. Y eso está documentado verbatim, es de MIROVA, y no lo
tenemos implementado — está anotado en `MIROVA_DIVERGENCES.md` (D14) desde S128:

> *"...and filtered in terms of **distance and/or intensity** of the thermal anomaly to minimize
> the false alerts and the double counting (coming from different detectors acquiring at the same
> time) thus resulting in 9712 data points (**ca. 12 %**)."*  — Laiolo 2026, Bull. Volcanol.

MIROVA se queda con el **12 %** de sus imágenes: filtra por distancia y por **intensidad**, y
descarta el doble conteo entre detectores. Nuestro criterio de conformidad es «publica un cúmulo
con VRP > 0 dentro del ROI», o sea mide **reporte**. Si MIROVA detecta en Stromboli y no lo
publica por intensidad, nuestros tres falsos positivos son de reporte y no de detección — que es
exactamente el límite que el pre-registro declaró de antemano.

Es coherente con lo demás: en los tres negativos las magnitudes son 1,5 · 5,0 y 22,1 MW, y el
mismo grupo escribe que considera los valores bajo 0,1 MW «probablemente nube o mala geometría».
El siguiente candidato a medir es ese filtro de intensidad y de doble conteo, no otro umbral de
detección.

## Nota de método: dos errores propios en este tramo

1. **Mi primera lectura de este resultado fue equivocada.** Comparé los brazos y me dieron
   idénticos, contradiciendo el propio reporte del run. La causa: el artefacto trae **dos** JSON,
   porque el runner hace checkout del repo —que ya tiene `out_apendice/` commiteado del brazo
   anterior— y el brazo de la prosa escribe en `out_apendice_prosa/`. Mi `glob` tomó el primero.
   Décimo error de instrumento de la sesión, y del mismo tipo que los otros nueve: **el archivo
   que leí no era el que creía**. Lo delató que los conteos del primer pase salieran idénticos
   dígito por dígito, que es imposible si el umbral cambió.
2. **Escribir la salida de un brazo en un directorio versionado invita a ese error.** Vale
   recordarlo si se agregan más brazos: la salida de un experimento no debería compartir ruta con
   la de otro, ni vivir donde el checkout la repone.
