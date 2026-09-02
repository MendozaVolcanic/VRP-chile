# S131 · Eje dashboard — correctitud adversarial y utilidad operacional

Auditoría del entregable final: las 4 vistas publicadas en
<https://mendozavolcanic.github.io/VRP-chile/>. Dos mitades independientes:
**(A)** ¿lo que la pantalla dice coincide con lo que está persistido? (técnica T7),
**(B)** ¿le sirve al turno de OVDAS que a las 3 de la mañana tiene que decidir un
nivel de alerta?

Todo lo que sigue está medido sobre la **copia publicada** (bajada el 2026-09-02
16:10 UTC: `_recent.json` de los 11 Tier A, ventana de 100 días, 11.599 records),
no sobre el checkout local — que estaba un día atrasado. Scripts en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s131_audit\dashboard\`.

---

## Resultado

**La aritmética del dashboard está sana. Lo que falla es lo que la pantalla
*afirma* sin tener con qué respaldarlo.**

Repliqué en Python, verbatim, los diez predicados de display de `index.html`
(`mirovaEqVrp`, `f5CoreMagnitude`, `mirovaEqVrpCore`, `isCirrusArtifact`,
`isDiffuseFieldArtifact`, `isValidDetection`, `isSummitDetection`,
`latestDetection`, `getLevel`, la distancia de "ancla honesta" S106) y comparé
contra el DOM real del sitio publicado. **Las 11 tarjetas coinciden hasta el
último decimal** — VRP, nivel, distancia, píxeles, timestamp, sensor — y también
las cajas del panel de detalle (Villarrica VRE 686,5 GJ / 140 detecciones;
PCC 2.847,5 GJ / 229; Láscar 206,4 GJ / 85 / Max 1,90 MW). Cero errores de
consola, cero requests fallidos, 5,3 MB transferidos y toda la data lista en
**166 ms**. El deploy es **byte a byte idéntico** al repo tras normalizar
CRLF→LF. Los tres bugs que arregló S130 (barra congelada, "Actualizado" = reloj
del navegador, index↔mosaico con distinto nivel) están efectivamente cerrados: lo
verifiqué, no lo heredé.

Contra eso, cuatro cosas que la pantalla dice y no son ciertas o no significan
lo que parece:

1. El punto verde **"Sistema Operativo"** del encabezado es HTML fijo. No lo
   toca ningún dato. Lo vi latiendo en verde mientras las 11 tarjetas decían
   *"datos atrasados · última pasada hace 38 h"*.
2. La **tarjeta y el panel de detalle del mismo volcán muestran dos niveles de
   alerta distintos, en la misma pantalla, en los 11 de 11 casos** ahora mismo
   (tarjeta "Muy Bajo", detalle "Bajo"). Es el hallazgo #0 de S129 renacido en un
   par de vistas que nadie había cruzado.
3. **"◉ 0,0 km del cráter"** no es una medición: es el ancla puesta por
   construcción. Entre el 15 % y el 86 % de los marcadores del mapa (mediana
   ~72 % en 90 días) caen sobre **una sola coordenada**. Y el tooltip que los
   explica dice otra cosa que la que el código calcula.
4. Los dos mecanismos diseñados para que el operador distinga **señal real
   sub-umbral (cat-b) de artefacto** están **inertes**: el marcador naranja
   `geo_class == "extension"` no aparece en ninguno de los 11.599 records de la
   ventana publicada (y aunque apareciera, la rama que lo pinta es inalcanzable
   en la vista por defecto), y el filtro `isThermalArtifact` de S90/S93 no marca
   **ninguno** de 57.851 records porque sus umbrales quedaron por encima del
   rango de magnitudes que el sistema produce hoy.

Y una nota de método sobre los problemas conocidos que traía el encargo: **los
dos que sonaban peor resultaron ser ciertos en el código y nulos en el efecto**.
Las cuatro divergencias entre las copias de `mirovaEqVrp` —incluido el famoso
cap de 50.000 MW ausente en `diario`, redescubierto cuatro veces— siguen
escritas y producen **0 diferencias sobre 57.851 records**. Y
`auto_audit_weekly` efectivamente no usa `isValidDetection`, pero el gate que
realmente decide qué se grafica coincide con el del audit **exactamente, con 0
desacuerdos**. Probablemente por eso se redescubren: cada auditoría los encuentra
leyendo y ninguna los mide.

Y el problema de fondo, que no es de código: **en 4.279 ventanas rodantes de
48 h sobre 100 días, los 11 volcanes marcaron "Muy Bajo" el 100 % del tiempo.**
El badge de alerta es una constante. A las 3 de la mañana no le dice nada a
nadie.

---

## Parte A · Correctitud adversarial (T7)

Clasificación: **CONFIRMADO** (lo verifiqué y está), **FALSO** (lo verifiqué y no
está), **OBSOLETO** (estaba, ya se arregló), **SIN RESPALDO** (no pude medirlo).

### A1 · CONFIRMADO · severidad ALTA — el semáforo "Sistema Operativo" no mira ningún dato

`frontend/index.html:378-379` es HTML estático:

```html
<div class="status-label">
  <div class="status-dot"></div>
  Sistema Operativo
</div>
```

y `frontend/index.html:33` le pone `background: var(--green)` con
`animation: pulse 2s infinite`. No hay ninguna asignación en JS: `grep -n
"Sistema Operativo\|status-dot" frontend/index.html` devuelve sólo esas tres
líneas, todas declarativas.

**Evidencia del daño**: corriendo el sitio contra el checkout local (data hasta
2026-09-01 07:06 UTC, 38 h de atraso) el DOM daba simultáneamente

```
header  : "Sistema Operativo" (punto verde pulsante)
tarjetas: "● datos atrasados · última pasada hace 38 h"  ×11
```

El indicador más prominente del encabezado —el que un operador mira primero para
saber si el sistema respira— es incapaz de ponerse en rojo. Es exactamente la
forma de A87 al revés: no es un flag que se apaga y se lee como resuelto, es un
flag que **nunca se enciende** y se lee como sano.

El dato honesto **ya existe**: `monitoringFreshness(lastTime)` alimenta el
badge por tarjeta y funciona bien (verde "monitoreado · 13 h" hoy; ámbar "datos
atrasados · 38 h" ayer). Sólo falta que el encabezado consuma el peor de los 11.

### A2 · CONFIRMADO · severidad ALTA — dos niveles de alerta del mismo volcán en la misma pantalla

- Tarjeta: `buildCards()` → `latestDetection()` → **última** detección de 48 h
  (`index.html:1798-1806`, decisión S90 de Nicolás).
- Panel de detalle: `renderDetail()` → `getLevel(maxVrp)` donde `maxVrp` es el
  **máximo** de la ventana de 30 días (`index.html:1918-1921`).

Ambos badges usan la misma clase visual, la misma leyenda "Escala MIROVA" y
ninguno dice de qué ventana sale. Medido sobre la data publicada del
2026-09-02:

| volcán | tarjeta | nivel tarjeta | máx 30 d | nivel detalle |
|---|---|---|---|---|
| Isluga | 0,07 | Muy Bajo | 1,66 | **Bajo** |
| Láscar | 0,21 | Muy Bajo | 1,90 | **Bajo** |
| Lastarria | 0,06 | Muy Bajo | 2,88 | **Bajo** |
| Tupungatito | 0,02 | Muy Bajo | 5,00 | **Bajo** |
| Planchón-Peteroa | 0,02 | Muy Bajo | 4,59 | **Bajo** |
| Nevados de Chillán | 0,02 | Muy Bajo | 3,21 | **Bajo** |
| Copahue | 0,02 | Muy Bajo | 2,00 | **Bajo** |
| Llaima | 0,03 | Muy Bajo | 3,08 | **Bajo** |
| Villarrica | 0,04 | Muy Bajo | 5,00 | **Bajo** |
| Puyehue–Cordón Caulle | 0,25 | Muy Bajo | 5,00 | **Bajo** |
| Chaitén | 0,09 | Muy Bajo | 5,00 | **Bajo** |

**11 de 11 discrepan.** Confirmado en el navegador: al hacer clic en la tarjeta
"Láscar · Muy Bajo", el encabezado del detalle dice literalmente `Láscar BAJO`.

S130 sincronizó `index`↔`mosaico` porque la tarjeta de mosaico *enlaza* a index.
Este par —tarjeta de index y detalle de index— está a **un clic** de distancia y
nunca se cruzó.

### A3 · CONFIRMADO · severidad ALTA — el costo medido de "última pasada"

La decisión S90/S130 de titular con la última pasada en vez del máximo es
deliberada y no la discuto. Lo que faltaba era medir su costo. Sobre **4.206
ventanas rodantes de 48 h** (paso 6 h, 100 días publicados):

| volcán | n vent. | nivel distinto vs máx 48 h | ratio mediano máx/última | peor caso |
|---|---|---|---|---|
| Isluga | 389 | 20,8 % | 5,4× | 0,07 → 2,65 MW |
| Láscar | 353 | 4,5 % | 1,5× | 0,21 → 1,90 MW |
| Lastarria | 377 | 12,7 % | 2,4× | 0,06 → 3,10 MW |
| Tupungatito | 389 | 23,7 % | 22,7× | 0,02 → 5,00 MW |
| Planchón-Peteroa | 385 | 31,9 % | 20,6× | 0,02 → 5,00 MW |
| Nevados de Chillán | 373 | 24,7 % | 6,5× | 0,02 → 5,00 MW |
| Copahue | 389 | 21,6 % | 23,5× | 0,02 → 5,30 MW |
| Llaima | 388 | 33,0 % | 14,5× | 0,03 → 4,93 MW |
| Villarrica | 385 | 24,7 % | 11,3× | 0,04 → 4,70 MW |
| **Puyehue–Cordón Caulle** | 389 | **90,2 %** | 20,0× | 0,25 → 13,60 MW |
| Chaitén | 389 | 43,4 % | 10,0× | 0,09 → 6,67 MW |
| **TOTAL** | **4.206** | **30,4 %** | | |

En **una de cada tres ventanas** el operador lee un nivel más bajo que el que le
correspondería al pico de las últimas 48 h. En PCC, nueve de cada diez.
Ejemplo concreto y fechado: el **2026-06-06 02:35 UTC** MODIS Terra midió
**13,60 MW** en PCC (el máximo absoluto de los 100 días, nivel "Moderado"); la
tarjeta de esa ventana mostraba **0,25 MW · Muy Bajo**.

Esto no pide revertir S90. Pide que la tarjeta muestre **las dos cifras**
(«última 0,25 MW · máx 48 h 13,60 MW»), que es exactamente lo que MIROVA logra
poniendo la serie temporal al lado del número.

### A4 · CONFIRMADO · severidad MEDIA-ALTA — "◉ 0,0 km del cráter" es el ancla, no una medición; y el tooltip dice otra cosa

`index.html:1418-1428` (S106, "ancla honesta"): si
`final_hotspot_source ∈ {ctx_cluster, test1_roi, test1_nti_peak}` la distancia
que se muestra es `final_hotspot_dist_km`, **no** `pc.centroid_dist_km`. Para
`test1_roi` ese valor es 0,0 por construcción (el ancla ES el cráter).

Pero `index.html:1846` sigue diciendo:

```js
dcRow.title = "Distancia del centroide del cluster de la última detección al cráter, y su extensión en píxeles.";
```

El texto describe un campo que el código dejó de usar en S106. Contraste medido
sobre el checkout local del 2026-09-01, donde 7 de las 11 tarjetas estaban en
`test1_roi`:

| volcán | lo que muestra la tarjeta | `pc.centroid_dist_km` real |
|---|---|---|
| Isluga | 0,0 km | **1,207 km** |
| Láscar | 0,0 km | **2,856 km** |
| Planchón-Peteroa | 0,0 km | **2,905 km** |
| Nevados de Chillán | 0,0 km | **2,205 km** |
| Copahue | 0,0 km | **1,575 km** |
| Llaima | 0,0 km | **2,965 km** |
| Villarrica | 0,0 km | **2,787 km** |

El número no está mal *calculado* — el ancla honesta es la decisión correcta,
porque el `pc` de un record Test1 es el footprint de la integral con arrastre
topográfico A69. Lo que está mal es **el rótulo**: dice "centroide del cluster"
cuando es el ancla, y dice "0,0 km" cuando lo honesto sería "en el cráter
(ancla)". La tabla del detalle **ya lo hace bien** — escribe la palabra
`cráter` en la columna DIST en vez de `0,00`. La tarjeta no.

### A5 · CONFIRMADO · severidad MEDIA — el mapa apila cientos de detecciones en una coordenada

Consecuencia directa de A4 en el eje espacial. Con los defaults del dashboard
("Solo cráter", "Solo pixel principal"), replicando `index.html:2472-2560`:

| volcán | marcadores 90 d | coordenadas distintas | % en 1 sola coordenada |
|---|---|---|---|
| Copahue | 372 | 53 | **86,0 %** |
| Villarrica | 375 | 80 | 78,9 % |
| Llaima | 341 | 80 | 76,8 % |
| Nevados de Chillán | 354 | 84 | 76,6 % |
| Tupungatito | 337 | 82 | 76,0 % |
| Lastarria | 351 | 98 | 72,4 % |
| Planchón-Peteroa | 320 | 95 | 70,6 % |
| Chaitén | 416 | 178 | 57,5 % |
| Láscar | 389 | 223 | 42,9 % |
| Isluga | 398 | 263 | 34,2 % |
| Puyehue–Cordón Caulle | 678 | 576 | 15,2 % |

El problema conocido decía "57-78 % de las VIIRS375". Medido sobre **todos** los
marcadores y **todos** los sensores da **15,2 %–86,0 %** (mediana 72,4 %) —
o sea, es más extendido de lo que se creía. Para 7 de 11 volcanes la **mediana**
de la distancia del marcador visible es exactamente **0,00 km**.

Lo que el operador ve es una mancha roja densa sobre el cráter que parece
trescientas mediciones independientes convergiendo ahí, y es **una sola
coordenada repetida trescientas veces**.

### A6 · CONFIRMADO · severidad MEDIA — PCC pinta 82 % de sus marcadores como "summit" a más de 5 km

`inner_radius_km = 20` para PCC (valor oficial del KML MIROVA, correcto). Pero el
frontend usa ese mismo radio para decidir el color rojo-summit. Distancia al
cráter de los marcadores **visibles** (90 d):

| volcán | inner | n | p50 | p90 | máx | % > 5 km |
|---|---|---|---|---|---|---|
| Puyehue–Cordón Caulle | 20 | 678 | **8,05 km** | **18,74 km** | 24,98 km | **82,3 %** |
| Tupungatito | 7 | 337 | 0,00 | 4,26 | 18,05 | 5,0 % |
| Villarrica | 5 | 375 | 0,00 | 3,15 | 5,82 | 1,1 % |
| resto (8) | 3-5 | — | 0,00-0,83 | 1,01-3,33 | 3,40-21,50 | 0,0-0,6 % |

El offset de PCC es **real** (lacolito Cordón Caulle, ~7,8 km, A20/A68) — no es
un error del pipeline. El problema es que el rojo-summit lo mezcla con la cola
dispersa de ruido VIIRS750, y el operador no puede separarlos. La vista
`comparacion.html` (pestaña 3) tiene el render propuesto que sí los separa
(rojo proximal / naranja lacolito / gris cola) y sigue siendo un preview desde
S115.

### A7 · CONFIRMADO · severidad ALTA — el marcador que distingue cat-b real de artefacto está doblemente muerto

`index.html:2538` define `isExtension` a partir de
`primary_cluster.geo_class === "extension"`, y `:2585-2589` le da el color
naranja con el rótulo *"Extensión volcánica (no publicada por MIROVA)"*. Es el
único elemento del dashboard pensado para responder «¿esto es señal real
sub-umbral o es artefacto?».

**Muerto por el lado del dato**: sobre los 11.599 records de la ventana
publicada de 100 días, `geo_class` toma los valores
`{'summit': 7035, None: 4211, 'far': 353}`. **`"extension"` aparece 0 veces.**
`pipeline/volcanic_features.yaml` sólo cataloga features para 2 de los 11
volcanes (PCC y Lastarria), y en PCC el `inner_radius_km = 20` se traga el
lacolito antes de que `store.py:513` pueda etiquetarlo (`pcd <= inner_radius_km`
gana y devuelve `"summit"`).

**Muerto por el lado del render**, aunque el dato existiera: el estilo naranja
está en la rama `(isExtension && isFar)` de `:2585`, pero `:2545` ya hizo
`if (isFar && !includeFarDistance) return;`. En la vista por defecto ningún
marcador `far` llega a pintarse. El naranja es **inalcanzable salvo que el
operador prenda "Incluir lejanas"** — y si lo prende, la extensión se pinta
naranja en medio de todas las lejanas grises.

### A8 · CONFIRMADO · severidad MEDIA — el valor 5,00 MW es un cap, y se muestra como si fuera una medición

`PATH_D_ONLY_CAP_MW = 5.0` en el perfil operacional (verificado con
`VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p;
print(p.PATH_D_ONLY_CAP_MW)"`). `pipeline/path_d_cap.py` lo aplica cuando el
path D dispara sobre cirrus, donde la suma cruda llega a 80-510 MW.

En la ventana publicada de 100 días, **479 de 6.599 clusters con VRP > 0 (7,3 %)
valen exactamente 5,000 MW**, y sólo 20 superan ese valor. PCC solo aporta 56 de
esos records. El resultado es que "Max VRP: **5,00** MW" aparece como número
redondo en el panel de detalle de Tupungatito, Nevados de Chillán, Villarrica,
PCC y Chaitén, y en `diario.html` para tres de ellos.

Nada en la pantalla dice que ese 5,00 es un valor **censurado**. Un operador que
compare 5,00 con 4,93 concluirá que el primero es apenas mayor, cuando en
realidad el primero significa «≥ 5, no sabemos cuánto, y probablemente sea
cirrus».

### A9 · CONFIRMADO · severidad MEDIA — el dashboard abre en un volcán vacío

`currentVolcano` arranca en el primer elemento del array `VOLCANOES`, que es
**Taapaca** — uno de los 34 sin data operacional. Verificado en el DOM del sitio
publicado:

```
activeCard: "Taapaca"
detailHead: "Taapaca SIN DATOS ... Max VRP — MW ... Detecciones 0 granules Total granules 0 procesados"
posicionPrimerVolcanConDato: 4 de 45
```

El panel principal —gráficos, mapa, tabla, métricas vs MIROVA— está vacío al
abrir la URL. Como efecto colateral, `#updated-label` (la única etiqueta del
encabezado que diría cuándo se actualizó **el dato**) queda en `""`, porque se
puebla desde `d.updated` del volcán activo y Taapaca no tiene. Verificado:

```
utcClock: "20:18:58 UTC"   (reloj del navegador)
lastRefresh: "🔄 20:18 UTC" (último auto-refresh del navegador)
updatedLabel: ""            (el dato: vacío)
```

Tres relojes en el encabezado y ninguno es el del dato. `mosaico.html` sí lo
hace bien: *"Dato al 2026-09-02 15:05 UTC"*, que es el `max(updated)` real de
los 11.

### A10 · CONFIRMADO · severidad MEDIA — `index` y `mosaico` ubican dos volcanes en la región equivocada

`volcanoes.yaml` **no tiene campo `region`**, así que las tres vistas lo
hardcodean por separado y ya divergieron:

| volcán | `index.html` / `mosaico.html` | `diario.html` |
|---|---|---|
| Lastarria | `region: "Atacama"` (`index:650`, `mosaico:209`) | `region: "Antofagasta"` (`diario:143`) |
| Tupungatito | `region: "Valparaíso"` (`index:652`, `mosaico:210`) | `region: "Metropolitana"` (`diario:144`) |

`diario` es el que está bien en los dos casos: Lastarria (-25,168, -68,507) está
en la Región de Antofagasta y Tupungatito (-33,400, -69,800) en la Región
Metropolitana. Las dos vistas que Nicolás usa como dashboard principal son las
equivocadas. Para un producto que apoya la decisión de alerta de SERNAGEOMIN —
donde la región determina a qué delegación presidencial y a qué SENAPRED
regional escala la información — es un error de credibilidad barato de arreglar
y caro de dejar.

**Recomendación estructural**: mover `region` a `volcanoes.yaml` y que las tres
vistas lo lean de ahí, en vez de tener tres tablas paralelas.

### A11 · CONFIRMADO · severidad ALTA (móvil) — `index` desborda 2,09× el ancho en celular

Con viewport 375×812 (preset mobile) sobre el sitio publicado:

| vista | `clientWidth` | `scrollWidth` | desborde |
|---|---|---|---|
| `index.html` | 375 | **783** | **2,09×** |
| `diario.html` | 375 | **448** | 1,19× |
| `mosaico.html` | 375 | 375 | **ninguno** ✅ |

Los elementos que se salen en `index` son, medidos por
`getBoundingClientRect().right`:

- `.header-right` → 716 px
- `<a>📊 Vista Diaria` → 399 px
- `<a>🧪 Laboratorio` → 510 px
- `<a>⚖️ Comparación` → 632 px
- `<button>ℹ️ Acerca de` → 716 px
- `.overview-map-wrapper` / `.map-controls` / el mapa Leaflet → 420 px

O sea: **los cuatro enlaces a las demás vistas y el botón "Acerca de" quedan
fuera de pantalla en celular**, y el mapa general se corta. `body` tiene
`overflow-x: visible`, así que la página scrollea horizontalmente sin aviso. En
la captura, el logo "VRP Chile · Monitoreo Volcánico · MODIS + VIIRS · NASA
Earthdata · 11 volcanes Tier A MIROVA" se envuelve en **diez líneas** y ocupa
media pantalla antes de mostrar el primer dato.

El turno de las 3 AM que mira el celular es exactamente el caso de uso donde
esto duele. `mosaico.html` demuestra que se puede hacer bien.

### A12 · CONFIRMADO · severidad BAJA — voseo rioplatense en texto visible

- `frontend/comparacion.html:43` — *"**Decidí** cuáles promover al dashboard."*
- `frontend/comparacion.html:91` — *"Acá **podés** comparar el render actual…"*

Formas de tú en Chile: *"Decide cuáles promover"*, *"puedes comparar"*. Hay un
tercer caso (`index.html:2154`, "usá") pero está dentro de un comentario de
código, no se proyecta.

### A13 · CONFIRMADO · severidad MEDIA — la galería "Imágenes MIROVA" está muerta en el sitio publicado

`frontend/mirova_imgs_index.json` tiene `generated_utc: "2026-05-30T14:39:57Z"`
— **95 días de antigüedad** al 2026-09-02. Contenido:

- `tifs`: 11 volcanes × ~200 entradas, con `path` apuntando a
  `../../mirova-tif-archive/data/tif/...`, **fuera del repo**.
- `kmz`: ídem.
- `pngs`: sólo **4 volcanes**, 24 imágenes, fechas **2026-04-25 y 2026-04-26**
  (129 días).

El código lo maneja con elegancia —`archiveAvailable()` (`index.html:1593`)
devuelve `false` en `github.io` y muestra "solo local" en vez de un link roto—
así que no hay error visible. Pero el encabezado de la galería anuncia
*"24 PNGs · 200 TIFs · 200 KMZs"* y en el sitio publicado **ninguno de los 400
TIF/KMZ es alcanzable**. La comparación visual contra la imagen per-volcán de
MIROVA, que es justo lo que A62 recomienda hacer antes de confiar en un número,
no está disponible para el operador.

### A14 · CONFIRMADO en el código · INALCANZABLE con la data — las 4 divergencias entre las copias de `mirovaEqVrp`

*Denominador distinto al resto del informe: 57.851 records de los 11 Tier A del
checkout local, ventana 2025-02-15 01:40 → 2026-09-01 07:06 UTC.*

Las cuatro divergencias que `docs/AUDIT_S125_PROFUNDA.md:216-246` (B4) reportó
**siguen escritas**, y las cuatro producen **0 registros de diferencia**:

| # | `index` / `mosaico` | `diario` | records afectados |
|---|---|---|---|
| a · cap 50.000 en el fallback | `index:975-980` `vfb > 50000 ? 0 : vfb` | `diario:243` `return r.vrp_mw ?? 0`, **sin cap** | **0** — ningún record sin `primary_cluster` pasa de 50.000 MW |
| b · orden de los chequeos | `!pc` primero (`:975`), `distance_class` después (`:985`) | `distance_class` primero (`:241`), `!pc` después (`:243`) | **0** — no existe ningún record con `primary_cluster = null` **y** `distance_class ≠ summit`; los 18.469 sin cluster (31,93 %) tienen todos `distance_class = null` |
| c · `vrp_mir_mw` faltante | `?? r.vrp_mir_mw ?? 0` | ausente | **0** — `vrp_mw` nunca es `None`; nunca se llega al fallback |
| d · default inner 5 vs 10 | `?? 10` | `?? 5` | **0** — `diario:141` cierra la vista a los 11 Tier A, todos en `INNER_RADIUS_KM` |

`mirovaEqVrp_index(r) ≠ mirovaEqVrp_diario(r)` en **0 de 57.851 (0,0000 %)**.
`index:972` y `mosaico:245` son **byte a byte idénticas**. `f5CoreMagnitude`,
`parseUtcMs` y `_havKm` son idénticas en las tres.

O sea: el problema conocido «`diario.html` sin cap de 50.000 MW, redescubierto
cuatro veces» es **cierto en el código y falso en el efecto**. Es una bomba de
tiempo, no un bug activo — y ésa es probablemente la razón por la que se
redescubre: cada auditoría lo encuentra en el texto y ninguna lo mide.

Dos divergencias más, no catalogadas antes, ambas benignas y verificadas:
`mirovaEqVrpCore` de `mosaico:308` cablea `includeFar = false` (coherente: esa
vista no tiene el toggle); y `mirovaEqVrpDisplay` de `index:1096` **no** aplica
el filtro de artefacto mientras `eqVrpDisplay` de `diario:372` y `mosaico:364`
**sí** — `index` lo compensa envolviéndolo en cada uno de sus call sites
(`:1201`, `:1408`, `:1909`), verificados los cuatro. Efecto neto igual.

**Las tablas `inner_radius_km` NO divergen**: los 11 coinciden entre
`volcanoes.yaml`, `index` (`VOLCANOES_ALL`), `mosaico` (`VOLCANOES`) y `diario`
(`INNER_RADIUS_KM`). La divergencia de A10 es sólo del campo `region`, que
`volcanoes.yaml` ni siquiera tiene.

### A15 · CONFIRMADO pero SIN IMPACTO — `auto_audit_weekly` no usa `isValidDetection`, y da igual

`scripts/auto_audit_weekly.py:231-239` usa su propio predicado —
`0 < pc.vrp_mw ≤ 50000` ∧ `centroid_dist_km ≤ inner` ∧
`distance_class ∈ {None, "summit"}` — y **nunca menciona `triggered_test1`**,
frente a `frontend/index.html:1371`.

Comparados sobre los mismos 57.851 records: `isValidDetection` da 37.200
positivos (64,30 %), el predicado del audit 24.338 (42,07 %), y **discrepan en
12.892 (22,28 %)**, casi todos en una dirección (12.877 son sí-frontend /
no-audit; 2.419 de ellos disparan sólo por `triggered_test1` con `vrp_mw = 0`).

**Pero `isValidDetection` no es el gate del gráfico.** El gate efectivo del
dashboard —filtro de artefacto ∧ `mirovaEqVrpDisplay > 0`— da **24.338, exactamente
el mismo conjunto que el audit, con 0 desacuerdos**. `isValidDetection` es un
guard adicional que aplican los paneles (`:1405`, `:1450`, `:1532`, `:1970`,
`:2149`, `:2760`, `:2814`, `:3158`, `:3304`) pero **no** `buildDatasets`
(`:1909`) ni `computeMetrics` (`:1201`). El audit semanal y lo que Nicolás ve
graficado miden lo mismo. El problema conocido queda **confirmado en la letra y
descartado en el efecto**.

Cola fina, sí real: **15 records** (14 de Villarrica MODIS + 1 de PCC) tienen
`vrp_mw = 0` con `discarded_reason` (`cluster_too_large_for_volcano`,
`eruption_hotspot_too_far`) pero `pc.vrp_mw > 0` dentro del inner. Entran al
gráfico y al audit y quedan fuera de la tarjeta. Es la asimetría A46 en
miniatura, sobre 57.851: despreciable.

### A16 · CONFIRMADO · severidad MEDIA — el filtro de artefacto térmico S90/S93 está inerte

Hallazgo colateral, y converge con A7: `isThermalArtifact` (cirrus S90 ∨ campo
difuso S93) devuelve `true` en **0 de 57.851 records**.

- Hay **4.304** records con `t_max_k < 273,15` y `eqVrp > 0` — pero **ninguno**
  supera los 10 MW que exige el gate cirrus (`index:1115`).
- Hay **256** con `t_max_k < 278,15` ∧ `n_pixels ≥ 100` — pero **ninguno**
  alcanza `VRP ≥ 50 ∧ VRP/px < 1,0` (`index:1137`).

Los dos umbrales se calibraron en S90/S93 contra magnitudes que el sistema ya no
produce: hoy el máximo absoluto de la ventana publicada es 13,60 MW (B1) y el
cap del path D corta en 5,0 (A8). Es un caso de manual de **A87**: el filtro no
marca nada y eso se lee como «ya no hay artefactos», cuando lo que pasó es que
el rango de magnitudes se movió por debajo del umbral. Candidato a recalibrar
tras el retiro del piso VRP de S130 — **pero no en esta sesión y no sin A/B**:
bajar esos umbrales es exactamente el tipo de gate que A55 y A83 desaconsejan
sin estratificar por régimen.

### A17 · PARCIALMENTE OBSOLETO — `audit_metrics.mirova_eq_vrp()` ya no diverge, pero sigue muerta

`docs/AUDIT_S125_PROFUNDA.md` B3 decía que el helper de Python estaba muerto
**y** divergido de las copias JS. La cara «divergida» está **refutada**: S126 le
agregó `SANITY_CAP_VRP_MW = 50000` (`pipeline/audit_metrics.py:64`, `_cap()`
`:67`) y hoy da **0 desacuerdos** con el frontend y con `auto_audit_weekly`
sobre los 57.851 records. Hay además un test que lo fija
(`tests/test_audit_metrics_paridad_frontend_s126.py`).

La cara «muerta» sigue **confirmada**: `grep` de `mirova_eq_vrp`,
`audit_metrics.` e imports con alias sólo encuentra los dos tests y tres
experimentos de S90-S92. `auto_audit_weekly.py` **no la importa** — importa
`mirova_csv_loader`, `store` y `profile`. Está correcta y nadie la usa.

### A18 · OBSOLETO — los tres bugs de S129/PR #569-570 están cerrados

Los verifiqué en el sitio publicado en vez de heredarlos:

- **Barra "Estado actual" congelada** → hoy lee `0 Alto · 0 Moderado · 0 Bajo ·
  11 Muy Bajo · 34 Sin datos`, coherente con las 45 tarjetas del DOM.
- **`mosaico` "Actualizado" = reloj del navegador** → hoy muestra
  *"Dato al 2026-09-02 15:05 UTC"*, que es el `max(updated)` real de los 11
  (`NevadosDeChillan` 15:00:51, `Copahue` 15:05:02).
- **`index` y `mosaico` con distinto nivel de alerta** → **cerrado**. Las 11
  cifras coinciden exactamente entre las dos vistas y con mi recómputo:
  0,07 · 0,21 · 0,06 · 0,02 · 0,02 · 0,02 · 0,02 · 0,03 · 0,04 · 0,25 · 0,09.
  `mosaico.html:373-410` porta ahora `isValidDetection`, `isSummitDetection` y
  `latestVRP` sincronizados con `index`.
- **VRE: caja vs curva** (hallazgo #2 de S129) → cerrado por S130. La caja de
  Villarrica dice 686,5 GJ y mi recómputo con `eqVrp` da 686,5 GJ; el comentario
  de `index.html:2779-2790` documenta el cambio de `r.vrp_mw` a `eqVrp(r)`.

### A19 · FALSO — el deploy no está desfasado, y la carga no está rota

- `index.html` publicado vs repo: **idéntico byte a byte** tras normalizar
  CRLF→LF (203.943 = 203.943). El repo local es CRLF; GitHub Pages sirve LF.
- Los `_recent.json` **sí existen** en el sitio publicado
  (`Last-Modified: Wed, 02 Sep 2026 16:54:32 GMT`, 3,27 MB Villarrica) y llevan
  `_recent_window_days: 100`. Localmente no existen —están en `.gitignore:115` y
  los genera `scripts/build_recent_json.py` dentro de `pages-deploy.yml:76`—
  así que el preview local cae por el fallback al JSON completo. Los 11 x 404 de
  `*_recent.json` que aparecen en la consola local son **esperados**, no un bug.
- Rendimiento real del sitio publicado: 11 requests, **5,3 MB transferidos**
  (gzip), `domContentLoaded` 57 ms, **última respuesta de data a los 166 ms**. La
  más lenta es `NevadosDeChillan_recent.json` con 110 ms. La carga está sana.
- **0 errores de consola y 0 requests fallidos** en las cuatro vistas publicadas.

### A20 · SIN RESPALDO / no aplica — tema claro

El sitio es **dark-only deliberado**: `body` pinta `rgb(26,26,46)` explícito y no
hay ninguna regla `prefers-color-scheme` en la hoja embebida (verificado). Con
`colorScheme: light` emulado el sitio se mantiene oscuro y legible. Para un
turno nocturno es la elección correcta; no lo reporto como defecto.

---

## Parte B · ¿Le sirve al turno de OVDAS?

Ordenado por impacto en la decisión de alerta, no por elegancia.

### B1 · El badge de alerta es una constante: 100 % "Muy Bajo" en 4.279 ventanas

Barrí ventanas rodantes de 48 h cada 6 h sobre los 100 días publicados,
recomputando el nivel que habría mostrado cada tarjeta:

| volcán | Sin datos | **Muy Bajo** | Bajo | Moderado | Alto | n |
|---|---|---|---|---|---|---|
| los 11, cada uno | 0,0 % | **100,0 %** | 0,0 % | 0,0 % | 0,0 % | 389 c/u |
| **TOTAL** | 0,0 % | **100,0 %** | 0,0 % | 0,0 % | 0,0 % | **4.279** |

Ni una sola ventana, en ningún volcán, en 100 días, alcanzó "Bajo". La escala
que el dashboard muestra en la leyenda —*Muy Bajo <1 · Bajo 1-10 · Moderado
10-100 · **Alto >100 MW***— está calibrada para el rango global de MIROVA, donde
un lago de lava del Nyiragongo da 10³ MW. Nuestros once volcanes viven, hoy, en
el piso: el **máximo absoluto de los 100 días es 13,60 MW** (PCC, MODIS Terra,
2026-06-06 02:35 UTC), y sólo 20 de 6.599 clusters pasan de 5 MW.

Consecuencia operacional: **la tarjeta no discrimina**. El operador que la mira
cada noche aprende, correctamente, que siempre dice lo mismo — y deja de
mirarla. Cuando algún día diga "Bajo", nadie lo va a notar porque el color
apenas cambia dentro de una banda que ocupa tres órdenes de magnitud.

**Lo que falta**: un eje de **anomalía respecto de la propia línea de base del
volcán**, no de la escala global. Villarrica pasando de 0,04 a 0,40 MW es un
factor 10 sobre su propio fondo y sigue diciendo "Muy Bajo"; eso es justamente
lo que un turno necesita ver. Es fix de frontend puro: percentil móvil de los
últimos 30-90 días por volcán, ya calculable con la data que se baja.

### B2 · El operador no puede saber si MIROVA también lo vio, salvo pinchando marcador por marcador

`_mirova_confirmed` se computa en el cliente (`index.html:1310-1360`: mismo
bucket de sensor, ±60 min) y **sólo se pinta en dos lugares**: el anillo del
marcador (`:2609`) y el popup del mapa (`:2632`). `grep -n "_mirova_confirmed"`
sobre las cuatro vistas confirma que **no aparece** en la tarjeta, ni en la
tabla "Últimas detecciones", ni en `mosaico`, ni en `diario`.

Repliqué el cruce offline. De lo que el dashboard **muestra**:

| volcán | detecciones visibles 90 d | con alerta MIROVA de la misma pasada | % |
|---|---|---|---|
| Láscar | 276 | 198 | **71,7 %** |
| Isluga | 394 | 224 | 56,9 % |
| Lastarria | 194 | 74 | 38,1 % |
| Tupungatito | 314 | 92 | 29,3 % |
| Planchón-Peteroa | 313 | 78 | 24,9 % |
| Puyehue–Cordón Caulle | 655 | 145 | 22,1 % |
| Chaitén | 415 | 56 | 13,5 % |
| Villarrica | 374 | 35 | 9,4 % |
| Nevados de Chillán | 229 | 10 | 4,4 % |
| Copahue | 372 | 7 | **1,9 %** |
| Llaima | 339 | **0** | **0,0 %** |
| **TOTAL** | **3.875** | **919** | **23,7 %** |

Tres de cada cuatro puntos en pantalla no tienen alerta MIROVA equivalente. Eso
**no** los hace falsos —según A54 alrededor del 46 % son features volcánicas
reales que MIROVA no publica, y ése es el valor agregado del proyecto— pero el
operador no tiene forma de separar los grupos sin abrir un popup a la vez.

**Fix de frontend puro, alto impacto**: una columna «MIROVA» (▲ / —) en la tabla
"Últimas detecciones" y un contador en la tarjeta («7 detecciones 48 h · 2
corroboradas por MIROVA»). El dato ya está calculado en memoria.

### B3 · No hay forma visual de distinguir cat-b real de artefacto

Es A7 mirado desde el turno. Las tres categorías que la metodología del proyecto
distingue con claridad —alerta MIROVA-equivalente, señal real sub-umbral
(lava lake de Villarrica, fumarolas de Lazufre, lacolito de PCC), y artefacto
(topográfico A69, cirrus D9)— llegan a la pantalla **con el mismo color rojo**.

Los mecanismos existen y ninguno opera en la vista por defecto:

| mecanismo | estado |
|---|---|
| `geo_class = "extension"` → naranja | **0/11.599** records; y la rama sólo corre si `isFar`, que se descarta antes (A7) |
| `isCirrusArtifact` / `isDiffuseFieldArtifact` | **0/57.851** — umbrales por encima del rango de magnitudes actual (A16) |
| `_mirova_confirmed` → anillo verde | vivo, pero sólo en el mapa y sólo en el popup (B2) |
| cap `PATH_D_ONLY_CAP_MW = 5.0` | se muestra como número normal, sin marca de valor censurado (A8) |

De los cuatro, **dos no producen nada y uno está escondido**. El único que
opera —el cap— opera en silencio.

Lo único que hoy le permite al operador sospechar es la tabla del detalle, que
muestra **T MAX** y **T FONDO** por record. Ejemplo real de Láscar
(2026-09-02 06:06): `T MAX 8,2 °C · T FONDO −10,1 °C`. Un geólogo lee ahí que no
hay roca fundida expuesta —8 °C no es lava— y que el contraste es de 18 K sobre
un fondo bajo cero. Eso es información de primera calidad y está enterrada en la
quinta columna de una tabla que hay que ir a buscar. **Súbanla a la tarjeta.**

### B4 · Qué NO ve este sistema: no está escrito en ninguna parte

El modal "Acerca de" es excelente en atribución (Coppola, Wooster, los siete
papers canónicos, la advertencia A9 sobre Di Bella/INGV Catania) y en métricas
(recall VIIRS375 98,4 %, paridad 9/11 en banda). Pero un `grep` sobre sus 5.780
caracteres da:

- `/limitac|no detecta|falso/i` → **false**
- `/CPLT|372|transparen|algorítmic/i` → **false**

Faltan las dos cosas que un operador necesita antes de decidir:

1. **Qué significa un cero.** Una erupción explosiva o freática sin lava
   expuesta es **térmicamente invisible** al MIR (A78: si `nti_max` no sube de
   ~−0,9 en ningún sensor, no hay material caliente resoluble). Un foco
   incandescente sub-píxel para 375 m puede ser perfectamente visible en SWIR de
   alta resolución (A77: el caso de Nevados de Chillán en junio 2026, con
   Sentinel-2 `NPixHot = 6` y VIIRS marginal). El MIR sólo sirve de noche. Nada
   de esto está en pantalla. Un operador que lea "sin detección" y concluya "el
   volcán está tranquilo" estará equivocado en toda una clase de erupciones.
2. **La ficha de transparencia algorítmica.** El proyecto se declara SDA en
   scope de la Resolución CPLT N°372 y mantiene
   `docs/FICHA_SDA_VRP_CHILE.md` como documento *publicable*. El dashboard es la
   única cara pública del sistema y **no la enlaza**. Es un link, no un
   desarrollo.

Además, las métricas del modal son **texto fijo con fecha S119 (2026-07-01)**,
63 días atrás. Están bien, pero envejecen sin avisar — a diferencia de las cajas
Recall/Precision/F1 del panel de detalle, que sí se recalculan en vivo.

### B5 · La grilla: 34 de 45 tarjetas son relleno permanente

El operador entra y ve 45 tarjetas, de las cuales **34 dicen "Sin datos · sin
datos (no monitoreado)"** y siempre lo van a decir: `loadVolcano()`
(`index.html:895`) corta con `if (!v.hasMirova) return` y ni siquiera intenta
bajarlas. La primera tarjeta con dato es la **#4** de 45.

Dos consecuencias:

- **Ruido de escaneo**: para encontrar los 11 que importan hay que recorrer
  visualmente toda la grilla. Los volcanes están ordenados norte→sur, así que
  los 11 quedan intercalados entre los 34 vacíos.
- **Una afirmación imprecisa**: los 34 sí tienen data en el repo — entre 67 y 94
  records cada uno, del **2026-04-17 al 2026-04-24**, con 3 a 32 detecciones
  (Laguna del Maule 32, Antuco 24, Olca-Paruma 22). "Sin datos" describe el
  estado del **monitoreo**, que es lo correcto operacionalmente, pero la
  semana de abril existe y no es alcanzable desde ninguna vista.

**Recomendación**: colapsar los 34 detrás de un desplegable «34 volcanes sin
monitoreo NRT» al pie de la grilla. La barra "Estado actual" ya los cuenta
aparte.

### B6 · Los clics para responder las cinco preguntas del turno

| pregunta | dónde está | clics |
|---|---|---|
| ¿QUÉ volcán? | tarjeta, tras recorrer 45 | 0 (visual) |
| ¿CUÁNTO? | tarjeta, `0.25 MW` | 0 |
| ¿DESDE CUÁNDO? | tarjeta, timestamp UTC + hora Chile | 0 |
| ¿QUÉ sensor? | pills de la tarjeta (grupo, no el satélite) | 0 |
| ¿A QUÉ distancia? | tarjeta, pero es el ancla (A4) | 0 |
| **¿MIROVA lo vio?** | popup de un marcador del mapa | **3+** |
| **¿es real o artefacto?** | T MAX/T FONDO, tabla del detalle | **2** |
| **¿cuántas pasadas detectaron en 48 h?** | no está en ninguna vista | **∞** |
| **¿el pico de las 48 h?** | hay que leer el gráfico | **2** |
| **¿el NRT está al día?** | badge por tarjeta (bien) — y el header lo contradice (A1) | 0 |

Las cinco primeras están resueltas y bien resueltas: la tarjeta de `index` es
compacta, tiene la hora local de Chile *y* la UTC, el nivel, el sensor, la
extensión en píxeles y la frescura del monitoreo. Eso es mejor que la tarjeta de
mirovaweb. Las cuatro que faltan son justamente las que deciden si se escala una
alerta.

### B7 · Latencia pasada → dashboard: ~3 h de proceso, ~10 h de espera

Nunca se había medido. Primero, la mala noticia metodológica: **el record no
tiene ningún sello de tiempo de proceso**. De sus 75 claves, cero coinciden con
`ingest|process|created|updated|fetch|_at`. El único sello es `updated`, a nivel
de archivo. Así que la latencia por record no es medible hoy — arreglarlo cuesta
un campo en `store.py`.

Con lo que hay (una medición por volcán por snapshot, n = 11):

| tramo | mediana | p90 | rango |
|---|---|---|---|
| última pasada → `updated`, snapshot local (2026-09-01) | **3,08 h** | 3,13 h | 2,46 (Chaitén) – 7,82 (PCC) |
| última pasada → `updated`, snapshot publicado (2026-09-02) | 7,76 h | 8,38 h | 7,67 – 8,38 |
| **pasada → publicado en GitHub Pages** | **10,21 h** | 10,81 h | — |
| `updated` → deploy | — | — | 1,82 – 2,56 h |

El número honesto de **latencia de proceso es el local: ~3 h**, consistente con
LANCE NRT (~3 h de latencia propia) más el cron cada 2 h. Los 7,76 h del
snapshot publicado son mayormente **espera de la próxima pasada**, no proceso: el
hueco entre pasadas consecutivas en los últimos 30 días tiene **p90 ≈ 17,1-17,3 h**
(máximo 20-22 h), porque el MIR es sólo nocturno.

Para el turno esto significa una cosa concreta que el dashboard no dice: **entre
dos oportunidades de ver un cambio térmico pueden pasar 17 horas**, y no es una
falla del sistema, es la órbita. El badge de frescura por tarjeta (bueno, A1)
pone el umbral ámbar en un valor que no distingue «el NRT se cayó» de «todavía
no amanece del otro lado». Recomendación: que el badge diga «próxima pasada
esperada ~HH:MM» en vez de sólo «hace N h».

### B8 · Lo que sí está bien y no hay que tocar

Vale tanto como los hallazgos, porque evita trabajo inventado:

- **La tabla del detalle es lo mejor del dashboard.** `FECHA UTC · SENSOR ·
  ZONA · VRP · DIST · T MAX · T FONDO · PÍXELES`, con el satélite concreto
  (`VIIRS_NOAA21` vs `VIIRS_NOAA21_750`), `🎯 Dentro` como etiqueta de zona y la
  palabra `cráter` en vez de un `0,00` engañoso. Es exactamente el nivel de
  detalle que un geólogo necesita.
- **Las métricas vs MIROVA por sensor, en vivo**, con TP/FP/FN explícitos:
  Láscar VIIRS375 `Recall 0,95 (TP=20 FN=1) · Precision 0,53 (TP=20 FP=18) ·
  Ratio med 0,53× (N=20 pares)`. Ningún sistema comparable publica su propia
  precisión en la misma pantalla que el dato.
- **`diario.html` es la vista más honesta del conjunto**: pone la serie nuestra
  contra la referencia MIROVA desglosada por sensor, con las tres líneas
  discontinuas del mismo color, y el conteo crudo al lado
  («Copahue: 372 det. nuestras · MIROVA: 3 alertas»). Ese 124× es incómodo y
  está a la vista, que es como corresponde.
- **La frescura por tarjeta** (`monitoringFreshness`) funciona y distingue
  «monitoreado · tranquilo» de «datos atrasados». Es el modelo que debería
  seguir el encabezado.
- **La carga y el deploy** (A15).
- **El modal "Acerca de"** en atribución y trazabilidad metodológica.
- **`mosaico.html` en móvil**: 375/375, cero desborde. Es la prueba de que el
  problema de `index` es arreglable.
- **`comparacion.html` sin `mirovaEqVrp`** es deliberado y está rotulado como
  preview; no lo toqué (`docs/AUDIT_S127.md:170`).

---

## Recomendaciones

Ordenadas por relación impacto/costo. Marco cuál es frontend puro y cuál toca
pipeline o configuración.

### Frontend puro — se pueden hacer todas en una sesión

| # | qué | dónde | cómo validarlo |
|---|---|---|---|
| **R1** | Alimentar el semáforo del encabezado con `min(monitoringFreshness)` de los 11, y que pueda ponerse ámbar/rojo. O borrarlo. | `index.html:378-379` | Congelar la data 40 h atrás y verificar que el punto deja de estar verde (hoy no lo hace: A1) |
| **R2** | Rotular las dos ventanas. Tarjeta: «última pasada»; detalle: «máximo 30 d». Y mostrar en la tarjeta «última X MW · máx 48 h Y MW». | `index.html:1806` y `:1921` | Recorrer los 11 y comprobar que ningún par tarjeta/detalle muestra dos badges sin rótulo (hoy los 11: A2, A3) |
| **R3** | Columna «MIROVA» (▲/—) en la tabla "Últimas detecciones", y contador en la tarjeta. | `index.html:2155-2200`; el dato ya está en `r._mirova_confirmed` | Cruzar contra `experiments/_s131_audit/dashboard/confirmadas.py`: debe dar 23,7 % en 90 d |
| **R4** | Corregir el tooltip de distancia y escribir «en el cráter (ancla Test 1)» en vez de «0,0 km», como ya hace la tabla. | `index.html:1846` | Las 7 tarjetas hoy en `test1_roi` deben dejar de decir «0,0 km del cráter» (A4) |
| **R5** | Subir T MAX / T FONDO a la tarjeta. Es el único discriminante físico que el operador tiene hoy. | `index.html:1830-1860` | Comparar contra la tabla del detalle del mismo volcán (B3) |
| **R6** | Arreglar el móvil de `index`: `flex-wrap` en `.header-right`, `overflow-x:auto` en `.map-controls`, `overflow-x:hidden` en `body`. Copiar de `mosaico`. | `index.html` CSS | `document.documentElement.scrollWidth` debe bajar de 783 a 375 con viewport 375 (A11) |
| **R7** | Arrancar en el primer volcán **con data** en vez de Taapaca, y colapsar los 34 sin monitoreo. | `index.html` init + `buildCards()` | El panel de detalle no debe decir «SIN DATOS» al abrir la URL (A9, B5) |
| **R8** | Marcar el 5,00 MW como valor censurado (asterisco + tooltip «cap path D, cirrus»). | donde se formatea VRP | 479/6.599 records (7,3 %) deben quedar marcados (A8) |
| **R9** | Corregir la región de Lastarria y Tupungatito en `index` y `mosaico`. | `index:650,652`; `mosaico:209,210` | Contra `diario:143-144`, que es el correcto (A10) |
| **R10** | Español de Chile en `comparacion.html`. | `:43`, `:91` | (A12) |
| **R11** | Enlazar `docs/FICHA_SDA_VRP_CHILE.md` y agregar al modal una sección **«qué NO ve este sistema»** (explosiva sin lava expuesta A78; sub-píxel que pide SWIR alta-res A77; sólo noche; nubes). | modal "Acerca de" | `grep` sobre el texto del modal debe encontrar «limitaciones» y «CPLT» (B4) |
| **R12** | Eje de anomalía respecto de la línea de base del propio volcán (percentil móvil 30-90 d), al lado del nivel MIROVA absoluto. | nuevo, en la tarjeta | Debe distinguir situaciones que hoy son las 4.279 ventanas idénticas (B1) |
| **R13** | En el badge de frescura, «próxima pasada esperada ~HH:MM» además de «hace N h», para separar «el NRT se cayó» de «todavía no hay órbita» (hueco entre pasadas p90 ≈ 17 h). | `monitoringFreshness()` | Contra el histograma de huecos de `t3_latencia.py` (B7) |

### Necesita `volcanoes.yaml`, configuración o un campo nuevo (no toca detección)

- **R14** — mover `region` a `volcanoes.yaml` y que las tres vistas lo lean de
  ahí. Elimina la clase de bug de R9 en vez de parchear dos casos.
- **R15** — poblar `pipeline/volcanic_features.yaml` para los 11 (hoy sólo PCC y
  Lastarria) **y** resolver el caso PCC: con `inner_radius_km = 20` el lacolito
  nunca puede etiquetarse `"extension"` porque `store.py:513` lo resuelve como
  `"summit"` primero (`pcd <= inner_radius_km` gana). Sin esto, R16 no tiene con
  qué pintar.
- **R16** — hacer alcanzable el marcador naranja: sacar `isExtension` de la rama
  `(isExtension && isFar)` de `index.html:2585`, para que una extensión
  catalogada se pinte naranja **también dentro** del inner radius. Es lo que la
  pestaña 3 de `comparacion.html` viene proponiendo desde S115 y es lo que
  resuelve el 82,3 % de PCC (A6). **Ojo A55**: no es un gate que filtre
  detecciones — es sólo color; magnitud y detección quedan intactas.
- **R17** — agregar un sello de tiempo de proceso al record en `store.py`. Hoy
  no existe ninguno de las 75 claves, así que la latencia sólo se puede estimar
  por archivo (B7). Un campo hace medible el SLA del NRT.

### Bajo prioridad, con reserva

- **R18** — recalibrar los umbrales de `isCirrusArtifact` (>10 MW) y
  `isDiffuseFieldArtifact` (VRP ≥ 50) de S90/S93, hoy inertes sobre 57.851
  records (A16). **Con reserva expresa**: bajar un umbral de supresión es
  exactamente lo que A55 llama anti-patrón y lo que A83 muestra que destruye
  cat-b real cuando se hace con un escalar global. Si se toca, va con A/B
  estratificado focal/nevado y midiendo FN sobre cat-b confirmado — no como
  ajuste de display.

### Necesita reactivar un pipeline externo

- **R19** — `mirova-tif-archive`: el polling está parado y el índice congelado
  hace 95 días, con los TIF/KMZ fuera del alcance del sitio publicado (A13).
  Sin esto, la comparación visual contra MIROVA que A62 pide como control no
  existe para el operador. Fuera del scope de este eje, pero es la capacidad
  dormida de mayor valor para la parte B.

### Lo que NO recomiendo tocar

- **No revertir S90/S130** («última pasada» en la tarjeta). Es decisión de
  Nicolás y tiene sentido operacional: la tarjeta describe el **estado actual**,
  no un pico que ya pasó. El arreglo es mostrar las dos cifras (R2), no cambiar
  cuál manda.
- **No agregar ningún gate ni filtro nuevo** al pipeline a partir de esta
  auditoría. Todo lo de arriba es display. La sobre-detección de fondo (3.875
  detecciones visibles contra 919 corroboradas) es el frente A54/A68/A82, ya
  auditado y cerrado por la vía espectral; reabrirlo desde el dashboard sería
  anti-A8.
- **No "arreglar" `comparacion.html`** replicándole `mirovaEqVrp`
  (`docs/AUDIT_S127.md:170`).

---

## Lo que no pude verificar

- **La confirmación MIROVA de los records `far`.** El cruce
  `_mirova_confirmed` es enriquecimiento de cliente; lo repliqué offline para
  los visibles (B2) pero no separé la rama `far` con la misma tolerancia. La
  columna «n far MIROVA-conf = 0» que salió en la corrida de D13 **no es una
  medición válida** y no la uso como argumento.
- **El último punto de la curva "VRE acumulada"** contra la caja: el gráfico
  sólo se construye cuando su pestaña está activa y mi extracción no lo capturó.
  Sí verifiqué que **la caja** coincide con mi recómputo usando `eqVrp`
  (Villarrica 686,5 · PCC 2.847,5 · Láscar 206,4 GJ), que es el campo al que
  S130 alineó la curva. La paridad es muy probable pero no la observé.
- **El comportamiento con «180 días» / «Todo»**, que dispara la descarga del
  JSON completo (~171 MB los 11). No lo ejercité; la latencia de ese camino
  queda sin medir.
- **`frontend/experimental/`** («Laboratorio»), fuera del encargo.
- **La latencia por record**: no hay sello de proceso en el schema (B7). Los
  números de esa sección son **entre volcanes en un snapshot**, no percentiles
  entre corridas, y no aíslan el tramo commit → deploy (git prohibido en este
  eje).

---

## Nota de denominadores (A90)

Este informe mezcla dos corpus y los rotula en cada tabla:

| corpus | n | ventana | usado en |
|---|---|---|---|
| `_recent.json` publicados, bajados 2026-09-02 16:10 UTC | **11.599** records, 11 vols | 100 días (2026-05-25 → 2026-09-02) | A2-A8, B1-B3, B5, todas las cifras de mapa y ventanas rodantes |
| checkout local `data/mirova_equivalent/` | **57.851** records, 11 vols | 2025-02-15 01:40 → 2026-09-01 07:06 | A14-A17, B7 |

No son comparables entre sí: el segundo incluye el backfill histórico de 2025
que S120 agregó (A90 — el corpus creció hacia atrás). Cuando un número de este
informe se compare con uno de una auditoría futura, hay que reconstruir primero
la ventana.

## Scripts

Todos en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s131_audit\dashboard\`,
read-only sobre el repo:

| script | qué mide |
|---|---|
| `replicate_frontend.py` | puerto verbatim de los 10 predicados de `index.html`; genera `expected.json` / `expected_pub.json` |
| `operator_signal.py` | nivel de la tarjeta en 4.279 ventanas rodantes de 48 h (B1) |
| `last_vs_max.py` | última pasada vs máximo de 48 h (A3) |
| `map_points.py` | marcadores, coordenadas distintas, `test1_roi` (A5) |
| `far_and_distance.py` | D13 y distribución de distancias visibles (A6) |
| `confirmadas.py` | réplica offline de `enrichWithMirovaConfirmation` (B2) |
| `t1_helper_diff.py` | diff semántico de los helpers en las 3 vistas (A14) |
| `t2_predicate.py` | `isValidDetection` vs el predicado del audit (A15-A17) |
| `t3_latencia.py` | latencia pasada → `updated` → publicado (B7) |
