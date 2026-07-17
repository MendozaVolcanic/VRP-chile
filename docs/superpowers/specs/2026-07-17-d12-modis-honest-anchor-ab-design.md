# D12 — A/B del ancla honesta MODIS (¿el gate S111 resuelve el destape?) — S121

> **Estado: DISEÑO. No ejecutado.** Cambio de `enable_*` en profile → requiere el A/B
> con reproc real + R2/R3 + OK Nicolás antes de tocar `mirova_equivalent.yaml` (trigger
> vinculante del proyecto). El A/B usa profile AISLADO (puerta 3 MISSION, no toca operacional).

## Fenómeno (geólogo primero)

Láscar es un volcán persistentemente activo: casi todas las noches tiene un foco térmico
real y débil en el cráter (0.4-6 MW). A 25 km está el **Salar de Atacama**, que en MODIS
(1 km) produce su propia señal térmica (evaporitas/geotermal). El pipeline, al elegir el
"hotspot suelto más caliente" de la escena, a veces se va al Salar → marca la noche `far`
→ el gate del dashboard la borra. Resultado: **429 noches de actividad crateriana real de
Láscar (727 records MODIS) desaparecen** aunque el `primary_cluster` está bien anclado al
cráter (1-4 km). Es un FALSO NEGATIVO sobre señal real — la categoría más grave (D12,
verificado con datos S121).

## El fix YA existe, gateado — y el bloqueo puede estar caduco

La "ancla honesta" (S106) deriva `distance_class` del **cluster vent-anchored** (que está
en el cráter) en vez del píxel suelto scene-wide. Para MODIS está **cableada
(`process_modis.py:1275-1316`) pero OFF** (`enable_honest_anchor_modis: false`).

Motivo del OFF (design 2026-06-11 §3.3/§4): activarla también reclasificaría far→summit
**131 records MODIS path-D-only con pc.vrp>5 MW que son 0% MIROVA = artefacto de magnitud**
(el blob difuso irreducible a 1 km, A82). Decisión pre-comprometida: no mergear sin un fix
de magnitud (C1 cap / C2 ctxpeak). C1 fue REFUTADO (§7); C2 quedó sin probar.

**INSIGHT S121 (la hipótesis de este A/B)**: ese bloqueo se evaluó el **11-jun**. El gate
`ENABLE_HONEST_ANCHOR_MODIS_FIRST_PASS_GATE` (`profile.py:306`, default True) es del
**16-jun (S111)** — POSTERIOR. El gate solo aplica el override si hay **≥1 píxel del
FIRST-PASS Tests 2&3 dentro del inner** (excluye recaptura second-pass y path-D). El foco
real de Láscar ES first-pass genuino; los 131 artefacto son path-D-only. **Hipótesis: el
gate S111 ya filtra los 131 → el destape no ocurre → D12 se cura sin fix de magnitud.**
El propio código lo afirma (`process_modis.py:1273-1274`) pero nunca se midió con reproc.

## A/B (criterio pre-registrado)

**Profile aislado** `_d12_honest_anchor_modis` (= mirova_equivalent + `enable_honest_anchor_modis:
true`, gate True, `data_subdir` propio). Brazo único vs baseline operacional (gate ya default).

**Volcanes / ventanas** (reproc dirigido, patrón A15/A64):
- **Láscar** (mide la CURA): ventanas con actividad MODIS 2025 (feb-may, las 429 noches).
  Criterio: recupera ~summit las noches con cluster crateriano first-pass; ratio magnitud
  Láscar se mantiene ~0.92× (S102) — el ancla NO infla Láscar.
- **NdC + PuyehueCordonCaulle + Tupungatito** (miden el DESTAPE / artefacto): los volcanes
  nevados/difusos donde viven los 131 path-D. Criterio: los records path-D-only pc.vrp>5
  **NO se promueven a summit** (el gate first_pass los excluye), o si se promueven son <5 MW.

**Veredicto**:
- ✅ **Adoptar** si: Láscar recupera las noches FN (recall MODIS sube), Láscar ratio intacto,
  y NdC/PCC/Tupun destapan **0** (o ≤ umbral tolerable) records path-D artefacto pc.vrp>5.
- ❌ **No adoptar / re-diseñar C2** si: el destape ocurre igual (gate no alcanza) → el ancla
  MODIS sigue bloqueada, se necesita el fix de magnitud ctxpeak (C2) primero.

## Ejecución (cuando Nicolás dé OK)

1. Crear `pipeline/profiles/_d12_honest_anchor_modis.yaml` (data_subdir aislado).
2. Workflow reproc dirigido (clonar `reproc-*.yml`, matrix Láscar+NdC+PCC+Tupun × ventanas).
3. Script de análisis pre-escrito: cura FN Láscar (noches far→summit con first-pass) +
   destape (records path-D pc.vrp>5 promovidos en los nevados), → `docs/AUDIT_S1xx_D12_AB.md`.
4. Si adopta: R2 pixel-level (Láscar TIF) + R3 audit independiente + **tag defensivo A45 +
   OK explícito Nicolás** antes de flip `enable_honest_anchor_modis: true` en operacional.

## Lo que NO se toca
El operacional (`mirova_equivalent.yaml`) hasta el veredicto+R2+R3. La magnitud legacy
(vrp/pc.vrp) intacta — el ancla solo reclasifica POSICIÓN (distance_class), no recalcula MW.
