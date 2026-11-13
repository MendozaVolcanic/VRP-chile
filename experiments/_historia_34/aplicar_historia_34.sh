#!/usr/bin/env bash
# Lo despacha .github/workflows/aplicar-reemplazo.yml (plan docs/superpowers/plans/2026-11-13-historia-34-volcanos-via.md, Tarea 6).
set -euo pipefail
python experiments/_historia_34/aplicar_historia_34.py   --informe experiments/_historia_34/aplicado/informe.json --aplicar
