# D8 (S35) — Cluster selection diverge de MIROVA

**Status**: implementación H_D8_5 iniciada S37 (2026-05-11) — skeleton + perfil + tests sintéticos. Lógica ETI cuadrático + second-pass + sum reporting pendiente (commits 2-N S37).
**Driver**: bug detectado durante análisis A/B H8. Sin fix D8, H8 amplifica overdetection.
**Reach**: 34/191 alertas MIROVA (18%) tienen `dist_diff > 5km` entre primary_cluster.centroid_dist_km y MIROVA reported distance.

**Tracking implementación**:
- [x] S37 commit 1 — skeleton (perfil `_h_d8_5_full.yaml` + stubs `compute_eti_scene_quadratic`/`second_pass_adjacent` + tests sintéticos D8 bug + xfail markers)
- [ ] S37 commit 2 — implementar `compute_eti_scene_quadratic` (regresión polinomial scene-wide, paper eqs 4-5)
- [ ] S37 commit 3 — implementar `second_pass_adjacent` (paper líneas 347-356)
- [ ] S37 commit 4 — integrar ambas funciones en `process_modis.py` / `process_viirs.py` / `process_viirs_mod.py` gated por flags del perfil
- [ ] S37 commit 5 — implementar `enable_sum_vrp_reporting` en `store.py` (campos `vrp_mw_sum_active` + `hotspot_dist_km_furthest`)
- [ ] S37 commit 6 — workflow A/B reproc 30 días H_D8_5 vs mirova_equivalent baseline
- [ ] S37 commit N — validación R2 pixel-level vs mirova-tif-archive + R3 audit independiente

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

## Coppola 2016a (SP426.5) — algoritmo COMPLETO leído (2026-05-11)

**PDF localizado**: `VRP Chile/documentacion/sp426.5.pdf` (9.4 MB) + `sp426_5.txt` extraído.
Yo había leído antes solo el note resumido en Vault. Lectura completa revela
la matemática exacta de TODOS los gaps.

### Paso 1: Spectral analysis (NTI + ETI)

**NTI** (Wright et al. 2002):
```
NTI = (L_MIR - L_TIR) / (L_MIR + L_TIR)
```

**NTI_app** (synthetic NTI assuming homogeneous pixel temperature):
```
T_app = BT_TIR                                          # asume T uniforme per pixel
L_MIR,app = Planck_MIR(T_app)                           # eq 2
NTI_app = (L_MIR,app - L_TIR) / (L_MIR,app + L_TIR)     # eq 3
```

**ETI cuadrático** (background regresional scene-wide):
```
# Regresión polynomial sobre scene completa (NTI vs NTI_app)
# Parámetros a, b, c se ajustan por imagen (no fijos):
NTI_bk = a·NTI²_app + b·NTI_app + c                     # eq 4
ETI = NTI - NTI_bk                                      # eq 5
```
**Resultado**: ETI alto = pixel anómalo vs el comportamiento esperado de la
escena. Hot pixels desvían de la regresión.

### Paso 2: Spatial analysis (dNTI + dETI)

Para cada pixel:
```
dNTI_pix = NTI_pix - mean(NTI_8_neighbors)
dETI_pix = ETI_pix - mean(ETI_8_neighbors)
```
- Todos los 8 vecinos usados (NO cloud filter)
- Filter "unsuitable": edge pixels, dNTI/dETI < -0.1

### Paso 3: Test 1 (Fixed NTI threshold)

```
NTI_pix > K1     → flag as active, remove from further analysis
```
- K1 = **-0.8 noche** / -0.6 día (uniforme para ROI1 y ROI2)
- Settled per MODVOLC global validation (Wright et al. 2002)

### Paso 4: Tests 2 + 3 (Contextual thresholds) — BOTH must hold

```
Test 2: dNTI_pix > C1   OR   dNTI_pix > μ_dNTI + C2·σ_dNTI
Test 3: dETI_pix > C1   OR   dETI_pix > μ_dETI + C2·σ_dETI

# Pixel flagged active iff Test 2 AND Test 3 (línea 315 paper)
```

**Tabla 1 oficial Coppola 2016a** (parámetros noche/día × ROI1/ROI2):
| Parámetro | ROI1 (summit 5×5km) night | ROI2 (scene) night | ROI1 day | ROI2 day |
|---|---|---|---|---|
| K1   | -0.8 | -0.8 | -0.6 | -0.6 |
| C1   | **0.003** | **0.01** | 0.02 | 0.02 |
| C2   | **5**     | **10**   | 15   | 15   |

ROI1 = summit (más sensible). ROI2 = whole scene minus ROI1 (más estricto).

### Paso 5: Second-pass adyacente (CRITICAL — gap nuestro)

Cita exacta (líneas 347-356):
> "active pixels may strongly modify the average values of their surroundings,
> with a consequent decrease in the dNTI and dETI values of adjacent pixels.
> To avoid this problem, step 2 (spatial analysis) is performed a **SECOND
> TIME**, being particularly careful to eliminate all of the 'active' pixels
> already detected. Hence, the previous step (contextual threshold: tests 2
> and 3) are applied again to the new dNTI and dETI matrices."

Implicación: el cluster crece orgánicamente recapturando pixels marginales que
quedan opacados por el primer pass.

### Paso 6: VRP calculation

```
ΔL4_pix = L4_alert - L4_bk                              # eq 6
L4_bk = arithmetic mean of pixels around the active cluster   # NO global annulus

RP_pix = 18.9 · A_pix · ΔL4_pix                         # eq 7 (W)
RP_total = Σ RP_pix                                     # eq 8 over ALL active pixels
```
**Crítico**: RP total = suma de TODOS los pixels active en TODA la escena.
**NO se selecciona un "primary cluster"**.

### Paso 7: Distance reportada

Cita líneas 510-513:
> "we measured the approximate distance (±1 km) between the **main vent**
> (whose location must be known a priori) and **the centre of the furthermost
> alerted pixel**"

Distance = vent → **pixel ACTIVE MÁS LEJANO**, no centroide cluster.

---

## Implicación para D8 (cluster selection bug)

VRP-chile actualmente:
1. Detecta pixels active vía paths (BT, dNTI, Test 1)
2. **Clustering posterior**: agrupa pixels conectados (8-conn) en clusters
3. **Selecciona primary_cluster**: por máximo VRP / máximo n_pixels
4. **Reporta**: pc.vrp_mw, pc.centroid_dist_km

MIROVA:
1. Detecta pixels active vía NTI + ETI + dNTI + dETI + 4 tests
2. **NO clustering posterior** ni selección de primary
3. **Reporta**: Σ RP_pix de TODOS los pixels active
4. **Distance**: vent → pixel más lejano (¡no del cluster!)

**Conclusión D8**: el "bug cluster selection" no es bug — es divergencia
arquitectural. VRP-chile inventó un concept de primary_cluster que MIROVA
no usa. Si reportamos sum(vrp_mw) en vez de pc.vrp_mw, eliminamos el bug
D8 estructuralmente.

**PERO** sum(vrp_mw) sin filtros ETI cuadrático suma TODOS los pixels
detectados, incluyendo Salar Atacama (Lascar) y fuegos. Para que sum(vrp_mw)
matchee MIROVA, hay que tener detección filtered como MIROVA → necesitamos
ETI cuadrático + second-pass.

### H_D8_5 (FINAL, basada en paper completo): 3 fixes combinados

1. **ETI cuadrático**: implementar `NTI_bk = a·NTI²_app + b·NTI_app + c`
   con regresión polynomial scene-wide por imagen. Reemplaza nuestro
   background local annulus.

2. **Second-pass adyacente**: tras primera detección de active pixels,
   re-correr Step 2 + Tests 2/3 EXCLUYENDO active pixels (para que no
   contaminen mean de 8-vecinos).

3. **Reporting MIROVA-style**:
   - vrp_mw_total = sum(vrp_mw) sobre TODOS los pixels active
   - hotspot_dist_km = max(dist_km) entre active pixels (no centroide cluster)
   - primary_cluster.vrp_mw → DEPRECATE (no MIROVA concept)

**Implementación**: feasible ahora que tenemos la matemática completa.
Costos: ~3-5 días de trabajo, NUEVO perfil experimental, A/B 30 días.

### H_D8_4 (anterior, parcial) — superseded by H_D8_5

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
