# tasks/_archive_s80/

Archivados S80 (auditoría post-pérdida-contexto). 30 archivos `.md` de
sesiones S1–S70 que ya estaban implementados o superados.

## Categoría

**Planes implementados** (features ya en `mirova_equivalent.yaml`):
- `plan_s10_mirova_parity.md` — paridad MIROVA (S20 cerrado)
- `plan_s11_nti_relative_path.md` — Path B NTI (refutado S78, no dispara Andes)
- `plan_s13_test1_integrated_roi.md` — Test 1 (S27 MILESTONE)
- `plan_s15_p3_*` (3 archivos) — P3.1/P3.2/P3.6 (validado S15-S16)
- `plan_s16_*` (3 archivos) — bg_annulus bbox + e2 MODIS vent + restore S9
- `plan_s32_driver_b_pixel_extent.md` — Driver B (S32-S44)
- `plan_s33_driver_b_phase2.md` — Driver B Phase 2 (S33)
- `plan_s33_tupungatito_d4_subpixel.md` — Tupungatito D4 sub-pixel
- `plan_s70_0_saneamiento.md` + `plan_s70_1.md` + `plan_s70_2.md` — saneamiento S70

**Status históricos**:
- `status_s12_overnight.md`, `status_s13_bibliography_closed.md`,
  `status_s14_handoff.md`, `status_s15_arranque.md`, `s47_progreso_2026_05_16.md`
- `S61_workflow_status.md`, `S62_workflow_status.md` (cierres workflow S61/S62)
- `HANDOFF_S28_MORNING.md`, `SETUP_LOG_S70.md`
- `reporte_cobertura_per_vol_s51.md` (snapshot histórico)

**Decisiones cerradas**:
- `fork_plan.md` — fork mainline+lab 2026-04-09 (mainline ganó)
- `audit_s1_to_s14.md` — auditoría inicial (cubierta por `SESSION_INDEX_CONSOLIDATED_S80.md`)
- `backlog_no_mirova.md` — propuestas descartadas por MISSION.md
- `fix_primary_cluster_test1_coherence.md` — S30 fix implementado

**Lecciones archivadas**:
- `lessons_archive_s5-s6.md` — superpuesto por `lessons.md` actual

**Misc**:
- `todo.md` — session 9 plan post-contamination (cerrado)

## Recuperación

Si en alguna sesión futura necesitás revisar uno de estos archivos:
```bash
git log --diff-filter=R --follow tasks/_archive_s80/<file>.md
# o simplemente
cat tasks/_archive_s80/<file>.md
```

Permanecen versionados en git (`git mv`), no se perdió historial.
