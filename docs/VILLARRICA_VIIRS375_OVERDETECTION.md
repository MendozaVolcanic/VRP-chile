# Villarrica VIIRS-I 375m — sobre-detección vs MIROVA real

> Documento creado S52 (2026-05-17) en respuesta a observación de Nicolás
> (geólogo SERNAGEOMIN): "los reportes reales son mucho menos en VIIRS375
> que los nuestros".
>
> **Confirmado empíricamente**: VRP-chile sobre-detecta en factor ~40×
> en conteo y ~31× en magnitud comparado con alertas MIROVA NRT.

## Datos crudos (window 2026-01-01 → 2026-05-16, 5 meses)

### MIROVA per-mes (CSV consolidado scraper Mirova-v1)

| Mes | ALERTA_TERMICA | FALSO_POSITIVO | RUTINA | NULO | Total |
|---|---:|---:|---:|---:|---:|
| 2026-01 | 3 | 0 | 83 | — | 86 |
| 2026-02 | 1 | 1 | 112 | — | 114 |
| 2026-03 | 1 | 2 | 120 | — | 123 |
| 2026-04 | 1 | 2 | 156 | — | 159 |
| 2026-05 | 2 | 2 | 75 | — | 79 |
| **TOTAL** | **8** | **7** | **546** | — | **561** |

### VRP-chile per-mes (data/mirova_equivalent/Villarrica.json, VIIRS-I 375m only)

| Mes | summit (pc.vrp>0, ≤5 km) | d≤1 km | d≤0.5 km |
|---|---:|---:|---:|
| 2026-01 | 3 | 0 | 0 |
| 2026-02 | 91 | 12 | 3 |
| 2026-03 | 69 | 8 | 0 |
| 2026-04 | 96 | 11 | 1 |
| 2026-05 | 58 | 7 | 3 |
| **TOTAL** | **317** | **38** | **7** |

## Métricas clave de la divergencia

### Conteo

- MIROVA alertable (ALERTA + FP) en 5 meses: **15**
- VRP-chile "summit detecciones": **317**
- **Ratio sobre-detección: ~21×** (si comparamos con alertable MIROVA)
- **Ratio sobre-detección: ~40×** (si comparamos solo ALERTA)

### Coincidencia espacial-temporal

De nuestras 317 detecciones summit:
- **7 (2.2%)** coinciden con MIROVA ALERTA o FP
- **151 (47.6%)** coinciden con MIROVA RUTINA (= MIROVA procesó pero no alertó)
- **159 (50.2%)** sin contraparte MIROVA en ±10 min

### Magnitud (5 ALERTAs MIROVA con granule descargado)

| Fecha | MIROVA VRP | VRP-chile pc.vrp | Ratio |
|---|---:|---:|---:|
| 2026-05-14 05:48 | 0.31 | 3.74 | 12.1× |
| 2026-05-11 06:00 | 0.31 | **0.39** | **1.2×** ✓ |
| 2026-04-09 06:00 | 0.11 | 7.14 | 64.9× |
| 2026-03-08 06:00 | 0.21 | 6.63 | 31.6× |
| 2026-02-26 05:42 | 0.12 | **10.11** | **84.2×** |

**Ratio mediano magnitud: 31×**. Solo el caso 2026-05-11 está calibrado (1.2×) — los otros 4 están MASIVAMENTE inflados.

### Diferenciador "buenas" (con contraparte MIROVA) vs "extras"

| Métrica | n=7 con contraparte | n=310 sin contraparte |
|---|---:|---:|
| dist mediana (km) | 1.53 | 1.55 |
| pc.vrp_mw mediano | 6.63 | 2.54 |
| pc.n_pixels mediano | 71 | 49.5 |

**La distancia NO discrimina** — ambas familias caen ~1.5 km del cráter. MW y npx sí discriminan algo (2.6× más brillantes y 1.4× más grandes las "buenas").

## Hallazgo metodológico crítico

El CSV consolidado MIROVA tiene **dos columnas distintas** que confunden si no se lee bien:
- `Tipo_Registro`: ALERTA_TERMICA / FALSO_POSITIVO / RUTINA / NULO (← la categoría operacional MIROVA)
- `Clasificacion Mirova`: NULO / Muy Bajo / Bajo / Moderado / Alto (← intensidad, no es alerta)

Filtrar por `Clasificacion Mirova == "Muy Bajo"` da resultados muy distintos a `Tipo_Registro == "ALERTA_TERMICA"`. **Documentar y validar matchers usan `Tipo_Registro`** (que es el correcto).

## Interpretación volcanológica

### Por qué tantas detecciones summit pero pocas alertas MIROVA

MIROVA alerta solo cuando:
1. **Cluster espacialmente confinado al cráter** (todas las 8 alertas tienen `Distancia_km = 0.84 km` exacto = pixel I-band snapped al centro del cráter)
2. **VRP supera umbral interno conservador** (~0.05 MW persistente)
3. **Posiblemente confirmación en 2+ granules consecutivos**

Nosotros marcamos summit a TODO cluster con `pc.vrp > 0` dentro de inner_radius=5 km (paridad MIROVA radio detección, NO criterio de alerta). Resultado: capturamos:
- (a) Las pocas alertas reales MIROVA (legítimas)
- (b) Detecciones MIROVA RUTINA (MIROVA vio pero no alertó — son legítimas también, MIROVA NRT sin supervisión humana)
- (c) Detecciones nuestras sin contraparte MIROVA (gap CSV scraper o sobre-detección real)

## Causa probable inflación magnitud

`pc.vrp_mw` suma TODOS los pixels del primary_cluster después de vent_anchored selection. Pero esos pixels incluyen:
- Pixel summit caliente (señal real)
- Pixels borde cluster con BT moderada (calor residual roca)
- Pixels glaciar/nieve con BT baja pero contribución positiva al sum

MIROVA reporta probablemente:
- Solo el pixel TOP VRP del cluster (1 pixel)
- O integración limitada a un sub-cluster sub-pixel

Sin acceso al código MIROVA es difícil saber exactamente.

## Opciones para próxima sesión (decisión Nicolás)

### Opción A: Aceptar como diseño actual + documentar interpretación

- "VRP-chile reporta DETECCIONES (pc.vrp del cluster summit completo)"
- "MIROVA reporta ALERTAS (subset estricto)"
- Mantener todo el pipeline. Documentar en dashboard que `pc.vrp` no es directamente comparable con "MW MIROVA".
- **Pasa MISSION.md** ✓ (no cambia metodología)

### Opción B: Agregar flag derivada `is_mirova_like_alert`

- Nuevo campo en records: `is_mirova_like_alert = (pc.dist <= 1.0 AND pc.vrp_mw <= 1.0 AND ...)` (calibrado contra las 8 alertas reales)
- Frontend filtra para mostrar "Alertas tipo MIROVA" vs "Todas las detecciones"
- **Pasa MISSION.md Q3** (alineación interna, no cambia pipeline core)
- Mantiene compatibilidad — no destruye nada

### Opción C: Restringir cluster_hotspots a pixels muy cercanos al vent (<1.5 km)

- Cambio en `pipeline/clustering.py` cluster_hotspots
- Resultado esperado: pc.vrp magnitud se reduce ~30×, conteo summit cae a ~10-15
- **NO pasa MISSION.md** sin paper que respalde este filtro estricto
- Probable regresión recall otros volcanes (Lascar fumarola persistente, PCC lacolito 6 km)
- **NO recomendado**

### Opción D: Investigación profunda código MIROVA

- Coppola tiene OSF v2.5 con código posiblemente publicado
- Buscar GitHub repos MIROVA o suplementos papers
- Si encontramos su método magnitud → implementar igual
- **Recomendado solo si Opciones A/B no satisfacen a SERNAGEOMIN**

## Recomendación pragmática

**Opción B + Opción A combinadas**:
1. Mantener pipeline actual (detección sub-pixel summit es ventaja única VRP-chile)
2. Agregar `is_mirova_like_alert` derived flag para mostrar subset estricto
3. Dashboard: dos toggles separados: "Detecciones (todas)" vs "Alertas tipo MIROVA"
4. Documentar claramente la diferencia para usuarios SERNAGEOMIN

Costo implementación: ~1 sesión. Sin riesgo regresión.
