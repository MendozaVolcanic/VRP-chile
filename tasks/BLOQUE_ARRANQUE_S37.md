# Bloque de arranque S37 (2026-05-11+)

## Lee primero (10 min, OBLIGATORIO antes de cualquier acción)

1. `CLAUDE.md` — especialmente sección "Documentación bibliográfica" (nueva S36)
2. `~memory/project_s35_s36_close.md` — resumen ejecutivo S35+S36 (20 PRs)
3. `~memory/reference_bibliography_synthesis.md` — apunte al source-of-truth bibliográfico
4. `tasks/handoff_s35_2026_05_10.md` — handoff S35 (background H7/H8)
5. `docs/superpowers/specs/2026-05-11-plan-integrado-s36.md` — plan integrado 4 bloques A/B/C/D
6. `docs/superpowers/specs/2026-05-10-d8-cluster-selection.md` — D8 design completo

## Estado al cierre S36 (2026-05-11 11:30 GMT)

### Sistemas operacionales (no requieren atención)
- VRP-chile NRT funcionando con fix H7 (IPv4 + retry extendido)
- mirova-tif-archive scraper cron 5min, 591 filas / 285MB
- Suite tests 231/0/16 verde

### Bugs activos en operacional (decisiones conscientes)
- **H8** sigue activo (13.7% records descartados injustamente). Fix existe
  como flag opt-in pero NO adoptado porque sin D8 amplifica overdetection
- **D8** investigado completo, H_D8_5 fix listo en design doc pero NO implementado

### Data ground truth nueva (S36 logro)
- **OSF v2.5**: 48,360 refs Tier A en `data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv`
- Filtrado: `reports/osf_v25_tier_a.csv` (8 MB, regenerable con `experiments/82_osf_v25_audit.py`)
- Cobertura: 2000-2025. Para 2026+ usar OCR consolidado Mirova-v1.

## Plan S37 — 4 caminos posibles (decisión Nicolás)

### Camino 1: Implementar H_D8_5 (operacional, 3-5 días)

ETI cuadrático + second-pass adyacente + sum(vrp) reporting.

Pasos:
1. Crear perfil `_h_d8_5_full.yaml` en `pipeline/profiles/`
2. Implementar `compute_eti_scene_quadratic()` en `pipeline/detection_context.py`
3. Implementar `second_pass_adjacent()` en `pipeline/process_*.py`
4. Cambiar reporting en `store.py` a `sum(anomaly_pixels.vrp_mw)`
5. Tests sintéticos (R1+R7)
6. A/B reproceso 30 días Tier A con perfil nuevo
7. Validación R2 pixel-level vs mirova-tif-archive
8. R3 audit independent
9. Si valida: adopción operacional (cambiar mirova_equivalent.yaml)

Comando arranque: invocar `superpowers-brainstorming` + leer design doc D8.

### Camino 2: HotLINK benchmark R3 (independiente, 1 día)

USGS AVO CNN +22% vs MIROVA. Código público.

Pasos:
1. `git clone https://github.com/csaundersshultz/HotLINK`
2. `pip install -e .` + dependencias (tensorflow 2.15, satpy, earthaccess)
3. Correr HotLINK sobre Lascar/Puyehue período 2026-05 (granules ya disponibles)
4. Tri-way comparison: VRP-chile vs MIROVA OCR vs HotLINK
5. Si HotLINK detecta lo que VRP-chile pierde → evidencia D8 adicional
6. Si HotLINK detecta lo que MIROVA no → futuro: agregar como path

### Camino 3: Quick wins (~1h cada uno)

E. **Actualizar `experiments/80_h8_apples_to_apples.py`** para soportar OSF v2.5
   como ground truth alternativa (flag CLI `--source osf|ocr`)

F. **Investigar Llaima 411 FPs curados OSF**:
   - Filter OSF v2.5 Tier A → Llaima class=0
   - ¿Son geográficos (Conguillío lake ~9km NE) o temporales (estación cálida)?
   - Si geográficos → revalida nuestros exclude_zones removidos S27

G. **Sintetizar 1-2 PDFs prioridad ALTA** del backlog (`VOLCANOMS`, `V-STAR`,
   etc.) y agregar a `BIBLIOGRAPHY_SYNTHESIS.md`. 26 PDFs pendientes.

### Camino 4: Revisar Tupungatito caso especial

Tupungatito 0 refs en OSF v2.5 pero ALERTAs en 2026 (post-cierre OSF).
Documentar como caso operacional especial: NRT only, sin paridad histórica.
Update `~memory/project_tiering_osf_v2_5.md`.

## Recomendación de orden

**Mi sugerencia strict para S37**:
1. **E (15min)** primero — desbloquea audits futuros con OSF
2. **F (30min)** después — info crítica para decisión sobre exclude_zones
3. **C2 H8 fix opt-in en perfil experimental con OSF baseline** (combinación):
   correr A/B H8 con OSF v2.5 como ground truth. Tarda 1-2h pero da
   métricas más confiables que el A/B previo
4. Solo entonces: **B (H_D8_5 implementación)** o **D (HotLINK)**

## NO HACER

- **NO modificar `mirova_equivalent.yaml`** sin A/B + R2 + R3 (regla R5/R6 CLAUDE.md)
- **NO revertir fix S33 `mirovaEqVrp`** hasta D8 resuelto (frontend mostraría confuso)
- **NO buscar papers online sin antes** verificar `documentacion/` + `BIBLIOGRAPHY_SYNTHESIS.md`

## Si Nicolás dice "qué hacemos?"

Responder con esta lista de caminos. Si dice "el que más impacto" → Camino 1 (H_D8_5).
Si dice "lo más rápido" → Camino 3.E + 3.F.
Si dice "validación externa" → Camino 2 (HotLINK).
