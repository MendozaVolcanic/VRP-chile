# -*- coding: utf-8 -*-
"""S193: el día de MODIS encendido en producción, y sólo ahí (decisión de Nicolás del 2026-11-21, A/B #813).

POR QUÉ. El A/B diurno sobre la vía (experiments/_s190_diurno/INFORME_VEREDICTO.md, con la desviación declarada 1)
salió DECIDE NICOLÁS CON M4, y Nicolás decidió encender el día sólo en MODIS: «continua con todo lo que recomiendes»
(recomendación «D2: encender el día sólo en MODIS»). VIIRS sigue sólo de noche hasta mirar en imagen lo que publica de
día fuera de Chillán. El A/B midió la vía en los 11 Tier A; los perfiles que heredan de producción y no son esa vía
sobre esos volcanes (la guardia K, el laboratorio con el detector anterior, las sombras) quedan con el día apagado de
forma explícita, para no encender algo que nadie midió. Se comprueba resolviendo pipeline.profile, no leyendo el YAML
(A89).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCCION = "mirova_equivalent"
# Heredan de producción y NO deben abrir el día de MODIS (ver el POR QUÉ).
SIN_DIA = ("guardia_k_modis", "guardia_k_viirs", "experimental", "experimental_lowT", "experimental_ndc_focus",
           "sombra_34", "sombra_codigo_mirova")

_RESOLVER = """
import importlib, json, os, sys
out = {}
for n in sys.argv[1:]:
    os.environ["VRP_PROFILE"] = n
    import pipeline.profile as p
    p = importlib.reload(p)
    out[n] = {"modis": p.ENABLE_DAYTIME_MODIS, "viirs": p.ENABLE_DAYTIME_VIIRS, "via_modis": p.ENABLE_MODIS_CODIGO_MIROVA}
print("@@" + json.dumps(out))
"""


def _resolver(*nombres):
    r = subprocess.run([sys.executable, "-c", _RESOLVER, *nombres], capture_output=True, text=True, cwd=ROOT,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"), check=True)
    return json.loads([l for l in r.stdout.splitlines() if l.startswith("@@")][0][2:])


def test_produccion_abre_el_dia_solo_en_modis():
    p = _resolver(PRODUCCION)[PRODUCCION]
    assert p == {"modis": True, "viirs": False, "via_modis": True}, p


def test_los_perfiles_derivados_quedan_sin_dia_de_modis():
    res = _resolver(*SIN_DIA)
    assert {n: v["modis"] for n, v in res.items()} == {n: False for n in SIN_DIA}
    assert not any(v["viirs"] for v in res.values())


def test_las_tres_compuertas_del_dia_abren_para_modis_y_no_para_viirs():
    """La trampa de S92: un flag que abre una sola compuerta mide cero. Con el perfil de producción, el filtro previo a
    la descarga, el salto del gránulo ya bajado (misma función) y el rechazo del record abren para MODIS y no para
    VIIRS."""
    codigo = """
import json, os
os.environ["VRP_PROFILE"] = "mirova_equivalent"
from pipeline import diurno, store
import pipeline.profile as p
print("@@" + json.dumps({
  "filtro_modis": [diurno.aplica_filtro_nocturno(True, x) for x in ("MODIS_TERRA", "MODIS_AQUA")],
  "filtro_viirs": [diurno.aplica_filtro_nocturno(True, x) for x in ("VIIRS_SNPP", "VIIRS_NOAA20_750")],
  "rechazo_modis": store._reject_daytime("MODIS_TERRA", 30.0, p.ENABLE_DAYTIME_MODIS, p.ENABLE_DAYTIME_VIIRS),
  "rechazo_viirs": store._reject_daytime("VIIRS_NOAA20", 30.0, p.ENABLE_DAYTIME_MODIS, p.ENABLE_DAYTIME_VIIRS),
}))
"""
    r = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, cwd=ROOT,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"), check=True)
    d = json.loads([l for l in r.stdout.splitlines() if l.startswith("@@")][0][2:])
    assert d == {"filtro_modis": [False, False], "filtro_viirs": [True, True], "rechazo_modis": False,
                 "rechazo_viirs": True}, d
