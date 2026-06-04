# S100 — A/B Test1 magnitud (ctxpeak) sobre los 11 Tier A

Run GH **26921561612** (success, 22 jobs = baseline/ctxpeak × 11 Tier A, ventana
2026-04-01..05-31). Artifacts → `experiments/_s99_audit/_ab_full_art/`. Motivado por
la pregunta de Nicolás S100: validar la adopción contra TODA la base, no solo los 3
vols del A/B S99.

## ⚠️ Confounder detectado (A8/A18/A62)
El veredicto crudo (`ab_test1_audit_full.py`) marcó 4 vols con "regresión" de recall
(Lascar -2, Lastarria -1, PCC -1, Isluga +1 FN). **Era artefacto, no efecto del flag.**
Cada job del A/B fetchea granules de NASA independientemente; con los timeouts de CMR
del 03-jun, baseline y ctxpeak bajaron **conjuntos de granules distintos** (ej.
Villarrica 130 records solo-baseline vs 111 solo-ctxpeak; Llaima 46 vs 194). El
record "perdido" Lascar 04-16 05:24 simplemente no se bajó en el job ctxpeak.

## Auditoría JUSTA (solo records comunes a ambos perfiles) — `ab_test1_fair.py`
Aísla el efecto del flag comparando únicamente records con mismo (datetime, sensor)
presentes en baseline Y ctxpeak (272 pares):

| Volcán | pares | recall bl→cp | FN bl→cp | ratio bl→cp |
|---|---|---|---|---|
| **Tupungatito** | 37 | 33→33 | 4→4 | **18.44 → 1.24** |
| Lastarria | 27 | 26→26 | 1→1 | 1.42 → 0.91 |
| PlanchonPeteroa | 37 | 37→37 | 0→0 | 2.32 → 1.64 |
| Isluga | 35 | 35→35 | 0→0 | 1.24 → 1.15 |
| Lascar (control) | 64 | 63→63 | 1→1 | 0.86 → 0.82 |
| PuyehueCordonCaulle | 56 | 56→56 | 0→0 | 1.32 → 1.29 |
| Chaiten | 10 | 10→10 | 0→0 | 1.9 → 1.9 |
| Villarrica | 2 | 2→2 | 0→0 | 2.0 → 2.0 |
| Copahue | 1 | 1→1 | 0→0 | 3.18 → 3.18 |
| NevadosDeChillan | 3 | 0→0 | 3→3 | — (faint VIIRS375, ajeno al flag) |
| Llaima | 0 | — | — | — |
| **TOTAL** | **272** | **d_recall +0** | **d_FN +0** | — |

## Veredicto
**ctxpeak adoptable.** Sobre base comparable: **0 pérdida de recall, 0 FN nuevo** en
los 11 Tier A, y cura la magnitud donde hay path Test1 (Tupungatito 18.4×→1.24×,
Lastarria 1.42→0.91, PP 2.32→1.64). Los ya-calibrados intactos (Lascar 0.82, PCC
1.29). Donde el ratio no cambia (Villarrica/Chaiten/Copahue) los matched no son
test1 (path eruption), así que el flag no los toca — correcto.

Caveat honesto: Llaima/Copahue/Villarrica/NdC tienen muy pocos pares comunes (0-3),
evidencia débil ahí — pero también poca actividad test1, así que el flag los afecta
poco. La señal es sólida donde importa (Tupun/Lastarria/PP/Isluga/Lascar/PCC, 256
de los 272 pares).

## Adopción (A45) — pendiente OK Nicolás
1. `git tag pre-s100-test1-magnitude-adopt <sha> && git push --tags`
2. flip en `pipeline/profiles/mirova_equivalent.yaml` (paths:):
   `enable_test1_contextual_filter: true` + `enable_test1_contextual_keep_peak: true`
3. reproc operacional Tier A → `data/mirova_equivalent/`
4. verif 3 vistas (preview) + R8 público
5. doc divergencia en `MIROVA_DIVERGENCES.md` (contextual literal puro crea FN por
   cráter embebido; keep-peak cura sin FN — divergencia JUSTIFICADA MISSION).
