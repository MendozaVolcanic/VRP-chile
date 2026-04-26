# S23 T21 — JSON inflación Chaitén/Lascar audit

**Fecha**: 2026-04-26 (S23 audit followup)
**Hallazgo audit S22**: Chaitén 8.6 MB y Lascar 22 MB son notablemente más
grandes que Tier A típico (1-3 MB). Investigar si campos pesados innecesarios.

## Causa raíz identificada

```
data/mirova_equivalent/*.json sizes:
  Llaima:                 1.4 MB  (881 records)
  Lastarria:              1.5 MB  (801 records, max 357 px/record)
  PuyehueCordonCaulle:    2.5 MB
  Villarrica:             3.0 MB
  PlanchonPeteroa:        3.9 MB
  Tupungatito:            5.1 MB  (896 records, max 1144 px/record)
  Chaitén:                8.6 MB  (1033 records, max 3845 px/record) ← inflado
  Lascar:                 22 MB   (798 records, max 4111 px/record) ← MUY inflado
```

**Causa**: el campo `anomaly_pixels` guarda lat/lon/dist/bt/vrp **por pixel**.
Records normales tienen 0-5 pixels (~1 KB cada). Outliers tienen 3000-4000
pixels (~100 KB cada) → 1 record outlier = 100× tamaño normal.

Origen físico de outliers:
- Granules con cobertura nubosa heterogénea (sigma_bg inflado por nubes)
- Escenas con escala de gradientes térmicos amplios donde N·σ gating dispara
  miles de pixels falsamente
- Lascar tiene 206 records con pixels (de 798) — distribución bimodal:
  cráter activo dispara 1-5 pixels normales + escenas malas con miles.

## Solución propuesta (NO implementada — diferida S24+)

**Cap top-N anomaly_pixels al guardar** en `pipeline/store.py append_record`:
- Mantener solo los top-N pixels más calientes (sort por bt_k descendente).
- N=100 preserva 99% de información útil (cráter + halo cercano).
- Reduce Lascar 22 MB → ~3-4 MB esperado.
- Pre-condición: validar que ningún consumer del frontend o experiments/
  necesita ALL pixels (probablemente solo top-K usados visualmente).

```python
# Pseudocódigo store.py:
MAX_ANOMALY_PIXELS_STORED = 100  # TOP_N por record
if len(record.get("anomaly_pixels", [])) > MAX_ANOMALY_PIXELS_STORED:
    record["anomaly_pixels_truncated_count"] = len(record["anomaly_pixels"])
    record["anomaly_pixels"] = sorted(
        record["anomaly_pixels"],
        key=lambda p: -float(p.get("bt_k") or 0)
    )[:MAX_ANOMALY_PIXELS_STORED]
```

## Impacto esperado del cap top-100

- Lascar.json: 22 MB → ~3-4 MB (-85%)
- Chaitén.json: 8.6 MB → ~1.5 MB (-83%)
- Tupungatito.json: 5.1 MB → ~2-3 MB
- Resto: sin cambio significativo

## Riesgos/contraindicaciones

1. **Frontend dashboard**: si usa `anomaly_pixels` para mostrar TODOS los
   puntos en mapa, perdería los pixels far. Verificar `frontend/index.html`.
2. **Experiments/forenses futuros**: si necesitan TODA la distribución espacial
   de un evento (e.g., para cluster analysis factor 42), la truncación los
   afectaría.
3. **Reproceso histórico**: aplicar cap al guardar afecta solo nuevos records.
   Records históricos siguen inflados. Para limpieza retroactiva, script de
   migración que toque cada JSON.

## Decisión S23

NO implementar el cap ahora. Razones:
- Bloat es 22 MB (Lascar) — tolerable (GitHub LFS allows hasta 100 MB/file).
- Frontend uso de pixels no auditado → riesgo regresión visual.
- Sin urgencia operacional (no causa fallos NRT ni problemas perf).

Documentado para S24+ si se decide implementar.

## Items derivados S24+

- Validar uso de `anomaly_pixels` en `frontend/index.html` y experiments/.
- Si ningún consumer necesita >100 pixels → implementar cap top-N en store.py.
- Script migración: `scripts/truncate_anomaly_pixels.py` para records históricos.
