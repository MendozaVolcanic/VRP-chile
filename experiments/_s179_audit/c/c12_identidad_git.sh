#!/usr/bin/env bash
# Frente C, auditoria S179. Instrumento c12: identidades de git que sostienen la lectura (solo lectura del repo).
# LAS DOS PREGUNTAS. (1) Si el codigo de la via que corrio la retrospectiva no fuera el que se va a encender, o el
# pre-registro hubiera cambiado tras el sello, esto lo ve (lista los archivos que difieren). (2) Instrumento muerto:
# control positivo, el diff de pipeline/ entre el tag de despacho y main TIENE que listar pipeline/fetch.py (cambio
# en #966, posterior al despacho); si sale vacio, el diff no esta mirando nada.
export MSYS_NO_PATHCONV=1
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile" || exit 1
echo "== tags de despacho y commit"; for t in s172-retro-d1 s172-retro-d2 s172-retro-d3 s172-retro-d4; do echo "$t -> $(git rev-parse --short "$t^{commit}")"; done
echo "== pre-registro: sha256 del blob en el sello, en loop/activo 0472cd95e y en origin/loop/activo"
for r in s173-prereg-retro-sellado 0472cd95e origin/loop/activo; do echo "$r $(git show $r:experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md | sha256sum | cut -c1-16)"; done
echo "== mensaje del tag del sello (el §11 pide que traiga el sha256 LF del documento)"; git cat-file -p s173-prereg-retro-sellado | tail -2
echo "== pre-registro en el arbol de la ref de lectura s178-retro-lectura:"; git ls-tree -r --name-only s178-retro-lectura -- experiments/_s172_prereg_retro | wc -l
echo "== lector: sha256 LF en la ref de lectura y en main 438a60a1e"
for r in s178-retro-lectura 438a60a1e; do echo "$r $(git show $r:experiments/_s172_retro_paquete/leer_retro.py | tr -d '\r' | sha256sum | cut -c1-16)"; done
echo "== codigo: tag de despacho a7a6ae360 contra main 438a60a1e (pipeline/, run_pipeline.py, volcanoes.yaml)"
git diff --stat a7a6ae360 438a60a1e -- pipeline/ scripts/run_pipeline.py volcanoes.yaml | cat
echo "== codigo: a7a6ae360 contra la punta de #974 (bbbe2068d) y de #983 (e68819484)"
for h in bbbe2068d e68819484; do echo "-- $h"; git diff --stat a7a6ae360 $h -- pipeline/ scripts/run_pipeline.py volcanoes.yaml | cat; done
echo "== flags de MODIS en produccion (438a60a1e) que el perfil de la retrospectiva fija"
git show 438a60a1e:pipeline/profiles/mirova_equivalent.yaml | grep -n -E '^\s*(enable_modis_geo_mxd03|enable_modis_crater_sin_dato|enable_modis_dist_desde_crater|enable_modis_codigo_mirova|enable_test1_path|enable_tests_23_prose_branch|enable_modis_b22_primary)'
echo "== roi_v750 de los 11 Tier A en grillas_mirova.yaml (tag, main, #983)"
for c in a7a6ae360 438a60a1e e68819484; do echo "-- $c: $(git show $c:pipeline/grillas_mirova.yaml | grep -E '^\s+(Chaiten|NevadosDeChillan|Copahue|Isluga|Lascar|Lastarria|Llaima|PlanchonPeteroa|PuyehueCordonCaulle|Tupungatito|Villarrica):' | sed -E 's/^\s+([A-Za-z]+):.*roi_v750: ([a-z]+).*/\1=\2/' | tr '\n' ' ')"; done
echo "== frontend y etiquetado: tag de despacho contra main 438a60a1e"
git diff --stat a7a6ae360 438a60a1e -- frontend/index.html frontend/cambio_detector.js scripts/banco_paridad.py scripts/clase_mirova.py scripts/referencia_mirova_unificada.py scripts/auto_audit_weekly.py scripts/calidad_referencia_mirova.py | cat
echo "== orden de los commits de S178 (hora local -03)"
for c in 2bfc9164b 254cefb9c 5a3f21faa c592ac2d2 6a07f8ea2 caf2b24e3 cd48bc133 ba5ef81c5 f8304c161 ff8a39972; do git show -s --format='%h %cd | %s' --date=format-local:'%Y-%m-%d %H:%M:%S' $c | cut -c1-150; done
