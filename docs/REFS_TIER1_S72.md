# Refs Tier 1 — papers/recursos prioritarios identificados S72 (2026-05-21)

> Derivado de Perplexity Pro Deep Research (F1.9) + F1.8 backlog bibliográfico. Refs con alta prioridad para clon MIROVA NRT VRP Chile o "beyond MIROVA" extensions.

## Resumen ejecutivo

| Categoría | Refs | Status descarga |
|---|---|---|
| Fix D9 cirrus filter (beyond MIROVA) | EMSEV 2012 BTD multi-band | 🔄 F1.10 corriendo |
| Benchmark independiente MIROVA | HotLINK CNN Frontiers 2024 | 🔄 F1.10 corriendo |
| Verificar identidad (probable duplicado) | TIRVolcH (Campus 2024 RSE) | 🔄 F1.10 corriendo |
| Validación ML cluster MIROVA | (Perplexity ronda 2 puede identificar más) | 🔄 F1.11 corriendo |

## Detalle por ref

### EMSEV 2012 — BTD multi-band cirrus filter MODIS

**Por qué Tier 1**:
- F1.9 Perplexity citado como *"referencia más concreta para fix D9 path D dNTI ctx S71 T1"*.
- Algoritmo específico: BTD entre bandas MODIS 31-32, 20-31, 31-27, 34-35.
- **MIROVA NO lo usa** (admite cloud handling "ausente en todos los algoritmos" en Coppola 2019 §1449).
- Sería pieza concreta para "beyond MIROVA literal" extension.

**Caveat**: el nombre "EMSEV 2012" es ambiguo. Puede ser:
- "Earthquakes, MagnetoSphere and Electromagnetic Variations" conference proceedings.
- O publicación afiliada.
- O confusión Perplexity con foundational papers MODIS cloud mask (Inoue 1985, Ackerman 1998, Frey 2008).

F1.10 (corriendo) verifica identidad + accesibilidad.

**Aplicación a VRP Chile**:
- Si accesible → implementar BTD cirrus filter como **opción adicional** del pipeline (no clon literal, pero "beyond MIROVA" defendible operacionalmente).
- Si MIROVA NO lo usa pero produces FPs en cirrus → adoptar este filtro nos hace **MEJOR que MIROVA** en operacional, manteniendo paridad en otros aspectos.

### HotLINK CNN — Frontiers Earth Sci 2024

**Por qué Tier 1**:
- Benchmark independiente más fuerte conocido de MIROVA.
- Alaska comparativa: **+22% detecciones, -12% FPs vs MIROVA**.
- ML approach (no clon literal).

**Caveat**: ML, no transferible directamente a clon MIROVA literal. Pero útil como:
- Referencia de **techo de mejora** alcanzable sobre MIROVA con ML.
- Casos de uso donde MIROVA falla (-12% FPs = ¿qué FPs MIROVA tiene en Alaska?).
- Evaluación independiente de la calidad del ground truth MIROVA.

### TIRVolcH — Campus 2024 RSE

**Por qué Tier 1**:
- Single-band TIR VIIRS, ΔT 0.5K, FP 1.8%.
- Autores MIROVA-canónicos (Campus, Massimetti, Coppola, Aveni, Laiolo).
- DOI probable: 10.1016/j.rse.2024.114388 (citado por Perplexity).

**Verificación pendiente F1.10**:
- ¿Es nuestro `documentacion/campus2024_extracted.txt` o paper distinto?
- Si es nuestro → confirmar identidad.
- Si es distinto → descargar.

## Plan de acción post-descarga (S73+)

### Si EMSEV 2012 (o equivalente foundational) accesible:

1. Procesar exhaustivo con extracción de ecuaciones BTD exactas.
2. Diseñar profile aislado `mirova_equivalent_btd_cirrus_v1.yaml` con BTD filter implementado.
3. A/B reproc 11 Tier A vs operacional.
4. Decisión: si reduce FPs **>10% sin tocar recall** en Tier A Muy Bajo → adopción operacional como "beyond MIROVA literal" extension.

### Si HotLINK accesible:

1. Leer abstract + metodología.
2. NO implementar ML (fuera de scope clon MIROVA literal).
3. Documentar benchmark numbers para contexto comparativo.

### Si TIRVolcH = paper distinto:

1. Procesar exhaustivo.
2. Comparar ΔT 0.5K threshold con nuestros records Tier A Muy Bajo.
3. Si aporta sub-MW detection improvement → considerar adopción.

## Otras refs (rondas Perplexity pueden traer)

F1.11 (ronda 2) busca:
- Implementaciones GitHub open source.
- OVDAS SERNAGEOMIN validation methods.
- BTD MODIS bands implementations específicas.
- AVTOD-like datasets.
- Cross-validation MIROVA vs field data.
- Multi-sensor integration architectures.
- NASA Earthdata throttling alternatives.
- MIR sub-pixel deconvolution.
- Cluster connected-component algorithms.
- Papers post-2024 que mencionen MIROVA.

Update cuando F1.11 termine.

## Aprendizaje meta A31

**A31 (S72 2026-05-21)** — **Perplexity Pro Deep Research es complementario a APIs gratis, no sustituto**. Confirma AP20 (S17 Papers/Educación 69% overlap). En esta sesión F1.9 trajo 3 papers Tier 1 que las APIs gratis no priorizaron:
- EMSEV 2012 cirrus filter (cita indirecta, no MIROVA-canónica).
- HotLINK benchmark (Frontiers no aparece sin query muy específica).
- Confirmation de "no clon MIROVA open source" (necesita búsqueda multi-source).

**Costo Perplexity** ~10 min wall-clock. **Valor**: 3 papers nuevos + verdict sobre estado del arte.

**Trigger para usar Perplexity Pro Deep Research**:
- Confirmar gaps bibliográficos post-APIs gratis.
- Identificar comparativas/benchmarks cross-system.
- Validar que no existe X (e.g., clon MIROVA open source).
