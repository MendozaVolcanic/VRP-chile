#!/usr/bin/env bash
# S160 (R13, hallazgo H-V1 de la auditoría de Mirova-v1): baja los dos CSV de MIROVA y regenera
# data/mirova/<Vol>.json. Es el cuerpo de los pasos de `.github/workflows/sync-mirova-csv.yml`
# movido tal cual a un archivo, para que el bucle de push lo pueda volver a correr sobre
# origin/main en vez de rebasar.
#
# POR QUÉ un archivo y no los pasos del workflow: si el push pierde la carrera, lo correcto es
# volver a origin/main y rehacer el trabajo, no mezclar el CSV como texto (`git pull --rebase
# -X theirs` dejaba filas dos veces o ninguna: commit 81dd25ce3, 822 duplicados y 163 llaves
# menos). Rehacer el trabajo exige correr la misma descarga y la misma regeneración dos veces,
# y dos copias del mismo código en el yml envejecen por separado (A102).
#
# Qué se baja y cómo se regenera no cambia respecto del workflow anterior (mismas URL, mismas
# defensas del OCR, mismo comando de rebuild, sólo cuando cambió el consolidado).
#
# Escribe en $GITHUB_OUTPUT (si existe): changed, ocr_changed, ocr_bad.
# Sale en rojo sólo si no se pudo bajar el consolidado (igual que antes, con `set -e`).
set -eu

salida() { echo "$1" >> "${GITHUB_OUTPUT:-/dev/null}"; }

# --- Consolidado (antes: pasos "Download fresh CSV" y "Check if changed") ---
curl -fsSL \
  "https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/monitoreo_satelital/registro_vrp_consolidado.csv" \
  -o latest_consolidado.csv.new || { echo "::error::no se pudo bajar el consolidado desde Mirova-v1"; exit 1; }

if cmp -s latest_consolidado.csv latest_consolidado.csv.new; then
  echo "CSV sin cambios, skip commit"
  changed=false
  rm latest_consolidado.csv.new
else
  mv latest_consolidado.csv.new latest_consolidado.csv
  changed=true
  echo "Rows: $(wc -l < latest_consolidado.csv)"
  echo "Latest date: $(awk -F, 'NR==2{print $2}' latest_consolidado.csv | head -c 16)"
fi
salida "changed=$changed"

# --- OCR (antes: paso "Download fresh OCR CSV from Mirova-v1") ---
# Mismas defensas que el consolidado (archivo temporal + cmp) más dos que el consolidado no
# tiene y que acá hacen falta: el OCR es la entrada de un rótulo que lee el geólogo, así que un
# archivo vacío o truncado es peor que un archivo viejo.
#
# POR QUE no aborta: este sync también trae el consolidado. Si el OCR viene mal, se salta el
# OCR, el consolidado igual se commitea, y el último paso del workflow deja la corrida en ROJO
# para que el fallo no pase en silencio (A87).
OCR=data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv
URL=https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/monitoreo_satelital/registro_vrp_ocr.csv
ocr_changed=false; bad=false
if ! curl -fsSL "$URL" -o "$OCR.new"; then
  echo "::error::no se pudo bajar el OCR desde Mirova-v1"
  bad=true
else
  nuevas=$(wc -l < "$OCR.new"); viejas=$(wc -l < "$OCR")
  cabecera=$(head -1 "$OCR.new")
  # Vacío / sin la cabecera esperada / más corto que lo que ya tenemos:
  # el registro de MIROVA sólo crece, así que encogerse es truncamiento.
  if [ "$nuevas" -lt 2 ] || ! printf '%s' "$cabecera" | grep -q "Fecha_Satelite_UTC" \
     || [ "$nuevas" -lt "$viejas" ]; then
    echo "::error::OCR invalido: lineas=$nuevas (previas=$viejas) cabecera='${cabecera:0:60}'"
    rm -f "$OCR.new"
    bad=true
  elif cmp -s "$OCR" "$OCR.new"; then
    echo "OCR sin cambios, skip commit"
    rm -f "$OCR.new"
  else
    mv "$OCR.new" "$OCR"
    ocr_changed=true
    echo "OCR rows: $nuevas (antes $viejas)"
    echo "OCR latest date: $(tail -1 "$OCR" | cut -d, -f2)"
  fi
fi
salida "ocr_changed=$ocr_changed"
salida "ocr_bad=$bad"

# --- JSON por volcán (antes: paso "Rebuild data/mirova/<Vol>.json from CSV (F54 fix)") ---
# F54/S77: el dashboard frontend NO lee latest_consolidado.csv directamente. Lee
# data/mirova/<Volcano>.json (records filtrados por volcán) generados por
# scripts/rebuild_mirova_from_consolidado.py. Sin esto, sync del CSV mantenía latest_consolidado
# fresh pero data/mirova/*.json quedaban congelados meses -> banner stale F49 aparecía aunque el
# sync funcionaba. Detectado S77 2026-05-25.
#
# Mapping JSON_stem -> "Volcan" en CSV (verificado 2026-05-25).
# 11 Tier A según volcanoes.yaml mirova_monitored=true.
if [ "$changed" = true ]; then
  for entry in \
    "PuyehueCordonCaulle|Puyehue-Cordon Caulle" \
    "Villarrica|Villarrica" \
    "Lascar|Lascar" \
    "Copahue|Copahue" \
    "NevadosDeChillan|Nevados de Chillan" \
    "Llaima|Llaima" \
    "Chaiten|Chaiten" \
    "PlanchonPeteroa|PlanchonPeteroa" \
    "Lastarria|Lastarria" \
    "Isluga|Isluga" \
    "Tupungatito|Tupungatito"
  do
    stem="${entry%%|*}"
    csvname="${entry##*|}"
    echo "Rebuilding data/mirova/${stem}.json from CSV (Volcan='${csvname}')"
    python scripts/rebuild_mirova_from_consolidado.py \
      "$stem" "$csvname" \
      --source latest_consolidado.csv \
      --ocr data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv \
      || echo "  WARN: rebuild $stem failed (continuing)"
  done
fi
exit 0
