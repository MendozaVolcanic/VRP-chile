# -*- coding: utf-8 -*-
"""S177, PR B2: la vía «código MIROVA» de VIIRS 750 queda ENCENDIDA en producción, y ningún perfil vivo la hereda sin
querer.

POR QUÉ. En VIIRS 750, K publica cerca de la mitad de la potencia que MIROVA le asigna al volcán (0,510 en la
retrospectiva de experiments/_s162_v750c/INFORME.md; 0,482 en la sombra, n 14, pasadas con alerta del 2026-11-03 al
11-07), porque recorta el cúmulo y usa su propio fondo, mientras MIROVA suma todos los píxeles que alerta. La vía corre
el código publicado por MIROVA sobre su misma grilla y da 0,999 en la retrospectiva y 1,000 en la sombra. Nicolás pidió
encender VIIRS con la vía y K de guardia (diseño del encendido de VIIRS del 2026-11-08, decisión 7, en la rama
loop/activo; regla experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md, SIN SELLO al escribir esto; tag defensivo
pre-s178-b1-b2). Este guard fija dos cosas que fallan en silencio:
  1. el flag de producción, leído desde pipeline.profile (A89): si una consolidación lo apagara, VIIRS 750 volvería a
     K sin que nada lo dijera (A63); si B2 se revierte, este archivo se va con él;
  2. el valor del flag en cada perfil que corre un workflow vivo. Los perfiles con `extends: mirova_equivalent`
     heredan lo que no declaran (A117): el laboratorio `experimental` (congelado en C0, sombra de K de
     scripts/vigilancia_sombra.py), `experimental_ndc_focus` y el ancla de los tests pre-K (`_s146_ab_control`) habrían
     pasado a la vía de VIIRS 750 sin que nadie lo decidiera. Por eso B2 los declara apagados en su YAML.
Un perfil derivado que aparezca en un workflow programado y no esté en VIVOS hace caer la prueba: hay que decidir su
valor, no dejarlo heredar. La vía de VIIRS 375 es de B1 y este archivo no la fija, para que B1 y B2 se puedan mergear
y revertir en cualquier orden.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
PERFILES = ROOT / "pipeline" / "profiles"
WORKFLOWS = ROOT / ".github" / "workflows"
FLAG = "ENABLE_V750_CODIGO_MIROVA"
CLAVE = "enable_v750_codigo_mirova"

# perfil vivo -> valor esperado de ENABLE_V750_CODIGO_MIROVA, con el porqué
VIVOS = {
    "mirova_equivalent": True,        # producción: el encendido de este PR
    "sombra_codigo_mirova": True,     # la sombra corre las tres vías a propósito (S167)
    "sombra_34": True,                # sombra de los 34 con las tres vías (#932)
    "guardia_k_viirs": False,         # la guardia es K de los dos VIIRS (S176, PR A)
    "guardia_k_modis": False,         # K pura de MODIS; no corre VIIRS, pero si heredara la vía pediría pyproj
    "experimental": False,            # laboratorio congelado en C0: sombra de K (S150, S156); lo declara B2
    "experimental_ndc_focus": False,  # producción de antes de K para Chillán, despachado desde nrt.yml; lo declara B2
}
# perfiles que B2 obliga a declarar el flag apagado en su YAML (los otros apagados ya lo declaraban)
DECLARAN_APAGADA = ("experimental", "experimental_ndc_focus", "_s146_ab_control", "guardia_k_modis", "guardia_k_viirs")

_LEER = """
import importlib, json, os, sys
nombres = json.loads(sys.argv[1]); out = {}
import pipeline.profile as p
for n in nombres:
    os.environ["VRP_PROFILE"] = n
    importlib.reload(p)
    out[n] = p.ENABLE_V750_CODIGO_MIROVA
print("@@" + json.dumps(out))
"""


def _resueltos(nombres):
    r = subprocess.run([sys.executable, "-c", _LEER, json.dumps(sorted(nombres))], capture_output=True, text=True,
                       cwd=ROOT, env=dict(os.environ, PYTHONIOENCODING="utf-8"), check=True)
    return json.loads([ln for ln in r.stdout.splitlines() if ln.startswith("@@")][0][2:])


def test_produccion_corre_la_via_de_viirs_750():
    env = dict(os.environ, VRP_PROFILE="mirova_equivalent", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-c", f"import pipeline.profile as p; print(p.{FLAG})"],
                       cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip().splitlines()[-1] == "True"


def test_el_procesador_de_viirs_750_recibe_el_flag_encendido():
    """El flag llega al procesador que lo usa (pipeline/process_viirs_mod.py), no sólo a pipeline.profile (A118)."""
    env = dict(os.environ, VRP_PROFILE="mirova_equivalent", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-c", f"from pipeline import process_viirs_mod as P; print(P.{FLAG})"],
                       cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip().splitlines()[-1] == "True"


def test_b2_no_toca_los_flags_de_mxd03_ni_la_via_de_modis():
    """B2 enciende VIIRS 750 y nada más (regla §2): MODIS sigue con su vía (#934) y los de MxD03 apagados."""
    env = dict(os.environ, VRP_PROFILE="mirova_equivalent", PYTHONIOENCODING="utf-8")
    codigo = ("import pipeline.profile as p; print([p.ENABLE_MODIS_CODIGO_MIROVA, p.ENABLE_MODIS_GEO_MXD03, "
              "p.ENABLE_MODIS_CRATER_SIN_DATO, p.ENABLE_MODIS_DIST_DESDE_CRATER])")
    r = subprocess.run([sys.executable, "-c", codigo], cwd=ROOT, env=env, capture_output=True, text=True,
                       encoding="utf-8")
    assert r.stdout.strip().splitlines()[-1] == "[True, False, False, False]"


def test_cada_perfil_vivo_resuelve_el_valor_que_le_corresponde():
    res = _resueltos(VIVOS)
    malos = {n: (res[n], esperado) for n, esperado in VIVOS.items() if res[n] is not esperado}
    assert not malos, f"(resuelto, esperado): {malos}"


@pytest.mark.parametrize("perfil", DECLARAN_APAGADA)
def test_los_perfiles_que_no_siguen_a_produccion_lo_declaran_en_thresholds(perfil):
    """Declarado donde lo lee el código (A89): en otra sección no cuenta y el perfil heredaría la vía."""
    cfg = yaml.safe_load((PERFILES / f"{perfil}.yaml").read_text(encoding="utf-8"))
    assert (cfg.get("thresholds") or {}).get(CLAVE) is False, perfil


def test_el_ancla_pre_k_resuelve_la_via_apagada():
    """`_s146_ab_control` es el ancla de tests/produccion_pre_k.py (la producción de antes de K, que no tenía la vía)."""
    assert _resueltos(["_s146_ab_control"])["_s146_ab_control"] is False


def _programados():
    """Workflows que corren solos (schedule o workflow_run)."""
    out = []
    for f in sorted(WORKFLOWS.glob("*.yml")):
        on = (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("on") or {}
        if isinstance(on, dict) and ({"schedule", "workflow_run"} & set(on)):
            out.append(f)
    return out


def test_todo_perfil_derivado_que_nombra_un_workflow_programado_tiene_valor_decidido():
    derivados = set()
    for f in PERFILES.glob("*.yaml"):
        cfg = yaml.safe_load(f.read_text(encoding="utf-8"))
        if isinstance(cfg, dict) and cfg.get("extends") == "mirova_equivalent":
            derivados.add(f.stem)
    nombrados = set()
    for wf in _programados():
        txt = wf.read_text(encoding="utf-8")
        nombrados |= {n for n in derivados if re.search(r"(?<![A-Za-z0-9_])" + re.escape(n) + r"(?![A-Za-z0-9_])", txt)}
    assert nombrados, "control: algún perfil derivado aparece en un workflow programado"
    sin_decidir = nombrados - set(VIVOS)
    assert not sin_decidir, f"perfiles vivos sin valor decidido de la vía de VIIRS 750: {sorted(sin_decidir)}"


def test_control_el_instrumento_ve_un_perfil_que_hereda():
    """Si `experimental` no declarara el flag, lo resolvería igual que producción: True. Un brazo viejo de A/B que no
    lo declara sirve de control de que el lector ve la herencia (si diera False, el guard de arriba no probaría nada)."""
    res = _resueltos(["mirova_equivalent", "_s146_ab_sin_test1"])
    assert res["mirova_equivalent"] is True and res["_s146_ab_sin_test1"] is True
