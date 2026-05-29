# BLOQUE ARRANQUE S89

**Sesión previa**: S88 (2026-05-29). 4 PRs mergeados (#238 análisis+tests, #239 fix
integridad, #240 Frente A infra + 2º fix integridad, #241 diseño Frente B). 100%
offline, 0 cambios al pipeline NRT (A45 no disparada). Auditoría adversarial ejecutada.

## §0 — Worktree + primer comando

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat experiments/_s88_lascar_reselect/RESULTS_reselect.md          # resultado S88
cat docs/superpowers/specs/2026-05-29-s88-pc-classification-design.md  # diseño Frente B
cat tasks/BLOQUE_ARRANQUE_S89.md
```

## §1 — Lo que cerró S88

### Hito: la re-selección offline NO es proxy del pipeline (refuta el atajo)

S88 intentó estimar el match del pipeline actual re-aplicando `vent_anchored` sobre los
`anomaly_pixels` persistidos. **Falló como método** (reconfirma A18): el match BAJA
74.7% → 69.0% global, fuerte en cráteres compactos bien calibrados (Lastarria −15,
Villarrica −27, Tupungatito −18). Causa: re-clusterizar el top-100 persistido (sesgado a
los pixeles más calientes de escena) no reproduce la selección real sobre el grid
completo. **El 74.7% de S87 sigue siendo el único número; el reproceso real es la única
vía de validación limpia.**

### Decomposición Lascar feb (válida — propiedad factual de los pixeles)

De 10 no-match Lascar-feb: **0 recuperables offline + 2 borde + 8 detection-loss**. Los 8
son MODIS (Terra Y Aqua) durante la erupción, con el cráter AUSENTE del top-100
persistido (`dmin` 7-14 km). Mecanismo: pipeline viejo (bt_path ON + sin gates S84/S85 +
vrp_max) llenó el top-N con pixeles del Salar off-nadir, evictando el cráter. VIIRS-I las
mismas noches sí retuvo el cráter. **Fortalece el diagnóstico S87** (deuda histórica) con
mecanismo más preciso: no es selección, es pérdida de detección.

### Dos deslices de integridad — corregidos en sesión

- PR #238 documentó números ANTICIPADOS (resel 75.4%, +4.4pp, 7 recuperables) →
  fabricados. Corregido PR #239 con números reales (69.0%, +2.5pp, 0 recuperables).
- Auditoría adversarial detectó: el doc decía "todos detection-loss MODIS_TERRA
  ~01-02:30" cuando los records ganadores de varias noches son AQUA ~06-08. Corregido #240.
- **Regla nueva** (`memory/feedback_integridad_numeros_S88.md`): ningún número/afirmación
  entra a doc/commit/PR sin copiarse del output verificado del script. Tras error de
  integridad, correr auditoría adversarial independiente.

## §2 — Frentes S89

### Frente A — EJECUTAR el reproceso (infra ya en main, PR #240)

1. `gh workflow run reproc-s88-lascar-validation.yml --ref main`
   (workflow_dispatch invocable porque ya está en main — S73).
2. Esperar (~30-90 min, Lascar feb solo, timeout 150 min). Notificación al terminar.
3. `git pull` (el workflow commitea `data/_s88_reproc_validation/Lascar.json`).
4. `python experiments/_s88_lascar_reselect/post_reproc_validate.py` → tabla old vs new.
5. **Hipótesis a confirmar**: los 8 detection-loss + 2 borde flipean al cráter con la
   config actual → Lascar sube de ~67% a ~76%, valida que el gap es deuda histórica.
6. Documentar resultado en `experiments/_s88_lascar_reselect/` + cerrar.

### Frente B — implementar tras decisión Nicolás (diseño listo, PR #241)

Diseño en `docs/superpowers/specs/2026-05-29-s88-pc-classification-design.md`.
**Espera 3 decisiones** (§7 del doc):
1. ¿`geo_class` en store.py (geometría) + `mirova_confirmed` en frontend (cruce CSV)?
2. ¿`EXT_KM` 2 km global o per-vol (PCC/PP necesitan más)?
3. ¿Fase 2 (artefacto físico PCC/Tupungatito) en roadmap, o 3 categorías honestas basta?

Tras decisión: TDD → tag `pre-s89-geo-class` (A45) → `volcanic_features.yaml` →
`store.py` geo_class ~15 líneas → frontend render → verificación. **NO usar gate
`t_bg<260K` (refutado S86).**

### Frente C — coverage tests ampliable (opcional, sin riesgo)

Los 3 G-R ya están (#238). Más cobertura: process_viirs_mod paridad profunda, edge
cases de profile inheritance.

## §3 — Escudo anti-drift (vigente)

1. NO cambiar criterio de selección (vent_anchored validado S87, reconfirmado S88).
2. NO gate `t_bg<260K` en ninguna forma (refutado S86, pierde Lascar eruptivo).
3. NO huella/G1/exclude_zones/gate-intra-radio nuevo (A55).
4. Criterio = mayor de escena + distancia, como MIROVA.

## §4 — Reglas vinculantes activas

A45 (tag + OK antes de pipeline), A47 (no paralelo local), A52, A54, A55, A18
(re-selección offline ≠ pipeline), M1, M2, M8, calidad-paso-a-paso. Integridad
(regla S88): números/afirmaciones solo del output verificado.

## §5 — Pendiente lateral (spawn task S88)

Discrepancia `mirova_center` PCC: `volcanoes.yaml` (-40.5903,-72.1187) vs
`frontend/index.html` (-40.582,-72.131) = 1.39 km. El dashboard mide distancias PCC
desde otro punto que el pipeline. Determinar canónico (KMZ + AUDIT_INTEGRAL_S81),
sincronizar frontend↔yaml, revisar los otros 10 Tier A. NO toca pipeline.

## §6 — Comunicación con Nicolás

Geólogo: fenómeno físico → mecanismo pipeline → fórmula al final.
