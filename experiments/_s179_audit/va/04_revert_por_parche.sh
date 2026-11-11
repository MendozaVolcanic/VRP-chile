#!/usr/bin/env bash
# VA-04 (afirmación 403): ¿choca revertir el PR B (#934, merge 499935c37) sobre main 438a60a1e y sobre las ramas de B1/B2?
# Camino distinto al del auditor (merge-tree): se aplica AL REVÉS el parche de B (diff entre el primer padre y el merge)
# sobre un índice temporal cargado con el destino, archivo por archivo, sin --3way. Un archivo cuyo parche inverso no
# entra es un choque (o al menos un archivo que una persona tiene que resolver a mano). No escribe objetos ni toca el
# checkout: índice temporal en la carpeta del verificador, `git apply --cached --check`.
# Preguntas del instrumento: (1) si el revert chocara, se vería: lista los archivos que no aplican. (2) instrumento
# muerto: el control (destino = el propio merge) tiene que dar 0 archivos que no aplican; y un destino distinto tiene que
# dar algo distinto de 0 si los archivos de B cambiaron después.
export MSYS_NO_PATHCONV=1
R="C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
T="D:/vrp-trabajo/temporales/s179-audit/va/idx"; mkdir -p "$T"
cd "$R" || exit 1
M=499935c37
P1=$(git rev-parse $M^1)
archivos=$(git diff --name-only $P1 $M)
echo "archivos que toca B (diff $P1..$M): $(echo "$archivos" | wc -l)"
for destino in $M 438a60a1e origin/claude/s177-b1-v375 origin/claude/s178-b2-sobre-b1; do
  export GIT_INDEX_FILE="$T/index_$(git rev-parse --short=9 $destino)"
  git read-tree $destino
  malos=0; lista=""
  for f in $archivos; do
    if ! git diff --binary $P1 $M -- "$f" | git apply -R --cached --check >/dev/null 2>&1; then
      malos=$((malos+1)); lista="$lista $f"
    fi
  done
  cambiados=$(git diff --name-only $M $destino -- $archivos | wc -l)
  echo "=== destino $destino ($(git rev-parse --short=9 $destino)): archivos de B cambiados después del merge: $cambiados | parche inverso NO aplica en: $malos"
  for f in $lista; do echo "   $f"; done
  echo "   flag MODIS en el destino: $(git show $destino:pipeline/profiles/mirova_equivalent.yaml | grep -n 'enable_modis_codigo_mirova' || echo 'sin la clave')"
  if git diff $P1 $M -- pipeline/profiles/mirova_equivalent.yaml | git apply -R --cached --check >/dev/null 2>&1; then
    echo "   el hunk del YAML (el flag) se revierte limpio: SI"
  else
    echo "   el hunk del YAML (el flag) se revierte limpio: NO"
  fi
  rm -f "$GIT_INDEX_FILE"
done
