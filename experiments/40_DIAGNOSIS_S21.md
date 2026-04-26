# Diagnóstico Fase 1 — D6 reformulado a H_S21_9 (Task 8 final)

> Output del experimento 40 + cross-análisis con experiments 38 (forense) y 39
> (centroide fumarola). Decide cuál es la causa raíz del cuello Tupungatito y qué
> camino tomar en Fase 2.

## Datos de entrada

| Vol | Refs MIROVA (latest.php) | TP | T4 | Recall summit |
|---|---:|---:|---:|---:|
| Tupungatito | 35 | 20 | 12 | 0.571 |
| Lascar | 79 | 58 | 2 | 0.734 |
| Chaitén | 4 | 4 | 0 | 1.000 |

## Análisis distribución `n_anomalous_pixels` por clase

| Vol | Clase | n records | n_anom mediana | n_anom mean | Interpretación |
|---|---|---:|---:|---:|---|
| Tupungatito | TP | 20 | **0** | 207 | TP llegan vía Regla D vent-path (vrp_vent>0, eruption-path vacío) |
| Tupungatito | T4 | 12 | **372** | 353 | Eruption-path SÍ detecta muchos pixels, pero NINGUNO en summit |
| Lascar | TP | 58 | 2 | 870 | TP mixto vent + eruption |
| Lascar | T4 | 2 | 11 | — | Casos raros, muestra chica |

**Inferencia clave** (Tupungatito): los TP vienen de **vent-path** (n_anom mediana=0
significa eruption-path vacío). Los T4 vienen de **eruption-path con pixels far**
pero **vent-path no detectó** el cráter en esas pasadas.

## Análisis `diag_sigma_bg_k` (std_bg global)

**Bloqueador detectado** (H_S21_8): `process_viirs.py` no guarda `diag_sigma_bg_k`,
solo `process_modis.py` lo hace. Como refs MIROVA Tupungatito son 100% VIIRS
(H_S21_2), no podemos comparar T4 vs TP directamente para Tupungatito.

Solo Lascar tiene 2 T4 MODIS para comparar: ratio T4/TP=0.87 (T4 ligeramente menor).
Muestra chica e inconclusiva, pero **NO sostiene "background inflado en T4"**.

## Análisis `t_bg_k` (T base, sí guardado en VIIRS)

| Vol | Clase | t_bg mediana (K) | std (K) |
|---|---|---:|---:|
| Tupungatito | TP | 266.94 | 1.96 |
| Tupungatito | T4 | 265.51 | 1.44 |
| Lascar | TP | 266.61 | 2.40 |
| Lascar | T4 | 273.27 | 2.00 |

T4 Tupungatito ~1.4 K más frío que TP. Diferencia chica, podría ser nubes finas
o glaciar más visible. NO suficiente para explicar 12 records perdidos.

## Centroide fumarola (experiments/39)

| Vol | n_pixels (within inner) | Offset vs vent_lat/lon nominal |
|---|---:|---:|
| Tupungatito | 60 | **2.76 km** ⚠️ |
| Lascar | 279 | 0.27 km ✅ ok |
| Chaitén | 281 | 1.08 km |

**Tupungatito**: fumarola activa observada (centroide ponderado VRP) está a 2.76 km
del vent nominal del YAML. Existe `mirova_center_lat/lon` en YAML pero apunta a
otro lugar (offset 4.85 km SE del vent nominal, vs nuestro centroide 2.76 km SW).

## Verificación en código

[process_viirs.py:518](../pipeline/process_viirs.py#L518):
```python
vent_dist = haversine_km(vent_lat, vent_lon, lat, lon)
vent_roi_mask = vent_dist <= vent_radius_km
```

**Vent-path filtra por `vent_lat/vent_lon` nominal**, ignora `mirova_center`. Si
la fumarola está a 2.76 km y `vent_radius_km=5`, técnicamente la incluye, pero
las pasadas donde el pixel principal cae fuera del radio (esquinas, errores
geocodificación VIIRS 375m) la pierden.

Más importante: el `mirova_center_lat/lon` ya existente en YAML Tupungatito
(de S15 fix Planchón-Peteroa) **NO se usa** en vent-path.

## Conclusión

**La hipótesis original D6 (background localizado bajaría threshold y dispararía
ΔT real) probablemente NO resuelve el cuello.** Evidencia:

1. T4 tiene `n_anom_median=372` → eruption-path SÍ está detectando, threshold no
   es la barrera que pensamos.
2. TP tiene `n_anom_median=0` → llegan por vent-path Regla D (S20). El vent-path
   funciona en LAS pasadas donde captura el cráter.
3. Lascar T4 sigma_bg ratio 0.87 → no hay background inflado (muestra chica pero
   apunta a refutar D6).
4. Centroide observado a 2.76 km del vent nominal → mismatch geometrico real.

**Causa raíz reformulada (H_S21_9)**: vent-path Tupungatito a veces NO captura
el cráter porque el `vent_lat/lon` nominal está descentrado de la fumarola
activa real (~2.76 km offset SW). Las pasadas T4 son las pasadas donde el
centro detectado por VIIRS cae fuera del `vent_radius_km=5` desde el nominal.

## Caminos para Fase 2 (decisión informada)

### Opción E (recomendada — más barata)
**Cambiar vent-path en `process_viirs.py` para usar `mirova_center_lat/lon`
cuando exista, fallback a `vent_lat/lon`.**

- Costo: ~5-10 líneas + tests TDD. NO requiere reproceso (NRT cron lo arregla
  gradualmente; reproceso opcional para histórico).
- Pre-requisito: validar con experiments/39 que `mirova_center` (o el centroide
  observado nuestro) sea correcto para los 11 Tier A. Para Tupungatito, el YAML
  existente -33.4269,-69.8004 NO es el centroide observado nuestro -33.412,
  -69.839 — discrepancia 1.7 km. Decidir cuál usar.

### Opción A (D6 original)
Implementar `std_bg_summit` ROI1 5×5 km local. **Probablemente NO resuelve el
cuello** según análisis arriba. Costo grande (reproceso 7 h, schema change,
TDD complejo). Diferir hasta verificar que Opción E no alcanza.

### Opción E + A combinadas
Opción E primero (rápido). Si Tupungatito recall sube a >0.85, listo. Si no,
agregar D6 sobre el centro corregido.

### Opción B (cambiar vent_radius_km)
Ampliar `vent_radius_km` Tupungatito de 5 a 10 km. Más simple aún, pero
introduciría más FPs porque captura altiplano lateral. NO recomendada.

## Próximo paso S22

Implementar **Opción E** con `superpowers:writing-plans` + `test-driven-development`
sobre `pipeline/process_viirs.py`. Validar con re-corrida de experiments/38 sobre
los 3 Tier A — esperar Tupungatito recall ~0.85+.
