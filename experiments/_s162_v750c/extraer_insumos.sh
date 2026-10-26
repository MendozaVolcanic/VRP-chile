#!/usr/bin/env bash
# Extrae, sin tocar el árbol de trabajo, los insumos de la ablación V750-C desde la rama s159-pruebas.
# Uso: bash extraer_insumos.sh <carpeta_destino>   (fuera del repo; no se commitea)
set -euo pipefail
DEST="$1"
REF=origin/s159-pruebas
mkdir -p "$DEST/n" "$DEST/oraculo_r2"
for f in $(git ls-tree -r --name-only "$REF" experiments/_s159/n | grep -E '(objetivos_n|objetivos_censo)\.json$|resultados_[0-9]+\.json$'); do
  rel="${f#experiments/_s159/n/}"
  mkdir -p "$DEST/n/$(dirname "$rel")"
  git show "$REF:$f" > "$DEST/n/$rel"
done
git show "$REF:experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py" > "$DEST/oraculo_r2/mirova_v750_r2.py"
git rev-parse "$REF" > "$DEST/REF_SHA.txt"
echo "insumos en $DEST (ref $(cat "$DEST/REF_SHA.txt"))"
