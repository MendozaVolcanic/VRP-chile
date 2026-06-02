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
Run GH Actions: **26830238766** (workflow `reproc-s98-anchor.yml` con artifacts;
5 vols × 05-01..05-18; checkout code_ref=s98). El 1er intento (run 26824615190,
reuse del workflow refresh S97) procesó OK pero falló en el commit step (race A47
+ branch feature) → cancelado y reemplazado por el workflow con artifacts.
Al terminar — un solo comando:
```
bash experiments/_s98_anchor/fetch_and_audit.sh 26830238766
```
(descarga artifacts → data/_s98_anchor/ → corre audit_spatial.py + audit_ratio.py)

**Run 26830238766 (success, 5 vols, 05-01..05-18). Audits: experiments/_s98_anchor/.**

| Volcán | det→cráter base→fix | ratio base→fix | recall (vs MIROVA) | veredicto |
|---|---|---|---|---|
| Tupungatito | 5.76 → **1.25 km** ✓ | 20.0 → 18.9× ✗ | 15/15 → 15/15 ✓ | espacial CURADO; magnitud = 2º problema |
| PuyehueCordonCaulle | 7.23 → **0.69 km** ✓ | 0.63 → **1.24×** ✓ | 37 → 37 ✓ | CURADO (espacial + magnitud) |
| PlanchonPeteroa | 2.69 → **1.14 km** ✓ | 2.43 → **1.50×** ✓ | 22 → 22 ✓ | CURADO (espacial + magnitud) |
| Lascar (control) | 0.36 → 0.37 km ✓ | 0.82 → 0.85× ✓ | 77 → 77 ✓ | SIN CAMBIO ✓ |
| Villarrica (control) | 1.47 → 1.33 km ✓ | 1.90 → 1.90× ✓ | 4 → 4 ✓ | SIN CAMBIO ✓ |

**Confirmación espacial (A61, ubicación no número):** las detecciones de Tupungatito
pasaron del glaciar sur (centroides lat ~-33.43, bin dominante (-33.43,-69.79)) al
**cráter** (lat ~-33.38, bin dominante (-33.38,-69.83)). Es exactamente el bug que
veía Nicolás (MIROVA en el cráter, nosotros en el glaciar) → RESUELTO.

### Veredicto
- **Criterio 1 (det→cráter <2 km): CUMPLE en los 3 afectados** (Tupun 1.25, PCC 0.69,
  PP 1.14). Controles sin cambio.
- **Criterio 3 (controles/recall): CUMPLE** — recall vs MIROVA intacto en los 5;
  espacial estable (PP incluso sube 110→125).
- **Criterio 2 (ratio 0.5-2.0): CUMPLE en PCC y PP** (los lleva a rango), **NO en
  Tupungatito** (sigue ~19×).
- **Hallazgo clave (A62 adversarial):** Tupungatito ahora detecta EN el cráter pero
  la magnitud sigue ~19× → la inflación NO venía de elegir el cluster del glaciar
  (ambos clusters dan ~19-20×), es **sistémica del cómputo de VRP sobre el campo
  glaciar frío** (A12 ΔL inflado Test1 / VRP sumado). Es el "segundo problema" que
  el diseño anticipó y difirió (§2). El fix B NO lo empeora (18.9 ≤ 20).

→ **El fix hace lo que prometía** (anclar al cráter): resuelve el bug espacial
reportado, mejora PCC/PP en magnitud, no rompe controles ni recall. La magnitud de
Tupungatito es un frente separado (§2, post-fix).

## El 19× de Tupungatito: diagnóstico físico (investigación post-veredicto)
Pregunta de Nicolás: ¿desde cuándo el 19× y por qué solo Tupungatito? Respuesta con
datos (snapshot MIROVA CONS+OCR + data mirova_equivalent):

- **Desde abril 2026.** Ratio mediano pc.vrp/MIROVA por mes: feb 4.2×, **mar 1.04×**,
  **abr 20.8×**, may 20.0×. En marzo era perfecto (como Lascar, estable ~1× siempre).
- **MIROVA estable ~0.2 MW** todos los meses (fumarólico "Muy Bajo", actividad real
  constante). No bajó. Lo que cambió es NUESTRA magnitud en los records matcheados.
- **Mecanismo (datos de los matcheados):** el cluster explotó de **2 px (marzo,
  nuestro vrp 0.23 ≈ MIROVA) a 58 px (abril, nuestro vrp 3.99 = 20×)**. Mismo sensor
  VIIRS375. single_pixel_mode cayó 19/33 → 7/39. n_pixels global subió 8→16→23
  (mar→abr→may).
- **Física:** Tupungatito = cráter fumarólico muy débil (~0.2 MW) sobre glaciar a
  5682 m. En otoño-invierno austral cae nieve fresca → mosaico nieve/roca de alto
  contraste local. El path **dNTI contextual** (8 vecinos) no distingue lava de ese
  mosaico → marca decenas de píxeles. Como VRP = SUMA del cluster, se infla a ~4 MW.
  MIROVA usa el pico/NTI, no la suma del campo → se queda en 0.2. Lascar no sufre
  esto (señal fuerte ~1-2 MW sobre desierto seco, sin manto de nieve).
- **Por qué el fix del ancla NO lo tocó:** movió el cluster al cráter (correcto), pero
  el cluster del cráter en invierno igual incorpora el halo nival de 58 px → magnitud
  sigue inflada. Confirma que es problema separado (§2).
- **Mitigación operacional ya existente:** el dashboard usa **Núcleo F5'** por defecto
  (#313, R_core 0.75 km), que recorta el halo → S95 lo calibró a ~2.5× (no 20×).
- **Vías de fix (frente §2, con OK):** gate path dNTI ctx con t_bg muy frío (A23);
  cap n_pixels del cluster en régimen Muy Bajo; usar pico NTI estilo MIROVA.

## PROMOCIÓN A OPERACIONAL (S98, completada)
- Fix de código mergeado a main (PR #318, commit 588cc8fc) → NRT ancla al cráter.
- Tag defensivo `pre-s98-promote-operational`.
- Reproc histórico 90 días (2026-03-04..06-02, decisión Nicolás) de Tupun/PCC/PP a
  mirova_equivalent (runs 26839962842/67867/73072, código con fix), ensamblado con
  pre-90d intacto (merge_promote.py).
- **Verificación preview (3 vistas, S92 L5):** tarjetas Tupun "0.4 km del cráter",
  PCC "2.1 km", PP "0.4 km"; controles Lascar 1.0 / Villarrica 1.5 sin cambio.
  diario/mosaico cargan sin error. det→cráter 90d: 1.25/1.33/1.17 km.
- pre-90d (ene-mar) queda con ancla viejo (decisión 90d); coherente para las vistas
  del dashboard (90d/30d/48h).

## Pendiente DESPUÉS (no en este fix)
- **§2 — magnitud Tupungatito (19× estacional):** recortar el halo nival del cluster
  (ver vías arriba). Brainstorm propio.
- Gates intra-radio redundantes (A55).
- Reproc del histórico pre-90d (ene-mar) si se quiere coherencia total (opcional).

## Notas
- Ground truth MIROVA acotado a 05-01..05-18 (snapshot CONS). A17: actualizable.
- A18: el reproc real es la única validación (preview offline no predice cluster
  selection). A45: NO promover sin OK.
