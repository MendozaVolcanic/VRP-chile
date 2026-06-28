# AUDIT_S116 — C2: Investigación de los gates intra-radio S84/S85

**Fecha:** 2026-06-27 · **Sesión:** S116 · **Método:** workflow read-only de 4 ángulos paralelos
(mecánica file:line · redundancia frontend · MISSION+historia · impacto en records) + síntesis
adversarial. **NO toca pipeline** (diagnóstico). Run: `wf_ac99e8e1-895`.

**Gatillo:** AUDIT_S116 marcó estos gates como contradicción C2 (anti-patrón A55, flagged por S86 y
S105, "standing sin decisión"). Nicolás pidió **investigar antes de decidir**. Esta es la
investigación; la conclusión **refina y corrige** el framing "redundante → revertir".

---

## Los dos gates (mecánica, verificada file:line)

Son **dos cosas distintas**, no un par simétrico:

| Gate (flag) | Sensor | Qué hace | file:line |
|---|---|---|---|
| `enable_path_d_intra_radio_gate` (yaml l.188) | **MODIS only** (en VIIRS el símbolo se importa pero NO se invoca) | **SUPRIME** toda la máscara Path-D (dNTI contextual 8-vec) que cae **fuera** del inner_radius (`dnti_ctx_hot & dist≤inner`) | `path_d_intra_radio.py:44-49`; `process_modis.py:563-570` |
| `enable_second_pass_intra_radio_gate` (yaml l.207) | **MODIS + VIIRS** | **PRESERVA** el first-pass intacto y solo recorta la **recaptura NUEVA** del second_pass que cae fuera del inner; la recaptura **dentro** del inner se conserva | `second_pass_intra_radio.py:65-72`; `process_modis.py:788-795`, `process_viirs.py:1083`, `process_viirs_mod.py:760` |

**Punto clave (corrige una creencia previa):** el second-pass gate **NO elimina** el cluster
near-crater artefacto (valle topográfico NdC, A55/A73) cuando cae **dentro** del inner — solo recorta
lo de afuera. Por eso S111 mide `first_pass_summit` sobre `fp_hot` crudo (pre-recaptura), para no
contaminarse con esa recaptura preservada.

---

## ¿Redundantes con el frontend? **PARCIAL, no total** (refuta el framing simple)

- El frontend `mirovaEqVrp` (index.html:951-972, replicado en diario/mosaico) opera a **nivel de
  record/DISPLAY**: devuelve 0 si `distance_class != "summit"` o `pc.centroid_dist_km > innerKm`.
  **No toca el JSON.**
- Los gates operan a **nivel de PÍXEL, ANTES del clustering**: cambian el **dato persistido**
  (`n_anomalous_pixels`, cluster ganador, `pc.vrp_mw`, footprint `anomaly_pixels`, `distance_class`).
- **Solapan solo** cuando los píxeles lejanos arrastran el centroide fuera del inner (ahí el frontend
  ya mostraría 0). Cuando el cluster del cráter gana igual, el gate limpia el footprint y el frontend
  NO lo replica. Y los conjuntos difieren: los gates tocan solo Path-D + recaptura; el frontend gatea
  todos los paths (A/B/D/Test1).

→ La afirmación S86/S105 "redundante con el frontend" es **parcialmente cierta** (mismo umbral
espacial, plano distinto), pero **no implica que quitarlos sea inocuo**.

---

## MISSION (3 preguntas, por gate)

| | P1 (¿papers MIROVA core?) | P2 (¿cierra divergencia D?) | P3 (¿alineación infra?) | Veredicto |
|---|---|---|---|---|
| `path_d_intra_radio` (#224/#226) | NO (motivación empírica FPs MODIS) | NO (D9 cerró por cap C S71 + nadir/focal) | GRIS, refutada (frontend ya suprimía desde S33) | **anti-patrón** |
| `second_pass_intra_radio` (#229) | NO (docstring admite drift vs Coppola §347-356) | NO | GRIS, refutada | **anti-patrón** |

A55 (CLAUDE.md) y MISSION.md (tabla anti-patrones l.130 + sección l.137-147) los nombran
explícitamente. Formalmente: **anti-patrón a remover**. PERO ver el impacto antes de actuar.

---

## Impacto en records — **BIMODAL** (lo que cambia la recomendación)

De los 7509 records (43% de los 11 Tier A) con recaptura sobreviviente, **4560 son summit-intra** (lo
que los gates preservan dentro del inner). Solo **26.7% están MIROVA-confirmados** (37.1% con ±1 día).
Pero la confirmación se **parte por firma física del volcán**:

| Tipo | Volcanes (%TP de lo preservado) | Naturaleza | Magnitud pc.vrp_mw |
|---|---|---|---|
| **Focal / desértico** | Láscar 49%, Lastarria 46% (Lazufre), Isluga 36%, PP 29%, PCC 27% (lacolito) | **cat-b REAL** (focos sub-umbral que MIROVA cuantifica) | acotada: med 0.09, max 5 MW |
| **Cumbre nevada** | Llaima 0.4%, Copahue 1.4%, Villarrica 2%, NdC 5%, Tupungatito 22% (ring glaciar) | **artefacto A55/A69** (gradiente topográfico/cirrus) | cola pesada: hasta **60 MW** |

**Implicación:** revertir los gates **global** castigaría a los focales (destruye cat-b real). En los
5 nevados limpiaría ~puro ruido. **No es una decisión binaria limpia.**

**Limitación honesta del análisis read-only (sostiene la recomendación):** estos números miden lo que
el gate **PRESERVA** (intra-radio sobreviviente), NO lo que **REMUEVE** (extra-radio, enmascarado
antes del conteo → invisible en el JSON). Cuantificar la remoción exige un reproc gate-ON vs gate-OFF.

> **Seguimiento S116 (`docs/AUDIT_S116_FOLLOWUP.md` Hilo 1 — precursor read-only del A/B):** se buscó
> un **discriminante FÍSICO per-record** que reemplace el gate geométrico (la "vía MISSION-preferida").
> **Resultado negativo:** NO existe escalar físico universal. El mejor candidato (`test1_k_observed`,
> energía MIR integrada del Test1) da AUC 0.859 pero su cut es régimen-dependiente (focal ~4-5 K /
> nevado ~2,8-3,9 K) y cualquier cut global que rechace ~70 % del artefacto nevado destruye 14-16 % del
> cat-b real. La hipótesis A80 (`nti_max` en el piso) quedó **refutada** (AUC 0.251, inverso — el cat-b
> real está MÁS frío, el piso es compartido). → El A/B futuro **debe ser estratificado focal/nevado**;
> NO seguir buscando un escalar físico universal (frente agotado, anti-A8). El eje espacial es la única
> dimensión que separa las clases (refuerza A82).

---

## Recomendación: **(d) NO revertir ahora — A/B reproc estratificado cuando se reabra el frente Test1/fondo-local**

1. **Respetar la orden S105 de Nicolás** ("no revertir ni re-justificar aún" — los gates están atados
   a la misma zona del pipeline que el frente Test1/fondo-local). Sigue siendo correcta.
2. **No revertir global** (destruiría cat-b en focales; refuta el framing "redundante → quitar").
3. Cuando se reabra el frente Test1: **A/B reproc** gate-ON vs gate-OFF, brazos aislados (A47),
   comparando **JSON crudos** no dashboard (A18: el reproc re-elige cluster desde cero), estratificado
   por volcán focal vs nevado, cruzando lo **removido** contra MIROVA (A10 `pc.vrp_mw`, A61 espacial).
4. **Desenlace probable:** no un flip global, sino **gate per-volcán** (ON nevados / OFF focales) o un
   **discriminante no-geométrico** (que separe cat-b real de artefacto topográfico sin máscara de
   distancia por path).

**Estado de la contradicción C2 (A51):** de "standing sin decisión" pasa a **"decisión informada y
documentada: diferir con razón + plan de A/B"**. Esto cierra el problema que el gatillo A51 señalaba
(la falta de decisión), aunque los flags queden ON por ahora.

**No hay contradicciones entre los 4 ángulos** (consistentes). Único matiz: el Ángulo C dice "como el
frontend ya filtra, revertir no altera la vista" — cierto solo para records cuyo centroide cae fuera
del inner; A/B/D matizan que el efecto sobre el **dato** (footprint/n_anomalous/selección de cluster)
no lo replica el frontend. No es contradicción (vista vs dato).
</content>
