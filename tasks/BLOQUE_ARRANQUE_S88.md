# BLOQUE ARRANQUE S88

**Sesión previa**: S87 (2026-05-29). Experimento central respondido + 2 PRs mergeados (#234, #235). Trabajo 100% offline, cero tags defensivos (no tocó pipeline NRT).

## §0 — Worktree canónico + primer comando

**Path**: `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/` (raíz, main).

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat docs/AUDIT_S86.md                                   # marco fundacional
cat experiments/_s87_bloque2/RESULTS_dominant_anomaly.md  # resultado S87
cat tasks/BLOQUE_ARRANQUE_S88.md
```

## §1 — Lo que cerró S87

### Hito: vent_anchored validado como criterio óptimo (A/B con datos)

La pregunta central de S87 (¿nuestra mayor anomalía = la de MIROVA?) se respondió
**100% offline** reconstruyendo la escena desde `anomaly_pixels` persistidos
(`cluster_pixels_geographic`). A/B de 3 criterios:

| Criterio | Global ponderado (n=529) |
|---|---|
| **vent_anchored (actual)** | **74.7%** (gana 9/11) |
| vrp_max escena | 47.7% |

**Refuta el experimento L preliminar** (que proponía vrp_max_inner / re-ancla PCC).
El pipeline ya elige bien. Detalle: `experiments/_s87_bloque2/RESULTS_dominant_anomaly.md`.

### Hallazgos clave

- **PCC (25.8%)**: NO es bug de selección (vent_anchored ≈ vrp_max). Lacolito difuso
  707 km² (A20/A24, categoría b). VIIRS 375m resuelve el campo; MIROVA lo colapsa. No forzar.
- **Lascar (67%) DIAGNOSTICADO**: el primary a 18-29 km en erupciones MODIS feb es
  **deuda histórica pre-S38** (records con estrategia vieja `vrp_max`, vent_anchored
  adoptado 2026-05-12, NRT no reprocesa histórico). Post-S38 el pipeline elige el
  cráter bien. **No es bug del pipeline actual.**
- **Premisa refutada**: "rehacer cruce → gap ≤0.5" es falso (script_C ya unía CONS∪OCR;
  el +45% es a nivel pasada, el cruce opera a nivel noche = +9%). Gap 0.243 genuino.
- **Lección metodológica**: el experimento lee el `primary_cluster` persistido = mezcla
  épocas de estrategia. El 74.7% es PISO. Validación limpia del pipeline actual requiere
  reproceso histórico con config vigente.

### PRs S87

- [#234](https://github.com/MendozaVolcanic/VRP-chile/pull/234) — validación + fix dist OCR loader + experimento.
- [#235](https://github.com/MendozaVolcanic/VRP-chile/pull/235) — diagnóstico Lascar pre-S38.

## §2 — Frentes S88 (sin uno obvio — decisión de Nicolás)

### Frente A — Reproceso histórico con config vigente (valida pipeline actual limpio)

El 74.7% mezcla épocas. Reprocesar la ventana 2026-01-29→05-12 con la config actual
(vent_anchored + fixes S38-S40) y re-correr `dominant_anomaly.py` daría el match REAL
del pipeline actual (hipótesis: sube, sobre todo Lascar feb).

- **Regla S15**: reprocesos históricos en **máquina local de Nicolás**
  (`scripts/run_pipeline.py --profile mirova_equivalent --volcano Lascar --start ... --end ...`),
  NO GH Actions (timeout). 11 Tier A × ~105 días es largo → considerar Lascar primero.
- **A47**: reproc local NUNCA paralelo sobre el mismo `data_subdir` (race). Loop secuencial.
- Output: re-correr `experiments/_s87_bloque2/dominant_anomaly.py` post-reproc.

### Frente B — Bloque 3: etiquetar honestamente las detecciones (`pc.classification`)

Implementar el campo derivado de 4 categorías (mirova_confirmed / volcanic_extension /
summit_unconfirmed / artifact_candidate) en `store.py` + rendering frontend.
- **⚠️ A45**: toca `store.py` + frontend → **tag defensivo `pre-s88-classification-field`
  + confirmación EXPLÍCITA de Nicolás antes de arrancar.**
- Diseño completo en `tasks/BLOQUE_ARRANQUE_S87.md` §Bloque 3 + `docs/AUDIT_S86.md`.

### Frente C — Bloque 4: coverage tests (opcional, sin riesgo)

G-R1 (`process_viirs_mod.py` paridad), G-R2 (`profile.py` invariantes), G-R3 (MIR
solo nocturno). Offline, mejora robustez.

### Frente D — Chaitén/Tupungatito divergencia residual — ✅ CERRADO S87

Investigado offline (bearing de nuestra anomalía vs mirova_center). **Tupungatito**: el
gap es por el punto de referencia (mirova_center a 4.86 km del cráter, offset KMZ
confirmado S81 = A30), nuestro primary ancla bien en el cráter — **resuelve C3**.
**Chaitén**: mc centrado, divergencias = dispersión real del domo (categoría b). No hay
acción de pipeline. Detalle: `RESULTS_dominant_anomaly.md` §5.

## §3 — Escudo anti-drift (vigente, NO hacer)

1. NO cambiar el criterio de selección (vent_anchored validado óptimo S87).
2. NO huella como gate. NO G1 ciego (VIIRS750). NO exclude_zones. NO gate intra-radio (A55).
3. NO `t_bg<260K` global (pierde Lascar eruptivo).
4. Criterio = mayor de escena + distancia, como MIROVA.

## §4 — Reglas vinculantes activas

A45 (tag + OK Nicolás antes de pipeline), A47 (no paralelo local), A52, A54, A55,
A56-A60 (META_RULES_S80), M1 (cap PRs 12/20), M2 (persistencia in-vivo), M8 (audit
cada 10 sesiones O 25 PRs), calidad-paso-a-paso, when-to-close-session.

## §5 — Comunicación con Nicolás

Geólogo: fenómeno físico → mecanismo pipeline → fórmula al final.

## §6 — Prompt copy-paste S88

```
Sesión S88 — VRP Chile. S87 cerró respondiendo el experimento central:
vent_anchored (criterio actual) valida 1:1 contra MIROVA (74.7% global, gana
9/11 vols), refutando la hipótesis del experimento L de cambiar el criterio.
PCC 25.8% es lacolito difuso (no bug). Lascar 67% es deuda histórica pre-S38
(records vrp_max no reprocesados), NO bug actual. 2 PRs mergeados (#234 loader
fix + experimento, #235 diagnóstico Lascar).

Worktree: C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile
Primer comando:
  git fetch origin --prune && git pull --ff-only
  cat experiments/_s87_bloque2/RESULTS_dominant_anomaly.md
  cat tasks/BLOQUE_ARRANQUE_S88.md

Frentes (decisión Nicolás, sin uno obvio):
- A: reproc histórico config vigente (valida pipeline actual limpio; LOCAL S15, no GH Actions).
- B: Bloque 3 etiquetar pc.classification (A45 tag + OK explícito antes de tocar store.py).
- C: coverage tests (offline). D: Chaitén/Tupungatito halo ~3km (offline 2D).

Escudo anti-drift: NO cambiar criterio selección (validado). NO huella/G1/exclude_zones/
gate-intra-radio (A55). Criterio = mayor de escena + distancia, como MIROVA.

Reglas: A45, A47, A52, A54, A55, M1, M2, M8, calidad-paso-a-paso. Comunicame como geólogo.
```
