#!/bin/bash
# uso: consumidores.sh <S> <etiqueta>
S="$1"; T="$2"; R="$S/raiz"; O="$S/$T"; mkdir -p "$O"
export PYTHONIOENCODING=utf-8
cd "$R"
run() { name=$1; shift
  rm -rf "$R/data/audit_continuous"; cp -r "$S/audit_continuous_pristino" "$R/data/audit_continuous"
  ( time python "$@" ) > "$O/$name.stdout" 2> "$O/$name.stderr"; echo "$name exit $?" >> "$O/exits.txt"
  mkdir -p "$O/$name.audit"; (cd "$R/data/audit_continuous" && for f in $(find . -type f -newer "$S/audit_continuous_pristino" 2>/dev/null); do mkdir -p "$O/$name.audit/$(dirname $f)"; cp "$f" "$O/$name.audit/$f"; done)
}
touch "$S/audit_continuous_pristino"
run guardia_modis scripts/vigilancia_guardia_modis.py
run sombra scripts/vigilancia_sombra.py
run clasificar scripts/clasificar_referencia.py --stats "$O/clasificar_stats.json" --out "$O/clasificar_out.json"
run banco scripts/banco_paridad.py --snapshot --dest "$O/_dl" --out "$O/banco_out.json"
run auto_audit scripts/auto_audit_weekly.py
