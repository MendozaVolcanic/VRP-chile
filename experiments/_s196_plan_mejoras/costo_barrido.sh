#!/usr/bin/env bash
# Costo de referencia para el plan S196: minutos-job del barrido del laboratorio de S195 (paso 3 del plan S190).
# POR QUÉ: los costos del plan se dan contra una corrida real del mismo tipo, no estimados de memoria.
# Uso: bash experiments/_s196_plan_mejoras/costo_barrido.sh > experiments/_s196_plan_mejoras/salida_costo_barrido.txt
RUN=45114681532
gh api repos/MendozaVolcanic/VRP-chile/actions/runs/$RUN --jq '"run \(.id): \(.name); creado \(.created_at), terminado \(.updated_at), \(.conclusion)"'
gh api "repos/MendozaVolcanic/VRP-chile/actions/runs/$RUN/jobs?per_page=100" \
  --jq '[.jobs[] | select(.started_at and .completed_at) | ((.completed_at|fromdateiso8601)-(.started_at|fromdateiso8601))] | "jobs con duración: \(length); minutos-job: \(add/60|floor)"'
