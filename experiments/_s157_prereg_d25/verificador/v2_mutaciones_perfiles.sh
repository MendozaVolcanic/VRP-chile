#!/usr/bin/env bash
# Verificador S157 1.29: mutaciones de los perfiles de los brazos sobre una copia (git archive) en un temporal.
# Cada mutacion debe hacer FALLAR tests/test_perfiles_d25_k_s157.py por una ASERCION (no por caida).
# Uso: bash v2_mutaciones_perfiles.sh <copia>   (la copia sale de: git archive HEAD pipeline tests/test_perfiles_d25_k_s157.py .github/workflows/reproc-s146-ab-sin-test1.yml)
C=$1; P=$C/pipeline/profiles
correr() {  # $1 nombre
  out=$(cd $C && TMP='D:\vrp-trabajo\temporales' TEMP='D:\vrp-trabajo\temporales' python -m pytest -q -p no:cacheprovider tests/test_perfiles_d25_k_s157.py 2>&1)
  res=$(echo "$out" | tail -1); asr=$(echo "$out" | grep -c "AssertionError\|^E\s*assert"); err=$(echo "$out" | grep -c "Error:" )
  echo "$1 | $res | lineas de asercion: $asr"
}
backup() { cp -r $P $C/_bk; cp $C/.github/workflows/reproc-s146-ab-sin-test1.yml $C/_bk_wf; }
restore() { rm -rf $P; cp -r $C/_bk $P; cp $C/_bk_wf $C/.github/workflows/reproc-s146-ab-sin-test1.yml; }
backup
correr "M0 sin mutar (debe pasar)"
sed -i 's/  enable_vrp_bg_neighbor_mean_viirs750: true//' $P/_s157_ab_d25_k_on.yaml; correr "M1 D sin el flag de V750"; restore
printf '\nthresholds:\n  vrp_bg_neighbor_max_half_px: 2\n' >> $P/_s157_ab_d25_k_on.yaml; correr "M2 D con ventana 5x5"; restore
sed -i 's/  enable_tests_23_prose_branch: true/  enable_tests_23_prose_branch: true\n  enable_vrp_bg_neighbor_mean_viirs375: true/' $P/_s157_ab_d25_k_gemelo.yaml; correr "M3 gemelo con D25 en V375"; restore
sed -i 's/  modis: false/  modis: true/' $P/_s157_ab_d25_k_control.yaml; correr "M4 control con MODIS"; restore
sed -i 's/enable_modis_b22_primary: true/enable_modis_b22_primary: true\nenable_vent_anchored_clustering: false/' $P/_s157_ab_d25_k_on.yaml; correr "M5 D con otra palanca (vent_anchored off, raiz)"; restore
sed -i 's/  enable_tests_23_prose_branch: true/  enable_tests_23_prose_branch: true\n  enable_vent_anchored_clustering: false/' $P/_s157_ab_d25_k_on.yaml; correr "M5b D con vent_anchored off en paths"; restore
sed -i "s/'SENSOR_MODIS'//" $C/.github/workflows/reproc-s146-ab-sin-test1.yml; correr "M6 FLAGS_BRAZO sin SENSOR_MODIS"; restore
sed -i 's/  enable_test1_path: false/  enable_test1_path: true/' $P/mirova_equivalent.yaml; correr "M7 produccion vuelve a C0 en Test 1 (brazos fijan false)"; restore
