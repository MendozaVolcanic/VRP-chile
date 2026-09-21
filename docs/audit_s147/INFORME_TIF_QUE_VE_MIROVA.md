# Qué hay en la imagen de MIROVA donde la réplica publica y MIROVA calla (S147)

> **Encargo**: agente con contexto limpio y preámbulo anti-fabricación entero, sobre la copia
> local de `mirova-tif-archive` (sin `pull` ni `fetch`). Tenía que separar dos explicaciones
> rivales: (A) MIROVA ve el mismo píxel tibio pero su umbral es más exigente, o (B) en la imagen
> de MIROVA ese píxel no existe porque su remuestreo suaviza el ruido.
>
> **Ventana de todo lo que sigue: 2026-05-09 a 2026-05-20**, VIIRS 375 m, banda I04. Es anterior
> a #535 y #571, así que describe mayo: no se verificó que el mismo patrón valga hoy (A104).
> Población: cúmulos contextuales (`final_hotspot_source = "ctx_cluster"`) dentro del radio
> interno, con el TIF de MIROVA de **esa misma pasada** (delta 0 minutos). n = 43 donde MIROVA
> dijo RUTINA con VRP 0, n = 52 de control donde alertó.

## Respuesta corta

**Ni A ni B como estaban planteadas.** Las dos imágenes **son la misma** (refuta B), y el píxel
del residual **no está caliente en ninguna de las dos**. MIROVA además publica alertas de 0,03 MW,
por debajo de la mediana del residual, así que tampoco es un corte en megawatts (refuta la versión
ingenua de A). **Lo que sobra lo fabrica el criterio contextual de la réplica.**

## Hallazgos

### H1 (5). Las dos imágenes coinciden, y en ninguna hay calor donde publicamos
Inversión de Planck sobre el valor del TIF en la celda de nuestro píxel, contra el `bt_k` del
record (control de ida y vuelta: 274,1 K, 0,13069, 274,1 K).

| | donde MIROVA no vio nada (n = 40) | donde MIROVA alertó (n = 52) |
|---|---|---|
| BT de MIROVA menos BT nuestra, mediana | **+0,17 K** | −2,02 K |
| exceso del píxel sobre su fondo, en nuestro dato | **+0,31 K** (p10 −4,42, p90 +3,17) | +4,88 K |
| exceso en la misma celda, en la imagen de MIROVA | +1,08 K | +3,80 K |
| el píxel está **más frío** que nuestro propio fondo | **42 %** | 4 % |
| el píxel excede el fondo en más de 3 K | 12 % | 75 % |

No hay dos imágenes distintas: hay una imagen sin nada, leída dos veces. Y donde MIROVA sí alertó
el instrumento ve el calor, así que el control funciona.

### H2 (5). MIROVA sí remuestrea, a una grilla fija que no se mueve entre pasadas
Sobre los 637 TIF de VIIRS 375 únicos en disco: los 11 volcanes tienen grilla **idéntica en todas
sus pasadas**, 134 × 134 celdas de ~383 m, caja de ~51 km, **EPSG:4326** en toda la ventana
(ningún UTM). VIIRS 750: 67 × 67 de ~760 m. MODIS: 51 × 51 de ~1.010 m. Software del GeoTIFF:
MATLAB R2024b, Mapping Toolbox.

### H3 (5). El remuestreo es interpolado y suave, no vecino más cercano, y aun así conserva picos de una celda
Sobre 227 TIF con cenital conocido: **cero** pares de celdas contiguas exactamente iguales (no hay
bloques repetidos), autocorrelación a una celda 0,968, y la rugosidad **no aumenta** hacia el
borde (baja 13 %). Pero el máximo global del exceso de una celda sobre sus vecinas llega a 34,9
desviaciones: **un píxel caliente genuino sobrevive como pico aislado**. El suavizado del
remuestreo no puede ser lo que borra nuestro píxel, porque no borra los reales.

Parche de control, Isluga 2026-05-09 05:36 UTC (MIROVA alertó, 0,31 MW): una celda a 0,1475 sobre
un fondo de 0,070, con derrame de 0,1248 en la vecina. Parche del residual, Copahue 2026-05-13
06:06 UTC (MIROVA VRP 0; nosotros 0,051 MW a 2,99 km): un gradiente liso, sin nada.

### H4 (5). La pregunta central, con su nulo medido
Percentil del valor de nuestra celda dentro de un disco de 5 km de la misma imagen de MIROVA.
**Nulo medido** con 120 celdas sorteadas a más de 6 km: 0,500 y 0,503.

| | percentil mediano | z robusto | es el máximo del disco |
|---|---|---|---|
| donde MIROVA no vio nada (n = 43) | **0,638** [0,588 a 0,710] | +0,39 | 2,3 % (1 de 43) |
| donde MIROVA alertó (n = 52) | **0,872** [0,813 a 0,935] | +1,58 | 11,5 % |
| donde MIROVA marcó falso positivo (n = 8) | 0,942 | +2,19 | 25,0 % |

AUC alerta contra residual: 0,75 [0,644 a 0,846]. El sitio del residual es **levemente** más
tibio que su entorno (0,638 contra un nulo de 0,500, con intervalo que no toca 0,50), pero no es
un píxel que sobresalga.

### H5 (4). No es un corte de magnitud: lo que separa es la geometría
| | residual (n = 43) | alertas (n = 52) |
|---|---|---|
| cúmulo de un píxel | 88 % | 60 % |
| magnitud mediana | 0,060 MW | 0,129 MW |
| distancia al cráter, mediana | **1,30 km** | **0,33 km** |
| cenital mediano | **59,4°** (60 % sobre 52°) | **31,1°** (21 % sobre 52°) |

MIROVA publica alertas de 0,03, 0,05 y 0,06 MW en la misma ventana y los mismos volcanes en que
calla frente a nuestros 0,060 MW medianos.

### H6 (3). El exceso persiste en otro gránulo de la misma noche
Control A109 contra la maldición del ganador: el percentil pasa de 0,636 (mismo gránulo) a 0,592
(otro gránulo, a 51 minutos). No lo fabrica el ruido de nuestro detector: es una tibieza
persistente del terreno. **Reserva del agente**: el mismo control colapsa a 0,570 en las alertas,
así que no es un control limpio (A110) y no sirve como línea base de sitio.

### H7 (4). No hay hueco de bow-tie en ninguno de los 103 casos
Los TIF tienen huecos, pero su fracción no crece con el cenital y en 0 de 103 casos nuestro píxel
cae en uno o a menos de 3 celdas. Descartado "MIROVA no tiene dato ahí".

### H8 (3). Los KMZ no codifican radios, ni grilla, ni centro: sólo una caja
Abiertos los 1.965 KMZ: un `GroundOverlay` con `LatLonBox` y un PNG de visualización. Ni un
`Placemark`, ni un `Polygon`. **El `inner_radius_km` por volcán de `volcanoes.yaml` no pudo salir
de estos KMZ**; si salió de KML de MIROVA, fue de otros archivos.

### H9 (3). El centro de la grilla de MIROVA está lejos del cráter en tres volcanes
| volcán | distancia del centro del TIF al cráter de la réplica |
|---|---|
| Puyehue Cordón Caulle | **7,58 km** |
| Tupungatito | **4,78 km** |
| Planchón Peteroa | **2,00 km** |
| Villarrica | 0,71 km |
| Chaitén | 0,61 km |

La caja es una sola por volcán y su centro es el ancla de MIROVA. Es la referencia correcta para
entender contra qué punto mide MIROVA sus distancias (`Distancia_km` no trae acimut), y **dónde
cae su caja de 5 × 5 km**. Toca D15, D17 y D18.

### H10 (3). Un cuarto del exceso aparente no es comparable
De 242 cúmulos contextuales dentro del radio interno en la ventana, **65 (27 %) no tienen fila en
la referencia ni TIF de esa pasada**. No son "publicamos donde MIROVA calló": son pasadas donde no
sabemos qué hizo MIROVA. Un conteo que los incluya está inflado.

### H11 (2). La hora del nombre del archivo
De 1.070 filas de VIIRS 375, 678 llevan la hora de adquisición en el nombre, 162 el
`Last-Modified` y 230 ninguna de las dos. La diferencia mediana entre publicación y adquisición es
de **8,3 horas**. Toda la medición central se hizo con delta 0 minutos contra nuestro record.

## Lo que el agente no pudo medir

- **El NTI de MIROVA**: el archivo sólo trae la banda MIR. Sin la térmica no se puede calcular el
  NTI ni el ETI de MIROVA. Todo lo dicho sobre "la imagen de MIROVA" es sobre su campo MIR.
- **La dirección de las detecciones de MIROVA**: la referencia no trae acimut (A93, A107).
- **La estratificación por volcán**: 7 de los 10 volcanes del residual tienen 4 casos o menos, y
  el estrato está dominado por Chaitén (10) y Puyehue Cordón Caulle (8). SOSPECHA por volcán.
- **Si el patrón vale en el régimen de hoy**: mayo es anterior a #535 y #571.

## Lectura del agente

Es el **criterio contextual** el que declara anomalía a un píxel que está a +0,31 K de su fondo.
El eje que separa el residual de las alertas de MIROVA es la **geometría** (distancia al cráter y
cenital), lo que apunta al gradiente del terreno y a la degradación del muestreo en el borde del
barrido como lo que alimenta el test contextual. Coherente con A69 y A80, ahora con una medición
externa que antes no existía.
