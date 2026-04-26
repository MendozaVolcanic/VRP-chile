# Inventario de imágenes MIROVA — `imagenes/`

> Snapshots fechados de mirovaweb.it. Ground truth visual complementaria al CSV
> `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv`.

## Estructura

`imagenes/<YYYY_MM_DD>/<Volcano>_<Sensor>_<Tipo>.png`

Snapshots disponibles:
- **`2026_04_25/`**: 36 imágenes, Last Update varía 05:54:01–06:00:01 UTC.
  Entregadas por Nicolás S21.
- **`2026_04_26/`**: 36 imágenes, bajadas automáticamente con `scripts/`
  (S22, ver "Reposición" abajo). Last Update ~18:18:01 UTC del 25-Abr
  (mirovaweb actualiza cuando hay nuevas detecciones, no cada hora).

## URLs MIROVA web (templates predictibles)

```
MODIS:    https://www.mirovaweb.it/OUTPUTweb/MIROVA/MODIS/VOLCANOES/<Volcano>/<Volcano>_MODIS_<Type>.png
VIIRS750: https://www.mirovaweb.it/OUTPUTweb/MIROVA/VIIRS750/VOLCANOES/<Volcano>/<Volcano>_VIIRS750_<Type>.png
VIIRS375: https://www.mirovaweb.it/OUTPUTweb/MIROVA/VIIRS375/VOLCANOES/<Volcano>/<Volcano>_VIIRS375_<Type>.png
```

Type ∈ {Dist, VRP, logVRP, Latest10NTI}.

## Cobertura

3 volcanes × 3 sensores × 4 tipos de plot = **36 imágenes por snapshot**.

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

## Hallazgos visuales 2026-04-26 (gap actividad Tupungatito)

Comparación 25-Abr vs 26-Abr en Tupungatito_VIIRS375_Dist:
- 25-Abr Last Update: 05:54:01 UTC. Línea roja densa hasta el final.
- 26-Abr Last Update: 25-Apr-2026 18:18:01 UTC. **Sin detecciones rojas
  después del 24-Abr** en Last Month plot. Confirma que MIROVA no detecta
  Tupungatito en últimos 2-3 días → fumarola en período de actividad muy
  baja (consistente con T4 que vimos).

## Reposición

Snapshot manual de cualquier fecha:
```bash
mkdir -p imagenes/$(date +%Y_%m_%d)
cd imagenes/$(date +%Y_%m_%d)
for vol in Tupungatito Lascar Chaiten; do
  for type in Dist VRP logVRP Latest10NTI; do
    curl -sL -o "${vol}_MODIS_${type}.png" \
      "https://www.mirovaweb.it/OUTPUTweb/MIROVA/MODIS/VOLCANOES/${vol}/${vol}_MODIS_${type}.png"
    curl -sL -o "${vol}_VIIRS750_${type}.png" \
      "https://www.mirovaweb.it/OUTPUTweb/MIROVA/VIIRS750/VOLCANOES/${vol}/${vol}_VIIRS750_${type}.png"
    curl -sL -o "${vol}_VIIRS375_${type}.png" \
      "https://www.mirovaweb.it/OUTPUTweb/MIROVA/VIIRS375/VOLCANOES/${vol}/${vol}_VIIRS375_${type}.png"
  done
done
```

Para volcanes adicionales (e.g. Lastarria, Villarrica), agregar al loop.

Generación automatizada futura: scrape mirovaweb.it/latest.php directamente
(Mirova-v1 ya lo hace cada 5min, ver `~memory/feedback_mirova_no_human_supervision`).
