# BLOQUE ARRANQUE S113

**Sesión S112 (2026-06-17)** entregó 3 adopciones en producción + auditoría integral. PRs #437-442.
Registro completo: `project_s112_estado` (memoria) + `docs/AUDIT_S112_DASHBOARD_MIROVA.md`.

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat docs/AUDIT_S112_DASHBOARD_MIROVA.md     # auditoría + lista priorizada de frentes
```
Leer en memoria: `project_s112_estado` (ESTADO FINAL + A77-A80).

## ✅ Cerrado en S112 (LIVE en producción)
1. **VIIRS375 "Muy Bajo" NdC** (#439/#440): anillo intermedio [1.5,3] recupera la magnitud de la
   reactivación (06-16 0.068 vs MIROVA 0.06). Tag pre-s112-intermediate-bg-adoption.
2. **Focal VIIRS750** (#442): cura artefacto topográfico A69 (V750 8-20× → ~1×). A/B 24/24, Lascar
   canario preservado, MODIS/VIIRS375 byte-idént. Tag pre-s112-focal-v750.
3. **Auditoría integral** (`docs/AUDIT_S112_DASHBOARD_MIROVA.md`): paridad SANA; caso PCC resuelto
   (artefacto cirrus path-D, no lacolito).

## §1 — PRIORIDAD S113 (orden aprobado Nicolás): #3 → #2
**#3 — coherencia A46 (CONTENIDO, empezar por acá):** ~6 records Villarrica con cluster lejano
marcado "summit". Flagship: **Villarrica 06-15 75.6 MW @ cluster 28km marcado "summit"** (sensor
VIIRS375, src=vent → final_dist≈0 → summit, pero el pc.vrp viene del cluster a 28km). Fix:
`distance_class` debe seguir `primary_cluster.centroid_dist_km` (la fuente de pc.vrp), no el ancla.
Investigar dónde se setea distance_class (process_*.py) + cómo el frontend lo usa (audit: index.html
isSummitDetection:1355, popup:2609 usan distance_class crudo). Clasificación, posiblemente sin reproc
(relabel post-hoc) pero verificar A18 (no afecta cluster selection). A45 + TDD + verificar 3 vistas.

**#2 — cirrus D9/A23 (MAYOR IMPACTO, más delicado):** la raíz de las 56 detecciones lejanas de PCC
(86% path-D ctx_cluster, 77% t_bg<270K) + ~210 cirrus en los 11 + residual Isluga del focal V750.
Divergencia D9 abierta. Fix candidato: co-validación obligatoria path-D con BT/NTI absoluto, O gate
atmosférico (rechazar path-D-only cuando t_bg<270K), O cap magnitud path-D frío. **Papers-first
(Coppola 2016a §SP426.5, Campus 2024) + MISSION + A/B 3 brazos + A45.** Toca detección → cuidado con
refutados (V1 NTI per-píxel S104 apagó el Test1).

## §2 — Frentes menores (backlog)
- #4 MODIS difuso A69 (sobre-detección RUTINA 91-98%; frente abierto, focal MODIS + co-val).
- #5 inner_radius PCC 20→10km (display/clasificación; conserva lacolito real ≤8.5km). Validar A18.
- #6 20 records MODIS PCC clavados en pc.vrp=5.0 (¿cap?); diario:432 datetime sin Z (S89, parseUtcMs).
- Backfill histórico completo VIIRS375+V750 (NRT llena forward; reproc mayo-junio para series completas).
- Parte C Test1-lowmag (NdC 22-mar 0.49 FN detección — probablemente sub-píxel, verificar OLI/MSI).
- FICHA SDA update (cambios metodológicos S112).

## 🔑 revise-claude-md S113: formalizar A77-A80 (en project_s112_estado, mover a CLAUDE.md proyecto)
- **A77**: ante "erupciona pero VRP no lo ve" → revisar MIROVA OLI/MSI (alta-res SWIR); foco sub-píxel
  → canal Landsat/Sentinel-2 (NHI), no VIIRS/MODIS. El experto insistió 5×, tenía razón (A62).
- **A78**: erupción explosiva/freática ≠ efusiva en firma MIR; escanear nti_max multi-sensor.
- **A79**: al adoptar un parámetro, verificar el EVENTO ESPECÍFICO objetivo, no solo la métrica agregada
  ([2,4] tenía buen med_err pero perdía el trigger 06-16).
- **A80**: detecciones V750/MODIS con nti_max plano = artefacto topográfico A69 amplificado por área.

## Estado operacional (sano)
NRT cada 2h. 3 adopciones S112 live (NRT las aplica forward). Suite 769. 6 PRs (#437-442).
Las series históricas se completan forward; los backfills cubrieron ventanas clave (no full-history).
