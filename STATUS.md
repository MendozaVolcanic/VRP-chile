# STATUS — VRP Chile
**Ultima actualizacion:** 2026-04-05 (sesion 2 — vent-scale detection)

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

---

## Datos por volcan (sesion 2 — 2026-04-05)

| Volcan | Registros | Detecciones (VRP > 0) | Max VRP | MIROVA ref | Estado |
|--------|-----------|-----------------------|---------|------------|--------|
| Puyehue-Cordon Caulle | 134 | 2 | 3.81 MW | 89 registros | OK (NRT activo) |
| Villarrica | 0 (reset) | -- | -- | 8 registros | Pendiente recalibracion |
| Lascar | 0 (reset) | -- | -- | 203 registros | Pendiente recalibracion |
| Copahue | 0 (reset) | -- | -- | 0 registros | Pendiente recalibracion |

**Villarrica, Lascar y Copahue reseteados** para recalibracion limpia con vent-scale detection.
Test exitoso con Lascar 2026-03-28: VIIRS SNPP 375m detecto 1.917 MW (MIROVA: 2.34 MW). Vent-scale funciona.

---

## Lo que se hizo sesion 2 (2026-04-05)

1. **Vent-scale detection** — Nuevo modo de deteccion para senales debiles (fumarolas, lagos de lava)
   - Threshold 1K sobre background regional (vs 5K del modo erupcion)
   - ROI pequeno (~2 km) centrado en el vent conocido
   - Implementado en los 3 procesadores: MODIS, VIIRS 375m, VIIRS 750m
2. **Coordenadas de venteo** — Agregadas a Villarrica, Lascar y Copahue en volcanoes.yaml
3. **Normalizacion VRP en store.py** — Todos los registros ahora tienen `vrp_mw` unificado (max entre eruption y vent-scale)
4. **Normalizacion t_max_k** — VIIRS 375m ahora exporta `t_max_k` ademas de `t_max_i04_k`
5. **MIROVA ref importados** — Villarrica (8 rec) y Copahue (0 rec) desde Mirova-v1
6. **Workflow recalibracion** — GitHub Actions ahora soporta --start/--end para rangos de fechas
7. **Test validacion Lascar 2026-03-28**:
   - VIIRS SNPP 375m: 1.917 MW (MIROVA: 2.34 MW) — coincide orden de magnitud
   - VIIRS NOAA20 375m: 0.115 MW (MIROVA: 0.11 MW) — match exacto
   - VIIRS SNPP 750m: 1.733 MW (MIROVA: 2.0 MW) — cercano
8. **Reset datos** — Villarrica, Lascar, Copahue limpiados para recalibracion fresca

---

## Lo que se hizo sesion 1 (2026-04-05)

1. **Implementacion multi-pixel anomaly tracking** — Los 3 procesadores (MODIS, VIIRS 375m, VIIRS 750m) ahora guardan `anomaly_pixels[]` con lat/lon/BT/VRP por cada pixel anomalo
2. **Fix critico MODIS radiance** — `L_bg = median(radiance)` cambiado a `L_bg = Planck(T_bg)` por no-linealidad de Planck
3. **Fix falsos positivos topograficos (Lascar)** — NTI dual-criteria + filtro local ROI p95
4. **Fix falsos positivos diurnos** — Triple barrera nocturna implementada
5. **Dashboard features completas**:
   - Panel resumen global
   - Chart distancia vs tiempo
   - VRE acumulada (GJ)
   - Comparacion MIROVA
   - Exportacion CSV
   - Mapa hotspot con Leaflet (multi-pixel, colores por sensor, popups)
6. **README.md reescrito** — Documentacion completa del proyecto
7. **STATUS.md actualizado** — Estado actual detallado
8. **Repo en GitHub** — Push completo a https://github.com/MendozaVolcanic/VRP-chile
9. **Datos MIROVA importados** — Lascar (203 rec) y PCC (94 rec) desde Mirova-v1

---

## Arquitectura

```
scripts/run_pipeline.py       Entry point CLI (filtro nocturno, multi-sensor)
pipeline/fetch.py             Descarga granulos NASA Earthdata (earthaccess)
pipeline/process_modis.py     MODIS Terra/Aqua Band 21/22 (1 km, 3.93 um)
pipeline/process_viirs.py     VIIRS I-band I04/I05 (375 m, NTI dual-criteria)
pipeline/process_viirs_mod.py VIIRS M-band M13 (750 m, 4.05 um)
pipeline/store.py             JSON persistence + nighttime solar gate
frontend/index.html           Dashboard (Chart.js + Leaflet.js)
.github/workflows/nrt.yml     GitHub Actions NRT (cron 6h + trigger manual)
volcanoes.yaml                Config volcanes (4 activos)
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

---

## Features del dashboard (todas implementadas)

| Feature | Estado | Detalles |
|---------|--------|----------|
| VRP time series | Listo | Chart.js, escala log, colores por sensor |
| Mapa hotspot | Listo | Leaflet.js, multi-pixel, popups por pixel |
| Distancia vs Tiempo | Listo | Distancia anomalia al crater |
| VRE acumulada | Listo | Integral energia termica (GJ) |
| Comparacion MIROVA | Listo | Overlay VRP nuestro vs MIROVA |
| Exportacion CSV | Listo | Descarga datos filtrados |
| Panel resumen global | Listo | Stats cruzados todos los volcanes |
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

## Historial de bugs corregidos

### 2026-04-05 — Falsos positivos topograficos (Lascar)
- Lascar a 5592 m rodeado de terreno mas calido → T_bg artificialmente bajo → 59 pixeles falsos (587 MW)
- Fix: NTI dual-criteria + filtro local ROI p95
- Resultado: elimina FP topograficos sin enmascarar senales volcanicas reales

### 2026-04-04 — Bug no-linealidad Planck en MODIS (CRITICO)
- `L_bg = median(radiance)` ≠ `Planck(median(BT))` con terreno heterogeneo
- Fix: `L_bg = Planck(T_bg)` consistente
- PCC paso de 1438 MW a ~3.81 MW (alineado MIROVA)

### 2026-04-04 — Falsos positivos diurnos
- 78 registros diurnos con VRP hasta 4307 MW por radiacion solar reflejada en MIR
- Fix: triple barrera nocturna (elevacion solar > 0 = rechazo)

### 2026-04-04 — Migracion formula Wooster
- Pipeline original usaba Stefan-Boltzmann para MIR → ~15x mas alto que MIROVA
- Migrado a Wooster `VRP = 18.9 * A * delta_L`

---

## PROXIMA SESION — Pasos a seguir

### 1. Recalibracion completa via GitHub Actions (URGENTE)
- Datos de Villarrica, Lascar y Copahue reseteados — necesitan recalibracion
- Usar workflow_dispatch con --start 2026-01-01 --end 2026-04-05 para cada volcan
- Ejemplo: volcano=Lascar, start=2026-01-01, end=2026-04-05
- MODIS solo funciona en GitHub Actions (pyhdf requiere Linux)
- Verificar resultados contra MIROVA ref (data/mirova/)

### 2. Validar recalibracion vs MIROVA
- Lascar: esperado 0.03-4.61 MW, ~200+ detecciones en 3 meses
- Villarrica: esperado 0.05-0.37 MW, ~8 detecciones
- Copahue: esperado 0 detecciones (MIROVA tampoco tiene)
- Si hay discrepancias grandes, revisar thresholds

### 3. PCC sin anomaly_pixels (formato legacy)
- PuyehueCordonCaulle tiene 134 registros pero los antiguos no tienen campo `anomaly_pixels`
- Los registros nuevos (post-fix) si lo tienen
- Decidir: (a) re-procesar PCC completo, o (b) dejar los legacy como estan (el dashboard maneja ambos formatos)

### 4. PCC recalibracion con vent-scale
- PCC ya tiene vent_lat/vent_lon (campo fumarolico 2011)
- Pero los 134 registros existentes NO tienen vrp_vent_mw
- Considerar re-procesar para capturar senales debiles que el eruption-scale pierde

### 6. Cloud masking (mejora de calidad)
- Actualmente sin filtro de nubes
- Nubes producen BT frias → generalmente no generan falsos positivos
- Pero SI ocultan anomalias reales → datos faltantes
- Opciones: (a) MODIS cloud mask (MOD35), (b) BT umbral frio para descartar pixeles nublados
- Prioridad media, pero importante para estadisticas de cobertura

### 7. NTI para MODIS
- Actualmente NTI solo funciona para VIIRS 375 m (tiene I04 MIR + I05 TIR)
- MODIS necesitaria leer Band 31 (11 um TIR) ademas de Band 21/22 (3.93 um MIR)
- Agregaria robustez al filtro de anomalias de MODIS
- Requiere modificar `read_modis_l1b()` para extraer Band 31

### 8. Expansion a mas volcanes
- Actualmente: 4 volcanes
- Meta: 43 volcanes chilenos (lista Copernicus-v1)
- `volcanoes.yaml` ya soporta multiples volcanes → solo agregar coordenadas
- Considerar limites de GitHub Actions (tiempo de ejecucion) y NASA Earthdata (rate limits)
- Expandir gradualmente: 4 → 10 → 20 → 43

### 9. Mapa global (feature F pendiente)
- Mapa tipo MIROVA con todos los volcanes monitoreados
- Leaflet.js con circulos de color segun ultimo VRP
- Click para ir al detalle de cada volcan
- Decidimos dejarlo para cuando tengamos >10 volcanes

### 10. Alertas NRT (feature G pendiente)
- Notificacion cuando VRP supera umbral configurable
- Opciones: email, Telegram bot, GitHub notification
- Requiere definir umbrales por volcan (c_rad coefficients de Coppola 2023)

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
