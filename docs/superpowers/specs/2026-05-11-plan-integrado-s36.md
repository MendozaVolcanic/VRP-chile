# Plan Integrado S36 — todo el contexto en una vista

**Fecha**: 2026-05-11
**Driver**: Nicolás reportó pérdida de memoria sobre paper Coppola 2016a (SP426.5)
que estaba en `documentacion/`. Auditoría reveló múltiples documentos críticos
fuera del scope de CLAUDE.md / memoria persistente.

---

## Fallo metodológico raíz (R6 obligatorio analizar)

### Qué pasó

1. `~memory/reference_papers_mirova.md` apunta a Vault notes (`coppola2016enhanced.md`)
   que son **resúmenes parciales** del paper.
2. CLAUDE.md NO menciona la carpeta `VRP Chile/documentacion/` que contiene
   **60 PDFs + 9 archivos sintetizados** incluyendo el paper completo.
3. Cuando "investigué Coppola 2016a" en sesión previa, leí solo el Vault note,
   no busqué PDFs en disco.
4. **El BIBLIOGRAPHY_SYNTHESIS.md** (429 líneas, S13 hace 23 días) tiene el
   algoritmo completo escrito + tabla de umbrales + sistemas competidores
   listados. Nunca lo encontré porque tampoco está apuntado por memoria.

### Acciones correctivas (este plan + más)

1. **Agregar a CLAUDE.md** sección "Documentación bibliográfica" con apunte
   explícito a `documentacion/BIBLIOGRAPHY_SYNTHESIS.md` como **source of truth**.
2. **Agregar a ~memory/** entrada `reference_bibliography_synthesis.md` con
   resumen ejecutivo de lo que hay en synthesis.
3. **Workflow obligatorio**: ANTES de investigar papers, hacer `find documentacion/`
   y verificar synthesis primero. Solo si no está sintetizado, investigar.

---

## Lo que sabemos integrado (cross-validated 4 fuentes)

### Algoritmo MIROVA completo (Coppola 2016a SP426.5 leído verbatim S36)

7 pasos:
1. NTI espectral + NTI_app (Planck synthetic)
2. **ETI cuadrático**: `NTI_bk = a·NTI²_app + b·NTI_app + c` regresión per scene
3. **dNTI / dETI**: pixel - mean(8 vecinos)
4. **Test 1**: NTI_pix > K1 (K1=-0.8 noche, -0.6 día)
5. **Tests 2 + 3** (AMBOS): dNTI > C1 OR dNTI > μ + C2·σ; idem dETI
   - ROI1 summit (5x5km): C1=0.003, C2=5 noche
   - ROI2 scene (50x50km): C1=0.01, C2=10 noche
6. **Second-pass adyacente**: re-correr Step 2 excluyendo active pixels
7. **VRP = Σ RP_pix** sobre TODOS los active. **NO cluster selection**.
8. **Distance reportada** = vent → pixel active más lejano.

### Diferencia arquitectural VRP-chile vs MIROVA

| Aspecto | VRP-chile | MIROVA |
|---|---|---|
| Background | local annulus (5-25km) | regresión cuadrática scene-wide |
| Cluster | `cluster_hotspots` 8-conn post-detección | **NO clustering**, suma global |
| Reporting | `primary_cluster.vrp_mw` (max VRP cluster) | Σ RP_pix de TODO active |
| Second-pass | NO | SÍ |
| Distance reported | `final_hotspot_dist_km` (cluster centroid) | pixel active más lejano |

### Por qué MIROVA reporta el lacolito y no el cluster cráter

**Hipótesis confirmada**: ETI cuadrático scene-wide ajusta `NTI_bk` alto en
zona warm-BG (cráter Puyehue), → ETI ≈ 0 → no pasa Tests 2/3 → cluster
cráter NO se flagea. Solo el lacolito (BG bajo en zona lava field) pasa.
Sum reporting da entonces solo VRP del lacolito.

VRP-chile NO tiene ETI cuadrático → todos los warm pixels pasan → cluster
cráter compite con lacolito → `primary_cluster` selection elige el grande.

---

## Lo que tenemos a nivel data (cross-validated, integrar)

### mirova-tif-archive (scraper propio, ground truth pixel-level)
- 591 filas / 343 deterministic / 285 MB
- 14 ALERTAs MIROVA capturadas en 10-11 may con TIF disponible
- Scraper saludable cron 5 min sin fallar 24h
- Casos R2-grade: Lascar MODIS 01:25, Puyehue lacolito 04:36, Lastarria 06:12

### MIROVA OSF v2.5 (descargada 2026-04-18 en data/mirova_reference/)
- **615,470 filas globales** (3 órdenes de magnitud más que CSV OCR consolidado)
- Por sensor:
  - MODIS 1km: 262,455
  - VIIRS 375m: **252,374** (confirma MIROVA SÍ publica I-bands)
  - VIIRS 750m: 100,641
- Cobertura Chile (vs nuestros refs OCR S12):
  - Chaitén: 5,809 vs 15 (×387)
  - PCC: 5,488 vs 84 (×65)
  - Lastarria: 5,368 vs 59 (×91)
  - Villarrica: **5,211 vs 6 (×868)** ← Villarrica recall 0% era con 6 refs
- **No usado en audits actuales**. Implementar uso es siguiente prioridad audit.

### HotLINK CNN (USGS AVO, código público)
- U-Net 64x64 inputs MIR+TIR normalized
- +22% recall vs MIROVA, -12% FPs (sobre Alaska)
- Inference ~12ms/imagen (NRT viable)
- Entrenado Alaska, transfer Andes incierto → fine-tuning con 200 imágenes Villarrica/Lascar
- **Útil como R3 audit benchmark INDEPENDIENTE** (no requiere replicar MIROVA)

---

## Roadmap S36+ priorizado

### Bloque A — Corregir fallo metodológico (~30 min, debe hacerse YA)

A1. **Actualizar CLAUDE.md** con sección "Documentación bibliográfica":
   - Apunte a `documentacion/BIBLIOGRAPHY_SYNTHESIS.md`
   - Regla: "Antes de investigar papers, leer synthesis primero"
A2. **Actualizar ~memory/** con `reference_bibliography_synthesis.md`:
   - Resumen de qué contiene synthesis
   - Status cobertura (30/60 sintetizados)
A3. **Auditar BIBLIOGRAPHY_SYNTHESIS.md** y completar 26 PDFs faltantes
    en próximas sesiones (V-STAR, VOLCANOMS, FY-3D, etc.)

### Bloque B — Implementar H_D8_5 (ETI + second-pass + sum reporting)

Es el fix correcto y completo basado en algoritmo verbatim Coppola 2016a.

B1. **Implementar ETI cuadrático** en perfil experimental:
   - Nueva función `compute_eti_scene_quadratic(nti_grid, t_tir_grid)`
   - Regresión per escena
   - Reemplaza/aumenta nuestro background local annulus
   - Costo: 1-2 días dev + tests sintéticos

B2. **Implementar second-pass adyacente**:
   - Re-correr detection step 2 (dNTI/dETI) excluyendo active pixels
   - Re-aplicar Tests 2/3 al new dNTI/dETI
   - Cluster crece orgánicamente
   - Costo: 1 día dev + tests

B3. **Cambiar reporting a sum(vrp_mw)**:
   - `vrp_mw_total` = sum sobre TODOS los pixels active in-radius
   - `hotspot_dist_km` = max(pixel.dist_km)
   - `primary_cluster` DEPRECATE (no MIROVA concept)
   - Costo: 0.5 día (cambio en store.py + frontend)

B4. **A/B reproceso 30 días** Tier A con perfil `_h_d8_5_full.yaml`:
   - Comparar vs `mirova_equivalent` baseline
   - Métricas: recall, ratio, FP rate
   - R2 pixel-level con mirova-tif-archive
   - Costo: 1 día (trigger + análisis)

### Bloque C — Integrar MIROVA OSF v2.5 como ground truth principal

C1. **Reemplazar OCR consolidado** por OSF v2.5 en audits:
   - Update `experiments/80_h8_apples_to_apples.py`
   - Update `experiments/77_r2_h8_pixel_audit.py`
   - 5,211 Villarrica refs vs 6 = recall reportada cambia drasticamente

C2. **Re-correr audit completo** con nueva ground truth.
   - Predicción: Villarrica recall ya no es 0% (era data stale, no bug)

### Bloque D — HotLINK como R3 audit benchmark

D1. **Clonar HotLINK** repo, instalar (Python 3.11 + tensorflow 2.15)
D2. **Correr HotLINK sobre granules Lascar/Puyehue mismo período** que VRP-chile
D3. **Tri-way comparison**: VRP-chile vs MIROVA vs HotLINK
D4. Si HotLINK detecta lo que VRP-chile pierde, evidencia adicional D8 bug
D5. Si HotLINK detecta cosas que MIROVA no, evidencia de gap MIROVA (futuro: integrar)

### Bloque E — Continuar acumulación + monitoreo

E1. mirova-tif-archive sigue corriendo (no requiere acción)
E2. NRT VRP-chile sigue (no requiere acción)
E3. Cada semana: audit alertas nuevas + cross-ref con mirova-tif-archive

---

## Decisión inmediata para Nicolás

**Recomendación**: ejecutar Bloque A primero (fallo metodológico, 30 min,
prevent re-pérdida) y luego decidir B vs C vs D según prioridad operacional.

- **Si prioridad = operacional para SERNAGEOMIN**: B (D8 fix combinado)
- **Si prioridad = data audit profundo**: C (OSF v2.5)
- **Si prioridad = benchmark independiente**: D (HotLINK)
- **Si prioridad = mantener context**: A (corregir fallo metodológico)

Mi recomendación strict: A → C → B → D. C antes que B porque cambia
nuestro baseline de medida, y todo lo que midamos cambia con eso. Mejor
empezar con la ground truth correcta antes de tocar el pipeline.
