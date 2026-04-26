# Forense H17 replicable — Tupungatito

Ventana: 2026-03-25 → 2026-04-25  ·  inner_radius_km=5.0  ·  tolerance_min=60

**N refs MIROVA (latest.php only)**: **35**

## Conteos

| Clase | Count | % | Significado |
|---|---:|---:|---|
| TP | 20 | 57.1% | Detectamos correctamente (summit o inner) |
| T1 | 2 | 5.7% | No hay record nuestro en la ventana — sin granule |
| T2b | 1 | 2.9% | Record presente, escena fría (n_anomalous=0) |
| T3 | 0 | 0.0% | vrp_vent>0 pero clasificado far — Regla D NO aplicada (regresión) |
| T4 | 12 | 34.3% | n_anomalous>0, todos far — D6 background no localizado |

**Recall summit-class (TP/N)**: 0.571