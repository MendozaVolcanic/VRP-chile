# S131 · Eje ground truth exógeno — evidencia por pasada

> **Qué es esto**: nuestras detecciones comparadas **pasada por pasada** contra las dos
> evidencias externas que existen — el archivo de GeoTIFF/KMZ que MIROVA publica
> (`../mirova-tif-archive`, 1.960 escenas del 2026-05-08 al 05-20) y el CSV de MIROVA
> (CONS ∪ OCR, 2026 completo).
>
> **Read-only.** Ningún archivo del repo ni del archivo de TIF fue modificado, ningún
> comando de git. Todos los números salen de un script que los persiste; ninguno
> transcrito a mano (S91). Scripts y JSON en
> `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/experiments/_s131_audit/ground_truth/`.

---

## Resultado primero

1. **El GeoTIFF público no puede adjudicar posición.** El control obligatorio lo refuta
   con un margen que no admite discusión: contra la `Distancia_km` que MIROVA misma
   publica, el mejor estimador que se puede sacar de la escena tiene error mediano de
   **4,80 km** y correlación de Spearman **0,151** (n=100 alertas con escena de la misma
   pasada). En MODIS y VIIRS750 el estimador **pierde contra el nulo trivial** —contra
   decir siempre «el punto está en el cráter»— en 86 % y 88 % de las pasadas. Esto
   **confirma y endurece el guard de AUDIT_S128 §3**, que se apoyaba en un control más
   débil. De 16 celdas volcán×sensor, **2** pasan el criterio pre-registrado.

2. **Y sin embargo la escena de MIROVA sí dice algo, y es fuerte.** El máximo de
   infrarrojo medio de su escena es **bimodal**: o cae sobre el edificio, o se va al borde
   del recuadro. Cae sobre el edificio en **23 %** de las pasadas VIIRS375, **6,6 %** de
   las VIIRS750 y **0,8 %** de las MODIS (2 de 236). Cuando cae sobre el edificio en
   VIIRS375, **nuestro clúster está a 228 m de él —0,61 píxeles— y el 92,7 % dentro de
   dos píxeles** (n=41). Es la primera confirmación exógena de que nuestra posición a
   375 m es correcta.

3. **La cara oscura de lo mismo: a 1 km el infrarrojo medio absoluto no ve el volcán, y
   nuestro `final_hotspot` de MODIS lo demuestra.** En 236 pasadas MODIS con detección,
   nuestro `final_hotspot` está a **21,43 km** del cráter (mediana) y el máximo de la
   escena de MIROVA a **20,76 km** — los dos perdidos en el gradiente topográfico, y a
   **24,90 km uno del otro** (Spearman 0,023: ni siquiera coinciden entre sí). Mientras
   tanto nuestro `primary_cluster` está a **2,11 km** del cráter. Como `distance_class` se
   deriva del `final_hotspot` (`pipeline/process_modis.py:1261`), **el 87 % de las
   detecciones MODIS cuyo clúster está a menos de 2 km del cráter quedan etiquetadas
   `far`** (1.073 de 1.233) y desaparecen del dashboard. Es A46/A81 con evidencia externa
   y con el denominador más filoso hasta ahora.

4. **MIROVA mide su `Distancia_km` desde el centro de su grilla, no desde el cráter.**
   Sobre 1.815 pasadas TP: anclando en `mirova_center` el error mediano es **0,48 km**
   (76,3 % dentro de 1 km, ρ=0,487); anclando en el `vent` es **1,02 km** con ρ=**−0,073**
   —o sea, ninguna relación—. Cualquier auditoría que compare distancias tiene que
   anclar en `mirova_center`. Explica de una vez PCC (7,50 km de error con `vent`, 0,44
   con `mirova_center`), Tupungatito (4,78 → 0,33) y PP (1,52 → 0,27).

5. **El recall contra MIROVA, sobre pasadas comunes nocturnas de 2026, es alto**: MODIS
   **1,000** (65/65), VIIRS375 **0,961** (1.490/1.550), VIIRS750 **0,836** (260/311). Los
   **111 FN** son señal sub-umbral genuina: VRP de MIROVA mediano **0,19 MW**, el 90,1 %
   bajo 0,5 MW, `nti_max` mediano −0,927 con el 78,4 % en el piso, y el 42,3 % con ángulo
   de vista >45°. **Ninguno es un artefacto nuestro ni un granule faltante.**

6. **La sobre-detección es real y está concentrada en MODIS.** En pasadas donde MIROVA
   publica RUTINA, nosotros entregamos VRP>0 en el **99,6 %** de las MODIS, 64,5 % de las
   VIIRS375 y 23,8 % de las VIIRS750. Pero al cortar en 0,1 MW la VIIRS375 se cae a
   **4,4 %** (son clústeres de 0,047 MW) y MODIS se queda en **96,2 %**, con VRP mediano
   0,852 MW. Sobre 2026 completo, **5.163 de 5.193 records MODIS (99,4 %) llevan un
   `primary_cluster` con VRP>0**.

7. **`half_km = 25,5` está bien; el `LatLonBox` del KMZ es un recorte de display.** Medido
   sobre los GeoTIFF —que son la escena real— el semiancho de MIROVA es 25,29–25,65 km en
   los tres sensores (desvío ≤0,21 km contra 25,5). Los 15 KMZ del repo dan 23,99–25,80 km,
   hasta **1,51 km menos** por lado. Cierra el pendiente #6 de AUDIT_S128.

---

## Control de instrumento (obligatorio, antes de cualquier veredicto)

**El fenómeno primero.** El GeoTIFF que MIROVA publica trae **una sola banda**: el
infrarrojo medio (B21 / M13 / I04). No trae el térmico, así que el NTI —que es el índice
con que MIROVA detecta— no se puede reconstruir. Lo único medible es radiancia MIR
**absoluta**, y en un volcán de altura con cumbre nevada y valle tibio abajo, ese campo
está dominado por el gradiente de temperatura con la altitud, no por el foco volcánico
(A69). O sea: el instrumento tiene exactamente el defecto que vine a buscar.

**La prueba.** Para cada pasada donde el CSV de MIROVA declara ALERTA con su
`Distancia_km`, extraigo el punto caliente de la escena de MIROVA y pregunto si cae a esa
distancia. Cuatro estimadores × tres anclas.

| estimador · ancla | n | error mediano | ≤1 km | ρ Spearman |
|---|---|---|---|---|
| **realce 3×3 · mirova_center** | 100 | **4,80 km** | 0,40 | 0,151 |
| realce 3×3 · gvp | 100 | 5,22 km | 0,33 | 0,107 |
| realce 5×5 · mirova_center | 100 | 7,37 km | 0,35 | 0,111 |
| realce 9×9 · mirova_center | 100 | 8,85 km | 0,26 | 0,027 |
| **máximo crudo · mirova_center** | 100 | **19,65 km** | 0,05 | 0,210 |

**El control que decide** es contra el nulo trivial: decir siempre «el punto caliente está
en el cráter, distancia 0».

| sensor | n | error del estimador | error del nulo trivial | el estimador gana en |
|---|---|---|---|---|
| MODIS | 7 | 12,72 km | **1,00 km** | 14 % |
| VIIRS375 | 77 | 1,06 km | 1,55 km | **51 %** |
| VIIRS750 | 16 | 12,22 km | **1,50 km** | 12 % |

En MODIS y VIIRS750 el instrumento es **peor que no medir nada**. En VIIRS375 empata a
cara o sello. **Veredicto: refutado como árbitro de posición.**

**Criterio pre-registrado por celda** (n≥10, error mediano ≤1,0 km y ganarle al nulo en
>60 %): pasan **2 de 16** — `Isluga|VIIRS375` (n=11) y `PuyehueCordonCaulle|VIIRS375`
(n=15). Y `PlanchonPeteroa|VIIRS375` y `Lascar|VIIRS375` quedan fuera sólo por la tercera
condición (ganan al nulo en 55 %), que es justamente la que evita aprobar un volcán cuyas
alertas están todas a distancia ~0.

**Intento de rescate, y fracaso honesto.** Si el máximo es bimodal, tal vez la fuerza del
realce en el máximo (z robusto con MAD) separe los dos modos. Se ajustó el umbral en
PCC+Isluga (n=26) y se validó en los otros nueve volcanes (n=60): la tasa de acierto en
holdout se queda en **33–35 % para cualquier umbral entre z=3 y z=12**. **No separa.**

> **Consecuencia metodológica**: el eje espacial de esta auditoría **no tiene árbitro
> externo** salvo en dos celdas. Todo lo que sigue sobre posición se apoya en (a) el
> subconjunto condicional del punto 2, declarado como favorable, y (b) el cráter, que es
> una coordenada que nadie discute.

---

## M1 · Cobertura del archivo TIF

**Ventana del archivo: 2026-05-08 a 2026-05-20 (11,5 días).** No hay más; el prompt pedía
«2026» y el archivo exógeno son once días. Todo lo que use TIF vive en esa ventana.

- 2.684 filas de `index.csv` → **1.960 escenas únicas** tras deduplicar por md5 y por
  (volcán, sensor, adquisición).
- **1.556** tienen `acquisition_utc` real; las otras 404 llevan el timestamp derivado del
  `Last-Modified` (filas legacy previas al fix del scraper) y **no emparejan con nada**:
  su |Δt| mediano al vecino más cercano es de 122–263 min. Quedan excluidas.
- **Tolerancia de emparejamiento: ±5 min**, y la elección no cambia nada. La distribución
  de |Δt| es **bimodal**: 0–5 min (mediana exacta 0,0) o >60 min. No hay masa intermedia.

| | MODIS | VIIRS375 | VIIRS750 | total |
|---|---|---|---|---|
| escenas de MIROVA con hora de adquisición | 460 | 475 | 621 | 1.556 |
| records nuestros en la ventana | 353 | 717 | 713 | 1.783 |
| **pares (misma pasada)** | **236** | **225** | **261** | **722** |

Por celda volcán×sensor los pares van de **17 a 29** — suficiente para describir, corto
para afirmar.

**Las escenas de MIROVA sin par no son detecciones que perdimos.** Están concentradas en
las horas **12–14 y 17–21 UTC**, que son las pasadas diurnas: MODIS 12–14 y 19–21,
VIIRS 17–19. Los **1.783 de 1.783** records nuestros de la ventana tienen cenit solar >90°
— el pipeline es night-only por diseño (contaminación solar del MIR). Del otro lado, los
1.061 records nuestros sin escena son pasadas nocturnas para las que MIROVA no republicó
su TIF; el archivo captura por cambio de `Last-Modified` y no todas las adquisiciones
generan uno.

---

## M2 · Eje espacial

### A. Con respaldo exógeno — el acuerdo condicional

El modo del máximo de la escena de MIROVA se puede leer **sin mirar nuestro dato**: si su
máximo de realce está a ≤2 km del cráter, esa pasada es una en que la escena de ellos ve
el volcán. Es un subconjunto favorable —son las pasadas de señal más fuerte— y hay que
decirlo.

| sensor | modo | n | nuestro clúster al máximo de MIROVA | en píxeles | ≤2 píxeles |
|---|---|---|---|---|---|
| **VIIRS375** | **escena sobre el volcán** | **41** | **228 m** | **0,61** | **92,7 %** |
| VIIRS375 | escena al borde | 137 | 16.276 m | 43,4 | 0 % |
| VIIRS750 | escena sobre el volcán | 4 | 423 m | 0,56 | 100 % |
| VIIRS750 | escena al borde | 57 | 17.089 m | 22,8 | 1,8 % |
| MODIS | escena sobre el volcán | **2** | 2.432 m | 2,43 | 0 % |
| MODIS | escena al borde | 234 | 20.811 m | 20,8 | 0 % |

Fracción de pasadas en que la escena de MIROVA tiene su máximo sobre el volcán: **MODIS
0,8 % · VIIRS750 6,6 % · VIIRS375 23,0 %**.

Por volcán, en el modo bueno de VIIRS375 (n≥5): Tupungatito 77 m (0,20 px, n=5) · Isluga
98 m (0,26 px, n=7) · PP 154 m (0,41 px, n=7) · Láscar 177 m (0,47 px, n=7) · PCC 464 m
(1,24 px, n=10).

### B. El `final_hotspot` de MODIS contra la escena de MIROVA

| sensor | n | `final_hotspot` al cráter | `primary_cluster` al cráter | máximo de MIROVA al cráter | fh al máximo de MIROVA |
|---|---|---|---|---|---|
| **MODIS** | 236 | **21,43 km** | **2,11 km** | 20,76 km | **24,90 km** |
| VIIRS750 | 61 | 0,36 km | 1,32 km | 17,44 km | 17,23 km |
| VIIRS375 | 178 | 0,00 km | 2,66 km | 16,62 km | 16,61 km |

Correlación de Spearman entre «cuán lejos está nuestro `final_hotspot`» y «cuán lejos está
el máximo de MIROVA», en MODIS: **0,023**. Los dos están lejos y en lugares distintos: el
máximo de MIR absoluto a 1 km no es un rasgo estable del terreno, es el píxel más tibio de
un campo tibio ancho, y cuál gana es ruido.

`final_hotspot_source` en esas 236 pasadas: `eruption` 231, `test1` 3, `cluster_rescue` 2.
`distance_class`: **far 211, summit 25**.

### C. El sesgo direccional de nuestras detecciones (2026 completo, sin instrumento externo)

Offset **mediano** del `primary_cluster` respecto del cráter (A70: mediana, y componentes
norte/este, nunca la media de la distancia). Sólo celdas con n≥15; extracto de las de
mayor offset.

| volcán · sensor | n | offset mediano | rumbo | cuadrante dominante |
|---|---|---|---|---|
| Copahue · VIIRS375 | 746 | **1.952 m** | 181° | **S 51 %** |
| Llaima · VIIRS375 | 711 | **1.927 m** | 9° | **N 52 %** |
| Lastarria · VIIRS375 | 701 | **1.824 m** | 312° | **N 61 %** |
| Villarrica · VIIRS375 | 849 | **1.404 m** | 283° | O 46 % |
| Lastarria · VIIRS750 | 285 | 1.427 m | 328° | N 57 % |
| Isluga · VIIRS375 | 708 | 834 m | 218° | S 60 % |
| Tupungatito · MODIS | 454 | 764 m | 308° | N 31 % / O 35 % |
| NdC · VIIRS750 | 218 | 523 m | 48° | E 35 % |
| Láscar · VIIRS375 | 705 | **104 m** | 289° | reparto parejo |
| PCC · VIIRS375 | 805 | **99 m** | 18° | reparto parejo |

**El sesgo direccional persiste en 2026, después de S102–S104, y no es «al norte».** Es al
sur en Copahue e Isluga, al norte en Llaima y Lastarria, al oeste en Villarrica y PP. Eso
**no refuta A69, refuta su enunciado corto**: el mecanismo es el terreno tibio de baja
altitud, y ese terreno está en una dirección distinta en cada volcán. La formulación
«nevados corridos al N» de S104 describía los casos que S104 miró, no una regla.

Descarta que sea una coordenada de cráter mal puesta: si lo fuera, los tres sensores
mostrarían el mismo offset. En Copahue son 295 m a 242° (MODIS), 1.952 m a 181° (VIIRS375)
y 623 m a 174° (VIIRS750) — depende del sensor, o sea es de la detección.

Los dos volcanes **sin** sesgo (Láscar y PCC, ~100 m) son justamente los de anomalía
fuerte y persistente: donde hay señal de verdad, la señal manda sobre la topografía.

---

## M4 · Cruce contra el CSV de MIROVA, pasada a pasada

**Ventana 2026-01-01 a 2026-09-02.** 36.111 filas del CSV (CONS ∪ OCR, alias completos),
25.702 records nuestros, **16.568 pasadas comunes** (±6 min), de las cuales **14.146
nocturnas** — el universo de todo lo que sigue. Quedan fuera 19.543 filas del CSV sin
record nuestro y 9.134 records nuestros sin fila del CSV; compararlos sería llamar «falta
de detección» a un granule que el otro lado no procesó.

Se excluyen además **54 alertas diurnas de MIROVA** (todas MODIS): A76, reflexión solar;
perderlas es hacer las cosas bien.

### (a) Las dos partes coinciden — TP

| sensor | pasadas | TP | FN | **recall** | ratio de magnitud (nuestro / MIROVA) |
|---|---|---|---|---|---|
| MODIS | 2.489 | 65 | 0 | **1,000** | **1,016** (p25 0,58 · p75 1,90) |
| VIIRS375 | 5.995 | 1.490 | 60 | **0,961** | **0,600** (p25 0,39 · p75 0,87) |
| VIIRS750 | 5.662 | 260 | 51 | **0,836** | **0,581** (p25 0,41 · p75 0,88) |

Recall por celda con ≥15 alertas: Chaitén·V375 1,000 · Láscar·MODIS 1,000 ·
Villarrica·V375 1,000 · PP·V375 0,993 · Isluga·V375 0,983 · Láscar·V375 0,969 ·
PCC·V375 0,969 · Tupungatito·V375 0,938 · Láscar·V750 0,936 · Lastarria·V375 0,921 ·
PCC·V750 0,842 · **Isluga·V750 0,700**.

**El ratio de magnitud de VIIRS (0,58–0,60) está fuera de la banda de paridad [0,7–1,4]**
en las dos bandas, sobre n=1.490 y n=260. Es el mismo sub-reporte de factor ~1,7 que S125
y S128 aislaron; este cruce lo reconfirma con el denominador por pasada. MODIS, en las
pocas pasadas donde MIROVA publica, está en paridad (1,016).

**Desde dónde mide MIROVA su distancia** (n=1.815 TP con `Distancia_km`):

| ancla | error mediano | ≤1 km | ρ Spearman |
|---|---|---|---|
| **`mirova_center`** | **0,48 km** | **0,763** | **0,487** |
| `volcano lat/lon` (GVP) | 0,71 km | 0,688 | 0,421 |
| `vent` (cráter) | 1,02 km | 0,492 | **−0,073** |

Por volcán (n≥15), error con `mirova_center` vs con `vent`: PCC **0,44 vs 7,50** ·
Tupungatito **0,33 vs 4,78** · PP **0,27 vs 1,52** · Láscar 0,66 vs 1,05 · Villarrica 0,35
vs 0,69 (acá gana GVP con 0,12) · Isluga 0,32 vs 0,29 (empate) · Chaitén 0,24 vs 0,25 ·
Lastarria 0,90 vs 0,92.

### (b) MIROVA alerta y nosotros no — los 111 FN

| | |
|---|---|
| n | **111** de 1.926 alertas nocturnas en pasadas comunes (**5,76 %**) |
| por sensor | VIIRS375 **60** · VIIRS750 **51** · MODIS **0** |
| por volcán | Láscar 23 · Tupungatito 23 · Lastarria 19 · Isluga 17 · PCC 14 · PP 7 · NdC 6 · Villarrica 2 |
| VRP de MIROVA | mediana **0,19 MW**, p90 0,49 MW, **90,1 % bajo 0,5 MW** |
| `nti_max` nuestro | mediana **−0,927**, **78,4 % en el piso** (<−0,9) |
| ángulo de vista | mediana **40,8°**, **42,3 % sobre 45°** |
| fuente | CONS 85 · OCR 26 |

**La pasada existe en nuestro JSON en los 111 casos** —por construcción, el cruce es sobre
pasadas comunes—, así que no falta ningún granule. Lo que falta es señal: el NTI está en el
piso, la magnitud de referencia es sub-umbral y casi la mitad son de mala geometría de
vista. Es el régimen que el proyecto ya declaró aceptable (FN sub-píxel <0,5 MW).

### (c) Nosotros detectamos y MIROVA no publica — 6.335

| sensor | pasadas sin alerta de MIROVA | VRP>0 | VRP>0,1 MW | VRP>0,5 MW | VRP mediano de los positivos |
|---|---|---|---|---|---|
| **MODIS** | 2.419 | **99,6 %** | **96,2 %** | **70,4 %** | **0,852 MW** |
| VIIRS375 | 4.122 | 64,5 % | **4,4 %** | 0,0 % | 0,047 MW |
| VIIRS750 | 5.334 | 23,8 % | 18,8 % | 7,8 % | 0,306 MW |

**Dónde caen** (n=6.335): el **94,9 %** tiene el clúster dentro del `inner_radius`,
mediana **2,44 km** del cráter, 40,8 % a menos de 2 km, y sólo **8,9 % a más de 5 km**.

| sensor | ≤2 km (edificio) | 2–5 km (flanco) | 5–10 km | >10 km |
|---|---|---|---|---|
| MODIS | 1.233 | 935 | 148 | 94 |
| VIIRS375 | 500 | 2.070 | 45 | 42 |
| VIIRS750 | 850 | 182 | 64 | 172 |

**Los 565 casos a más de 5 km (8,9 %) no son un rasgo geotérmico**: en los once volcanes están
repartidos en los **cuatro cuadrantes** a 6–24 km, que es la firma del ruido, no la de un
lago o un campo fumarólico (que estaría en un rumbo fijo). No pude reproducir la
clasificación física de S86 al nivel de rasgo nombrado —no existe un gazetteer en el
repo— y lo digo: la atribución «lago Conguillío», «Lazufre», «salar» **no está verificada
en esta auditoría**. Lo que sí está medido es que la masa (91,1 %) está sobre el edificio.

**El resultado que importa es MODIS**: 2.410 pasadas con clúster positivo de **0,852 MW
mediano**, el 90 % de ellas a menos de 5 km del cráter, y MIROVA no publica ninguna. Con
2.316 de 2.410 sin disparar Test 1, la detección viene de los paths contextuales de
NTI/dNTI, no del MIR absoluto — o sea, la detección es metodológicamente legítima. La
duda es si el objeto detectado es el foco sub-píxel real o el campo difuso, y A82/A83 ya
declararon agotada esa discriminación por vía espectral.

**En la banda ≤2 km del cráter, 1.073 de 1.233 detecciones MODIS (87 %) llevan
`distance_class = far`.** Ese es el bug, y no está en la detección.

---

## M5 · La grilla, desde los KMZ y desde los GeoTIFF (pendiente #6 de AUDIT_S128)

**Los GeoTIFF son la escena real.** Semiancho medido sobre las 33 combinaciones
volcán×sensor:

| sensor | píxeles | semiancho N-S | semiancho E-O | paso N-S | paso E-O | vs `half_km=25,5` |
|---|---|---|---|---|---|---|
| MODIS | 51×51 | 25,651 km | 25,545 km | 1.005,9 m | 1.001,8 m | **+0,151 / +0,045** |
| VIIRS375 | 134×134 | 25,587 km | 25,481 km | 381,9 m | 380,3 m | **+0,087 / −0,019** |
| VIIRS750 | 67×67 | 25,396 km | 25,290 km | 758,1 m | 754,9 m | **−0,104 / −0,210** |

**`half_km = 25,5` es correcto**, dentro de ±0,21 km. El residuo es la distorsión de
reproyectar a EPSG:4326 un cuadrado UTM, no un desacuerdo de diseño. Las formas confirman
Campus 2022 (51×51 / 67×67 / 134×134) y los pasos, la resolución nominal.

**Los 15 KMZ de `kmz/`** (los otros 4 archivos del directorio son .tif) dan semianchos de
**23,99 a 25,80 km**, medianas 24,66–25,16 km: **hasta 1,51 km menos por lado** (Villarrica
VIIRS750, eje N-S). El `LatLonBox` es un recorte de visualización, **no** la extensión de
la escena; usarlo para fijar el ROI achicaría el anillo de fondo.

**Como centro, en cambio, el KMZ está bien**: el centro del `LatLonBox` coincide con
`mirova_center_lat/lon` de `volcanoes.yaml` con mediana de **1 m** y máximo de **265 m**
(2 de 15 sobre 200 m: Copahue·VIIRS750 y Láscar·VIIRS750). Coherente con S128: el valor
heredado del KMZ en S80 sirve como centro y no como extensión.

---

## Hallazgos

| # | hallazgo | clase | severidad |
|---|---|---|---|
| H1 | El GeoTIFF público **no puede adjudicar posición**: error mediano 4,80 km, ρ=0,151, y en MODIS/VIIRS750 pierde contra el nulo trivial en 86–88 % de las pasadas. Sólo 2 de 16 celdas pasan el criterio pre-registrado. | **CONFIRMADO** (endurece el guard de AUDIT_S128 §3) | alta — bloquea un eje |
| H2 | **A69 confirmado con evidencia exógena**: en el 99,2 % de las pasadas MODIS, el máximo de infrarrojo medio de la escena **de MIROVA** está a 20,76 km del cráter. A 1 km, el MIR absoluto no ve el volcán — ni para ellos ni para nosotros. | **CONFIRMADO** | alta |
| H3 | Nuestro `final_hotspot` de MODIS está a 21,43 km del cráter (mediana, n=236) mientras el `primary_cluster` está a 2,11 km; como `distance_class` sale del primero, **el 87 % de las detecciones MODIS con el clúster a ≤2 km del cráter quedan `far`**. | **CONFIRMADO** (A46/A81 con denominador nuevo) | **alta — es el bug** |
| H4 | **MIROVA mide `Distancia_km` desde `mirova_center`, no desde el cráter**: 0,48 km de error mediano y ρ=0,487, contra 1,02 km y ρ=−0,073 con el `vent`. | **CONFIRMADO** (n=1.815) | media — invalida comparaciones pasadas |
| H5 | «Los nevados están corridos al **N**» (A69/S104) **no generaliza**: el sesgo persiste en 2026 pero es al S en Copahue (1.952 m) e Isluga, al N en Llaima (1.927 m) y Lastarria, al O en Villarrica (1.404 m). El mecanismo de A69 se sostiene; el enunciado corto, no. | **OBSOLETO** (el enunciado, no la regla) | media |
| H6 | En VIIRS375, cuando la escena de MIROVA tiene su máximo sobre el edificio (23 % de las pasadas), **nuestro clúster está a 228 m = 0,61 píxeles**, 92,7 % dentro de 2 píxeles (n=41). | **CONFIRMADO** | — (es evidencia a favor) |
| H7 | Los 111 FN son señal sub-umbral, no fallas: 0,19 MW mediano de MIROVA, 90,1 % bajo 0,5 MW, `nti_max` en el piso en 78,4 %, 42,3 % con vista >45°. Cero FN en MODIS. | **CONFIRMADO** | baja |
| H8 | El sub-reporte de magnitud de VIIRS está **fuera de la banda de paridad**: 0,600 (V375, n=1.490) y 0,581 (V750, n=260). MODIS en paridad (1,016, n=65). | **CONFIRMADO** (reconfirma S125/S128) | media |
| H9 | La sobre-detección de VIIRS375 es de **0,047 MW mediano**: al cortar en 0,1 MW baja de 64,5 % a **4,4 %**. La de MODIS **no** se cae con el umbral: 96,2 % sobre 0,1 MW, 0,852 MW mediano. Sobre 2026, **99,4 % de los records MODIS (5.163/5.193) llevan clúster positivo**. | **CONFIRMADO** | media-alta |
| H10 | La atribución de los «FP» a rasgos físicos nombrados (lago Conguillío, Lazufre, salares) **no se pudo verificar**: no hay gazetteer en el repo. Lo medible es que el 91,1 % está a ≤5 km del cráter y que los 565 de >5 km se reparten en los cuatro cuadrantes — firma de ruido, no de un rasgo fijo. | **SIN RESPALDO** (la clasificación de A54, no recomputada) | media |
| H11 | Los records MODIS **no tienen la clave `nti_max` de nivel superior** (0 no nulos en 5.193 records de 2026); sólo `diag_nti_max`. Un script que lea `nti_max` recibe `None` y lo lee como «no se calculó el NTI». Es el patrón A7/A89. | **CONFIRMADO** | baja — trampa para auditorías |
| H12 | `half_km = 25,5` es correcto (±0,21 km contra los GeoTIFF). El `LatLonBox` del KMZ recorta hasta 1,51 km por lado y no sirve para fijar la extensión; como centro sí sirve (≤265 m). | **CONFIRMADO** — cierra pendiente #6 de AUDIT_S128 | baja |

---

## Recomendaciones

**R1 — Arreglar `distance_class` en MODIS, en el algoritmo, no en el display (A72, H3).**
El dato que se está ocultando **es un artefacto**: el `final_hotspot` de MODIS es el máximo
de MIR absoluto de la escena y está a 21 km del cráter porque el MIR absoluto a 1 km no ve
el volcán (H2, probado con la escena de MIROVA). No es señal real sub-umbral, así que la
salida no es el display: es no derivar la clasificación de distancia de un punto que mide
topografía. El candidato natural es derivarla del `primary_cluster.centroid`, que es el
punto que el dashboard ya reporta como magnitud (A10) y que aquí queda a 2,11 km del
cráter.
*Cómo validarlo*: A/B con reproc real (A18 — el preview offline no predice la selección de
clúster), criterio pre-registrado sobre las 65 pasadas TP de MODIS (que hoy dan recall
1,000: el cambio no puede bajarlas) y sobre las 2.410 de la celda (c) (medir cuántas pasan
de `far` a `summit` y cuál es su distribución de distancia). Y A45: tag defensivo y
confirmación explícita de Nicolás antes de tocar `process_modis.py`.

**R2 — Anclar en `mirova_center` toda comparación de distancia con MIROVA (H4).** Hoy hay
auditorías y documentos que comparan contra el `vent`; con ese ancla la correlación con la
`Distancia_km` de MIROVA es **−0,073**, o sea nula, y PCC/Tupungatito/PP se ven corridos
por kilómetros que no existen. *Cómo validarlo*: ya está validado (n=1.815); lo que falta
es propagarlo — un helper único en `experiments/_s126_lib.py` que devuelva la distancia
anclada, y revisar quién compara contra el `vent`.

**R3 — Corregir el enunciado de A69 en `CLAUDE.md` (H5).** La regla es correcta y el
mecanismo también; lo que hay que sacar es «corridos ~1 km al N», que describe los dos
volcanes que S104 miró. Reemplazar por «corridos hacia el terreno tibio de menor altitud,
cuya dirección es propia de cada volcán» y adjuntar la tabla de M2c. *Cómo validarlo*: la
tabla está en `m2_espacial.json`, n de 199 a 849 por celda.

**R4 — No volver a intentar validar posición contra el GeoTIFF (H1).** El guard de S128
decía «no adjudica detección ni magnitud»; hay que agregarle **posición**. La única
excepción medida es el acuerdo condicional de VIIRS375 (H6), que sirve para **confirmar**
que estamos bien, no para arbitrar cuando discrepamos.

**R5 — Persistir `nti_max` en los records MODIS (H11).** Es el fix de seis líneas del
patrón A7: la variable ya se calcula (`diag_nti_max` está poblado en los 5.193), sólo falta
la clave de nivel superior. Sin eso, cualquier auditoría cross-sensor que use `nti_max`
—y varias reglas del proyecto lo hacen, A80 entre ellas— trata MODIS como si no tuviera NTI.

**R6 — Recomputar la clasificación física de A54, o dejar de citarla como medida (H10).**
El «95 % son físicamente reales» de S86 nunca se recomputó y esta auditoría tampoco pudo
—falta el gazetteer—. Lo que sí se puede hacer barato: cargar las coordenadas de los rasgos
conocidos (cráteres secundarios, campos fumarólicos, lagos) a `volcanoes.yaml` como una
lista de rasgos con nombre y radio, y entonces la clasificación se vuelve un `join`.
Mientras no exista, la cifra de S86 es una afirmación sin denominador vigente (A90).

---

## Lo que no pude verificar

- **La ventana exógena son 11,5 días** (2026-05-08 a 05-20), no 2026. Todo M2-A, M3 y M5
  vive ahí. El archivo dejó de actualizarse el 2026-05-20; si el poller sigue vivo, un
  archivo de más meses convertiría celdas de n=11 en celdas afirmables.
- **La atribución de los «FP» a rasgos nombrados** (H10).
- **La magnitud** no la toqué con el TIF: A24 y el guard de S128 lo prohíben y el control
  de M3 no da ninguna razón para levantarlo.
- **`Isluga|VIIRS375` pasa el gate con n=11**, bajo el umbral de 15 que el propio encargo
  fija. La reporto como indicio, no como celda afirmable; la única celda que pasa el gate
  **y** llega a n≥15 es `PuyehueCordonCaulle|VIIRS375`.

---

## Archivos

Todo en `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/experiments/_s131_audit/ground_truth/`:

| script | qué mide | JSON |
|---|---|---|
| `_lib.py` | universo común: emparejamiento, sensores, lectura de GeoTIFF, loader del CSV | — |
| `m1_cobertura.py` | M1 — cobertura del archivo y tolerancia | `m1_cobertura.json`, `pares_pasada.csv` |
| `m3_control_instrumento.py` | M3 — 4 estimadores × 3 anclas contra `Distancia_km` | `m3_control.json`, `m3_control_detalle.csv` |
| `m3b_gate.py` | M3b — criterio pre-registrado por celda + nulo trivial | `m3b_gate.json` |
| `m2c_tabla_pasadas.py` | tabla maestra 1.556 escenas × record × fila del CSV | `m2c_tabla_pasadas.csv` |
| `m2_espacial.py` | M2 — acuerdo con el TIF y offset direccional 2026 | `m2_espacial.json`, `m2b_offsets.csv`, `m2a_tif_vs_nuestro.csv` |
| `m2d_acuerdo_condicional.py` | M2d — acuerdo condicional por modo de la escena | `m2d_acuerdo_condicional.json` |
| `m4_cruce_csv.py` | M4 — las tres celdas, ancla de la distancia, magnitud | `m4_cruce.json`, `m4_cruce_detalle.csv`, `m4_FN_detalle.csv`, `m4_nos_sin_alerta_detalle.csv` |
| `m5_kmz_grilla.py` | M5 — los 15 KMZ del repo | `m5_kmz_grilla.json`, `m5_kmz_grilla.csv` |

Además `m4b_sensibilidad.json` (umbral de magnitud y recall por celda), `m4c_modis_nti.json`
(H11) y `m5b_tif_extents.json` (extensión real de la escena).
