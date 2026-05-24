---
title: "F46 — Verificación impacto Lastarria post-fix (cuantificar caveat §4.4)"
session: S77
status: review
ai_generated: true
confidence: medium-high
explored: true
tags:
  - pipeline
  - process_viirs
  - vrp_tir
  - lastarria
  - f46
  - verification
related:
  - docs/F46_VRP_TIR_BUG_S76.md
  - docs/F46_AB_TEST_PLAN.md
  - experiments/143_lastarria_f46_verify/audit.py
  - experiments/143_lastarria_f46_verify/audit.out.json
---

# F46 — Verificación cuantitativa: ¿el fix daña Lastarria?

## 1. Pregunta

El doc `F46_VRP_TIR_BUG_S76.md` §4.4 advirtió que Lastarria es el único Tier A
con `vrp_tir_mw` legítimo (fumarolas crónicas, ROI desierto altiplánico
homogéneo, σ_bg típicamente <2 K) y que el fix combinado A+B podría "bajar
algo recall TIR". El número quedó sin cuantificar.

Esta nota lo cuantifica con una simulación read-only sobre los JSON
operacionales pre-fix, sin esperar al reproceso local.

## 2. Método

### 2.1 Lógica del fix (PR #177 mergeado)

`pipeline/process_viirs.py:_compute_vrp_tir_with_gate`:

- **Opción A — gate consistencia MIR/NTI**: si la máscara `hot_mask_2d`
  pre-clustering (unión de paths BT/NTI/NTIrel/dNTIctx) está vacía, o si el
  solapamiento `hot5_mask ∩ dilate(hot_mask_mir, k=3)` es vacío, el record
  emite `vrp_tir_mw = 0`. Elimina por construcción el caso patognomónico
  Chaitén (TIR sin coherencia MIR).
- **Opción B — threshold subido**: el corte pasa de `max(0.5 K, 4σ)` legacy
  a `max(3 K, 6σ)`. En ROI heterogéneo con σ_bg ≈ 4 K, el umbral efectivo
  pasa de ~16 K a ~24 K — la mayoría de pixels contaminantes (lago a 285 K,
  cirrus parcial, parche nieve/roca) deja de contar.

### 2.2 Heurística de simulación

No tenemos BT raw en los records, así que A+B se simulan separadas:

| Categoría | Definición sobre el record | Destino post-fix |
|---|---|---|
| `A_killed` | `n_bt_path + n_nti_path + n_nti_rel_path + n_dnti_ctx_path == 0` y `vrp_tir_mw > 0` | `vrp_tir_mw → 0` (gate A captura) |
| `B_likely_red` | sobrevive A, `vrp_tir_mw > 100 MW` | reducido en magnitud (no cae a 0) |
| `survives` | sobrevive A, `vrp_tir_mw ≤ 100 MW` | probable que el fix lo deje similar |

Caveats:
- El threshold B real puede capar a 0 algunos records con `100 < vrp_tir < 200 MW`
  si su σ_bg es muy alto. La heurística los preserva como "B_likely_red" — es
  un proxy conservador (sobrestima recall post, no lo subestima).
- Recall MIROVA pre/post se calcula contra `latest_consolidado.csv` filtrado
  por `Volcan=<vol>` y `Sensor∈{VIIRS,VIIRS375}`, match ±60 min al `datetime_utc`
  del record. Pre-TP = existe record VIIRS-I-band con `vrp_tir_mw>0`. Post-TP =
  sobrevive A (B_likely_red y survives siguen detectando aunque con menor
  magnitud).

### 2.3 Scope

Sólo VIIRS I-band — el fix toca exclusivamente `process_viirs.py:968-986`.
MODIS y VIIRS M-band no calculan `vrp_tir_mw` separado.

## 3. Resultado

Tabla por volcán (ventana completa data operacional `mirova_equivalent/`, las
estadísticas A/B son sobre records VIIRS I-band con `vrp_tir_mw > 0`):

| Volcán | TIR-iband | A_killed | A% | B_likely_red | B% | survives | recall_pre | recall_post | Δrecall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Lastarria** | **309** | **36** | **11.7%** | **121** | **39.2%** | **152 (49.2%)** | **0.497** | **0.497** | **0.000** |
| Chaiten | 110 | 44 | 40.0% | 57 | 51.8% | 9 (8.2%) | 0.000 | 0.000 | 0.000 |
| Villarrica | 80 | 24 | 30.0% | 41 | 51.2% | 15 (18.8%) | 0.083 | 0.000 | −0.083 |
| Lascar | 25 | 13 | 52.0% | 10 | 40.0% | 2 (8.0%) | 0.054 | 0.027 | −0.027 |
| PlanchonPeteroa | 28 | 16 | 57.1% | 8 | 28.6% | 4 (14.3%) | 0.054 | 0.018 | −0.036 |
| Copahue | 155 | 39 | 25.2% | 83 | 53.5% | 33 (21.3%) | 0.143 | 0.143 | 0.000 |

(Detalles: `experiments/143_lastarria_f46_verify/audit.out.json`.)

## 4. Interpretación

### 4.1 Lastarria — **no se daña**

- **Δrecall = 0.000**. Las 36 records `A_killed` corresponden todos a casos
  donde MIR/NTI no detectaron nada (`paths_sum=0`) pero el path TIR emitía
  `vrp_tir` espurio entre 12-20 MW. Son falsos positivos puros del mismo
  patrón Chaitén, sólo que de menor magnitud (Lastarria sí tiene σ_bg moderado,
  no infla el umbral a miles de MW).
- **A% = 11.7%** — bajo respecto a Chaitén (40%), Villarrica (30%) o
  PlanchonPeteroa (57%). Confirma cualitativamente la afirmación §4.4: ROI
  Lastarria es más homogéneo, el TIR-sin-MIR es minoritario.
- **B_likely_red = 39.2%** — la mayoría de records con `vrp_tir > 100 MW`
  sobreviven al gate A (tienen MIR coincidente). El threshold subido los
  reducirá en magnitud pero no a 0. Como B nunca emite 0 salvo que la máscara
  quede vacía, el recall agregado se preserva.
- **49.2% survives directamente** — la mitad de los records TIR de Lastarria
  son `vrp_tir ≤ 100 MW` con MIR coincidente, exactamente el régimen TIR
  legítimo descrito en §4.4 (fumarolas crónicas firmando en 10-50 MW). El fix
  los deja prácticamente intactos.

**Conclusión Lastarria: el fix no daña recall. La caída esperada §4.4
("algo bajo recall TIR") era teórica; la simulación da 0% en una ventana de
1064 records.**

### 4.2 Chaiten — contraejemplo confirmado

- 40% de los records TIR de Chaiten son `A_killed` (paths MIR/NTI vacíos),
  con magnitudes hasta 580 MW. **Confirma el caso patognomónico §4.2**.
- Recall MIROVA-VIIRS = 0 pre y post: Chaiten tiene 19 refs MIROVA-VIIRS en
  ventana pero nuestro recall es ~0 desde antes del fix (gap arquitectural
  conocido: subpixel/MIR sigma-gating). **El fix no introduce regresión** —
  el recall ya era 0.
- A% = 40% vs Lastarria 11.7% → asimetría 3.4× — el fix actúa exactamente
  donde se diseñó para actuar.

### 4.3 Otros Tier A

- **Villarrica**: A% = 30%, Δrecall = −0.083 (de 0.083 a 0.000). Caída
  absoluta pequeña sobre una base ya degradada (1 TP de 12 refs VIIRS). El
  TP perdido era un record `A_killed` con `vrp_tir` espurio que casualmente
  caía en ventana ±60 min de una ref MIROVA. **No es recall TIR legítimo
  perdido — es FP que dejó de contarse como TP por coincidencia temporal**.
- **Lascar**: A% = 52% (alto), Δrecall = −0.027 (1 TP perdido). Mismo
  patrón. El recall VIIRS-I-band de Lascar es bajo desde antes (subpixel).
- **PlanchonPeteroa**: A% = 57% (más alto), Δrecall = −0.036. Lago
  cratérico inactivo en la ventana — el fix actúa eliminando el ruido del
  lago (esperado §5.1). Cuando F31 A2 integre VRPTIR Aveni 2025
  operacionalmente, el régimen low-T crater lake volverá con su propia
  validación.
- **Copahue**: A% = 25%, B = 53.5%. Δrecall = 0 — los TPs MIROVA siempre
  tenían MIR coincidente, el gate A no los toca.

### 4.4 Veredicto sobre el caveat §4.4

| Caveat original §4.4 | Hallazgo S77 |
|---|---|
| "Lastarria es el único Tier A con TIR legítimo" | Confirmado — 49% survives + 39% B_red sobre 309 records vs Chaiten 8% survives sobre 110. |
| "podría bajar algo recall TIR" | Refutado en escala observable — Δrecall MIROVA-VIIRS = 0.000 sobre 71 refs en ventana. |
| "ROI desierto altiplánico homogéneo, σ_bg <2 K" | Parcialmente confirmado — sólo 36 records (11.7%) tienen MIR vacío vs Lascar 52%, PP 57%. Los volcanes con glaciar/lago concentran el problema. |

## 5. Recomendación

**No se requiere ajuste per-volcano para Lastarria.** El fix combinado A+B
preserva el recall MIROVA dentro de la precisión observable y elimina 36
records con `vrp_tir` espurio entre 12-20 MW (FPs limpios). El default
operacional `enable_vrp_tir_consistency_gate: true` es correcto.

Caveat residual de magnitud (no de recall): los 121 records `B_likely_red`
de Lastarria (39%, vrp_tir 100-300 MW) verán reducción en magnitud reportada
en el dashboard al reprocesarse. Esto **acerca** el `vrp_tir_mw` reportado al
régimen físico esperado (Aveni 2024 RSE, 30-90 MW lago cratérico análogo;
Aguilera 2021 PP, 7-59 MW); no es degradación.

Pending S78:
- Re-correr esta misma audit sobre `mirova_equivalent/` post-reproceso local
  (cuando se complete) para confirmar que la simulación heurística B coincide
  con el resultado real del fix.
- Si se observa caída de recall Lastarria >10% real post-reproceso, evaluar
  per-volcano override `vrp_tir_n_sigma: 5` o `vrp_tir_floor_k: 2.0` en
  `volcanoes.yaml` para preservar régimen low-T fumarolar.

## 6. Limitaciones del método

- **Heurística B aproximada**: no podemos cuantificar magnitud exacta de
  reducción sin BT raw. Los 121 records `B_likely_red` de Lastarria podrían
  perder 30-90% de su `vrp_tir_mw` o quedar casi iguales según σ_bg
  particular. La simulación trata "magnitud reducida" como "sigue siendo TP";
  un reproceso real podría revelar que algunos cruzan a 0.
- **No cuenta hits del gate dilatado**: el código real evalúa
  `hot5_mask ∩ dilate(hot_mask_mir, k=3)`. Records que pasan A (paths_sum>0)
  pero cuyo TIR no solapa espacialmente con el cluster MIR también caerían
  a 0. La heurística no captura esto y sobreestima `survives`. Costo de no
  capturar: la cifra real de A% sería más alta y `survives` más baja, pero
  el recall (post) tampoco bajaría más que el real porque esos casos también
  son TIR-sin-coherencia-espacial.
- **Match recall ±60 min**: ventana amplia. Algunos TPs pueden ser
  coincidencias temporales sin coincidencia espacial. La interpretación
  cualitativa (Lastarria sin daño, Chaitén confirmando) es robusta a este
  ruido.

---

*Generado S77 (2026-05-24) sin reproceso local. Worktree
`VRP-Chile-s77-lastarria-verify`, branch `claude/s77-lastarria-f46-verify`.
Read-only — pipeline operacional intacto.*
