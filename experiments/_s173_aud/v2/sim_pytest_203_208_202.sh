#!/usr/bin/env bash
# V2: pruebas sobre el árbol combinado (201, 205), sobre el revert (X1), simulación del squash (203), de la línea vecina
# (208) y del merge de #932 con la rama de la ROI de V750-B (202). Todo en el worktree propio s173-v2-merge.
set -u
export MSYS_NO_PATHCONV=1 PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
W=/d/vrp-trabajo/worktrees/s173-v2-merge
O=/d/vrp-trabajo/temporales/s173_aud/v2
cd "$W" || exit 1
PT="python -m pytest -p no:cacheprovider -q --no-header -rN"

echo "##### 1. pytest sobre A+B+#932 (orden ABS, $(git rev-parse --short v2_orden_ABS))"
git checkout -q --detach v2_orden_ABS
$PT tests/test_guard_modis_codigo_mirova_encendido_s172.py 2>&1 | tail -8
echo "--- resto de pruebas de S172 + sombra 34 + vía MODIS"
$PT tests/test_auto_audit_via_modis_s172.py tests/test_sombra_34_s172.py tests/test_guardia_k_modis_s172.py \
    tests/test_vigilancia_guardia_modis_s172.py tests/test_guard_pyproj_vias_s172.py \
    tests/test_cambio_detector_via_modis_s172.py tests/test_vigilancia_sombra_via_modis_s172.py \
    tests/test_tablero_ancla_codigo_mirova_s172.py tests/test_sombra_codigo_mirova_s167.py \
    tests/test_mirova_modis_codigo_s164.py tests/test_guard_adopcion_k_s153.py tests/test_experimental_congelado_s150.py \
    tests/test_guard_laboratorio_no_mas_ciego_s147.py 2>&1 | tail -6

echo; echo "##### 2. pytest sobre el revert de B (= main+A+#932, $(git rev-parse --short v2_revertB))"
git checkout -q --detach v2_revertB
ls tests/test_guard_modis_codigo_mirova_encendido_s172.py 2>/dev/null || echo "(el guard de B no existe en el revert, esperado)"
$PT tests/test_auto_audit_via_modis_s172.py tests/test_sombra_34_s172.py tests/test_guardia_k_modis_s172.py \
    tests/test_vigilancia_guardia_modis_s172.py tests/test_guard_pyproj_vias_s172.py \
    tests/test_cambio_detector_via_modis_s172.py tests/test_sombra_codigo_mirova_s167.py \
    tests/test_mirova_modis_codigo_s164.py tests/test_guard_adopcion_k_s153.py tests/test_experimental_congelado_s150.py \
    tests/test_guard_laboratorio_no_mas_ciego_s147.py tests/test_vigilancia_sombra_s156.py tests/test_process_modis_core.py 2>&1 | tail -6
echo "--- flag de producción en el revert (A89)"
VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print('ENABLE_MODIS_CODIGO_MIROVA =', p.ENABLE_MODIS_CODIGO_MIROVA)" 2>/dev/null | tail -1
git checkout -q --detach v2_orden_ABS
echo "--- flag de producción en A+B+#932 (A89)"
VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print('ENABLE_MODIS_CODIGO_MIROVA =', p.ENABLE_MODIS_CODIGO_MIROVA)" 2>/dev/null | tail -1

echo; echo "##### 3. (203) squash de A y luego squash de B sin rebase"
git checkout -q --detach a3c5a9b49
git merge --squash 0a0dae344 >/dev/null 2>&1 && git commit -q -m "squash A" && echo "squash A: ok $(git rev-parse --short HEAD)"
if git merge --squash c9525f994 >/dev/null 2>&1; then echo "squash B: LIMPIO"; git reset -q --hard HEAD; else echo "squash B: CONFLICTO en:"; git diff --name-only --diff-filter=U; git reset -q --hard HEAD; fi
echo "--- control: merge commit de B sobre squash(A)"
if git merge --no-ff --no-edit -m "merge B" c9525f994 >/dev/null 2>&1; then echo "merge commit B sobre squash A: LIMPIO"; else echo "merge commit B sobre squash A: CONFLICTO"; git diff --name-only --diff-filter=U; git merge --abort; fi

echo; echo "##### 4. (208) revert de B tras un commit que toca la línea vecina del flag"
git checkout -q --detach v2_orden_ABS
MB=$(git log --format=%H --grep='^merge B$' -1)
grep -n 'enable_modis_dist_desde_crater\|enable_modis_codigo_mirova: true' pipeline/profiles/mirova_equivalent.yaml
sed -i 's/^  enable_modis_dist_desde_crater: false /  enable_modis_dist_desde_crater: true  /' pipeline/profiles/mirova_equivalent.yaml
git commit -q -am "otro PR: toca la linea vecina (enable_modis_dist_desde_crater)" && echo "commit vecino: $(git rev-parse --short HEAD)"
if git revert --no-edit -m 1 $MB >/dev/null 2>&1; then echo "revert de B con línea vecina tocada: LIMPIO"; else echo "revert de B con línea vecina tocada: CONFLICTO en:"; git diff --name-only --diff-filter=U; git revert --abort; fi
echo "--- control: un commit que toca una línea LEJANA (background.inner_km) y luego el revert"
git checkout -q --detach v2_orden_ABS
sed -i 's/^  inner_km: 5.0$/  inner_km: 5.0 # comentario/' pipeline/profiles/mirova_equivalent.yaml
git commit -q -am "otro PR: linea lejana" && echo "commit lejano: $(git rev-parse --short HEAD)"
if git revert --no-edit -m 1 $MB >/dev/null 2>&1; then echo "revert de B con línea lejana tocada: LIMPIO"; else echo "revert de B con línea lejana tocada: CONFLICTO en:"; git diff --name-only --diff-filter=U; git revert --abort; fi

echo; echo "##### 5. (202) #932 + rama de la ROI de V750-B (cd5aa300c)"
git checkout -q --detach cd5aa300c
echo "--- control: la prueba en la rama de la ROI sola"
$PT tests/test_roi_v750b_variantes_s169.py 2>&1 | tail -3
git checkout -q --detach 28183712a
if git merge --no-ff --no-edit -m "merge roi" cd5aa300c >/dev/null 2>&1; then
  echo "merge #932 + roi: LIMPIO $(git rev-parse --short HEAD)"
  $PT tests/test_roi_v750b_variantes_s169.py 2>&1 | tail -3
  echo "--- cuáles fallan"; $PT tests/test_roi_v750b_variantes_s169.py 2>&1 | grep -E '^(FAILED|ERROR)' | sed 's/ - .*//' | head -40
  echo "--- entradas en grillas_mirova.yaml:"; python -c "import yaml;print(len(yaml.safe_load(open('pipeline/grillas_mirova.yaml',encoding='utf-8'))['volcanes']))"
else echo "merge #932 + roi: CONFLICTO"; git diff --name-only --diff-filter=U; git merge --abort; fi
git checkout -q --detach v2_orden_ABS
echo "FIN"
