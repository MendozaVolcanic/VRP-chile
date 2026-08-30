# S129 · Tres papers sobre nuestros propios volcanes

Racimo leído: **Aguilera, Caro & Layana 2021** (lagos cratéricos de Peteroa, 1984-2020,
`documentacion/feart-09-722056.pdf`, Front. Earth Sci. 9:722056), **Pallister et al. 2013**
(`Pallister_2013_Chaiten_rhyolite_dome.pdf`, Andean Geology 40(2):277-294) y **Bernstein et al.
2013** (`Bernstein_2013_Chaiten_FLIR_thermal.pdf`, Andean Geology 40(2):295-309). Ninguno es canon
MIROVA ni metodológico: se leen por **conocimiento físico del volcán**.

---

## 1. Peteroa: cuatro lagos, dos campos fumarólicos, y hasta tres focos calientes a la vez

### 1.1 La geometría, en números

> "Peteroa volcano (35.240 °S, 70.570 °W, 3,603 m a.s.l.) […] is formed by a ∼5 km diameter
> caldera-type crater, which includes four nested craters (150–500 m diameter; all hosting lakes)
> and a scoria cone" — p. 2.

> "Fumarolic activity is present in Craters 1, 2, and 3, and in the zone between Craters 2 and 4"
> — p. 2.

Áreas máximas de los lagos (Tabla 2, p. 10): **31.514 / 10.575 / 20.344 / 15.171 m²** para Cráteres
1-4. Campo fumarólico nuevo de 1987, en la posición del actual Cráter 3: "**covering an area of
∼100 m²**" (p. 3) con "40–50 vents" (p. 10). Cráter anidado de 2018: "**the nested crater grew up to
∼75 m diameter**" (p. 4). El campo fumarólico del Cráter 1 está "**located in the western side of
the crater**" (p. 8).

**Traducción a nuestra geometría**: la caldera entera (radio ~2,5 km) cabe dentro de nuestro
`inner_radius_km = 3` y también dentro de `vent_radius_km = 3` (verificado en `volcanoes.yaml`;
la máscara es `vent_roi_mask = vent_dist <= vent_radius_km`, `pipeline/process_viirs.py:1573` y
`pipeline/process_modis.py:1152`). Es decir: **los seis focos térmicos documentados compiten
legítimamente por ser el cluster primario en cada pasada**. Nada de lo que el paper describe queda
fuera de la ventana de búsqueda ni requiere ampliarla.

### 1.2 Temperaturas y flujos medidos (el dato que decide si los vemos)

> "The measured maximum radiative heat fluxes (Q rad) measured were 1.2, 1.5, 2.3, and 1.4 MW for
> Crater Lake 1, 2, 3, and 4, respectively, whereas the measured maximum volcanic heat fluxes
> (Q volc) measured were 7.1, 38, 31, and 23 MW" — p. 8.

> "The highest brightness temperature measured in each crater lake was 323, 328, 334, and 326 K for
> Lake 1, 2, 3, and 4" — p. 8.

> "The highest Q volc recorded on Peteroa volcano was reached during a quiescence period,
> specifically in January 2006, corresponding to 59 MW, **when three craters were thermally active
> (Craters 2, 3, and 4)**" — p. 16.

Ojo con la contabilidad: `Q_volc` es el residuo del balance energético del lago (Ec. 1, p. 6), no
radiancia. Lo comparable con nuestro VRP es `Q_rad` (Stefan-Boltzmann sobre el pixel Landsat TIR,
Ec. 8, p. 6, con σ = 5,67×10⁻⁸ y ε 0,93-0,95 según estación): **1,2-2,3 MW por lago**.

### 1.3 El cálculo que importa: ¿un lago tibio dispara nuestro pipeline?

Cálculo propio (Planck, no del paper), tomando el caso más caliente documentado — Cráter 3, 334 K,
20.344 m² — sobre fondo nival a 273 K:

| sensor | fracción de píxel | ΔL_MIR | **VRP** | **dNTI** |
|---|---|---|---|---|
| VIIRS I04 375 m | 0,145 | 0,216 | **0,55 MW** | **0,049** |
| MODIS B21 1 km | 0,020 | 0,030 | **0,58 MW** | **0,008** |

Con el lago más grande (Cráter 1, 31.514 m² a 330 K) sube a **0,73 MW** y dNTI 0,060. Nuestro piso
de detección dNTI summit es **C1 = 0,003** (`pipeline/profiles/mirova_equivalent.yaml:98`, con
`enable_dnti_dual_roi: true` verificado en `pipeline.profile`). Es decir: **un lago cratérico de
Peteroa está entre 3 y 20 veces por encima de nuestro umbral de detección, y produce por sí solo
entre 0,3 y 0,7 MW de "VRP"** — sin una gota de lava.

Eso es exactamente el rango en que vive PP hoy: sobre 3.105 records con `pc.vrp_mw > 0`, la mediana
es **0,156 MW** y el p90 **1,26 MW** (`data/mirova_equivalent/PlanchonPeteroa.json`, cálculo propio).

### 1.4 ¿Explica esto la bimodalidad A22?

**Da la base física, pero la bimodalidad que medimos hoy NO es la que el paper predice.** El paper
sí autoriza el mecanismo: hasta tres lagos térmicamente activos simultáneos (enero 2006), más dos
campos fumarólicos, y una **migración documentada** del foco entre cráteres a lo largo de décadas
("the migration of the thermal/eruptive activity, and the interconnection of fluid pathways", p.
18). Un pipeline anclado al vent que cada noche elige el cluster más caliente dentro de 3 km, sobre
un campo con 4-6 focos que encienden y apagan, **va a saltar de foco sin ningún bug**.

Pero al mirar nuestros datos, el segundo modo no está donde debería si fueran dos cráteres.
Histograma de distancia centroide→vent (n=3.105):

- **0,0-0,5 km: 584 records** — VRP mediana 0,139 MW, 58 % con rumbo **W** (el lado donde el paper
  pone el campo fumarólico del Cráter 1). 1 píxel.
- 0,5-2,5 km: 1.449 — VRP mediana **0,435 MW**, 2 píxeles, rumbos repartidos. Este es el modo
  "caldera": el que integra varios focos, y el que explica los ratios altos.
- **2,5-3,0 km: 891 records** — VRP mediana **0,053 MW**, 1 píxel, rumbos E/NW/SE.

El tercer grupo es un **apilamiento en el borde de `vent_radius_km = 3`**, con la magnitud exacta de
nuestro artefacto topográfico (0,04-0,06 MW) y dominado por VIIRS 375 m (53 % de los records SNPP
caen ahí, contra 7 % en MODIS_TERRA). **No es un segundo cráter.** Prueba: Chaitén, que también
tiene `vent_radius_km: 3` y **un solo** centro térmico, muestra el mismo apilamiento (773 records en
2,5-3,0 km sobre 3.421). Es geometría del pipeline, no geología.

### 1.5 En qué nos contradice

1. **Los "focos" de Peteroa no son de alta temperatura.** El paper no reporta ni una sola
   temperatura de superficie sobre ~334 K en 36 años. La calibración de Wooster que usamos
   (`WOOSTER_COEFF = 18.9/19.7/18.0`) es para emisores >600 K; aplicarla a un lago a 60 °C es
   extrapolar fuera de dominio. **Nuestro VRP de PP no es "poca lava": es un lago tibio y un campo
   fumarólico, magnitud que el método MIR no está calibrado para medir.** Esto pesa sobre el frente
   del **piso VRP**: subir el piso a 0,1 MW en PP no borra artefacto — borra los lagos.
2. **La anomalía es intrínsecamente multi-foco y migratoria.** Un `mirova_center` fijo 2,02 km al
   norte de nuestro vent (verificado: `mirova_center_lat: -35.2232` vs `vent_lat: -35.241099`) y un
   único `vent_lat/lon` describen mal un objeto de 5 km con seis focos.
3. **Contradice al frente de nube.** El paper descartó 400 de 1.208 imágenes Landsat por nube sobre
   los cuatro cráteres (p. 6) y advierte que la nube "produc[e] an underestimation of Q volc […]
   where Q volc = 0" (p. 16). PP está en la Cordillera central, no en el altiplano seco: apagar la
   máscara de nube (D14) es más caro acá que en Láscar.
4. **Nada sostiene un halo regional.** En 36 años el paper no reporta actividad térmica en Planchón
   ni en Azufre. Todo lo publicado está dentro de la caldera de Peteroa. Cualquier detección nuestra
   a >3 km del vent (181 records, VRP mediana 0,94 MW, p90 5,0 MW) **no tiene respaldo en la
   literatura del volcán**.

### 1.6 Qué NO dice

No dice nada sobre MIR, NTI, VRP ni sobre MODIS/VIIRS: es **exclusivamente TIR+SWIR Landsat 30-120 m
y óptico Planet 3-5 m**. No da coordenadas por cráter (sólo la Figura 1B). No mide temperatura de
fumarolas en terreno. Y su `Q_volc` **no es comparable** con nuestro VRP: es un residuo de balance
energético que incluye evaporación y conducción, no radiancia.

---

## 2. Chaitén: el domo es enorme, los puntos calientes son metrizos

### 2.1 Tamaño — decide sub-píxel vs resuelto

> "the Chaitén lava dome complex is **about 2x3 km in size**" — Bernstein, p. 299.
> "circular **2.5 km diameter** collapse caldera" — Pallister, p. 278 (Bernstein dice "3-km-diameter"
> en p. 296: discrepan entre sí).
> "The 2008-2009 rhyolite lava dome has a total volume of approximately **0.8 km³**" — Pallister, p. 277.

Un complejo de ~6 km² son ~43 píxeles VIIRS I-band y ~6 píxeles MODIS: **el domo NO es sub-píxel**.
Nuestro `inner_radius_km = 5` lo cubre entero con holgura, y el `vent_radius_km = 3` también.

⚠️ **Bernstein trae un error de coordenada**: "centered at 42°59' south and 72°38' west" (p. 296) =
−42,983°, que está **16 km al sur** del domo. GVP y nuestro `vent_lat = −42,8344815` (≈42°50'S) son
lo correcto. **No mover nada por esta línea.**

### 2.2 Temperaturas FLIR (aéreo, 1 m/píxel, 7,5-13 µm)

FLIR SC640, "spatial resolution of 0.99 m at a distance of 1,500 m", ε = 0,95, precisión "±2 °C or
2 %" (Bernstein, p. 298). Advertencia del autor: "the temperatures obtained are probably **minimum
temperatures**" (p. 299).

| fecha | máximos medidos |
|---|---|
| 25-feb-2009 | Espina "**near 400 °C**" en su base oeste; punto en flanco E del Domo 2 "**near 300 °C**"; Domo 1 "**exceeding 200 °C**" (pp. 302-303) |
| 24-ene-2010 | "A small lobe had temperatures **near 200 °C**, and another area on the dome had maximum pixel temperatures **near 270 °C**"; vista general "Maximum temperature is about **110 °C**" (pp. 304-305) |

**Emisión focal, no difusa**, y con "thermal divide" entre focos: "we interpret the area of highest
temperatures at the summit of Dome 2 to be the likely location of its vent, **more than 200 m away
from the Spine**" (p. 301). Tres vents simultáneos y estructuralmente independientes (Domo 1, Domo 2,
Espina; p. 303).

### 2.3 Lo que esto significa para nosotros

Un parche de 200-400 °C de decenas de metros dentro de un píxel de 375 m es **exactamente** el
régimen en que el método MIR de Wooster funciona bien: emisor discreto, alto contraste, área
pequeña. Explica por qué Chaitén nos da ratio 1,26× y contraste al cráter z hasta 24,8 en el archivo
TIF, mientras PP (lago a 60 °C, extendido) se descalabra. **Son dos físicas distintas: en Chaitén
medimos un objeto para el que el algoritmo está calibrado; en PP no.**

Contra nuestra confianza, sin embargo: la fuente térmica de Chaitén **está fría desde ~2010**.
"By 24 January 2010 the number, size and temperatures of hot areas on the lava dome complex had
decreased significantly" (p. 304), y los autores dudan del origen: los hotspots "could be isolated
areas of residual dome growth or possibly hot rock surrounding active fumaroles, though there is
**no obvious correlation between the hot areas and active fumarole condensation plumes**" (p. 304).
Es decir: **no hay evidencia publicada de fumarolas persistentes localizadas** que sostengan lo que
vemos hoy. Nuestro `notes: 'Persistent fumarolic activity'` en `volcanoes.yaml` no está respaldado
por estos dos papers — habría que ir a la literatura post-2013.

Verificado en nuestros datos: Chaitén tiene 3.421 records con `pc.vrp_mw > 0`, mediana **0,125 MW**
y máximo 42,6 MW. Ese máximo merece revisión aparte: no hay nada en Pallister ni Bernstein que
justifique 42 MW en un domo apagado hace 15 años.

### 2.4 Qué NO dicen

Ninguno de los dos calcula VRP, radiancia MIR ni flujo radiativo integrado. Bernstein es explícito:
"We present and interpret our results **mostly qualitatively rather than quantitatively**" (p. 299),
por las tres cámaras distintas y los rangos de calibración distintos. **No usar sus temperaturas
como serie temporal calibrada.** Pallister no habla de térmica satelital en absoluto: es volumen y
tasa de efusión (66 m³/s las primeras dos semanas, 45 m³/s los primeros cuatro meses, ±20 %, p. 288).

---

## 3. Bibliografía que citan y no tenemos

| ref | por qué nos sirve | DOI |
|---|---|---|
| **Layana et al. 2020**, *VOLCANOMS*, Remote Sens. 12:1589 | Sistema chileno de monitoreo térmico por Landsat — el software VIPS con que se calculó este paper. Competidor/complemento directo de MIROVA, hecho en la UCN | 10.3390/rs12101589 |
| **Romero et al. 2020**, JVGR 402:106984 | Erupción 2018/19 de Peteroa con teledetección + ceniza; juvenil vs lítico | 10.1016/j.jvolgeores.2020.106984 |
| **Aguilera et al. 2016**, Andean Geol. 43(1):20-46 | Erupción 2010-2011 de PP; temperaturas de lago **en terreno** (7,4 / 43 / 19 °C en marzo 2011, citadas p. 11) | 10.5027/andgeoV43n1-a02 |
| **Lewicki et al. 2016**, Bull. Volcanol. 78:53 | Balance energético de lago cratérico con validación in situ (Kawah Ijen) | 10.1007/s00445-016-1049-9 |
| **Aldeghi et al. 2019**, Remote Sens. 11:2151 | Monitoreo volcánico con CubeSats Planet de alta cadencia | 10.3390/rs11182151 |
| **Tassi et al. 2016**, Chem. Geol. 432:41-53 | Gases fumarólicos PP 2010-2015: dos fuentes magmáticas | 10.1016/j.chemgeo.2016.04.007 |
| **Vaughan et al. 2005**, GRL 32:L19305 | TIR satelital sobre domo (Mount St. Helens) | 10.1029/2005GL024112 |
| Spampinato et al. 2011, Earth-Sci. Rev. 106:63-91 | Revisión de cámaras IR en vigilancia volcánica | — |

---

## 4. Acciones concretas que se desprenden

1. **PP: no subir el piso VRP a 0,1 MW sin separar antes lago de artefacto.** El cálculo de §1.3
   pone los lagos en 0,3-0,7 MW y el artefacto en 0,04-0,06 — el piso los separa bien *en teoría*,
   pero el modo 2,5-3,0 km (891 records) mezcla ambos.
2. **Revisar el apilamiento en `vent_radius_km = 3`.** Es transversal (PP y Chaitén lo tienen
   igual), es de 1 píxel y de 0,05 MW. Merece su propio hilo — no es geología.
3. **Chaitén max 42,6 MW**: sin respaldo en la literatura del domo. Auditar ese record.
4. **`notes` de Chaitén en `volcanoes.yaml`** ("Persistent fumarolic activity") no está sostenido
   por estos papers; verificar antes de seguir citándolo.
