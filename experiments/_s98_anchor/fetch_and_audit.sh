#!/usr/bin/env bash
# S98 — descarga los artifacts del reproc de validación, los ensambla en
# data/_s98_anchor/ y corre los dos audits A/B (espacial + ratio).
# Uso: bash experiments/_s98_anchor/fetch_and_audit.sh [RUN_ID]
set -euo pipefail
RUN_ID="${1:-26830238766}"
REPO="C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
cd "$REPO"

ART="experiments/_s98_anchor/_artifacts"
rm -rf "$ART"; mkdir -p "$ART"
echo ">>> descargando artifacts del run $RUN_ID ..."
gh run download "$RUN_ID" -D "$ART"

mkdir -p data/_s98_anchor
for d in "$ART"/s98-anchor-*/; do
  cp "$d"*.json data/_s98_anchor/ 2>/dev/null || echo "  (sin json en $d)"
done
echo ">>> data/_s98_anchor/:"
ls -1 data/_s98_anchor/ || true

echo ""
echo "========================= AUDIT ESPACIAL ========================="
PYTHONIOENCODING=utf-8 python experiments/_s98_anchor/audit_spatial.py
echo ""
echo "========================= AUDIT RATIO ============================"
PYTHONIOENCODING=utf-8 python experiments/_s98_anchor/audit_ratio.py
