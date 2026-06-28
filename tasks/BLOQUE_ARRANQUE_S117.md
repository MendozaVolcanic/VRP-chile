# BLOQUE ARRANQUE S117

**Sesión S116 (2026-06-27)** ejecutó la **auditoría integral A51** ([`docs/AUDIT_S116.md`]) **Y el
sprint de consolidación completo** ("vamos avanzando con todo paso a paso", 6 PRs #457-462, suite
791→**796**). Veredicto de la auditoría: **motor SANO, deuda de TRACKING**; la deuda se saldó casi
toda en la misma sesión. Registro: `project_s116_estado` (memoria) + `docs/AUDIT_S116.md` +
`docs/AUDIT_S116_C2_GATES.md`.

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
```

## ✅ Cerrado en S116 (sprint de consolidación — NO reabrir)
- **C3** (#458): R2 pixel-level reactivado (fix path TIF stale + selección de posición robusta a
  A46-bidireccional, **7/7**) + goldens regenerados al estado actual (pre-S27 obsoletos → 4 records,
  **8/8**). Suite con +21 tests reales (antes skipped).
- **C1** (#459): 6 cabeceras FICHA SDA Nivel-1 (process_modis/viirs/viirs_mod, store, anchor,
  detection_context). Ficha publicable → **v1.1**. Deuda legal CPLT N°372 cerrada.
- **C2** (#461, investigado): gates intra-radio S84/S85 → **NO revertir** (impacto bimodal: cat-b real
  en focales, artefacto en nevados). Decisión: **diferir + A/B estratificado cuando reabra Test1/
  fondo-local** (respeta S105). Ver `docs/AUDIT_S116_C2_GATES.md`. C2 ya NO es "standing sin decisión".
- **C4** (#458): NEW-8 nota S116 (urgencia rebajada, re-evaluar, NO obsoleto).
- **P3** (#460 housekeeping: .gitignore scratch + 96→45 branches; #462 **CMR-search breaker** fetch.py
  espejo A64, TDD 5 tests, tag pre-s116-cmr-search-breaker).
- Doc CLAUDE.md/backlog corregido (anchor.py NO tenía FICHA — el inventario S115 era falso).

## Backlog S117 (sin frente urgente — el sistema está sano y consolidado)
1. **C2 — A/B gates intra-radio**: SOLO cuando se reabra el frente Test1/fondo-local (tocan la misma
   zona, orden S105). Diseño: A/B gate-ON vs gate-OFF, brazos aislados (A47), comparar JSON crudos no
   dashboard (A18), **estratificado focal vs nevado** (clave), cruzar lo REMOVIDO vs MIROVA (A10/A61),
   medir FN sobre cat-b real no solo FP. **NO buscar un discriminante físico universal** — refutado S116
   (A83, `docs/AUDIT_S116_FOLLOWUP.md`): no existe escalar físico que separe cat-b real de artefacto sin
   geometría; un cut "físico" que funcione es régimen-estratificado = gate per-volcán disfrazado.
   Desenlace probable: gate per-volcán (ON nevados / OFF focales). **A45 + MISSION.**
1b. **Llaima / `ctx_cluster` re-ancla (A46-adyacente)** (NEW S116, Hilo 3): el ancla honesta cura el
   sesgo topográfico N cuando `final_hotspot_source=test1_roi` pero NO cuando hereda `ctx_cluster`
   (VIIRS750 solo 49% al cráter). El `ctx_cluster` debería re-anclarse al cráter cuando hay señal Test1
   al cráter, igual que `test1_roi`. Toca pipeline → **A/B + A45**. Bajo (afecta posición display, no detección).
2. **Cabeceras FICHA — pasada exhaustiva opcional** a ~11 módulos de detección secundarios (`test1_*`,
   `path_d_*`, `second_pass_*`, `exclusion_zones`, `single_pixel_mode`). Menor prioridad (el gap crítico
   = 6 núcleo ya hecho). A45.
3. **`Distancia_km` del CSV en diario.html** (validación de posición desperdiciada, Eje 3). Frontend, bajo.
4. **Integrar `IDEAS_CROSS_SENSOR.md` + `IDEAS_MEJORAS_DASHBOARDS.md`** (carpeta padre Volcanologia) a
   `docs/` o backlog del repo. Bajo.
5. **Backfill histórico VIIRS375+V750** (de AUDIT_S112; NRT llena forward). Bajo.
6. **#5 display PCC `geo_class=extension`** (solo si Nicolás lo pide; eligió "no tocar" en S115). Frontend.
7. **Archivar `data/_*/` (757 MB) + `_s76_experiments_pending/` (115 MB)**: Nicolás eligió "dejar como
   está" en S116. Reabrir solo si necesita el espacio.

## 🚫 NO reabrir (anti-A8)
- far→summit MODIS / D11 / A69 (A82, irreducible, cerrado S114).
- inner_radius PCC 20→10 (rechazado S115).
- Parte C Test1-lowmag NdC (sub-píxel → Landsat-v1/NHI-v1, A77, OTRO repo).
- C2 NO se revierte sin el A/B estratificado (destruiría cat-b real en focales).

## Reglas vinculantes (siempre)
A45 (tag + OK Nicolás antes de `pipeline/`), MISSION 3-preguntas, A62 adversarial (cruzar vs MIROVA
con `pc.vrp_mw` — A10), A61 (re-anclar al GVP), A48/A50 (file:line + cross-source). Explicar como geólogo.

## Estado operacional (sano + consolidado)
NRT cada 2h (~92-98% éxito; breaker LANCE-descarga A64 + **breaker CMR-search S116** OK). Guard A46
LIVE. Detección MODIS fiel a Coppola (S114/S116). FICHA SDA v1.1 con cabeceras de código. Suite **796
passed**. R2 (7/7) + goldens (8/8) reactivados. Recall VIIRS375 98.4% / V750 85% / MODIS cráter 100%.
</content>
