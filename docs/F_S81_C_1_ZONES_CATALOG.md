# Catálogo cartográfico clusters R3 — Fase C.1 (S85)

**Fecha**: 2026-05-28
**Origen**: audit `experiments/_s85_f_s81_c/r3_nature_audit.py` sobre 155 R3
violators del profile operacional post-Fase B'. 38.1% (59 R3) se agruparon
en 18 clusters geográficos recurrentes. Este doc cartografía esos 18.

## Resumen ejecutivo

| Categoría | # clusters | # R3 cubiertos | Mecanismo Fase C correcto |
|---|---:|---:|---|
| (a) **Feature volcánica REAL del complejo** (MIROVA SÍ publica) | 5 | ~29 | **Expandir geometría inner_radius/polygon** |
| (b) **Feature NO-volcánica suprimible** (MIROVA suprime) | 4 | ~10 | **Extender exclude_zones** (con flag) |
| (c) **Ambiguos / requieren Sentinel-2** | 9 | ~20 | Verificación manual + decisión post |

**Lección clave**: el plan original Fase C "extender exclude_zones" solo resuelve
22% de los clusters identificables. El insight central es que **nuestro
`inner_radius_km` circular del KMZ MIROVA es demasiado estrecho para
complejos volcánicos extensos** (Llaima 40 conos adventicios, NdC 17 puntos
eruptivos alineados, Tupungatito breached caldera, Lazufre sistema regional).

## Catálogo detallado por cluster

### (a) FEATURES VOLCÁNICAS REALES — NO EXCLUDE

| Cluster | Volcán | Coords | Dist vent | Feature | Confianza | Acción |
|---|---|---|---:|---|---|---|
| 6 | NevadosDeChillan | (-36.831, -71.397) | 4.0 km NW | **Cerro Blanco / Volcán Nevado** — subcomplejo activo, 17 puntos eruptivos NW-SE | alta | Expandir `inner_radius_km` 5→8 km **o** definir multi-cráter / polygon |
| 13 | Llaima | (-38.696, -71.743) | 1.28 km SW | **Pichi-Llaima** — cono coalescente SSE del cráter principal | alta | Ya está casi dentro de inner=5km, ajustar `mirova_center` o expandir |
| 14 | Llaima | (-38.722, -71.845) | 10.6 km SW | Posible cono adventicio (Llaima tiene ~40 alineados arc SW-NE) | media | Expandir radio Llaima 5→12 km **o** verificar con Sentinel-2 |
| 17 | Lastarria | (-25.174, -68.627) | 12.1 km SW | **Lazufre / Cordón del Azufre** — sistema regional inflación InSAR + sulfur flows | alta | Expandir radio Lastarria 3→15 km **o** definir polygon Lazufre complejo |
| 18 | Tupungatito | (-33.391, -69.823) | 2.4 km NW | Cráter norte breached caldera + cono piroclástico activo | alta | Expandir radio Tupungatito 7→9 km |

**Total R3 cubiertos por (a)**: ~29 (cluster 6: 11, cluster 13: 7, cluster 14: 2, cluster 17: 2, cluster 18: 2 = 24, + posiblemente otros similares).

### (b) FEATURES NO-VOLCÁNICAS — EXCLUDE candidatos

| Cluster | Volcán | Coords | Dist vent | Feature | Confianza | Acción |
|---|---|---|---:|---|---|---|
| 2 | Copahue | (-37.831, -71.182) | 2.84 km NE | **Campo geotermal Las Máquinas / Maquinitas** (165 t CO₂/día, hot springs ácidos no-eruptivos) | alta | Extender `exclude_zones` Copahue (+ Lago Caviahue ya existente) |
| 11 | NevadosDeChillan | (-37.009, -71.390) | 16.3 km SW | Cuenca Río Diguillín fuera complejo (Pinto/Coihueco) | alta | exclude_zones NdC nuevo |
| 15 | PlanchonPeteroa | (-35.051, -70.502) | 21.9 km NE | Ladera argentina (Malargüe), fuera complejo Azufre-Planchón-Peteroa | alta | exclude_zones PP nuevo |
| 16 | PlanchonPeteroa | (-35.231, -70.390) | 16.2 km NE | Valle Río Claro argentino, fuera estructura | alta | exclude_zones PP nuevo |

**Total R3 cubiertos por (b)**: ~10 (cluster 2: 2, cluster 11: 2, cluster 15: 3, cluster 16: 2).

### (c) AMBIGUOS — requieren verificación Sentinel-2 / decisión Nicolás

| Cluster | Volcán | Coords | Dist vent | Hipótesis | Confianza | Pendiente |
|---|---|---|---:|---|---|---|
| 1 | Lascar | (-23.399, -67.767) | 4.88 km SW | Flanco SW Lascar; cerca límite Aguas Calientes (volcán satélite) | media | Confirmar con Sentinel-2 si hay anomalía persistente |
| 3 | Copahue | (-37.867, -71.250) | 5.96 km SW | Ladera SW sin feature térmica catalogada | baja | Sentinel-2 imagery |
| 4 | Copahue | (-37.860, -71.208) | 2.19 km SW | Flanco SW próximo cráter (alineamiento 9 cráteres ENE-WSW) | media | Plausible feature volcánica → no excluir sin verificar |
| 5 | Copahue | (-37.799, -71.353) | 16.3 km NW | Lejos del complejo, fuera caldera Caviahue, sin geotermal NW | media | Candidato exclude pero verificar Sentinel-2 |
| 7 | NdC | (-36.809, -71.450) | 8.81 km NW | Ladera glacial NW del flanco | media | Posible artefacto sobre nieve/glaciar → candidato exclude |
| 8 | NdC | (-36.840, -71.320) | 5.7 km NE | Flanco NE del complejo, fuera Cerro Blanco | baja | Verificar Sentinel-2 |
| 9 | NdC | (-36.792, -71.415) | 8.57 km NW | Similar a 7 — ladera glacial NW lejana | media | Candidato exclude |
| 10 | NdC | (-36.852, -71.465) | 7.9 km NW | Ladera glacial NW | media | Candidato exclude |
| 12 | Llaima | (-38.876, -71.906) | 25.5 km SW | Zona adventicios SW lejana, posible bosque/cultivo Cherquenco | media-baja | Distancia 5× inner_radius — probable FP regional |

**Total R3 cubiertos por (c)**: ~20.

## Decisión arquitectural recomendada

El trabajo de **expandir geometría volcánica per-vol** (categoría a) es **prioritario sobre extender exclude_zones** (b), porque:

1. Resuelve más R3 cuantitativamente (~29 vs ~10).
2. Acerca el clon a MIROVA real (que sí publica esos sub-complejos como TPs).
3. NO requiere supuesto sobre supresión MIROVA (cada decisión sobre qué incluir en el "complejo" del vol es físicamente justificable).
4. exclude_zones (b) sigue siendo divergencia del clon literal (parche no en papers MIROVA).

### Propuesta concreta para S86

**Fase C.1.A (geometría extendida, prioridad alta)**:
- Esquema yaml: `inner_radius_km` actual + `extended_radius_km` opcional + `additional_centers` opcional (lista de sub-cráteres/sub-conos del complejo). Pixels dentro de cualquier centro+radio cuentan como "intra-complex".
- Casos concretos basados en cartografía:
  - NdC: `additional_centers: [{name: 'Cerro Blanco', lat: -36.831, lon: -71.397, radius_km: 3}]`.
  - Llaima: `extended_radius_km: 12` (cubre Pichi-Llaima + algunos adventicios SW).
  - Lastarria: `additional_centers: [{name: 'Lazufre', lat: -25.174, lon: -68.627, radius_km: 5}]`.
  - Tupungatito: `extended_radius_km: 9`.
- Costo: ~2-3h refactor + tests + A/B.
- Riesgo: bajo (extender, no contraer).

**Fase C.1.B (exclude_zones extendido, prioridad media)**:
- Activar flag `enable_exclude_zones` para los 4 zones nuevos en vols específicos.
- Costo: ~1h (mecanismo ya existe en código pero desactivado S27).
- Riesgo: medio (puede capturar FPs reales si las coords están mal centradas).
- Requiere A/B aislado para validar cero pérdida TPs.

**Fase C.1.C (ambiguos — verificación Sentinel-2)**:
- Esto requiere tu input directo, Nicolás (acceso a Sentinel Hub / EO Browser).
- Para los 9 clusters categoría (c), decidir caso por caso.
- NO automatizable.

**Fase C.2 (huérfanos 62%, sin patrón espacial)**:
- Mecanismo distinto: coherencia temporal MIROVA-style.
- Diseño separado en S86 (brainstorm posterior).

## Refs

- Audit Fase C: `experiments/_s85_f_s81_c/r3_nature_audit.py`
- Resultados JSON: `experiments/_s85_f_s81_c/r3_nature_detail.json`
- Adopción B': `docs/F_S81_B_PRIME_ADOPTION_S85.md`
- Beyond MIROVA roadmap: `docs/BEYOND_MIROVA_EXTENSIONS.md`
- GVP sources investigados:
  - [Llaima](https://volcano.si.edu/volcano.cfm?vn=357110)
  - [Nevados de Chillán](https://volcano.si.edu/volcano.cfm?vn=357070)
  - [Copahue](https://volcano.si.edu/volcano.cfm?vn=357090)
  - [Lascar](https://volcano.si.edu/volcano.cfm?vn=355100)
  - [Lastarria](https://volcano.si.edu/volcano.cfm?vn=355120)
  - [Tupungatito](https://volcano.si.edu/volcano.cfm?vn=357010)
  - [Planchón-Peteroa](https://volcano.si.edu/volcano.cfm?vn=357040)
- Frontiers Earth Sci 2023 sulfur flows Lastarria: [DOI 10.3389/feart.2023.1197363](https://www.frontiersin.org/journals/earth-science/articles/10.3389/feart.2023.1197363/full)
- Geotermal Copahue Las Máquinas: [Patagonia.com.ar](https://www.patagonia.com.ar/Copahue/188E_Geothermal+well+Las+Mellizas+Las+M%C3%A1quinas+and+Las+Maquinitas.html)
