# PAPER VRP CHILE — DRAFT ESQUEMÁTICO (S72, actualizado S120)

> **Estado S120 (2026-07-01)**: skeleton actualizado con los números de la auditoría
> integral S119 (`docs/AUDIT_S119.md`) y las DECISIONES DE NICOLÁS ya tomadas (§0).
> Los números viejos S72 (7/9, ratios S61-S63) quedaron obsoletos — la fuente de
> verdad de validación es AUDIT_S119 + `experiments/_s119_audit/*.json` (regla S91:
> ningún número transcrito a mano; regenerar tablas desde los scripts).
>
> **Hallazgo motivador (F1.9 + F1.11 Perplexity Deep Research, 2026-05-21)**:
> no existe a la fecha ninguna implementación open source publicada del algoritmo MIROVA.
> VRP Chile sería la primera. Esto justifica per se la publicación, independiente de
> resultados operacionales chilenos.

---

## 0. Decisiones — TOMADAS (Nicolás, S120, 2026-07-01)

1. **Venue: DECIDIDO — sin presupuesto para APC.** Restricción vinculante: no hay
   dinero para publicar. Recomendación primaria: **Volcanica** (volcanica.org,
   diamond OA — sin costo para autores ni lectores, revista de la comunidad
   volcanológica, publica methods/software). Journal of Applied Volcanology
   (sugerencia inicial de Nicolás) queda descartado por APC £1,390/US$1,990
   (SpringerOpen, sin waiver para Chile). Ver §A actualizado.
2. **Authorship: contactar a Coppola DESPUÉS** — "cuando tengamos más seguridad y
   más pulido el trabajo" (Nicolás S120). Por ahora: Mendoza lead + co-autores
   SERNAGEOMIN/OVDAS por confirmar. Claude en Acknowledgments con disclosure (no
   co-author, policy journals 2026).
3. **Scope: DECIDIDO — clon + beyond MIROVA.** El paper cubre (a) la validación del
   clon literal (core) y (b) las extensiones beyond-MIROVA como sección propia
   (§7bis): lo que el algoritmo de Coppola captura y MIROVA NRT no publica
   (extensión cat-b clasificada geológicamente, Eq.16 lava lake, vista experimental).

---

## 1. Title (tentativo + alternativas)

**Tentativo primary**:
"VRP Chile: An open source implementation of the MIROVA near-real-time volcanic thermal monitoring algorithm, validated for Chilean volcanoes"

**Alternativas**:
- "Open source replication of the MIROVA algorithm for near-real-time thermal monitoring of Chilean volcanoes"
- "Reproducible NRT volcanic thermal anomaly detection: an open source MIROVA-equivalent pipeline applied to the Southern Andes"
- "Democratizing volcanic thermal monitoring: an open source MIROVA clone validated against OSF v2.5 for 11 Chilean volcanoes"

---

## 2. Abstract (target ~250 words)

Skeleton:

> Volcanic thermal monitoring from MODIS and VIIRS sensors enables early detection of
> effusive activity, lava lake variations, and persistent degassing fields. The MIROVA
> system (Coppola et al., 2016, 2019, 2023) has become the de facto reference for NRT
> volcanic thermal monitoring, but no open source implementation of its algorithm has
> been published, limiting reproducibility, regional adaptation, and operational
> integration by national monitoring agencies.
>
> We present **VRP Chile**, the first published open source implementation of the
> MIROVA NRT algorithm, applied to 45 Chilean volcanoes (11 Tier A actively monitored)
> by the Chilean Geological Survey (SERNAGEOMIN). The pipeline implements the NTI/dNTI/ETI
> tests of Coppola (2016, SP 426.5), the dual-ROI thresholds of Coppola (2016, Table 2),
> the contextual 8-neighbor dNTI kernel (Campus 2024), and per-sensor Wooster MIR
> coefficients empirically calibrated against the MIROVA OSF v2.5 database (median
> error ≤0.17% across 48,360 records).
>
> Validation against MIROVA NRT (consolidated CSV, 25,210 rows + 737 OCR-extracted
> per-volcano records from mirovaweb.it) shows [UPDATE S119, regenerar de
> experiments/_s119_audit/]: nightly detection recall of 98.4% (VIIRS 375 m), 84.5%
> (VIIRS 750 m) and 100% at-crater (MODIS); median per-volcano VRP ratios within
> [0.5–2.0]× for 9/11 Tier A volcanoes, with no volcano over-estimating — the two
> below-band cases are physically attributable (Lastarria: MIROVA integrates the
> extended Lazufre fumarole field while our primary cluster anchors the crater).
> A directional-median spatial audit (per volcano, per sensor) shows no systematic
> bias beyond the documented ~1 km northward residual on snow-covered edifices,
> which we show to be physically irreducible at 375 m–1 km pixel scale.
>
> The pipeline runs on GitHub Actions free tier (cron 2h, public repo) and is published
> under MIT license at github.com/MendozaVolcanic/VRP-chile. It provides a replicable
> framework for other volcanic regions and bridges the gap between published MIROVA
> methodology and operational regional monitoring.

**Figura de abstract**: composite mostrando (a) algoritmo MIROVA esquema, (b) mapa Chile
con 11 Tier A, (c) timeseries ejemplo Villarrica/Lascar comparado con MIROVA web.

---

## 3. Introduction

Skeleton ~3 párrafos:

> ¶1 — Volcanic thermal anomalies as primary indicator: lava lakes, effusive eruptions,
> persistent fumarolic fields. MODIS Terra/Aqua (2000+) y VIIRS Suomi-NPP/NOAA-20/-21
> (2012+) como sensores espaciales de baja revisita y cobertura global. Cita: Wright et
> al. 2002 MODVOLC; Coppola 2016; Massimetti 2020 (HOTSAT); Marchese 2019 (NHI); Del
> Negro Catania (RSDF / HOTSPOT V-STAR).
>
> ¶2 — MIROVA como referencia operacional: arquitectura algorítmica (NTI/dNTI/ETI),
> validación contra observaciones ground-truth (Coppola 2016 Stromboli, 2019 Mt Etna,
> 2024 chapter Springer), integración con observatorios (INGV-Catania, INGV-Pisa, vía
> mirovaweb.it). Limitación: no hay implementación open source publicada (verified
> 2026-05 via systematic literature review, Perplexity Deep Research F1.11). El código
> MIROVA Torino+Firenze es cerrado.
>
> ¶3 — Gap y contribución: regionalización requiere reproducir + adaptar. Chile tiene
> 90+ volcanes activos, SERNAGEOMIN OVDAS monitorea 45 con instrumentación in-situ
> heterogénea. Need: NRT thermal layer open source, validado contra MIROVA pero
> ejecutable autónomamente. Este paper presenta VRP Chile como esa implementación.

**Figuras propuestas**:
- Fig 1: cobertura MODIS+VIIRS sobre Chile (revisita media diaria).
- Fig 2: 45 volcanes configurados + 11 Tier A overlay sobre mapa.

**Citas obligatorias** (DOIs conocidos):
- Coppola 2016 SP 426.5: 10.1144/SP426.5
- Coppola 2019 (Stromboli SSR/JVGR review): por confirmar
- Coppola 2023 OSF v2.5: 10.17605/OSF.IO/... (verificar)
- Coppola 2024 Springer chapter: por confirmar DOI
- Campus 2022 (HOTSAT contextual dNTI): por confirmar
- Campus 2024 (review thermal anomaly detection): por confirmar
- Massimetti 2020 (HOTSAT): por confirmar
- Massimetti 2024: por confirmar
- Aveni 2024 RSE (TIRVolcH): por confirmar
- Aveni 2025 GRL (Eq.9 k_TIR): por confirmar
- Wooster 2003 MIR radiance: por confirmar
- Wright 2002 MODVOLC: por confirmar
- Saunders-Shultz 2024 HotLINK: por confirmar
- Zhu 2023 cirrus BTD MODIS: por confirmar

---

## 4. Background — MIROVA algorithm

Skeleton:

> ¶1 — Sensor radiances: MIR (3.74–4.05 μm) sensitivity to hot subpixel sources via
> Planck function exponential dependence. TIR (10–12 μm) background reference.
>
> ¶2 — NTI = (BT_MIR − BT_TIR) / (BT_MIR + BT_TIR). Diagnostic ratio robust to surface
> emissivity. dNTI = NTI − NTI_background. ETI: extended TIR test for high-T regimes
> where MIR saturates.
>
> ¶3 — Three-test logic (Coppola 2016 §3.x): Test 1 absolute NTI threshold, Test 2 dNTI
> contextual 8-neighbor (Campus 2022/2024), Test 3 ETI. "Second pass" relaxes thresholds
> around already-detected pixels (region growing). ROI dual: summit (inner radius
> per-vol from KMZ) vs scene (outer radius 25 km / 51×51 km UTM grid). Thresholds
> Tabla 2 (c1=0.003 summit, 0.010 scene).
>
> ¶4 — Wooster MIR radiance → VRP MW conversion: VRP = k × ΣL_MIR_anomaly. k empirical
> per-sensor. VRP TIR Stefan-Boltzmann puro (Coppola 2024 + Aveni 2024 RSE).
>
> ¶5 — Explicit limitations declared by Coppola 2016 §247-249: clouds "not taken into
> account" (no cloud mask). False positives "typically <5 MW" (§687). These two
> declarations anchor several adoption decisions in VRP Chile.

**Figura 3**: diagrama de bloques algorítmico MIROVA (Test 1/2/3 + second pass + ROI dual + VRP).
**Tabla 1**: thresholds Coppola 2016 Table 1 + Table 2 (NTI/dNTI per sensor + summit/scene).

---

## 5. Methods — VRP Chile implementation

Skeleton:

> ¶1 — Arquitectura: GitHub Actions cron 2h, repo público (minutos ilimitados), matrix
> per-volcano (max-parallel=8). Cada job: fetch L1B (NASA Earthdata via earthaccess) →
> process_modis/process_viirs/process_viirs_mod → store JSON → commit. Frontend
> Chart.js + Leaflet (GitHub Pages). Profile-based: `mirova_equivalent` (literal clone)
> vs `experimental` (extensiones).
>
> ¶2 — Sensores: MODIS bands 21/22 (3.929/3.959 μm) + 31 (11 μm TIR); VIIRS I04
> (3.74 μm) / I05 (11.45 μm) at 375 m; VIIRS M13 (4.05 μm) / M15 (10.76 μm) at 750 m.
> NOAA-21 added S18 (VJ202IMG/VJ202MOD) — explicit gap fix vs initial implementation.
> NRT vs Standard L1B: fallback NRT (_NRT) si Standard no disponible (<3h latency).
>
> ¶3 — Calibración Wooster: per-sensor k validated against OSF v2.5 (48,360 records):
> - MODIS 1 km: k = 18.9 × A_pix(1e6) = 18,900,000 (Wooster 18.9)
> - VIIRS M-band 750 m: k = 1.97×10⁷ × A_pix(km²) = 11,081,250 (Wooster 19.7)
> - VIIRS I-band 375 m: k = 18.0 × A_pix(140,625) = 2,531,250 (Wooster 18.0)
> MIROVA uses A_pix nadir-fijo (no zenith correction) for all three. Error mediano
> ≤0.17% sobre 48,360 records. Di Bella 2024 k=2.48×10⁷ for VIIRS 375m fails OSF
> reproducibility — discarded.
>
> ¶4 — Geometría: radius_km=25 km uniforme (MIROVA grid UTM 51×51 km, inscribed 25.5 km).
> inner_radius_km per-volcán from KMZ oficiales (3-20 km). Esquema dual "detect wide +
> classify visual": detections inside inner→`summit`, outside→`far` (not filtered).
>
> ¶5 — TIR VRP: Stefan-Boltzmann puro σ=5.67×10⁻⁸ (Coppola 2024 chapter Eq.16, Aveni
> 2024 RSE Eq.5). Aveni 2025 GRL Eq.9 con k_TIR=60.17 explorado pero no adoptado
> operacionalmente.
>
> ¶6 — Reproducibility: profiles YAML (`pipeline/profiles/mirova_equivalent.yaml`),
> tests 796 passed (S119), golden files versionados (`tests/golden/`), constants and feature
> flags documented (`docs/MISSION.md` con regla "3 preguntas" antes de cualquier cambio
> metodológico).

**Tabla 2**: 11 Tier A volcanoes con coords (vent + mirova_center), inner_radius_km, n records.
**Tabla 3**: per-sensor Wooster coefficients + OSF v2.5 validation error.
**Figura 4**: arquitectura pipeline (fetch → process → store → frontend).
**Figura 5**: ROI dual + dual-ROI thresholds esquema visual (un volcán ejemplo).

---

## 6. Validation

Skeleton:

> ¶1 — Ground truth: OSF v2.5 algorítmico (Coppola 2023, 615k records globales, 48k
> chilenos 2000-2025) + MIROVA NRT operacional (CSV consolidado scraped + OCR via
> Mirova-v1 sub-repo, ~13.7k filas, 3.5 meses).
>
> ¶2 — Métricas per-vol: VRP ratio (mediana ours/MIROVA), recall (TP/TP+FN), precision
> (TP/TP+FP), F1. Tolerancia operacional: ratio individual 0.5-2.0, mediano 0.7-1.4
> (MIROVA declara ±30% en publicación), recall ≥0.60, precision ≥0.50.
>
> ¶3 — Resultados Tier A [ACTUALIZADO S119 — fuente: docs/AUDIT_S119.md §2 +
> experiments/_s119_audit/eje2_recall_magnitud.json; regenerar tabla del script]:
> recall de noches ALERTA por sensor: VIIRS375 98.4% / VIIRS750 84.5% / MODIS-cráter
> 100%. Magnitud (mediana pc.vrp/MIROVA, noches comunes 2026): **9/11 en banda
> [0.5–2.0]×, ninguno sobre-estima**. Fuera de banda solo por abajo: Lastarria 0.466×
> (cat-b Lazufre: MIROVA integra el campo, nuestro cluster ancla el cráter) y Llaima
> 0.357× (n=2, sin significancia). Los ratios per-vol S61-S63 del skeleton original
> quedaron obsoletos tras nadir-fijo (S102-S103) + magnitud focal (S109-S112) +
> gates OFF (S118).

**Tabla 4**: per-vol validation metrics (ratio mediano, recall, precision, n, sensor coverage).
**Figura 6**: scatter ours vs MIROVA VRP per-vol (4 ejemplos Lascar/Villarrica/Lastarria/PP).
**Figura 7**: timeseries comparativa 6 meses, un volcán Tier A activo (Villarrica o Lascar).
**Figura 8**: histograma ratios per-record (mostrar distribución vs ±30% banda).

---

## 7. Case studies

### 7.1 Tupungatito — mirova_center anchor mistake (S64-S65)

> KMZ MIROVA tiene bbox center que NO coincide con vent activo (offset ~5 km).
> Pipeline ancla cluster selection en mirova_center y elige FPs flanco SE. Fix S65:
> quitar mirova_center, anclar en vent oficial (Smithsonian GVP). Resultado: 56% records
> con cluster correcto. Cluster selection residual S70+ (pendiente).

**Figura 9**: mapa Tupungatito con mirova_center vs vent + cluster pre/post-fix.

### 7.2 D9 — Path D contextual cirrus FPs (S70-2)

> Atacama winter conditions: cirrus alto t_bg <260 K. Path D dNTI contextual computes
> dNTI = NTI_pixel − mean(NTI_8neighbors). Cirrus cools background uniformly, inflando
> dNTI artificialmente. FPs sistémicos vrp_mw 20-150× MIROVA.
>
> Solución adoptada: cap a 5 MW siguiendo Coppola 2016 §687 ("FPs typically <5 MW").
> Validado bajo regla S33 (R1 tests sintéticos + R2 pixel-level vs MIROVA web + R3 audit
> independiente). 100% bug elimination, recall preservado en 2/2 vols Tier A afectados.

**Figura 10**: ejemplo FP cirrus Lastarria winter 2025 — antes/después cap.
**Figura 11**: distribución vrp_mw FPs pre-cap vs post-cap.

### 7.3 Lastarria — R2 retroactivo pixel-level (S69)

> Primer caso S62-S65 con R2 pixel-level retroactivo (ratio 1.05×, drift centroide TIF
> 0.752 km). Demuestra reproducibilidad <1 km y <10% VRP error en escena bien
> caracterizada.

**Figura 12**: TIF MIROVA vs VRP Chile mapa pixel-level Lastarria.

---

## 7bis. Beyond MIROVA — extensiones (scope confirmado S120)

Sección nueva del scope decidido (clon + beyond). Skeleton:

> ¶1 — Motivación: la auditoría integral mostró que ~95% de las detecciones nuestras
> "extra" sobre MIROVA son **anomalías térmicas físicamente reales que MIROVA captura
> pero no publica** (AUDIT_S86/S119): campo fumarólico Lazufre (Lastarria), lacolito
> Cordón Caulle en enfriamiento (PCC), lava lake sub-umbral (Villarrica), Cerro Blanco
> (NdC). El clon literal las hereda; el valor agregado es CLASIFICARLAS, no filtrarlas.
>
> ¶2 — Extensión cat-b clasificada geológicamente: zonas por volcán (proximal /
> extensión / dispersión) ancladas en literatura de deformación y datos de campo —
> ej. lacolito PCC: ~0.8 km³, uplift ~2 km², 20-200 m de profundidad (Castro et al.
> 2016, Nat. Comms. 10.1038/ncomms13585) → radio de extensión ~2 km del vent 2011.
> Separación display-only: la detección (clon) no se toca (regla MISSION).
>
> ¶3 — Magnitud recuperada de lava lake (Coppola 2024 Eq.16): implementada flag-OFF,
> validación dirigida sobre Villarrica (lago reactivado jun-2026, confirmado por
> MIROVA-OCR 0.28-0.54 MW al cráter) — perfil experimental aislado `_s99_test1_eq16`.
> [Pendiente reproc — Panel 2b]
>
> ¶4 — Vigilancia continua de paridad: auto-audit semanal (recall/magnitud/espacial
> vs MIROVA como job cron) — convierte la validación de episódica en monitoreo.
> [Si está implementado al momento de redactar, citarlo como feature]

**Figura 13**: Panel 2a beyond-mirova (zonas geológicas PCC/Lastarria con detecciones).
**Figura 14**: serie Villarrica cruda vs Eq.16 (cuando exista el reproc).

---

## 8. Discussion

Skeleton:

> ¶1 — Logros: primera implementación OSS de MIROVA validada. Reproducibilidad
> garantizada (profiles + tests + goldens). Framework adaptable a otras regiones
> (cambiar volcanoes.yaml + KMZ + vent coords).
>
> ¶2 — Limitaciones técnicas:
> - pyhdf roto en Windows → MODIS solo Linux (GitHub Actions).
> - NASA LANCE NRT ~3h latencia inevitable.
> - NRT throttling Earthdata desde Azure IPs (GH Actions runners) — issue NRT cron
>   intermittente diagnosticado S70-0.
>
> ¶3 — Divergencias identificadas vs MIROVA literal (catálogo
> MIROVA_DIVERGENCES_CATALOG_S71): drifts D1-D9 documentados. D3 (TIR k_TIR) resuelto
> S17. D9 (cirrus FPs) resuelto S70-2 con cap 5 MW. Resto en backlog.
>
> ¶4 — Extensiones más allá de literal (no operacional, investigación):
> - Zhu 2023 cirrus BTD MODIS como gate adicional pre-Path-D (alternativa al cap).
> - HotLINK CNN (Saunders-Shultz 2024) como benchmark ML para FP reduction.
> - AVTOD ASTER (Reath et al.) como ground truth independiente cross-validation
>   (pendiente).
>
> ¶5 — Comparación con otros sistemas: HOTSAT (INGV-Pisa), NHI (CNR-IMAA Potenza),
> RSDF/V-STAR (INGV-Catania), FIRMS (NASA), MODVOLC (Hawaii). VRP Chile es replicación
> MIROVA específicamente — no compite, complementa.
>
> ¶6 — Caso Tupungatito: ejemplo de cómo dependencia rígida de metadatos KMZ MIROVA
> oficiales puede arrastrar errores. Validación visual + vent Smithsonian GVP como
> ground truth fue necesaria.

---

## 9. Conclusions

> - Primer clon open source publicado del algoritmo MIROVA NRT.
> - Recall de noches ALERTA 98.4% (VIIRS375) / 84.5% (VIIRS750) / 100% MODIS-cráter;
>   magnitud 9/11 Tier A en banda [0.5–2.0]× sin sobre-estimación (audit S119).
> - Caracterización del límite físico de resolución: el foco sub-píxel débil y el
>   gradiente topográfico nevado son indistinguibles a 375 m–1 km (A82/A83) — el eje
>   espacial es el único discriminante.
> - Beyond MIROVA: clasificación geológica de la señal real que MIROVA no publica
>   (Lazufre, lacolito PCC, lava lake) sin tocar la detección.
> - Framework replicable: GitHub Actions free tier + Earthdata + KMZ oficiales.
> - Integración operacional SERNAGEOMIN OVDAS en curso.
> - Código MIT en github.com/MendozaVolcanic/VRP-chile.

---

## 10. Code and data availability

- **Code**: github.com/MendozaVolcanic/VRP-chile (MIT license recomendado — confirmar con SERNAGEOMIN).
- **Data**: per-vol JSON committed bajo `data/mirova_equivalent/`. Raw L1B HDF NO committed (NASA Earthdata reproducible via fetch.py).
- **Reproducibility**: profiles YAML + workflows + tests (796 passed S119) + goldens versionados.
- **Reference data**: OSF v2.5 (Coppola 2023, DOI por confirmar) + MIROVA NRT scraper en github.com/MendozaVolcanic/Mirova-v1.

---

## 11. Acknowledgments

Skeleton:

> The authors thank the MIROVA team (Coppola, Laiolo, Massimetti, Campus, Aveni,
> Cigolini, Università di Torino / Firenze / Sapienza Roma) for the foundational
> methodology and the open-access OSF v2.5 database that made empirical calibration
> possible. We thank SERNAGEOMIN OVDAS for institutional support and operational
> requirements feedback. Development of the pipeline was substantially assisted by
> Claude (Anthropic), an AI coding assistant, in code authoring, methodology review,
> systematic debugging, and documentation; per current journal AI authorship policies,
> AI assistants are not co-authors but their substantive contribution is hereby
> disclosed. NASA LANCE/Earthdata provided MODIS and VIIRS L1B data.

---

## 12. References

A completar con DOIs. Lista mínima inicial (~30-40 refs):

1. Coppola et al. 2016 SP 426.5 — MIROVA core methodology
2. Coppola et al. 2019 — MIROVA review/extension
3. Coppola et al. 2023 — OSF v2.5 database
4. Coppola et al. 2024 — Springer chapter
5. Campus et al. 2022 — HOTSAT contextual
6. Campus et al. 2024 — review
7. Massimetti et al. 2020 — HOTSAT
8. Massimetti et al. 2024 — by confirm
9. Aveni et al. 2024 RSE — TIRVolcH
10. Aveni et al. 2025 GRL — k_TIR Eq.9
11. Wooster et al. 2003 — MIR radiance
12. Wright et al. 2002 — MODVOLC
13. Marchese et al. 2019 — NHI
14. Saunders-Shultz et al. 2024 — HotLINK CNN
15. Zhu et al. 2023 — cirrus BTD
16. Del Negro et al. — RSDF/V-STAR INGV-Catania
17. Reath et al. — AVTOD ASTER
18. Smithsonian GVP — vent coords reference
19. NASA LANCE Earthdata — data source documentation
20. SERNAGEOMIN — OVDAS institutional reference

---

## A. Venue analysis

| Venue | Pros | Cons | Recomendación |
|---|---|---|---|
| **JVGR** (Elsevier) | Audiencia volcanología núcleo; Coppola y MIROVA team publican aquí | Paywall (€2,500+ APC OA opcional); revisión lenta (6-12m); orientado más a casos volcanológicos que a methods/software | Solo si paywall aceptable |
| **Frontiers in Earth Science — Volcanology** | OA nativa; ~$2,950 APC; revisión rápida (~3m); MIROVA-friendly (Coppola publica); audience matches | APC alto si SERNAGEOMIN no cubre; perfil "methods + validation" cabe perfectamente | **Recomendado primario** |
| **Remote Sensing (MDPI)** | OA $2,700; revisión muy rápida (1-2m); audience técnica sensores | Reputación variable; menos exposición a comunidad volcanológica directa | **Recomendado alternativo** si timeline crítico |
| **Geoscientific Model Development (Copernicus)** | OA gratis muchos casos; estándar reproducibilidad software altísimo (perfect fit pipeline OSS) | Audiencia más modelado que volcanología; revisión exigente con código | Considerar si scope se inclina más a "software paper" que "case study" |
| **Bulletin of Volcanology** | Prestigio comunidad | Paywall; revisión lenta; menos methods-friendly | Descartar |
| **JGR Solid Earth / Geophys. Res. Lett.** | Alto impact factor | Scope amplio earth sciences, methods OSS poco frecuente | Descartar salvo case study fuerte |

**Recomendación final — ACTUALIZADA S120 (restricción: sin presupuesto APC)**:

| Venue | APC | Veredicto |
|---|---|---|
| **Volcanica** (volcanica.org) | **US$ 0** (diamond OA, comunidad volcanológica) | **ELEGIDA** — sin costo, peer review serio, publica methods/software/monitoring, indexada (Scopus). Audiencia exacta |
| Journal of Applied Volcanology (SpringerOpen) | £1,390 / US$1,990 | Descartada por costo (sugerencia inicial; sin waiver para Chile) |
| Frontiers Earth Sci — Volcanology | ~US$2,950 | Descartada por costo |
| Remote Sensing (MDPI) | ~US$2,700 | Descartada por costo |
| JVGR / Bull Volc (suscripción, OA opcional) | 0 si se publica cerrado | Plan B solo si se acepta paywall (contra el espíritu open del proyecto) |

Decisión S120 (delegada por Nicolás): **Volcanica**. Encaja además con la identidad
del proyecto: revista open de la comunidad para un pipeline open de una agencia pública.

---

## B. Authorship

Propuesta tentativa (Nicolás confirma):

1. **Mendoza, N.** (SERNAGEOMIN, lead) — concepción, implementación, validación, redacción.
2. **[SERNAGEOMIN supervisor/colaborador]** — supervisión institucional, validación operacional, requisitos OVDAS. (¿Quién?)
3. **[opcional MIROVA team co-author]** — si se invita a Coppola u otro miembro para validación/colaboración formal. Beneficio: legitimación + revisión más rápida. Riesgo: tiempo coordinación.
4. **[opcional cobertura técnica adicional]** — si hay co-autor académico para análisis estadístico de validación.

**Claude/Anthropic**: NO co-author (policy mayoritaria journals 2026, incluyendo Elsevier, Frontiers, MDPI, Copernicus). Mencionar substancialmente en Acknowledgments + Code availability con disclosure explícito.

---

## C. Roadmap tiempos (realista)

Estimación a draft completo enviable, contando ~6-10h/semana de Nicolás:

| Hito | Tiempo |
|---|---|
| Skeleton (esto) → Sections 1-4 redactadas | 2-3 semanas |
| Sections 5-6 (Methods + Validation con tablas finales) | 3-4 semanas |
| Sections 7-8 (Case studies + Discussion) | 2-3 semanas |
| Figuras finales (12+) | 2-3 semanas (paralelo) |
| Referencias completas + formato venue | 1 semana |
| Revisión interna + iteración Nicolás | 2-3 semanas |
| Co-author review (si aplica) | 2-4 semanas |
| **Total draft completo enviable** | **~4-6 meses** |
| Submission → first decision (Frontiers) | +2-3 meses |
| Revisión + resubmission | +1-2 meses |
| Publicación | **~8-12 meses desde hoy** |

Aceleradores: dedicar dispatching-parallel-agents a borradores de secciones específicas; usar
notas existentes (`MIROVA_DIVERGENCES_CATALOG_S71`, `DRIFTS_S17.md`, `HYPOTHESIS_LOG`,
`PAPERS_AUDIT.md`) como base directa de secciones 4, 7, 8.

Desaceleradores potenciales: validación AVTOD ASTER si se incluye en scope; co-author MIROVA
team coordinación; SERNAGEOMIN approval institucional.

---

## D. Pendientes inmediatos para Nicolás antes de redactar

1. Confirmar venue (§A).
2. Confirmar authorship + invitar co-autores (§B).
3. Decidir scope: literal-clone validation only vs incluir extensiones D9 + cirrus BTD + AVTOD (§7-8).
4. Confirmar licencia código (MIT vs Apache 2.0 vs GPL — recomendado MIT por compatibilidad académica).
5. Resolver DOIs pendientes (todas las refs marcadas "por confirmar").
6. Validar disclosure AI assistant con SERNAGEOMIN y journal target policy.

---

*Documento creado S72 (2026-05-21). Próxima iteración: tras decisiones §D.*
