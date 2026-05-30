# BLOQUE ARRANQUE S92

**Sesión previa**: S91 (2026-05-30). 5 PRs mergeados (#261–265). Sesión marcada
por **4 errores de integridad de números** (todos corregidos) por un entorno que
entrelazaba/corrompía salidas de comandos. Nicolás pidió auditoría → se hizo +
auditoría independiente (subagente) → 4/4 archivos PASS tras correcciones.

## §0 — Worktree + primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat tasks/BLOQUE_ARRANQUE_S92.md
```

## §0.5 — REGLA DURA DE INTEGRIDAD (aplicar TODA la sesión)

Ver `~memory/feedback_s91_no_transcribir_numeros.md`. Resumen vinculante:
1. **Un tool call por mensaje** si el entorno muestra cancelaciones en cascada /
   salidas entrelazadas (pasó toda la S91).
2. **Ningún número entra a doc/PR/commit transcrito a mano.** Script reproducible
   = fuente de verdad; el doc apunta a él.
3. **Verificación programática doc==fuente** antes de commitear (`python -c` que
   imprima OK/MISMATCH + ALL_VERIFIED).
4. **JSON/txt con BOM (utf-8-sig) = lo escribió un subagente** → números NO
   verificados de 1ª mano (A48). Re-verificar o descartar.

## §1 — Lo que cerró S91 (PRs #261–265)
- **#261** warm-scene PCC diagnosticado + tooling A/B (`analyze_ab.py`). Tenía 2
  errores de transcripción → corregidos en #262.
- **#262** corrección integridad tabla warm-scene + `audit_warmscene.py`
  (reproducible, ALL_VERIFIED).
- **#263** fix `analyze_ab.py`: print duplicado + **guard A/B incompleto** (aborta
  si enabled o disabled vacío, evita Δ ilusorio).
- **#264** Villarrica A/B (tenía afirmación falsa "MODIS=0") → corregido #265.
- **#265** corrección: Villarrica SÍ tiene MODIS; Δ=0 verificado pero causa fina
  PENDIENTE.

Refs memoria: `reference_s91_warmscene_pcc_closed` (CERRADO),
`reference_s91_daytime_ab_pending`, `feedback_s91_no_transcribir_numeros`.

## §2 — PENDIENTES S92 (en orden de valor)

### 2.1 — A/B detección diurna MODIS — CERRAR (lo más importante)
- Verificar runs terminados: `gh run list --workflow=reproc-daytime-modis-ab.yml`.
  Al cierre S91: Villarrica (26687842353) ✓ completo; **NdC (26687718294) aún
  in_progress**. NdC es el caso que decide (tiene ~264 records MODIS).
- `git pull` (los JSON los commitea el workflow a `data/_daytime_modis_{enabled,disabled}/`).
- Correr `python experiments/_s90_daytime_modis/analyze_ab.py --volcano NevadosDeChillan --start 2026-03-01 --end 2026-04-30`.
- **R2 pixel-level** evento diurno NdC vs TIF MODIS (NdC tiene 47 TIFs, PR #254):
  `scripts/compare_tif_mirova_vs_ours.py`.
- Criterios adopción: `docs/superpowers/specs/2026-05-30-daytime-modis-detection-design.md` §7.
- **Si valida** → `enable_daytime_modis: true` en `mirova_equivalent.yaml` con
  **TAG + OK explícito Nicolás (A45)** + reproc operacional + dashboard.
- Si FP solares dominan → NO adoptar, documentar.

### 2.2 — BUG SOSPECHADO: el flag diurno toca VIIRS (verificar PRIMERO en limpio)
**Hallazgo S91 (hipótesis fuerte, NO confirmado por entorno degradado)**: el A/B de
Villarrica mostró ~108 records con `mirova_eq_vrp` distinto enabled vs disabled, y
casi todos eran **VIIRS** (NOAA20/SNPP/NOAA21), t_max 277–299K (escenas diurnas).
Por diseño, `enable_daytime_modis` **NO debería tocar VIIRS** (VIIRS sigue
nocturno, clon literal MIROVA — design doc §11).
- **Investigar (systematic-debugging)**: ¿el perfil `_daytime_modis_enabled.yaml`
  cambia algún threshold que se aplica también a VIIRS? Revisar cómo
  `process_viirs*.py` lee `nti_k1_day`/`n_sigma_mir_day`/`dnti_contextual_c1_day`
  y si `_reject_daytime`/`_select_thresholds` tienen fuga de scope a VIIRS.
- Re-correr el diff enabled vs disabled sobre Villarrica en LIMPIO (un comando,
  salida a archivo, leer con Read) para confirmar el número y los sensores.
- Si es bug real de scope → es relevante para la adopción (el A/B no es limpio si
  el flag contamina VIIRS). Tag + OK antes de tocar pipeline (A45).
- **OJO**: puede ser artefacto de ruido del reproc (re-cluster no determinista) y
  no del flag. Distinguir: ¿los records VIIRS que cambian tienen el MISMO
  `vrp_mw` pero distinto `mirova_eq_vrp`? eso apuntaría a cluster selection, no a
  thresholds. Verificar con cuidado, NO asumir.

### 2.3 — Warm-scene PCC: CERRADO (no reabrir salvo dato nuevo)
Categoría b (real, sobre-estimado por suma de campo difuso MODIS vs foco VIIRS
MIROVA). Ver `reference_s91_warmscene_pcc_closed`. Corrección menor pendiente
(cosmética): en `FINDINGS.md` §4 el "0.51 MW @ 2026-04-04" está mal-fechado
(es de 2026-01-22); el OCR de 04-04 tiene 0.55/0.63. No afecta conclusión.

### 2.4 — Tabla v2 frontend (no empezada S91)
Rotular/atenuar artefactos cirrus en la tabla del dashboard. **Requiere preview
en navegador no-UTC** (no solo node --check). Offline, independiente del A/B.

### 2.5 — (opcional) Cargar OCR en `data/mirova/<vol>.json`
Hoy solo CONS → mejora precisión REPORTADA, no recall (A54). Tooling.

## §3 — Escudo anti-drift (vigente, NO violar)
1. NO vent_anchored nuevo (validado S87/S88).
2. NO gate `t_bg<260K` (refutado S86). Criterio cirrus usa `t_max`, NO `t_bg`.
3. NO huella/exclude_zones/gate-intra-radio nuevo (A55).
4. geo_class/mirova_confirmed/supresión cirrus = ETIQUETAS/display, NO filtran.
5. Detección diurna MODIS sigue **flag OFF** hasta validar A/B (NO setear sin tag+OK).

## §4 — Reglas vinculantes
A45 (tag+OK antes de pipeline), A47, A52, A54, A55, A18, A48, M1, M2, M8.
**Integridad S91 §0.5 (reforzada): números solo de output verificado, script
reproducible, verificación programática antes de commit.**
Frontend: verificar en preview navegador no-UTC.

## §5 — Comunicación con Nicolás
Geólogo: fenómeno físico → mecanismo pipeline → fórmula al final.
**Todo queda registrado para el paper futuro** (provenance, hipótesis, A/B, criterios).
