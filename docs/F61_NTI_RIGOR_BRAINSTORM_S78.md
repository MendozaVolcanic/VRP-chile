# F61 — NTI rigor brainstorm (S78, read-only)

**Tipo**: investigación / brainstorm (sin cambios de código ni de datos).
**Branch**: `claude/s78-brainstorm-nti`.
**Worktree**: `VRP-Chile-s78-brainstorm-nti/` (aislado, A44).
**Profile auditado**: `mirova_equivalent` (operacional, 11 Tier A).
**Snapshot**: `data/mirova_equivalent/<Volcano>.json` (commit `f2f60acb`, S78 post-merge #206).

## Por qué este brainstorm

La auditoría S78 sobre falsos positivos identificó ~353 detecciones recientes
sobre cuerpos de agua (lago/laguna) que no son lava ni fumarólica. La firma física
de agua nocturna en sensores satelitales es muy distinta de la de lava o de un
fumarol: el agua irradia casi exclusivamente en TIR (11 µm) y casi nada en MIR
(3.9-4 µm). El indicador que MIROVA usa para diferenciar esos dos modos
espectrales es el **NTI** (Normalized Thermal Index, Coppola 2015 SP 426.5):

```
NTI = (L_MIR - L_TIR) / (L_MIR + L_TIR)
```

- **Agua/lago**: L_MIR ≈ 0 ⇒ NTI ≈ -1 (típicamente < -0.85, casi siempre < -0.90).
- **Lava real**: L_MIR domina ⇒ NTI > -0.6, a menudo > 0.
- **Fumarólica débil**: intermedio, -0.85 a -0.6.

MIROVA define el threshold operacional `k1 = -0.8` (Coppola 2016a Eq.4): un pixel
solo se clasifica como hot si `NTI > k1`. Nuestro pipeline tiene el constante
`NTI_K1_NIGHT = -0.8` cargado en todos los perfiles `mirova_equivalent`, pero
**no lo aplica como gate global**. Lo aplica solo en uno de los cinco paths de
detección. El resultado: cuando los otros cuatro paths disparan, la detección
emite VRP > 0 **aunque el pixel sea físicamente agua**.

Este documento cuantifica el daño y propone tres opciones de fix.

## Hallazgo cuantitativo (vrp_mw > 0, 11 Tier A, histórico completo)

### Distribución de NTI entre positivos

| Bucket NTI            | Count | Interpretación física        |
|-----------------------|------:|-------------------------------|
| -1.00 ≤ NTI < -0.95   |   771 | Agua pura (lago)              |
| -0.95 ≤ NTI < -0.90   | 6,122 | Agua / nieve / suelo frío     |
| -0.90 ≤ NTI < -0.85   | 1,121 | Agua o snow-mix               |
| -0.85 ≤ NTI < -0.80   |    74 | Borderline (fumarólica débil) |
| -0.80 ≤ NTI < -0.70   |    44 | Fumarólica débil              |
| -0.70 ≤ NTI < -0.60   |     6 | Fumarólica fuerte             |
| -0.60 ≤ NTI < -0.40   |     2 | Mezcla lava-fumarola          |
| NTI ≥ -0.40           |     2 | Lava                          |

- **8,014 / 8,068 (99.3%)** de los positivos tienen `NTI < -0.85` (lago/agua,
  no lava). Inaceptable para un clon MIROVA operacional.
- Solo **54 positivos en toda la historia** (lit. 0.7%) tienen `NTI > -0.80`,
  es decir caen del lado correcto del threshold MIROVA.

### Magnitud VRP de los positivos lago-like

| Subconjunto              | n    | min      | mediana | mean   | max      |
|--------------------------|-----:|---------:|--------:|-------:|---------:|
| Lago-like (NTI < -0.85)  | 8,014| 0.02 MW  | 4.42 MW | 55.78  | 1,659.60 |
| Lava-like (NTI > -0.80)  |    54| 0.43 MW  | 5.12 MW | 10.91  |   254.32 |

Los positivos lago-like incluyen **records de >1 GW**, incompatibles con cualquier
fenómeno fumarólico/lacustre. Son detecciones espurias amplificadas por Wooster
sobre pixels que ni siquiera son anomalías térmicas reales.

### Últimos 30 días (período operacional NRT activo)

| Volcán              | Positivos lago-like (NTI < -0.85, 30d) |
|---------------------|---------------------------------------:|
| PuyehueCordonCaulle |                                    296 |
| Villarrica          |                                    227 |
| PlanchonPeteroa     |                                    213 |
| Chaiten             |                                    209 |
| Tupungatito         |                                    202 |
| Copahue             |                                    201 |
| Llaima              |                                    193 |
| Isluga              |                                    185 |
| Lascar              |                                    181 |
| Lastarria           |                                    173 |
| NevadosDeChillan    |                                    108 |
| **TOTAL 30d**       |                              **2,188** |

Estos 2,188 FPs son el ruido visible para Nicolás y SERNAGEOMIN en el dashboard.

## Qué path está disparando cada FP (cross-tab por path)

Cada record VRP > 0 trae cuatro contadores: `diag_n_bt_path`, `diag_n_nti_path`,
`diag_n_dnti_ctx_path`, y el flag `triggered_test1`. Cruzo cuántos positivos
caen por path y qué fracción son lago-like (NTI < -0.85):

| Path / combinación              | n     | % lago-like (NTI<-0.85) |
|---------------------------------|------:|------------------------:|
| Path B (n_nti_path > 0)         |    54 |          **0.0%**       |
| Path A "BT-only"                |     3 |        100.0%           |
| Path D "dNTI-ctx only"          | 7,001 |         99.5%           |
| Test 1 (integrated-ROI)         | 4,178 |         97.2%           |
| dNTI-only sin Test 1            | 3,920 |        ~99.5%           |
| dNTI-only con Test 1            | 3,081 |        ~99%             |
| Test 1 sin dNTI                 |   921 |        ~97%             |

**Por construcción**, Path B aplica `nti > NTI_K1_NIGHT` (gate `> -0.8`) y por
eso tiene 0% de FPs lago-like. Es el único path que respeta el filtro MIROVA Eq.4.

Los otros tres (Path A, Path D, Test 1) emiten hot pixels **sin verificar NTI
absoluto**. Resultado: el 99.3% de los positivos del perfil operacional son
firmas espectrales de agua, no de magma.

## Qué dice el código (mapeo path → gate NTI)

| Path | Definición operacional                                            | Aplica `NTI > -0.8` absoluto? | Ref. |
|------|-------------------------------------------------------------------|:-----------------------------:|------|
| A — BT absoluto      | `bt > t_bg_i04 + threshold_mir`                       | **No**                        | `pipeline/process_viirs.py:414` |
| B — NTI absoluto     | `(nti > NTI_K1_NIGHT) & (bt > t_bg + NTI_BT_SANITY)`  | **Sí**                        | `pipeline/process_viirs.py:419-424` |
| C — NTI relativo     | `(nti > nti_bg + N·σ_nti)`                            | No directo (solo relativo)    | `pipeline/process_viirs.py:~440` |
| D — dNTI contextual  | `nti_local > mean(nti_8nbrs) + N·σ_local_dnti`        | **No**                        | `pipeline/process_viirs.py:~470` |
| Test 1 (integrated)  | suma de radiancia integrada en ROI > K_test1          | **No**                        | `pipeline/test1_integrated.py` |
| Reglas eruption-path | `bt-cluster > t_bg + N·σ` con sigma-cap (S15 Tema F)  | **No**                        | `pipeline/process_viirs.py:~700` |

Path C usa criterio *relativo* (3σ sobre `nti_bg`), lo cual no es equivalente
al gate absoluto: si el ROI está sobre lago, `nti_bg` puede ser ≈ -0.93, y un
pixel con `nti = -0.89` (todavía agua) supera el gate `> nti_bg + 3·0.01`.

## Fenómeno físico — por qué pasa

Sobre un lago/laguna grande (Villarrica laguna del Encanto, Llaima Conguillío,
Puyehue lago Ranco, etc.) en una noche fría:

1. El agua tiene calor residual y irradia en 11 µm. `bt_TIR ≈ 285-290 K`.
2. Pixels del lago **no irradian en 3.9 µm** (NTI muy negativo, ≈ -0.93).
3. El fondo terrestre fuera del lago en invierno chileno está a `bt_TIR ≈ 270-275 K`.
4. **El lago aparece más caliente que el fondo en TIR** (no porque haya
   actividad volcánica, sino porque el agua tarda en enfriarse).
5. Path D, Path A y Test 1 ven el contraste **en BT/radiancia** y disparan
   "hot pixel" — el pipeline calcula `vrp_mir_mw` usando la radiancia MIR que
   en realidad es ruido del sensor sobre agua, multiplicada por Wooster k=18.9
   o k=18.0 (VIIRS), produciendo valores absurdos de hasta 1.6 GW.
6. Path B (que sí aplicaría `NTI > -0.8`) **descarta** ese pixel correctamente.

Es decir: el gate NTI absoluto **ya está cargado en el perfil y ya se usa en
Path B**, pero la decisión de hot mask global (`hot_mask_2d = bt_path_hot | nti_path_hot | nti_rel_hot | dnti_ctx_hot | test1_hot`)
hace una unión booleana donde cualquier path puede levantar la mano. Path B
puede decir "no", pero si Path D dice "sí" el pixel pasa.

## Opciones de fix (ordenadas por costo creciente)

### Opción A — Gate `NTI > -0.85` como AND global sobre TODOS los paths

**Cambio**: justo antes de armar `hot_mask_2d`, calcular `nti_gate = (nti > -0.85)`
y aplicar `hot_mask_2d &= nti_gate` (con manejo de NaN ⇒ False).

- **Ventajas**:
  - Una línea de código, fácil de revertir.
  - Elimina el 99.3% del ruido lago.
  - Coherente con Coppola 2016a Eq.4 (k1=-0.8, dejamos margen -0.85 para no perder fumarólica).
  - Path B queda redundante pero inocuo.
- **Riesgos**:
  - Si algún FN MIROVA conocido tiene NTI realmente entre -0.85 y -0.8 (fumarólica
    crepuscular post-puesta de sol), lo perdemos.
  - Implica re-validar recall sobre los 11 Tier A contra MIROVA-CSV S15.

**Estimación impacto numérico**: de los 2,188 FPs lago-like de 30d, esperamos
eliminar al menos 2,160 (todos los `NTI < -0.85`). Recall MIROVA esperado
**no debería caer** porque los 54 lava-like de toda la historia tienen `NTI > -0.80`,
no caen del lado afectado.

### Opción B — Gate solo en los paths actualmente sin filtro (D, Test 1, A)

**Cambio**: en `dnti_ctx_hot`, `test1_hot`, `bt_path_hot` agregar `& (nti > -0.85)`.

- **Ventajas**:
  - Preserva Path B intacto (ya correcto).
  - Aísla el cambio a los paths conocidos como problemáticos.
  - Más fácil de auditar A/B (un flag por path).
- **Riesgos**:
  - Path A (BT-only) en MODIS pre-S11 era el principal en algunos volcanes.
    Filtrar por NTI ahí puede tocar Lascar S11 regresión que está en investigación.
  - Mantiene la asimetría arquitectural (NTI gate per-path, no global).

### Opción C — NTI threshold per-path empírico

**Cambio**: cada path tiene su propio `k1_path` en perfil:
```yaml
nti_k1_night_bt_path: -0.65    # estricto: BT-only solo lava clara
nti_k1_night_dnti_path: -0.80  # MIROVA literal
nti_k1_night_test1_path: -0.75 # estricto: integrated-ROI sobre lava
```

- **Ventajas**: máxima granularidad, permite tuning per-path por volcán.
- **Riesgos**:
  - Cuatro hiperparámetros nuevos → drift respecto al "clon MIROVA literal".
  - Más combinaciones para A/B testear.
  - Difícil de defender ante un revisor sin un paper que respalde gates per-path.
  - Viola la regla MISSION.md: no agregar parámetros nuevos sin pasar las 3 preguntas.

## Recomendación

**Opción A con threshold -0.85** (con margen de 0.05 frente al k1 MIROVA estricto -0.80).

Justificación:
1. Es la más cercana a "clon literal MIROVA": MIROVA usa k1=-0.8, nosotros
   usaríamos -0.85, ligeramente más permissive para no perder fumarólica
   borderline.
2. Cumple las 3 preguntas de `docs/MISSION.md` afirmativamente:
   - ¿Lo hace MIROVA? Sí, Eq.4 Coppola 2016a.
   - ¿Está documentado en paper autoritativo? Sí.
   - ¿Es el camino mínimo? Sí, una línea.
3. El experimento es trivial de revertir: flag `enable_global_nti_gate` en perfil
   experimental antes de adoptar operacional.
4. El piso de fumarólica borderline (-0.80 a -0.85) son 74 records en toda la
   historia. Pérdida marginal de recall, ganancia masiva de precision.

## Pre-condiciones antes de implementar

Antes de tocar `pipeline/`:

1. **Invocar `superpowers-brainstorming`** (CLAUDE.md: trigger vinculante para
   adopción operacional metodológica).
2. **Escribir test sintético** en `tests/test_nti_gate.py` con caso lago (NTI=-0.93,
   BT_anomaly=10K) que actualmente pasa Path D, debe fallar post-fix.
3. **Crear perfiles A/B** `_global_nti_gate_{enabled,disabled}.yaml` con
   `data_subdir` aislado, no contaminar `mirova_equivalent`.
4. **Reproc local** sobre 2 Tier A representativos (Villarrica laguna + Lascar
   summit, 30d) para verificar:
   - Precision sube (FPs lago-like → 0).
   - Recall vs MIROVA-CSV no cae > 5 puntos porcentuales.
   - Path B still triggers en los 54 lava-like históricos.
5. **R2 verificación pixel-level vs MIROVA web** (lección S33): comparar pixel a
   pixel sobre 5 noches MIROVA-positivas confirmadas antes de adoptar.
6. **Documentar la decisión** en `docs/DRIFTS_S17.md` (drift catalog) y en
   `docs/PROCESS_RULES_S33.md` (regla de adopción operacional).

## Numero síntesis

- **2,188** FPs lago-like (NTI < -0.85) en últimos 30 días sobre 11 Tier A.
- **8,014 / 8,068 (99.3%)** del histórico operacional son lago, no lava.
- **54** positivos lava-like en toda la historia operacional (filtro NTI > -0.80).
- **3 paths sin filtro NTI**: D (dNTI ctx), A (BT-only), Test 1 (integrated).
- **1 path con filtro NTI correcto**: B (`nti > NTI_K1_NIGHT`).
- **Fix recomendado**: Opción A, gate global `NTI > -0.85` como AND sobre hot_mask.
- **Costo cambio**: 1 línea + 1 flag + tests + reproc A/B.
- **Costo NO cambiar**: dashboard SERNAGEOMIN sigue mostrando ~73 detecciones lago/día.

## Anexo — fuentes y referencias

- Coppola, D. et al. (2016a) "Enhanced volcanic hot-spot detection using MODIS:
  the MIROVA system" *Geological Society SP* 426, 5. Eq. 4 (NTI threshold), Eq. 5-6.
- `pipeline/process_viirs.py:419-424` (Path B, único con gate NTI absoluto).
- `pipeline/process_viirs.py:460-485` (Path D, dNTI contextual sin gate NTI).
- `pipeline/test1_integrated.py` (Test 1, sin gate NTI).
- `pipeline/profiles/mirova_equivalent.yaml:38` (`nti_k1_night: -0.8`, cargado pero
  solo usado en Path B).
- `docs/MISSION.md` — las 3 preguntas obligatorias antes de tocar pipeline.
- `docs/DRIFTS_S17.md` — catalog drifts pendientes vs literatura autoritativa.
- Auditoría S78 lagos (referencia conceptual al "353 FPs identificados" mencionado
  en bloque arranque).

## No-acción explícita

Este brainstorm **no modifica ningún archivo de `pipeline/` ni de `data/`**.
Es read-only por diseño (A44 aislamiento, MISSION.md compliance). La adopción de
la Opción A queda como propuesta para la próxima sesión, condicionada al
brainstorming colectivo con Nicolás (skill `superpowers-brainstorming`) y al ciclo
de validación R2/R3 (`docs/PROCESS_RULES_S33.md`).
