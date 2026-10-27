#!/bin/bash
# Verificador: re-corrida de los scripts del autor sobre MI copia de los artefactos (instruccion R1 de la tarea).
set -o pipefail
cd "D:/vrp-trabajo/s162-mxd03" || exit 1
export PYTHONIOENCODING=utf-8
export VRP_PROFILE=mirova_equivalent
V="experiments/_s162_mxd03/resultado/verificador"
ART="D:/vrp-trabajo/s162-mxd03/$V/copias/tandas"
echo "=== hora inicio $(date -u +%FT%TZ) HEAD $(git rev-parse HEAD)"
echo "=== vara_mxd03.py --evaluar"
python -I experiments/_s162_mxd03/vara_mxd03.py --evaluar --art "$ART" 2>&1
echo "exit vara: $?"
echo "=== evaluar_mxd03.py"
python -I experiments/_s162_mxd03/evaluar_mxd03.py --art "$ART" --vara "$ART/vara_resultado.json" --ref D:/vrp-trabajo/temporales/s162_mxd03/ref 2>&1
echo "exit evaluar: $?"
echo "=== hora fin $(date -u +%FT%TZ)"
