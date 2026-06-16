# AUDIT_S110 — Diagnóstico de path: qué detecta el artefacto A69 en NdC (frente D11)

**Fecha**: 2026-06-16. **Read-only sobre** `data/mirova_equivalent/NevadosDeChillan.json`
(reproc histórico run 27584249199 en vuelo; este análisis usa la data live pre-promoción).
**Pedido Nicolás (S110)**: antes de brainstormear D11, atribuir con datos QUÉ path del
pipeline genera las detecciones-artefacto MODIS en NdC (Test1-MIR vs path-D vs eruption).

## Universo
"Destape" = record MODIS `distance_class='far'` con `primary_cluster.centroid_dist_km ≤ 5 km`
(cluster al cráter) y `pc.vrp_mw > 0` = exactamente lo que el ancla honesta MODIS flipearía a
summit. **n = 199 records** (ene–jun 2026).

## Hallazgo 1 — el detector NO es Test1 (refuta el framing del bloque S110)

| Mecanismo | Records que dispara | |
|---|---|---|
| **Test1** (`triggered_test1`) | **0 / 199 (0%)** | el bloque lo culpaba — FALSO |
| BT path (`diag_n_bt_path`) | 0% | legacy, no alimenta hot_mask |
| NTI path (`diag_n_nti_path`) | 0% | legacy |
| ETI path (`diag_n_eti_path`) | 0% | legacy |
| dNTI contextual (`diag_n_dnti_ctx_path`) | 92 / 199 (46%), 568 px | aporta píxeles |
| **eruption first-pass** (`final_hotspot_source='eruption'`) | **199 / 199 (100%)** | **el detector real** |

`discarded_reason='partial_eruption_hotspot_too_far'` en 169/199 (85%): el píxel suelto más
caliente cae lejos (valle, ~7–8 km NW), se descarta, y queda el **cluster al cráter**
(centroide mediana -36.8648/-71.3788 ≈ cráter Nuevo/Arrau -36.868/-71.378, a 0.4 km).

## Hallazgo 2 — el detector ya ES NTI-contextual (refuta "portar NTI como VIIRS")

La detección MODIS real corre por `first_pass_tests_2_and_3` (`pipeline/detection_context.py`,
Coppola 2016a SP426.5:316-325) cuando `ENABLE_FIRST_PASS_TESTS_2_AND_3` (ON). Es la conjunción:

- **Test 2**: `dNTI > min(C1, μ_dNTI + C2·σ_dNTI)`
- **Test 3**: `dETI > min(C1, μ_dETI + C2·σ_dETI)`

con `dNTI = NTI − mean_8vecinos(NTI)` (8-vecino aritmético) y dual-ROI
summit/scene (C1_summit=0.003/C2=5, C1_scene=0.010/C2=10). Los paths legacy (bt/nti/eti/
dnti_ctx) se computan pero **no contribuyen al hot_mask** cuando el first-pass está ON.

**Implicación**: "hacer que MODIS detecte por NTI contextual como VIIRS" es un no-op — **ya lo
hace**. El frente NO es portar NTI; es **por qué el test NTI-contextual deja pasar el valle
tibio** pese a que el NTI debería cancelar la topografía (A69 verificó (I04−I05) plano sobre
gradiente de 15 K).

## Hallazgo 3 — la firma física (eje espacial A61 + cross-sensor A62)

Los `anomaly_pixels` (más calientes) están en el **valle tibio de baja altitud** (BT 295–298 K)
repartidos a **5–24 km del cráter**, no en el cráter. El más caliente a 15–23 km NW (valle bajo).

Discriminante por confirmación cruzada VIIRS375 (el sensor más fino):

| Categoría | n | ΔT cluster (t_max−t_bg) | pc.vrp med | σ_bg med |
|---|---|---|---|---|
| **ARTEFACTO** (VIIRS pasó, NO vio nada) | 141 (71%) | **8.6 K** | 0.52 MW | 3.47 K |
| **REAL** (VIIRS vio summit, cat-b) | 49 (25%) | 12.6 K | 1.11 MW | 4.42 K |
| parcial (VIIRS far) | 9 (5%) | 10.8 K | 0.20 MW | 3.82 K |

El **ΔT de los artefactos = 8.6 K ≈ el gradiente topográfico A69 (~9 K)**: la "anomalía" del
cluster artefacto es literalmente la diferencia de temperatura cumbre-nevada↔valle, no calor
volcánico. Las distribuciones REAL vs ARTEFACTO se **solapan** (8.6 vs 12.6 K) → **no hay umbral
ΔT limpio** (misma no-separabilidad que refutó V1/V2/fondo-local en S104-S106).

## Mecanismo físico propuesto (hipótesis, requiere probe L1B para confirmar)

El umbral efectivo del first-pass es `min(C1, μ+C2σ)`. Con C1 un piso **absoluto** pequeño
(0.003 summit / 0.010 scene), en un volcán nevado la cumbre fría deprime el background local y
píxeles near-crater apenas tibios (calentados por topografía/orientación, NO por lava) superan
el piso C1. El NTI cancela el gradiente SUAVE de gran escala, pero a 1 km el valle tiene textura
real (parches tibios sub-píxel: roca desnuda, cuerpos de agua, agricultura) que produce dNTI
genuino > C1 — anomalías térmicas NO volcánicas (cat-d A54). VIIRS a 375 m resuelve fino y no ve
fuente sub-píxel → confirma artefacto.

## Lo que el JSON NO puede decir (gap → probe L1B en Actions, A65 instrumentación-primero)

La data persistida no guarda, por píxel-semilla del first-pass: su NTI, dNTI, dETI, **cuál de
las dos ramas pasó** (piso absoluto C1 vs estadística μ+C2σ), ni su dist al cráter. Eso decide
el candidato D11 correcto:
- Si pasa por **C1 absoluto** → el piso es demasiado permisivo en escenas de alto rango dinámico
  (candidato: C1 régimen-dependiente, o C1 escalado por σ_NTI de la escena).
- Si pasa por **μ+C2σ** → el background μ/σ contaminado por la cumbre fría (candidato: bg local
  al cluster, ya refutado como fondo-local… o pool de bg que excluya la cumbre nevada).

**Probe propuesto** (espejo S104 ground-truth + A65): reprocesar ~5 granules NdC de noche-
artefacto + ~5 de noche-real en GH Actions con instrumentación `print(flush=True)` que vuelque,
por píxel-semilla, (NTI, dNTI, dETI, rama-que-pasó, dist_cráter, BT). pyhdf roto en Windows →
MODIS solo corre en Actions. Barato (1 corrida), definitivo para no apuntar al path equivocado.

## Veredicto para el brainstorming D11

1. **NO es Test1, NO es "portar NTI"** — es el first-pass Tests 2&3, que ya es NTI-contextual.
2. El leak topográfico sobrevive al NTI por el **piso absoluto C1** y/o el **background μ/σ
   contaminado por la cumbre fría** — a confirmar con el probe L1B.
3. La separación REAL↔ARTEFACTO existe pero es **blanda** (ΔT 8.6 vs 12.6 K solapado) → cualquier
   gate duro arriesga apagar el cat-b real (lección D11 S104-S106). El candidato debe atacar el
   **mecanismo de detección** (piso/background), no un umbral post-hoc de magnitud o ΔT.
