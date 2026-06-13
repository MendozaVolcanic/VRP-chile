# Diseño S106 — Magnitud MODIS: fondo LOCAL adyacente al cluster (Coppola 2016a Eq.6)

**Estado**: DISEÑO — pendiente OK Nicolás (A45) para implementación flag-OFF + A/B.
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

**Infraestructura existente reutilizable**: ya hay fondo local para Test1
(`effective_L_bg`, ring 1-3 km, S26/S33/S39) y `ENABLE_LOCAL_KERNEL_BG` (S60-62). El fix
extiende un fondo local-adyacente al cómputo de magnitud del cluster eruption/first-pass
(líneas 855-858), no solo al path Test1.

## 4. Decisión de diseño (a validar con reproc, no offline)

No se puede recomputar offline (requiere la grilla de radiancia del granule + estructura
de vecinos). Necesita A/B en GH Actions (MODIS solo corre en Linux). Dos variantes:

- **V-A: anillo local adyacente** — L_bg = media de píxeles en un anillo estrecho
  (p.ej. 1-3 km) alrededor del centroide del cluster, excluyendo los píxeles del cluster.
  Fiel a "surrounding the active cluster".
- **V-B: vecinos inmediatos** — L_bg = media de la corona 8-vecinos del bounding box del
  cluster (más literal "pixels surrounding"). Más sensible a clusters grandes.

Discriminador pre-registrado: V-A vs V-B por cuánto preservan Láscar real (ratio 0.92×
debe mantenerse) vs cuánto desinflan PCC/Chaitén/Copahue.

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

1. Tag `pre-s106-modis-local-mag` + push.
2. TDD: test sintético — cluster tibio sobre escena tibia (ΔL→0 con fondo local) vs lava
   sobre roca fría (ΔL preservado), ANTES del código.
3. Implementar helper `local_cluster_background()` (puro) + flag
   `enable_local_cluster_magnitude` (OFF) en process_modis.py:855-858. Cuidado A49
   (returns) + reuso de la infra `effective_L_bg`.
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
