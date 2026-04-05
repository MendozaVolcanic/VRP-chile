# STATUS — VRP Chile
**Ultima actualizacion:** 2026-04-05 (fin de sesion)

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

## Datos por volcan (al cierre de sesion 2026-04-05)

| Volcan | Registros | Rango fechas | Detecciones (VRP > 0) | Max VRP | MIROVA ref |
|--------|-----------|--------------|----------------------|---------|------------|
| Puyehue-Cordon Caulle | 132 | 2024-03-12 a 2026-04-04 | 2 | 3.81 MW | 94 registros |
| Villarrica | 13 (parcial) | 2026-01-01 a 2026-04-04 | 0 | 0 MW | -- |
| Lascar | 10 (parcial) | 2026-01-01 a 2026-04-04 | 0 | 0 MW | 203 registros |
| Copahue | 11 (parcial) | 2026-01-01 a 2026-04-04 | 0 | 0 MW | -- |

**NOTA**: Las recalibraciones de Villarrica, Lascar y Copahue quedaron corriendo al cerrar sesion.
Los datos son parciales — probablemente hay mas registros pendientes de escribir.
PCC paso de 74 a 132 registros (NRT automatico sigue sumando), y max VRP bajo de valores inflados a 3.81 MW (alineado con MIROVA).

---

## Lo que se hizo esta sesion (2026-04-05)

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

### 1. Verificar recalibraciones (URGENTE)
- Las recalibraciones de Villarrica, Lascar y Copahue quedaron corriendo
- **Verificar** si terminaron: revisar `data/Villarrica.json`, `data/Lascar.json`, `data/Copahue.json`
- Si no terminaron o fallaron: re-ejecutar el pipeline manualmente para Jan-Mar 2026
- Comparar nuestros VRP nocturnos vs datos MIROVA de referencia (data/mirova/)
- **Esperado**: Lascar deberia mostrar 0.03-4.61 MW (rango MIROVA), Villarrica ~0-0.5 MW

### 2. Commit y push datos calibrados
- Hacer `git add data/*.json` y push con los datos recalibrados
- Verificar que el dashboard en GitHub Pages muestra datos correctos para los 4 volcanes

### 3. PCC sin anomaly_pixels (formato legacy)
- PuyehueCordonCaulle tiene 132 registros pero los antiguos no tienen campo `anomaly_pixels`
- Los registros nuevos (post-fix) si lo tienen
- Decidir: (a) re-procesar PCC completo, o (b) dejar los legacy como estan (el dashboard maneja ambos formatos)

### 4. Importar datos MIROVA para Villarrica y Copahue
- Ya tenemos MIROVA ref para PCC (94 rec) y Lascar (203 rec)
- Faltan Villarrica y Copahue — buscar en https://github.com/MendozaVolcanic/Mirova-v1
- Convertir CSV a JSON en `data/mirova/Villarrica.json` y `data/mirova/Copahue.json`
- Necesario para que la tab "Comparacion MIROVA" funcione para esos volcanes

### 5. Validar detecciones vs actividad conocida
- Lascar: actividad fumarolica persistente → deberia tener detecciones VRP 0.03-5 MW
- Villarrica: lago de lava abierto → detecciones frecuentes VRP ~0.1-1 MW
- Si las recalibraciones dan 0 detecciones para todo, investigar si los thresholds son demasiado estrictos
- El filtro ROI p95 podria estar eliminando senales reales debiles → revisar

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
