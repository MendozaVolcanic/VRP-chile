#!/usr/bin/env bash
# S168 MOD-D fase 4: reproduce sin red el fallo del humo (run 41163955456, job `prueba`) y prueba el arreglo.
# Por qué falla: actions/checkout@v5, despachado desde un tag, baja el COMMIT del tag con
#   git fetch --no-tags --depth=1 origin +<sha_del_commit>:refs/tags/<tag>
# y deja refs/tags/<tag> apuntando al commit. El tag del candado es ANOTADO (su objeto no es el commit), así que el
# paso que vuelve a bajar refs/tags/<tag> sin --force cambiaría el tag local de objeto y git se niega:
# «would clobber existing tag». Con --force el tag local pasa a ser el del remoto, que es justo lo que se quiere
# comprobar: que el tag publicado apunta al commit que corre.
# Uso: bash repro_fetch_tag.sh <directorio_temporal_vacío>   (escribe todo ahí; no toca el repo)
set -u
T="${1:?directorio temporal}"
mkdir -p "$T" && cd "$T" || exit 9
rm -rf origen.git trabajo runner
export GIT_AUTHOR_NAME=x GIT_AUTHOR_EMAIL=x@x GIT_COMMITTER_NAME=x GIT_COMMITTER_EMAIL=x@x
git init -q trabajo && cd trabajo
mkdir -p experiments/_s157_prereg_d25 && echo "evaluador sellado" > experiments/_s157_prereg_d25/evaluar_d25.py
git add -A && git commit -q -m c1
git tag -a candado -m "tag anotado"
echo otro > otro.txt && git add otro.txt && git commit -q -m c2 && C2=$(git rev-parse HEAD)
git tag -a candado_movido -m "tag anotado sobre otro commit" "$C2"
cd .. && git clone -q --bare trabajo origen.git
SHA=$(git -C origen.git rev-parse 'candado^{commit}')
BLOB=$(git -C origen.git rev-parse 'candado:experiments/_s157_prereg_d25/evaluar_d25.py')

checkout() {  # imita actions/checkout@v5 con ref = tag y GITHUB_SHA = commit del tag
  rm -rf runner && git init -q runner && git -C runner remote add origin "$T/origen.git"
  git -C runner fetch -q --no-tags --prune --depth=1 origin "+$1:refs/tags/$2"
  git -C runner checkout -q "refs/tags/$2"
}
paso() {  # $1 = opciones de fetch; $2 = tag; reproduce las tres líneas del paso del workflow
  ( cd runner && git fetch $1 --depth 1 origin "refs/tags/$2:refs/tags/$2" 2>&1 | sed 's/^/    git: /' ; \
    [ "${PIPESTATUS[0]}" = 0 ] || exit 11
    test "$(git rev-parse "$2^{commit}")" = "$(git rev-parse HEAD)" || exit 12
    test "$(git hash-object experiments/_s157_prereg_d25/evaluar_d25.py)" = "$BLOB" || exit 13 )
}
informe() { case $1 in 0) echo "PASA";; 11) echo "FALLA en el fetch";; 12) echo "FALLA: el tag no es el commit";;
  13) echo "FALLA: el evaluador no es el sellado";; *) echo "código $1";; esac; }

echo "(1) paso VIEJO (sin --force), tag anotado, checkout como el runner:"
checkout "$SHA" candado; paso "" candado; r=$?; echo "  -> $(informe $r)"
echo "(2) paso NUEVO (--force), mismo caso:"
checkout "$SHA" candado; paso "--force" candado; r=$?; echo "  -> $(informe $r)"
echo "(3a) paso NUEVO, el tag publicado apunta a OTRO commit que el que corre:"
checkout "$SHA" candado_movido; paso "--force" candado_movido; r=$?; echo "  -> $(informe $r)"
echo "(3b) paso NUEVO, tag correcto pero el evaluador del árbol no es el sellado:"
checkout "$SHA" candado; echo "evaluador cambiado" > runner/experiments/_s157_prereg_d25/evaluar_d25.py
paso "--force" candado; r=$?; echo "  -> $(informe $r)"
echo "git $(git --version | cut -d' ' -f3)"
