#!/usr/bin/env bash
# Auditoría S179, frente B. Rearma los datos que leen sim_vigilancia.py, cotas_poder.py, detalle_sombra.py y pcc_v750.py.
# Todo sale de git show sobre el commit base 438a60a1e (no baja nada de la red). Destino: carpeta temporal del frente B.
# Uso: bash extraer_datos.sh   (desde cualquier carpeta; unos 176 MB)
set -euo pipefail
export MSYS_NO_PATHCONV=1
REPO="/c/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
B=/d/vrp-trabajo/temporales/s179-audit/b
REF=438a60a1e
cd "$REPO"
mkdir -p $B/datos/mirova_equivalent $B/datos/sombra_codigo_mirova $B/datos/guardia_k_viirs $B/datos/ref $B/datos/union
for v in Lascar Lastarria Isluga Tupungatito PlanchonPeteroa NevadosDeChillan Llaima Villarrica Copahue PuyehueCordonCaulle Chaiten; do
  for d in mirova_equivalent sombra_codigo_mirova guardia_k_viirs; do
    git show $REF:data/$d/$v.json > $B/datos/$d/$v.json
  done
done
git show $REF:data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv > $B/datos/ref/registro_vrp_ocr.csv
git show $REF:data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado_respaldo_20260408.csv > $B/datos/ref/registro_vrp_consolidado_respaldo_20260408.csv
git show $REF:data/mirova_reference/union_historica/consolidado_filas_perdidas.csv > $B/datos/union/consolidado_filas_perdidas.csv
sha256sum $B/datos/ref/registro_vrp_ocr.csv   # tiene que empezar con 7e54155a3e0ddd0a
# El consolidado de la vara es D:/vrp-trabajo/temporales/s179-audit/main/latest_consolidado.csv (sha256 40b1b928c602b37f...).
