# F52 — Villarrica sobre-estimación VRP root cause (S77)

**Fecha**: 2026-05-24 · **Worktree**: `VRP-Chile-s77-f52-villarrica` · **Branch**: `claude/s77-f52-villarrica-rootcause` · **Modo**: read-only audit + doc.

## Resumen ejecutivo

- **Severidad**: alta. Ratio mediano ours/MIROVA = **10.91×** sobre 6 records con match temporal MIROVA NRT en ventana 7d (2026-05-17 a 2026-05-24). Sobre-estimación sistemática.
- **Volumen de sobre-detección**: 31 records nuestros summit/pc>0, solo 6 con match MIROVA NRT (±60 min) → **25 falsos positivos / 31 = 81%**.
- **Hipótesis confirmada**: **H4 (clustering vent-anchored mal calibrado)** dominante, con componente secundario **H3 (inner_radius_km=5 km demasiado generoso para Villarrica)**. H1 (lago) y H2 (coords) **refutadas**.
- **Fenómeno físico**: el flanco NW del cráter (rumbo 280-360° desde vent) contiene el glaciar Pichillancahue + fumarolas laterales. Los pixels VIIRS 375m integran roca caliente y nieve. Clusters de 16-86 pixels capturan parche caliente del flanco con t_max 284-290 K, t_bg 269-283 K, ΔT 5-11 K. MIROVA NRT lo reporta como ~0.2-0.55 MW (señal real, débil); nuestro pipeline lo infla a 3-20 MW por sobre-acumulación de pixels marginales.

## Veredicto de hipótesis

| Hipótesis | Resultado | Evidencia |
|---|---|---|
| **H1 — Lago Villarrica contamina** | ❌ Refutada | Lago centroide a 21.1 km del vent (bearing 322°). 0/25 unmatched dentro del bbox del lago. 0/25 dentro del `exclude_zone` (r=7 km) ya configurado en yaml. Clusters problemáticos caen a 0.5-1.7 km del vent, sobre flanco glaciar, no sobre agua. |
| **H2 — Coords vent obsoletas** | ❌ Refutada | `volcanoes.yaml`: `vent_lat=-39.420227, vent_lon=-71.939876` a **117 m** de coords conocidas Rinconada lava lake (-39.4197, -71.9387). Coordenadas correctas. |
| **H3 — inner_radius_km=5 generoso** | ✅ Parcial | Distribución unmatched: 4 a <1 km, 20 a 1-3 km, 1 a 3-5 km. Reducir a 3 km descartaría el ~50% lateral pero no la totalidad. Es síntoma del bug real (clustering), no causa raíz. |
| **H4 — Clustering vent-anchored mal calibrado** | ✅ Confirmada | Clusters de **16-86 pixels VIIRS 375m** con t_max apenas 284-290 K (ΔT 5-11 K sobre t_bg 269-283 K). 18/25 unmatched (72%) con bearing 280-360° (NW). Incluso los 5/6 matched caen en mismo bucket NW con ratio 4.8-16.3×. **Solo 1 record (de 31) cae a 0.17 km del vent con ratio sano 1.97×**. El clustering está agregando pixels glaciares marginales que MIROVA descarta. |

## Datos

- **Total records ventana (S77)**: 1262 históricos · 85 con `datetime_utc >= 2026-05-17` · **31 summit con pc.vrp_mw>0 y pc.dist<=5 km**.
- **MIROVA NRT refs Villarrica ventana**: 5 timestamps (todos VIIRS, VRP_MW 0.21-0.55).
- **Matched (±60 min, mismo sensor bucket)**: 6 · **Unmatched**: 25.
- **Sensores afectados**: 100% VIIRS (NOAA20/21/SNPP, ambas resoluciones 375 m e I/M-band 750 m). MODIS no aparece en ventana.
- **Bearing analysis vent → cluster**:
  - Hacia NW (280-360°): **18/25** unmatched + **5/6** matched.
  - Hacia E-SE (20-110°): 4/25.
  - Hacia S-SW (110-280°): 3/25.
  - Bearing vent → lago Villarrica: 322° (coincide direccionalmente pero a 21 km, el lago NO está siendo detectado).

### Tabla resumen MATCHED (6 records)

| datetime_utc | sensor | brg° | d_vent km | t_bg K | t_max K | pc.vrp MW | MIROVA MW | ratio |
|---|---|---|---|---|---|---|---|---|
| 2026-05-17 04:54 | VIIRS_NOAA21 | 340.3 | 0.87 | 275.4 | 283.8 | 3.34 | 0.21 | **15.89** |
| 2026-05-17 05:24 | VIIRS_SNPP | 318.3 | 1.13 | 275.3 | 284.8 | 3.43 | 0.21 | **16.33** |
| 2026-05-17 05:48 | VIIRS_NOAA20 | 275.7 | 0.17 | 275.1 | 285.0 | 0.41 | 0.21 | 1.97 |
| 2026-05-17 06:36 | VIIRS_NOAA21 | 307.8 | 1.33 | 275.2 | 283.7 | 2.23 | 0.21 | 10.60 |
| 2026-05-22 05:00 | VIIRS_NOAA21 | 348.0 | 1.67 | 277.5 | 284.6 | 2.65 | 0.55 | 4.81 |
| 2026-05-22 05:30 | VIIRS_SNPP | 312.9 | 1.20 | 277.5 | 285.0 | 6.17 | 0.55 | 11.22 |

**El único record con ratio sano (1.97) cae a 170 m del vent.** Los 5 con ratio inflado caen a 0.87-1.67 km, en bearing NW.

### Resumen estadístico

| Métrica | MATCHED | UNMATCHED |
|---|---|---|
| n | 6 | 25 |
| mediana pc.vrp_mw | 2.99 | **5.53** |
| mediana pc.n_pixels | 47 | 36 |
| mediana d_vent km | 1.16 | 1.25 |
| mediana t_bg K | 275.4 | 278.4 |
| mediana t_max K | 284.7 | 286.8 |
| mediana σ_bg K | 3.30 | 3.54 |

**Observación clave**: UNMATCHED tiene VRP **mayor** que MATCHED (5.53 vs 2.99 MW). Los falsos positivos brillan más que los reales — patrón típico de inflación por agregación de pixels marginales.

## Interpretación física

t_max 284-290 K = 11-17 °C sobre fondo de 269-283 K. **No es lava lake** (lava activa Villarrica ~600-900 K en pixels saturados, ~320-360 K post-mezcla en pixel VIIRS 375m). Es **calentamiento diurno tardío del flanco NW** o **fumarolas glaciares dispersas** mezcladas con nieve. El flanco NW (Pichillancahue) tiene mayor exposición geotérmica documentada y glaciar permanente — combinación que crea heterogeneidad térmica que infla σ_bg y permite clusters expansivos.

MIROVA lo trata como background ruidoso (no cuenta esos pixels) o lo agrega bajo umbrales más estrictos que los nuestros. Nosotros lo tratamos como anomalía.

## Fix recomendado (bite-sized)

**Approach mínimo (1 sesión, ~3-4h)**: tighter clustering para Villarrica.

1. **Investigar `pipeline/process_viirs.py` clustering** — cómo se construye `primary_cluster.n_pixels`. Si usa conectividad 8 sin tope, agregar `max_pc_pixels_by_volcano` con default 8-12 para Villarrica (vs MODIS típico 3-5 pixels en un evento real Coppola 2016a).
2. **Per-volcano `inner_radius_km` config**: Villarrica → 2 km (no 5). Cráter de Villarrica tiene ~250 m de diámetro; lava lake Rinconada es puntual; cualquier cluster con centroide a >2 km es flanco glaciar, no actividad summit real.
3. **Test A/B vs profile experimental** `_villarrica_tight_cluster` antes de tocar `mirova_equivalent`. Patrón validado S24+S25.

**Approach defensivo (1 día)**: agregar diagnostic `pc_max_pixel_bt_k` y `pc_pixel_count_above_t_bg_plus_15K` al record. Pixels reales de lava lake deben tener al menos algunos >300K. Si todos los pixels del cluster son <290K, marcar `is_likely_glacial_noise: true` en VIIRS Villarrica.

**Tag defensivo obligatorio** antes de cualquier fix: `pre-s77-f52-villarrica-fix` (regla A38).

## Artefactos generados

- `experiments/146_f52_villarrica/audit.py` — script reproducible read-only.
- `experiments/146_f52_villarrica/audit_result.json` — todos los matched/unmatched serializados con métricas espaciales y térmicas.

## Referencias cruzadas

- F46 (S?): patrón cirrus t_bg<270K — descartado parcial acá (sólo 3/25 unmatched con t_bg<270).
- A8 verificar data fresca antes de asumir problema — confirmado: bug actual S77 con data 2026-05-17 a 2026-05-24, no stale.
- Coppola 2016a SP 426.5: clusters típicos en lava lake activos son pequeños (3-8 pixels MODIS, ~10-25 VIIRS 375m). Nuestros 36-47 pixels mediana son señal de over-clustering.
