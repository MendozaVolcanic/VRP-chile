# El costo de apagar el filtro contextual — y por qué el veredicto de S125 estaba invertido

> Todos los números salen de scripts que los persisten (regla S91). Ninguno
> transcrito a mano. Scripts: `experiments/_s125_magnitud/0{4,5,6,7,8,9}_*.py`,
> salidas en los `.json` de al lado.
>
> Trabajo **read-only**: no se tocó `pipeline/`, ni ningún perfil, ni
> `mirova_equivalent`. Sólo se leyeron los brazos ya reprocesados en disco.

## Veredicto: NO ADOPTAR el brazo E. Y el hallazgo de S125 hay que reescribirlo.

S125 cerró diciendo que apagar `enable_test1_contextual_filter` explicaba **todo**
el sub-reporte de VIIRS 375: la mediana del ratio nuestro/MIROVA pasaba de 0,600 a
1,043. Ese número es correcto, pero **agrupa los cuatro volcanes en una sola
mediana**, y al desagregarlo dice lo contrario:

| volcán | n | control | **E** | F | G |
|---|---|---|---|---|---|
| Villarrica | 8 | 0,764 ✓ | 1,315 ✓ | 0,764 ✓ | 1,315 ✓ |
| Planchón-Peteroa | 13 | **0,957 ✓** | **6,636 ✗** | 0,957 ✓ | 6,636 ✗ |
| Láscar | 35 | 0,434 ✗ | 0,635 ✗ | 0,434 ✗ | 0,434 ✗ |
| Puyehue-Cordón Caulle | 21 | 0,722 ✓ | 1,141 ✓ | 0,722 ✓ | 1,141 ✓ |
| **agrupado (lo que reportó S125)** | 77 | **0,600** | **1,043** | 0,600 | 0,747 |
| **volcanes en banda [0,7–1,4]** | | **3/4** | **2/4** | 3/4 | 2/4 |

El criterio pre-registrado número 1 es "más volcanes dentro de banda". El brazo E
**pierde uno**: Planchón-Peteroa estaba en 0,957 —prácticamente calibrado— y se va
a **6,636**, siete veces MIROVA.

La mediana agrupada "mejora" por composición de la muestra, no por calibración:
Láscar aporta el 45 % de los pares y sigue clavado en 0,43; Planchón se dispara
×6,9. La mediana del conjunto cae por casualidad cerca de 1,0. Es el mismo error
que las auditorías de S124 tumbaron —mezclar poblaciones fabrica un veredicto—
sólo que esta vez la estratificación que faltaba no era por sensor sino **por
volcán**.

## El costo, medido: no son falsas alarmas, es que todos los números quedan mal

Lo primero que sorprende es que **la detección casi no cambia**:

| | control | E |
|---|---|---|
| pasadas con detección | 608 | 604 |
| detecciones nuevas | — | **0** |
| detecciones perdidas | — | 4 |
| noches sin contraparte MIROVA | 349 | 346 (**−3**) |

Cero alarmas nuevas. El costo está entero en la **magnitud**:

| volcán | régimen | n_pixels del clúster | clústeres de 1 píxel | ratio pareado E/control |
|---|---|---|---|---|
| Villarrica | nevado | 1 → **43** | 98,8 % → 13,5 % | **×16,3** (máx 45) |
| Planchón-Peteroa | nevado | 1 → **44** | 99,3 % → 16,2 % | ×11,8 (máx 39) |
| Puyehue-Cordón Caulle | nevado | 1 → 2 | 67,4 % → 37,0 % | ×1,0 (p75 9,1) |
| Láscar | desierto | 1 → 8 | 80,9 % → 25,5 % | ×1,0 (p75 3,1) |

Y el reparto entre noches con y sin actividad confirma que **no es señal**:

| | ratio E/control |
|---|---|
| noches que MIROVA confirma | ×1,0 (n=258) |
| noches **sin** alerta de MIROVA | **×12,2** (n=346) |

Si el filtro estuviera recortando energía volcánica real, el aumento tendría que
concentrarse donde hay actividad. Hace lo contrario. Y los píxeles que E agrega
aportan el **92,8 %** de la VRP del clúster: no se recupera una fracción perdida,
se reemplaza la medición entera.

## Por qué pasa: el fondo es el 75 % de lo que se está midiendo

Dos constantes del perfil operacional, leídas de `pipeline.profile`:

```
TEST1_ROI_KM                  = 3.0        -> el Test 1 vive en el disco r < 3 km
TEST1_INTERMEDIATE_BG_RING_KM = (1.5, 3.0) -> el fondo sale de la corona exterior
```

La corona [1,5–3] km es el **75 % del área** del mismo disco cuyos píxeles se
suman. Y en `process_viirs.py:1729` la energía de cada píxel es

```python
t1_delta_L = np.maximum(t1_L - effective_L_bg, 0.0)
```

donde `effective_L_bg` es la radiancia de la media de esa corona. O sea: cada
píxel se compara contra el promedio de sus propios tres cuartos exteriores, y el
recorte a cero se queda con la mitad de arriba. Sumar esa mitad da una VRP que
crece con la **cantidad de píxeles**, no con la energía del volcán.

El filtro contextual era lo único que impedía que esa corona entrara a la suma.

**La prueba geométrica.** Si E recuperara un foco volcánico, los píxeles
agregados se apiñarían cerca del cráter. Si integra terreno, se reparten como el
**área** de cada corona. Sobre 24.235 píxeles agregados en los nevados:

| anillo | esperado por área | observado | obs/esp |
|---|---|---|---|
| 0,0–0,5 km | 2,8 % | 2,0 % | 0,71 |
| 0,5–1,0 km | 8,3 % | 6,1 % | 0,74 |
| 1,0–1,5 km | 13,9 % | 10,4 % | 0,75 |
| 1,5–2,0 km | 19,4 % | 18,7 % | 0,96 |
| 2,0–2,5 km | 25,0 % | 27,4 % | 1,10 |
| 2,5–3,0 km | 30,6 % | 35,4 % | 1,16 |

Es el reparto del área, con una leve inclinación hacia afuera —los píxeles más
bajos son los más tibios, gradiente topográfico A69— y **el cráter queda
sub-representado** (0,71–0,75). El rumbo es uniforme (N 24,8 % · E 25,7 % ·
S 21,7 % · W 27,8 %). Un foco volcánico no se ve así. El terreno sí.

Cierra el corte abrupto en 3,0 km exactos: no hay nada físico ahí, es el borde
del ROI.

## Por qué G no es igual a E (la TAREA 2, contestada)

El bloque de arranque decía "si G ≈ E, cerrado". **No lo son**: agrupado, E da
1,043 y G da 0,747. Desagregado se ve dónde está la diferencia y no hay misterio:

- En Villarrica, PP y PCC, **G ≡ E** exacto.
- En **Láscar**, G vuelve a 0,434 = el control, exacto.

Es coherente con el mecanismo: G apaga el anillo intermedio, así que el fondo
vuelve al global 5–25 km. En el desierto ese fondo global es más caliente que la
corona interior, el clip a cero borra los píxeles agregados y la VRP espuria
desaparece. En los nevados el gradiente topográfico hace que el global también
sea caliente, pero los píxeles de la corona ya venían del recorte y G no alcanza
a borrarlos.

Sobre toda la población el efecto es chico (G/E = 0,950 en píxeles, 0,946 en VRP);
en el emparejamiento contra MIROVA se nota porque Láscar es el 45 % de la muestra.

**F ≡ control byte a byte** (0,600 y 0,434 idénticos): el anillo intermedio no
hace nada mientras el filtro contextual esté encendido, porque sólo sobrevive un
píxel. Sólo aparece cuando el filtro se apaga. Ésa es la interacción.

## Hallazgo colateral, y es el más grave: dónde medimos hoy Villarrica

Esto sale del **control**, o sea de la configuración operacional, sin tocar nada.
Partiendo las noches según MIROVA confirme o no (distancia del centroide del
clúster que se publica, al cráter):

| volcán | noches | n | dist. mediana | % más allá de 1,5 km | bt − t_bg | VRP mediana |
|---|---|---|---|---|---|---|
| Láscar | MIROVA confirma | 97 | **0,18 km** | 10 % | **+7,8 K** | 0,102 |
| | sin alerta | 13 | 2,63 km | 77 % | −1,79 K | 0,027 |
| PCC | MIROVA confirma | 86 | **0,28 km** | 19 % | **+5,4 K** | 0,108 |
| | sin alerta | 95 | 2,73 km | 70 % | +2,75 K | 0,042 |
| Planchón-Peteroa | MIROVA confirma | 45 | **0,59 km** | 40 % | −1,59 K | 0,069 |
| | sin alerta | 101 | 2,72 km | 85 % | −2,57 K | 0,042 |
| **Villarrica** | **MIROVA confirma** | **31** | **2,74 km** | **74 %** | **−4,74 K** | **0,049** |
| | sin alerta | 140 | 2,81 km | 98 % | −3,2 K | 0,045 |

Tres de los cuatro se comportan como corresponde: cuando hay actividad real el
clúster está **en el cráter** y el píxel es varios grados más caliente que el
fondo; en las noches quietas se va a ~2,7 km y el contraste desaparece.

**Villarrica no distingue las dos situaciones.** Con actividad confirmada por
MIROVA medimos a 2,74 km del cráter, con el píxel **4,74 K más frío** que el
fondo de la escena. En las noches sin alerta, lo mismo: 2,81 km y 0,045 MW. El
número que publicamos para Villarrica no está midiendo el cráter — es la
fluctuación más alta de la corona nival, y da positivo sólo porque se compara
contra la media de esa misma corona.

Detalle sobre los clústeres de un solo píxel de Villarrica (n=168, el 98 % de
sus detecciones): distancia mediana **2,79 km** (p25 2,64 / p75 2,91), rumbo medio
**267° (oeste)**, dentro de la corona de fondo el **94 %** de las noches. La
dispersión estrecha pegada al borde de 3,0 km es la firma: un foco volcánico no
se apila contra un límite de software.

Verificaciones hechas antes de afirmarlo (A62 — intentar refutarse):
`final_hotspot_source` es `test1_roi` (157) / `ctx_cluster` (11), no otro path;
`pc.n_pixels` = 1 en los 168; mi haversine coincide con el propio
`pc.centroid_dist_km` del pipeline dentro de 0,0009 km, así que el ancla es el
cráter y no hay error de referencia; los 168 van etiquetados **`summit`** porque
2,8 km < `inner_radius_km` = 5.

Esto es el frente #506 de S123 (Villarrica) con el mecanismo a la vista, y es
A69 operando en VIIRS 375. Es **artefacto**, no señal sub-umbral: por A72 se
arregla en el algoritmo, no en el display.

## Lo que queda abierto

1. **Láscar es el sub-reporte que sigue vivo** — 0,434, el 45 % de la muestra, y
   ninguno de los tres brazos lo mueve (G lo deja idéntico). Es el frente real de
   magnitud, y no tiene que ver con el filtro contextual.
2. **Villarrica mide fuera del cráter incluso con actividad confirmada.** Es un
   problema de detección/posición, no de magnitud, y ningún ajuste de escala lo
   arregla.
3. El **fondo autorreferente** (ROI 3,0 km contra corona 1,5–3,0 km) es una
   decisión de diseño que conviene revisar por separado del filtro. Hoy está
   tapada por el filtro contextual; cualquier cambio que deje entrar más píxeles
   la destapa.

## Lo que NO hay que concluir

- **No "el filtro contextual es correcto"**: es un parche que tapa el fondo
  autorreferente. Funciona por la razón equivocada — deja un píxel, y con un
  píxel el fondo casi no importa. Quitarlo sin arreglar el fondo es lo que
  destapa la corona.
- **No "S125 se equivocó al medir"**: los números de S125 son correctos y
  reproducibles. Lo que falló fue agrupar cuatro volcanes en una mediana. El
  propio bloque de arranque mandaba estratificar; faltó hacerlo por volcán.
- **No reabrir F**: `enable_test1_intermediate_bg` no mueve nada por sí solo
  (F ≡ control exacto). Sólo importa en interacción, y sólo en Láscar.
