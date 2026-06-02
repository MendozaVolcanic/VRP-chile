# S97 — Causa raíz Tupungatito: el ancla de clustering es el centro del grid KMZ, no el cráter

**Corrige mi conclusión previa S97** (dije "Tupungatito coincide con MIROVA, no es bug
nuestro"). Estaba MAL: mi R2 usaba el centroide ponderado de TODO el TIF, que se estira
con el campo difuso + una fuente lejana a 21 km, y caía en el centro del grid. Medido
BIEN (radiancia local), MIROVA ve el calor EN EL CRÁTER.

## Evidencia

### El TIF de MIROVA ve el calor en el cráter (norte), no al sur
Radiancia del TIF VIIRS375 (20260512) sumada en radio 3 km de cada candidato:
- **Cráter (vent_lat -33.389,-69.826): radiancia máx 0.482, suma 45.1** ← la más fuerte
- GVP (-33.4,-69.8): máx 0.308, suma 26.7
- mirova_center (-33.427,-69.800): máx 0.415, suma 23.4

El TIF está georreferenciado EPSG:4326; sus **bounds están centrados en el mirova_center**
(grid 50×50 km). El cráter cae 4.86 km al NORTE del centro del grid. MIROVA centra su
imagen en el grid pero el calor está en el cráter (norte).

### Nuestras detecciones caen al sur (grid center), salvo cuando aíslan el cráter
Records 2026-05-12: la mayoría de píxeles a ~7 km del cráter, BT 262-263 K (−11 °C,
glaciar), cerca del mirova_center. PERO la pasada 05:36 detectó 1 píxel **a 0.10 km del
cráter, 271 K** — y quedó con `pc_dist=4.80` (medido desde mirova_center) → el cluster sur
le ganó como primario y el cráter real quedó etiquetado "lejos".

## Causa raíz (bug de config, no de algoritmo)
`pipeline/geo_utils.py:get_effective_vent()` devuelve `mirova_center` con **prioridad 1**,
cayendo al `vent` (cráter real) solo si mirova_center no está. Para Tupungatito el
`mirova_center` (extraído del LatLonBox del KMZ, S80) es el **centro del grid**, 4.86 km al
SUR del cráter. Ese eff_vent se usa para:
- anclar el clustering vent_anchored (inner_radius alrededor de eff_vent),
- la detección vent-path (distancia por píxel desde eff_vent),
- la distancia reportada (`centroid_dist_km` desde eff_vent).

→ El clustering ancla al sur, selecciona el cluster glaciar del sur, y el cráter real
queda "far". La distancia `centroid_dist_km` mide desde el sur, así que parece chica
("0.8 km") aunque la señal esté a ~5-7 km del cráter.

## Alcance: proporcional al offset mirova_center↔cráter
| Volcán | offset | impacto esperado |
|---|---|---|
| PuyehueCordonCaulle | 7.57 km | alto (pero lacolito difuso A20, "cráter" difuso) |
| Tupungatito | 4.86 km | alto — confirmado |
| PlanchonPeteroa | 2.02 km | medio (multi-cráter A22) |
| resto (8 vols) | <0.55 km | despreciable |

La preocupación de Nicolás ("puede pasar en todos") es correcta para los de offset grande;
en los demás el offset es <0.55 km y no desplaza.

## Fix propuesto (A45 — requiere OK + reproc, NO aplicado)
Opción A: invertir prioridad en `get_effective_vent` → preferir `vent` (cráter morfológico
verificado por Nicolás) sobre `mirova_center`. Mantener mirova_center solo para el EXTENT
del grid (no como ancla).
Opción B: corregir el `mirova_center_lat/lon` de Tupungatito/PCC/PP al cráter real
(el grid KMZ no debe ser el ancla).
Ambas tocan clustering/distancia de TODOS los vols → validar con reproc (A18: preview
offline NO predice cluster selection) que no rompe los bien-calibrados (<0.55 km no
deberían cambiar) y que Tupungatito/PCC/PP re-anclan al cráter. Brainstorming + A45 + tests.

## Generalización confirmada (TIF radiancia local vs nuestra ubicación)
| Volcán | offset | TIF<3km cráter vs grid | nuestra detec mediana al cráter |
|---|---|---|---|
| Tupungatito | 4.86 | 26.4 > 18.1 | **5.86 km (corrido)** |
| PCC | 7.57 | 33.9 > 28.2 | **5.46 km (corrido)** |
| Planchón | 2.02 | 22.9 ≈ 26.2 | 2.45 km |
| Lascar | 0.83 | 62.7 | 0.19 km ✓ |
| Villarrica | 0.54 | 31.7 | 0.99 km ✓ |
Donde el offset es chico (<1 km) clavamos el cráter; donde es grande (Tupun, PCC)
detectamos ~5.5 km corrido, mientras MIROVA ve el calor en el cráter.
KMZ = GroundOverlay (mismo recuadro que el TIF, centrado en el grid); no trae punto de
hotspot. La ubicación real de MIROVA = el pico de radiancia DENTRO de la imagen = el cráter.

## ⚠️ CORRECCIÓN CRÍTICA (la imagen propia de MIROVA): el TIF es el campo de fondo, NO la anomalía
Al renderizar el PNG del KMZ (la imagen propia de MIROVA, georreferenciada) se ve que el
TIF/PNG es el **campo de radiancia MIR de TODA la escena**, dominado por la TOPOGRAFÍA:
valles bajos O/SO = rojo (cálido), summit glaciado central = azul (frío). Los píxeles más
"calientes" del TIF son los valles a ~20 km, no la anomalía volcánica. **El TIF NO es el
mapa de anomalías** — es la radiancia de fondo (A24, confirmado visualmente).

→ **Toda mi auditoría espacial R2 (ambas rondas) midió el fondo topográfico, no la
ubicación de la anomalía volcánica de MIROVA. Esas conclusiones espaciales NO son válidas.**
No se puede ubicar la anomalía de MIROVA desde el centroide/sumas del TIF. La anomalía
volcánica es un realce LOCAL de NTI/dNTI sobre el fondo, invisible como "el píxel más
brillante".

### Lo que SÍ sabemos (evidencia, no inferencia)
- MIROVA detecta Tupungatito (109 ALERTAs CONS+OCR), reporta dist CONSISTENTE ~5.21 km
  (91/109 a ~5 km), VRP mediana 0.20 MW, casi todo "Muy Bajo". Referencia de esa distancia
  = INCIERTA (¿GVP? ¿computada por el scraper Mirova-v1? cambia la interpretación).
- Literatura (Coppola 2016a): MIROVA usa NTI/dNTI, NO umbral T<0; NO hay vent-anchored
  cluster selection documentado; usa dual-ROI (summit ≤5km más sensible).
- Nicolás (autoridad de dominio): MIROVA muestra la anomalía EN el lago cratérico; nuestro
  mapa la muestra al sur.
### Lo que NO sabemos (pendiente de prueba)
- La posición lat/lon exacta donde MIROVA reporta la anomalía de Tupungatito por pasada.
- Desde qué punto se miden los 5.21 km.
- Si nuestras detecciones al sur coinciden o no con MIROVA (la dist ~5 km es sospechosamente
  parecida a la nuestra → podríamos estar coincidiendo, o ambos sobre el glaciar).
→ Próximo paso: obtener la posición real de MIROVA (mapa web vía Chrome, o guía de Nicolás)
ANTES de proponer cualquier fix. NO concluir más desde el TIF.

## RESOLUCIÓN (hipótesis Nicolás + evidencia de distancia) — alta confianza
Nicolás (autoridad de dominio + autor del scraper): MIROVA reporta casi siempre el lago
cratérico, y la **distancia se mide desde el centro del área del TIF/KMZ** (centro del grid).
Evidencia que lo confirma:
- MIROVA reporta Tupungatito a **~5.2 km consistente** (mediana 5.21, rango 4.8-6.5).
- El cráter (vent) está a **4.86 km del centro del grid** → **4.86 ≈ 5.2** ✓.
- Nuestras detecciones caen a **5.86 km del cráter = ~1 km del centro del grid** → detectamos
  EN el centro del grid (sur, glaciar), NO en el cráter.
→ **MIROVA = cráter (~5 km del centro del grid). Nosotros = centro del grid (glaciar). Estamos
  corridos ~5 km.** Coincide con la observación visual de Nicolás.

Caveat honesto: el render del TIF (valores .tif) NO mostró un píxel brillante claro en el
cráter el 05-12 (anomalía 0.27 MW demasiado débil; topografía domina). No se pudo confirmar
por imagen del .tif; la confirmación viene de la DISTANCIA + dominio. Próximo: estudiar el
mapa web de MIROVA (volcanoMap.php) para ver la anomalía en la fuente.

## 🔴 EL "POR QUÉ SEGUIMOS CON ESTO": una regresión S65→S80 (git-confirmado)
- **S38** (commit 8a51df89): vent_anchored introducido para cerrar D8 (cluster selection
  elegía el cluster lejano grande, no el cráter). Intención correcta: anclar al cráter.
- **S62-S64**: descubrimos que `mirova_center` de Tupungatito = centro del bbox KMZ (4.86 km
  del cráter) → vent_anchored anclaba mal (HYPOTHESIS_LOG H_S64).
- **S65 (PR #93)**: FIX = quitar el mirova_center de Tupungatito → eff_vent cae a vent_lat
  (cráter). HYPOTHESIS_LOG:233 "Adopción operacional: ✅ kept. Fix S65 PR #93 mantiene
  Tupungatito sin mirova_center."
- **S66**: validado — **56% de ALERTAS curadas, ratio 0.67×** (clon literal) en los records
  con cluster <1 km del cráter. (44% restante = 2º problema, ver abajo.)
- **S80 (commit 01c51c64, PR #220, "consolidación post-pérdida-contexto... 11/11
  mirova_center")**: re-derivó el mirova_center de LOS 11 volcanes desde el LatLonBox del
  KMZ → **RE-INTRODUJO el offset de Tupungatito, revirtiendo el fix S65 sin saberlo.**
→ Respuesta a "por qué seguimos con vent_anchored aunque no servía": NO es que vent_anchored
  sea malo; **arreglamos el ancla en S65 y una consolidación S80 (post-pérdida-de-contexto)
  lo deshizo** al regenerar todos los mirova_center desde el grid. Regresión-por-consolidación.

NOTA: la "validación S87 74.7%" que mencioné en turnos previos NO se encontró en docs/
experiments (búsqueda del subagente). No la afirmo — fue memoria mía sin respaldo.

## Segundo problema (el 44% que S65 no curó): selección de cluster por VRP sumado
Aun con el ancla correcta, `cluster_hotspots` puede elegir el campo glaciar grande (muchos
píxeles fríos, VRP sumado alto) sobre el cráter chico. MIROVA usa NTI/dual-ROI (summit más
sensible), no VRP sumado. Este es el 2º eje a revisar (F63 S78 ya lo había rozado:
"cluster lejano elegido cuando clusters cercanos al vent tienen vrp_mw=0 por clip D4").

## Mecanismo del error nuestro (por qué detectamos en el centro del grid, no el cráter)
1. `get_effective_vent` usa `mirova_center` (centro del grid) como ancla de clustering +
   distancia (prioridad sobre el cráter).
2. La selección de cluster por **VRP sumado** prefiere el campo glaciar grande (muchos
   píxeles fríos) del centro sobre el cráter chico y débil (pocos píxeles).
MIROVA usa NTI/dNTI + dual-ROI (summit más sensible) y reporta el cráter. Fix = anclar al
cráter (vent) + revisar selección de cluster; A45 + reproc.

## Lección de método (proceso — pedido Nicolás: "qué hacer para que te fijes")
Mi 1ra Y 2da auditoría NO detectaron esto. Causa del fallo:
1. **Audité número-vs-número** (nuestra distancia reportada vs la de MIROVA) — pero AMBAS
   miden desde el mismo ancla sur (grid center), así que "coincidían" mientras ambas
   estaban corridas del cráter físico. Nunca comparé la UBICACIÓN (lat/lon) de nuestros
   píxeles contra el cráter físico ni contra la radiancia de la imagen MIROVA.
2. **Exceso de confianza**: tomé "coincide con los números de MIROVA" como "correcto", y
   cuando Nicolás (el experto del dominio) insistió, defendí mi conclusión en vez de asumir
   que estaba mal y cavar más hondo.

### Salvaguardas adoptadas (regla vinculante propuesta para CLAUDE.md)
- **AUDIT-SPATIAL**: toda auditoría de detección DEBE incluir un eje ESPACIAL: comparar la
  lat/lon de nuestras detecciones contra (a) el cráter físico (`vent_lat`) y (b) la
  radiancia de la imagen MIROVA (TIF local alrededor del cráter), NO solo números de
  distancia (que pueden compartir un ancla equivocado).
- **AUDIT-ADVERSARIAL**: cuando concluya "estamos bien", y MÁS aún si la intuición de
  dominio de Nicolás disiente, asumir que hay un error y refutarlo con datos antes de
  reafirmar. La insistencia del experto es señal, no ruido.
- **Herramientas que SÍ tengo**: Chrome MCP (puedo abrir mirovaweb/Maps — no decir "no
  puedo"); TIF en `../mirova-tif-archive`. Usarlas ANTES de concluir.
Mi 1ra y 2da auditoría fallaron en el eje espacial por: (1) comparar contra la distancia
REPORTADA por MIROVA (que también mide desde un ancla sur) en vez del cráter físico;
(2) usar centroide ponderado de TODO el TIF (se estira). La forma correcta: radiancia
LOCAL del TIF alrededor del cráter físico + comparar la UBICACIÓN (lat/lon) de nuestros
píxeles vs el cráter, no solo números de distancia que comparten ancla.
