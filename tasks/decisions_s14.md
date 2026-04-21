# Decisiones y aprendizajes S14 — 2026-04-21

Sesión S14 (continuación de S13 2026-04-18). Enfoque: paridad métrica con
MIROVA v2.5 OSF (615K filas) + corrección del esquema de clasificación
visual dual (summit/far).

---

## Decisiones operacionales tomadas

### D1. Esquema dual "detectar amplio + clasificar por distancia"
MIROVA no usa máscaras geométricas. Procesa una grilla cuadrada UTM 51×51 km
alrededor de cada volcán (radio inscrito 25.5 km) y luego **clasifica
visualmente** cada detección por distancia al centro:

- Dentro de `inner_radius_km` (valor oficial MIROVA) → rojo = anomalía
  volcánica real.
- Fuera de ese radio pero dentro de la grilla → negro/gris = posible pero
  menor confianza.

**Adoptamos el mismo esquema**:
- `radius_km = 25 km` uniforme para todos los volcanes chilenos (paridad
  con grilla MIROVA).
- `inner_radius_km` por volcán con los valores oficiales MIROVA extraídos
  de los KML (provistos por Nicolás, ver tabla en D2).
- Campo nuevo en cada record: `distance_class = "summit" | "far"` según
  distancia del hotspot al vent vs `inner_radius_km`.

### D2. Radios internos oficiales MIROVA (`inner_radius_km`)

| Volcán              | inner_radius_km |
|---------------------|----------------:|
| Lastarria           |               3 |
| Planchón-Peteroa    |               3 |
| Copahue             |               4 |
| Lascar              |               5 |
| Isluga              |               5 |
| Nevados de Chillán  |               5 |
| Llaima              |               5 |
| Villarrica          |               5 |
| Chaiten             |               5 |
| Tupungatito         |               7 |
| Puyehue-Cordón Caulle |            20 |

Fuente: KML oficial MIROVA, extraídos por Nicolás en su repo Mirova-v1.
Estos son los radios dentro de los cuales MIROVA pinta en rojo las
detecciones en su dashboard.

### D3. PCC — mantener vent en el domo de Cordón Caulle
Tu decisión S12 de usar el domo como vent sigue vigente. El
`inner_radius_km=20` cubre el complejo completo (Puyehue a 7 km + edge del
sistema a ~18 km). No es necesario mover al centroide MIROVA porque la
clasificación roja es funcionalmente equivalente.

### D4. Llaima — sin máscara geométrica de Conguillío
Con `radius_km=25` detectamos todo lo que MIROVA detecta, incluso hits del
lago Conguillío a 9 km. Esos hits caen en `distance_class="far"` porque
están fuera del `inner_radius_km=5` de Llaima. Aparecen en el dashboard
como puntos grises/negros, no como anomalía volcánica real. Replicamos
MIROVA exactamente sin necesidad de polígonos de exclusión.

### D5. Fix `WOOSTER_COEFF` por sensor (validado empíricamente en Paso 0)
- MODIS 1 km: `18.9` (sin cambio, ya correcto).
- VIIRS 750m (M-band): `18.9 → 19.7` (fix pendiente, aplicar).
- VIIRS 375m (I-band): `18.9 → 18.0` (ya aplicado en S13).

Derivación: coeficientes efectivos MIROVA extraídos directamente de OSF
v2.5 (columnas `Tot_Lmir_hot`, `Tot_Lmir_bk`, `VRP`). Cada sensor usa el
coeficiente constante con error ≤0.17%.

### D6. Schema fix — `final_hotspot_*` unificado
El commit S12 `8ad2f59` generó inconsistencia: `hotspot_lat/lon/dist_km`
solo se llenaba en eruption-path (2–40% de records positivos), quedando
vacío en vent-path (el 60–90% restante). El dashboard leía `hotspot_*` y
perdía los puntos vent-path.

**Fix**: nuevo campo `final_hotspot_lat/lon/dist_km` con lógica de
fallback (eruption-path → vent-path). El dashboard lee solo `final_*`.

### D7. mirova_equivalent recibe los fixes (no experimental)
Estos cambios son **correcciones de paridad**, no experimentos.
Se aplican al perfil `mirova_equivalent`. El perfil `experimental` queda
disponible para pruebas posteriores (integrated-ROI, TIRVolcH I5, ROI1/ROI2
de Coppola 2016a, etc.) sobre la base ya corregida.

---

## Aprendizajes transversales

### A1. La calibración empírica con OSF v2.5 reemplaza la derivación teórica
Cuando hay base de datos publicada (`Tot_Lmir_hot`, `Tot_Lmir_bk`, `VRP`),
calcular `coef_emp = VRP / (Tot_hot - Tot_bk)` y verificar contra fórmulas
candidatas es infinitamente más confiable que derivar unidades de papers.
Resolvió en 1 minuto la discrepancia Di Bella (k=2.48×10⁷) vs Laiolo
(k=18.0 × A_pix) que nos había preocupado un mes.

**Regla**: antes de confiar en un número de un paper, si hay data
publicada del mismo grupo, verificar empíricamente primero.

### A2. Los diagnósticos paralelos ahorran reprocesos caros
Paso 0 (coeficiente) + Paso 1a (régimen) + diagnósticos A/B/D (paralelos)
resolvieron el 80% de las dudas sin fetch. El Paso 1b (reproceso 24 GB)
quedó postergado hasta después de aplicar los fixes — ahora sí tiene
sentido correrlo porque valida cambios concretos.

**Regla**: siempre agotar los análisis sobre datos ya en disco antes de
descargar más. El costo de diagnósticos locales es minutos; el de
reprocesos horas o días.

### A3. `hotspot_dist_km` no es lo que parece
Se calcula desde `volcano_lat/lon` (centro nominal), no desde
`vent_lat/lon` (vent real). Esto es confuso especialmente cuando vent y
centro difieren (PCC con offset 7.58 km entre ambos).

**Regla**: cualquier campo con "distance" o "dist_km" en el schema debe
documentar explícitamente desde qué punto se mide. El fix `final_hotspot_*`
soluciona la ambigüedad.

### A4. MIROVA es arquitecturalmente más simple de lo que pensábamos
No hay máscaras geométricas, no hay detección con radios adaptativos, no
hay filtrado multi-capa. Es:
1. Grilla UTM 51×51 km alrededor del centro.
2. NTI + ETI + contextual thresholds (Coppola 2016a).
3. Clasificación visual post-detección por distancia al centro.

La complejidad está en los umbrales, no en la geometría. Replicarlo es
factible si respetamos esa arquitectura.

### A5. Las clasificaciones MIROVA oficiales son datos, no opiniones
Los `LIMITE_KM` que extrajo Nicolás de los KML MIROVA no son heurísticas
nuestras — son las decisiones documentadas del equipo UNITO sobre qué es
"anomalía volcánica real" por volcán. **Usarlos tal cual** es más
defendible que inventar nuestros propios umbrales geológicos.

Cuando podamos justificar divergencias con experimentos propios, bien. Por
ahora = MIROVA oficial.

---

## Archivos modificados en Paso 2

- `volcanoes.yaml`: +`inner_radius_km` por volcán, `radius_km=25` uniforme.
- `pipeline/process_modis.py`: +`final_hotspot_*`, +`distance_class`.
- `pipeline/process_viirs.py`: +`final_hotspot_*`, +`distance_class`.
- `pipeline/process_viirs_mod.py`: +`final_hotspot_*`, +`distance_class`,
  `WOOSTER_COEFF = 19.7`.
- `frontend/index.html`: render por `distance_class`, círculo del
  `inner_radius_km` visible, leyenda actualizada.

## Archivos de backup antes del cambio

- `volcanoes.yaml.S13backup` — snapshot pre-S14 para rollback.

---

## Siguiente sesión (si S14 no cierra acá)

1. Paso 1b — reproceso Nov 2025 sobre 4 volcanes con schema nuevo.
2. Auditoría cross-match evento-a-evento contra OSF v2.5.
3. Decisión: mergear a `mirova_equivalent` permanente o iterar si paridad no llega a [0.8, 1.25].
4. Track B — integrated-ROI Coppola 2015 Eq.1 para Villarrica sub-pixel
   (en `experimental`).
