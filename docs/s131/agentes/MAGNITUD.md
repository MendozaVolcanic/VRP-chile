# S131 · Auditoría de la cadena de MAGNITUD (VRP en MW) contra los papers, file:line

> Agente de auditoría S131, eje «magnitud». Read-only sobre `pipeline/`, `frontend/`,
> `data/`, `docs/`. Scripts y JSON en `experiments/_s131_audit/magnitud/`
> (`01_r1_r2_vigencia.py`, `02_correccion_area_por_angulo.py`, `03_pares_por_pasada.py`,
> `04_display_f5_vs_pc.py`). Flags leídos con `VRP_PROFILE=mirova_equivalent python -c
> "import pipeline.profile as p; ..."` (A89), nunca del YAML. Todo conteo lleva
> denominador y ventana (A90). Fecha de los datos: `data/mirova_equivalent/` al
> 2026-09-01 (último NRT commiteado `e27433a29`).

## 0. Resultado primero

**La física está bien; lo que divierge de MIROVA es lo que se suma, con qué fondo, y
sobre qué área.** Los tres coeficientes (18,9 · 19,7 · 18,0), las áreas nominales
(1e6 · 562.500 · 140.625 m²), Planck, el clip ΔL ≥ 0 y las unidades son fieles a
Coppola 2016a Eq. 7, Campus 2022 Eq. 1 y Campus 2024 Eq. 3, y coinciden con el
coeficiente que MIROVA usó de verdad en 48.360 filas del OSF v2.5 (error ≤ 0,17 %,
`experiments/21_results.json`). De ahí para abajo la cadena tiene **cinco desvíos
respecto del paper**, tres de ellos activos hoy en producción:

| # | desvío | paper | nuestro | estado hoy | efecto medido |
|---|---|---|---|---|---|
| 1 | **área del píxel** | Coppola 2014 §2.2: remuestreo a celdas de área constante, o sea la energía se integra sobre el área REAL | área nadir fija sobre el píxel real, sin remuestreo | activo, los 3 sensores | V375 por pasada: 0,77 en nadir → **0,45** a 50°+ (1,72×); corregido con la ley de área del ATBD queda **plano** (0,79–0,87) |
| 2 | **fondo** | Eq. 6: media aritmética de los píxeles que rodean al activo/clúster | mediana del anillo 5–25 km (contextual) · anillo 1,5–3 km (Test 1 V375) · kernel 3×3 en 5 volcanes opt-in | activo | déficit uniforme que persiste tras corregir el área: mediana global V375 **0,82**, V750 **0,77** |
| 3 | **integración** | Eq. 8: suma de TODOS los píxeles alertados | un solo clúster (S129) + R1 subconjunto focal + R2 máximo en vez de suma | activo: R1 MODIS 88 % de los records, R2 efectivo 11–26 % | suma/máximo reconstruido: MODIS **1,63**, V375 **1,48**, V750 **1,36** (medianas) |
| 4 | **cap 5 MW path D** | no existe como regla algorítmica (SP426.5 §675-696 es descriptivo) | `PATH_D_ONLY_CAP_MW = 5.0` con `t_bg < 270 K` | activo, sin flag `enable_` | MODIS 2026: **640 / 5.159** records capeados (12,4 %); **ninguno** coincide con una alerta MIROVA |
| 5 | **lo que ve el operador** | — | para VIIRS375 el dashboard muestra `f5CoreMagnitude`, no `pc.vrp_mw` | activo (`USE_F5_CORE = true`) | ratio vs MIROVA **0,68** (display) contra **0,58** (`pc.vrp_mw`); coinciden en el **5,7 %** de los records |

**Para un operador de OVDAS**: el MW publicado en el dashboard para VIIRS375 hoy es un
número que (a) no está en ningún JSON, (b) sube ~20 % lo que el pipeline calcula y
(c) sigue ~30 % por debajo de MIROVA en la mediana. Es comparable en orden de
magnitud; no es intercambiable. Las recomendaciones de §3 apuntan a que el número
que se publique sea uno solo, trazable, y con el sesgo de área corregido.

**Sobre el hallazgo de hoy (`docs/s131/REMUESTREO_LEY_DE_AREA.md`)**: el mecanismo es
correcto y alcanza; el número «f requerido 2,93×» **no**, porque nace de emparejar
cada pasada nuestra contra el máximo de la noche de MIROVA (§2.7). Emparejando pasada
con pasada (la ground truth tiene hora al segundo), el factor requerido a 58° es
**1,72×** y la ley del ATBD da **~1,9×** ahí: el área explica el gradiente completo,
no «a medias».

---

## 1. La cadena, sensor por sensor, con el paper al lado

Formato: paso → file:line nuestro → ecuación/cita del paper → veredicto.

### 1.1 MODIS (B21/B22 → `primary_cluster.vrp_mw`)

| paso | nuestro | paper | veredicto |
|---|---|---|---|
| DN → radiancia | `process_modis.py:243-247` `rad = (dn − offset) × scale`, `dn > 32767 → NaN` | MODIS L1B (convención `radiance_scales/offsets`); Coppola 2016a l.189 «all the pixels with DN > 32 768 … excluded» | fiel |
| banda MIR | `:492-495` **B21 primaria**, B22 sólo donde B21 es NaN (`np.where(isnan(rad21), rad22, rad21)`); cabecera `:29` «Band 22 … used where Band 21 is saturated» | Coppola 2016a l.141-144, verbatim: *«we built a corrected spectral band centred at 3.959 µm (hereby called band L21ok), by using the **L21 or L22** radiance, **depending on band 22 saturation** (or not)»* → **B22 primaria, B21 sólo si B22 satura** | **DIVERGENCIA** (§2.4) |
| BT y vuelta a radiancia | `:198-206` Planck con `BAND21_LAMBDA = 3.929`, `:968` `L_bg = Planck(t_bg)` | Coppola 2024 cap. 11 Eq. 17: «MODIS (λMIR = 3.959 µm) … A_pix = 1 × 10⁶ m²» | λ de B21 (3,929) con un k derivado para 3,959; segundo orden, ver §2.4 |
| fondo | `:487` `bg_mask = 5 ≤ dist ≤ 25 km`; `:519` `cloud_free` con `CLOUD_MASK_BT_K = 0.0` (inactivo, #535); `detection_context.py:995-996` **mediana** y `std` de BT del anillo; `ENABLE_TEST1_K1_BG_EXCLUDE = False` (los píxeles alertados quedan dentro) | Eq. 6 l.353-359: *«L4bk is estimated from the **arithmetic mean** of all the pixels **surrounding** the active one (or around the active cluster)»*; §352-356 excluir activos | **DIVERGENCIA** de dónde (regional vs corona), de qué (incluye activos) y de estadístico (mediana vs media) |
| fondo local opt-in | `:986-994` kernel 3×3 media de vecinos no-hot, sólo si `ENABLE_LOCAL_KERNEL_BG ∧ volcano.local_kernel_bg` (puente `run_pipeline.py:244`): **PCC, Villarrica, Chaitén, PP, Lastarria** = true; Copahue, Llaima = false; los otros 4 sin clave | Coppola 2024 l.1129 «T_bk is retrieved from the pixels adjacent to the hot one» | la versión más fiel a Eq. 6 existe y corre en **5 de 11**; el fondo de magnitud es hoy **per-volcán** |
| ΔL y potencia por píxel | `:1001` `delta_L = max(rad − L_bg, 0)`; `:1002` `area × 18.9 × ΔL / 1e6` | Eq. 7 l.374: `RP_PIX = 18.9 · A_PIX · ΔL4_PIX` | fiel |
| área | `:462-463` → `scan_geometry.py:143-144` `np.full(1.0e6)` con `ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS = True` | l.384: «A_PIX is the pixel size (1 km² for the **resampled** MODIS pixels)»; Coppola 2014 §2.2 (§2.1 de este informe) | **A_PIX nominal es válido sólo sobre la malla remuestreada**; nosotros no remuestreamos (`ENABLE_UTM_REGRID = False`) |
| suma | `clustering.py:113` suma por clúster; `:1023-1029` se publica **un** clúster (vent-anchored) | Eq. 8 l.386-395: `RP = Σ_{i=1}^{n alert} RP_PIX` — *«the total radiative power is calculated as being the sum of the single RP_PIX»* | **DIVERGENCIA** (S129 lo midió: 0,730 → 0,798 sumando <5 km) |
| corona Eq. 6 | `:1065-1085` **OFF** (`ENABLE_LOCAL_CLUSTER_MAGNITUDE = False`) | Eq. 6 | capacidad dormida (S125) — sigue dormida |
| **R1 focal** | `:1096-1100` `cluster_focal_vrp_mw` con `ENABLE_FOCAL_CLUSTER_MAGNITUDE = True`; también en Test 1 `:1347-1350` | no existe en Eq. 8 | **activo** (§2.5) |
| **cap D9** | `:1103-1104` `if _path_d_cap_active and _vrp_c > 5.0: _vrp_c = 5.0` | no existe (§2.6) | **activo** |
| **R2 single-pixel** | `:1124-1129` `apply_single_pixel_mode(threshold 5 MW, max 3 px)` → `vrp = max(per_pixel)`; también `:1371-1376` | no existe (Eq. 8 suma) | **activo** (§2.5) |
| Test 1 (recompute) | `:1286-1308`: `effective_L_bg` = anillo **5–25 km** si `lbg_global_compatible` (Láscar, NdC, Lastarria) o **mediana de radiancia del anillo 1–3 km** (`test1_integrated.py:411-412`) | Eq. 6 | fondo per-volcán otra vez |
| pisos / caps de sistema | `MIN_VRP_MW_MODIS = 0.0`, `MODIS_VENT_VRP_FLOOR_MW = 0.0`; `store.py:63` `SANITY_CAP_VRP_MW = 50000` | — | piso fuera (S130) confirmado; el cap 50 GW es sanidad física |

### 1.2 VIIRS I-band 375 m (I4 → `primary_cluster.vrp_mw`)

| paso | nuestro | paper | veredicto |
|---|---|---|---|
| DN → BT | `process_viirs.py:370-386` LUT `I04_brightness_temperature_lut`, `FLAG_DNS` (bow-tie deleted), bit-2 saturación, tope LUT | VIIRS L1B UserGuide (Aug 2021) | fiel |
| BT → radiancia | `:229-231` Planck, `I04_LAMBDA = 3.740` | Campus 2024 Eq. 3 (I4) | fiel |
| área | `:710-714` → `scan_geometry.py:206-207` `np.full_like(140625)` con `ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS = True` | Campus 2024 l.146: «A_pix is the pixel size (140,625 m² for VIIRS I-bands)», tras *«an initial resampling of the original granule»* (l.102) | mismo problema que MODIS: área nominal sin remuestreo |
| fondo contextual | `:743` anillo 5–25 km, `:794` `& cloud_free`, `:904-911` `compute_bg_stats` (mediana); `:1382-1393` kernel 3×3 si opt-in, si no `Planck(t_bg_i04)` | Campus 2024 l.120-123: *«arithmetic mean of the radiance of the pixels surrounding the alerted one(s)»* | DIVERGENCIA (§2.3) |
| ΔL, potencia, suma | `:1400-1404`, `:1441-1449` | Eq. 3 · Eq. 8 | fiel por píxel; un clúster |
| corona | `:1466-1472` **OFF** (`ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375 = False`) | Eq. 6 | dormida |
| R1 focal | **no existe en V375** (ni contextual ni Test 1) | — | 0 records (§2.5) |
| cap D9 | `:1478-1481` | — | 0 records 2026 capeados en V375 |
| R2 single-pixel | `:1502-1507` y `:1927-1932` | — | **activo**: aplicado en 7.115 / 7.169 (99,2 %), con efecto en 816 (11,4 %) |
| Test 1 (recompute) | `:1795-1855`: precedencia anillo **intermedio 1,5–3 km** (`ENABLE_TEST1_INTERMEDIATE_BG = True`, mediana de BT `test1_integrated.py:96-128`) > global 5–25 km per-volcán > local 1–3 km; luego `:1893-1950` clúster 8-conexo | Eq. 6 | tercer fondo distinto en el mismo sensor |

### 1.3 VIIRS M-band 750 m (M13 → `primary_cluster.vrp_mw`)

| paso | nuestro | paper | veredicto |
|---|---|---|---|
| DN → BT → radiancia | `process_viirs_mod.py:211-222` LUT; `:324-327` Planck `M13_LAMBDA = 4.050` | Campus 2022 §2 | fiel |
| área y coeficiente | `:435-438` 562.500 m²; `:63` `WOOSTER_COEFF = 19.7` → k·A = 11.081.250 | Campus 2022 Eq. 1 l.422-423: `VRP = ΔL_MIR · 1.97 × 10⁷ · A_pix`, «A_pix … equal to **0.5625** for VIIRS M-bands» | fiel. ⚠️ Coppola 2024 cap. 11 l.1131 dice «A_pix = 0.75 × 10⁶ m²» para VIIRS 750 — inconsistencia **dentro del canon**; el OSF confirma 11.081.250 (`21_results.json`, error 0,17 %) → nuestro valor es el correcto |
| fondo | `:462` anillo 5–25 km, `:483` mediana; `:947` `Planck(t_bg)`; **sin** kernel local en el bloque contextual | Campus 2022 l.428-429: «arithmetic mean of pixels surrounding the active one/s» | DIVERGENCIA |
| R1 focal | **sólo en el path Test 1** `:1212-1219` (`ENABLE_FOCAL_CLUSTER_MAGNITUDE_VIIRS750 = True`); el bloque contextual `:980-1021` **no** lo tiene | — | asimetría entre paths: 632 / 1.076 records `test1_roi` con R1 vs 100 / 1.564 `ctx_cluster` (2026) |
| cap D9, R2 | `:997-1002`, `:1016-1021`, `:1242-1247` | — | activos: R2 con efecto 298 / 2.685 (11,1 %) |

**Nota de trazabilidad**: el campo `final_hotspot_source` del JSON (`ctx_cluster` /
`test1_roi` / `eruption` / `test1`) es de **posición**, escrito por
`resolve_honest_anchor` (`anchor.py:70-96`) DESPUÉS de los bloques de magnitud
(`process_viirs.py:1995-2004`). No dice qué bloque produjo `pc.vrp_mw`.

---

## 2. Hallazgos clasificados

### 2.1 CONFIRMADO · el área nominal fija es válida sólo sobre una malla remuestreada, y no remuestreamos — **severidad ALTA**

- **Paper**: Coppola 2014 §2.2 (`scratchpad/coppola2014.txt:235-247`), verbatim: *«high
  scan angles contribute to the growth of the projected ground spatial element (up to
  approximately 10 km² for scan angles of 55°) … This leads the radiance of a potential
  sub-pixel hot-spot to be integrated over a variable area … Thus, we cropped and resampled
  (into an equally spaced 1 km grid) … one hot-spot pixel, whose area is 2 km² in the
  original image, becomes two pixels with equal areas of 1 km² in the resampled image»*.
  Coppola 2012 §3.2 (`coppola2012.txt:161-175`) dice lo mismo con «UTM grid of 1 km».
  Campus 2022 l.413-415: «Resampling is performed in a UTM 51 × 51 km grid … keeping the
  nominal resolution of 750 m. This results in matrices of 67 × 67 pixels».
- **Nuestro**: `ENABLE_UTM_REGRID = False`; `ENABLE_NADIR_FIXED_PIXEL_AREA_{MODIS,VIIRS} = True`
  (verificado con `pipeline.profile`). `regrid.py` existe y no corre.
- **Prueba de que el coeficiente de MIROVA es «por celda nominal»**: `experiments/21_results.json`
  reconstruye `VRP / (ΣL_hot − ΣL_bk)` en el OSF v2.5 y da exactamente 18.900.000 / 11.081.250 /
  2.531.250 con `zenith_bin_stddev_of_median` de 5e-4 / 3e-4 / 5e-5: **el producto k·A que MIROVA
  aplica no cambia con el cenital**, porque su A es la de la celda remuestreada. La energía del
  píxel oblicuo se reparte en más celdas.
- **Equivalencia para la magnitud** (item 2c): nuestra integral es literalmente
  `Σ_píxeles A_i · k · ΔL_i` (`process_modis.py:1002-1003`, `process_viirs.py:1403-1404`,
  `process_viirs_mod.py:952-953`) con `A_i ≡ A₀`. Remuestrear un píxel de área real `A` en
  `A/A₀` celdas de área `A₀` y sumarlas da `k·A·ΔL`. Por lo tanto **usar el área real por píxel
  sin remuestrear reproduce la magnitud de MIROVA**, con dos condiciones que sí se cumplen en
  nuestro código: (i) el fondo no depende del área — `compute_bg_stats`
  (`detection_context.py:980-996`) opera sobre BT; (ii) ningún test de detección usa el área —
  `grep -n -i area pipeline/test1_integrated.py pipeline/detection_context.py` devuelve **0
  líneas**; los Tests 2/3 (dNTI/dETI) son índices de radiancia. El área entra en **una sola
  línea** por sensor: el producto k·A·ΔL.
- **Medido por pasada** (`03_pares_por_pasada.py`; par = record nuestro × fila ALERTA MIROVA
  CONS∪OCR del mismo bucket con |Δt| ≤ 20 min, nocturnas, 2026, 11 Tier A):

  | VIIRS375 | n | cenital med. | nuestro MW | MIROVA MW | ratio sin corregir | ratio × ley ATBD (B) | ratio × lineal (C) |
  |---|---|---|---|---|---|---|---|
  | 0–15° | 297 | 7,2 | 0,159 | 0,230 | 0,771 | 0,786 | 0,810 |
  | 15–25° | 248 | 21,7 | 0,146 | 0,235 | 0,657 | 0,797 | 0,878 |
  | 25–35° | 221 | 31,9 | 0,107 | 0,200 | 0,576 | 0,872 | 0,988 |
  | 35–50° | 351 | 42,6 | 0,093 | 0,210 | 0,494 | 0,813 | 1,173 |
  | 50°+ | 479 | 58,6 | 0,076 | 0,170 | **0,447** | **0,859** | **1,502** |
  | global | 1.596 | | | | 0,580 [0,560–0,600] | **0,824 [0,795–0,846]** | 1,032 [1,002–1,060] |
  | pares > 2,0 | | | | | 33 (2,1 %) | 158 (9,9 %) | 299 (18,7 %) |
  | en banda [0,7–1,4] | | | | | 468 (29,3 %) | 663 (41,5 %) | 671 (42,0 %) |

  El brazo B **aplana** el gradiente (0,79–0,87 en los cinco bins, dentro del ruido) y deja un
  déficit **uniforme** de ~0,82. El brazo C sobre-corrige (1,50 a 50°+; 18,7 % de pares > 2).
  Por volcán con B (n ≥ 15): Villarrica 1,00 · PP 1,07 · PCC 1,00 · Isluga 0,73 · Tupungatito
  0,86 · Chaitén 1,33 → **6 de 8 en banda**; Láscar 0,62 y Lastarria 0,65 quedan bajo la banda
  (con A eran 3 de 8). VIIRS750 (n = 255): global 0,56 → 0,77 con B; bins ruidosos (n 19–80).
  MODIS: 50 pares, todos Láscar → **no se puede afirmar nada** (A90).
- **MIROVA también cae** por pasada (0,230 → 0,170 MW de nadir a 50°+): la corrección del
  remuestreo es *«partial»* (Aveni 2023 pp. 15-16, citado en `AUDIT_S128.md` §6quater). Lo
  nuestro cae 2,1× en el mismo tramo.

### 2.2 CONFIRMADO · el docstring de `viirs_pixel_areas` tiene un número mal leído, y la rama está muerta — **severidad BAJA hoy, ALTA si se reactiva**

- `pipeline/scan_geometry.py:193-196`: *«Empirical aggregated I-band pixel area varies only
  between ~0.32 and ~0.6 km² across the full swath (Cao et al. 2014)»*; `:212-214` factor
  `1 + (sec θ − 1)/2` con tope `2.0`.
- ATBD 423-ATBD-002 Tabla 2.2-1 (`scratchpad/atbd_geo.txt:1146-1176`), verbatim: I4
  **0.371 × 0.388** km en nadir, **0.80 × 0.789** al fin de barrido → 0,144 → 0,631 km²,
  **4,38×**. El «~2» del ATBD (`:1073-1074`: *«The pixel growth multiplier is limited to
  approximately 2 both along track and along scan»*) es **por eje**; el área es el producto.
  Ni el extremo de nadir (0,32) ni el crecimiento (1,9×) del docstring coinciden con el ATBD.
- **Rama muerta**: `grep -rn nadir_fixed pipeline/ scripts/ .github/` → 3 call-sites
  (`process_modis.py:463`, `process_viirs.py:713`, `process_viirs_mod.py:438`), los tres con el
  flag del perfil, y los dos flags son `True`. El único perfil con `false` está en
  `profiles/_archive/_dibella_n12_viirs_only.yaml:67`. **Ningún número publicado pasa por la
  fórmula errada.** Es una mina, como dice el doc de hoy.

### 2.3 CONFIRMADO · el fondo de magnitud no es el de Eq. 6, y además es distinto por sensor, por path y por volcán — **severidad ALTA** (es el déficit uniforme que queda tras corregir el área)

- Eq. 6 (`sp426_5.txt:353-359`) y Campus 2024 l.120-123 piden la **media aritmética de los
  píxeles que rodean** al activo/clúster, **excluyendo los activos** (§352-356).
- Nuestro `t_bg` es la **mediana** de BT del anillo **5–25 km** (`compute_bg_stats:995`), con
  los píxeles alertados adentro (`ENABLE_TEST1_K1_BG_EXCLUDE = False`), y luego
  `L_bg = Planck(mediana BT)` (`process_modis.py:965-968` lo justifica; no es lo que dice el
  paper). En Test 1 V375 el fondo es la mediana del anillo 1,5–3 km; en Test 1 MODIS/V750 es la
  mediana de **radiancia** del anillo 1–3 km, o el global si el volcán tiene
  `lbg_global_compatible` (Láscar, NdC, Lastarria); en el contextual, 5 volcanes usan kernel 3×3
  (`local_kernel_bg: true` en `volcanoes.yaml` para PCC, Villarrica, Chaitén, PP, Lastarria).
  Son **cuatro definiciones de fondo** para una sola ecuación, y dos de ellas dependen de
  claves per-volcán (MISSION l.77).
- La implementación fiel (`cluster_corona_background`, `vrp_regimes.py:108-186`) está escrita,
  cableada en los tres procesadores y **apagada** (`ENABLE_LOCAL_CLUSTER_MAGNITUDE* = False`).
  Lo dijo S125; sigue igual.

### 2.4 CONFIRMADO · MODIS usa B21 como banda primaria; MIROVA usa B22 — **severidad MEDIA**, nunca registrada

- `sp426_5.txt:141-144`: *«… band L21ok, by using the L21 or L22 radiance, depending on band 22
  saturation (or not)»* → B22 salvo saturación. Coppola 2024 cap. 11 l.1131 deriva el k para
  «λMIR = 3.959 µm» (B22).
- `process_modis.py:492-495`: `rad_mir = np.where(np.isnan(rad21), rad22, rad21)` → **B21 salvo
  inválida**; cabecera `:29` lo declara al revés del paper. Toda la cadena MODIS (NTI, fondo,
  ΔL, k con λ = 3,929) corre sobre la banda de baja ganancia. Efecto sobre la magnitud: de
  segundo orden en el coeficiente (λ difiere 0,8 %); el efecto principal es de **ruido**
  (B21 es la banda de baja ganancia, rango hasta 500 K — `BT_SAT_MIR_K_MODIS = 500`; su NEΔT
  nominal es mucho mayor que el de B22, **cifra no verificada en documento local → SIN RESPALDO
  numérico**). Con 50 pares MODIS-MIROVA en 2026 no se puede medir el impacto.

### 2.5 CONFIRMADO · R1 y R2 de S125 siguen en producción; ahora con conteo, y el ratio suma/máximo que S125 dejó SIN RESPALDO queda respaldado — **severidad ALTA**

Flags efectivos: `ENABLE_FOCAL_CLUSTER_MAGNITUDE = True`, `..._VIIRS750 = True`,
`ENABLE_SINGLE_PIXEL_SUB_MW_MODE = True` (`SUB_MW_REGIME_THRESHOLD_MW = 5.0`,
`SINGLE_PIXEL_MAX_CLUSTER_PIXELS = 3`). Conteo `01_r1_r2_vigencia.py` — universo: records
nocturnos con `pc.vrp_mw > 0`, 11 Tier A:

| ventana | sensor | n | R1 aplicado | R1 degradado a 1 píxel | R2 con efecto (n_px 2–3) | cap D9 |
|---|---|---|---|---|---|---|
| 2026 | MODIS | 5.159 | 4.549 (88,2 %) | **2.523 (48,9 %)** | 1.324 (25,7 %) | 640 (12,4 %) |
| 2026 | VIIRS750 | 2.685 | 732 (27,3 %) | 631 (23,5 %) | 298 (11,1 %) | 23 |
| 2026 | VIIRS375 | 7.169 | 0 | 0 | 816 (11,4 %) | 0 |
| jun–sep 2026 | MODIS | 2.244 | 2.178 (97,1 %) | **916 (40,8 %)** | 495 (22,1 %) | 451 (20,1 %) |
| jun–sep 2026 | VIIRS750 | 1.115 | 593 (53,2 %) | 507 (45,5 %) | 63 (5,7 %) | 3 |
| jun–sep 2026 | VIIRS375 | 2.690 | 0 | 0 | 211 (7,8 %) | 0 |

- R1 en VIIRS750 corre **sólo en el path Test 1** (`process_viirs_mod.py:1212-1219`); el bloque
  contextual (`:980-1021`) no lo tiene. S125 lo describió como «(+ VIIRS 750)» sin ese matiz.
- **Ratio suma/máximo** (R2 con efecto), reconstruido desde `anomaly_pixels` tomando los
  `n_pixels` píxeles más cercanos al centroide y aceptando sólo si su máximo coincide con
  `pc.vrp_mw` ± 0,002 MW: MODIS mediana **1,634** (n = 818, p90 2,34) · VIIRS375 **1,483**
  (n = 760, p90 1,97) · VIIRS750 **1,358** (n = 272). Por volcán: Chaitén 1,84 · Villarrica
  1,80 · Lastarria 1,77 · PP 1,75 · PCC 1,62 · Copahue 1,33 · Llaima 1,29 · Láscar 1,18 ·
  Isluga 1,11 · NdC y Tupungatito 1,00 (n 81–406). El «1,50» de S125 era correcto en orden de
  magnitud; ahora tiene dato detrás.
- Los números de línea de S125 §0 (`process_modis.py:1069/:1317`, `process_viirs.py:1768`)
  quedaron **OBSOLETOS**: hoy `:1097/:1347` y `:1502/:1927`.

### 2.6 CONFIRMADO · el cap de 5 MW del path D es una regla nuestra, activa, y no toca ninguna noche que MIROVA publique — **severidad BAJA para paridad, MEDIA para transparencia**

- `PATH_D_ONLY_CAP_MW = 5.0`, `PATH_D_ONLY_CAP_TBG_MAX_K = 270.0`; no tiene flag `enable_`
  propio (se apaga sólo con `None`). `docs/MIROVA_DIVERGENCES.md:248-254` reconoce que en SP426.5
  la cifra es *«interpretativo post-hoc, no gate algorítmico»*.
- 2026: **640 / 5.159** records MODIS nocturnos con `pc.vrp_mw > 0` llevan `d9_capped`; en los 50
  pares MODIS-MIROVA por pasada hay **0** capeados. El cap actúa exclusivamente sobre records que
  MIROVA no publica; no distorsiona la paridad medible, pero sí el MW publicado de esos records
  (que el frontend muestra si son *summit*).

### 2.7 FALSO (por definición del emparejamiento) · «f requerido 2,93× a 60°» de `docs/s131/REMUESTREO_LEY_DE_AREA.md` §4 — **severidad MEDIA** (cambia la conclusión de «necesario, no suficiente» a «suficiente»)

- `experiments/_s131_remuestreo/factor_requerido.py:86-100` empareja **cada record** nuestro
  contra el **máximo de la noche** de MIROVA (`cargar_mirova` colapsa por `(fecha, bucket)`),
  aunque el docstring diga «un par por (volcán, fecha, bucket)». Una pasada oblicua débil
  queda comparada con la mejor pasada de MIROVA de esa noche, que suele ser otra, más cerca del
  nadir: el gradiente se infla. Es el error que el propio `_s126_lib.py` documenta en su
  cabecera («comparar cada pasada contra el máximo de MIROVA de la noche infla el objetivo»).
- Con un par por noche (script 02, regla `_s126_lib`) el gradiente V375 es 0,80 → 0,60; **por
  pasada** (script 03) es 0,77 → 0,45 → f requerido a 58° = **1,72**, y el modelo del ATBD da
  ~1,9 ahí. Con B, el IC95 bootstrap del bin 50°+ es [0,81–0,93] y el de nadir [0,74–0,84]:
  se solapan. Sin corregir son [0,41–0,50] contra [0,70–0,81], sin solape.
- **Consecuencia**: el área **explica el gradiente completo**; lo que sobra es el déficit
  uniforme (§2.3, §2.5). La tabla de §4 del doc de hoy y su frase «condición necesaria, no
  prueba» hay que reescribirlas con la definición por pasada. El resto del doc (mecanismo,
  cita, docstring, bow-tie ya hecho en VIIRS) se sostiene.

### 2.8 SIN RESPALDO · «el área es multiplicador en la integral de radiancia del Test 1» (A67, repetido en `REMUESTREO_LEY_DE_AREA.md` §2 y §6)

- En el código de hoy **el área no entra en ningún test de detección**: `test1_integrated.py`
  (`compute_test1_mir`, `compute_test1_nti`) integra `Σ max(0, L − L_bg)` sin área
  (`:411-436`), y `detection_context.py` no tiene la palabra `area`. La única vía por la que un
  cambio de área pudo apagar detecciones en S103 es aguas abajo (piso de VRP, hoy 0; o gates
  sobre MW). El mecanismo tal como A67 lo enuncia no está en el código y no se puede reconstruir
  read-only sin historial. **Corolario útil**: una ley de área correcta cambia **sólo la
  magnitud**; el A/B no necesita medir FN por este mecanismo (sí por cualquier gate en MW que
  quede, hoy ninguno con piso 0).

### 2.9 OBSOLETO / matiz · «MIROVA es plano» (S130) vale por noche, no por pasada

Por pasada MIROVA baja de 0,230 a 0,170 MW (V375) entre nadir y 50°+. Sigue siendo mucho más
plano que lo nuestro (0,159 → 0,076), y la conclusión de S130 («el sub-reporte es nuestro»)
se mantiene. Pero «plano» es la lectura del máximo por noche.

### 2.10 CONFIRMADO · lo que ve el operador para VIIRS375 no es `pc.vrp_mw` — **severidad ALTA para la pregunta del encargo**

- `frontend/index.html:1015` `USE_F5_CORE = persistedFlag("vrp_f5_core", true)`; `:1097` y
  `:3321-3323` usan `f5CoreMagnitude` para sensores VIIRS sin `_750`: suma de los
  `anomaly_pixels` a ≤ 0,75 km del píxel de máxima energía (dentro de `inner_radius` del
  centroide) o con `bt_k ≥ 295`.
- Replicado en `04_display_f5_vs_pc.py` sobre los mismos pares por pasada (n = 1.609): ratio vs
  MIROVA **0,681 [0,660–0,707]** para lo que se muestra, contra **0,580 [0,562–0,603]** para
  `pc.vrp_mw`; el display coincide con `pc.vrp_mw` en el **5,7 %** de los records. Por volcán:
  PCC 0,66 → 1,03 · Chaitén 0,98 → 1,31 · Láscar 0,42 → 0,53 · Lastarria 0,47 → 0,57 · Isluga
  0,53 → 0,58 · PP 0,79 → 0,90 · Villarrica 0,90 → 0,95 · Tupungatito 0,64 → 0,65.
- El número publicado **no se persiste en ningún JSON** y no es el que auditan los scripts
  (todos usan `pc.vrp_mw`, A10). Para MODIS y VIIRS750 el dashboard sí muestra `pc.vrp_mw`.

### 2.11 CONFIRMADO (no re-auditar) · lo que está bien

- Coeficientes y áreas nominales: `process_modis.py:82` 18,9 · `process_viirs_mod.py:63` 19,7
  · `process_viirs.py:74` 18,0; k·A = 18,9e6 / 11.081.250 / 2.531.250 = OSF v2.5 (`21_results.json`).
- Planck en los tres sensores con constantes compartidas (`pipeline/constants.py`); ΔL clip a 0;
  conversión `/1e6` a MW; `store.py` no toca `pc.vrp_mw` salvo el cap de sanidad 50 GW
  (`:148-150`) — `_filter_pixels_by_distance` (`:213-259`) recalcula sólo `vrp_mir_mw`/`hotspot_*`.
- Pisos de VRP en 0 (`MIN_VRP_MW_* = 0.0`, `MODIS_VENT_VRP_FLOOR_MW = 0.0`) — S130 aplicado.
- VIIRS bow-tie: `FLAG_DNS` en `process_viirs.py:80` enmascara `Bowtie_Deleted`; el ATBD
  (`atbd_geo.txt:1370-1374`) confirma que la deleción along-track es del sensor.
- `vrp_tir_mw` (Aveni/TIRVolcH) no entra a `pc.vrp_mw` (`ENABLE_VRP_TIR_OUTPUT = False`; grep
  sin cruce con `primary_cluster`).

### 2.12 Item 3 del encargo · qué da y qué no da el ATBD sobre área(θ)

**Da** (`scratchpad/atbd_geo.txt`, PDF `documentacion/VIIRS_Geolocation_ATBD_2014.pdf`):
- Tabla 2.2-1 (p. 13): HSI nadir / fin de barrido por banda (transcrita en §2.2).
- §2.2.1.1 (p. 14-15): *«At scan angles within +/- 31.589 degrees of nadir … groups of three
  samples are aggregated … between 31.589 degrees and 44.680 degrees … a sample aggregation
  factor of two is used, transitioning to a factor of one beyond +/- 44.680 degrees»*; para las
  M: «742 m by 259 m nadir footprint grows to approximately 1600 m by 1579 m at the end of scan».
- §3.3.1.1 (p. 27): *«The along-scan aggregation factor ranges from 3:1 at nadir to 1:1 at the
  maximum 56.063 degree scan angle … The discontinuities in this curve identify the aggregation
  factor transition points»*; *«The apparent Earth zenith angle of a LOS at a 55 degree scan
  angle is increased to approximately 65 deg by Earth curvature»*.
- §3.3.2.1.2 (p. 50): las tres zonas con conteo de muestras (I-band 7104 → 2368 en zona 3:1,
  2944 → 1472 en 2:1, 2560 sin agregar) — confirma que las **I-bands se agregan igual** que las M.
- §3.4.2.1 (p. 85) y Figura 3.3-1 (p. 28): la curva de crecimiento **es un gráfico, no una
  tabla ni una fórmula**.

**No da**: ninguna expresión área(θ_scan) ni valores intermedios tabulados (la Figura 2.2-7,
p. 16, trae un par de cotas a 35° y 50° en un esquema que `pdftotext` no deja legible con
confianza; no las uso).

**Lo que hice, declarado como modelo y no como transcripción** (`02_correccion_area_por_angulo.py:63-90`):
esfera R = 6371 km, h = 829 km; scan desde el cenital del record por
`sin θs = R sin θz / (R+h)`; crecimiento along-track = rango inclinado / h; along-scan crudo =
along-track / cos θz; agregación 3/2/1 por zona de scan; `f = g_track · g_scan_crudo · agg/3`.
Reproduce los anclajes del ATBD: 1,00 en nadir; **4,52 a 56,06° de scan** contra 4,38 de la
Tabla 2.2-1 (+3 %); along-track 2,17 contra 2,16; «growth factor of 6 along scan» sin agregar →
6,2. Los saltos: 1,79 → 1,20 en 31,589° (θz ≈ 36,3°) y 2,49 → 1,26 en 44,680° (θz ≈ 52,6°).
Con `n = 221–479` por bin, el diente de sierra **no se resuelve** en los datos (S128 ya lo dijo);
lo que sí se resuelve es que la media del modelo por bin aplana el ratio (§2.1).

---

## 3. Recomendaciones, en orden

1. **Cerrar el área con la geometría del propio granule, no con un modelo** (severidad alta,
   cambio de pipeline → A45: tag + confirmación). El L1B trae lat/lon por píxel; el área real
   es `|Δ along-scan| × |Δ along-track|` entre vecinos, que incluye los saltos de agregación sin
   modelar nada y vale para MODIS igual (sin el bow-tie, que en MODIS sí queda pendiente).
   Implementarla como nueva rama de `viirs_pixel_areas` / `modis_pixel_areas` bajo un flag
   OFF, y correr el A/B de 3 brazos (A66): control · área-geolocalizada · área-geolocalizada +
   corona Eq. 6. **Criterio pre-registrado**: ratio por bin cenital plano (bin 50°+ / bin 0–15°
   entre 0,9 y 1,1 por pasada), volcanes en banda ≥ 6/8 en V375, 0 noches MIROVA perdidas,
   pares > 2,0 ≤ 10 %. Validación con `03_pares_por_pasada.py` sobre el `data_subdir` del brazo.
2. **Reescribir §4-§5 de `docs/s131/REMUESTREO_LEY_DE_AREA.md`** con el emparejamiento por
   pasada (f requerido 1,72, no 2,93; «suficiente», no «necesario») y arreglar el docstring de
   `scan_geometry.py:187-215` (0,144 → 0,631 km², 4,38×, «~2 por eje»). Corregir el docstring de
   `factor_requerido.py` (dice «un par por (volcán, fecha, bucket)» y no lo hace) o el código.
   Sin tocar el número publicado; cero riesgo.
3. **Una sola magnitud publicada, trazable** (severidad alta para OVDAS). Dos opciones, decisión
   de Nicolás: (a) persistir `display_vrp_mw` (o `f5_core_vrp_mw`) en el record cuando
   `USE_F5_CORE` sea el default, para que el número del dashboard exista en el JSON y entre a las
   auditorías; o (b) volver el default a `pc.vrp_mw` y que F5' sea toggle. Validar con
   `04_display_f5_vs_pc.py` (hoy 0,68 vs 0,58) y con la regla «lo que se audita es lo que se
   publica».
4. **El A/B del fondo y de la suma que S125 pidió sigue siendo el correcto, y ahora tiene el
   tercer brazo**: apagar R1 + R2 + encender la corona Eq. 6, con el área geolocalizada como
   base. Medir por volcán (S126) y por pasada. Esperable: el 0,82 uniforme que queda tras el área
   se mueve hacia 1; Chaitén (1,33 con área) es el canario de sobre-reporte.
5. **B22 primaria en MODIS** (`process_modis.py:492-495` invertir el `np.where`; cabecera `:29`).
   Cambio de una línea bajo A45. Validación: MODIS Láscar por pasada (n = 50) antes/después, y
   `diag_sigma_bg_k` MODIS mensual (esperable que baje).
6. **Cap D9**: mantenerlo, pero exponerlo — el flag `d9_capped` ya viaja en el record; que el
   dashboard lo etiquete cuando muestre un record capeado (hoy 20 % de los MODIS recientes).
   Sin cambio de pipeline.
7. **No extender** la corrección de área a MODIS por extrapolación: 50 pares, un volcán. Primero
   más ground truth MODIS (o el cruce con el OSF, que trae `Tot_Lmir_hot` y cenital), después el
   A/B.

---

## 4. Lo que NO pude verificar

- El NEΔT de B21 vs B22 (§2.4): no está en `documentacion/MODIS_L1B_UserGuide_C7.md` ni en las
  otras fuentes locales que revisé; queda sin cifra.
- El mecanismo por el que nadir-fijo redujo detecciones en S103 (A67): requiere historial git;
  el encargo lo prohíbe.
- El cruce de nuestro `sensor_zenith_deg` contra `Zenith_Sat_deg` del OCR: sólo 35 filas con el
  campo, mediana de la diferencia 0,7°, p90 |dif| 27° — insuficiente para afirmar nada.
- El diente de sierra de las zonas de agregación en los datos (n por bin de 5° < 100).
