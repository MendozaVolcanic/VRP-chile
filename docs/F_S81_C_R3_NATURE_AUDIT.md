> ## 🔑 RESOLUCIÓN FINAL S85 (post-investigación cartográfica + audit empírico)
>
> **El gate de supresión "R3 cluster fuera de inner_radius" YA EXISTE
> operacionalmente desde S33** — vive en `frontend/index.html:868-889`
> (función `mirovaEqVrp`) y en `frontend/diario.html`.
>
> Cuando el dashboard renderiza, descarta cualquier record donde
> `pc.centroid_dist_km > inner_radius_km`. Los 155 "R3 violators" detectados
> por el audit S85 son visibles **solo** para audits Python que NO replican
> esa lógica del frontend. Para el usuario operacional (Nicolás vía
> dashboard / SERNAGEOMIN si lo consume) esos R3 nunca fueron visibles.
>
> **Validación empírica adicional**: cruce de las 367 ALERTAs MIROVA Tier
> A (CSV CONS+OCR ventana 45d) vs `inner_radius_km` del KMZ MIROVA por
> volcán da **367/367 (100%) dentro del inner_radius**. Cero excepciones.
> MIROVA aplica el mismo principio uniformemente (intuición Nicolás S85
> confirmada empíricamente).
>
> **Conclusión**: no hay problema R3 operacional a resolver. Las hipótesis
> intermedias (Fase B' second pass como causa, Fase C zonas no-volcánicas
> per-vol, geometría extendida per-vol) son caminos investigados y
> descartados con datos — su valor durable es eliminar espacio de búsqueda
> futuro.
>
> Lo único pendiente con valor real es schema consistency entre JSONs
> persistidos y dashboard. Opciones para S86 (no urgentes):
> - **A** — Enriquecer schema con campo derivado `pc.mirova_publishable`
>   (bool). Frontend sigue igual.
> - **B** — Mover lógica al backend (zero-out store.py). Rompe toggle
>   "incluir lejanas".
> - **C** — Statu quo (audits Python replican `mirovaEqVrp`).
>
> El catálogo cartográfico C.1 (`docs/F_S81_C_1_ZONES_CATALOG.md`) queda
> como referencia futura solo por si querés implementar exclude_zones
> tipo B (Las Máquinas Copahue, etc.) — pero NO es prioritario dado que
> el dashboard ya está limpio.

# Audit Fase C — Naturaleza de R3 violators residuales (S85)
**Profile**: `mirova_equivalent_f_s81_b_prime_2nd_pass_gate_enabled` (post-Fase B' adoptada)
**Ventana**: 2026-04-12 → 2026-05-26
**Total R3**: 155 (MODIS + VIIRS)

## Hipótesis a verificar (Nicolás S85)

> MIROVA prioriza anomalías volcánicas claras (vent-anchored) y
> suprime cuerpos térmicos no-volcánicos (lagos, salares,
> glaciares, fumarolas crónicas) salvo casos extremos como
> incendios grandes.

Si la hipótesis es correcta, esperamos que la mayoría de los
155 R3 caigan en (a) zonas térmicas documentadas en
`volcanoes.yaml exclude_zones` o (b) clusters geográficos
nuevos identificables como features físicas no-volcánicas.

## Distribución global

| Categoría | # R3 | % |
|---|---:|---:|
| En zona DOCUMENTADA (exclude_zones existente) | 0 | 0.0% |
| En cluster geográfico NUEVO (>1 R3 a <3km) | 59 | 38.1% |
| Huérfanos (R3 aislados) | 96 | 61.9% |
| **Total** | **155** | **100%** |

## Por volcán

| Volcán | R3 total | En zona doc | En cluster nuevo | Huérfanos | inner_km |
|---|---:|---:|---:|---:|---:|
| PuyehueCordonCaulle | 2 | 0 | 0 | 2 | 20.0 |
| Villarrica | 5 | 0 | 0 | 5 | 5.0 |
| Lascar | 11 | 0 | 2 | 9 | 5.0 |
| Copahue | 20 | 0 | 8 | 12 | 4.0 |
| NevadosDeChillan | 30 | 0 | 22 | 8 | 5.0 |
| Llaima | 31 | 0 | 18 | 13 | 5.0 |
| Chaiten | 3 | 0 | 0 | 3 | 5.0 |
| PlanchonPeteroa | 14 | 0 | 5 | 9 | 3.0 |
| Lastarria | 13 | 0 | 2 | 11 | 3.0 |
| Isluga | 9 | 0 | 0 | 9 | 5.0 |
| Tupungatito | 17 | 0 | 2 | 15 | 7.0 |

## Clusters geográficos nuevos detectados (candidatos exclude_zones)

Agrupados por proximidad ≤3.0 km. Solo se listan
clusters con ≥2 R3 (huérfanos quedan sin agrupar).

| Volcán | n_R3 | lat | lon | dist_vent | bearing | sensores | rango fechas |
|---|---:|---:|---:|---:|---|---|---|
| Lascar | 2 | -23.3993 | -67.7666 | 4.88 | SW | MODIS,VIIRS | 2026-04-16 → 2026-05-08 |
| Copahue | 2 | -37.8305 | -71.1815 | 2.84 | NE | MODIS | 2026-04-12 → 2026-04-19 |
| Copahue | 2 | -37.8665 | -71.2496 | 5.96 | SW | MODIS,VIIRS | 2026-04-15 → 2026-05-20 |
| Copahue | 2 | -37.8595 | -71.2076 | 2.19 | SW | MODIS | 2026-05-16 → 2026-05-19 |
| Copahue | 2 | -37.7988 | -71.3532 | 16.25 | NW | VIIRS | 2026-05-20 → 2026-05-20 |
| NevadosDeChillan | 11 | -36.8309 | -71.3974 | 4.01 | NW | MODIS | 2026-04-12 → 2026-05-18 |
| NevadosDeChillan | 3 | -36.8094 | -71.4499 | 8.81 | NW | MODIS | 2026-04-27 → 2026-05-11 |
| NevadosDeChillan | 2 | -36.8395 | -71.3201 | 5.7 | NE | VIIRS | 2026-04-15 → 2026-04-15 |
| NevadosDeChillan | 2 | -36.792 | -71.4146 | 8.57 | NW | MODIS | 2026-04-30 → 2026-05-20 |
| NevadosDeChillan | 2 | -36.8523 | -71.4648 | 7.9 | NW | MODIS | 2026-05-13 → 2026-05-14 |
| NevadosDeChillan | 2 | -37.009 | -71.3898 | 16.27 | SW | VIIRS | 2026-05-21 → 2026-05-21 |
| Llaima | 9 | -38.8755 | -71.906 | 25.53 | SW | VIIRS | 2026-05-02 → 2026-05-21 |
| Llaima | 7 | -38.6956 | -71.743 | 1.28 | SW | MODIS | 2026-04-19 → 2026-05-26 |
| Llaima | 2 | -38.7219 | -71.8453 | 10.63 | SW | MODIS | 2026-05-17 → 2026-05-25 |
| PlanchonPeteroa | 3 | -35.0509 | -70.5016 | 21.88 | NE | VIIRS | 2026-04-12 → 2026-04-12 |
| PlanchonPeteroa | 2 | -35.2308 | -70.39 | 16.2 | NE | MODIS,VIIRS | 2026-04-29 → 2026-05-07 |
| Lastarria | 2 | -25.174 | -68.6268 | 12.08 | SW | MODIS,VIIRS | 2026-04-29 → 2026-04-29 |
| Tupungatito | 2 | -33.3907 | -69.823 | 2.38 | NW | MODIS | 2026-05-20 → 2026-05-22 |

**Total clusters nuevos**: 18

## Veredict hipótesis Nicolás S85

- R3 identificados (zona doc + cluster nuevo): **59/155 (38.1%)**
- R3 huérfanos (sin patrón geográfico): **96/155 (61.9%)**

❌ **HIPÓTESIS REFUTADA EMPÍRICAMENTE** (<40% R3 identificables).
Acción: redirigir investigación a otro mecanismo (geometría cluster, single-pixel pixel mode edge cases, etc).

## Próximos pasos sugeridos

1. Para cada cluster nuevo identificado, identificar feature física
   (Google Maps / Sentinel-2 imagery / GVP catálogo del volcán).
2. Agregar exclude_zones documentadas a `volcanoes.yaml`.
3. A/B test gate `enable_r3_zone_suppression` (nuevo flag).
4. Si confirma reducción R3 ≥70% sin pérdida TPs → adoptar S86.

## Refs

- Adopción B': `docs/F_S81_B_PRIME_ADOPTION_S85.md`
- Beyond MIROVA roadmap: `docs/BEYOND_MIROVA_EXTENSIONS.md`
- Detalle JSON: `experiments/_s85_f_s81_c/r3_nature_detail.json`
