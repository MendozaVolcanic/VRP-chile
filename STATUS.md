# STATUS — VRP Chile
**Ultima actualizacion:** 2026-04-08 (sesion 6 — diagnóstico profundo MODIS, plan E2 listo para sesión 7)

---

## SESION 6 (2026-04-08) — Diagnóstico profundo

### Para arrancar sesión 7

**Lee primero**: `experiments/04_session6_final_findings.md` (reporte completo
con todos los hallazgos, datos crudos y plan E2 detallado).

**TL;DR**: el path eruption-scale de MODIS en `process_modis.py` está estructuralmente
roto desde siempre. 0 detecciones en 183 records históricos de Lascar. Todos los
VRP MODIS reportados vienen del vent-scale fallback. El diagnóstico está completo,
el fix está identificado pero NO implementado aún (esperando review).

### Hallazgos clave

1. **MIROVA reference contaminada con OCR**: regenerado `data/mirova/Lascar.json`
   desde `registro_vrp_consolidado.csv` (175 records limpios vs 203 con
   OCR truncado). Commit `0e76938`. Métrica mediana global global mejoró 1.003 -> 0.978.

2. **Phase A (vent TIR) revertida**: Phase A inflaba 20 PCC records de 0.18 -> 95 MW
   por bypass del distance filter. Commit `0e5e2eb`. Lección L5.5.

3. **E1 (exclude vent from p95) inert**: implementado en commit `53d5f62`,
   reproceso cambió 0 records. El p95 nunca fue el binding constraint.

4. **Diagnóstico instrumentado** (commit `b5c48d5`): 4 campos nuevos en MODIS:
   - `diag_sigma_bg_k`, `diag_roi_p95_k`, `diag_eff_threshold_k`, `diag_t_max_dist_km`
   - Reproceso febrero 2026 con instrumentación: commit `573b7d5`.

5. **El binding constraint REAL es `t_bg + 3·σ_bg`**:
   - σ_bg mediana en Lascar = 5.08 K, máximo 16.36 K
   - 3σ mediana = 15.24 K (vs floor de 5 K)
   - 100% (54/54) de records febrero confirman esto, 0% el p95
   - Causa A: nubes contaminan el background annulus (4 records con t_bg < 260 K)
   - Causa B: heterogeneidad orográfica (Lascar 5592m, valles 3000m, picos vecinos 5704+m)

6. **Hot pixels casi nunca están en vent_radius=3km**: de 12 records febrero con
   dT > 8K, solo 2 tenían el hotspot dentro de 3km del cráter. Los otros 10
   estaban a 6-9.6km. El vent del YAML no es la posición efectiva del MODIS pixel
   centroid.

### Plan E2 para sesión 7 (NO ejecutado aún)

**E2a — Cloud mask en background** (1 línea en `process_modis.py:177`):
```python
bg_vals = bt_mir[bg_mask & ~np.isnan(bt_mir) & (bt_mir > 260)]
```

**E2b — Cap del componente sigma** (en `process_modis.py:183`):
```python
MAX_SIGMA_COMPONENT_K = 7.0
sigma_component = min(N_SIGMA * std_bg, MAX_SIGMA_COMPONENT_K)
threshold = max(ANOMALY_THRESHOLD_K, sigma_component)
```

**Predicción**:
- Bucket MODIS 2-10 MW mediana ratio: 0.37 -> ~0.7-0.9
- ~25-30 records nuevos con `n_anomalous_pixels > 0` en febrero
- Mediana global ~1.0
- Riesgo: posibles falsos positivos en volcanes quietos (Chaiten, Michinmahuida).
  Validar antes de masificar.

### Commits sesión 6
- `0f039bd` Phase A vent TIR (REVERTIDO)
- `0e5e2eb` Revert Phase A
- `fd42536` Diagnostic framework (F1-F5)
- `0e76938` MIROVA Lascar regen sin OCR
- `d513cae` Lascar baseline post-revert reprocess
- `53d5f62` E1: vent exclusion from p95 (INERT)
- `f5f5e12` Lascar post-E1 reprocess (0 changes)
- `b5c48d5` Diagnostic instrumentation (4 fields)
- `573b7d5` Lascar Feb 2026 with diag fields

### Estado al cerrar sesión 6
- Diagnóstico completo y documentado en `experiments/04_session6_final_findings.md`
- E1 commit `53d5f62` está en main pero es inert. NO revertido a propósito
  (no hace daño, es defensible mantenerlo, decisión de revert para sesión 7
  según resultados de E2).
- 4 campos `diag_*` en MODIS records están en main. NO removidos a propósito
  (sirven para validar E2 cuando se ejecute).
- **Pendiente sesión 7**: implementar E2a+E2b' en `process_modis.py`,
  reprocesar Lascar feb 2026, validar contra MIROVA, decidir rollout.
- **Pendiente más lejano**: reprocesar 9 volánes restantes, primer pull 34 nuevos.

### Lecciones agregadas (`tasks/lessons.md`)
- L6.1: Fix the bug you can prove, not the bug you suspect (E1 inert)
- L6.2: MODIS eruption-scale path broken forever, hidden by vent-scale fallback
- L6.3: σ_bg en Lascar es 5-16 K naturalmente (nubes + orografía)
- L6.4: vent_radius=3km es muy ajustado para MODIS 1km pixels
- L6.5: Siempre preservar baseline JSON antes de reprocesar

---

## SESION 5 (2026-04-07)

### Fix de reprocesamiento
`store.py:append_record` deduplicaba por (datetime_utc, sensor) y saltaba
records existentes — los reprocesos solo agregaban records nuevos, nunca
actualizaban los viejos. Bug detectado cuando un "reproceso" de Villarrica
marzo 2026 solo agrego 1 registro y dejo los 241 existentes con los VRP pre-fix.

**Solucion**: flag `overwrite=True` propagado end-to-end:
- `pipeline/store.py`: append_record acepta overwrite, reemplaza existing
- `scripts/run_pipeline.py`: --overwrite CLI flag
- `.github/workflows/nrt.yml`: input workflow_dispatch `overwrite=true`
- Commit: `4d6af41`

### Reprocesamientos completados
- **Villarrica** 2026-03-01 -> 2026-03-31 (test): 43 records actualizados
  - VIIRS cap suave ~1.96x, MODIS sec3 variable 1.0-10.5x. Sin regresiones.
  - Commit: `1afb255`
- **Lascar** 2026-01-01 -> 2026-04-07 (rango completo): 644 records, 398 con VRP>0
  - Commit: `c956884`

### Validacion Lascar vs MIROVA (203 refs)

Script: `scripts/validate_lascar_vs_mirova.py`

| Metrica          | Pre-fix | Post-fix | Delta |
|------------------|---------|----------|-------|
| Capture rate     | 81.3%   | **88.7%** | +7.4  |
| Capture MODIS    | 64.3%   | **85.7%** | +21.4 |
| Capture VIIRS375 | 88.9%   | **93.9%** | +5.0  |
| Capture VIIRS750 | 80.6%   | **82.3%** | +1.7  |
| Mean ratio       | 0.60    | **1.14**  | +0.54 |
| **Median ratio** | **0.57**| **1.02**  | **+0.45** |

**Ratio por sensor (media):**
- MODIS: 0.50 -> 0.94 (mejora 1.87x)
- VIIRS-I 375m: 0.67 -> 1.28 (mejora 1.92x)
- VIIRS-M 750m: 0.54 -> 1.04 (mejora 1.91x)

**Conclusion**: El bias sistematico 0.55 documentado sesion 4 esta resuelto.
Mediana global post-fix = 1.02 (calibracion dentro del ~2% de MIROVA).
Todos los sensores mejoraron uniformemente ~1.9x, consistente con la teoria
(sec3 para MODIS, cap 2.0 para VIIRS bow-tie aggregated).

### Hallazgo metodologico: MIROVA procesa VIIRS diurno via TIR (I05)
Los outliers extremos de la validacion (ratio <0.1 o >3) trazan todos a
records MIROVA VIIRS375 a ~18:XX UTC = daytime en Lascar (local ~14:30).
Nuestro pipeline bloquea todos los records diurnos a nivel `store.py`.

Hipotesis: MIROVA extrae detecciones diurnas VIIRS usando banda I05 TIR
(11.45 um, Stefan-Boltzmann via Aveni 2024 TIRVolcH). El TIR es robusto a
contaminacion solar; solo el MIR (3-4 um) la sufre.

Proxima mejora (sesion futura): filtro nocturno **band-specific** en vez de
global — permitir I05 TIR diurno por un code path separado en
`process_viirs.py`. Ver `tasks/lessons.md` L5.3.

### Commits sesion 5
- `7bba3aa` Backup 11 volcano JSONs pre scan-angle reprocessing
- `4d6af41` Add --overwrite flag for reprocessing existing records
- `1afb255` NRT reprocess Villarrica 2026-03 (GitHub Actions)
- `c956884` NRT reprocess Lascar 2026-01 -> 2026-04 (GitHub Actions)

### Estado al cerrar sesion 5
- Scan-fix validado contra MIROVA. Bias 0.55 -> 1.02 (mediana).
- Villarrica y Lascar reprocesados.
- **Pendiente**: reprocesar los 9 volcanes restantes (Copahue, Chaiten, Isluga,
  Lastarria, Llaima, NevadosDeChillan, PlanchonPeteroa, PCC, Tupungatito).
  Rango recomendado: 2026-01-01 -> 2026-04-07.
- **Pendiente**: primer pull 34 volcanes nuevos.
- **Mejora futura**: daytime I05 TIR en process_viirs.py.

---

## SESION 4 (2026-04-07)

### Problema identificado
Sesgo sistematico ~2x (ratio 0.55 nuestro/MIROVA) en 152 detecciones pareadas de Lascar, independiente del sensor. Causa: usabamos area nadir fija (1 km² MODIS, 140625 m² VIIRS-I, 562500 m² VIIRS-M) sin corregir por angulo de escaneo off-nadir.

### Fix implementado
Nuevo modulo `pipeline/scan_geometry.py`:
- **MODIS**: correccion completa `A = A_nadir / cos³(θ_z)` (Wooster 2003, Wolfe 2002). Zenith del pixel calculado desde columna con curvatura terrestre: `sin(θ_z) = ((R+h)/R)·sin(θ_scan)`. Borde de swath ~13x mas area que nadir.
- **VIIRS**: correccion suave (lineal, capada en 2.0x). VIIRS tiene agregacion bow-tie on-board (Wolfe 2013) que mantiene tamano de pixel ~constante (0.32-0.6 km², Cao 2014), aplicar sec³ completo causaba overshoot 25x.

### Validacion (Lascar 2026-03-28, GitHub Actions run 24094697988)
| Sensor | Pre-fix | sec³ completo | **Post-fix** | MIROVA |
|---|---|---|---|---|
| MODIS Terra | -- | -- | 2.58 MW | ~2.34 MW |
| MODIS Aqua | -- | -- | 2.01 MW | -- |
| VIIRS SNPP 375m | 1.917 MW | 47.9 MW | **3.76 MW** | 2.34 MW |
| VIIRS SNPP 750m | 1.733 MW | 43.3 MW | **3.40 MW** | -- |
| VIIRS NOAA20 375m | -- | -- | 0.23 MW (vent) | -- |

Consistencia cross-sensor OK. Overshoot resuelto.

### Commits sesion 4
- `1e3428a` Add scan-angle pixel area correction to MODIS/VIIRS VRP
- `9da2157` Fix VIIRS scan-angle overshoot - use milder correction

### Estado al cerrar sesion
- Fix en `main`, ya pusheado y validado en 1 fecha
- **NINGUN volcan reprocesado aun** — los 11 JSON existentes siguen con areas nadir antiguas
- `data/Lascar_backup.json` existe (backup pre-sesion)
- `scripts/debug_search.py` existe (untracked, debug anterior)

---

## INSTRUCCIONES PARA CONTINUAR EN NUEVA SESION

### Paso 1 — Backup de datos actuales (antes de reprocesar)
```bash
cd "VRP Chile"
mkdir -p data/backups_pre_scanfix
for v in Chaiten Copahue Isluga Lascar Lastarria Llaima NevadosDeChillan PlanchonPeteroa PuyehueCordonCaulle Tupungatito Villarrica; do
  cp "data/$v.json" "data/backups_pre_scanfix/${v}_pre_scanfix.json"
done
git add data/backups_pre_scanfix/
git commit -m "Backup pre scan-angle reprocessing"
git push
```

### Paso 2 — Test de reproceso en 1 volcan (Villarrica, 1 mes)
Trigger GitHub Actions:
```bash
gh workflow run "NRT VRP Pipeline" \
  --field volcano=Villarrica \
  --field start=2026-03-01 \
  --field end=2026-03-31
gh run watch
```
Verificar que los VRP son razonables y coherentes con MIROVA antes de masificar.

### Paso 3 — Reproceso completo de los 11 volcanes
Lanzar en lotes (evitar rate limit NASA). Por volcan, rango completo 2026-01-01 → hoy:
```bash
for v in Lascar Copahue Villarrica PuyehueCordonCaulle Chaiten Isluga Lastarria Llaima NevadosDeChillan PlanchonPeteroa Tupungatito; do
  gh workflow run "NRT VRP Pipeline" --field volcano=$v --field start=2026-01-01 --field end=2026-04-07
  sleep 30
done
```
Nota: cada run tarda ~1-5 min, GitHub permite 20 runs concurrentes.

### Paso 4 — Validar vs MIROVA
Comparar capture rate y rangos VRP contra `data/mirova/*.json`. Esperado: capture rate >84%, VRP ~1.5-2x mayores que pre-fix (especialmente MODIS bordes de swath).

### Paso 5 — Primer pull de los 34 volcanes nuevos
Misma estrategia por lotes. Lista en STATUS.md arriba (Taapaca, Parinacota, Guallatiri, etc.).

### Paso 6 — Actualizar README + informe metodologico + export CSV
Pendiente del mensaje original del usuario (puntos 4, 6, 7, 8).

### Comandos utiles para nueva sesion
- Ver estado: `git log --oneline -15`
- Ver workflows corriendo: `gh run list --workflow="NRT VRP Pipeline" --limit 10`
- Ver log de un run: `gh run view <id> --log | grep -iE "VRP|MW"`
- Trigger manual: ver Paso 3

### Contexto critico para retomar
- **NO reprocesar sin backup** (Paso 1 primero)
- Los JSON actuales son todos pre-fix y subestiman VRP ~2x
- El fix VIIRS es deliberadamente suave (factor max 2.0) porque bow-tie aggregation ya compensa la geometria. NO cambiar a sec³ completo.
- MODIS usa sec³ completo, es fisicamente correcto.
- pyhdf no funciona en Windows → todo MODIS debe correrse en GitHub Actions.

---

---

## Estado actual

**Pipeline NRT operativo** en GitHub Actions (cada 6h).
- Repositorio: https://github.com/MendozaVolcanic/VRP-chile
- Dashboard: https://mendozavolcanic.github.io/VRP-chile/
- Formula VRP: Wooster MIR radiance (Coppola 2015, Eq. 7)
- Filtro nocturno activo (triple barrera: fetch, process, store)
- NTI dual-criteria para VIIRS 375 m
- Filtro local ROI p95 para todos los sensores (anti-falsos positivos topograficos)
- Multi-pixel anomaly tracking en los 3 procesadores
- NOAA-20 busqueda multi-version (2.1/2/1) para productos VJ1
- **Filtro distancia eruption-scale**: hotspots >5km del crater descartados como no-volcanicos
- **45 volcanes configurados** (11 con datos, 34 nuevos pendientes de primer pull)

---

## Datos por volcan (sesion 3 — 2026-04-05)

### Volcanes con datos (recalibrados)

| Volcan | Registros | Detecciones (VRP > 0) | Max VRP | MIROVA ref | Capture rate |
|--------|-----------|-----------------------|---------|------------|-------------|
| Puyehue-Cordon Caulle | 134 | 2 | 3.81 MW | 89 registros | -- |
| Villarrica | 765 | 96 | 1.900 MW | 8 detecciones | OK |
| Lascar | 631 | 308 | 5.120 MW | 203 detecciones | 84.1% |
| Copahue | 752 | 74 | 2.679 MW | 0 registros | OK (nosotros detectamos mas) |
| Isluga | datos | -- | -- | -- | -- |
| Lastarria | datos | -- | -- | -- | -- |
| Llaima | datos | -- | -- | -- | -- |
| NevadosDeChillan | datos | -- | -- | -- | -- |
| PlanchonPeteroa | datos | -- | -- | -- | -- |
| Tupungatito | datos | -- | -- | -- | -- |
| Chaiten | datos | -- | -- | -- | -- |

### Volcanes nuevos (sin datos aun — 34 volcanes)

Taapaca, Parinacota, Guallatiri, Irruputuncu, OlcaParuma, Ollague, SanPedro, Putana,
SanJose, Tinguiririca, DescabezadoGrande, CerroAzulQuizapu, LagunaDelMaule, NevadoDeLongavi,
Antuco, Callaqui, Lonquimay, Tolhuaca, Sollipulli, Quetrupillan, Lanin, MochoChoshuenco,
CarranLosVenados, AntillancaCasablanca, Osorno, Calbuco, YateHornopiren, Huequi,
Michinmahuida, CorcovadoYanteles, Melimoyu, Mentolat, MacaCay, Hudson

---

## Calibracion vs MIROVA (sesion 3)

### Metodologia de comparacion
- Comparamos fechas de deteccion (VRP > 0) entre nuestro pipeline y CSVs scrapeados de MIROVA
- **Capture rate global: 84.1%** (233 de 277 fechas MIROVA detectadas)
- Nuestra sensibilidad vent-scale (threshold 1K) detecta senales ~2x mas debiles que MIROVA (~0.023 MW vs ~0.05 MW)

### Filtro de distancia (fix critico sesion 3)
- Problema: 613 falsos positivos por hotspots eruption-scale a 5-15km del crater (fuentes urbanas, agricolas, geotermales)
- Solucion: `MAX_HOTSPOT_DIST_KM = 5.0` — descarta eruption-scale lejano, mantiene vent-scale
- Implementado en `store.py` y `normalize_data.py`

### Calibracion vent_radius por volcan
- Tupungatito: vent_radius 2→5 km (MIROVA avg dist 4.0km — recupera 23 fechas perdidas)
- PlanchonPeteroa: vent_radius 2→3 km (MIROVA avg dist 1.2km)
- Lastarria: vent_radius 2→3 km (MIROVA avg dist 1.6km)
- Lascar: vent_radius 2→3 km (MIROVA avg dist 1.1km)

---

## Lo que se hizo sesion 3 (2026-04-05)

1. **Recalibracion Villarrica, Lascar, Copahue** — Pull completo con vent-scale detection
2. **Filtro distancia eruption-scale** — Hotspots >5km descartados (elimina 613 FP)
3. **Calibracion vent_radius** — Ajustado por volcan segun distancias reales MIROVA
4. **Comparacion sistematica vs MIROVA** — 84.1% capture rate validado
5. **Expansion a 45 volcanes** — volcanoes.yaml + frontend + archivos JSON vacios
6. **Dashboard mejorado estilo MIROVA** — Barra resumen alertas, mapa overview con Leaflet, tabla NRT, reloj UTC, auto-refresh 5min
7. **Fix seguridad innerHTML** — Reemplazado por textContent/createElement
8. **Fix Isluga GVP ID** — Corregido de 355060 a 355030
9. **Normalizacion offline** — normalize_data.py con mismo filtro distancia que store.py

---

## Lo que se hizo sesion 2 (2026-04-05)

1. **Vent-scale detection** — Threshold 1K sobre background, ROI ~2km en vent
2. **Coordenadas de venteo** — Villarrica, Lascar, Copahue, PCC
3. **Normalizacion VRP en store.py** — vrp_mw unificado
4. **MIROVA ref importados** — Villarrica y Copahue
5. **Workflow recalibracion** — GitHub Actions con --start/--end
6. **Test validacion Lascar 2026-03-28**: VIIRS SNPP 1.917 MW (MIROVA: 2.34 MW)

---

## Lo que se hizo sesion 1 (2026-04-05)

1. **Multi-pixel anomaly tracking** — Los 3 procesadores guardan anomaly_pixels[]
2. **Fix critico MODIS radiance** — L_bg = Planck(T_bg) por no-linealidad
3. **Fix falsos positivos topograficos** — NTI dual-criteria + filtro local ROI p95
4. **Fix falsos positivos diurnos** — Triple barrera nocturna
5. **Dashboard completo** — VRP time series, mapa hotspot, distancia, VRE, comparacion MIROVA, CSV export
6. **README.md + STATUS.md** — Documentacion completa
7. **Datos MIROVA importados** — Lascar (203 rec) y PCC (94 rec)

---

## Arquitectura

```
scripts/run_pipeline.py       Entry point CLI (filtro nocturno, multi-sensor)
scripts/normalize_data.py     Normalizacion offline de campos VRP
pipeline/fetch.py             Descarga granulos NASA Earthdata (earthaccess)
pipeline/process_modis.py     MODIS Terra/Aqua Band 21/22 (1 km, 3.93 um)
pipeline/process_viirs.py     VIIRS I-band I04/I05 (375 m, NTI dual-criteria)
pipeline/process_viirs_mod.py VIIRS M-band M13 (750 m, 4.05 um)
pipeline/store.py             JSON persistence + nighttime solar gate + distance filter
frontend/index.html           Dashboard (Chart.js + Leaflet.js, 45 volcanes)
.github/workflows/nrt.yml     GitHub Actions NRT (cron 6h + trigger manual)
volcanoes.yaml                Config volcanes (45 activos)
data/mirova/                  Datos referencia MIROVA (JSON)
```

---

## Formula VRP (corregida 2026-04-04)

### Canal MIR — Metodo Wooster (Coppola 2015, Eq. 7)
```
VRP = 18.9 * A_pix * (L_hot - L_bg)
L = C1 / (lambda^5 * (exp(C2 / (lambda * T)) - 1))
```

### Canal TIR — Stefan-Boltzmann (Aveni 2024)
```
VRP_TIR = A_pix * sigma * (T_alert^4 - T_bg^4)
```
Solo aplica a VIIRS I05 (11.45 um).

---

## Criterios de deteccion de anomalias

Un pixel se marca como anomalo solo si pasa TODOS los filtros:

1. **BT threshold**: `BT > T_bg + max(5 K, 3 * sigma_bg)`
2. **Local ROI p95**: `BT > p95_ROI + max(3 K, 2 * sigma_ROI)`
3. **NTI filter** (VIIRS 375 m solamente): `NTI > NTI_bg + max(0.005, 3 * sigma_NTI)`
4. **Distance filter** (eruption-scale): hotspot > 5 km del crater = descartado

---

## Features del dashboard

| Feature | Estado | Detalles |
|---------|--------|----------|
| VRP time series | Listo | Chart.js, escala log, colores por sensor |
| Mapa hotspot | Listo | Leaflet.js, multi-pixel, popups por pixel |
| Distancia vs Tiempo | Listo | Distancia anomalia al crater |
| VRE acumulada | Listo | Integral energia termica (GJ) |
| Comparacion MIROVA | Listo | Overlay VRP nuestro vs MIROVA |
| Exportacion CSV | Listo | Descarga datos filtrados |
| Barra resumen alertas | Listo | Conteo por nivel de alerta MIROVA |
| Mapa overview | Listo | Leaflet con 45 volcanes, colores por alerta |
| Tabla NRT | Listo | Ultimas 30 detecciones de todos los volcanes |
| Reloj UTC | Listo | Hora UTC en tiempo real |
| Auto-refresh | Listo | Cada 5 minutos |
| Filtro nocturno | Listo | Triple barrera (fetch/process/store) |

---

## Sensores procesados

| Sensor | Producto | Banda | Resolucion | Area pixel |
|--------|----------|-------|------------|------------|
| MODIS Terra | MOD021KM | 21/22 (3.93 um) | 1 km | 1,000,000 m^2 |
| MODIS Aqua | MYD021KM | 21/22 (3.93 um) | 1 km | 1,000,000 m^2 |
| VIIRS SNPP 375 m | VNP02IMG | I04 (3.74 um) | 375 m | 140,625 m^2 |
| VIIRS NOAA-20 375 m | VJ102IMG | I04 (3.74 um) | 375 m | 140,625 m^2 |
| VIIRS SNPP 750 m | VNP02MOD | M13 (4.05 um) | 750 m | 562,500 m^2 |
| VIIRS NOAA-20 750 m | VJ102MOD | M13 (4.05 um) | 750 m | 562,500 m^2 |

---

## PROXIMA SESION — Pasos a seguir

### 1. Primer pull para los 34 volcanes nuevos
- Ejecutar recalibracion en GitHub Actions para todos los volcanes nuevos
- Rango: --start 2026-01-01 --end 2026-04-05
- Considerar batch processing para no exceder rate limits NASA
- Verificar que el workflow NRT ya los incluye automaticamente

### 2. Recalibrar volcanes con vent_radius actualizado
- Tupungatito (5km), PlanchonPeteroa (3km), Lastarria (3km), Lascar (3km) necesitan re-pull
- Los datos actuales fueron procesados con radios anteriores

### 3. PCC recalibracion con vent-scale
- 134 registros existentes NO tienen vrp_vent_mw
- Re-procesar para capturar senales debiles del campo fumarolico 2011

### 4. Cloud masking (mejora de calidad)
- Opciones: MOD35 cloud mask, BT umbral frio
- Prioridad media

### 5. NTI para MODIS
- Agregar Band 31 (11 um TIR) para NTI en MODIS

### 6. Umbrales por volcan
- Definir thresholds especificos usando coeficientes c_rad (Coppola 2023)
- Pendiente para sesion futura

### 7. GOES integracion
- En desarrollo en otra sesion (carpeta Goes/)

### 8. Alertas NRT
- En desarrollo en otra sesion
- Email, Telegram, GitHub notifications

---

## Escala de energia MIROVA

| Rango VRP | Clasificacion |
|-----------|--------------|
| < 1 MW | Muy Bajo |
| 1 - 10 MW | Bajo |
| 10 - 100 MW | Moderado |
| 100 - 1000 MW | Alto |
| > 1000 MW | Muy Alto |

---

## Referencias

- **Coppola 2015** — MIROVA core: metodo Wooster, NTI/ETI, coeficiente 18.9
- **Campus 2022** — Cross-calibracion MODIS-VIIRS, Sensors 22(5):1713
- **Aveni 2024** — TIRVolcH: deteccion TIR con Stefan-Boltzmann para I05, RSE 315:114388
- **Coppola 2023** — Base de datos MIROVA, coeficientes c_rad volcanes globales
