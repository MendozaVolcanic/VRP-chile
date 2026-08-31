# S129 · Auditoría espacial de los 11 mapas del dashboard

> `experiments/_s129_espacial/01_mapa_vs_datos.py` → `01_mapa_vs_datos.json`.
> Audita la coordenada que el mapa **realmente dibuja** (`final_hotspot_lat/lon`,
> `frontend/index.html:2220-2221`), no el `primary_cluster.centroid` de donde sale la
> magnitud. La regla A46 avisa que esas dos representaciones pueden discrepar.

Nicolás marcó tres cosas mirando los mapas. Las tres se confirman, y **las tres salen
de la misma causa de fondo vista por distintas puertas**.

---

## 1 · «En Planchón-Peteroa veo pocos puntos, como si estuvieran todos en el mismo lugar»

**Confirmado, y no es de PP solo.**

| volcán (VIIRS375) | puntos dibujados | posiciones distintas | |
|---|---|---|---|
| Llaima | 673 | 138 | **20,5 %** |
| Copahue | 706 | 149 | **21,1 %** |
| Villarrica | 840 | 224 | 26,7 % |
| Tupungatito | 616 | 196 | 31,8 % |
| **Planchón-Peteroa** | **677** | **327** | **48,3 %** |

La distancia mediana al cráter en esos cinco es **0,00 km**: la coordenada es la del
cráter, exacta.

**Por qué.** El 57-78 % de esas detecciones tienen `final_hotspot_source = "test1_roi"`
— PP 922 de 1.618, Villarrica 1.471 de 2.017, Copahue 1.325 de 1.689. El Test 1 es una
**integral sobre todo el ROI**: mide energía en una región, no en un punto, así que no
tiene una posición propia y el pipeline le asigna la del vent.

Eso **no es un error de detección**. Es que una detección integrada no tiene coordenada,
y el mapa la dibuja como si la tuviera. El operador ve *un* punto donde hay 922
apiladas, y no tiene forma de saberlo.

**Qué se puede mejorar**: distinguir visualmente las detecciones sin posición propia de
las que sí la tienen — un símbolo distinto, o un halo del tamaño del ROI en vez de un
punto. Es un cambio de display legítimo porque **el dato es real**: no oculta un
artefacto, deja de fingir una precisión que no existe.

---

## 2 y 3 · Cordón Caulle: MODIS en el lacolito y puntos en el bosque

Van juntas porque son el mismo mecanismo.

### El dato de MODIS, en los once

| | MODIS |
|---|---|
| detecciones por volcán | 393 – 545 |
| posiciones distintas | **100 %** en los once |
| distancia mediana al cráter | **15,8 – 24,3 km** |
| fuera del `inner_radius` | **92 – 98 %** (PCC: 22,5 %) |
| **noches confirmadas por MIROVA** | **0 %** en diez de once (Láscar: 23,6 %) |

O sea: MODIS aporta cerca de 450 puntos por volcán, dispersos a 15-25 km, y **MIROVA no
confirma ninguno** salvo en Láscar, que es el único con ground truth MODIS.

Es la cara far→summit de D11/A82: el `final_hotspot` de MODIS se calcula sobre **MIR
absoluto**, que en un nevado está dominado por el gradiente topográfico (A69), así que
salta al salar, al valle tibio o al bosque de baja altitud.

### Por qué se ve en PCC y no en los otros diez

El mapa **sí filtra** los `far` con el toggle por defecto (`index.html:2539`, S26 B).
En diez volcanes eso esconde la nube de MODIS.

**En PCC no, porque su `inner_radius_km` es 20** — el único así, puesto para abarcar el
lacolito del Cordón Caulle, que está realmente desplazado ~7 km. Con ese radio:

| PCC | n | dist. mediana | p90 | clasificados *summit* |
|---|---|---|---|---|
| **MODIS** | 1.062 | **15,71 km** | 26,55 km | **65,5 %** |
| VIIRS375 | 1.727 | 0,39 km | 12,77 km | 99,9 % |
| VIIRS750 | 1.305 | 2,52 km | 16,37 km | 99,8 % |

**1.054 detecciones MODIS a 15,7 km de mediana se pintan de rojo «dentro del cráter»,
sobre el bosque.** Eso es exactamente lo que Nicolás ve. Y las de VIIRS también llegan a
12-16 km en el p90, aunque su mediana esté al cráter.

⚠️ **Y hay una pieza que existe y no se usa.** El frontend tiene desde S88 un
tratamiento visual aparte para `primary_cluster.geo_class === "extension"`
(`index.html:2532`), pensado justo para esto: pintar la extensión difusa distinto del
cráter. En PCC, **1.054 de 1.062 records MODIS dicen `geo_class: "summit"`** y sólo 8
dicen `far`. Ninguno dice `extension`. El mecanismo está construido y nunca se pobló.

Esto ya se había diagnosticado en S103 (regla A68: *«el `inner_radius_km=20` lo pinta
todo summit-rojo → parece cráter denso»*) y la acción quedó anotada como pendiente. Hoy
está cuantificada.

---

## Qué se puede mejorar, en orden

**1 · Poblar `geo_class = "extension"` para lo que está fuera del cráter pero dentro del
inner radius.** El display ya sabe pintarlo distinto. Es el arreglo de mayor efecto y el
más barato: no cambia ninguna detección, sólo deja de afirmar «cráter» sobre algo que
está a 15 km. Aplica sobre todo a PCC, y a PP y Tupungatito en menor medida.

**2 · Marcar las detecciones sin posición propia.** Las de `test1_roi` son entre el 57 y
el 78 % de VIIRS375 en varios volcanes y todas se dibujan sobre el cráter. Un símbolo
distinto —o un área en vez de un punto— evita que el operador lea una precisión que el
dato no tiene.

**3 · Decidir qué hacer con la nube MODIS.** Acá hay que ser honesto sobre el límite: la
regla A82 estableció, con datos, que a 1 km el foco sub-píxel real y el gradiente
topográfico difuso **son indistinguibles por cualquier eje físico que se probó**. Así que
«filtrar los MODIS malos» no tiene solución algorítmica conocida.

Pero **el display sí tiene una decisión pendiente**, y es distinta: hoy el mapa dibuja un
punto a 20 km del volcán como si fuera una detección *de ese volcán*. Con 0 % de
confirmación de MIROVA en diez de once, eso es afirmar más de lo que el dato sostiene.
La regla A72 dice que a un artefacto se lo ataca en el algoritmo y no en el display —
pero acá la pregunta no es si generar el dato, sino **si el mapa de un volcán debe pintar
puntos que no son de ese volcán**. Es decisión de Nicolás, no del pipeline.

## Lo que esta auditoría NO tocó

El `inner_radius_km = 20` de PCC es correcto: el lacolito está realmente desplazado. El
problema no es el radio, es que «dentro del radio» y «en el cráter» se pintan igual.

Y un detalle de trazabilidad: el comentario de `frontend/index.html:809-811` dice que las
detecciones lejanas «siguen visibles en el mapa». **Es falso desde S26 B**, que las
filtra en la línea 2539. Otro caso de «declarado ≠ efectivo».
