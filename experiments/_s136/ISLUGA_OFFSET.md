# S136 — el offset de Isluga, medido sobre los TIF de MIROVA

> Responde la pregunta de Nicolás: «las coordenadas del cráter, ¿no deberíamos usar las mismas que
> ellos?». Respuesta corta: **no existe una coordenada de cráter de MIROVA que copiar**, y la que
> tenemos de ellos es otra cosa. La decisión sigue siendo nuestra, y en Isluga hay algo que
> corregir.

## Por qué la coordenada de MIROVA no sirve para esto

Hay tres puntos distintos en juego y sólo uno es el cráter:

| campo | qué es | quién lo usa |
|---|---|---|
| `vent_lat/lon` | el cráter morfológico | `get_detection_anchor` — **ancla de detección, clustering y distancia**, en el perfil operacional |
| `mirova_center_lat/lon` | el centro de la grilla UTM de 51×51 km de MIROVA, sacado de sus KMZ | encuadre / cotejo; `get_grid_center` **no tiene llamador en producción** (D17) |
| `lat/lon` | el centroide del volcán (GVP) | último recurso |

`mirova_center` es el **encuadre**, no su idea del cráter. La separación contra el cráter va de
0,115 km en Lastarria a **7,569 km en Puyehue**: si fuera dónde MIROVA cree que está el foco, en
Puyehue estaría errándole por 7,5 km, y no le erra — reporta el lacolito donde está.

Y MIROVA no publica coordenada: publica `Distancia_km`, cuantizada a su celda de grilla (D15). Su
«0,0 km» significa «en la misma celda que su referencia», no «en el cráter».

Anclar la detección al `mirova_center` además ya se probó y **se revirtió a propósito**: S65 lo
sacó de Tupungatito, S66 midió 56 % de mejora, S80 lo revirtió sin darse cuenta al regenerar la
config desde el KMZ (de ahí salió la regla A63), y S98 escribió `get_detection_anchor` para que el
cráter gane de forma uniforme en los 11.

**Conclusión: la coordenada del cráter es nuestra decisión, en los dos perfiles.** Y en Isluga
está escrita con **2 decimales** (−19,15 / −68,83) — el único Tier A así — lo que sólo por
redondeo vale ±0,55 km.

## Lo que dicen los TIF de MIROVA

54 TIF VIIRS375 de Isluga en `../mirova-tif-archive`, del 9 al 20 de mayo de 2026.

**Primer intento, y por qué estaba mal.** Buscar el máximo del TIF completo dio 4 casos, con el
máximo a **20-31 km** del cráter: son máximos de **escena** (el TIF cubre ~50 km), no el foco del
volcán. A61 ya lo advierte — hay que mirar la radiancia **local alrededor del cráter**. Corregido:
la búsqueda se restringe al `inner_radius_km` = 5 km.

**Resultado (9 pasadas con un máximo local que destaca del fondo):**

| | |
|---|---|
| componente N-S | **−0,609 km** (al sur) |
| componente E-O | **−2,086 km** (al oeste) |
| al norte del vent | **0 de 9** |
| al este del vent | **0 de 9** |

**Las 9 caen al suroeste, sin una sola excepción.** Y esa dirección coincide con las otras dos
fuentes independientes: la auditoría S134 encontró el foco 0,86 km al SO en el 100 % de los pares,
y el propio `mirova_center` está 0,37 km al SO. Tres caminos distintos apuntan al mismo cuadrante.

## Lo que estos datos NO permiten decir

- **La magnitud del offset no es medible acá.** El realce mediano del foco local es 1,58× — el
  campo de MIROVA en Isluga es casi plano, coherente con un volcán de régimen Muy Bajo. El pico de
  un campo plano es ruido, que es justo por lo que S106 descartó el `nti_peak` como ancla (A84).
- El **p75 de la separación es 5,00 km, exactamente el borde de la ventana de búsqueda**: en
  varios casos el máximo local está pegado al recorte, así que ese número es artefacto del método,
  no del volcán. Por eso la mediana de 3,63 km **no debe citarse como el offset**.
- El archivo cubre 12 días de mayo, no la serie.
- Y sobre todo: esto ubica **dónde MIROVA ve el calor**, no el cráter morfológico.

## Recomendación

La dirección está corroborada por tres fuentes; la magnitud, por ninguna. Lo que corresponde es
**refinar `vent_lat/lon` de Isluga con imagen o DEM** — es un cambio en `volcanoes.yaml`, barato, y
corrige toda distancia publicada de un Tier A. Pero la coordenada la fija el geólogo mirando el
cráter, no un máximo de radiancia de 1,58×.

Si se refina, conviene un test de regresión que fije la intención, como el que A63 pide desde que
una consolidación revirtió el fix de Tupungatito sin que nadie se enterara.
