# H8 (S35) — Filtro distance pixel-por-pixel en store.append_record

**Status**: design draft 2026-05-10
**Scope**: `pipeline/store.py` líneas 105-134
**Driver**: bug detectado en R2 Puyehue lacolito 05:42; reach 13.7% de records Tier A en 30d

---

## Problema (síntesis)

`store.py` línea 119 evalúa el filtro de distancia sobre `record["hotspot_dist_km"]`
— que es la distancia al **pixel individual más caliente**. Cuando ese pixel está
fuera del `radius_km` del volcán (típico: incendio agrícola, foco geotermal lejano),
descarta `anomaly_pixels` ENTERA → pierde el cluster summit real.

**Reach cuantificado** (últimos 30d, 11 Tier A):
- 426 records con `discarded_reason: eruption_hotspot_too_far`
- 13.7% del total de records
- 20 ALERTA_TERMICA de MIROVA confirmadas como pérdidas (38-84 pixels lacolito/cráter
  descartados por 1-2 pixels lejanos)

**Antigüedad**: introducido S12 (commit `7241584`, 2026-04-05).

---

## Tres preguntas vinculantes (MISSION.md)

1. **¿Está documentado en papers MIROVA core?**
   SÍ. Coppola 2016a SP426.5 reporta clusters como entidades individuales con su
   propia dist y VRP. MIROVA NO descarta clusters far por presencia de cluster
   más caliente. Cierre S33+ confirmó empíricamente: MIROVA web reporta
   `Distance Last Year` con cientos de puntos grises (>5km) junto a rojos (<5km).
2. **¿Cierra una divergencia documentada?**
   SÍ. D5 magnitud (re-abierto S33). El bug actual contribuye al ratio mediano
   2.53× actual: clusters reales perdidos sesgan el cálculo.
3. **¿Es alineación interna no-metodológica?**
   SÍ adicionalmente. Es alineación arquitectural sin cambio de paper.

**Conclusión**: las 3 son SÍ → autorizado a implementar.

---

## Tres hipótesis evaluadas

### H1 — Cambiar criterio del filtro all-or-nothing
Reemplazar `hotspot_dist_km` por `primary_cluster.centroid_dist_km` en línea 119.

| Pro | Con |
|---|---|
| Cambio mínimo (1 línea) | Si primary_cluster es el cluster lejano (fuego con 20+ pixels), bug persiste |
| Cluster-based como MIROVA | Sigue siendo all-or-nothing |
| Bajo riesgo de regression | No resuelve caso D (cluster cercano débil + cluster lejano grande) |

### H2 — Filtrar pixel-por-pixel (RECOMENDADO)
En `store.append_record`, separar `anomaly_pixels` en `in_range` (dist ≤ radius) vs
`out_of_range` (dist > radius). Recalcular `vrp_mir_mw` y campos de hotspot
desde `in_range`. Preservar `out_of_range` en `discarded_anomaly_pixels`.

| Pro | Con |
|---|---|
| Preserva cluster cercano siempre | Recálculo en store (lógica no debería estar acá) |
| Correcto para todos los casos A, B, C, D | Cambio más invasivo (~30 líneas) |
| Alineado con MIROVA literal (per-pixel) | Necesita migración de schema mínima (sin breaking change) |

### H3 — Multi-cluster output (1 record por cluster)
Cambiar schema: cada record = (sensor, pasada, cluster). MIROVA reportaría 2-3
records por la misma pasada si hay 2-3 clusters distinctos.

| Pro | Con |
|---|---|
| Replica MIROVA literalmente | Schema breaking |
| Permite distance_class por cluster | Cambios masivos en dashboard, audit, agregaciones |
| Más rico para análisis | Scope semanas, no días |

---

## Decisión: **H2** (pixel-level filter en store)

H2 es el mejor balance fix-impacto vs scope. H1 es insuficiente. H3 está fuera de
alcance inmediato (puede hacerse después si se justifica).

### Diseño de la implementación

```python
def _filter_pixels_by_distance(record, max_dist_km):
    """Filtra anomaly_pixels in/out por distance. Recalcula vrp_mir_mw, hotspot.

    Returns: (changed: bool, n_kept: int, n_discarded: int)
    """
    pixels = record.get("anomaly_pixels") or []
    if not pixels or max_dist_km is None:
        return False, len(pixels), 0

    in_range = [p for p in pixels if (p.get("dist_km") or 0) <= max_dist_km]
    out_range = [p for p in pixels if (p.get("dist_km") or 0) > max_dist_km]

    if not out_range:
        return False, len(in_range), 0  # nothing changed

    # Hay pixels descartados — recalcular
    record["discarded_anomaly_pixels"] = out_range
    record["anomaly_pixels"] = in_range

    if in_range:
        # Recalcular hotspot desde pixels preservados
        hottest = max(in_range, key=lambda p: p.get("vrp_mw", 0))
        record["hotspot_lat"] = hottest.get("lat")
        record["hotspot_lon"] = hottest.get("lon")
        record["hotspot_dist_km"] = hottest.get("dist_km")
        # Recalcular vrp_mir_mw como suma in_range
        new_vrp = sum(p.get("vrp_mw", 0) for p in in_range)
        record["vrp_mir_mw"] = round(new_vrp, 4)
        # Marcar discard parcial
        record["discarded_reason"] = "partial_eruption_hotspot_too_far"
        record["discarded_n_pixels"] = len(out_range)
    else:
        # Todo fuera de range — comportamiento legacy
        record["hotspot_lat"] = None
        record["hotspot_lon"] = None
        record["hotspot_dist_km"] = None
        record["vrp_mir_mw"] = 0
        record["discarded_reason"] = "eruption_hotspot_too_far"

    return True, len(in_range), len(out_range)
```

Y en `append_record`, reemplazar el bloque línea 119-133 con llamada a esta función.

---

## Estrategia de validación (R1-R8)

- **R1**: Tests sintéticos en `tests/test_store_eruption_filter_bug.py` ya escritos
  (3 tests fallan con código actual). Fix debe hacerlos pasar.
- **R2**: Verificación pixel-level vs MIROVA usando TIFs en `mirova-tif-archive`.
  Caso Puyehue lacolito 05:42 ya identificado.
- **R3**: Audit independiente en `experiments/77_audit_h8.py` (a escribir).
- **R4**: Pre-mortem (escrito abajo).
- **R5**: Este documento es el design doc obligatorio.
- **R6**: Cuestionar si recall sube >30% en A/B.
- **R7**: Tests cubren edge cases A, B, C, D.
- **R8**: Verificar URL pública del dashboard post-merge.

## Pre-mortem (R4)

Señales de alarma que invalidarían H8:

1. **Sub-detección por anomalía cero**: si in_range queda vacío después del filtro
   pero antes había muchos pixels válidos, podríamos perder eventos. **Mitigación**:
   los tests cubren caso B (todo out_of_range debe descartarse correctamente).

2. **Cambio de magnitud agregada**: si `vrp_mir_mw` recalculado da números muy
   distintos a lo que vemos en mirova_equivalent actual, dashboard puede mostrar
   alertas inesperadas. **Mitigación**: A/B reproceso 14d antes de adoptar.

3. **Impacto en `primary_cluster`**: el cluster computado por la pipeline upstream
   (process_*.py) usa TODOS los pixels (incluyendo los out_of_range). Si filtramos
   en store, `primary_cluster.n_pixels` y `primary_cluster.vrp_mw` quedan
   inconsistentes con `anomaly_pixels`. **Mitigación**: marcar `primary_cluster`
   con flag `recomputed_in_store=True` o recalcular el cluster en store si hay
   discard parcial.

4. **Regla D vent-priority**: si `vrp_vent>0`, código actual fuerza `class=summit`.
   Compatible con H8 — vent-path es independiente de eruption-path.

5. **Sanity cap**: si `vrp_mir_mw` recalculado > 50K MW, sanity cap aplica. OK.

## Migración de records existentes

NO hacer migración retroactiva del bug. Los 426 records descartados quedan como
están (con `discarded_anomaly_pixels` poblado). Para análisis histórico, futuras
audits pueden re-procesar usando `discarded_anomaly_pixels` directamente.

## Plan de implementación

1. ✅ Tests sintéticos escritos (`tests/test_store_eruption_filter_bug.py`)
2. ⏳ Implementar `_filter_pixels_by_distance` en `pipeline/store.py`
3. ⏳ Reemplazar bloque línea 119-133 con llamada a la función
4. ⏳ Tests deben pasar (3 fallan actualmente, deben todos pasar)
5. ⏳ Crear perfil A/B `_h8_pixel_filter_enabled.yaml` que activa el fix
6. ⏳ Reproceso 7d Tier A en GitHub Actions con max-parallel=1 por safety
7. ⏳ Comparar A/B contra `mirova_equivalent` baseline
8. ⏳ Si valida con R2 + R6 OK, proponer merge a `mirova_equivalent`
