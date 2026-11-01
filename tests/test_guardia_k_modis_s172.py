# -*- coding: utf-8 -*-
"""S172: la guardia K de MODIS (perfil, workflow y revisión de su corrida), parte del PR A del encendido de MOD-D.

POR QUÉ. Nicolás decidió (2026-10-31) encender la vía «código MIROVA» de MODIS sin esperar la sombra de 28 noches, con
K corriendo aparte como guardia: si la vía calla una alerta protegida que K habría publicado, se revierte el mismo día
(experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md §3 y §4, rama loop/activo; diseño
docs/superpowers/specs/2026-11-01-encendido-modd-design.md, decisión 2). La guardia sólo sirve si mide K de verdad:
estas pruebas fijan lo que puede fallar en silencio:
  1. el perfil resuelve K en MODIS (la vía apagada), sólo MODIS, en su propia carpeta, leído como lo lee el código
     (A89), y difiere de producción sólo en eso; si heredara la vía, la guardia sería producción y nunca dispararía;
  2. el workflow afirma el perfil desde pipeline.profile antes de correr, autentica sólo con token (A71), tiene grupo
     propio, commitea sólo su carpeta y revisa la corrida después del commit;
  3. la revisión de la corrida pone rojo una guardia que no escribió nada, que escribió records de la vía o que dejó
     un día sin MODIS sin prueba de que no hubo pasada.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

PERFIL = "guardia_k_modis"
WF = ROOT / ".github" / "workflows" / "guardia-k-modis.yml"
NRT = ROOT / ".github" / "workflows" / "nrt.yml"
SOMBRA_WF = ROOT / ".github" / "workflows" / "sombra-codigo-mirova.yml"


def _resuelto(perfil):
    """Constantes de pipeline.profile resueltas en un proceso aparte con VRP_PROFILE (A89: nunca el YAML)."""
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8")
    codigo = ("import json, pipeline.profile as p; "
              "print(json.dumps({k: repr(sorted(v) if isinstance(v, (set, frozenset)) else v) "
              "for k, v in ((k, getattr(p, k)) for k in dir(p) if k.isupper())}, sort_keys=True))")
    r = subprocess.run([sys.executable, "-c", codigo], cwd=ROOT, env=env, capture_output=True, text=True,
                       encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout.strip().splitlines()[-1])


# ------------------------------------------------------------------------------------- 1. el perfil
def test_la_guardia_resuelve_k_en_modis_solo_modis_y_carpeta_propia():
    g = _resuelto(PERFIL)
    assert g["ENABLE_MODIS_CODIGO_MIROVA"] == "False", "la guardia es K: la vía de MODIS va apagada"
    assert g["DATA_SUBDIR"] == repr(PERFIL)
    assert g["PROFILE_NAME"] == repr(PERFIL)
    # los tres flags de K, con el valor de producción (S153); MxD03 apagado como en producción
    assert g["ENABLE_TEST1_PATH"] == "False" and g["ENABLE_TESTS_23_PROSE_BRANCH"] == "True"
    assert g["ENABLE_MODIS_B22_PRIMARY"] == "True"
    for k in ("ENABLE_MODIS_GEO_MXD03", "ENABLE_MODIS_CRATER_SIN_DATO", "ENABLE_MODIS_DIST_DESDE_CRATER"):
        assert g[k] == "False", k


def test_la_guardia_difiere_de_produccion_solo_en_la_via_los_sensores_y_la_carpeta():
    """Cualquier otra diferencia haría que la guardia midiera otro paquete que el K de producción."""
    prod, g = _resuelto("mirova_equivalent"), _resuelto(PERFIL)
    distintas = {k for k in set(prod) | set(g) if prod.get(k) != g.get(k)}
    # Con el flag de producción apagado (PR A), la vía no difiere; con el PR B encendido, sí. Los dos casos valen.
    permitidas = {"DATA_SUBDIR", "PROFILE_NAME", "SENSOR_VIIRS_375", "SENSOR_VIIRS_750",
                  "ENABLE_MODIS_CODIGO_MIROVA"}
    assert distintas <= permitidas, sorted(distintas - permitidas)
    assert {"DATA_SUBDIR", "PROFILE_NAME"} <= distintas


def test_la_guardia_corre_solo_modis():
    cfg = yaml.safe_load((ROOT / "pipeline" / "profiles" / f"{PERFIL}.yaml").read_text(encoding="utf-8"))
    assert cfg["extends"] == "mirova_equivalent"
    assert cfg["sensors"] == {"modis": True, "viirs_375": False, "viirs_750": False}
    assert cfg["thresholds"]["enable_modis_codigo_mirova"] is False
    # leído por el código, no por el YAML (A89)
    g = _resuelto(PERFIL)
    assert (g["SENSOR_MODIS"], g["SENSOR_VIIRS_375"], g["SENSOR_VIIRS_750"]) == ("True", "False", "False")


def test_ningun_otro_perfil_escribe_en_la_carpeta_de_la_guardia():
    otros = []
    for f in sorted((ROOT / "pipeline" / "profiles").glob("*.yaml")):
        cfg = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if f.stem != PERFIL and ((cfg.get("output") or {}).get("data_subdir") == PERFIL):
            otros.append(f.stem)
    assert not otros
