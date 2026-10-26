#!/usr/bin/env bash
# ============================================================================
# Orquestador nocturno S124 — encadena los reprocesos del plan y deja los
# analisis YA CALCULADOS para cuando Nicolas despierte.
#
# POR QUE existe: el grupo de concurrencia `reproc-chunked` admite 1 corriendo
# + 1 pendiente; despachar un tercero EXPULSA al pendiente (paso 2 veces en
# S124). Este script serializa: lanza, ESPERA a que cierre, analiza, lanza el
# siguiente. Nada de despachar a ciegas.
#
# Plan: docs/superpowers/plans/2026-08-27-plan-reprocesos-s124-s125.md
#   Tarea 2  -> brazo B (grilla + kernel global) — el juez es Tupungatito
#   Tarea 0  -> NdC v2 REHECHO (el anterior salio con el merge roto)
#
# NO toca mirova_equivalent ni el cron (A45). Todo va a data_subdir aislado.
# Salida: docs/S124_NOCHE_RESULTADOS.md + este log.
# ============================================================================
set -uo pipefail
cd "$(dirname "$0")/.."

LOG="docs/S124_NOCHE_RESULTADOS.md"
VOLS="Lascar,Isluga,Lastarria,Llaima,Copahue,Tupungatito,NevadosDeChillan,Villarrica,Chaiten,PlanchonPeteroa,PuyehueCordonCaulle"
MAX_ESPERA=$((5 * 60 * 60 / 120))   # 5 h en ciclos de 120 s, techo de seguridad

log() { echo -e "$*" | tee -a "$LOG"; }

esperar_run() {   # $1 = run id, $2 = nombre legible
  local id="$1" nom="$2" i=0 st
  while [ $i -lt $MAX_ESPERA ]; do
    st=$(gh run view "$id" --json status -q .status 2>/dev/null || echo "?")
    if [ "$st" = "completed" ]; then
      local conc
      conc=$(gh run view "$id" --json conclusion -q .conclusion)
      log "  [$(date -u +%H:%M)] $nom -> $conc"
      [ "$conc" = "success" ] && return 0 || return 1
    fi
    sleep 120
    i=$((i + 1))
  done
  log "  [$(date -u +%H:%M)] $nom -> TIMEOUT del orquestador (5 h)"
  return 1
}

lanzar() {   # $1=perfil $2=vols $3=inicio $4=fin $5=max_days ; imprime run id
  gh workflow run reproc-chunked.yml --ref main \
    -f profile="$1" -f volcanoes="$2" -f start="$3" -f end="$4" -f max_days="$5" >/dev/null 2>&1
  sleep 25
  gh run list --workflow=reproc-chunked.yml --limit 1 --json databaseId -q '.[0].databaseId'
}

log "\n\n# Resultados de la noche — $(date -u +'%Y-%m-%d %H:%M UTC')\n"
log "Orquestador: \`scripts/orquestar_noche_s124.sh\`. Plan: \`docs/superpowers/plans/2026-08-27-plan-reprocesos-s124-s125.md\`.\n"

# ── 1) BRAZO B ──────────────────────────────────────────────────────────────
log "## Brazo B — grilla UTM + kernel de vecinos global (la hipotesis central)\n"
log "Criterio pre-registrado en \`pipeline/profiles/_f70_b.yaml\` (escrito antes de correr, A66)."
RUN_B=$(lanzar "_f70_b" "$VOLS" "2026-06-25" "2026-08-24" "37")
log "  [$(date -u +%H:%M)] lanzado run $RUN_B — https://github.com/MendozaVolcanic/VRP-chile/actions/runs/$RUN_B"

if esperar_run "$RUN_B" "brazo B"; then
  git pull --rebase -q 2>/dev/null || git pull -q 2>/dev/null
  log "\n### Lectura apareada (brazo B vs control)\n"
  log '```'
  python experiments/_s124_f70/03_leer_brazo.py _f70_b 2>&1 | tee -a "$LOG" >/dev/null
  python experiments/_s124_f70/03_leer_brazo.py _f70_b 2>&1 >> "$LOG"
  log '```'
  log "\n### Los 4 brazos, ratio mediano por volcan\n"
  log '```'
  python experiments/_s124_f70/04_tabla_brazos.py 2>&1 >> "$LOG" || echo "  (tabla no disponible)" >> "$LOG"
  log '```'
else
  log "\n  El brazo B no cerro bien: revisar el run antes de leer nada.\n"
fi

# ── 2) NdC v2 REHECHO ───────────────────────────────────────────────────────
log "\n## NdC experimental v2 (rehecho — el anterior salio con el merge roto)\n"
log "El merge por trozos resucitaba meses sin reprocesar (fix commit del 27-ago)."
RUN_N=$(lanzar "experimental_ndc_focus" "NevadosDeChillan" "2026-05-01" "2026-08-27" "30")
log "  [$(date -u +%H:%M)] lanzado run $RUN_N — https://github.com/MendozaVolcanic/VRP-chile/actions/runs/$RUN_N"

if esperar_run "$RUN_N" "NdC v2"; then
  git pull --rebase -q 2>/dev/null || git pull -q 2>/dev/null
  log "\n### Se reproceso de verdad esta vez? (el test que destapo el bug)\n"
  log '```'
  python experiments/_s124_ndc_focus/05_verificar_reproceso.py 2>&1 >> "$LOG"
  log '```'
  log "\n### Figuras regeneradas con la serie completa\n"
  python experiments/_s124_ndc_focus/plot_simple.py >> "$LOG" 2>&1
  python experiments/_s124_ndc_focus/plot_mapa.py >> "$LOG" 2>&1
  git add experiments/_s124_ndc_focus/*.png "$LOG" 2>/dev/null
  git commit -q -m "data(s124): figuras NdC con la serie v2 completa (orquestador nocturno)" 2>/dev/null
  git pull --rebase -q 2>/dev/null; git push -q 2>/dev/null
else
  log "\n  El reproceso de NdC no cerro bien: revisar el run.\n"
fi

# ── 3) Tarea 3d — origen de la grilla de MIROVA por volcan (read-only)
log "
## Origen de la grilla de MIROVA, volcan por volcan (tarea 3d)
"
log "De sus GeoTIFF. Offset grande = celdas desalineadas con nuestra ancla:"
log "mismo tamano de celda, distinta particion del terreno, otros vecindarios."
log '```'
python experiments/_s124_cuantizacion/02_origen_grilla_por_volcan.py >> "$LOG" 2>&1
log '```'

log "\n---\n**Orquestador terminado $(date -u +'%H:%M UTC').** Pendiente de decision humana: el veredicto F70 (tarea 2.4 del plan) — nada se promueve sin confirmacion explicita (A45).\n"
