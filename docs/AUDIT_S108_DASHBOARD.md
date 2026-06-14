# AUDIT_S108 — Dashboard / frontend (display, mapas, tablas)

**Fecha**: 2026-06-13 (S108). **Pedido Nicolás**: "auditá los dashboard, tablas, mapas;
buscá bugs o si está en display lo que debería estar actualmente."
**Contexto**: post-flip ancla honesta VIIRS750 (PR #416). Verificar que el dashboard
refleja el estado actual y no introduce bugs de display.

## Método (A48 + A61 + A62)
- 2 subagentes Explore sobre el código (`index.html`; `diario.html`+`mosaico.html`).
- Preview real navegador (`vrp-frontend` :8091, BASE_PATH `/`) — carga, consola, DOM, evals.
- Verificación cruzada sobre los JSON de `data/mirova_equivalent/` (no solo el código).
- A62 adversarial: cada "bug" candidato se intentó refutar antes de reportarlo.

## Veredicto: DASHBOARD SANO — 0 bugs. 1 deuda cosmética conocida (P2.3).

| Área | Estado | Evidencia |
|---|---|---|
| Carga / consola | ✅ | `ready=complete`, 0 errores de consola, 46 markers, 2 tablas, 2 charts |
| BASE_PATH / data | ✅ | `/frontend/` → BASE_PATH `/` → fetch `/data/...` OK; data 2026-06-13 servida |
| Posición (flip V750) | ✅ | cascada `final_hotspot_*` con guard `honestAnchor` (index.html:2124-2130, 2155-2162); data al cráter (audit pareado) |
| `distance_class` color | ✅ | lee del JSON, no recalcula (subagente; mirovaEqVrp gate doble) |
| Fechas (tz S89) | ✅ | `parseUtcMs` agrega 'Z' en las 3 vistas (index:1144, diario:346, mosaico:347) |
| `mirovaEqVrp` filtro | ✅ | gate distance_class + centroid_dist, usa `pc.vrp_mw`, cap 50000 (index:941-962) |
| Cirrus/difuso artefactos | ✅ | `isCirrusArtifact`/`isDiffuseFieldArtifact` display-only, replicados en las 3 vistas |
| Coherencia 3 vistas (L5) | ✅ | helpers replicados; diferencias de firma (volcanoName vs innerKm) correctas por diseño |
| Fallback sin primary_cluster | ✅ | de 4711 records-2026 sin pc, solo **2** (Villarrica lava lake real) tienen vrp>0+summit → no contamina |
| dist=0.0 en tabla | ⚠️ P2.3 | celda muestra "0.00" crudo (index.html:2200); el popup del mapa SÍ rotula "Distancia al cráter: 0.00 km" (2170) |

## Falsos positivos descartados (A48/A62)
- **"events-table Sin detecciones para Villarrica"**: NO es bug. El select `hotspot-volcano-filter`
  controla el MAPA de hotspots (index.html:3035), NO la `events-table` (que se puebla por el
  detail-panel, otro disparador). Confusión `.events-table`≠`.nrt-table` ya advertida (CLAUDE.md §A48).
- **"screenshot del preview cuelga"**: NO es bug del dashboard. Los tiles del mapa cargan (24/24);
  el `preview_screenshot` tool cuelga (probablemente canvas Chart.js animando). Contenido auditado
  vía eval + snapshot. El dashboard live (GitHub Pages, con red) renderiza normal.

## Único accionable: deuda P2.3 (cosmética, NO bug)
La celda "Dist (km)" de la tabla de detalle muestra `0.00` para records cuya posición es el
cráter por semántica del Test1 integrado (`final_hotspot_source=test1_roi`, `dist=0.0`). Es el
valor REAL (la posición ES el cráter — D11-bis), no un error. Riesgo: un operador podría leer
"0.00 km" como medición de sensor en vez de "posición = cráter". El popup del mapa ya lo aclara.
Mejora posible (decisión de display de Nicolás): etiqueta "cráter" o `0.0*` + tooltip en la celda.
Solo afecta `index.html` (diario/mosaico no tienen tabla con columna dist). Migración natural del
tooltip P2.3 ya pendiente desde S106.

## Reproducible
- Subagentes: prompts en transcript S108.
- Conteo fallback: `python -c "..."` sobre data/mirova_equivalent (transcript S108).
- Preview: `.claude/launch.json` perfil `vrp-frontend`.
