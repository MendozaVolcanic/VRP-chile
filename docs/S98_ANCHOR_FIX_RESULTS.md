# S98 — Resultados del fix del ancla de detección (enfoque B)

**Estado**: implementado + testeado; reproc de validación CORRIENDO; pendiente
audit final + OK Nicolás para promover a operacional (A45). Branch
`s98-detection-anchor`, tag `pre-s98-detection-anchor`.

## Qué se cambió
`pipeline/geo_utils.py`: se separó `get_effective_vent` (conflaba dos roles) en:
- `get_grid_center` → mirova_center prioritario (extent/grid/cross-check).
- `get_detection_anchor` → **vent_lat (cráter) prioritario** (detección dual-ROI,
  clustering vent_anchored, distance_class, distancia mostrada).
`get_effective_vent` queda como alias deprecado de `get_grid_center` (compat
experiments offline). `scripts/run_pipeline.py`: los 3 callers usan
`get_detection_anchor`. Uniforme para los 11 (sin special-casing → robusto a
consolidaciones, la causa de la regresión S80). Guard de regresión:
`tests/test_detection_anchor.py`. Suite: 639 passed, 24 skipped, 0 regresiones.

## Criterios de aceptación (diseño 2026-06-02)
1. Tupungatito: mediana det→cráter **<2 km** (baseline 5.9).
2. Ratio magnitud (Cluster/MIROVA) **hacia 0.5–2.0** (S66 dio 0.67×).
3. Los 8 de offset chico (incl. controles Lascar/Villarrica): **sin cambio**.
4. Recall **NO cae**.

## Baseline confirmado (data/mirova_equivalent, ancla=mirova_center)
Auditoría espacial (A61, det→cráter recomputado al cráter físico) + ratio vs
MIROVA CONS+OCR. Scripts reproducibles: `experiments/_s98_anchor/audit_spatial.py`
y `audit_ratio.py`.

| Volcán | offset cráter↔grid | det→cráter (km) | ratio mediano | %en[0.5,2] | recall |
|---|---|---|---|---|---|
| Tupungatito | 4.86 | **5.909** | **20.0×** | 13.3% | 15/15 |
| PuyehueCordonCaulle | 7.57 | 7.259 | 0.625× | 56.8% | 37/38 |
| PlanchonPeteroa | 2.02 | 2.691 | 2.428× | 36.4% | 22/23 |
| Lascar (control) | 0.83 | 0.357 ✓ | 0.819× ✓ | 80.5% | 77/94 |
| Villarrica (control) | 0.54 | 1.341 ✓ | 1.895× | 75.0% | 4/4 |

→ Correlación directa offset↔corrimiento espacial; Tupungatito magnitud 20×
inflada (cluster glaciar grande, VRP sumado). Diagnóstico S97 reconfirmado con
datos en ambos ejes.

## Resultado FIX (data/_s98_anchor, ancla=cráter) — PENDIENTE reproc
Run GH Actions: 26824615190 (11 vols × mayo, código branch s98). Al terminar:
```
git pull origin s98-detection-anchor    # trae data/_s98_anchor/*.json
PYTHONIOENCODING=utf-8 python experiments/_s98_anchor/audit_spatial.py
PYTHONIOENCODING=utf-8 python experiments/_s98_anchor/audit_ratio.py
```

| Volcán | det→cráter fix | ratio fix | recall fix | ¿cumple? |
|---|---|---|---|---|
| Tupungatito | _pend_ | _pend_ | _pend_ | _pend_ |
| PuyehueCordonCaulle | _pend_ | _pend_ | _pend_ | _pend_ |
| PlanchonPeteroa | _pend_ | _pend_ | _pend_ | _pend_ |
| Lascar (control) | _pend_ | _pend_ | _pend_ | sin cambio? |
| Villarrica (control) | _pend_ | _pend_ | _pend_ | sin cambio? |

## Pendiente DESPUÉS (no en este fix)
- El 44% que S65 no curó: selección de cluster por VRP sumado vs pico NTI. Medir
  cuánto cura B (este fix); si queda gap, brainstorm propio.
- Gates intra-radio redundantes (A55).
- Promoción a operacional: ensamblar mirova_equivalent + display distancia desde
  cráter + OK Nicolás.

## Notas
- Ground truth MIROVA acotado a 05-01..05-18 (snapshot CONS). A17: actualizable.
- A18: el reproc real es la única validación (preview offline no predice cluster
  selection). A45: NO promover sin OK.
