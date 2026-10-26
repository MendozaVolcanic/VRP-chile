#!/bin/sh
# Uso: sh correr.sh <caso> [objetivos_extra]   (corre evaluar.py sobre los artefactos fabricados del caso)
CASO=$1
OBJ=${2:-b2/objetivos_v375_b2.json}
V3="C:/vrp-trabajo/temporales/s162_v375/verif_v3/$CASO"
AQUI="$(cd "$(dirname "$0")" && pwd)"
cd "$AQUI/../.." || exit 1
cp "$V3/cache.json" "$V3/cache_run.json"
python -I evaluar.py --art162 "C:/vrp-trabajo/temporales/s162_v375/run_40116289866" --cobertura cobertura_marco.json \
  --cache "$V3/cache_run.json" --objetivos-extra "$OBJ" --art-extra "$V3" --deciden S162b --neg-pub-de S162 \
  --salida "$AQUI/salida_$CASO.txt" --json "$AQUI/salida_$CASO.json" > "$AQUI/stdout_$CASO.txt" 2>&1
echo "exit $? caso $CASO"
grep -n "con estado ok\|2.1 recálculo\|2.2 K re\|2.2b\|distintas\|ESTADO DEL INSTRUMENTO\|AVISO\|VEREDICTO\|INVALIDO\|sin grilla" "$AQUI/salida_$CASO.txt"
