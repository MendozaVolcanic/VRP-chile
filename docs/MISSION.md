# Misión VRP Chile — Clon literal MIROVA

> **Documento vinculante.** Leer al inicio de cada sesión. Aplica las 3
> preguntas antes de proponer o implementar cualquier cosa.

## Misión

Reproducir lo más fielmente posible el comportamiento de **MIROVA NRT** sobre
volcanes chilenos, usando **únicamente** la metodología documentada en los
papers core MIROVA. El objetivo no es "mejor que MIROVA" — es "igual que
MIROVA, en infraestructura propia para SERNAGEOMIN, con dashboard limpio".

Si encontramos que MIROVA tiene un comportamiento que no queremos (FPs en
lagos, sub-detección sub-pixel, etc.), eso queda como hallazgo documentado
pero **NO** es licencia para divergir metodológicamente. Si MIROVA falla en
algo, nosotros también fallamos en lo mismo. Esa es la definición de "clon".

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

2. **Si NO está en papers**, ¿cierra una divergencia ya documentada en
   `docs/MIROVA_DIVERGENCES.md`?**
   - D1: granularidad (1 punto/pasada).
   - D2: cobertura CSV ground truth.
   - D3: FP explícito MIROVA.
   - D4: recall sub-pixel summit.
   - D5: magnitud (resuelto).

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

**El patrón común**: cada parche resolvía el síntoma de un drift previo, no la
causa raíz. Cuando se acumulaban, anulaban la diferenciación summit/scene de
MIROVA. Volver a literal puro es la forma de detener el ciclo.

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
