# S30 Fix preparado — primary_cluster coherence cuando final_source=test1

## Bug

Cuando `final_hotspot_source=test1`, el campo `primary_cluster` sigue
apuntando al cluster geográfico mayor del granule (no al cluster Test 1
cercano al cráter). El delta report usa `primary_cluster.vrp_mw` como
métrica MIROVA-equiv, lo que produce ratio sobre-estima 6-14× en
Lastarria/PCC/Chaitén.

## Casos diagnosticados (data S29 actual)

| Volcán | Pasada | MIROVA VRP | Nuestro primary_cluster.vrp_mw | Ratio | final_src |
|---|---|---:|---:|---:|---|
| PCC | 2026-02-13 06:30 VIIRS375 | 0.02 | 6.006 (cluster lacolito 14px @16km) | 300× | test1 |
| PCC | 2026-02-10 05:42 VIIRS375 | 0.20 | 39.629 (cluster lacolito 59px) | 198× | eruption (summit @19km) |
| PCC | 2026-02-06 05:18 VIIRS750 | 0.59 | 15.141 (cluster lacolito 24px) | 118× | test1 |

En PCC el "cluster mayor" es el lacolito Cordón Caulle a 15-16 km del
vent registrado. Test 1 detecta el cráter pequeño cerca del vent (0.5 km),
pero el primary_cluster geográfico se queda con el lacolito.

## Fix propuesto

En `pipeline/process_viirs.py` y `process_modis.py`, después del bloque
"VRP recompute" (S26 D / S30), si `final_hotspot_source == "test1"`:

```python
# S30+: cuando Test 1 gana, primary_cluster debe representar lo que
# MIROVA reporta (cluster del cráter), no el cluster geográfico mayor.
if final_hotspot_source == "test1" and test1_n_contrib > 0:
    # Construir cluster sintético desde pixels Test 1
    primary_cluster = {
        "n_pixels": test1_n_contrib,
        "vrp_mw": round(vrp_mw if final_hotspot_source == "test1"
                        else vrp_mir_mw_test1_only, 3),
        "centroid_lat": round(test1_centroid_lat, 5),
        "centroid_lon": round(test1_centroid_lon, 5),
        "centroid_dist_km": round(test1_hotspot_dist_km, 3),
    }
```

Esto reemplaza `primary_cluster` con los datos del cluster Test 1 cuando
ese gana la cascada, garantizando coherencia entre `final_hotspot_*` y
`primary_cluster.*`.

## Aplicar

Esperar que termine reproc Lascar S30 (run 25238134425) primero para no
contaminar. Después aplicar fix + reproc combinado.

## Pasa las 3 preguntas (docs/MISSION.md)

1. **¿Está en papers MIROVA core?** Coppola 2015 Eq.7 Wooster aplicado al
   cluster del cráter (no al cluster lejano). MIROVA reporta UN VRP por
   pasada/volcán/sensor que corresponde al cluster contiguo del cráter
   cuando hay actividad real. Sí.
2. **¿Cierra divergencia documentada?** Sí — paridad magnitud
   (target 0.5-2.0×, actual 6-14×).
3. **¿Alineación interna?** Sí — coherencia `final_hotspot_source=test1`
   con `primary_cluster` (no contradictorio).

3/3 PASS.

## Predicción del impacto

- PCC ratio mediano: 12.0 → ~1.0 (eliminar contaminación lacolito).
- Chaitén ratio mediano: 14.5 → ~1.5.
- Lastarria ratio mediano: 6.3 → ~1.0 (TPs Test 1 actualmente sumando
  cluster mayor en otra parte).
- Recall: sin cambio (final_hotspot_source ya correcto, solo cambia el
  número de magnitud reportado).
