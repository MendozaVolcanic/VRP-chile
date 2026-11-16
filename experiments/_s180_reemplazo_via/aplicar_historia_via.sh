#!/usr/bin/env bash
# S180: reemplaza la historia publicada de los 11 Tier A con la union de la via, las tres familias de sensor
# (MODIS, VIIRS 375, VIIRS 750), y aparta las pasadas K sin par a data/_k_residuales_via/. Determinista: lo corre
# .github/workflows/aplicar-reemplazo.yml en cada intento sobre origin/main fresco. Decision de Nicolas del 2026-11-11.
# El tope de sin par por volcan y familia sale del ensayo (experiments/_s180_reemplazo_via/ensayo/); si un volcan lo
# pasa no se escribe nada (un tope pasado es un trozo que falta, no un descarte de borde).
set -euo pipefail
python experiments/_s180_reemplazo_via/aplicar_via.py --familias MODIS,VIIRS375,VIIRS750 \
  --max-sin-par "${MAX_SIN_PAR:-0.08}" --informe experiments/_s180_reemplazo_via/aplicado/informe.json --aplicar
