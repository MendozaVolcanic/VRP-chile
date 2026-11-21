#!/usr/bin/env bash
# S192: lleva a escena no medida (motivo_vacio "fondo_no_estimado", 0 MW) los records MODIS de la via guardados con
# fondo nulo (diag_codigo_mirova.L_bk == 0 con alertados), en data/mirova_equivalent, data/historia_34 y
# data/sombra_34. Sigue a #1065 (opcion a de Nicolas, 2026-11-20). Determinista e idempotente: lo corre
# .github/workflows/aplicar-reemplazo.yml en cada intento sobre origin/main fresco. El informe va junto al script.
# Si un archivo no se puede reescribir en su mismo formato o un record trae claves inesperadas, sale con codigo 2
# antes de escribir.
set -euo pipefail
python experiments/_s192_fondo_nulo/reemplazo_fondo_nulo.py \
  --informe experiments/_s192_fondo_nulo/aplicado/informe.json --aplicar
