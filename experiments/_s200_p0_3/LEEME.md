# P0 parte (3): enmascaramiento de un foco débil por una anomalía fuerte (S200)

Informe: `INFORME.md`. Pre-registro y adenda con su sha256: `PREREGISTRO.md`, `ADENDA_POSTHOC.md`.

Para reproducir:

1. El arnés importa el detector desde `main_snapshot/`, una copia de `pipeline/` de origin/main `b7626b03c` que no se
   versiona. Rearmarla desde la raíz del repo:
   `mkdir -p experiments/_s200_p0_3/main_snapshot && git archive b7626b03c pipeline | tar -x -C experiments/_s200_p0_3/main_snapshot`
2. Los 10 recortes VIIRS 750 (`recorte_*.npz`) viven en
   `experiments/_s158_audit_r2/granulos/run_39641637298/s158-r2-granulos/`, fuera de git; salen del artefacto del run
   39641637298 de S158. `comun.py` los busca con la ruta absoluta del checkout de Nicolás.
3. Orden: `control_c1_identidad.py`, `control_c2_linealidad.py`, `medir.py`, `medir_posthoc.py`, `resumen*.py`,
   `area_umbral.py`, `tabla_informe.py`, `armar_informe.py`. Cada script deja su salida en `<script>_salida.txt`.
