# Cuenta menciones del PR de adopcion (#850), del squash 34cea39e y del tag de reversion en los textos que se leen primero.
# P1: si un documento no menciona ni #850 ni 34cea39e ni el tag, sale 0/0/0: no hay forma trazable de llegar al merge.
# P2 control positivo: el tag pre-s153-adopcion-k debe aparecer en FICHA, MISSION y CLAUDE.md (#850 lo escribio).
for f in CLAUDE.md docs/MISSION.md docs/MIROVA_DIVERGENCES.md docs/FICHA_SDA_VRP_CHILE.md docs/INDEX.md docs/META_RULES_S80.md pipeline/profiles/mirova_equivalent.yaml pipeline/profiles/experimental.yaml frontend/index.html frontend/cambio_detector.js; do
  printf "%-45s #850=%s 34cea39e=%s tag=%s 2026-10-18=%s\n" "$f" "$(grep -c '#850' $f)" "$(grep -c '34cea39e' $f)" "$(grep -c 'pre-s153-adopcion-k' $f)" "$(grep -c '2026-10-18' $f)"
done
