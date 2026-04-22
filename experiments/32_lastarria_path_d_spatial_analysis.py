"""32_lastarria_path_d_spatial_analysis.py — diagnostic espacial.

Analiza donde caen los pixels Path D detectados en los 17 Lastarria records
reprocesados overnight. Cross-check contra distribucion OSF 25 anos.
Usado como justificacion fisica para P3.1 dual-ROI.

Resultados (2026-04-22):
  OSF Lastarria (5368 refs VRP>0): 80% en 0-3km, 11% en 15-25km.
  Path D Lastarria (836 px en 17 records): 0.24% en 0-3km, 55% en 15-25km.

Conclusion: P3.2 solo es "demasiado permisivo espacialmente" - captura
anomalias contextuales reales (Lazufre/Cordon del Azufre) pero MIROVA
nunca las retiene. Dual-ROI P3.1 cura esto: summit C1=0.003 sensible
+ scene C1=0.010 estricto que descarta pixels lejanos.
"""
# Script de referencia - resultados ya interpretados en memory/
