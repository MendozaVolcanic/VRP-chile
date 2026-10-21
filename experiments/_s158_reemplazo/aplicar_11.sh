#!/usr/bin/env bash
# S158, tarea 1.24 (d): aplica el reemplazo del historico con K en los 11 Tier A y aparta los residuos C0.
# Aprobado por Nicolas el 2026-10-21 (tasks/LOOP_OBJETIVOS.md, entrada S158). Correr desde la raiz del repo, sobre un
# arbol al dia con origin/main y con el NRT quieto. Se detiene al primer error: un volcan que el script rehusa
# (codigo 2) deja el arbol sin commitear para revisarlo.
set -euo pipefail
DESDE=2025-02-15
HASTA=2026-09-17
PERFIL=_s154_reproc_k_historico
OUT=experiments/_s158_reemplazo/aplicado
mkdir -p "$OUT"
for V in NevadosDeChillan Chaiten Copahue Isluga Lascar Lastarria Llaima PlanchonPeteroa PuyehueCordonCaulle \
         Tupungatito Villarrica; do
  python scripts/reemplazar_ventana_reproceso.py --operacional "data/mirova_equivalent/$V.json" \
    --reproceso "data/$PERFIL/$V.json" --desde "$DESDE" --hasta "$HASTA" --perfil-esperado "$PERFIL" \
    --informe "$OUT/informe_$V.json" --aplicar
done
python experiments/_s158_reemplazo/apartar_c0.py --desde "$DESDE" --aplicar | tee "$OUT/apartar_c0.txt"
