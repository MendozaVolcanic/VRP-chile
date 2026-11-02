#!/bin/bash
# uso: correr.sh <worktree> <etiqueta>; corre los archivos de la lista que existen en ese arbol
S="/c/Users/nmend/AppData/Local/Temp/claude/C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile/d7a1e8f0-95ba-454a-a8a3-73d7d75d9816/scratchpad"
cd "$1"; libre=$(df -k /d | tail -1 | awk '{print $4}'); [ "$libre" -lt 3145728 ] && { echo "PARADA: D bajo 3 GB"; exit 9; }
fs=$(while read f; do [ -f "$f" ] && echo "$f"; done < "$S/lista_pruebas.txt")
echo "[$2] HEAD $(git rev-parse --short HEAD) arbol $(git write-tree 2>/dev/null) archivos $(echo "$fs" | wc -l)"
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider -q $fs 2>&1 | tail -6
