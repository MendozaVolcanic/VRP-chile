#!/usr/bin/env bash
# S149. Despacha la cola de ventanas del pre-registro v3, DE A UNA. GitHub guarda un solo run pendiente
# por grupo de concurrencia: un tercer despacho desplazaria al que espera. Asi que se despacha el
# siguiente solo cuando hay a lo mas UN run vivo del workflow (uno corriendo, y el nuevo queda en cola).
# Un error de red se trata como "ocupado" y se reintenta: nunca se despacha a ciegas.
# Uso: bash despachar_cola.sh [indice_inicial]      Registro: despachos.log en esta carpeta.
set -u
cd "$(dirname "$0")"
WF=reproc-s146-ab-sin-test1.yml
ONCE='["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]'
LAS='["Lascar"]'
B=_s146_ab_sin_test1; F=_s147_ab_sin_test1_max; J=_s149_ab_sin_test1_b22; K=_s149_ab_sin_test1_b22_max; G=_s149_ab_sin_test1_gemelo
# nombre | start | end | vols | brazos | control
COLA=(
"marzo_lascar|2026-03-01|2026-03-31|$LAS|[\"$B\",\"$J\",\"$K\",\"$G\"]|$J"
"abril|2026-04-01|2026-04-30|$ONCE|[\"$B\",\"$F\"]|$B"
"abril_lascar|2026-04-01|2026-04-30|$LAS|[\"$J\",\"$K\",\"$G\"]|$J"
"mayo_lascar|2026-05-01|2026-05-31|$LAS|[\"$J\",\"$K\"]|$J"
"junio|2026-06-01|2026-06-30|$ONCE|[\"$B\",\"$F\"]|$B"
"junio_lascar|2026-06-01|2026-06-30|$LAS|[\"$J\",\"$K\",\"$G\"]|$J"
"julio|2026-07-01|2026-07-31|$ONCE|[\"$B\",\"$F\"]|$B"
"julio_gemelo|2026-07-01|2026-07-31|$LAS|[\"$G\"]|$G"
"agosto|2026-08-01|2026-08-27|$ONCE|[\"$B\",\"$F\"]|$B"
"agosto_gemelo|2026-08-01|2026-08-27|$LAS|[\"$G\"]|$G"
)
i=${1:-0}
log() { echo "$(date -u +%FT%TZ) $*" | tee -a despachos.log; }
vivos() {  # imprime el numero de runs vivos, o nada si la consulta fallo
  gh run list --workflow "$WF" -L 20 --json status -q '[.[]|select(.status!="completed")]|length' 2>/dev/null
}
log "inicio de la cola desde el indice $i de ${#COLA[@]}"
while [ "$i" -lt "${#COLA[@]}" ]; do
  n=$(vivos)
  if [ -z "$n" ]; then log "consulta fallida, reintento"; sleep 120; continue; fi
  if [ "$n" -gt 1 ]; then sleep 300; continue; fi
  IFS='|' read -r nombre ini fin vols brazos control <<< "${COLA[$i]}"
  if gh workflow run "$WF" --ref main -f preregistro_aprobado=si -f start="$ini" -f end="$fin" -f vols="$vols" -f brazos="$brazos" -f control="$control" >/dev/null 2>&1; then
    sleep 25
    id=$(gh run list --workflow "$WF" -L 1 --json databaseId -q '.[0].databaseId' 2>/dev/null)
    log "DESPACHADO [$i] $nombre $ini a $fin | control $control | run $id"
    i=$((i+1)); sleep 120
  else
    log "despacho de [$i] $nombre fallo, reintento"; sleep 120
  fi
done
log "cola terminada"
