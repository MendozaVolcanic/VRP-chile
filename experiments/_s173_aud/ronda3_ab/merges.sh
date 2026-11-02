#!/bin/bash
# Simula ordenes de merge (merge commit y squash) y la reversion de B con git merge-tree, sin tocar refs.
set -u
cd D:/vrp-trabajo/worktrees/s173-moddA
M0=$(git rev-parse origin/main); A=$(git rev-parse claude/s172-modd-encendido); B=$(git rev-parse claude/s173-modd-flip); P=$(git rev-parse origin/claude/s172-sombra-34)
echo "main=$M0 A=$A B=$B P932=$P"
mt() { # base-opcional ours theirs -> imprime tree o CONFLICTO
  local out rc; out=$(git merge-tree --write-tree --name-only "$@" 2>&1); rc=$?
  if [ $rc -eq 0 ]; then echo "$out" | head -1; else echo "CONFLICTO:$(echo "$out" | sed -n '2,20p' | grep -v '^$' | tr '\n' ' ')"; return 1; fi; }
mc() { local t; t=$(mt "$1" "$2") || { echo "$t" >&2; return 1; }; git commit-tree "$t" -p "$1" -p "$2" -m "sim merge"; }
sq() { local t; t=$(mt "$1" "$2") || { echo "$t" >&2; return 1; }; git commit-tree "$t" -p "$1" -m "sim squash"; }
rev() { # revertir commit C (padre 1) sobre HEAD H
  mt --merge-base="$2" "$1" "$2^1"; }
for modo in merge squash; do
  f=mc; [ $modo = squash ] && f=sq
  for orden in "A B P" "A P B"; do
    H=$M0; ok=1; declare -A C=()
    for x in $orden; do
      case $x in A) r=$A;; B) r=$B;; P) r=$P;; esac
      n=$($f $H $r 2>/tmp/err_$$) || { echo "[$modo] orden $orden: $x CHOCA: $(cat /tmp/err_$$)"; ok=0; break; }
      C[$x]=$n; H=$n
    done
    [ $ok = 1 ] || continue
    echo "[$modo] orden $orden: limpio, arbol final $(git rev-parse $H^{tree})"
    rt=$(rev $H ${C[B]}) && echo "[$modo] orden $orden: revert de B LIMPIO, arbol $rt" || echo "[$modo] orden $orden: revert de B $rt"
    # el revert debe dejar lo mismo que main + A (+ P) sin B
    if [ "${rt#CONFLICTO}" = "$rt" ]; then
      H2=$M0; for x in $orden; do [ $x = B ] && continue; case $x in A) r=$A;; P) r=$P;; esac; H2=$($f $H2 $r 2>/dev/null); done
      d=$(git diff --stat $rt ${H2}^{tree} | tail -1); echo "   diff revert vs (orden sin B): ${d:-vacio}"
    fi
  done
done
