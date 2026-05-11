# D8 (S35) — Cluster selection diverge de MIROVA

**Status**: investigación + design draft 2026-05-10
**Driver**: bug detectado durante análisis A/B H8. Sin fix D8, H8 amplifica overdetection.
**Reach**: 34/191 alertas MIROVA (18%) tienen `dist_diff > 5km` entre primary_cluster.centroid_dist_km y MIROVA reported distance.

---

## Problema (síntesis)

`pipeline/clustering.py:99-101` ordena clusters por `vrp_mw desc` (con vrp_per_pixel) o `n_pixels desc`. El `primary_cluster` reportado al record es el primero de esa lista.

**Resultado**: para casos con múltiples clusters detectables, VRP-chile elige el "más grande" mientras MIROVA elige otro (típicamente el más cercano al vent o el con mayor anomaly score relativo al bg local).

## Evidencia empírica

### Caso Puyehue lacolito 2026-05-09 05:42 VIIRS_NOAA21 (R2 confirmado pixel-level)
- **MIROVA reporta**: 0.18 MW @ 7.73 km (lacolito)
- **VRP-chile primary_cluster**: 0.689 km @ 4.94 MW (cluster cráter principal, 99 pixels, T_max=284K)
- **VRP-chile discarded_anomaly_pixels** (cuando se descartaba todo por bug H8): contiene cluster de 34 pixels @ 8.4 km vrp=0.54 MW = **EL LACOLITO**

VRP-chile DETECTÓ el lacolito pero el algoritmo de cluster selection lo desestimó por su bajo VRP relativo al cluster cráter.

### Patrón generalizado en Puyehue
| Acquisition | PC VRP-chile | MIROVA | Cluster lacolito en discarded |
|---|---|---|---|
| 05-09 06:18 V_SNPP | 0.28km / 2.5MW | (lacolito) | 29px @ 8.6km vrp=0.33 |
| 05-09 05:42 V_NOAA21 | 0.69km / 4.9MW | 0.18MW @ 7.7km | 34px @ 8.4km vrp=0.54 |
| 05-08 07:45 MODIS_AQUA | 16.6km / 14.2MW (FP lejano) | (alerta cráter) | 3px @ 7.5km vrp=3.4 |
| 05-07 02:40 MODIS_TERRA | 11.4km / 38.8MW | (alerta cráter) | 3px @ 7.0km vrp=11.3 |

### Patrón Lascar
- MIROVA: cluster cráter @ 1-2km, VRP 0.3-2 MW
- VRP-chile: cluster Salar Atacama @ 22-30km, VRP 3-15 MW
- 13 casos de 19 alertas Lascar tienen `dist_diff > 18km`

## Hipótesis sobre algoritmo MIROVA

### H_D8_1: cluster más caliente DENTRO del inner_radius
MIROVA filtra primero clusters con `centroid_dist_km <= inner_radius_km`,
luego elige por VRP máximo entre esos. Solo si no hay nada cercano,
considera lejanos.

**Pro**: explica Lascar (cluster Salar fuera de inner=5 → MIROVA elige cluster
cráter dentro de inner).
**Con**: NO explica Puyehue (ambos cluster cráter y lacolito están dentro
inner=20, MIROVA elige el lacolito que tiene VRP MENOR).

### H_D8_2: cluster con mejor anomaly score local (T_pixel - T_bg_local)
MIROVA evalúa el contraste local de cada cluster vs su background inmediato,
no la T absoluta.

**Pro**: explica Puyehue cluster cráter (T_max=284K pero bg local también
~280K → low contrast). Cluster lacolito tiene T similar pero bg en zona
lava field es más bajo (~265K) → high contrast.
**Con**: necesita datos T_max y bg per cluster que no se persisten en records.

### H_D8_3: cluster que dispara Test 1 integrated-ROI
Test 1 (Coppola 2015) opera sobre ROI summit (default 1-3 km). Cuando dispara,
MIROVA reporta el cluster que cae dentro del ROI Test 1.

**Pro**: explica Puyehue lacolito si MIROVA usa ROI Test 1 distinto al nuestro.
**Con**: VRP-chile YA tiene Test 1 enabled (`enable_test1_path: true`).
   Si Test 1 disparó, debería elegir cluster en ROI Test 1.

## Coppola 2016 enhanced — gaps detectados (clave para D8)

Lectura Vault `coppola2016enhanced.md` (verificada 2026-05-10) revela 2 algoritmos
clave de MIROVA que VRP-chile NO implementa, y que probablemente explican D8:

### Gap 1: ETI cuadrático (background adaptativo scene-wide)
```
NTI_bk = a·NTI²_app + b·NTI_app + c   # regresión cuadrática sobre la escena
ETI = NTI_pix − NTI_bk                # signal vs background regresional
```
VRP-chile usa background local annulus (5-25km del vent). MIROVA usa background
regresional sobre toda la escena. Para Puyehue cluster cráter (warm BG), la
regresión MIROVA scene-wide ajusta NTI_bk alto en esa zona → ETI bajo →
cluster cráter descartado. Para lacolito (zona lava field BG bajo), NTI_bk
bajo → ETI alto → cluster pasa threshold.

### Gap 2: Second-pass adyacente
Detect anomalous pixel → BAJAR threshold para 8-vecinos → agregar al cluster.
VRP-chile clusters post-detección por contigüidad, no organic growth.

### H_D8_4 (revisada): MIROVA = ETI cuadrático + second-pass
Gap arquitectural mayor. Implementar ETI cuadrático en perfil experimental
es la próxima acción concreta.

## Investigación pendiente

- [x] Leer Coppola 2016a (Vault) — DONE 2026-05-10
- [ ] Verificar si MIROVA reporta múltiples clusters por pasada o solo uno
  (revisar TIF MIROVA + KMZ Last_GE.kmz overlay)
- [ ] Sample casos Lascar Salar — ¿VRP-chile sí filtra cluster lejano por radius_km?
  Si sí, ¿por qué primary_cluster sigue apuntando a Salar (24-30km)?
- [ ] Test empírico: re-procesar Puyehue 05:42 con orderings alternativos:
  - sort by `n_pixels asc` (privilegiar pequeños = cluster lacolito gana)
  - sort by `centroid_dist_km asc` luego `vrp_mw desc` (privilegiar cercanos)
  - sort by `vrp_mw / n_pixels desc` (densidad VRP)
  Ver cuál se acerca más al MIROVA reported

## Decisión: NO implementar fix D8 ahora

**Razones**:
1. Algoritmo MIROVA exacto desconocido. Hipótesis múltiples competidoras.
2. Cualquier fix que cambie cluster selection puede romper otros casos no
   mapeados (los 157/191 = 82% donde primary_cluster ya matchea MIROVA).
3. R5 brainstorming requiere claridad sobre el criterio antes de implementar.
4. Mejor opción es leer Coppola 2016a primero o consultar con Coppola directo.

**Documentación**: D8 queda como "abierto" en `docs/MIROVA_DIVERGENCES.md`.
Reach 18% de alertas afectadas.

**Implicación para H8**: H8 fix sin D8 inflate ratio porque preserva más
clusters in-range pero `primary_cluster` sigue siendo el equivocado. El A/B
H8 confirmó esto empíricamente (ratio_med 3.48× → 5.09×, +46%).

**Recomendación**: H8 también queda como flag opt-in. NO adoptar en
operacional hasta tener D8 resuelto.

## Pre-mortem

Si en el futuro se intenta fix D8:
1. Necesario A/B contra dataset 30+ días (no 7 días) para detectar regresiones
   sobre los 157/191 casos que actualmente matchean correctamente.
2. Necesario R2 pixel-level vs MIROVA TIFs para validar cluster selection
   per caso (mirova-tif-archive ya tiene esos TIFs).
3. Si el fix mejora Puyehue/Lascar pero degrada Villarrica/Lastarria, no
   adoptar. La consistencia trans-volcán es el criterio.
4. Considerar que MIROVA puede tener algoritmo distinto por sensor (MODIS vs
   VIIRS) — testear separado.

## Plan investigación próxima sesión S36

1. ~~Leer Coppola 2016a §sección clustering (Vault tiene PDF)~~ — **DONE**:
   Vault tiene solo notes resumidos. Detalles cuantitativos del ETI cuadrático
   están en Coppola **2015a** (Geological Society SP, "Enhanced volcanic
   hot-spot detection using MODIS IR data") que NO está en Vault.

2. **PRIORIDAD ALTA**: obtener PDF Coppola 2016a (GS Special Publications).
   Sin ese paper, no podemos implementar ETI cuadrático correctamente.

   **Citation exacta** (encontrada S36 2026-05-11):
   Coppola, D., Laiolo, M., Cigolini, C., Delle Donne, D., & Ripepe, M. (2016).
   Enhanced volcanic hot-spot detection using MODIS IR data: results from the
   MIROVA system. **Geological Society, London, Special Publications**, 426,
   181–205.
   **DOI**: `10.1144/SP426.5`

   Posibles fuentes (en orden de menor fricción):
   - **ResearchGate** "Request PDF":
     https://www.researchgate.net/publication/277899112_Enhanced_volcanic_hot-spot_detection_using_MODIS_IR_data_results_from_the_MIROVA_system
     (autor Diego Coppola responde típicamente 0-2 días)
   - **Email directo Diego Coppola**: diego.coppola@unito.it
   - **Lyell Collection** (paywall): https://www.lyellcollection.org/doi/abs/10.1144/sp426.5
   - **Semantic Scholar** (abstract + refs):
     https://www.semanticscholar.org/paper/e90359a33659c945b767a7c97ea590e6ffa30547

3. Si paper no es accesible → contactar Coppola directo o publicar issue
   en algún repo MIROVA si existe.

4. **Confirmación cross-paper** (S35 update 2026-05-10):
   - Coppola 2020 thermal cita literal: "spatial operations allow us to
     highlight the pixels having these indices **in excess with respect to
     their surroundings** — hybrid and contextual approach"
   - Coppola 2016 fifteen redirige TODO el detalle algorítmico a Coppola 2015a
   - Coppola 2016 enhanced (Vault note) menciona ETI cuadrático pero sin
     fórmula completa
   - Coppola 2020/2016f confirman implícitamente: detección requiere
     superar el bg local Y un bg regresional scene-wide
