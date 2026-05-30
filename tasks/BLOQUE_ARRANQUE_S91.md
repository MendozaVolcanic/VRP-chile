# BLOQUE ARRANQUE S91

**Sesión previa**: S90 (2026-05-30). Sesión muy grande — 8 PRs (#252–259) + tag
defensivo. Todo persistido en memoria (`reference_s90_*`) + docs + experiments.

## §0 — Worktree + primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat tasks/BLOQUE_ARRANQUE_S91.md
```

## §1 — Lo que cerró S90 (PRs #252–259)
- **#252** tarjeta → "última detección" (no 48h máx) + fix bug TZ (`new Date`→`parseUtcMs`).
- **#253** auditoría recall CONS+OCR: **~75% robusto** (OCR no lo mueve). NdC/Villarrica
  faint VIIRS375-only (MODIS casi ciego, física sub-píxel).
- **#254** imágenes MIROVA de NdC destrabadas (carpeta archivo "ChillanNevadosde", A14).
- **#255–258** detección diurna MODIS: diseño → plan → **código (flag OFF)** → rastro.
  Cierra divergencia "MIR solo nocturno" (Coppola 2016a día K1=-0.6/C1=0.02/15σ; VIIRS
  sigue noche). Tag `pre-s90-daytime-modis` @2f3f73aa (A45).
- **#259** dashboard oculta artefactos cirrus incoherentes (display-only, criterio
  validado empíricamente: t_max<273K & VRP>10 & no-confirmado; 0 reales atrapadas).

Refs memoria: `reference_s90_recall_audit_ndc_villarrica`, `_daytime_modis_impl`,
`_display_cirrus_suppression`, `_coord_research_closed`, `_pcc_cirrus_exposure_and_card_fix`.

## §2 — Pendientes S91 (en orden de valor)

1. **Validar A/B detección diurna MODIS** (lo más importante). Runs GH Actions:
   - NdC: 26687718294 (mar-abr). Villarrica: 26687842353 (mayo). (Estaban encolados
     al cierre S90 — verificar que terminaron: `gh run list --workflow=reproc-daytime-modis-ab.yml`).
   - Comparar recall/precisión enabled vs disabled (computeMetrics) + **R2 pixel-level**
     contra TIF MODIS NdC (47 disponibles) + **R3** (TP diurnas matchean MIROVA real).
   - Criterios de adopción: `docs/superpowers/specs/2026-05-30-daytime-modis-detection-design.md` §7.
   - **Si valida**: `enable_daytime_modis: true` en `mirova_equivalent.yaml` con
     **tag + OK explícito Nicolás (A45)** + reproc operacional + verificar dashboard.
   - Si FP solares dominan → NO adoptar, documentar.
   - Registrar resultados en `experiments/_s90_daytime_modis/RESULTS.md` (paper trail).

2. **Investigar warm-scene highs** (PCC 645/338/222 MW con t_max≥273K). NO son cirrus
   (el fix #259 no los toca, correcto). Causa probable: off-nadir MODIS área inflada
   (A36) o contextual sobre terreno cálido, o señal real categoría b. systematic-debugging.
   NO extender el criterio cirrus bajando t_max ni metiendo t_bg (gate refutado S86).

3. **Marcado en tabla v2** (frontend): rotular los artefactos cirrus en la tabla con
   etiqueta "artefacto cirrus" + atenuar (hoy se conservan visibles sin marca). Preview.

4. **(opcional)** Cargar OCR en la referencia del frontend (`data/mirova/<vol>.json` es
   solo CONS). Mejora la PRECISIÓN reportada (A54: ~49% de "FPs" son OCR no consumido),
   no el recall. Tarea de tooling (regenerar el ground truth con CONS+OCR).

## §3 — Escudo anti-drift (vigente)
1. NO cambiar criterio de selección (vent_anchored validado S87/S88).
2. NO gate `t_bg<260K` en ninguna forma (refutado S86). El criterio cirrus usa `t_max`, NO `t_bg`.
3. NO huella/G1/exclude_zones/gate-intra-radio nuevo (A55).
4. `geo_class`, `mirova_confirmed`, supresión cirrus = ETIQUETAS/display — NO filtran detección.
5. Detección diurna MODIS: flag OFF hasta validar A/B (NO setear en operacional sin tag+OK).

## §4 — Reglas vinculantes activas
A45 (tag + OK antes de pipeline), A47, A52, A54, A55, A18, M1, M2, M8.
Integridad (S88): números/afirmaciones solo del output verificado del script.
Verificación frontend: cargar en preview en navegador no-UTC, no solo `node --check`.
**Criterio cirrus**: re-correr `experiments/_s90_display_artifact/test_criterion.py` si
cambia el dataset MIROVA (debe seguir dando 0 detecciones reales atrapadas).

## §5 — Comunicación con Nicolás
Geólogo: fenómeno físico → mecanismo pipeline → fórmula al final.
**Todo queda registrado para el paper futuro** (pedido S90): provenance de parámetros,
hipótesis, A/B, criterios. Mantener el rastro en docs/specs + experiments.
