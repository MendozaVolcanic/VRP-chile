# F-S81-A Fase 1b — Sanity check empírico p95 MODIS

**Sesión**: S83 (2026-05-26). **Estado**: COMPLETA — hallazgo crítico.
**Predecesor**: `docs/F_S81_A_FASE1_DIAGNOSIS.md` (mecanismo) y
`docs/superpowers/specs/2026-05-26-f_s81_a_gate_path_d_intra_radio.md`
(design Opción A original).
**Sucesor**: ajuste Opción A → A-simplificada (gate `inner_radius_km`
sin script p95 empírico).

## Pregunta

Antes de implementar el script `build_mirova_modis_radius.py` propuesto en
el design doc Fase 2 (Opción A), validar empíricamente el método:
`R_mirova_modis(vol) = percentil_95(distancia_alerta_termica_modis)` por
volcán Tier A, con fallback `inner_radius_km` si `n_alertas < 10`.

## Resultado

### CONS (`latest_consolidado.csv`, fetched 2026-05-26)

| Volcán | N ALERTA MODIS | p50 | p95 | max | Otros (RUTINA + FP) |
|---|---:|---:|---:|---:|---:|
| Lascar | **75** | 1.41 km | **2.00 km** | 2.24 km | 415 RUT + 2 FP |
| NevadosDeChillan | 1 | 1.41 | 1.41 | 1.41 | 570 RUT + 2 FP |
| Chaiten | 0 | — | — | — | 633 RUT + 2 FP |
| Copahue | 0 | — | — | — | 566 RUT + 4 FP |
| Isluga | 0 | — | — | — | 466 RUT |
| Lastarria | 0 | — | — | — | 485 RUT + 1 FP |
| Llaima | 0 | — | — | — | 557 RUT + 12 FP |
| PlanchonPeteroa | 0 | — | — | — | 544 RUT |
| PuyehueCordonCaulle | 0 | — | — | — | 597 RUT |
| Tupungatito | 0 | — | — | — | 407 RUT |
| Villarrica | 0 | — | — | — | 568 RUT + 3 FP |

### OCR (`registro_vrp_ocr.csv` fetched fresh 2026-05-26)

Sumas adicionales MODIS-only:
- Lascar: +32 ALERTAs (sin `Distancia_km` poblada por limitación OCR, todas =0)
- Copahue / Llaima / NdC: +1 ALERTA cada uno
- Resto: 0

Universo combinado CONS+OCR para MODIS: **Lascar 107, NdC 2, Copahue/Llaima 1, resto 0**.

## Implicaciones

**El método "p95 empírico ALERTA_TERMICA MODIS" colapsa al fallback
`inner_radius_km` en 10/11 Tier A** (regla `n_alertas ≥ 10` del pre-mortem
del design original). Solo Lascar tendría p95 propio (2.00 km, más
restrictivo que `inner_radius_km`=5 km del KMZ).

**Físicamente coherente**:
- Lascar tiene actividad real frecuente en cráter activo (Lascar V central).
  MIROVA publica ALERTA solo cuando hot spot < 2.2 km del vent → cualquier
  detección Path D MODIS a 8 km es ruido (suelo árido Atacama post-atardecer,
  cirrus alto).
- Los 9 volcanes con 0 ALERTA MODIS son sistemas de actividad débil o
  intermitente (Villarrica lava lake sub-pixel, Chaitén domo enfriado,
  fumarólicos como Copahue/Lastarria). MODIS 1 km es demasiado grosero para
  resolver señal sub-pixel lejos del cráter → MIROVA no publica MODIS far.
- NdC con N=1 ALERTA + 12 FP en Llaima son anecdóticos, ruido estadístico.

**Cross-check con Fase 1 distribución espacial**:
La Fase 1 mostró 89% de FPs MODIS a >10 km del cráter y solo 92 (11%)
dentro de `inner_radius_km`. Eso significa que un **gate puro
`distance ≤ inner_radius_km`** ya cae ~89% del problema, sin necesidad de
script offline ni nuevo campo per-volcán en yaml.

## Decisión preliminar: Opción A → A-simplificada

Reemplazar la Fase 2 propuesta originalmente por una versión más simple:

**A-simplificada**: Path D MODIS solo dispara si
`cluster_distance ≤ inner_radius_km` (campo ya existente en `volcanoes.yaml`,
extraído del KMZ oficial MIROVA). Sin script offline, sin yaml patch,
sin nuevo campo `mirova_modis_max_path_d_km`.

**Caso especial Lascar opcional**: si tras A/B test queda residual de FPs
Path D MODIS entre 2.2 km (max ALERTA) y 5 km (inner_radius_km), considerar
cap específico Lascar a 2.5 km en Fase 2.5.

**Tareas eliminadas** del plan original:
- Script offline `build_mirova_modis_radius.py` (1.5 h)
- Yaml patch `mirova_modis_max_path_d_km` per Tier A (0.5 h)

**Tareas mantenidas**:
1. Tag defensivo (5 min) — A45.
2. Test sintético geométrico TDD (1 h).
3. Gate en `process_modis.py` flag `enable_path_d_intra_radio_gate` (2 h).
4. 2 profiles A/B con `data_subdir` aislado (0.5 h).
5. Workflow GH Actions max-parallel=1 (0.5 h).
6. Audit independiente (2 h).
7. PR si adopción (1 h).

**Total revisado: ~6 h Fase 2 completa** (vs 9 h plan original).

## Impacto esperado A-simplificada

Sobre los 857 FPs MODIS del CSV S81 (`fp_genuine_all.csv`):
- **Caen los 765 `far`** (89%) — fuera de inner_radius_km.
- **Quedan los 92 `summit`** (11%) — dentro de inner_radius_km, requieren
  Fase 2.5 (posible combinación con Opción B `n_pixels ≥ 4` o cap Lascar).

Recall vs ALERTA MIROVA esperado **mantenido**:
- Lascar (75+32 ALERTAs todas <2.5 km): inner=5 km cubre cómodo.
- Resto Tier A (0–2 ALERTAs MODIS históricas): no hay TPs lejanos que
  preservar — el gate no rompe nada porque MIROVA no publica ahí.

## Riesgos pendientes

1. **Lascar gate insuficientemente estricto** (inner=5 km vs p95=2 km):
   posibles FPs Path D MODIS entre 2.2 y 5 km del Lascar. Hay que medir en
   audit Fase 2 si quedan residuales. Si sí → Fase 2.5 cap específico.
2. **Volcanes que activen ALERTA MODIS lejos en el futuro**: si Chaitén
   tiene erupción nueva con flujo a 10 km, el gate inner=5 km la silencia.
   Mitigación: el gate solo aplica a Path D — los Paths A (BT clásico) y B
   (NTI absoluto) siguen disparando sin restricción. Erupción real grande
   pasa por A o B, no requiere D.
3. **NULOs no contemplados**: el CSV tiene tag `NULO` (granule corrupto).
   No afecta el método (filtramos por ALERTA solamente).

## Datos de soporte

- `latest_consolidado.csv` (CONS scraper Mirova-v1, raíz repo, fetched
  hoy 2026-05-26 mediante `git pull`).
- `registro_vrp_ocr.csv` fetched fresh
  (`raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/monitoreo_satelital/`).
- `experiments/_s82_intra_radio/fase1_1_modis_classified.csv` (857 FPs
  Fase 1 con `distance_class`).

## Pendiente confirmación Nicolás

Antes de seguir con tag defensivo + implementación:

- ¿Vamos con **A-simplificada** (gate `inner_radius_km`, sin script p95)?
- ¿Caso especial **Lascar cap 2.5 km** en Fase 2 inicial, o esperar a
  Fase 2.5 si el audit lo amerita?
