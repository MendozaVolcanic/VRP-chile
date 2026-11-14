#!/usr/bin/env bash
# S184: reemplaza la serie VIIRS 750 de PuyehueCordonCaulle con el reproceso de la caja del crater (PR #999).
# Determinista: lo corre .github/workflows/aplicar-reemplazo.yml en cada intento sobre origin/main fresco.
# Toca solo data/mirova_equivalent/PuyehueCordonCaulle.json; el informe va junto al script.
# El tope de sin par sale del ensayo local (ensayo/informe.json); si se pasa, no se escribe nada.
set -euo pipefail
python experiments/_s184_pcc_crater_aplicar/aplicar_pcc_v750.py \
  --max-sin-par "${MAX_SIN_PAR:-0}" --informe experiments/_s184_pcc_crater_aplicar/aplicado/informe.json --aplicar
