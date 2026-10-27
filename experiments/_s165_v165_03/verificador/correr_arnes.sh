#!/bin/bash
export VRP_PROFILE=mirova_equivalent PYTHONIOENCODING=utf-8
B="D:/vrp-trabajo/temporales/s165_v16503_verificador"
S="$B/salidas"
cd "$B/arbol_tag"
echo "== tag apagado"; python tests/arnes_sin_dato_s165.py --salida "$S/tag_apagado.json" > "$S/tag_apagado.log" 2>&1; echo rc=$?
echo "== tag geo"; python tests/arnes_sin_dato_s165.py --salida "$S/tag_geo.json" --flag ENABLE_MODIS_GEO_MXD03=True > "$S/tag_geo.log" 2>&1; echo rc=$?
echo "== tag geo_sin_dato"; python tests/arnes_sin_dato_s165.py --salida "$S/tag_geo_sin_dato.json" --flag ENABLE_MODIS_GEO_MXD03=True --flag ENABLE_MODIS_CRATER_SIN_DATO=True > "$S/tag_geo_sin_dato.log" 2>&1; echo rc=$?
cd "$B/arbol"
echo "== head apagado"; python tests/arnes_sin_dato_s165.py --salida "$S/head_apagado.json" > "$S/head_apagado.log" 2>&1; echo rc=$?
echo "== head geo"; python tests/arnes_sin_dato_s165.py --salida "$S/head_geo.json" --flag ENABLE_MODIS_GEO_MXD03=True > "$S/head_geo.log" 2>&1; echo rc=$?
echo "== head geo_sin_dato"; python tests/arnes_sin_dato_s165.py --salida "$S/head_geo_sin_dato.json" --flag ENABLE_MODIS_GEO_MXD03=True --flag ENABLE_MODIS_CRATER_SIN_DATO=True > "$S/head_geo_sin_dato.log" 2>&1; echo rc=$?
echo "== head sin_dato solo"; python tests/arnes_sin_dato_s165.py --salida "$S/head_sin_dato_solo.json" --flag ENABLE_MODIS_CRATER_SIN_DATO=True > "$S/head_sin_dato_solo.log" 2>&1; echo rc=$?
echo FIN
