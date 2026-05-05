# Planchón regresión Driver B — análisis 3 FNs nuevos

Refs MIROVA Planchón ALERTA_TERMICA 90d: 31

## Records donde OFF detectó (vrp_summit>0) pero ON no detectó (vrp_summit=0)

| Fecha UTC | Sensor MIROVA | MIROVA MW | OFF pc_vrp | OFF n_t1pix | OFF dist_class |
|---|---|---:|---:|---:|---|
| 2026-04-08 06:18 | VIIRS375 | 0.060 | 2.395 | 60 | summit |
| 2026-02-27 05:24 | VIIRS375 | 0.050 | 1.721 | 78 | summit |
| 2026-02-10 05:42 | VIIRS375 | 0.070 | 3.266 | 87 | summit |

Total regresiones OFF→ON: 3

## Detalle pixel-level de los records OFF detectados

### 2026-04-08 06:18 VIIRS375 (MIROVA 0.060 MW)

**OFF**: vrp_summit=2.395, dist_class=summit, primary_cluster={'n_pixels': 56, 'vrp_mw': 2.395, 'centroid_lat': -35.21479, 'centroid_lon': -70.57356, 'centroid_dist_km': 1.005}, triggered_test1=True, n_test1_pixels=60
**ON**: vrp_summit=0.0, dist_class=summit, primary_cluster={'n_pixels': 56, 'vrp_mw': 0.0, 'centroid_lat': -35.21479, 'centroid_lon': -70.57356, 'centroid_dist_km': 1.005}, triggered_test1=True, n_test1_pixels=60
  OFF anomaly_pixels n=60, vrp top5: ['0.0000', '0.0000', '0.0000', '0.0000', '0.0000'], bt_k top5: ['273.7', '273.3', '273.3', '273.3', '273.1']

### 2026-02-27 05:24 VIIRS375 (MIROVA 0.050 MW)

**OFF**: vrp_summit=1.721, dist_class=summit, primary_cluster={'n_pixels': 54, 'vrp_mw': 1.721, 'centroid_lat': -35.21542, 'centroid_lon': -70.54986, 'centroid_dist_km': 1.983}, triggered_test1=True, n_test1_pixels=78
**ON**: vrp_summit=0.0, dist_class=summit, primary_cluster={'n_pixels': 54, 'vrp_mw': 0.0, 'centroid_lat': -35.21542, 'centroid_lon': -70.54986, 'centroid_dist_km': 1.983}, triggered_test1=True, n_test1_pixels=78
  OFF anomaly_pixels n=78, vrp top5: ['0.0000', '0.0000', '0.0000', '0.0000', '0.0000'], bt_k top5: ['275.1', '275.0', '274.9', '274.8', '274.8']

### 2026-02-10 05:42 VIIRS375 (MIROVA 0.070 MW)

**OFF**: vrp_summit=3.266, dist_class=summit, primary_cluster={'n_pixels': 85, 'vrp_mw': 3.266, 'centroid_lat': -35.21646, 'centroid_lon': -70.56745, 'centroid_dist_km': 0.772}, triggered_test1=True, n_test1_pixels=87
**ON**: vrp_summit=0.0, dist_class=summit, primary_cluster={'n_pixels': 85, 'vrp_mw': 0.0, 'centroid_lat': -35.21646, 'centroid_lon': -70.56745, 'centroid_dist_km': 0.772}, triggered_test1=True, n_test1_pixels=87
  OFF anomaly_pixels n=87, vrp top5: ['0.0000', '0.0000', '0.0000', '0.0000', '0.0000'], bt_k top5: ['276.1', '276.1', '276.1', '275.7', '275.6']


## Veredicto Planchón

Si las 3 regresiones tienen MIROVA<0.1 MW y OFF n_test1_pixels grande con vrp pixel chico:
  → señal sub-pixel real cortada por filtro 5σ. Considerar 4σ.
Si las 3 tienen ratio OFF >>5× MIROVA y pc_vrp inflada artificialmente:
  → eran FPs marginales (TPs por coincidencia temporal). Filter es CORRECTO eliminándolos.
Si pixels OFF tienen ΔT >5K consistentemente:
  → eran señal real, considerar relajar threshold.
