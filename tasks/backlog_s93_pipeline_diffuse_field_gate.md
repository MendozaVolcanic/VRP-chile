# BACKLOG S93 — Gate de coherencia "campo difuso" en PIPELINE (opcional, futuro)

**Estado**: ABIERTO, NO iniciado. Decisión de Nicolás (S93): hacer el display ahora
(PR S93, mergeado) y dejar este item documentado para una sesión dedicada **si** se
decide avanzar. El display ya resuelve el problema operacional.

## Contexto

El record PCC 2026-05-05 07:30 MODIS_AQUA reporta `pc.vrp_mw=337.7` cuando MIROVA
reporta el mismo evento a ~0.3 MW. Diagnóstico S93: es **artefacto A23/D9** — path D
(dNTI contextual) disparando sobre fondo gélido (`t_bg=242.9 K`, −30 °C); 670 píxeles
de terreno apenas tibio (`t_max=+1.8 °C`) sumados. **MODIS 1 km no resuelve el lacolito
real** (sub-píxel; MIROVA lo ve con VIIRS 375 m). Para ese record MODIS, lo correcto
físicamente es VRP≈0. Reclasificado cat. b → **cat. d artefacto** (consistente con A54).

El **display S93** (PR mergeado) atenúa+etiqueta estos records en el dashboard, pero
el pipeline los sigue generando en los datos. Este item es el fix opcional para que
el pipeline **no genere** el número.

## Criterio validado (display S93, reusable como base del gate)

Firma del artefacto = **campo amplio + radiancia DISPERSA**, opuesto a un foco real:
```
n_pixels ≥ 100 ∧ VRP/px < 1.0 ∧ t_max < 278.15 K (5 °C) ∧ VRP ≥ 50
```
- Usa `t_max` + geometría del cluster, **NUNCA `t_bg`** (el gate `t_bg<260K` fue
  refutado S86: mata la erupción Lascar 02-17 bajo nube fría). El Lascar real tiene
  `t_max +15/+45 °C`, 2–9 px → NO cae en el criterio. Validado 45 vols: **0 reales**.
- Fuente: `experiments/_s93_warmscene/validate_criterion.py` (ALL_VERIFIED, 2 nuevos
  PCC, 4 ya cubiertos por cirrus).

## Proceso OBLIGATORIO si se avanza (NO saltar — A45/A55/A18)

1. **Brainstorming + design doc** dedicado (no reusar este sin revisar).
2. **Tag defensivo** `git tag pre-s<NN>-diffuse-gate-integration <sha>` + push (A45).
3. **OK explícito de Nicolás** antes del primer edit a `pipeline/` (A45).
4. **TDD**: test sintético que capture el artefacto PCC 05-05 ANTES del fix.
5. **Decidir punto de inserción**: ¿clasificar/cap en `store.py` (post-cluster) o en la
   selección? NO un gate ciego en path D (A55, anti-patrón gate-intra-radio).
6. **Reproc histórico LOCAL** (no GH Actions, timeout S15) sobre PCC + verificar que
   no se pierde ningún TP en los 11 Tier A (A18: el preview offline NO predice la
   selección real de cluster — reproc real obligatorio).
7. **R2 pixel-level** vs TIF MIROVA (`../mirova-tif-archive`, desde 2026-05-09) para
   confirmar que el record corregido coincide con lo que MIROVA reporta.
8. **Verification-before-completion** + dashboard.

## Riesgo de NO hacerlo
Nulo operacional: el display ya oculta el número engañoso. El dato crudo queda en
`data/` para provenance/paper. Este item es "datos crudos más limpios", no urgente.
