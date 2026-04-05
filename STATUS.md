# STATUS — VRP Chile
**Ultima actualizacion:** 2026-04-05 (sesion 3 — expansion 45 volcanes + calibracion MIROVA)

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
