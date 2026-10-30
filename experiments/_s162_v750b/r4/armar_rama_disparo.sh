#!/usr/bin/env bash
# S162 V750-B, R4 (2026-11-03): arma, SIN checkout y SIN push, el commit de la rama de disparo.
#
# POR QUÉ. El probe corre con el código de main del día (probe_n.py y la población de experiments/_s159/n viven en main)
# y con la carpeta de V750-B tal como quedó sellada (tag s167-v750b-adenda3-sellada, con las adendas 1, 2 y 3). La rama
# de disparo es exactamente eso, más los objetivos generados ese día y la copia del workflow en .github/workflows/ con
# OBJETIVOS apuntando a la lista del run (adenda 2 §3, punto 2). Armarla con un índice aparte evita tocar el árbol de
# trabajo, donde corre el medidor de V750-A, y deja los archivos generados byte a byte (--no-filters), así que sus
# sha256 son los que imprimió el generador. El push a s162-v750b-disparo dispara el run: lo hace la coordinadora.
#
# Uso: armar_rama_disparo.sh <arbol con las salidas del generador> <commit base de main> <tag sellado> <rama local>
set -euo pipefail
ARBOL=$1; BASE=$2; TAG=$3; RAMA=$4
V=experiments/_s162_v750b
GENERADOS=("$V/objetivos_v750b.json" "$V/sin_granulo_v750b.json" "$V/poblacion_completa.json"
           "$V/adenda2/objetivos_supl_v750b.json" "$V/adenda2/sin_granulo_supl_v750b.json"
           "$V/adenda2/objetivos_run_v750b.json" "$V/adenda2/poblacion_supl.json")
WF=.github/workflows/probe-s162-v750b.yml
if git rev-parse --verify --quiet "refs/heads/$RAMA" >/dev/null; then echo "la rama $RAMA ya existe: no se pisa"; exit 2; fi
for f in "${GENERADOS[@]}"; do [ -f "$ARBOL/$f" ] || { echo "falta $ARBOL/$f"; exit 2; }; done
TMPD=$(mktemp -d)
export GIT_INDEX_FILE="$TMPD/indice"
git read-tree "$BASE"
# la carpeta de V750-B del tag sellado, blob por blob (reemplaza lo que main tenga ahí)
git ls-files -z -- "$V" | xargs -0 -r git update-index --force-remove --
git ls-tree -r "$TAG" -- "$V" | git update-index --index-info
for f in "${GENERADOS[@]}"; do
  sha=$(git hash-object -w --no-filters "$ARBOL/$f")
  git update-index --add --cacheinfo "100644,$sha,$f"
done
# el workflow: copia del sellado con OBJETIVOS en la lista del run (la única línea que cambia)
git show "$TAG:$V/probe-s162-v750b.yml" > "$TMPD/wf.yml"
n=$(grep -c '^  OBJETIVOS: "experiments/_s162_v750b/objetivos_v750b.json"$' "$TMPD/wf.yml" || true)
[ "$n" = "1" ] || { echo "la línea OBJETIVOS del workflow no calza ($n)"; exit 2; }
sed -i 's#^  OBJETIVOS: "experiments/_s162_v750b/objetivos_v750b.json"$#  OBJETIVOS: "experiments/_s162_v750b/adenda2/objetivos_run_v750b.json"#' "$TMPD/wf.yml"
sha=$(git hash-object -w --no-filters "$TMPD/wf.yml")
git update-index --add --cacheinfo "100644,$sha,$WF"
ARBOLGIT=$(git write-tree)
C=$(git commit-tree "$ARBOLGIT" -p "$BASE" -m "S162 V750-B: rama de disparo (main $BASE, carpeta de V750-B de $TAG, objetivos generados, workflow con la lista del run)")
git branch "$RAMA" "$C"
rm -rf "$TMPD"
echo "rama $RAMA -> $C (no empujada)"
for f in "${GENERADOS[@]}"; do echo "  $(git show "$C:$f" | sha256sum | cut -c1-64)  $f"; done
echo "  workflow: $(git show "$C:$WF" | grep '^  OBJETIVOS')"
echo "  diff contra main fuera de V750-B y del workflow (tiene que estar vacío):"
git diff --name-only "$BASE" "$C" | grep -v "^$V/" | grep -v "^$WF$" || echo "    (vacío)"
