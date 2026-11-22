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


# Brazos que declaran el día de MODIS encendido a propósito (el brazo diurno del A/B #813).
CON_DIA = {"_s190_ab_diurno_via_on"}


def _derivados():
    import yaml
    out = {}
    for f in sorted((ROOT / "pipeline" / "profiles").glob("*.yaml")):
        cfg = yaml.safe_load(f.read_text(encoding="utf-8"))
        if isinstance(cfg, dict) and cfg.get("extends") == PRODUCCION:
            out[f.stem] = cfg
    return out


def _sin_flag(cfg):
    """True si el YAML propio del perfil no declara el flag en `paths`, la sección donde lo lee pipeline/profile.py."""
    return "enable_daytime_modis" not in (cfg.get("paths") or {})


def test_todo_perfil_derivado_declara_el_dia_de_modis():
    """A117 y S153: un perfil que hereda de producción declara el flag en `paths` (donde lo lee pipeline/profile.py),
    así el próximo cambio de producción no se le filtra en silencio. Los brazos históricos se midieron con producción
    sólo de noche y lo declaran apagado; sólo el brazo diurno del A/B lo declara encendido. Se comprueba también lo que
    resuelve el código (A89)."""
    der = _derivados()
    assert len(der) >= 60
    sin = sorted(n for n, c in der.items() if _sin_flag(c))
    assert sin == [], f"perfiles derivados que heredarían el día de MODIS de producción: {sin}"
    encendidos = {n for n, c in der.items() if c["paths"]["enable_daytime_modis"] is True}
    assert encendidos == CON_DIA, encendidos
    res = _resolver(*sorted(der))
    assert {n for n, v in res.items() if v["modis"]} == CON_DIA


def test_control_negativo_el_guard_ve_un_derivado_sin_el_flag():
    assert _sin_flag({"extends": PRODUCCION, "paths": {"enable_test1_path": False}})
    assert _sin_flag({"extends": PRODUCCION, "thresholds": {"enable_daytime_modis": False}})  # sección equivocada
    assert not _sin_flag({"extends": PRODUCCION, "paths": {"enable_daytime_modis": False}})
