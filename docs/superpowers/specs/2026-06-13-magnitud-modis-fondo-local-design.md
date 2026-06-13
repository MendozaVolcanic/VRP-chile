# Diseño S106 — Magnitud MODIS: fondo LOCAL adyacente al cluster (Coppola 2016a Eq.6)

**Estado**: DISEÑO — pendiente OK Nicolás (A45) para implementación flag-OFF + A/B.
**Revisión S107 (2026-06-13)**: cerrado el gap A48 latente que detectó la auditoría de
design (AUDIT_S106 P2.1 + revisión S107). El fondo correcto es la **corona del cluster
CONTIGUO** (un solo `L_bg` para todos los píxeles del cluster), NO el kernel per-pixel
`compute_local_background` (vrp_regimes.py:21) ni el `effective_L_bg` vent-anchored. La
versión per-pixel falla en los píxeles INTERIORES de un blob compacto (todos sus vecinos
son hot → excluidos → `NaN` → fallback a `t_bg` regional frío en process_modis.py:849 →
**re-inflación**). §3, §4, §6 reescritos abajo con esta corrección. Sin ella, "reusar la
infra" reintroducía la trampa.
**Origen**: el frente "destape MODIS" del ancla honesta (§3.3/§7 del design 2026-06-11).
Tras refutar 6 discriminantes post-hoc + el "port ctxpeak", la auditoría papers-first
encontró la causa raíz real. Reemplaza el candidato ctxpeak de aquel doc.
**Principio rector (Nicolás)**: 1 algoritmo uniforme; raíz, no parche (No Laziness);
algoritmo sobre display (A72).

## 1. El problema (recordatorio)

131-134 records MODIS con `pc.vrp_mw > 5 MW`, **0% confirmados por MIROVA** = artefacto
de magnitud. Son blobs first-pass de escena tibia (Tbg 279-288K), cluster mediano 11 px,
mientras MIROVA reporta sus análogos "típicamente <5 MW" (sp426_5 §"Limits", L689-696) y
los descarta por inspección visual. El ancla honesta (S106) los reclasificaría
far→summit (destape), por eso el ancla MODIS está gateada hasta resolver esto.

## 2. Diagnóstico CORREGIDO (verificado con código + datos, no asumido — A48)

El design 2026-06-11 §7b propuso "portar ctxpeak" como candidato superviviente.
**REFUTADO al verificar el mecanismo**:

- **ctxpeak (`apply_contextual_test1_filter`) está gateado `if final_hotspot_source
  == "test1"`** (process_*.py). De los 132 inflados: **116 son `source=eruption`**, 11
  test1, 5 cluster_rescue, 2 vent (`triggered_test1=False` en 121/132). → ctxpeak
  **provablemente NO los toca** (solo 11/132). Casi diseñé sobre premisa falsa.
- **`single_pixel_mode` ya existe y está ON** (colapsa cluster→píxel pico) PERO su
  ventana es `vrp<5 AND n_px≤3`; los inflados son `vrp>5, n_px≈11` → caen FUERA a
  propósito. Son justo el complemento de lo que ese modo cubre.

**La causa raíz (datos)**: la magnitud del cluster eruption/first-pass se computa
(`process_modis.py:855-858`) como `ΔL = max(L_pix − L_bg, 0)` con **`L_bg` = mediana del
anillo REGIONAL 5-25 km** (frío en volcanes nevados/altura). Para un blob de escena
tibia, ese fondo regional frío infla ΔL de cada uno de los ~11 px marginales → suma
inflada. Evidencia offline (`probe_peak_vs_sum_modis.py`): magnitud por top-3 px cura
87% de los inflados y **preserva Láscar real al 100%** (sus clusters reales son ≤4 px;
los marginales del blob, que el top-3 recorta, son los que están cerca del fondo).

## 3. El fix MIROVA-fiel (Coppola 2016a Eq.6, verbatim verificado A35)

`sp426_5.txt` L350-359, Eq.6: ΔL4PIX = L4alert − L4bk, donde **L4bk se estima como la
media aritmética de los píxeles que rodean al cluster activo** (cita verbatim L357-359:
"the arithmetic mean of all the pixels surrounding the active... cluster").

MIROVA NO usa el anillo regional para la magnitud: usa el **fondo LOCAL adyacente al
cluster**. Mecanismo físico:
- **Blob de escena tibia** (artefacto): los píxeles que rodean al cluster están ~tan
  tibios como el blob → ΔL ≈ 0 → VRP pequeño. Por eso MIROVA los ve "<5 MW".
- **Lava real** (Láscar): el cluster está rodeado de roca fría → ΔL grande → VRP
  preservado.

Es el MISMO principio local-vs-regional que curó el sesgo topográfico del ancla (A69),
ahora aplicado a la MAGNITUD. NO es un cap (evita el anti-patrón MISSION.md): es cambiar
el fondo de referencia por el que el paper especifica.

**El fix correcto = la corona del cluster CONTIGUO (NO reusar la infra existente — guard A48).**
Eq.6 ofrece dos formas: "surrounding the active one" (per-pixel) **o** "around the active
cluster" (corona). Para el problema de los blobs inflados, la corona es la forma robusta y
la única A48-safe. Las dos piezas que el doc anterior llamaba "reutilizables" NO sirven:

- **`compute_local_background` (vrp_regimes.py:21, = `ENABLE_LOCAL_KERNEL_BG` S60-62)**: es la
  variante per-pixel "adjacent to the hot one" (Coppola 2024 L1129). Por CADA hot pixel
  promedia su 3×3 excluyendo los demás hot. Para un blob COMPACTO de ~11 px, los píxeles
  INTERIORES tienen los 8 vecinos hot → `neighbors` vacío → `NaN` (vrp_regimes.py:84-87) →
  el caller hace fallback al `t_bg` regional frío (process_modis.py:849) → **esos píxeles se
  vuelven a inflar**. Solo desinfla los píxeles del BORDE del blob. NO sirve para el destape.
- **`effective_L_bg` (ring 1-3 km Test1, S26/S33/S39)**: está anclado al VENT, no al cluster.
  Un cluster eruption/first-pass puede estar off-vent → fondo de referencia equivocado.

El fix introduce un **helper NUEVO** que calcula **un** `L_bg` desde la corona de píxeles que
rodean al cluster contiguo COMPLETO (la componente conexa 8-vecinos que ya se calcula en
process_modis.py:888-894), y lo aplica por igual a TODOS los píxeles de ese cluster (interiores
incluidos) en el cómputo `delta_L = max(L_pix − L_bg, 0)` (process_modis.py:857). Fiel a "around
the active cluster". NO debe llamar `compute_local_background` ni `effective_L_bg`.

## 4. Decisión de diseño (a validar con reproc, no offline)

No se puede recomputar offline (requiere la grilla de radiancia del granule + estructura
de vecinos). Necesita A/B en GH Actions (MODIS solo corre en Linux). Dos variantes:

Ambas variantes computan **un** `L_bg` por cluster contiguo (no per-pixel) y excluyen de la
corona **TODOS los hot pixels de la escena** (no solo los del cluster propio — evita que un
blob adyacente contamine la corona de otro). Reglas comunes (especificadas para no recaer en A48):

- **Exclusión**: la corona NUNCA incluye píxeles marcados hot por ningún path (Test1/dNTI/
  first-pass) ni NaN. Usar el `hot_mask_2d` completo de la escena (process_modis.py:893), no
  solo el footprint del cluster.
- **Borde del ROI**: si el cluster toca el borde de la grilla 51×51, usar los píxeles de corona
  disponibles. **Mínimo `N_corona ≥ 4`** píxeles válidos; si hay menos → fallback explícito a
  `L_bg_global` (regional) y marcar `corona_degraded=True` en diagnóstico (no silencioso).
- **Conectividad del cluster**: 8-vecinos, idéntica a la agregación existente (process_modis.py:891).

- **V-B (recomendada por fidelidad): corona 8-conexa del footprint del cluster** — el anillo de
  1 píxel de grosor inmediatamente adyacente a la componente conexa del cluster (dilatación
  morfológica 3×3 del footprint menos el footprint), excluyendo todos los hot de la escena.
  Es la lectura literal de "pixels surrounding the active cluster" y es invariante al tamaño/
  forma del cluster (no asume cluster ~circular).
- **V-A (alternativa): anillo geométrico** — media de los píxeles en el anillo `[r_in, r_out]` km
  alrededor del **centroide** del cluster, excluyendo footprint + hot. **Caveat de cluster grande**:
  para un cluster de ~11 px (extensión ~3-5 km) un anillo desde el centroide con `r_in` chico cae
  DENTRO del propio cluster → `r_in` debe ser ≥ el radio del footprint (computar `r_footprint` y
  usar `r_in = max(r_footprint + 1px, 1 km)`, `r_out = r_in + 2 px`). Menos robusto que V-B; se
  incluye solo como control del A/B.

Discriminador pre-registrado V-A vs V-B (numérico, A66): (1) Láscar control debe quedar en
ratio 0.92× ±15% en AMBAS; (2) ganadora = la que lleva ≥85% de los inflados pc.vrp>5 a ≤5 MW
**sin** bajar ningún summit MIROVA-confirmado >15%; (3) desempate = menor varianza de la corona
(N_corona efectivo) y menos records con `corona_degraded=True`.

## 5. Predicciones PRE-REGISTRADAS (A66 — antes del reproc)

| vol | predicción magnitud (fondo local vs regional) | criterio duro |
|---|---|---|
| Chaitén/Copahue/NdC/PP/PCC (inflados warm-scene) | ΔL colapsa → pc.vrp de >5 a <5 MW (los ~130 curados) | inflados pc.vrp>5 → ≤5; 0% eran MIROVA, no se pierde recall real |
| **Láscar** (control, lava real rodeada de roca fría) | fondo local ≈ fondo regional (roca fría en ambos) → magnitud SIN cambio | ratio 0.92× preservado (±15%) |
| Tupungatito/Villarrica/Llaima (V375 nevados) | NO afectados (este fix es MODIS; V375 ya curado por área nadir S103) | sin cambio |
| detección (todos) | el fondo de magnitud NO toca la detección (Tests/first-pass intactos) | trig/recall 0 diffs pareados — delta = BUG |

**Decisión pre-comprometida**: si Láscar pierde >15% de magnitud → el fondo local es muy
agresivo (roca fría mal estimada) → recalibrar anillo, NO promover. Si los inflados no
caen <5 → refuta la hipótesis (la inflación no era el fondo) → reabrir. Si detección
cambia → bug, parar.

## 6. Plan A45 (cuando Nicolás dé OK)

1. Tag `pre-s107-modis-fondo-local` + push.
2. TDD (RED→GREEN) ANTES del código. Casos sintéticos obligatorios:
   (a) **lava real**: cluster chico (≤4 px) sobre roca fría → corona fría → ΔL preservado (Láscar control).
   (b) **blob tibio**: cluster ~11 px sobre escena tibia → corona tibia → ΔL→0 → pc.vrp de >5 a <5.
   (c) **interior de blob compacto** (el caso que mata al per-pixel): verificar que los píxeles
       INTERIORES del cluster usan la corona (un solo L_bg), NO caen a fallback regional → desinflan.
   (d) **dos blobs adyacentes**: la corona de uno NO incluye píxeles hot del otro (exclusión escena-wide).
   (e) **cluster en el borde del ROI**: N_corona < 4 → fallback a L_bg_global + `corona_degraded=True`.
   (f) **detección no cambia**: trig_t1/recall idénticos al baseline (el fondo de magnitud no toca Tests).
3. Implementar helper NUEVO `cluster_corona_background()` (puro, en vrp_regimes.py) anclado al
   footprint del cluster contiguo + flag `enable_local_cluster_magnitude` (OFF) en
   process_modis.py (rama 819-859). **NO llamar `compute_local_background` (per-pixel) ni
   `effective_L_bg` (vent-anchored) — guard A48**. Cuidado A49 (no comer el `return`/desempaque
   de la rama eruption). El helper recibe la grilla de radiancia + el footprint del cluster +
   el `hot_mask_2d` escena-wide; devuelve un escalar L_bg + flag `corona_degraded`.
4. Profiles A/B `_modis_localmag_{a,b}` (V-A/V-B) + workflow (patrón S106), data_subdir
   aislado, 6 vols afectados + Láscar control.
5. Audit pre-escrito vs §5 + R3 independiente + verif pixel-level vs TIF MIROVA.
6. Si pasa criterios → flip + reproc 11 + activar espejo ancla MODIS (destape ya limpio)
   + frontend 3 vistas + cierre del frente §3.3/§7.

**NO implementar sin**: OK de Nicolás + variante elegida. El frente es nice-to-have
operacional (el dashboard hoy oculta los inflados por el far-class; el ancla MODIS sigue
OFF). Calidad > velocidad.

## 7. Por qué este diseño es mejor que "port ctxpeak"

| | port ctxpeak (§7b, refutado) | fondo local Eq.6 (este) |
|---|---|---|
| toca los inflados | NO (gate source=test1, 92% son eruption) | SÍ (cómputo de magnitud de todos) |
| grounding | heurística de S100 | Coppola 2016a Eq.6 verbatim |
| naturaleza | filtro de píxeles | fondo de referencia (raíz) |
| anti-patrón MISSION | — | NO es cap; es el fondo del paper |
| coherencia sesión | — | mismo principio local-vs-regional que A69 |
