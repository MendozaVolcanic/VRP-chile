# Diseño D11 — Ancla MODIS gateada por señal-summit propia (frente NdC + recall D12 Láscar)

**Fecha**: 2026-06-16 (S110). **Estado**: DISEÑO — NO implementado (gate duro brainstorming).
**Decisión brainstorming (Nicolás)**: target = **solo el ancla** (no tocar detección); discriminador
= **señal-summit propia MODIS** (single-sensor, opción B). **Requiere OK explícito + tag (A45)
antes de cualquier flip.**

## 1. Problema (fenómeno → mecanismo → evidencia)

El ancla espacial honesta MODIS (`enable_honest_anchor_modis`) está OFF. Si se flipea ON (para curar
el recall D12 de Láscar — cluster real al cráter clasificado `far` por el píxel suelto en el Salar),
también promovería a `summit` los **artefactos topográficos del valle de Nevados de Chillán**
(A69/D11): ~141 detecciones de bajo nivel cuyo cluster cae cerca del cráter pero **sin señal
volcánica real** (cráter ETI≈0, VIIRS375 no ve nada esas noches; "artefacto puro" confirmado por
Nicolás S110).

### Evidencia (probes S110 + papers-first, este frente)
- **Probe run-1** (27617831259): el leak entra 100% por el piso absoluto C1, nunca por μ+C2σ.
- **Probe run-2** (27622729779): el ETI espectral **SÍ cancela el grueso** del gradiente topográfico
  (valle ETI absoluto mediano ≈ 0). El leak es la **textura residual del valle** (scatter ETI ±0.01)
  cuya cola cruza C1_scene=0.010 vía dETI contextual. **El cráter es el discriminador**: ETI≈0 en
  noches-artefacto, +0.003 (lava débil, en C1_summit) en noches reales.
- **Papers (4 agentes, `AUDIT_S110_NDC_PAPERS_SYNTHESIS.md`)**: la supresión de topografía en MIROVA
  es espectral (ETI) — nuestro código es fiel (A48). MIROVA detecta la escena pero su defensa contra
  lejanas es el umbral más estricto, no un fix de detección; el FP no-volcánico se maneja por
  supervisión/clasificación, no apagando detección. → **gatear la promoción, no la detección.**

### Por qué NO tocar detección (decisión Nicolás)
Los píxeles del valle ya se clasifican `far` y el frontend los suprime (mirovaEqVrp). Tocar el test
de detección arriesga apagar la señal cat-b real débil (lección de los 3 fixes D11 refutados
S104-S106: V1/V2/fondo-local). El cambio mínimo y de menor riesgo es **condicionar el flip del
ancla a que el cráter tenga señal MODIS genuina**.

## 2. Decisión de diseño

**El ancla MODIS far→summit solo dispara si el MODIS tiene señal-summit propia genuina** dentro del
`inner_radius_km`. NdC artefacto (sin señal summit real) → NO flip → sigue `far` → suprimido como hoy.
Láscar D12 (cluster real al cráter) → flip → `summit` → recall curado.

- Cura (a) artefacto NdC: no se promueve.
- Cura (b) recall D12 Láscar: se promueve la señal real.
- Cura (c) NO apaga cat-b: la detección no se toca; el cat-b real débil con señal summit genuina SÍ
  flipea (las 49/199 noches reales VIIRS-confirmadas tienen señal summit).

## 3. ✅ Pregunta del spec RESUELTA (tarea #1, probe_ndc_assembly run 27625289232)

**¿De qué etapa vienen los píxeles near-crater (≤5 km) del cluster artefacto de NdC?**
**RESPUESTA (definitiva, atribución por etapa):**

| | first-pass summit | 2pass-recapture summit | gate S85 quitó near-crater |
|---|---|---|---|
| **ARTEFACTO** (5 noches) | **0** | **31** | 0 |
| **REAL** (3 noches) | **57** | 50 | 0 |

**Los píxeles near-crater de noches-artefacto son 100% recaptura del `second_pass_adjacent` que el
gate intra-radio S85 PRESERVA** (los mantiene por caer dentro del inner_radius; quita 0). **CERO
seeds genuinos del first-pass.** Las noches reales SÍ tienen first-pass genuino (57 vs 0).
**Confirma A55**: el gate S85 fabrica el cluster near-crater artefacto manteniendo recaptura sin
soporte de first-pass. El gate del ancla lo esquiva sin tocar detección.

## 4. ✅ Definición del gate (CONFIRMADA por tarea #1)

**"Señal-summit MODIS genuina" = existe ≥1 píxel hot del FIRST-PASS Tests 2&3 dentro de
`inner_radius_km`** (`first_pass_summit > 0`), **excluyendo la recaptura del second-pass / gate S85**.
- NdC artefacto: `first_pass_summit = 0` → NO flip. ✓ (probe: 0/5 noches)
- Láscar / cat-b real: `first_pass_summit > 0` → flip. ✓ (probe: 57 en 3 noches reales)

Implementación: el ancla MODIS necesita acceso a la máscara first-pass restringida al inner_radius
(o un flag/contador `n_first_pass_summit` persistido por el pipeline) para gatear el flip. NO usar
`primary_cluster.centroid` ni `n_anomalous_pixels` (contaminados por la recaptura S85).

## 5. Plan de validación (A/B, A45)

- **Tag** `pre-s11X-ancla-modis-crater-gated` antes del primer edit.
- Flag nuevo `enable_honest_anchor_modis_crater_gated` (o gate dentro de anchor.py), **default OFF**.
- A/B 3 brazos: base (ancla OFF) / ancla-ON-sin-gate / ancla-ON-con-gate, sobre los 11 Tier A × ventana.
- **Criterios pre-registrados (A66)**:
  - C1 NdC: ancla-con-gate NO promueve los ~141 artefacto (flip count NdC ≈ las ~49 reales VIIRS-conf).
  - C2 Láscar D12: ancla-con-gate SÍ cura el recall (recupera las ~70/79 alertas MIROVA-confirmadas).
  - C3 cat-b: los flips reales (VIIRS-confirmados) se preservan en los otros Tier A.
  - C4 detección invariante: triggered_test1 / n_first_pass 0-diffs (el gate no toca detección).
- Verificación pixel-level + R3 audit independiente + preview 3 vistas antes de promover.

## 6. MISSION (3 preguntas)
1. **¿Acerca a clon-literal MIROVA?** SÍ — MIROVA reporta summit solo con señal summit per-sensor;
   gatear el flip en señal-summit propia es más fiel que promover un centroide geométrico.
2. **¿Resuelve un drift real?** SÍ — el ancla sin gate promovería artefacto A69 (drift), y el bloqueo
   actual del ancla causa el FN D12 (drift). El gate resuelve ambos.
3. **¿Hay evidencia/papers?** SÍ — probes S110 (cráter = discriminador) + Coppola (summit per-sensor).
   PASS las 3 (vs los gates intra-radio S84/S85 que solo pasaban por puerta GRIS, A55).

## 7. Riesgos / alternativas
- Si la tarea #1 muestra que NO hay forma single-sensor limpia de definir "señal-summit" (la
  recaptura intra-radio contamina irreparablemente), **fallback a opción A** (co-confirmación VIIRS,
  A62) — discriminador cross-sensor ya validado en el destape.
- Relación con A55: este frente puede **resolver de paso** la duda de los gates intra-radio S84/S85
  (si son los que generan el artefacto near-crater, su revisión entra acá).

## 8. Rollback
Flag default OFF; flip reversible. `git checkout <tag> -- pipeline/...`. Reproc revertible vía
merge_promote pattern. NRT no afectado mientras el flag esté OFF.

## 9. NO incluye (YAGNI)
- NO toca el test de detección (first-pass, C1, ETI) — explícitamente fuera de scope (decisión Nicolás).
- NO el fondo temporal por píxel (familia B) — reservado como fallback de último recurso (departure MISSION).
- NO el re-reproc de PCC/Chaitén focal (§1 follow-up, frente separado).

## 10. ✅ IMPLEMENTACIÓN S111 (M1, OK Nicolás + tag pre-s111-ancla-modis-crater-gated)

**Mecánica M1 elegida** (menor riesgo): gatear la APLICACIÓN del override del ancla
honesta MODIS en el wiring, NO dentro del helper puro `resolve_honest_anchor` (que
queda intacto y no afecta a VIIRS, ya validado S108).

1. `pipeline/anchor.py` — helper puro nuevo `honest_anchor_applies(enabled,
   first_pass_gate_enabled, n_first_pass_summit)`: True si el override se aplica.
   Con gate ON requiere `n_first_pass_summit > 0`. Testeado sin pyhdf
   (`tests/test_honest_anchor_modis_gate.py`, 6 tests).
2. `pipeline/process_modis.py` — tras el first-pass:
   `n_first_pass_summit = int(np.sum(fp_hot & (vent_dist_per_pixel <= inner_radius_km)))`
   (idéntico al probe assembly). Persistido como `diag_n_first_pass_summit`. El
   bloque del ancla se gatea con `honest_anchor_applies(...)` en vez de
   `if ENABLE_HONEST_ANCHOR_MODIS`. Cuando el gate bloquea → queda la cascada
   legacy (far, como hoy) → **comportamiento operacional byte-idéntico con master OFF**.
3. `pipeline/profile.py` — flag `ENABLE_HONEST_ANCHOR_MODIS_FIRST_PASS_GATE`
   (default True). El brazo A/B "ancla-sin-gate" lo pone False.

**Por qué M1 y no M2** (gate dentro del helper): M1 preserva la clasificación legacy
EXACTA cuando el gate bloquea (199/199 NdC quedan far, no 196), no toca el helper
compartido con VIIRS, y la decisión del gate es una función pura trivialmente testeable.

**Verificación adversarial (A62)**: caracterización offline de los 11 Tier A
(`char_current_state.py`) confirmó que los candidatos a flip (105-289/vol) tienen
**0 `triggered_test1`** → la rama Test1 de la cascada NO es vía de escape del
artefacto; el gate sobre la cláusula ctx_cluster es completo.

**A/B 3 brazos** (`reproc-s111-d11-ab.yml`, 44 jobs, base=operacional):
`_d11_modis_nogate` (master ON, gate OFF) vs `_d11_modis_gated` (master ON, gate ON).
Audit: `experiments/_s111_d11/audit_d11_ab.py` (criterios C1-C4 + MECANISMO,
pre-registrados A66). Gather: `gather_ab_artifacts.py <RUN_ID>`.
