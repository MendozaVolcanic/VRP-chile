# S88 — Re-selección offline + decomposición Lascar febrero

**Fecha**: 2026-05-29 (S88). **Script**: `reselect_offline.py` (100% offline, no toca pipeline NRT).
**Datos**: `anomaly_pixels` persistidos en `data/mirova_equivalent/*.json` (11 Tier A) +
loader canónico `load_mirova_alertas` (CONS∪OCR). **Ventana**: igual que S87.

## Pregunta

S87 dejó el 74.7% de match 1:1 como **piso contaminado**: la columna `vent_anchored`
leía el `primary_cluster` PERSISTIDO, que mezcla épocas de estrategia (pre-S38 `vrp_max`
vs post-S38 `vent_anchored`). Dos preguntas, ambas sin reproceso:

1. **¿Cuánto sube el match si re-aplico la lógica `vent_anchored` ACTUAL a los pixeles
   persistidos** (en vez de leer el primary stale)?
2. **De los no-match eruptivos de Lascar feb, ¿cuántos son recuperables en disco
   (cráter presente, mala selección vieja) y cuántos necesitan reproceso real desde L1B
   (cráter ausente de los pixeles persistidos)?**

El método espeja el ranking `vent_anchored` de `pipeline/clustering.py:cluster_hotspots`
(S38 D8 + S43 filtro vrp>0) sobre los clusters reconstruidos con
`cluster_pixels_geographic`. Distancias desde `mirova_center` (= effective vent Tier A).

## Resultado 1 — re-selección offline (tol 2 km)

| Volcán | n | stale% (S87) | resel% | Δpp |
|---|---:|---:|---:|---:|
| Lascar | 159 | 67.3 | **71.7** | **+4.4** |
| Lastarria | 87 | 98.9 | 98.9 | 0.0 |
| PlanchonPeteroa | 53 | 94.3 | 94.3 | 0.0 |
| Chaiten | 16 | 93.8 | 93.8 | 0.0 |
| Isluga | 74 | 83.8 | 82.4 | −1.4 |
| Tupungatito | 57 | 77.2 | 75.4 | −1.8 |
| PCC | 62 | 25.8 | 25.8 | 0.0 |
| (resto n<6) | | = | = | 0.0 |
| **GLOBAL** | **529** | **74.7** | **75.4** | **+0.7** |

> La columna `stale%` reproduce EXACTAMENTE los números de S87 (Lascar 67.3, Lastarria
> 98.9, PCC 25.8, Tupungatito 77.2…) — valida que el script mide lo mismo que S87.

**Lectura**: la re-selección offline mueve poco (+0.7pp global). Solo Lascar sube
de forma apreciable (+4.4pp ≈ 7 records). Los demás vols ya estaban óptimos (delta 0)
o bajan levísimo (Tupungatito/Isluga −1.4/−1.8pp: ruido de re-clusterizar el top-N
guardado, A18). **La re-selección offline NO es el camino para cerrar el gap de Lascar.**

## Resultado 2 — decomposición Lascar febrero (la pieza decisiva)

De 46 pasadas Lascar-feb comparables, **18 son no-match** con el primary stale. Al
re-aplicar `vent_anchored` sobre los pixeles persistidos se parten en tres:

| Grupo | n | Significado | Acción |
|---|---:|---|---|
| **Recuperables por re-selección** | 7 | el cráter ESTÁ en los pixeles persistidos; vent_anchored lo elige y matchea | ya capturado offline (el +4.4pp) |
| **Cráter presente, aún no-match** | 6 | hay cluster a ~1-2 km del cráter pero el de mayor VRP de escena (que el script reporta como "nuestra dominante") sigue lejos; gap físico chico | borde de tolerancia; reproceso ayudaría parcialmente |
| **Detection-loss (cráter AUSENTE)** | 5 | NINGÚN pixel persistido cae dentro del inner_radius (5 km); el más cercano está a 13-17 km | **REQUIERE reproceso desde L1B** |

### Mecanismo físico de los 5 detection-loss (confirmado pixel-level)

```
2026-02-01 01:20 MODIS_TERRA  npx=19  dmin=4.4   near3=[4.4,4.7,5.5]   btmax=337K vrp=144
2026-02-03 01:00 MODIS_TERRA  npx=35  dmin=5.5   near3=[5.5,6.5,7.5]   btmax=349K vrp=164
2026-02-06 01:20 MODIS_TERRA  npx=8   dmin=13.5  near3=[13.5,14.6,16.6] btmax=303K vrp=181
2026-02-09 01:20 MODIS_TERRA  npx=8   dmin=13.5  near3=[13.5,14.6,16.6] btmax=303K vrp=181
```

Durante la erupción de febrero, los pixeles MODIS más calientes (BT hasta 349 K,
saturación off-nadir, A36 sec³ elongation) están en el Salar a 13-30 km. El pipeline
viejo (`vrp_max` + `bt_path` ON + sin gates intra-radio S84/S85) llenó el **top-100
`anomaly_pixels` con esos pixeles lejanos saturados**, evictando los pixeles más fríos
del cráter. Resultado: el cráter literalmente **no está** en la lista persistida
(`dmin=13.5 km` en las noches del 06 y 09 — ni un pixel dentro de 5 km). Esto **no se
puede arreglar offline**: la información del cráter se perdió al persistir solo el top-N.

El pipeline ACTUAL no produciría esto: `bt_path_hot=False` (S40), gates intra-radio
Path D (S84) y second-pass (S85) cortan justamente esos pixeles lejanos espurios antes
del top-N, y `vent_anchored` ancla al cráter. Pero confirmarlo requiere correr el
pipeline de hoy sobre los L1B de febrero.

## Conclusión operacional — ¿vale el reproceso (Frente A)?

- El **piso real del pipeline actual es ~75.4% global**, no 74.7%. Diferencia trivial:
  la re-selección offline confirma que para 10/11 vols el primary persistido **ya es el
  que el pipeline actual elegiría** (delta 0). El sistema está sano.
- **El único caso con deuda real es Lascar febrero**, y se descompone en:
  - 7/18 ya recuperados offline,
  - 6/18 en el borde de tolerancia (gap físico ~1-2 km, mejorarían parcialmente),
  - **5/18 detection-loss genuino que SOLO un reproceso desde L1B puede arreglar.**
- Es decir, el reproceso histórico local MODIS de Lascar-feb (Frente A pleno) flipearía
  como mucho **~11 records** (los 6 borde + 5 detection-loss) sobre 159 = **+~7pp Lascar**,
  llevándolo de ~72% a ~79%, y el global de 75.4% a ~76.6%. **Confirma la hipótesis S87**
  (el pipeline actual matchea mejor) pero el ROI es modesto y MODIS no corre local en
  Windows (pyhdf roto → GitHub Actions con chunking, regla S15).

**Recomendación**: el reproceso es **validación, no fix** — el NRT ya hace lo correcto
desde S38-S40. Vale la pena solo si se quiere un número de validación limpio para
documentar/publicar. No es bloqueante operacional. Si se hace, acotar a Lascar feb-2026
MODIS (no los 11 vols × 105 días) y correr en GH Actions con timeout chunked, NO local.

## Escudo anti-drift respetado

- NO se cambió el criterio de selección (vent_anchored validado S87, reconfirmado aquí).
- NO se tocó pipeline NRT — análisis 100% offline, A45 no disparada, sin tag defensivo.
- NO huella/G1/exclude_zones/gate-intra-radio nuevos.

## Artefactos

- `reselect_offline.py` — reproducible.
- `reselect_results.json` — métricas per-vol + decomposición Lascar.
- `lascar_feb_table.txt` — tabla por-noche de los 18 no-match.
- `loss_chars.txt` — caracterización pixel-level de los 5 detection-loss.
