#!/usr/bin/env bash
# Simulación de órdenes de merge A, B y #932 (y reversión de B) con git merge-tree sobre ÁRBOLES.
# No crea commits, ramas ni tags: sólo objetos tree sueltos en la base de objetos.
#
# Pregunta 1 (si lo medido estuviera roto, ¿se vería?): un conflicto textual da rc=1 y lista de conflictos;
#   un merge que "pierde" el cambio de una rama se ve comparando el árbol final contra el árbol esperado
#   (comparación de árboles al final y diff de nombres).
# Pregunta 2 (si el instrumento estuviera muerto, ¿se vería distinto?): control positivo al final: un merge
#   forzado a conflicto (B contra una versión de main con el mismo archivo editado distinto) debe dar rc=1.
set -u
cd "/c/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
t() { git rev-parse "$1^{tree}"; }
MAIN=a3c5a9b49; BASEAB=d3cd0b2ae; A=0a0dae344; B=c9525f994; P=28183712a; BASEP=$(git merge-base $MAIN $P)
TM=$(t $MAIN); TBA=$(t $BASEAB); TA=$(t $A); TB=$(t $B); TP=$(t $P); TBP=$(t $BASEP)
echo "main=$MAIN tree $TM | base AB=$BASEAB | A=$A | B=$B | #932=$P (base $BASEP)"
mt() { # base ours theirs etiqueta
  local out rc
  out=$(git merge-tree --write-tree --name-only --merge-base="$1" "$2" "$3" 2>&1); rc=$?
  local tree=$(echo "$out" | head -1)
  echo "  [$4] rc=$rc tree=$tree" >&2
  if [ $rc -ne 0 ]; then echo "$out" | sed 's/^/      /' >&2; fi
  echo "$tree"
}
echo "== Estrategia merge commit (la base natural de cada merge)"
echo "-- orden A -> B -> #932"
X1=$(mt $TBA $TM $TA "main+A (base d3cd)")
X2=$(mt $TA $X1 $TB "+B (base A, A ancestro de B)")
X3=$(mt $TBP $X2 $TP "+#932 (base 14fb)")
R1=$(mt $X2 $X3 $X1 "revert B tras #932: base=estado con B, theirs=estado previo a B")
echo "-- orden A -> #932 -> B"
Y1=$X1
Y2=$(mt $TBP $Y1 $TP "+#932")
Y3=$(mt $TA $Y2 $TB "+B (base A)")
R2=$(mt $Y3 $Y3 $Y2 "revert B inmediato")
echo "-- orden #932 -> A -> B"
Z1=$(mt $TBP $TM $TP "main+#932")
Z2=$(mt $TBA $Z1 $TA "+A (base d3cd)")
Z3=$(mt $TA $Z2 $TB "+B (base A)")
R3=$(mt $Z3 $Z3 $Z2 "revert B inmediato")
echo "== Estrategia squash (GitHub: base = merge-base(main del día, rama) = rama base original)"
echo "-- orden A -> B -> #932 (B sin rebasar sobre el squash de A)"
S1=$(mt $TBA $TM $TA "squash A")
S2=$(mt $TBA $S1 $TB "squash B (base d3cd, A ya en main como squash)")
S3=$(mt $TBP $S2 $TP "squash #932")
RS1=$(mt $S2 $S3 $S1 "revert squash B tras #932")
echo "-- orden #932 -> A -> B (squash)"
U1=$(mt $TBP $TM $TP "squash #932")
U2=$(mt $TBA $U1 $TA "squash A")
U3=$(mt $TBA $U2 $TB "squash B")
RU=$(mt $U3 $U3 $U2 "revert squash B inmediato")
echo "-- orden A -> #932 -> B (squash)"
V2=$(mt $TBP $S1 $TP "squash #932 tras A")
V3=$(mt $TBA $V2 $TB "squash B")
echo "== Igualdad de árboles finales (los tres órdenes y dos estrategias deberían dar el mismo árbol)"
echo "  X3=$X3"; echo "  Y3=$Y3"; echo "  Z3=$Z3"; echo "  S3=$S3"; echo "  U3=$U3"; echo "  V3=$V3"
echo "== Reversión de B: ¿queda exactamente main+A+#932 (sin B)?"
echo "  esperado (main+A+#932) Y2=$Y2"
echo "  R1 (merge commit, revert tras #932) = $R1  $( [ "$R1" = "$Y2" ] && echo IGUAL || echo DISTINTO)"
echo "  RS1 (squash, revert tras #932)       = $RS1  $( [ "$RS1" = "$Y2" ] && echo IGUAL || echo DISTINTO)"
echo "  R2 = $R2 R3 = $R3 RU = $RU (deben ser = $Y2 / $Z2 / $U2)"
for pair in "R1 $R1 $Y2" "RS1 $RS1 $Y2"; do set -- $pair; if [ "$2" != "$3" ]; then echo "  diff $1 vs esperado:"; git diff --stat $3 $2 | tail -5; fi; done
echo "== Árbol combinado exportado para pruebas"
echo "COMBO_ABP=$X3"; echo "COMBO_AP=$Y2"; echo "COMBO_AB=$X2"; echo "COMBO_A=$X1"
echo "== Control positivo del instrumento: forzar conflicto (B contra un árbol con mirova_equivalent.yaml distinto)"
# Árbol de control: tomar main y reemplazar mirova_equivalent.yaml por su versión de B con una línea cambiada.
TMP=$(mktemp -d)
git show $B:pipeline/profiles/mirova_equivalent.yaml | sed 's/enable_modis_codigo_mirova: true/enable_modis_codigo_mirova: false  # control/' > $TMP/me.yaml
BLOB=$(git hash-object -w $TMP/me.yaml)
IDX=$TMP/idx; GIT_INDEX_FILE=$IDX git read-tree $X1; GIT_INDEX_FILE=$IDX git update-index --cacheinfo 100644,$BLOB,pipeline/profiles/mirova_equivalent.yaml; TC=$(GIT_INDEX_FILE=$IDX git write-tree)
mt $TA $TC $TB "CONTROL: B sobre main+A con el flag editado distinto (debe dar rc=1)" >/dev/null
rm -rf $TMP
