# Inventario de imágenes MIROVA — `imagenes/`

> Capturas mirovaweb.it tomadas 2026-04-25 ~05:54:01 UTC (Last Update visible en headers).
> Entregadas por Nicolás S21 como ground truth visual complementaria al CSV
> `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv`.

## Cobertura

3 volcanes × 3 sensores × 4 tipos de plot = **36 imágenes**.

| Volcán | Sensores | Tier MIROVA | Estado pipeline |
|---|---|---|---|
| Chaitén | MODIS, VIIRS375, VIIRS750 | A | Recall 1.00 (S20 post-Regla D, supera S9 0.93) |
| Lascar | MODIS, VIIRS375, VIIRS750 | A | Recall 0.86 (S18 NOAA-21) → 0.73 summit-only post-Regla D |
| Tupungatito | MODIS, VIIRS375, VIIRS750 | A | Recall 0.57 (S20). Cuello D6 — target S22 |

## Tipos de plot por volcán/sensor

| Tipo | Eje Y | Significado |
|---|---|---|
| `*_Dist.png` | Distancia (km) al vent | Distribución espacial detecciones MIROVA, Last Month + Last Year |
| `*_VRP.png` | VRP (Watts) lineal | Magnitudes radiativas |
| `*_logVRP.png` | VRP (Watts) log10 | Misma data en log para ver escala dinámica |
| `*_Latest10NTI.png` | Mosaico NTI | 10 últimas detecciones con miniaturas BT y NTI |

## Hallazgos visuales clave

1. **Tupungatito MODIS Dist Last Year y Last Month VACÍOS** — MIROVA no detecta MODIS
   Tupungatito en 12 meses. Refs son 100% VIIRS. (Ver H_S21_2 en
   `~memory/project_s21_findings.md`.)
2. **Tupungatito VIIRS375 Dist Last Year**: línea roja casi continua a 5 km. Detecciones
   sistemáticas todos los días. Leyenda `<7km / >7km` (no `<5km` como Lascar).
3. **Lascar VIIRS375 Dist**: rojos a 1-2 km (cráter cercano), `<5km / >5km` leyenda.
   Cráter activo persistente.
4. **Chaitén VIIRS375 Dist**: rojos esporádicos. Pocos eventos en año, low-activity.
5. **Latest10NTI Tupungatito VIIRS375**: VRP 0.05–0.39 MW, todos sub-pixel. Confirma
   fumarola débil persistente, no eruptiva.

## Uso

- **Ground truth visual** complementario al CSV cuando hay duda sobre clasificación
  binned vs distancia real (CSV ya tiene `Distancia_km` exacta, ver H_S21_3).
- **Sanity check** post-fix: re-generar imágenes equivalentes desde nuestro pipeline
  con `scripts/visualize_volcano.py` (a crear S22+) y comparar contra mirovaweb.

## Reposición

Si las imágenes se pierden: descargar via Mirova-v1 visualizador
(`https://github.com/MendozaVolcanic/Mirova-v1/blob/main/visualizador.py`) o re-pedir
a Nicolás. Generación automatizada futura: scrape mirovaweb.it/latest.php directamente.
