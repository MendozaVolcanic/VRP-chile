#!/usr/bin/env bash
# S161, D-45: las verdes con el árbol QUIETO (A112). Corre en serie probar_evaluar_d25.py y la suite entera de pytest,
# y escribe TODO afuera del repositorio (C:/vrp-trabajo/tmp_s161/verdes/) mientras corre, para no tocar el árbol que
# mide; al terminar, copia las salidas a esta carpeta. Antes y después: hora UTC, HEAD, git status, sha256 del
# evaluador, de probar y de las seis baterías, procesos python vivos y copias experiments/_mut_*.
set -u
R=/c/vrp-trabajo/s159-evaluador
O=/c/vrp-trabajo/tmp_s161/verdes
rm -rf "$O"; mkdir -p "$O"
export TMP=C:/vrp-trabajo/tmp_s161 TEMP=C:/vrp-trabajo/tmp_s161 PYTHONIOENCODING=utf-8
cd "$R"
ARCH="experiments/_s157_prereg_d25/evaluar_d25.py experiments/_s157_prereg_d25/probar_evaluar_d25.py
tests/test_evaluar_d25_signos_p2_s161.py tests/test_evaluar_d25_calib_p2_s160.py tests/test_evaluar_d25_p2_s159.py
tests/test_evaluar_d25_dias_d29_s160.py tests/test_evaluar_d25_punta_a_punta_s160.py tests/test_evaluar_d25_placebo_s159.py"
foto() {
  { date -u; git rev-parse HEAD; git status --short; echo "procesos python vivos (sin contar este script): $(tasklist 2>/dev/null | grep -ci '^python')";
    echo "copias experiments/_mut_*: $(ls -d experiments/_mut_* 2>/dev/null | wc -l)"; } > "$O/status_$1.txt"
  { date -u; sha256sum $ARCH; } > "$O/sha_$1.txt"
}
foto antes
# S161: probar_evaluar_d25.py exige su carpeta de casos como argumento (l. 65); la primera corrida la omitió y cayó por
# IndexError en la línea de arriba de todo, sin correr ningún caso (exit 1, salida guardada fuera del repo).
{ date -u; time python experiments/_s157_prereg_d25/probar_evaluar_d25.py C:/vrp-trabajo/tmp_s161/probar_casos; echo "exit probar $?"; date -u; } > "$O/probar_salida.txt" 2>&1
rm -rf C:/vrp-trabajo/tmp_s161/probar_casos
{ date -u; time python -m pytest -q -p no:cacheprovider --basetemp C:/vrp-trabajo/tmp_s161/bt_suite; echo "exit suite $?"; date -u; } > "$O/suite_salida.txt" 2>&1
foto despues
cp "$O"/*.txt "$R/experiments/_s159/instrumentos/signos_p2/"
rm -rf C:/vrp-trabajo/tmp_s161/bt_suite
tail -3 "$O/probar_salida.txt"; tail -4 "$O/suite_salida.txt"
diff <(tail -n +2 "$O/status_antes.txt") <(tail -n +2 "$O/status_despues.txt") && echo "status igual salvo la hora"
diff <(tail -n +2 "$O/sha_antes.txt") <(tail -n +2 "$O/sha_despues.txt") && echo "sha256 iguales"
