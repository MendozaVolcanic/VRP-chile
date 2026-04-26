#!/usr/bin/env bash
# 51_p31_ab/run_forenses.sh — Genera 8 forense JSONs (4 volcanes × 2 profiles)
# tras pull de los datos del workflow A/B P3.1.
#
# Uso (desde raíz del repo):
#   bash experiments/51_p31_ab/run_forenses.sh
#
# Después correr: python experiments/51_p31_ab/delta_report.py
set -e
cd "$(dirname "$0")/../.."

START=2026-04-12
END=2026-04-25
VOLCANOES=(Lascar Lastarria Tupungatito Chaiten)
PROFILES=(_p3_1_enabled _p3_1_disabled)
OUTDIR=experiments/51_p31_ab

for prof in "${PROFILES[@]}"; do
  for vol in "${VOLCANOES[@]}"; do
    json_in=data/${prof}/${vol}.json
    if [[ ! -f "$json_in" ]]; then
      echo "WARN: $json_in no existe (workflow A/B no terminó o falló para este caso). Skip."
      continue
    fi
    echo "=== Forense $prof / $vol ==="
    python experiments/forense_h17_replicable.py \
      --volcano "$vol" \
      --start "$START" --end "$END" \
      --records "$json_in" \
      --output-json "${OUTDIR}/forense_${prof}_${vol}.json" \
      --output-md "${OUTDIR}/forense_${prof}_${vol}.md"
  done
done

echo
echo "Listo. Ahora: python experiments/51_p31_ab/delta_report.py"
