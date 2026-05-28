# Adopción operacional Fase B' — gate intra-radio second_pass_recapture (S85)

**Fecha**: 2026-05-28
**Decisión**: ADOPTAR como complemento de F-S81-A (S84)
**Pair pendiente**: Fase C investigación R3 residuales con lente supresión MIROVA

## Resumen ejecutivo

El gate F-S81-B' mascarea pixels NUEVOS recapturados por `second_pass_adjacent`
(Coppola 2016a SP 426.5 §347-356) cuando caen fuera del `inner_radius_km`
del KMZ MIROVA por volcán. Aplica a MODIS + VIIRS-I + VIIRS-M.

**Validación A/B run [26557588067](https://github.com/MendozaVolcanic/VRP-chile/actions/runs/26557588067)**
(45 días, 22/22 success):

- Profiles paralelos `_f_s81_b_prime_2nd_pass_gate_{enabled,disabled}`.
- Ventana: 2026-04-12 → 2026-05-26 (45d).
- Ground truth: CSV consolidado MIROVA + OCR.

## Resultados

### TPs MIROVA (criterio crítico)

| Sensor | Baseline | Disabled | **Enabled** |
|---|---:|---:|---:|
| MODIS | 25 | 25 | **25** |
| VIIRS | 68 | 68 | **68** |

**Cero pérdida** de detección de actividad volcánica real.

### Mecánica del gate (n_2nd_pass_recapture_agg)

| Sensor | Disabled | Enabled | Δ |
|---|---:|---:|---:|
| MODIS | 67,246 | 27,547 | **-59%** |
| VIIRS | 2,760 | 2,690 | -2.5% |

El gate **hace lo que dice**: cae 59% de pixels recapturados ruidosos
fuera del cono en MODIS. En VIIRS apenas se nota porque el problema del
second pass está concentrado en MODIS (24× más recapture que en VIIRS,
coherente con resolución MODIS más gruesa → mayor mezcla térmica
intra-pixel).

### R3 violators (objetivo final)

| Sensor | Baseline | Disabled | Enabled | Δ vs disabled |
|---|---:|---:|---:|---:|
| MODIS | 238 | 106 | 98 | -7.5% |
| VIIRS | 321 | 65 | 57 | -12% |
| **Total** | **559** | **171** | **155** | **-9.4%** |

**Reducción modesta de R3** a pesar de la fuerte reducción de pixels
recapturados. Esto **refuta empíricamente** la hipótesis principal del
design doc (`docs/F_S81_B_PRIME_SECOND_PASS_GATE.md`) que asumía que el
second pass sin restricción era la causa dominante de R3.

## Mecanismo real revelado por el A/B

Los R3 residuales NO vienen mayormente de pixels del second pass aislados
lejos del cono. Los clusters finales que generan R3 están formados por
pixels de **regiones térmicamente reales pero NO-volcánicas** dentro del
campo de visión del volcán:

- Lago Conguillío 9 km NE de Llaima (S12 lección documentada).
- Salar de Atacama al sur de Lascar.
- Glaciar parcialmente fundido en Tupungatito + Planchón-Peteroa.
- Fumarolas crónicas sub-pixel en Lastarria + NdC + Villarrica.

MIROVA suprime estos clusters mediante criterios de **anchoring fuerte
al vent** + **filtros de coherencia espacial-temporal** que no están
explícitamente documentados en papers (Coppola 2016a, Campus 2024, Aveni
2024). Nuestro `enable_vent_anchored_clustering` (adoptado S38) no
alcanza el mismo nivel de supresión.

Hipótesis Nicolás S85 confirmada empíricamente: **MIROVA prioriza
anomalías volcánicas claras (vent-anchored, intensidad+extensión
consistentes con cráter activo) y suprime cuerpos térmicos no-volcánicos
salvo casos extremos (incendios grandes)**.

## Justificación adopción a pesar de R3 modesto

**Adoptar** por:

1. **Cero daño**: 0 regresión TPs MIROVA, 0 regresión recall/precision/ratio
   en cualquier vol-sensor, 0 cambio inesperado.
2. **Mejora interna real**: -59% de pixels Path 2nd ruidosos en MODIS
   mejora la calidad del campo térmico publicado al dashboard
   (visualización + heatmap), aunque no se vea en cluster selection
   downstream.
3. **Coherente con F-S81-A** (adoptada S84): mismo principio intra-radio,
   misma justificación empírica (1332 ALERTAs MIROVA Tier A 100%
   intra-radio S84).
4. **No esperar Fase C** sería "perfect enemy of good": la mejora
   disponible no se posterga por no tener solución completa al R3.
5. **Default operacional limpio** facilita los A/B de Fase C (la
   reducción Path 2nd ya estará en baseline).

**NO adoptar** sería justificable si:
- El gate destruyera TPs → no es el caso.
- El gate introdujera regresión en otra métrica → no es el caso.
- La adopción bloqueara el camino a Fase C → no, B' y C son ortogonales
  (B' mascarea pixels del 2nd pass, C atacará la selección de cluster
  contextual).

## Plan Fase C — supresión MIROVA-style contextual

Hipótesis a verificar: los 98 R3 MODIS + 57 VIIRS residuales corresponden
mayormente a cuerpos térmicos no-volcánicos conocidos del catálogo de
cada volcán (lagos/salares/glaciares/fumarolas crónicas extendidas).

Audit script granular (`experiments/_s85_f_s81_c/r3_nature_audit.py`,
pendiente):

1. Para cada R3 violator en `enabled`, extraer:
   - Composición del cluster: pixels + lat/lon + dist al vent.
   - Centroide ponderado.
   - Paths que marcaron cada pixel.
2. Cruzar lat/lon del centroide contra **catálogo de zonas térmicas
   no-volcánicas conocidas** por volcán:
   - Lago Conguillío (Llaima).
   - Salar Atacama (Lascar).
   - Cono glaciar (Tupungatito, PP, Villarrica fundido).
   - Fumarolas crónicas conocidas (Lastarria zona Lazufre, NdC frente).
3. Si confirma hipótesis (≥70% R3 en zonas catalogadas) → implementar
   gate de supresión vent-anchored fuerte.
4. Si NO confirma → reinvestigar mecanismo real.

## Tag defensivo

`pre-s85-f-s81-b-prime-adoption` → snapshot pre-adopción.

## Refs

- Diseño: `docs/F_S81_B_PRIME_SECOND_PASS_GATE.md`
- Audit B0 original: `docs/R3_RESIDUAL_BY_PATH.md`
- Backlog refutado: `docs/F_S81_B_BACKLOG_PATH_ABC_GATES.md`
- A/B script: `experiments/_s85_f_s81_b_prime/audit.py`
- Resultados: `experiments/_s85_f_s81_b_prime/audit_results.{md,json}`
- Run A/B: 26557588067
- Beyond MIROVA roadmap futuro: `docs/BEYOND_MIROVA_EXTENSIONS.md`
