# BLOQUE DE ARRANQUE S70 — VRP Chile

> Cierre S69 (2026-05-20): 89% Tier A clon literal MIROVA NRT logrado.
> 5 vols con kernel-bg adoptado + 2 calibrados natural + Tupungatito fix parcial.
> Audit metodológico integral validado. Bug S33 regression FIXED.

---

## 1. Lectura obligatoria al inicio S70

1. **Este doc** — 5 min
2. **`docs/HYPOTHESIS_LOG.md`** entries S68-S69 (top 6 nuevas)
3. **`tasks/BLOQUE_ARRANQUE_S68.md`** + **`BLOQUE_ARRANQUE_S65.md`** — contexto continuo
4. **`docs/MISSION.md`** + 3 preguntas vinculantes
5. **`CLAUDE.md`** sección "Reglas operacionales S60-S62 (aprendizajes A10-A19)"
6. **Dashboard live**: https://mendozavolcanic.github.io/VRP-chile/ (About modal con métricas S68)

---

## 2. Estado FINAL al cierre S69

### Cobertura Tier A — 89% clon literal logrado

| Vol | Status | Ratio mediano | Adopción | R2 validado |
|---|---|---:|---|---|
| **Lascar** | calibrado natural | 1.37× | — | sí (S46) |
| **Isluga** | calibrado natural | 1.33× | — | sí (S46) |
| **Lastarria** | kernel-bg | **1.07×** | S62 | ✅ **S69 R2 retroactivo: drift 0.75 km, ratio 1.05×** |
| **Chaiten** | kernel-bg | 2.23× | S63 | pendiente R2 |
| **Villarrica** | kernel-bg | 2.17× | S61 | sí (S46) |
| **PCC** | kernel-bg | 0.29× | S63 | pendiente R2 |
| **PlanchonPeteroa** | kernel-bg | 2.84× | S61 | pendiente R2 |
| **Tupungatito** | fix mirova_center | parcial 56% records ✓ | S65 | bloqueado (TIF MIROVA ≠ actividad) |
| Llaima / Copahue / NdC | n bajo | esperar | — | — |

### Adopciones operacionales acumuladas

- `enable_local_kernel_bg: true` en `mirova_equivalent.yaml`
- Per-vol flag `local_kernel_bg: true`: Villarrica, PlanchonPeteroa, Lastarria, Chaiten, PCC
- Tupungatito: `mirova_center` REMOVIDO S65 (PR #93) → vent_anchored ancla cráter activo
- Otros 4 vols: false (calibrados o n bajo)

### Infraestructura

- **NRT cron** cada 2h, ~93-98% success rate (failures intermitentes NASA en vols no-Tier-A)
- **Pages-deploy fix S62 PR #87**: dashboard live se refresca aunque NRT failure parcial
- **TIF archive scraper** funciona perfecto cada 5min en GH Actions (NO es tarea Nicolás)
- Tests: **334 passed / 16 skipped** (goldens pre-S27, technical debt)

### Documentación acumulada

- **18 hipótesis** en HYPOTHESIS_LOG (S60-S69)
- **10 learnings A10-A19** en CLAUDE.md (memoria operacional)
- **6 bloques arranque** (S60-S70)
- **8 audit scripts** experiments/110-115
- **MIROVA_DIVERGENCES.md** consolidado S60-S62

---

## 3. Pendientes priorizados S70

### Prioridad MEDIA — R2 retroactivos (replicar método Lastarria)

> **Nota S70-0 T3 (2026-05-20)**: el método R2 S69 fue auditado y validado en S70-0 T3. Ver `docs/MIROVA_DIVERGENCES.md` D6 y `docs/HYPOTHESIS_LOG.md` H_S70_TIF_VRP_SUMABILITY. El TIF de `mirova-tif-archive` NO se debe sumar como VRP per-pixel (es campo de radiancia visualizable), pero el método R2 S69 NO suma TIF — usa `pc.vrp_mw` (pipeline) vs MIROVA CSV para magnitud y TIF top10 **<3km del vent** para geometría. Patrón replicable de 5 pasos documentado en `experiments/120_audit_tif_vrp_sumable/README.md` Parte 2.

**1. R2 retroactivo Chaiten/PCC/Villarrica/PP** (cierra deuda audit S67)

Método validado S69 (experiments/115_r2 implícito):
```python
# Descargar TIF via gh API (NO requiere sync local repo mirova-tif-archive)
gh api repos/MendozaVolcanic/mirova-tif-archive/contents/data/tif/<Vol>?ref=main
curl -sL <download_url> -o /tmp/<vol>.tif
# Comparar centroide TIF (top10 pixels <3km vent, ponderado) vs pc.centroid
# Tolerancia: 2km drift, ratio magnitud 0.3-3.0×
```

Casos sugeridos:
- **Chaiten**: 2026-05-12 05:36 ALERTA 0.27 MW VIIRS375 (record nuestro pc.vrp=2.78, ratio 10× pre-fix vs post-fix esperado <3×)
- **PCC**: 2026-05-11 05:54 ALERTA 0.22 MW VIIRS375
- **Villarrica**: 2026-05-11 06:00 ALERTA 0.31 MW VIIRS375 (ya parcialmente validado S35)
- **PlanchonPeteroa**: cualquier ALERTA reciente (no había TIFs antes, ahora hay)

Costo: ~15 min cada uno con método validado.

---

### S70-1 RESUELTO (2026-05-20): R2 retroactivo completado 5/5 Tier A

**Resultados**:
- Lastarria: PASS limpio (focal Tier A Alto)
- Chaiten: PASS revisado (focal + cola térmica)
- Villarrica: PASS revisado (focal + halo lava lake)
- PP: marginal (ratio 2.08× sobre límite 2.0 por 0.08, drift 2.20 km — patrón Tier A Muy Bajo)
- PCC: R2 con drift no aplica (lacolito difuso); magnitud valida adopción S63

**Documentación**:
- H_S70_R2_RETROACTIVO_4VOLS en HYPOTHESIS_LOG (cierre formal)
- D7 en MIROVA_DIVERGENCES.md (bandas gates por régimen)
- Experimentos individuales: `experiments/122-125/`

**Pendientes S70-2+** (no bloqueantes):
- Multi-caso PP (3-5 ALERTAs) para validación robusta del marginal.
- Formalizar bandas gates por régimen en `docs/MISSION.md` o doc dedicado.
- Métrica alternativa para vols no focales (PCC, Tupungatito 43% residual).

### Prioridad MEDIA — limpieza técnica

**2. Regenerar 16 goldens pre-S27**

Tests `test_golden_records.py` líneas 190+200: 16 tests skipped esperando regeneración post-S27/S31+. Cuando se regeneren, suite pasa a 350 passed.

Comando esperado: `pytest tests/test_golden_records.py --update-goldens` o similar. Verificar pytest config primero.

**3. Limpiar ~15 workflows obsoletos** (audit agente A S67):

Workflows candidatos archivar `.github/workflows/_archive/` o eliminar:
- `reproc-villarrica-test1*.yml` (S25-S26 obsoletos)
- `reproc-no-bt-path-15d.yml` (S40 cleanup ya adoptado)
- `reproc-ab-p3-1.yml` (S15-S24)
- `reproc-ab-test1*.yml` (S33 adoptado)
- `reproc-d8-d4-per-vol-15d.yml`, `reproc-ab-d8-*.yml` (S37-S38 adoptado)
- `reproc-ab-h-d8-5.yml`, `reproc-ab-h8.yml` (S35 adoptado)
- `reproc-ndc-retry.yml` (one-shot)
- `reproc-vent-anchored-30d-preview.yml` (S37-S38)
- `reproc-failed-tier-a.yml` (sin uso reciente)

### Prioridad BAJA — refinamientos

**4. Tupungatito cluster selection residual 43%**

H_S66_TUPUNGATITO_FIX_VALIDATED_PARTIAL: 56% records cluster correcto con fix S65, pero 43% siguen con cluster 1-3km (no en cráter exacto). Mecanismo: vent_anchored a veces elige cluster más grande/caliente vs el más cercano al vent. Fix arquitectural: agregar `min_pc_centroid_dist_km` per-vol o preferir cluster MÁS cercano al vent en lugar del más grande.

**5. MODIS final_hotspot fix** (S62 paralelo identificado)

`final_hotspot_lat/lon/dist_km` se asigna al pixel más caliente individual de escena. Para vols con clusters lejanos (lago Villarrica norte, salar PCC), `final_hotspot` cae far aunque cluster summit esté correcto. Fix: asignar `final_hotspot` al pixel más caliente DEL CLUSTER SUMMIT. Requiere TDD + reproc Tier A.

**6. Frontend bugs menores 6-11** (audit S67):

- Stat "Detecciones" vs tabla events count divergen
- Overview marker size lineal (cambiar a log)
- Hotspot layer auto-refresh 5min stale
- Sensor legend toggle parcial
- Toggles no persisten en sessionStorage
- Distance scatter no respeta toggle far
- Cards distance counts fijos 7d

**7. Llaima/Copahue/NdC con `pc.vrp_mw`**

S62 paralelo finding: Llaima n=3 ratio 6-12×, Copahue n=1 ratio 3.18× con pc.vrp_mw. Si llegan más ALERTAS 2026-05/06: considerar A/B kernel-bg. NO accionable sin más data.

---

## 4. Errores S67-S69 a NO repetir S70

0. **NO asumir reportes de agentes sin verificación empírica** — S68 agente reportó "TIF scraper parado" cuando era directorio local desactualizado, y "anti-patrones MISSION.md violados" cuando estaban mitigados operacionalmente.

1. **NO asumir bin top centroides = anomalía real** — puede ser bin FPs sistemáticos (caso Tupungatito S62-S64).

2. **PNGs MIROVA son dashboards de timeline**, NO mapas con coord. Solo PNG Distance es útil.

3. **Usar `pc.vrp_mw` siempre** para comparar con MIROVA (no `record.vrp_mw`).

4. **Preview offline cluster selection es engañoso** (Lección A18). Reproc REAL obligatorio para parámetros cluster.

5. **CSV vol names variantes** (Lección A14): `PlanchonPeteroa` sin guión, `Puyehue-Cordon Caulle` con guión.

6. **TIF archive remoto vs local** — sincronizar local con `git pull` cuando se necesite, o usar `gh api` para TIFs específicos.

---

## 5. Estado git al cierre S69

- Último PR mergeado: #101 (S69 paralelo R2 + MODIS + About modal)
- Total PRs S62-S69 mergeados: **27**
- Workflows operacionales activos:
  - `nrt.yml` cron cada 2h ✓
  - `pages-deploy.yml` (fix S62 #87) ✓
  - 30+ workflows reproc/A/B (varios obsoletos S70 cleanup)
  - `mirova-tif-archive/poll.yml` cada 5min ✓
- Audit scripts: `experiments/110-115_s62-s69_*`
- Tests: 334 passed / 16 skipped

---

## 6. Hipótesis activas pendientes / parcialmente resueltas

- **H_S66_TUPUNGATITO_FIX_VALIDATED_PARTIAL**: 56% records correcto. 43% restante = cluster selection residual S70+
- **H_S67_DASHBOARD_AUDIT_FINDINGS**: 11 inconsistencias frontend. Bug S33 regression FIXED S68. Bugs 6-11 pendientes S70+
- **H_S69_MODIS_OUTLIERS_05_17**: FPs regionales atmosféricos identificados. Frontend filtra far. No acción urgente.

---

## 7. Lecciones meta S60-S69

### Lo que funciona bien

1. **Trabajo paralelo con dispatching-parallel-agents** — múltiples investigaciones independientes en paralelo
2. **`pc.vrp_mw` + universo CONS+OCR** como métrica audit ratio
3. **`gh api` para descargar TIFs sin sync local** — R2 retroactivo Lastarria validado S69
4. **HYPOTHESIS_LOG persistencia in-vivo** — cada finding se documenta inmediatamente
5. **Bloque arranque + cierre formal por sesión** — continuidad clara

### Lo que requirió correcciones

1. **Asumir reportes de agentes sin verificación** (TIF scraper, anti-patrones)
2. **Confundir bin top centroides con anomalía** (Tupungatito S62-S64)
3. **Confiar en preview offline para cluster selection** (PCC inner=7 S62 revertido)
4. **`record.vrp_mw` vs `pc.vrp_mw`** (Lección A10 olvidada hasta S61 auditoría)

---

## 8. Persistencia in-vivo (regla meta-meta)

Cuando S70 descubra hallazgo nuevo: persistir INMEDIATAMENTE en `docs/HYPOTHESIS_LOG.md`. NO esperar al cierre.

Si comienza R2 batch (Chaiten/PCC/Villarrica/PP): documentar cada caso en HYPOTHESIS_LOG con resultados drift centroide + ratio magnitud.

---

## 9. Quick reference comandos S70

```bash
# R2 retroactivo método validado
gh api "repos/MendozaVolcanic/mirova-tif-archive/contents/data/tif/<Vol>?ref=main" --paginate | \
  python -c "import json,sys; [print(f['name']) for f in json.load(sys.stdin) if f['name'].endswith('.tif')]"
curl -sL <download_url> -o "C:/Users/nmend/AppData/Local/Temp/<vol>.tif"
# Audit ratio + centroide drift con rasterio

# Sync mirova-tif-archive local (cuando convenga)
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/mirova-tif-archive"
git pull

# Test suite
python -m pytest tests/ -q  # 334 passed / 16 skipped

# Dashboard live
curl -sL https://mendozavolcanic.github.io/VRP-chile/data/mirova_equivalent/Lastarria.json | head

# PR cierre típico
gh pr create --title "..." --body "..."
gh pr merge <PR#> --squash --delete-branch -R MendozaVolcanic/VRP-chile
```

---

## S70-2 T4-T5 hallazgo crítico (2026-05-20): bug path D dNTI ctx en cirrus

**Severidad**: ALTA — afecta dashboard live (picos 20-30 MW Lastarria visibles en "Solo cráter" mode).

**Confirmado empíricamente** (cross-check 32 records Lastarria vs MIROVA NRT):
- 68.8% FPs nuestros (path D dispara espuriamente en cirrus alto, t_bg<270K)
- 31.2% TPs amplificados 62× sobre MIROVA (path D suma pixels marginales)
- 100% path D solo, BT=0, NTI=0

Detalles: `docs/MIROVA_DIVERGENCES.md` D8 + `docs/HYPOTHESIS_LOG.md` H_S70_PATH_D_CIRRUS_FP.

**Próximo bloque S71** (prioridad ALTA):
1. Brainstorming opción gate atmosférico (3 opciones en D8: gate t_bg, co-validación, cap magnitud).
2. A/B test profile flag aislado (`mirova_equivalent_path_d_atm_gate_v1.yaml`).
3. R2 pixel-level vs MIROVA por régimen.
4. Si fix valida → adoptar en operacional.

**Mientras tanto**: dashboard muestra honestamente los datos del pipeline. Comunicar a usuarios externos (SERNAGEOMIN) que los picos altos en cirrus pueden no ser actividad volcánica real, fix en curso S71.
