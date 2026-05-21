# Beyond MIROVA Extensions — backlog de mejoras documentadas (vivo)

> **Doc vivo de mejoras que NO son parte del clon MIROVA literal pero quedan documentadas como caminos futuros**.
>
> **Regla operacional**: VRP Chile objetivo PRIMARIO = clon MIROVA NRT literal (papers Coppola/Laiolo/Massimetti/Campus/Aveni). Extensiones beyond MIROVA quedan en este backlog hasta que (a) clon literal esté validado completamente, (b) tengamos resources para investigar, (c) haya justificación operacional o científica para implementarlas.
>
> **Cada item documentado**: hipótesis + cita bibliográfica + costo estimado + decisión.

## 1. Cloud filtering "beyond MIROVA"

MIROVA admite explícitamente que su cloud handling per-scene está **ausente** (Coppola 2016 SP 426.5 §247-249 + §712-728, Coppola 2019 §1443-1480). El cap S71 (5 MW @ t_bg<270K) es la mitigación clon-MIROVA-compatible. Pero hay alternativas publicadas:

### EXT-1 — Zhu et al. 2023 BTD cirrus filter MODIS

**Source**: Zhu et al. 2023 "Daytime LST Extraction from MODIS TIR under Cirrus Clouds" — Remote Sensing MDPI, DOI `10.3390/rs150509942`, **OA**.

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

**Decisión**: Backlog. Referencia canónica MODIS BTD. Útil como soporte teórico de Zhu 2023.

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

### EXT-11 — Two-component model Coppola 2024 Eq.14-16

**Source**: Coppola 2024 Springer book chapter §1132-1141.

**Mecanismo**: `L_hotpix(λ, T_hotpix) = f_hot · B(λ, T_hot) + (1 − f_hot) · B(λ, T_bk) (Eq. 14)`. Permite recovery A_hot dado assumption sobre T_hot.

**Caveat**: **MIROVA NRT NO usa Eq.14-16** (Coppola 2024 §1159-1171: "requires assuming T_hot"). Es teoría no operacional.

**Decisión**: Backlog descartado para operacional. Útil para discussion paper.

### EXT-12 — TIRVolcH Aveni 2024 single-band TIR low-T

**Source**: Aveni et al. 2024 RSE "TIRVolcH" — DOI `10.1016/j.rse.2024.114388` (YA tenemos como `1-s2.0-S0034425724004140-main.pdf`).

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
| Zhu 2023 BTD cirrus | 🔄 F1.12 descarga | EXT-1 cirrus filter "beyond MIROVA" |
| Frey 2008 MOD35 | ✅ Descargado F1.10 | EXT-2 base teórica BTD |
| MOD06 ATBD Platnick | 🔄 F1.12 descarga | EXT-2 soporte canónico |
| AVTOD Reath 2019 | 🔄 F1.12 descarga (paywall) | EXT-8 ground truth secundario |
| HotLINK paper | ✅ Descargado F1.10 | EXT-6 ML benchmark |
| HotLINK GitHub | 🔄 F1.14 exploración | EXT-6 técnicas comparativas |
| TIRVolcH Aveni 2024 | ✅ Ya teníamos (`1-s2.0-S0034425724004140-main.pdf`) | EXT-12 sub-MW low-T |
| Pallister 2013 Chaitén | 🔄 F1.12 descarga | EXT-9 validation field-based |
| Valade 2019 MOUNTS | ✅ Descargado F1.10 | EXT-3 ML cloud + EXT-4 multi-sensor |

### Prioridad orden post-clon-literal

1. **EXT-8 AVTOD** (cross-validation ground truth) — más crítico para paper publication.
2. **EXT-1 Zhu 2023 BTD cirrus** — fix D9 "beyond MIROVA" con base bibliográfica directa.
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

## 10. Aplicación futura

Cuando termine el clon literal (post adopción F2.1 unsuitable filters + Tupungatito mirova_center):

1. **Paper open source VRP Chile**: describir clon MIROVA + listar extensions documentadas en este doc como "future work".
2. **Iteración EXT-1 Zhu 2023**: implementar BTD cirrus filter como primera extension experimental.
3. **EXT-8 AVTOD cross-validation**: integrar al workflow validation antes de publication.

Cuando Nicolás decida priorizar alguna extension específica → mover de "backlog" a "in_progress" + abrir tarea + iniciar implementación.
