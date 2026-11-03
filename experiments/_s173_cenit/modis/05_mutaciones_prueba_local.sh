#!/usr/bin/env bash
# 05 (S173): ¿la prueba local del arnés atrapa un arnés roto? Copia experiments/_s173_cenit_modis a _s173_mut dentro del
# worktree, aplica UNA mutación por vez a piezas.py y cuenta las FALLA de probar_local.py. Una mutación con 0 fallas
# es un hueco de la prueba (se informa, no se esconde). Uso: bash 05_mutaciones_prueba_local.sh <worktree>
WT="$1"; cd "$WT/experiments" || exit 1; export PYTHONIOENCODING=utf-8
for m in m0_sin_mutar m1_patch_ignora_brazo m2_anillo_desde_0km m3_caja_nativa_todo_sensible m4_X2_no_dobla; do
  rm -rf _s173_mut; cp -r _s173_cenit_modis _s173_mut
  python - "$m" <<'PY'
import sys
m = sys.argv[1]; p = '_s173_mut/piezas.py'; s = open(p, encoding='utf-8').read()
rep = {'m1_patch_ignora_brazo': ('        if brazo == "V0":\n', '        brazo = "V0"\n        if brazo == "V0":\n'),
       'm2_anillo_desde_0km': ('sel = (dist_km >= BG_INNER_KM)', 'sel = (dist_km >= 0.0)'),
       'm3_caja_nativa_todo_sensible': ('    box = np.full(lat.shape, np.nan)\n    box[dentro]', '    box = np.full(lat.shape, 2.0)\n    box[dentro]'),
       'm4_X2_no_dobla': ('coef=2 * coef', 'coef=1.999 * coef')}
if m in rep:
    a, b = rep[m]; assert a in s, m; s = s.replace(a, b, 1)
open(p, 'w', encoding='utf-8').write(s)
PY
  out=$(python -I _s173_mut/probar_local.py 2>&1)
  echo "== $m: $(echo "$out" | grep -c '^FALLA') fallas"; echo "$out" | grep '^FALLA' | sed 's/^/     /'
done
rm -rf _s173_mut
