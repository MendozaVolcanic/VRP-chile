# Análisis FPs curados OSF v2.5 — Llaima

Generado por `experiments/83_llaima_fp_analysis.py` (Bloque F S37, 2026-05-11)
desde `reports/osf_v25_tier_a.csv`.

## Pregunta operacional

Llaima tiene 411 records class=0 (FPs curados por MIROVA) en el archive OSF
v2.5 Tier A. ¿Validan los `exclude_zones` Lago Conguillío que removimos en
S27 al adoptar "clon literal MIROVA"?

## Resumen

- **411** records class=0 (FPs curados)
- **330** records class=1 (detecciones reales)
- **741** total → **FP rate global 55.5%** (la mitad de lo que MIROVA reporta
  en Llaima históricamente termina marcado como FP en la curación humana)
- Vent referencia: (-38.692, -71.729)

## Hallazgo central — distribución radial summit vs scene

Las clases tienen **separación radial limpia**:

| dist desde vent | class=1 (real) | class=0 (FP) |
|---|---|---|
| 0–4 km (summit) | 330 (100%) | 46 (11%) |
| 4–30 km (scene) | 0 (0%) | **365 (89%)** |

**Las 330 detecciones reales caen TODAS dentro de 4 km del vent**. Ningún
class=1 fuera de 4 km en toda la historia OSF.

**El 89% de los FPs (365/411) están fuera del inner_radius=5 km.**

Físicamente coherente: Llaima es un estratovolcán con actividad fumarólica
sumital residual. No hay flujos lávicos largos, no hay lacolitos descentrados,
no hay vents secundarios activos. **Cualquier señal real ocurre en el cráter
sumital.** Todo lo que el algoritmo detecta lejos es ruido del background
nevado/heterogéneo.

## Hipótesis Conguillío NE — REFUTADA

Lago Conguillío está ~10 km NE del cráter. Si fuera el contribuyente
dominante de FPs, esperábamos concentración en sectores N/NNE/NE/ENE.

**Resultado**: solo **74 FPs (18.0%)** caen en esos cuatro sectores. Distribución
real por sector:

| sector | % FPs | sector | % FPs |
|---|---|---|---|
| ESE | 12.4% | SW | 7.3% |
| SE | 12.4% | SSE | 7.1% |
| NW | 9.0% | NNW | 6.6% |
| **NE** | **4.6%** | **N** | **4.1%** |

Los sectores SE/ESE acumulan más FPs (24.8%) que los del cuadrante NE.

**Conclusión**: la hipótesis Conguillío como feature dominante NO se sostiene.
Los FPs están repartidos en arco amplio sin un único feature hidrológico
explicándolos.

## Hallazgo secundario — sesgo brutal de sensor

| sensor | class=0 (FP) | class=1 (real) | FP rate |
|---|---|---|---|
| MODIS | 93 | 327 | 22.1% |
| VIIRS 750 m | 20 | 0 | **100%** |
| VIIRS 375 m | 298 | 3 | **99.0%** |

**MIROVA en Llaima esencialmente solo confía en MODIS.** VIIRS dispara 318
FPs históricos y solo 3 detecciones reales. Esto es consistente con la
sensibilidad submuestreada de la fumarola sumital al pixel I-band 375 m sobre
una caldera nevada heterogénea: σ_bg local infla y dispara falsas anomalías.

## Hallazgo terciario — estacionalidad invernal otoño-primavera

| mes | FP rate (FP/(FP+Real)) | mes | FP rate |
|---|---|---|---|
| Ene | 29.1% | Jul | 59.4% |
| Feb | 40.0% | Ago | 72.4% |
| Mar | 75.8% | **Sep** | **82.4%** |
| Abr | 35.8% | **Oct** | **96.8%** |
| May | 58.2% | **Nov** | **82.1%** |
| Jun | 68.9% | Dic | 37.8% |

Los meses con mayor cobertura de nieve estacional (Sep–Nov) tienen FP rate
>80%. Verano chileno (Dic–Feb) baja a 30–40%. Físicamente: nieve fresca con
microrelieve heterogéneo → σ_bg local irregular → más falsos picos sobre el
test contextual.

## Conclusión operacional

**Sobre `exclude_zones` Conguillío (removido S27):**

❌ **NO se justifica reintroducirlo.** El parche apuntaba a un feature
específico (~10 km NE) que aporta solo el 4.6% de los FPs. Removerlo en S27
fue una decisión correcta dentro del objetivo (1) clon literal MIROVA.

**Sobre lo que sí ayudaría a Llaima específicamente (no acción inmediata):**

1. **Cap distance Llaima-específico**: dado que el 100% de detecciones reales
   históricas caen dentro de 4 km del vent, descartar todo >5 km en Llaima
   eliminaría 89% de los FPs (365/411) sin costo en recall. Esto NO es
   `exclude_zones`, es `outer_radius_km=5` específico para Llaima.

2. **Path VIIRS 375m más estricto en Llaima**: VIIRS 375m tiene FP rate 99%
   y aporta 3 detecciones reales en la historia OSF. Subir el threshold para
   este sensor en Llaima específicamente recortaría ~298 FPs.

3. **Filtro temporal estacional**: no estándar en VRP, complejo de defender
   contra "clon literal". Notado como observación, no acción.

**Decisión recomendada para S37**: NO tocar `mirova_equivalent.yaml` por
Llaima ahora. El bug H8 y D8 son prioridad operacional mayor (impacto recall
en 11 volcanes vs precisión en 1). Documentar el hallazgo en backlog para
una posible fase "tuning per-volcano" futura.

## Métricas crudas — top clusters geográficos (grid 0.05°)

| lat | lon | n_FPs | dist vent | sector | sensor dominante |
|---|---|---|---|---|---|
| -38.700 | -71.700 | 23 | 2.7 km | ESE | VIIRS375 (19) |
| -38.800 | -71.550 | 22 | 19.6 km | SE | MODIS (10) |
| -38.700 | -71.750 | 16 | 2.0 km | WSW | VIIRS375 (15) |
| -38.750 | -71.550 | 13 | 16.8 km | ESE | MODIS (6) |
| -38.750 | -71.500 | 11 | 20.9 km | ESE | MODIS (6) |
| -38.800 | -71.600 | 10 | 16.4 km | SE | VIIRS375 (5) |
| -38.650 | -71.500 | 9 | 20.4 km | ENE | MODIS (7) |
| -38.800 | -71.650 | 9 | 13.8 km | SSE | VIIRS375 (4) |
| -38.600 | -71.850 | 9 | 14.7 km | NW | VIIRS375 (7) |
| -38.500 | -71.800 | 8 | 22.2 km | NNW | VIIRS375 (5) |

Notar: clusters >15 km están dominados por MODIS, sugiriendo background
térmico amplio en la cuenca del Bío-Bío valle abajo. No hay feature concentrado.

## Reproducir

```bash
python experiments/83_llaima_fp_analysis.py
```

Lee `reports/osf_v25_tier_a.csv` (regenerable con `experiments/82_osf_v25_audit.py`).
