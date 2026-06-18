# S113 #3 — Guard de coherencia A46 (`distance_class` summit→far)

**Estado: RESUELTO (LIVE).** Tag defensivo `pre-s113-a46-coherence-guard`. Decisión Nicolás
(A45): guard de pipeline unidireccional. Cierra el ítem #3 de `docs/AUDIT_S112_DASHBOARD_MIROVA.md`.

## Fenómeno (geólogo primero)
En una sola pasada satelital, el sensor puede ver a la vez una señal débil del cráter **y** un
incendio o el Salar de Atacama a 15–34 km. La etiqueta visual del dashboard (rojo=cráter "summit",
gris=lejano "far") la decidía el `final_hotspot`, mientras que el **número de magnitud** que muestra
el dashboard viene del `primary_cluster.vrp`. Cuando no coinciden, aparecía un punto rojo "summit"
cuya magnitud venía de un cluster lejano.

## Diagnóstico (A8 — verificar data fresca)
El flagship del bloque ("Villarrica 06-15, 75 MW @ 28 km summit") **ya se había auto-curado**: el
ancla honesta (`enable_honest_anchor: true`, ya ON) recomputó `distance_class`. Sobre datos actuales,
el bug A46 genuino (`distance_class=="summit"` AND `pc.vrp>0` AND `pc.centroid_dist_km > inner`) eran
**2 records full-history**, ambos Villarrica, ambos artefactos (NTI piso −0.93/−0.95, `geo=far`,
MIROVA silente), que bypasseaban el ancla honesta vía dos forzados de `store.py`:
- **cluster_rescue** (F47): rescata si `pc_cdist <= MAX_HOTSPOT_DIST_KM`, pero MAX = geofence
  `radius_km` (~25 km) ≫ `inner_radius_km` (3–7 km). La suposición "cerca por construcción" es falsa.
- **Regla D vent** (S20): `vrp_vent>0` fuerza summit, pero el `primary_cluster` puede ser lejano.

## El hallazgo grande (por qué NO se re-deriva simétrico)
La prescripción naive ("`distance_class` sigue `pc.centroid`") flipearía **2527 records far→summit**
(la cara opuesta de la asimetría: cluster crateriana real `geo="summit"` tapado por un píxel lejano).
Cruce vs MIROVA (A62/A10): 98.8% en noches MIROVA-confirmadas, PERO impacto NETO de recall = solo
**84 noches enteramente ocultas, 73 de NdC** (artefacto topográfico A69 sub-píxel, A68/D11 — NO
destapar; ver `reference_s113_a46_bidirectional`). El resto son redundantes (cubiertas por otra
pasada summit). El gate conservador S100 ("far" cuando el hotspot es lejano) **es correcto**.
→ Fix **UNIDIRECCIONAL** (solo summit→far). Trap A48/A18 evitado.

## El fix
Guard en `pipeline/store.py` (tras todos los forzados): si `distance_class=="summit"` AND
`primary_cluster.vrp_mw>0` AND `primary_cluster.centroid_dist_km > inner_radius_km` → `"far"` +
`diag_a46_relabel="summit_to_far_pc_beyond_inner"`. Alinea el campo con el gate que el frontend YA
aplica (`mirovaEqVrp`). NO toca detección, cluster selection (A18), magnitud ni paths (MISSION Q3).

- **TDD**: `tests/test_store_a46_coherence_s113.py` (7 tests: 2 RED bandera + 5 GREEN anti-regresión,
  incluye protección de la Regla D S20 y el ancla honesta). Suite 776 passed, 0 regresiones.
- **Relabel post-hoc** (sin reproc, A18-safe): `experiments/_s113_a46/relabel_a46_coherence.py`
  (`--apply`). Cambió exactamente 2 records en `Villarrica.json`.
- **Verificación 3 vistas** (preview real, funciones propias del frontend): los 2 records →
  `isSummit=false`/`mirovaEqVrp=0`; la detección summit genuina de la misma noche (06-18 VIIRS375 @
  1.82 km, 0.823 MW) quedó **intacta** (precisión del guard). 0 errores de consola en index/diario/mosaico.

## MISSION 3 preguntas
Q1 (papers): `distance_class` es campo derivado de clasificación visual (S14 D1), no algoritmo Coppola
→ Q3. Q2 (divergencia): no. **Q3 (alineación interna): SÍ** — hace coincidir el campo persistido con
el gate que el frontend ya aplica. NO es el anti-patrón "gate intra-radio" (A55): no suprime detección
ni magnitud, solo corrige la etiqueta de color.
