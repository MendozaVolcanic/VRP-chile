#!/usr/bin/env bash
# Simula `git revert -m 1 499935c37` (el merge del PR B, #934, que enciende la via de MODIS) sin tocar el checkout:
# git merge-tree con base = el merge, "ours" = la rama destino, "theirs" = el primer padre del merge.
# Los objetos nuevos van a un directorio propio (GIT_OBJECT_DIRECTORY), no al .git del repo.
# Preguntas del instrumento: (1) si el revert chocara, se veria: lista los CONFLICT. (2) instrumento muerto: el control
# (revert sobre el propio merge) tiene que salir limpio (exit 0) y los destinos reales no.
export MSYS_NO_PATHCONV=1
R="C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
T="D:/vrp-trabajo/temporales/s179-audit/a/objs"; mkdir -p "$T"
export GIT_OBJECT_DIRECTORY="$T"
export GIT_ALTERNATE_OBJECT_DIRECTORIES="$R/.git/objects"
cd "$R" || exit 1
M=499935c37
for destino in $M 438a60a1e origin/claude/s177-b1-v375 origin/claude/s178-b2-sobre-b1; do
  echo "=== revert de #934 sobre $destino ($(git rev-parse --short=9 $destino))"
  out=$(git merge-tree --write-tree --name-only --merge-base=$M $destino $M^1 2>&1); rc=$?
  echo "exit=$rc | conflictos: $(echo "$out" | grep -c '^CONFLICT')"
  echo "$out" | grep '^CONFLICT' | cut -c1-150
  arbol=$(echo "$out" | head -1)
  echo "flags de via en mirova_equivalent.yaml del arbol resultante:"
  git show $arbol:pipeline/profiles/mirova_equivalent.yaml | grep -n "codigo_mirova:" || echo "  (ninguna linea enable_*_codigo_mirova: el flag de MODIS queda en su valor por defecto, False)"
done
