# BLOQUE ARRANQUE S118

**Sesión S117 (2026-06-28)** ejecutó el backlog no-urgente que quedó tras la consolidación S116.
Sistema **sano y consolidado**, sin frente urgente. 3 PRs (#466-468), suite 797, 0 cambios de
lógica de pipeline. Registro: `project_s117_estado` (memoria) + `docs/AUDIT_S116_FOLLOWUP.md`
(addendum cierre #1b).

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
```

## ✅ Cerrado en S117 (NO reabrir)
- **#2 FICHA módulos 2°** (#466): cabecera FICHA SDA Nivel-1 en los **8 módulos de decisión**
  (`test1_integrated/contextual_filter/spatial_core`, `path_d_cap/intra_radio`,
  `second_pass_intra_radio`, `exclusion_zones`, `single_pixel_mode`). Excluidos por §4.8:
  serialización (`anomaly_pixels`/`clustering`) + no-productivos (`vrptir` OFF, `detect_tirvolch`
  0 refs). Ficha publicable → **v1.2**. Comment-only, tag `pre-s117-ficha-secondary`.
- **#3 Distancia_km MIROVA en diario.html** (#467): chip "MIROVA dist: X.XX km" (validación de
  posición A61, antes desperdiciada). Verificado en preview real (auto-validó Villarrica 0.84/PCC
  7.83). Frontend, deploy Pages live.
- **#3b IDEAS**: NO copiados al repo (son bancos cross-proyecto del workspace, no material VRP —
  premisa S116 errada, A48). Pointer agregado a `INDICE_GLOBAL.md` (workspace, sin versionar).
- **#1b re-ancla ctx_cluster Llaima**: **CERRADO — no existe fix seguro** (#468, regla **A84**).
  Probe read-only + cross-source S106 convergen: snap-a-vent rompe el Lazufre real de Lastarria;
  nti_peak es ruido en NTI plano (S106 brazo B ya descartado con reproc real). Cosmético (records
  ya summit). Instance-en-posición de A82. Addendum en `docs/AUDIT_S116_FOLLOWUP.md`.
- Cleanup: 5 artefactos de experimentos descartados (árbol git limpio).

## Backlog S118 (sin frente urgente — sistema sano y consolidado)
1. **C2 — A/B gates intra-radio**: SOLO cuando se reabra el frente Test1/fondo-local (orden S105).
   **Estratificado focal vs nevado** (A83), aislar brazos (A47), cruzar removido vs MIROVA (A10/A61),
   medir FN sobre cat-b real. **NO buscar discriminante físico universal** (A83). A45 + MISSION.
2. **Cabeceras FICHA — pasada exhaustiva opcional**: los críticos (6 núcleo S116 + 8 secundarios
   S117) ya están. Quedarían utilitarios fronterizos solo si se quiere 100% (no obligatorio §4.8). A45.
3. **Backfill histórico VIIRS375+V750** (de AUDIT_S112; NRT llena forward). Bajo.
4. **#5 display PCC `geo_class=extension`** (solo si Nicolás lo pide; eligió "no tocar" S115). Frontend.
5. **Archivar `data/_*/` (757 MB) + `_s76_experiments_pending/`**: Nicolás eligió "dejar como está" S116.

## 🚫 NO reabrir (anti-A8)
- far→summit MODIS / D11 / A69-como-bug (A82, irreducible, cerrado S114).
- **#1b re-ancla ctx_cluster (A84, cerrado S117)** — no hay fix seguro; antes de cualquier reproc de
  ancla/posición, el A/B vent-vs-nti_peak de S106 (`docs/superpowers/specs/2026-06-11...`) YA está hecho.
- inner_radius PCC 20→10 (rechazado S115).
- Parte C Test1-lowmag NdC (sub-píxel → Landsat-v1/NHI-v1, A77, OTRO repo).
- C2 NO se revierte sin el A/B estratificado.

## Reglas vinculantes (siempre)
A45 (tag + OK Nicolás antes de `pipeline/`), MISSION 3-preguntas, A62 adversarial (cruzar vs MIROVA
con `pc.vrp_mw` — A10), A61 (re-anclar al GVP), A48/A50 (file:line + cross-source — S117: A50 evitó
re-correr el reproc de S106). Explicar como geólogo.

## Estado operacional (sano + consolidado)
NRT cada 2h (~92-98%; breakers LANCE-descarga A64 + CMR-search S116). Guard A46 LIVE. Detección MODIS
fiel a Coppola (S114/S116). FICHA SDA **v1.2** (6 núcleo + 8 secundarios con cabecera). Suite **797
passed**. R2 (7/7) + goldens (8/8) activos. Recall VIIRS375 98.4% / V750 85% / MODIS cráter 100%.
