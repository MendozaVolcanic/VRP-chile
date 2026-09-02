# Beyond MIROVA Extensions — backlog de mejoras documentadas (vivo)

> **Doc vivo de mejoras que NO son parte del clon MIROVA literal pero quedan documentadas como caminos futuros**.
>
> **Regla operacional**: VRP Chile objetivo PRIMARIO = clon MIROVA NRT literal (papers Coppola/Laiolo/Massimetti/Campus/Aveni). Extensiones beyond MIROVA quedan en este backlog hasta que (a) clon literal esté validado completamente, (b) tengamos resources para investigar, (c) haya justificación operacional o científica para implementarlas.
>
> **Cada item documentado**: hipótesis + cita bibliográfica + costo estimado + decisión.

## 1. Cloud filtering "beyond MIROVA"

MIROVA admite explícitamente que su cloud handling per-scene está **ausente** (Coppola 2016 SP 426.5 §247-249 + §712-728, Coppola 2019 §1443-1480). El cap S71 (5 MW @ t_bg<270K) es la mitigación clon-MIROVA-compatible. Pero hay alternativas publicadas:

### EXT-1 — Fan, Tang, Wu 2015 LST extraction under cirrus MODIS

> **Corrección S72 F1.12**: Perplexity (F1.9) citó como "Zhu et al. 2023 DOI 10.3390/rs150509942". Validación Crossref reveló que el paper REAL es **Fan, Tang, Wu 2015** "Daytime Land Surface Temperature Extraction from MODIS Thermal Infrared Data under Cirrus Clouds" en MDPI **Sensors** (no Remote Sensing). DOI canónico: `10.3390/s150509942` (sin la "r"). AP21 confirmado: Perplexity hallucina autores+años. Paper descargado como `documentacion/Fan_2015_DaytimeLST_Cirrus.pdf`.

**Source corregido**: Fan, Tang, Wu 2015 "Daytime Land Surface Temperature Extraction from MODIS Thermal Infrared Data under Cirrus Clouds" — MDPI Sensors 15(5):9942-9962, DOI `10.3390/s150509942`, **OA**.

**Mecanismo**: fórmulas y thresholds BTD (Brightness Temperature Difference) específicos para filtrar falsos hotspots por cirrus en MODIS bandas 31-32.

**Pros**:
- Cita bibliográfica directa ⭐⭐⭐.
- OA accesible.
- Más específico que Frey 2008 (cloud mask genérico).

**Cons**:
- NO es MIROVA (sería extensión).
- Requiere lectura del paper para implementación exacta.

**Costo estimado**: 1-2 semanas (lectura + implementación + tests + A/B).

**Decisión**: Backlog. Implementar como `enable_btd_cirrus_filter_zhu2023: true` en profile aislado `mirova_equivalent_btd_cirrus_v1.yaml` cuando clon literal esté validado.

### EXT-2 — Frey 2008 MOD35 collection 5 cloud mask

**Source**: Frey et al. 2008 "Cloud Detection with MODIS Part I: Improvements in MODIS Cloud Mask for Collection 5" — AMS J. Atmos. Ocean. Tech. DOI `10.1175/2008JTECHA1052.1`, **OA**.

**Mecanismo**: tests BTD operacionales producto MOD35: split-window cirrus (BT31-BT32), high-cloud tests (BT35-BT33, BT35-BT34), water-vapor channels (banda 27).

**Decisión**: Backlog. Referencia canónica MODIS BTD. Útil como soporte teórico de Fan 2015.

### EXT-3 — Valade 2019 MOUNTS ML cloud filter

**Source**: Valade et al. 2019 "Towards global volcano monitoring using multisensor sentinel missions and artificial intelligence: The MOUNTS monitoring system" — Remote Sensing MDPI, DOI `10.3390/rs11131528`.

**Mecanismo**: ML-based cloud filtering (CNN) sobre imágenes Sentinel.

**Decisión**: Backlog informativo. NO clonar literal (es ML, no MIROVA). Pero útil como benchmark conceptual.

## 2. Multi-sensor fusion extensions

### EXT-4 — MOUNTS architecture multi-sensor

**Source**: Valade 2019 MOUNTS — arquitectura S1+S2+S5P+MODIS fusion.

**Aplicabilidad**: VRP Chile actualmente integra MODIS Terra/Aqua + VIIRS I + M. Extensiones posibles:
- Sentinel-2 SWIR (Massimetti 2020 ya validó S2 SWIR vs MIROVA).
- Sentinel-5P (TROPOMI) SO2.
- Landsat 8/9 OLI thermal.
- Multi-temporal fusion para reducir noise.

**Costo**: 4-6 semanas (cada sensor requiere fetch+parse+calibration).

**Decisión**: Backlog futuro. Prioridad: completar clon MIROVA primero.

### EXT-5 — Schroeder 2022 VIIRS/MODIS/OLI fire characteristics

**Source**: Schroeder 2022 DOI `10.3390/rs14194745`, OA.

**Aplicabilidad**: comparación cuantitativa cobertura/resolución/tasa de detección entre los 3 sensores. Calibra expectativas operacionales.

**Decisión**: Backlog reference. Útil para discussion section paper open source.

## 3. ML / Deep Learning approaches

### EXT-6 — HotLINK CNN Saunders-Shultz 2024

**Source**: Saunders-Shultz et al. 2024 "Automatic identification and quantification of volcanic hotspots in Alaska using HotLINK" — Frontiers Earth Sci 12:1345104, DOI `10.3389/feart.2024.1345104`, **OA + código GitHub `csaundersshultz/HotLINK`**.

**Mecanismo**: CNN entrenada VIIRS+MODIS. Benchmark vs MIROVA: **+22% detecciones, -12% FPs**.

**Aplicabilidad**:
- NO clonar literal (ML, no MIROVA).
- Replicar su benchmark sobre nuestros vols chilenos sería valioso (validation independiente).
- Estudio de técnicas (no implementación) puede revelar approaches útiles.

**Decisión**: Backlog. F1.14 (corriendo) explora código para estudio comparativo.

### EXT-7 — PyRawS ESA Phi-Lab S2 thermal

**Source**: PyRawS ESA Phi-Lab — Sentinel-2 RAW thermal hotspot classification + segmentación.

**Decisión**: Backlog futuro. Solo aplicable si extendemos a S2 (EXT-4).

## 4. Validation extensions

### EXT-8 — AVTOD ASTER Volcanic Thermal Output Database

**Source**: Reath, Pritchard, Pieri, **Coppola**, Moruzzi, Alcott 2019 — DOI `10.1016/j.jvolgeores.2019.03.019` JVGR (paywall).

**Mecanismo**: catálogo manual 330 volcanes latinoamericanos 2000-2017 a 90m ASTER, ya validado cross-MIROVA por sus propios autores. Cubre todos nuestros vols Tier A chilenos.

**Aplicabilidad CRÍTICA**:
- **Ground truth INDEPENDIENTE de OSF v2.5** (metodología distinta: ASTER manual vs MIROVA NRT automático).
- Permite **doble cross-validation** VRP Chile (vs MIROVA + vs AVTOD).
- Identificar vols donde MIROVA diverge de AVTOD → casos especiales documentables.

**Decisión**: **TOP PRIORITY DESCARGA** (F1.12 corriendo). Si lo conseguimos, integrar al workflow validation antes de paper publication.

### EXT-9 — Pallister 2013 Chaitén FLIR

**Source**: Pallister et al. 2013 USGS/JVGR — FLIR ThermaCAM SC640 Chaitén, datos co-publicados SERNAGEOMIN.

**Aplicabilidad**: validation cross-method para Chaitén (campañas field-based). Único caso conocido publicado de medición térmica field-based en vol chileno.

**Decisión**: Backlog ground truth tercer fuente. F1.12 corriendo.

### EXT-10 — AVA ASTER Volcano Archive NASA JPL

**Source**: NASA JPL — 1,430 volcanes activos AST_09T, open con registro.

**Aplicabilidad**: combinable con AVTOD+MIROVA para curvas VRP/LST multi-sensor.

**Decisión**: Backlog. Requiere registro NASA JPL.

## 5. Sub-pixel signal recovery

### EXT-11 — Two-component model Coppola 2024 Eq.14-16 (lava lake sub-píxel)

**Source**: Coppola 2024 Springer book chapter §1132-1141 (two-component) + §"Lava
lakes" (Burgi-Coppola, Eq.15-16, T_e asumido).

**Mecanismo**: `L_hotpix(λ, T_hotpix) = f_hot · B(λ, T_hot) + (1 − f_hot) · B(λ, T_bk) (Eq. 14)`.
Despeja A_hot asumiendo T_e (1000 K lava lake) → φ_rad = A_hot σε (T_e⁴ − T_bk⁴) (Eq.16).

**Caveat (reconfirmado S99 contra fuente primaria)**: **MIROVA NRT NO usa Eq.14-16**.
El capítulo lo presenta en sección "Applications" como **producto de 2º nivel manual,
calibrado caso por caso** ("requires specific calibrations", "valid only within the
limits of the assumptions"). MIROVA NRT es UN algoritmo por SENSOR uniforme (ver
MISSION.md hecho canónico S99). Por eso es **beyond-MIROVA, NO clon literal**.

**Estado S99 (importante)**: la función **`compute_vrp_lava_lake_eq16` YA está
construida + 10 tests** (`pipeline/vrp_regimes.py:105`, `tests/test_vrp_regimes_lava_lake.py`)
y **cableada flag-OFF** (S99 PR #326: `enable_test1_lava_lake_eq16`, gate per-vol
`lava_lake_magmatic` en Villarrica). Era un hallazgo dormido (DF-1 de
`docs/S99_DORMANT_FINDINGS_AUDIT.md`) — construida S57, nunca conectada. **Medida en el
A/B S99 por completitud** (perfil `_s99_test1_eq16`), pero **NO adoptable a
`mirova_equivalent`** (sería drift; MISSION.md anti-patrón S99).

**Caveat de calibración**: con T_e=1000 K el test canónico Villarrica da ~0.05 MW vs
MIROVA 0.31 (subestima ~6×). El A/B S54 que debía calibrar T_e (600-1400 K) nunca se
corrió → por eso quedó dormida. Si se prioriza para la fase independiente: calibrar
T_e empíricamente vs CSV MIROVA Villarrica.

**Valor beyond-MIROVA**: para la fase (2) "herramienta independiente / mejor que
MIROVA", Eq.16 es el método físicamente correcto para magnitud de lava lakes sub-píxel
(Villarrica, Erebus-tipo) — donde el Wooster del clon literal subestima por estar fuera
de rango (<600 K). Citable como contribución propia. NO encender en operacional clon.

**Decisión**: beyond-MIROVA priorizado para fase post-clon. Código ya listo (solo falta
calibrar T_e + decidir reporte dual "VRP Wooster" + "VRP lava lake"). Diseño completo en
`docs/superpowers/specs/2026-05-17-vrp-three-regimes-design.md` (incluye R3 crater lake
Eq.25 — NO escrito aún). Hermano: EXT-12 TIRVolcH (otra vía sub-MW low-T).

### EXT-12 — TIRVolcH Aveni 2024 single-band TIR low-T

**Source**: Aveni et al. 2024 RSE "TIRVolcH" — DOI `10.1016/j.rse.2024.114388` (YA tenemos como `Aveni_2024_TIRVolcH_RSE.pdf`).

**Mecanismo**: single-band TIR VIIRS I5 11.45 μm, matrices REF mensuales. **Sensibilidad 0.5 K sobre background, FP 1.8%**.

**Aplicabilidad**: detección sub-MW Tier A Muy Bajo régimen (Villarrica/Chaiten/PCC). Es extensión natural si necesitamos ir más allá de Tests 2/3 MIR.

**Decisión**: Backlog priorizado para fase post-clon-literal. Re-procesar exhaustivo el PDF que ya tenemos.

## 6. Algorithmic refinements MIROVA-internal (no son extensions)

Estos sí son parte del clon MIROVA literal, sólo que pendientes de implementar:

### INT-1 — HT1.5-NEW-1 cluster scene-wide aggregation

**Source**: Massimetti 2024 §561-562 ("5 km radius + sum scene-wide").

**Status**: **EN RE-INTERPRETACIÓN**. F1.8 (Thesis Ch2 per-cluster CONTEXTUAL) + F1.9 (state-of-the-art primary_cluster) sugieren que nuestro `primary_cluster` actual puede ser correcto. Esperar A/B unsuitable filters (PR #115) para evaluar.

**NO es extension beyond MIROVA** — si valida, sería parte del clon literal.

### INT-2 — HT1.5-NEW-3 Method-2 weekly local minima

**Source**: Coppola 2023 §530-540 ("local VRP minima are removed").

**Status**: Post-processing temporal MIROVA. **NO aplicable a NRT real-time** (es agregación weekly post-NRT).

**Aplicación posible**: dashboard layer (mostrar mediana weekly en lugar de último overpass).

**NO es extension beyond MIROVA** — es feature dashboard, no algorithm.

## 7. Estado actualizado (post-F1.10 + F1.11)

### Refs Tier 1 disponibles

| Ref | Status | Aplicabilidad |
|---|---|---|
| **Fan 2015 LST cirrus** ⭐⭐⭐ | ✅ F1.12 descargado `Fan_2015_DaytimeLST_Cirrus.pdf` | EXT-1 cirrus filter "beyond MIROVA" (corrige hallucinación "Zhu 2023") |
| Frey 2008 MOD35 | ✅ Descargado F1.10 | EXT-2 base teórica BTD |
| MOD06 ATBD Platnick | ✅ F1.12 descargado `Platnick_MODIS_MOD06_ATBD.pdf` | EXT-2 soporte canónico |
| **AVTOD Reath 2019** ⭐⭐⭐ | ✅ Ya teníamos (`AVTOD_Reath_2019.pdf` → renamed `AVTOD_Reath_2019.pdf`) | EXT-8 ground truth secundario CRÍTICO |
| HotLINK paper | ✅ Descargado F1.10 | EXT-6 ML benchmark |
| HotLINK GitHub | ✅ F1.14 exploración (5 conceptos transferibles identificados) | EXT-6 técnicas comparativas |
| TIRVolcH Aveni 2024 | ✅ Ya teníamos (`Aveni_2024_TIRVolcH_RSE.pdf` → renamed `Aveni_2024_TIRVolcH_RSE.pdf`) | EXT-12 sub-MW low-T |
| Pallister 2013 Chaitén | ✅ F1.12 descargado `Pallister_2013_Chaiten_rhyolite_dome.pdf` (secuencia eruptiva, NO FLIR como Perplexity citaba) | EXT-9 context Chaitén |
| **Bernstein 2013 Chaitén FLIR** ⭐ (bonus) | ✅ F1.12 descargado `Bernstein_2013_Chaiten_FLIR_thermal.pdf` | EXT-9 validation field-based REAL FLIR paper |
| Valade 2019 MOUNTS | ✅ Descargado F1.10 | EXT-3 ML cloud + EXT-4 multi-sensor |

### Prioridad orden post-clon-literal

1. **EXT-8 AVTOD** (cross-validation ground truth) — más crítico para paper publication.
2. **EXT-1 Fan 2015 BTD cirrus** — fix D9 "beyond MIROVA" con base bibliográfica directa.
3. **EXT-12 TIRVolcH** — sub-MW detection enhancement.
4. **EXT-6 HotLINK study** (no implementación, estudio).
5. **EXT-9 Pallister 2013** — campañas field validation (cuando tengamos colaboración SERNAGEOMIN).

## 8. Decisiones documentadas

| Decisión | Justificación | Fecha |
|---|---|---|
| Cap 5 MW path D D9 = clon literal, NO extension | Base directa Coppola 2016 §687 ("FPs <5 MW") | S71 PR #112 |
| Method-2 weekly minima → dashboard layer | NO aplicable a NRT real-time | S72 F1.8 |
| Two-component Eq.14-16 → no perseguir operacional | MIROVA NRT no lo usa, requiere T_hot assumption | S71 papers review |
| C2 distinto Muy Bajo → refutado | Laiolo 2017 §208-213: sensibilidad MIROVA nativa 1 MW basta | S72 F1.8 |
| `mirova_center` Tupungatito como anchor empírico | A30: anchor de cluster selection, no verdad geológica | S72 F1.7 |

## 9. Aprendizaje meta A32

**A32 (S72 2026-05-21)** — **separar claramente "clon MIROVA literal" vs "extensions beyond MIROVA"** en docs.

Antes: los "drifts" iban todos a `docs/MIROVA_DIVERGENCES.md` (divergencias vs MIROVA, deseables cerrar) y los "experimentos" a `experiments/`. Pero **mejoras potencialmente publicables (Zhu BTD, HotLINK study, AVTOD validation)** son territorio distinto: NO son drifts a cerrar, son features que podrían diferenciar VRP Chile como contribución científica propia.

Este doc `BEYOND_MIROVA_EXTENSIONS.md` consolida ese tercer territorio. Tres categorías:
- **MIROVA_DIVERGENCES.md**: drifts del clon literal — cerrar.
- **MIROVA_DIVERGENCES_CATALOG_S71.md**: hipótesis priorizadas para investigar.
- **BEYOND_MIROVA_EXTENSIONS.md** (este doc): mejoras potencialmente publicables como contribución propia.

## 10. EXT-12 PCC_VENT_ANCHOR — centroide térmico empírico como ancla dual (S81)

**Origen**: S48 D9-MODIS fix derivó un centroide térmico empírico para
PuyehueCordonCaulle promediando scenes MODIS con n_pixels>2500 del archive
`mirova-tif-archive/data/tif/PuyehueCordonCaulle/*MODIS*.tif`. Resultado:
`(-40.582, -72.131)` — aproximadamente la zona del **lacolito 2011 SE**
del cone morfológico. El vent canonical (`vent_lat/vent_lon`) queda a
~6.7 km al N del centroide térmico.

**Por qué se descartó S81 como `mirova_center_lat/lon`**: el clon MIROVA
literal exige usar las coords del KMZ oficial MIROVA VIIRS375
(`-40.5903, -72.1187` — centro del bbox UTM 51×51 km). Diferencia 1.39 km.
Adoptado S81 Nicolás explícito; preserva paridad bit-a-bit con MIROVA web
para R2 pixel-level. Tag `pre-s81-pcc-mirova-center`.

**Por qué vale guardar el centroide térmico como extension**: en PCC
~98% detecciones son VIIRS (donde el clon literal pesa más). Pero MODIS
del lacolito queda ~11-18 km off del `mirova_center` KMZ (el centroide
real térmico está al SE del bbox MIROVA, no en su centro). Para MODIS
específicamente, anclar `vent_anchored_clustering` al lacolito térmico
mejoraría recall + reduciría drift documentado S47.

**Idea EXT-12 — dual anchor MIROVA + empírico**:

```yaml
# Hipótesis: usar mirova_center para ROI bbox (paridad MIROVA) y un
# vent_anchor distinto para cluster anchoring (centroide térmico).
volcanoes:
  PuyehueCordonCaulle:
    mirova_center_lat: -40.5903   # KMZ MIROVA — define ROI bbox
    mirova_center_lon: -72.1187
    vent_anchor_modis_lat: -40.582   # NUEVO — centroide térmico empírico
    vent_anchor_modis_lon: -72.131   # solo para vent_anchored_clustering MODIS
```

**Implementación** (cuando se priorice EXT-12):
1. Agregar `vent_anchor_<sensor>_lat/lon` opcionales a `volcanoes.yaml`.
2. En `get_effective_vent(sensor)`: si `vent_anchor_<sensor>_*` existe,
   priorizarlo sobre `mirova_center_*` solo para clustering, no para ROI.
3. A/B test PCC MODIS 30d profile baseline vs dual-anchor. Métrica: recall
   MODIS + ratio vs MIROVA + drift centroide cluster.
4. R2 pixel-level: confirmar que el bbox ROI sigue alineado con MIROVA web
   (el cambio es interno al clustering, no afecta el bbox).
5. Generalizar a otros volcanes con offset vent-térmico documentado
   (Tupungatito 4.86 km SE del KMZ, Planchon-Peteroa 2.02 km N).

**Por qué es "beyond MIROVA"**: MIROVA usa un solo centro por volcán.
Dual-anchor es una innovación nuestra que reconoce que el vent
morfológico y la zona caliente real pueden diverger en volcanes complejos
(lacolitos, fisuras, lagos). Citable como contribución metodológica.

**Estado**: idea preservada S81. NO accionar hasta clon MIROVA literal
completo (post F2.1 + F46 completo + reproc histórico Tier A).

## 11. Aplicación futura

Cuando termine el clon literal (post adopción F2.1 unsuitable filters + Tupungatito mirova_center):

1. **Paper open source VRP Chile**: describir clon MIROVA + listar extensions documentadas en este doc como "future work".
2. **Iteración EXT-1 Fan 2015**: implementar BTD cirrus filter como primera extension experimental.
3. **EXT-8 AVTOD cross-validation**: integrar al workflow validation antes de publication.

Cuando Nicolás decida priorizar alguna extension específica → mover de "backlog" a "in_progress" + abrir tarea + iniciar implementación.
