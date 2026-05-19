# S63 Paralelo Findings — investigación mientras corre PCC A/B

**Fecha**: 2026-05-19 (S63 paralelo).

## 1. Tupungatito mecanismo profundo (gap 10× sin kernel-bg)

Top 10 outliers Tupungatito CONS+OCR window 80d:

| Patrón observado | Valor |
|---|---|
| `src=test1` (10/10) | 100% Test 1 path |
| BT_mean pixels | **256-267 K** (-6 a -17°C) |
| pc_dist al vent | 0.93-1.41 km (cerca cráter) |
| n_pix cluster | 20-95 |
| MIROVA VRP | 0.03-0.22 MW |
| Ours pc.vrp | 1.3-7.98 MW |
| Ratio | 36-235× |

**Mecanismo identificado**:
- Tupungatito = glaciar permanente + nieve alta montaña
- Ring background extremo frío (254-267K)
- Pixels cráter modestamente más calientes (266K mean vs 255K bg)
- Test 1 integrated-ROI suma muchos pixels con ΔL pequeño per pixel
- **Kernel-bg NO cura**: vecinos directos hot pixel también son glaciar → L_bg local ≈ L_bg ring → ΔL invariable

**Centroides spread**: 11 km N-S alrededor del vent. Actividad dispersa flanco glaciar.

### Fixes candidatos Tupungatito S64+

1. **Threshold pixel-level BT mínimo absoluto** (e.g. BT > 270K para contar pixel anómalo)
   - Excluye pixels glaciar puros (< 270K)
   - Mantiene pixels cráter real (>270K)
2. **k_sigma más estricto** para Test 1 (3.0 → 5.0 summit, Coppola 2016a Tabla 1)
3. **min_n_pixels** mayor para cluster Test 1
4. **inner_radius_km** menor (de 7 a 3) — si centroides spread es artefacto, no actividad real

Requiere experimentación A/B controlada S64+.

## 2. MODIS Villarrica final_hotspot vs pc.centroid

Caso 2026-05-17 06:55 MODIS_AQUA detallado:
- Pixel #1 más caliente (9.17 MW): 5.64 km E del cráter
- Pixels #2-5 (~9 MW): 20-22 km N (lago Villarrica)
- **pc.centroid** (cluster summit correcto): 0.95 km del cráter (24.79 MW)
- **final_hotspot** asignado al pixel más caliente individual: 5.64 km E
- `distance_class=far` → dashboard excluye

**Patrón generalizado**: 21/21 MODIS Villarrica últimos 10 días tienen `distance_class=far` excepto 2.

**Consistencia con MIROVA**: MIROVA NO publica MODIS Villarrica frecuentemente (1 FP MODIS histórico). Excluir MODIS Villarrica del summit es CONSISTENTE con clon literal MIROVA NRT.

### Fix candidato S64+

`final_hotspot_lat/lon/dist_km` debería asignarse al pixel más caliente
**dentro del cluster summit seleccionado por vent_anchored**, no al pixel
más caliente individual de la escena. Eso haría que `distance_class=summit`
cuando el cluster está cerca del cráter, aunque haya pixels más calientes
lejanos en otras partes de la escena.

Implementación: `pipeline/process_modis.py` función que asigna final_hotspot
debería filtrar por cluster summit primero.

Decision: **NO implementar S63** — esperar Chaiten/PCC/Tupungatito S64+
investigación combinada.

## 3. PCC pre-audit ready

`experiments/113_s63_audit_pcc.py` listo. Baseline LEGACY:
- 97 ALERTAS, recall 89/97 (92%), ratio mediano **3.64×** (mezclado pre/post
  intento inner=7 S62 revertido).

Cuando A/B PCC (run 26115708153) complete, ejecutar script → adopción
condicional similar a Chaiten.

Predicción extrapolación: PCC ΔT 11.2K (régimen Muy Bajo igual Villarrica/
Lastarria/Chaiten) → fix kernel-bg debería curar a ~1.5-2.5×.

## Estado S63 al cierre paralelo

- ✅ Chaiten adoptado (1.07× → 2.23×)
- ⏳ PCC A/B corriendo (run 26115708153, ETA ~3h)
- ✅ Tupungatito mecanismo identificado (BT pixels glaciar + Test 1 over-detection)
- ✅ MODIS Villarrica patrón documentado (correcto pero potencial fix)
- ✅ Pages-deploy fix permanente (PR #87)
- ✅ 11 PRs S62+S63 mergeados a main
- ✅ 6 vols Tier A calibrados (Lascar, Isluga, Villarrica, PP, Lastarria, Chaiten)
