# BLOQUE ARRANQUE S122 — post-S121 (dashboard revivido, repo podado, D12 investigado)

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat docs/AUDIT_S121_MEJORA_INTEGRAL.md   # informe auditoría integral
cat docs/AUDIT_S121_D12_AB.md            # veredicto D12: NO adoptar (por qué)
```

## Estado al cierre S121 (todo en main)
- **Dashboard producción VIVO** (PR #491): las 3 vistas cargan `_recent.json` 100d (171→27 MB).
  Verificado en Pages real (55 ms, 11.427 recs). Historia completa bajo demanda >90d.
- **Repo podado** (PRs #492/#493): 68 dirs A/B (~1.5 GB) fuera de GitHub. Backup local en
  `../VRP-Chile-data-archive/` + tag `pre-s121-data-prune`. data/ 2.0GB→645MB. `.git` sigue 3.0GB.
- **Disco C destrabado**: se borraron 338 MB de tmp_pack huérfanos (era el blocker real de la red).
- **D12 investigado**: A/B ancla honesta MODIS → **NO adoptar** (destape path-D, PCC 117 MW).
- Auditoría integral multi-modelo (`AUDIT_S121_MEJORA_INTEGRAL.md`), GAP #A corregido.

## §1 — FRENTE A: C2 / D12 (destrabar el FN de Láscar) — el plan
Diseño: `docs/superpowers/specs/2026-07-17-c2-ctxpeak-modis-ab-design.md`.
**⚠️ Premisa corregida**: "portar ctxpeak a MODIS" NO sirve — ya está portado y ON
(`enable_focal_cluster_magnitude`). El blob 117 MW es 100% contextual → el filtro de máscara
no lo baja. C2 real = mecanismo NUEVO (peak-of-kernel de radiancia), no un flag flip.

**Paso 0 (empezar acá, read-only, barato, DECIDE viabilidad)**: sobre los 41 records
destapados (artifacts run 29582035729, o reproc), mirar la distribución de radiancia MIR
por-píxel dentro del blob path-D. ¿Hay núcleo (1-2 píxeles pico + cola difusa → C2 viable)
o blob plano (sin núcleo → D12 irreducible a 1 km, A82, cerrar)? Script sobre `anomaly_pixels`.
El resultado del Paso 0 decide si se invierte en código C2 o se cierra D12 honestamente.

## §2 — FRENTE B: experimental Beyond MIROVA — mejorarlo
Plan: `docs/PLAN_EXPERIMENTAL_BEYOND_MIROVA_S122.md`. Prioridades:
- **M1 — zonas 2a de 8 vols faltantes** [con NICOLÁS, 30-45 min navegador]: mover sliders
  por volcán hasta que la zona naranja abrace el cuerpo real; persistir en ZONE_PRESETS con
  cita física. Incluye WATCH Copahue (cráter El Agrio). Hoy solo PCC/Lastarria/Villarrica.
- **M2 — AVTOD (EXT-8) como 2º ground truth** [ALTA, para paper]: `documentacion/AVTOD_Reath_2019.pdf`
  ya está. Extraer VRP AVTOD vols chilenos → CSV → superponer en Panel 1. Doble cross-validation
  = argumento de robustez del paper Volcanica.
- M3 distancias OCR en Panel 1 · M4 geo_class display (tras M1) · M5 Eq.16 reproc Chaitén/PCC.

## §3 — Otros pendientes (sin urgencia)
- **filter-repo** (`docs/S121_GIT_FILTER_REPO_DESIGN.md`): reducir .git 3.0GB. Destructivo,
  force-push, ventana coordinada + OK Nicolás. Nivel A conservador ~1.4 GB.
- **Backfill P4** (2025-01-01..02-15) — cierra 2025. Despachar `backfill-tier-a.yml`.
- **Arquitectura data sostenible** (AUDIT_S121 §4): el NRT infla ~30 MB/día; repo satélite /
  Releases / branch orphan. Diseñar antes de que .git vuelva a duplicar.
- Paper Volcanica (draft `docs/PAPER_VRP_CHILE_DRAFT_S72.md`, números S119) · solicitud
  Claude Science USD 30k (deadline 15-jul PASÓ — verificar si hay otra ronda).

## 🚫 NO reabrir (anti-A8)
far→summit MODIS como bug con gate/discriminante (A82, agotado) · gates C2 intra-radio (S118) ·
fondo-local (S105) · re-ancla ctx_cluster (A84) · GAP #A (RESUELTO S115 mislabel) ·
ancla honesta MODIS SIN fix de magnitud (S121: destapa 117 MW).

## Reglas vinculantes
A45 (tag+OK antes de pipeline) · A62 (adversarial, el dato refuta la hipótesis — pasó 2× en
S121) · A48/A50 (verificar file:line + cross-source) · A10 (pc.vrp_mw) · S91 (números de
scripts) · A38 (tag+backup antes de borrado) · explicar como geólogo.
