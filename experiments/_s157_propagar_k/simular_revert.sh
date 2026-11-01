# Simula `git revert 34cea39e` sobre HEAD sin tocar el arbol (git merge-tree, solo escribe objetos).
# P1: si la reversion fuera limpia, merge-tree sale con 0 y sin lineas CONFLICT.
# P2: control: el arbol resultante debe traer el YAML de produccion con los tres flags de C0 (prueba que la
#     simulacion si revierte algo y no es un no-op).
git merge-tree --write-tree --name-only --merge-base 34cea39e HEAD 34cea39e~1
