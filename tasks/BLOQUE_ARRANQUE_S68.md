# BLOQUE DE ARRANQUE S68 — VRP Chile

> Cierre S67: audit completo dashboard reveló 51% MODIS over-detection +
> 11 inconsistencias frontend. Fixes planificados pero diferidos S68.

---

## 1. Lectura obligatoria

1. **Este doc** — 5 min
2. **`docs/HYPOTHESIS_LOG.md`** entry H_S67_DASHBOARD_AUDIT_FINDINGS
3. **`tasks/BLOQUE_ARRANQUE_S66.md`** — contexto S65 → S66 → S67
4. **Dashboard live**: https://mendozavolcanic.github.io/VRP-chile/

---

## 2. Estado S67 al cierre

### Pipeline operacional (sin cambios desde S66)
- 5 vols con `local_kernel_bg: true` (Villarrica, PP, Lastarria, Chaiten, PCC)
- 2 vols calibrados natural (Lascar, Isluga)
- Tupungatito: fix mirova_center funciona para 56% de records (S66)
- 3 vols con poca data (Llaima, Copahue, NdC)
- Tests: 335 passed / 16 skipped

### Hallazgos S67 documentados

**Problema 1**: MODIS over-detection sistémica
- 51% MODIS records últimos 10d >5 MW (22/43) sin match MIROVA
- Mecanismo: 1km resolución + ring background extremo frío (glaciar) + Test 1 integrated-ROI
- Outlier: Tupungatito 82.52 MW MODIS_TERRA

**Problema 2**: 11 inconsistencias frontend
- VRE chart diverge de stat box VRE
- MIROVA Comparison chart sin validar pc.centroid_dist
- Toggle far parcial (no propagado a todos los widgets)
- About modal desactualizado
- Sin label visual kernel-bg adoptado

---

## 3. Pendientes S68 priorizados

### Prioridad CRÍTICA — fixes core dashboard

**A. Unificar source-of-truth VRP frontend** (highest impact)

Problema: 4+ fallback chains diferentes en frontend para el mismo VRP:
- `mirovaEqVrp(r, innerKm, includeFar)` — la "correcta" (alert bar, cards, stats)
- `r.vrp_mw ?? r.vrp_mir_mw` — `buildVREData`, `buildDistanceData`
- `pc.vrp_mw ?? vrp_mw` (sin distance check) — `buildComparisonData`
- `getDisplayVrp` — table events (con/sin pc)

Fix: crear UNA función `getReportableVrp(r, innerKm, includeFar)` que replique exactamente `mirovaEqVrp`. Reemplazar TODOS los call-sites. Tests sintéticos para cada widget.

Files:
- Modify: `frontend/index.html` (líneas 1438-1476 charts secundarios)
- Create: tests JS opcionales

Costo: ~2h + verificación visual dashboard

**B. Filtrar/etiquetar MODIS over-detection** (alto impacto usuario)

Opciones (decidir en S68):
- B1. **Backend filter**: agregar `bt_min_anomaly_k` per-vol para MODIS, default 270K. Excluye pixels glaciar puros. Requiere reproc.
- B2. **Frontend filter**: si MIROVA NO publica MODIS para vol X (verificable CSV), no mostrar records MODIS en dashboard para ese vol.
- B3. **Label visual**: mantener records pero marcar "MODIS over-detection sub-MIROVA" en tabla/tooltip.

Recomendación: empezar con B3 (low risk) + considerar B1 si validate empíricamente.

Costo: B3 ~1h, B1 ~3h + reproc Tier A 6-12h GH Actions

### Prioridad IMPORTANTE

**C. Actualizar About modal**

Modal cita S48 F1 98.3% pero estamos en S67. Actualizar con:
- Adopciones kernel-bg S61-S65 (Villarrica/PP/Lastarria/Chaiten/PCC)
- 7-8/9 vols Tier A en clon literal MIROVA NRT
- Cobertura 78-89% logrado

Costo: ~30 min

**D. Label visual kernel-bg adoptado**

En cards o detail panel mostrar pill "kernel-bg ✓" para vols adoptados. Usuario distingue cuáles están "curados".

Costo: ~1h

### Prioridad BAJA — bugs menores

E-K (de audit S67):
- Distance scatter no respeta toggle far
- Cards distance counts fijos 7d
- Overview marker size lineal (cambiar a log)
- Hotspot layer auto-refresh 5min stale
- Sensor legend toggle parcial
- Toggles no persisten sessionStorage
- `mirovaEqVrp` fallback legacy sin distance check
- Stat "Detecciones" vs tabla events divergen

---

## 4. Errores S67 a NO repetir S68

1. **NO modificar source-of-truth VRP sin actualizar TODOS los callsites** (sino se crean inconsistencias entre widgets)
2. **NO filtrar MODIS sin validar con MIROVA NRT por vol** (algunos vols sí publica MODIS — Lascar, Tupungatito a veces)
3. **NO actualizar About modal con métricas desactualizadas** — mantener referencias S65-S66 con datos reales

---

## 5. Estado git S67

- HYPOTHESIS_LOG entry H_S67 persistida
- Total PRs S62-S67 mergeados: 18+ (sin cambios pipeline S67, solo doc)
- Workflows operacionales sin cambios
- Dashboard live serving correct data (con bugs visuales conocidos)

---

## 6. Resumen objetivo clon literal MIROVA

### Logrado S60-S67
- **89% Tier A clon literal MIROVA NRT** (7-8/9 vols ≤3×)
- Pipeline operacional curado para Muy Bajo regime
- Dashboard live actualizado automáticamente
- Documentación completa (13 hipótesis, 10 learnings, 5 bloques arranque)

### Pendientes S68+
1. Fixes dashboard frontend (S68)
2. MODIS over-detection (S68 backend o S69 frontend)
3. Tupungatito cluster selection residual (43% records aún 1-3km del cráter) — S69+
4. Llaima/Copahue esperar más data

---

## 7. Persistencia in-vivo

Cuando S68 implemente fixes: documentar antes/después en HYPOTHESIS_LOG. Test sintético para `getReportableVrp` antes de reemplazar callsites.
