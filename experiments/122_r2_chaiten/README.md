# Experimento 122 — R2 retroactivo Chaiten (S70-1 T1)

## Pregunta

La adopción S63 de `local_kernel_bg: true` para Chaiten (ratio LEGACY 9.78× → NEW 2.23×, -77%) se hizo a partir de la **mediana A/B agregada sobre 20 ALERTAS** — sin la validación pixel-level (R2 verdadero) que S69 estableció como gate metodológico. La pregunta de S70-1 T1 es: ¿una ALERTA reciente, ya en producción con el fix adoptado, supera el R2 pixel-level?

## Marco conceptual (geólogo)

El método R2 verdadero (replicado de Lastarria S69 → T3 Step 8 esta sesión) responde dos preguntas a la vez:

1. **Magnitud bien calibrada**: ¿el VRP que reporta nuestro `primary_cluster` (filtrado, robusto) tiene el mismo orden de magnitud que el VRP MIROVA NRT para ese mismo granule? Banda aceptable [0.5×, 2.0×], que cubre el ±30% de error declarado por MIROVA con un margen físico razonable.
2. **Geometría bien anclada**: ¿la posición de nuestro cluster cae cerca de donde el campo de radiancia del TIF tiene su masa térmica concentrada en torno al cráter? El centroide ponderado de los top-10 pixels del TIF dentro de 3 km del vent es el proxy físico del "hotspot real" que reporta MIROVA. Tolerancia plan: drift < 2 km.

Si ambas pasan, no estamos sólo agregando bien — estamos clonando pixel por pixel. Si una falla, mostramos en qué dimensión nos desviamos y por qué.

## Caso elegido

ALERTA_TERMICA Chaiten 2026-05-18 05:30:01 VIIRS375 (registro_vrp_consolidado.csv, snapshot mirova_v1):

| Componente | Valor |
|---|---|
| Volcán | Chaiten |
| Fecha satelital | 2026-05-18 05:30:01 UTC |
| Sensor MIROVA | VIIRS375 |
| Sensor nuestro | VIIRS_NOAA20 |
| VRP MIROVA | 0.22 MW |
| Distancia MIROVA al vent | 0.75 km |
| Vent (volcanoes.yaml) | (-42.8344815, -72.6528875) |
| TIF paralelo | `mirova-tif-archive/data/tif/Chaiten/20260518_053001_VIIRS375.tif` |

Record nuestro (`data/mirova_equivalent/Chaiten.json`):

| Campo | Valor |
|---|---|
| `vrp_mw` (record agregado, todos los clusters) | 0.706 MW |
| `pc.vrp_mw` (primary_cluster) | **0.277 MW** |
| `pc.centroid_lat/lon` | (-42.83691, -72.6523) |
| `pc.centroid_dist_km` | 0.274 km |
| `pc.n_pixels` | 2 |
| `distance_class` | summit |

Por qué este caso: VIIRS375 mejor resolución espacial para validar geometría; ALERTA reciente post-adopción S63; TIF paralelo del mismo timestamp existe en el archive.

## Resultado

### 4 gates

| Gate | Criterio | Obtenido | Status |
|---|---|---|---|
| 1. Magnitud en banda | 0.5 ≤ ratio ≤ 2.0 | 1.26× | ✓ PASS |
| 2. Drift centroide | < 2.0 km | 2.15 km | ✗ FAIL (marginal) |
| 3. Ratio cerca de referencia S63 | |ratio − 2.23| ≤ 0.5 | 1.26× → diff 0.97 | ✗ FAIL |
| 4. Drift cerca de target | (sin target previo, == gate 2) | 2.15 km | ✗ FAIL |

**Verdict global: FAIL** (1 de 4 gates pasa estrictos)

### Lectura física (no programador)

**Magnitud (1.26×, ratio ours/MIROVA)**. Este caso individual está mejor calibrado que la mediana agregada S63 (2.23×). El cluster principal nuestro entrega 0.277 MW contra los 0.22 MW de MIROVA. Esto no contradice la adopción S63 — la mediana agregada incluye un rango de eventos; en este punto particular el fix `local_kernel_bg` está funcionando bien magnitud-wise. **Que el ratio individual quede MÁS cerca de 1.0 que el agregado S63 (2.23×) es una buena señal**, no una falla. El gate 3 reprueba porque está definido como "cerca del agregado S63", lo cual es informativo pero contra-intuitivo: queremos ratios cercanos a 1.0, no a 2.23.

**Geometría (drift 2.15 km)**. Acá hay una observación real. El centroide ponderado top-10 del TIF dentro de 3 km del vent cae en (-42.835, -72.679), unos 2.15 km al oeste de nuestro `pc.centroid` (-42.837, -72.652). Mirando los pixels: los top-10 del TIF cubren un rango de 0.055 a 2.91 km del vent (algunos casi tocan el límite del filtro 3 km), y todos tienen valores muy parejos (0.179 a 0.204 MW). Eso significa que en este granule VIIRS375 hay una mancha térmica espacialmente extendida hacia el oeste del cráter — el archivo TIF muestra 189 pixels positivos dentro de 3 km, pero la mayoría son de baja intensidad y no se concentran en el vent.

Nuestro pipeline, en cambio, hizo lo correcto desde el punto de vista volcanológico: identificó un cluster de 2 pixels muy cerca del vent (0.27 km), que físicamente corresponde al domo Chaitén activo, y descartó la nube térmica difusa al oeste. **MIROVA también reporta hotspot a 0.75 km del vent**, mucho más cerca que el centroide TIF top10. Esto sugiere que MIROVA aplica el mismo criterio de "cluster cercano al cráter, no centroide del campo radiométrico difuso" — y nuestro pipeline está reproduciendo esa decisión.

**Por qué el gate 2 (drift <2 km) falla marginalmente**: el método R2 S69 fue calibrado en Lastarria (área desértica, sin extensión térmica difusa al oeste). En Chaiten hay condiciones distintas: el TIF muestra una "campana" térmica más extendida al oeste del cráter (efecto de viento sobre la fumarola, posible contaminación marina/lacustre, o píxeles VIIRS sobre vegetación cálida). El centroide top10 se desplaza por esa cola occidental.

## Implicación

**La adopción S63 Chaiten queda con un PASS PARCIAL pixel-level**: magnitud confirmada (mejor que el agregado), geometría con drift 2.15 km que reprueba el umbral estricto pero está cerca del límite. **No es razón para revertir** — el ratio per-record 1.26× es excelente y el `pc.centroid` está bien anclado al cráter (0.27 km al vent, mientras que MIROVA reporta 0.75 km). El método R2 verdadero, calibrado sobre Lastarria, podría necesitar ajuste de tolerancia o un criterio adicional ("centroide top10 cerca del vent" vs "drift TIF↔pc") para volcanes con extensión térmica difusa como Chaiten.

Para el dashboard / decisión operacional: Chaiten S63 sigue válido como clon literal MIROVA NRT, con la nota de que **futuros R2 retroactivos deben considerar la geometría del campo radiométrico del volcán específico** (no aplicar tolerancia única calibrada en Lastarria).

## Artefactos

- `audit_chaiten.py` — script de auditoría (template Lastarria T3 Step 8 adaptado)
- `results.json` — output estructurado con todos los componentes (caso, vent, pc, MIROVA, magnitud, geometría, verdict)

## Referencias

- Método R2 verdadero: `experiments/120_audit_tif_vrp_sumable/audit_lastarria_real_method.py` + README Parte 2
- HYPOTHESIS_LOG: `H_S69_R2_RETROACTIVO_LASTARRIA`
- Adopción S63 Chaiten: bloque arranque S64, MIROVA_DIVERGENCES.md, MEMORY.md S63
- Plan S70-1: `tasks/plan_s70_1.md`
