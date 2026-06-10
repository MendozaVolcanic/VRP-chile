# Misión VRP Chile — Clon literal MIROVA + extensión volcánica documentada

> **Documento vinculante.** Leer al inicio de cada sesión. Aplica las 3
> preguntas antes de proponer o implementar cualquier cosa que toque el
> pipeline algorítmico.

## Misión (objetivos simultáneos, post-S86)

VRP Chile cumple dos objetivos que comparten la misma infraestructura de
detección pero se reportan distinto:

**Objetivo (1) — Clon literal MIROVA NRT** (PRIMARIO algorítmico).
Reproducir lo más fielmente posible el comportamiento de MIROVA NRT sobre
volcanes chilenos, usando **únicamente** la metodología documentada en
papers core MIROVA. El objetivo no es "mejor que MIROVA" — es "igual que
MIROVA, en infraestructura propia para SERNAGEOMIN, con dashboard limpio".
Si encontramos que MIROVA tiene un comportamiento que no queremos (FPs en
lagos, sub-detección sub-pixel, etc.), eso queda como hallazgo documentado
pero **NO** es licencia para divergir metodológicamente.

**Objetivo (2) — Extensión volcánica documentada** (SECUNDARIO reporte).
Reportar las detecciones que el algoritmo Coppola 2016a captura pero que
MIROVA NRT no publica por scope operacional (sub-complejos volcánicos,
cráteres secundarios, lava lakes sub-pixel, lacolitos difusos, fumarolas
crónicas catalogadas Smithsonian GVP). El hallazgo S86 (auditoría
profunda) mostró empíricamente que **95.4% de las "FPs" del cruce estricto
contra MIROVA son anomalías térmicas físicamente reales** — 49.1%
publicaciones MIROVA que el cruce nuestro perdió por bugs del loader local
+ 46.3% features volcánicas reales no publicadas por MIROVA. Solo 4.6%
son artefactos espurios. Reportar (2) honestamente como valor agregado
SERNAGEOMIN — no eliminarlo.

**Importante**: el algoritmo de detección es ÚNICO (el de papers MIROVA
core). La distinción (1) vs (2) vive en el campo derivado `pc.classification`
(diseño S87 Bloque 3) + en el frontend que separa visualmente las
categorías. No se introducen gates adicionales para "limpiar" (2).

## Las 3 preguntas vinculantes

**Antes de implementar cualquier feature, fix, threshold, exclusion, path,
filtro, agregación o transformación en el pipeline, responder en orden**:

1. **¿Está documentado en papers MIROVA core?** Lista oficial:
   - Coppola 2015 (Test 1, NTI).
   - Coppola 2016a SP 426.5 (Tabla 1 N·σ summit/scene, dual-ROI, dNTI 8-vec).
   - Coppola 2020 Frontiers (review sistema MIROVA).
   - Coppola 2024 cap Springer (review pedagógico).
   - Coppola 2025 Fernandina (NRT moderno).
   - Coppola 2022 Sabancaya (k VIIRS I4).
   - Campus 2022 / Campus 2024 Vulcano (k VIIRS).
   - Aveni 2024 RSE TIRVolcH (Stefan-Boltzmann TIR).
   - Laiolo 2026 Stromboli (sin cloud filter automático).
   - Massimetti 2024 Stromboli + 2020 Sentinel-2.

   Lista de papers **NO MIROVA** (no usar como autoridad): Di Bella 2024,
   Torrisi 2022/2025, Cariello, Corradino, Amato, Marchese, Pergola,
   Genzano, Filizzola, Falconieri. Ver `~memory/reference_papers_mirova_canonical.md`.

   **Si SÍ está en papers core → puede implementarse.**

   **⚠️ Regla de verificación verbatim (S99, raíz de la confusión Eq.16):**
   responder "SÍ está en papers" exige una **cita verbatim del paper** (archivo +
   línea) que muestre que el **sistema MIROVA NRT automático APLICA** ese mecanismo —
   NO basta que el paper lo *mencione* o lo *discuta*. Distinguir SIEMPRE:
   - *"el sistema MIROVA computes/applies automatically X"* (verbo activo, sistema) →
     SÍ, parte del clon.
   - *"X can be estimated / was applied to volcano Y / requires calibration"* (voz
     pasiva, sección "Applications", caso de estudio manual) → NO es el pipeline NRT;
     va a `BEYOND_MIROVA_EXTENSIONS.md`, no a `pipeline/`.
   - Las afirmaciones de **design docs internos sobre "qué hace MIROVA" NO son
     autoritativas** hasta cotejarse contra la fuente primaria verbatim. La confusión
     Eq.16 (S53→S99) nació de tomar la interpretación de un design doc como hecho.

   **Hecho canónico (verificado S99):** MIROVA NRT = **UN algoritmo por SENSOR**
   (MODIS / VIIRS750 / VIIRS375), **uniforme entre volcanes**. La única variación
   por-objetivo es (a) geometría ROI/summit (centro GVP) y (b) sensor (bandas + α +
   umbrales). **NO conmuta de método por volcán ni por régimen térmico.** Cualquier fix
   de magnitud fiel debe ser uniforme por sensor (Coppola 2016a §98-119, §431-441,
   §689-695; Coppola 2024 §1148-1155).

2. **Si NO está en papers**, ¿cierra una divergencia ya documentada en
   `docs/MIROVA_DIVERGENCES.md`?**
   **El catálogo VIVO es el doc — esta lista es resumen (actualizada S105, AUDIT_S105):**
   - Resueltas (no justifican features nuevas): D1 granularidad, D4 recall sub-pixel
     (S27), D5 magnitud (nadir S102/103 + ctxpeak D10 S100), D8/D8' cluster selection
     (S38/S62), sec³ off-nadir (S102/103), fix del ancla de detección (S98).
   - **Abiertas**: D2 cobertura CSV ground truth · D3 FP explícito MIROVA ·
     **D9 path D cirrus/escena tibia** (cap 5MW = mitigación, causa raíz abierta;
     residuo MODIS ~131 records pc.vrp>5, 0% confirmados MIROVA — AUDIT S105) ·
     **D11 sesgo topográfico de paths MIR-absolutos (A69, S104)** — el Test1 integrado
     MIR/NTI-anillo se sesga ~1 km al valle tibio en nevados; MIROVA inmune (NTI +
     fondo local). Fix candidato fondo-local-NTI en A/B S105 (V1 y V2 refutados) ·
     VIIRS750 disperso glaciar (Tupun/PP, pendiente portar ctxpeak S102§2) ·
     NEW-8 gaps 2-4 (pool estadístico m,σ).
   - **Pendiente de decisión** (S105, Nicolás): gates intra-radio S84/S85 (veredicto
     anti-patrón A55 en AUDIT_S86 §C6; siguen ON; decidir con más datos al cerrar el
     frente Test1/fondo-local).

   Cerrar divergencia = alinear comportamiento con MIROVA, no agregar
   funcionalidad nueva. **Si SÍ cierra divergencia → puede implementarse.**

3. **Si NO está en papers y NO cierra divergencia documentada**, ¿es
   alineación interna no-metodológica?**
   Ejemplos válidos: render del frontend, infra A/B, tests, scripts de
   evaluación, documentación, persistencia de memoria.

   **Si SÍ es alineación interna → puede implementarse.**

**Si las 3 son NO → NO IMPLEMENTAR.** Anotar en `tasks/backlog_*.md` con la
razón "no cumple regla MIROVA literal" y seguir.

## Anti-patrones a evitar (lecciones acumuladas)

Estas fueron las desviaciones históricas. Nunca repetir.

| Parche histórico | Razón rechazo | Estado |
|---|---|---|
| `MAX_SIGMA_COMPONENT_K=7K` cap eruption | No en papers; anula 5σ/10σ MIROVA | Removido S27 |
| Vent-path entero | No en papers; sub-pixel debe ir por Test 1 (Coppola 2015) | Removido S27 |
| `exclude_zones` (Salar, lagos) | No en papers; MIROVA no usa máscaras geográficas | Removido S27 |
| Regla D vent-priority | Parche de clasificación visual, no en papers | Removido S27 |
| Regla D Test 1-priority | Parche de composición de paths, no en papers | Removido S27 |
| Cloud mask BT<260K | Laiolo 2026 textual: "no atmospheric correction or cloud-contamination automatic filtering" | Removido S27 |
| Pisos VRP por sensor | Coppola 2023 dice "floor ~1 MW" genérico, no por sensor | Removido S27 |
| Path C NTI relativo (default ON) | No en papers | Default OFF mantenido |
| Subir `inner_radius_km` ad-hoc | Parche para recuperar recall; no es metodológico MIROVA | Rechazado S27 |
| N·σ Di Bella 2024 (12σ noche VIIRS) | Di Bella es INGV Catania, NO MIROVA | Identificado S26 |
| **Gate intra-radio por path** (S83-S85 PRs #224, #229) | No en papers; el frontend `mirovaEqVrp` ya hacía exactamente eso desde S33 → adopciones redundantes | Identificado S86 |
| **Eq.16 lava lake / Eq.25 crater lake POR-VOLCÁN** (design S53, casi adoptado S99) | El capítulo Coppola 2024 las presenta en sección "Applications" como productos de 2º nivel MANUALES y calibrados caso por caso ("requires specific calibrations", "valid only within the limits of the assumptions") — **NO el pipeline NRT automático**. MIROVA NRT es UN algoritmo por SENSOR uniforme (Coppola 2016a: "completely autonomous", "self-adapting thresholds independent of local conditions"). Conmutar de método por volcán es un drift. | Identificado S99 — movido a beyond-MIROVA (`docs/BEYOND_MIROVA_EXTENSIONS.md` EXT-11). Citas verbatim: `experiments/_s99_audit/dormant/papers_per_sensor.md` |

**El patrón común**: cada parche resolvía el síntoma de un drift previo, no la
causa raíz. Cuando se acumulaban, anulaban la diferenciación summit/scene de
MIROVA. Volver a literal puro es la forma de detener el ciclo.

**Familia "gate intra-radio" (S86)**: las adopciones S83-S85 (path D
restringido a intra-radio + second pass restringido a intra-radio)
pasaron las 3 preguntas solo por puerta 3 GRIS "alineación infraestructural",
pero la auditoría S86 reveló que el gate intra-radio ya existía en el
frontend desde S33 — eran adopciones redundantes que además, si se
hubieran combinado con G1 (`sensor != VIIRS_M_750`) propuesto S86,
habrían suprimido categoría (b) "features volcánicas reales no publicadas
por MIROVA". **Cualquier PR futuro que proponga otro gate "intra-radio por
path" requiere primero**: (a) verificar que el frontend no hace ya esa
supresión, (b) clasificar la categoría físicamente (E S86) de los
records que el gate filtraría, (c) confirmar que ninguno pertenece a (b).

## Cuándo SÍ se puede divergir

**Solo en estos casos** documentados explícitamente:
- **Datos / infraestructura**: NOAA-21 integration, A_pix nadir + scan-angle,
  cap top-100 anomaly_pixels (anti-bloat), gitignore de snapshots locales.
- **Render frontend**: visualización 1 marker/record alineado con MIROVA NRT
  (S27).
- **Cluster aggregation** (S27): alineación con `n_hotspots` MIROVA via
  `scipy.ndimage.label` 8-conn — explícitamente Coppola 2016a "neighbor
  pixels" connectivity.
- **Tests** que validan comportamiento contra papers.
- **Scripts evaluación / forense** que comparan vs CSV consolidado MIROVA NRT.

Cualquier otra divergencia requiere actualizar este documento primero,
justificando contra papers MIROVA core.

## Si encontrás que el literal puro pierde recall

Esa es señal de que MIROVA usa un mecanismo que no replicamos todavía. La
respuesta correcta NO es agregar parche — es **investigar qué mecanismo
documentado en papers MIROVA core estamos pasando por alto**.

Hipótesis abiertas (S28+, ver `~memory/project_s27_mirova_literal_negativo.md`):
- H_S27_1: Test 1 summit-only más agresivo (Coppola 2015 §2.2 Eq.1).
- H_S27_2: dNTI con C1 negativo (cooling) además de positivo.
- H_S27_3: path TIR-only Aveni 2024 RSE TIRVolcH.
- H_S27_4: composición paths cascada vs OR (cómo MIROVA combina internamente).
- H_S27_5: subir `inner_radius_km` — **RECHAZADA** como parche.

## Auditoría obligatoria al cierre de cada sesión

Antes de marcar una sesión como completa, responder explícitamente:
1. ¿Qué cambios hice en `pipeline/` esta sesión?
2. Por cada uno: ¿pasa las 3 preguntas?
3. Si alguno NO pasa: revertirlo o documentar excepción explícita en este
   archivo.

## Referencias

- Divergencias actuales: `docs/MIROVA_DIVERGENCES.md`
- Papers MIROVA canonical: `~memory/reference_papers_mirova_canonical.md`
- Parches no-MIROVA inventario: `~memory/project_s26_parches_no_mirova.md`
- A/B literal puro NO APROBADO: `~memory/project_s27_mirova_literal_negativo.md`

---

## R2 retroactivo — referencia operacional

Para aplicar el método R2 retroactivo a un vol nuevo (validación de adopción metodológica
post-S70), seguir el patrón documentado en `docs/R2_GATES_BY_REGIME.md`. Las bandas
gates son **régimen-dependientes** (Tier A Alto, Tier A Muy Bajo simple, Tier A Muy
Bajo complejo, No focal). Aplicar gates Lastarria-style a cualquier vol sin clasificar
régimen primero introduce FAIL marginales sistemáticos que ocultan que la adopción de
hecho funciona en agregado.
