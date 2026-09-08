# Resultado — conformidad contra el caso A6 del paper (Villarrica, 24-jun-2009)

> Run 34281070800, success. Criterio de `docs/PREREGISTRO_CONFORMIDAD_A6_S136.md`, fijado antes de
> correr. La primera corrida (34280181463) quedó inutilizada por un error de instrumento propio
> —leía `nti_max`, el nombre de VIIRS, donde MODIS persiste `diag_nti_max`— corregido en #615.

## Control de validez: SUPERADO

El paper entrega un solo número, NTI ≈ −0,93 en la anomalía de la cumbre. Medido:

| pasada | `diag_nti_max` | banda [−0,97, −0,85] |
|---|---|---|
| Terra `MOD021KM.A2009175.0410` | **−0,9052** | en banda |
| Aqua `MYD021KM.A2009175.0555` | **−0,9019** | en banda |

Dos pasadas nocturnas de las 5 del día (las otras 3 son diurnas y quedan fuera del universo del
pipeline por diseño). Estamos mirando la escena del paper.

## Desenlace: CONFORME

| afirmación del paper | resultado |
|---|---|
| **(1)** detecta la anomalía de la cumbre (NTI muy por debajo de K1 = −0,80) | **2 de 2** — cúmulo a **0,73 km** y **1,02 km** del cráter |
| **(2)** el lago tibio no produce detección (el ETI lo cancela) | **0 detecciones** sobre el lago (los cúmulos quedan a 21,2 y 21,6 km) |

Y con `ENABLE_EXCLUDE_ZONES = False`: **ninguna máscara geográfica oculta el lago**. La segunda
afirmación se cumplió por el algoritmo, no por un parche.

**El núcleo de detección reproduce el caso de validación del propio autor.**

## El hallazgo: conforme, y aun así invisible para el operador

Las dos pasadas llevan **`distance_class = "far"`**, con el cúmulo primario a 0,73 y 1,02 km del
cráter. El dashboard filtra por *summit*, así que **ninguna de las dos se publicaría**.

Es la cara oculta de A46/A81, con un caso de referencia del autor detrás: la etiqueta se deriva de
`final_hotspot` y no del cúmulo, de modo que una detección crateriana correcta —la misma que el
paper llama *"easily detected"*— no llega a la vista del operador. Hasta ahora esa cara se conocía
por su tamaño (15-17 % de los records de cada mes desde feb-2025, A90); ahora hay además un caso
en que **sabemos, por el autor del algoritmo, que la detección es correcta**.

## Lo que matiza del reencuadre de esta sesión

En las dos pasadas: `triggered_test1 = False` y `diag_n_nti_path = 0`, pero el primer pase
contextual entrega **10 y 102 píxeles**.

O sea: la señal la vio el contextual, exactamente como dice el paper (*"detected after performing
the spatial filtering"*), sin participación del umbral fijo ni del Test 1 integrado. Eso **matiza
la hipótesis de «contextual débil»** que quedó planteada al cerrar el frente de K1: en MODIS, sobre
Villarrica, con NTI ≈ −0,90, el contextual funciona. Si es débil, lo es en VIIRS 375 m o en
condiciones específicas, no de forma universal.

## Límites, los declarados de antemano

- **Es MODIS, no VIIRS 375 m.** No absuelve al sensor que hoy carga el recall.
- Una sola fecha. Un caso conforme no valida el algoritmo entero; el valor es asimétrico —uno no
  conforme habría localizado un defecto.
- El paper no da μ, σ, dNTI ni dETI: el test es binario y de posición.
- El paper no dice si su imagen es nocturna; las dos que usamos lo son.

## Qué sigue

**Los ocho casos restantes del Apéndice A** (`sp426_5.txt:770-836`), que también nunca se
corrieron. Los tres negativos son los más valiosos para el frente del artefacto: Dubbi 3-jul-2013,
Tolbachik 20-nov-2012 y Stromboli 19-ene-2010, donde el algoritmo **no** debe detectar. Si
detectamos ahí, es sobre-detección estructural con referencia del autor.

Requieren coordenadas de volcanes extranjeros, que **no se deben inventar**: el paper sólo da las
altitudes (Ubinas 5.672 m, Tolbachik 3.611 m, Etna 3.330 m, Stromboli 924 m, Eyjafjallajökull
1.666 m, Erta-Ale 613 m, Dubbi 1.625 m), que sirven para verificar que la coordenada elegida es el
volcán correcto. Fuente natural: el catálogo Smithsonian GVP, que el proyecto ya usa (`gvp_id`).
