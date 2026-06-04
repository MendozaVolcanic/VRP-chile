# S100 — Auditoría de coherencia del dashboard (index.html)

**Fecha**: 2026-06-04. **Método**: extracción del DOM live (Chrome MCP) +
recomputo desde `allData` cargado, cruzando las 4 representaciones del
dashboard operacional (`index.html`): tarjetas, resumen de estado, marcadores
del mapa, tabla NRT. Snapshot: data publicada `updated 2026-06-03 17:33Z`.

> Alcance: SOLO `index.html`. `diario.html` y `mosaico.html` (vistas con copias
> separadas de helpers, S92 L5) NO auditadas todavía — pendiente parte 2.

## ✅ Lo que SÍ conversa (sin discrepancias)

- **Tarjetas ↔ resumen ↔ marcadores del mapa**: coinciden EXACTO en los 11
  volcanes activos. `latestVRP` (resumen/mapa) == `latestDetection.vrp`
  (tarjeta) en los 11; mismo nivel de alerta. Resumen DOM (`0 alto / 0 mod /
  3 bajo / 8 muy bajo / 34 sin datos`) == recomputado.
- **Eje espacial (A61)**: las 11 detecciones de las tarjetas son al cráter
  (summit), dist 0.1–2.5 km dentro del inner. Incluido **Tupungatito a 1.13 km**
  (fix ancla S98 confirmado; antes ~5.9 km en el glaciar).
- **Tabla NRT**: 30 filas, todas con record real en `allData`, dentro de la
  ventana 7 d, orden temporal correcto. La magnitud mostrada usa núcleo F5'
  (VIIRS375) / cluster coherentemente.

## 🔴 Hallazgo 1 — `distance_class` corrupto en records MODIS (PIPELINE, A46/Eje5-S95)

La etiqueta `distance_class` NO concuerda con `primary_cluster.centroid_dist_km`
en 5/30 filas de la tabla (todas MODIS de la pasada ~07:45–07:55Z del 03-jun):

| Volcán | sensor | distance_class | centroide cluster | inner | inconsistencia |
|---|---|---|---|---|---|
| **Villarrica** | MODIS_AQUA | `summit` | **21.73 km** | 5 | summit pero lejísimos |
| Tupungatito | MODIS_AQUA | `far` | 3.70 km | 7 | far pero dentro del inner |
| Chaitén | MODIS_AQUA | `far` | 1.95 km | 5 | far pero cerca |
| Isluga | MODIS_AQUA | `far` | 0.23 km | 5 | far pero al cráter |
| Láscar | MODIS_AQUA | `far` | 0.64 km | 5 | far pero al cráter |

**Causa**: `distance_class` se deriva del *hotspot suelto* (final_hotspot_dist /
hotspot_dist, p.ej. Villarrica 21.7 km, Isluga 23–29 km) mientras el
`primary_cluster` apunta a otro lado. Es el patrón A46 (schema asimétrico hotspot
single vs primary_cluster) + Eje5 S95 (incoherencia distance_class). Estaba en
backlog como "0 pérdida recall" — **esta auditoría muestra que SÍ tiene efecto
visible** (ver Hallazgo 2). Sube prioridad.

Nota física: los casos "far pero al cráter" (Isluga/Láscar) son path-D MODIS sobre
escena fría (t_bg 264–267 K, n_anom 80–104, vrp_mir 61–65 capeado a 5 por D9) —
artefacto de campo difuso (= frente §2 MODIS pendiente). Que NO se muestren
prominentes es correcto, pero por la razón equivocada (etiqueta far accidental).

## 🔴 Hallazgo 2 — la tabla NRT no aplica el gate de distancia (DASHBOARD)

`buildNRTTable` incluye filas solo por `isValidDetection` + cutoff 7 d, SIN el
gate `distance_class==summit && centroid_dist_km<=innerKm` que `mirovaEqVrp`
aplica en tarjetas/mapa/resumen. Resultado: **7/30 filas (23%) muestran VRP que
el resto del dashboard descarta** (las tarjetas dan 0):

- **El más grave**: **Villarrica MODIS 07:50 = 7.545 MW** en la tabla, mientras
  la tarjeta de Villarrica dice 0.202 MW (muy bajo). El "7.5 MW" es un cluster a
  **21.7 km** del cráter (no es el volcán) que pasó por `distance_class=summit`
  mal puesto (Hallazgo 1). Un operador lee "Villarrica 7.5 MW hoy" — falso.
- Otras: Chaitén (0.69, 0.29), Tupungatito (0.23), Isluga (5), Láscar (5) — todas
  MODIS far/capeadas que la tarjeta no cuenta.
- Menor: 1 fila Láscar VIIRS 06:42 con VRP **0.000** en la tabla (record válido
  pero magnitud 0 → fila sin información útil).

## Recomendaciones (NO implementadas — requieren decisión + A45 si tocan pipeline)

1. **Raíz (pipeline, A45 + brainstorming)**: corregir `distance_class` para que
   derive del `primary_cluster` (la representación que el dashboard ya usa para
   magnitud), no del hotspot suelto. Alinea las 4 vistas de un saque. Es A46/Eje5
   reabierto con evidencia de impacto display. Espejo del fix de ancla S98.
2. **Parche (display, frontend)**: que `buildNRTTable` aplique el mismo gate que
   `mirovaEqVrp` (incluir solo `mirovaEqVrpDisplay(r,inner,includeFar) > 0`), o
   marcar las filas far como tales. Quita el "Villarrica 7.5 MW" fantasma.
3. Filtrar de la tabla las filas con VRP mostrado == 0.

## 🔴 Hallazgo 3 (parte 2) — magnitud por DEFECTO divergente entre las 3 vistas (DASHBOARD, S92 L5)

Verificado en runtime (Chrome) + código. El default del toggle Cluster/Núcleo F5'
NO es el mismo en las 3 vistas:

| Vista | default magnitud | código | toggle storage key |
|---|---|---|---|
| `index.html` | **Núcleo F5'** | `persistedFlag("vrp_f5_core", true)` | `vrp_f5_core` |
| `diario.html` | **Cluster** | `let USE_F5_CORE = false` (L251) | `diario_f5_core` (sessionStorage) |
| `mosaico.html` | **Cluster** | `let USE_F5_CORE = false` (L258) | `mosaico_f5_core` (sessionStorage) |

**Efecto**: por defecto el MISMO volcán muestra magnitud distinta según la vista.
Ej. Tupungatito 03-jun: **0.227 MW (núcleo) en el dashboard** vs **~1.267 MW
(cluster) en la vista diaria**. Villarrica/Llaima/PCC ídem. El operador ve un
número en index y otro en diario/mosaico.

**Causa**: S97 puso Núcleo F5' como default SOLO en `index.html`; `diario` y
`mosaico` quedaron en Cluster. Es la lección S92 L5 (un cambio de display debe
replicarse en las 3 vistas) incumplida. Además el toggle usa 3 keys de storage
distintas → cambiarlo en una vista no se propaga a las otras.

Verificado (A62): la lógica del toggle de `diario` (L596, guarda el valor opuesto
antes del reload) NO es bug — funciona. El único problema es el default.

`mirovaEqVrpDisplay` existe solo en `index.html`; `diario`/`mosaico` resuelven
core-vs-cluster inline (`USE_F5_CORE ? core : cluster`). Funcionalmente equivalente
salvo por el default divergente.

**Fix (display, frontend)**: unificar el default a `true` (Núcleo F5') en las 3
vistas — `diario.html:251` y `mosaico.html:258` a `true` (idealmente vía un helper
`persistedFlag` compartido con la misma key para que el toggle sea global). Bajo
riesgo, display-only.

## 🔴 Hallazgo 4 (S100, observación Nicolás "veo MODIS en Chaitén") — MODIS artefacto sistémico no cubierto

Barrido de records MODIS recientes en los 11 Tier A (`_diag` ad-hoc) revela que el
problema MODIS es MUCHO más grande que #1:

1. **`distance_class="far"` está corrupto en CASI TODOS los MODIS** (no ocasional):
   prácticamente cada record MODIS reciente sale "far" con el cluster a <inner del
   cráter ("far pero CERCA"). El fix #2 (gate tabla NRT) en consecuencia oculta casi
   todos los MODIS de la tabla (0 MODIS en el top-30 live) — bien para los artefactos,
   pero es un parche sobre `distance_class` roto, no la cura.

2. **Los MODIS que SÍ pasan como "summit" son campo difuso / cirrus sobre escena
   gélida, y los filtros de artefacto display (S92/S93) NO los atrapan.** Caso Chaitén
   (inner 5 km), 5 MODIS contados como summit en 10 días:
   - 05-29 21:30: vrp_mw **206 MW**, t_bg −3 °C, 41 px → no marcado.
   - 06-03 02:15: **545 px**, t_bg **−48 °C**, vrp 2.5 → no marcado (n_px≥100 ∧ t_max<5°C
     pero vrp<50 → falla el AND del filtro difuso).
   - 06-02 07:15: 102 px, t_bg −16 °C, vrp 5 (cap D9) → no marcado.
   Ninguno es foco real: MODIS 1 km no resuelve el domo de Chaitén en calma (vlow);
   captura el contraste nube/nieve fría que el path D lee como anomalía. Efecto visible:
   **pill "MODIS" engañoso en la tarjeta** + **picos de 50–206 MW en la serie de
   `diario.html`**. (El NIVEL de alerta NO se infla: la tarjeta usa la última detección
   VIIRS, vlow 0.16 — pero el sensor MODIS y los picos del chart sí confunden.)

3. **Es sistémico en los 11**, no solo Chaitén: Villarrica (MODIS far 20–30 km, vrp
   60–185 MW), Llaima (far 13–20 km, hasta 250 MW), NdC (140–280 MW), PCC (campo
   difuso masivo, 180–630 MW, n_px hasta 800), Lascar/Isluga/Tupun/Lastarria/Copahue
   (mayoría far-pero-cerca capeados a 5 MW por D9). Casi todo MODIS reciente en reposo
   es campo difuso/cirrus, no foco.

**Alcance honesto de la auditoría**: la coherencia entre vistas (hallazgos 1-3) cubrió
los 11. La VALIDEZ registro-a-registro (¿real o artefacto?) NO se había hecho; este
barrido (disparado por la observación de Nicolás) la inicia y muestra que el frente
MODIS es grande. NO se arregló nada aquí — entra al frente MODIS (brainstorming + A45).

**Pendiente frente MODIS (ampliado)**: (a) `distance_class` derivar del cluster (#1);
(b) magnitud campo difuso (§2); (c) **ampliar los filtros de artefacto display** para
cubrir estos casos (criterio espacial: campo disperso n_px alto + fondo gélido, sin el
AND restrictivo actual que los deja pasar). Todo MODIS, mismo reproc.

## Resumen ejecutivo (4 hallazgos)
1. **`distance_class` corrupto en MODIS** (pipeline, A46/Eje5-S95): etiqueta
   cráter/lejos no concuerda con el cluster. Raíz de los hallazgos 2. Reabrir con
   A45 (espejo del fix de ancla S98).
2. **Tabla NRT sin gate de distancia** (display): muestra 7/30 filas que las
   tarjetas descartan (Villarrica 7.5 MW fantasma a 21.7 km).
3. **Default de magnitud divergente entre vistas** (display, S92 L5): index=Núcleo,
   diario/mosaico=Cluster → mismo volcán, números distintos. **[FIXEADO PR #335]**
4. **MODIS artefacto sistémico** (pipeline+display): distance_class corrupto en ~todos
   los MODIS + campo difuso/cirrus sobre escena gélida pasa como summit (Chaitén 206 MW,
   545 px −48°C; los 11 afectados). Filtros artefacto display no lo cubren. = frente MODIS.

Estado: #2 y #3 FIXEADOS (PR #335). #1 y #4 = **frente MODIS** pendiente (pipeline +
display, brainstorming + A45 + reproc MODIS, junto con §2 campo difuso). Afecta los 11.
