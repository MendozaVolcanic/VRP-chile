# Forense H17 replicable — Lascar

Ventana: 2026-04-12 → 2026-04-25  ·  inner_radius_km=5.0  ·  tolerance_min=60

**N refs MIROVA (latest.php only)**: **40**

## Conteos

| Clase | Count | % | Significado |
|---|---:|---:|---|
| TP | 38 | 95.0% | Detectamos correctamente (summit o inner) |
| T1 | 0 | 0.0% | No hay record nuestro en la ventana — sin granule |
| T2b | 0 | 0.0% | Record presente, escena fría (n_anomalous=0) |
| T3 | 0 | 0.0% | vrp_vent>0 pero clasificado far — Regla D NO aplicada (regresión) |
| T4 | 2 | 5.0% | n_anomalous>0, todos far — D6 background no localizado |

**Recall summit-class (TP/N)**: 0.950