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

## Lección de método
Mi 1ra y 2da auditoría fallaron en el eje espacial por: (1) comparar contra la distancia
REPORTADA por MIROVA (que también mide desde un ancla sur) en vez del cráter físico;
(2) usar centroide ponderado de TODO el TIF (se estira). La forma correcta: radiancia
LOCAL del TIF alrededor del cráter físico + comparar la UBICACIÓN (lat/lon) de nuestros
píxeles vs el cráter, no solo números de distancia que comparten ancla.
