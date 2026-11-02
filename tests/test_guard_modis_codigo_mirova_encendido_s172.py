# -*- coding: utf-8 -*-
"""S172, PR B: la vía «código MIROVA» de MODIS queda ENCENDIDA en producción, y ningún perfil vivo la hereda sin querer.

POR QUÉ. Nicolás decidió el 2026-10-31 adelantar MODIS: encender la vía sin esperar la sombra de 28 noches, con K de
guardia (experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md, rama loop/activo; tag defensivo
pre-s171-adopcion-modd). Este guard fija dos cosas que fallan en silencio:
  1. el flag de producción, leído desde pipeline.profile (A89): si una consolidación lo apagara, MODIS volvería a K
     sin que nada lo dijera (A63); si el PR B se revierte, este archivo se va con él;
  2. el valor del flag en cada perfil que corre un workflow vivo. 58 perfiles hacen `extends: mirova_equivalent` y
     heredan lo que no declaran (A117). El laboratorio `experimental` (data/experimental_v2/, congelado en C0, la
     sombra de K que lee scripts/vigilancia_sombra.py) y `experimental_ndc_focus` habrían pasado a la vía de MODIS:
     el laboratorio dejaría de ser C0 en MODIS y la vigilancia de K compararía otra cosa. La guardia tiene que ser K y
     la sombra, la vía. Hallazgo de la sesión de VIIRS 750 (S172), anotado por la coordinadora.
Un perfil derivado que aparezca en un workflow programado y no esté en VIVOS hace caer la prueba: hay que decidir su
valor, no dejarlo heredar.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PERFILES = ROOT / "pipeline" / "profiles"
WORKFLOWS = ROOT / ".github" / "workflows"

# perfil vivo -> valor esperado de ENABLE_MODIS_CODIGO_MIROVA, con el porqué
VIVOS = {
    "mirova_equivalent": True,        # producción: el encendido de este PR
    "sombra_codigo_mirova": True,     # la sombra corre las tres vías a propósito (S167)
    "guardia_k_modis": False,         # la guardia es K de MODIS (PR A)
    "experimental": False,            # laboratorio congelado en C0: sombra de K (S150, S156)
    "experimental_ndc_focus": False,  # laboratorio de Chillán, despachado desde nrt.yml: no sigue a producción
}
# S173 (hallazgo 201): perfiles vivos que llegan con otro PR. Entran a VIVOS sólo si su YAML existe, para que el guard
# no dependa del orden de los merges.
VIVOS_SI_EXISTEN = {
    "sombra_34": True,                # sombra de los 34 con las tres vías (#932, sombra-34.yml)
}
VIVOS.update({n: v for n, v in VIVOS_SI_EXISTEN.items() if (PERFILES / f"{n}.yaml").exists()})

_LEER = """
import importlib, json, os, sys
nombres = json.loads(sys.argv[1]); out = {}
import pipeline.profile as p
for n in nombres:
    os.environ["VRP_PROFILE"] = n
    importlib.reload(p)
    out[n] = p.ENABLE_MODIS_CODIGO_MIROVA
print("@@" + json.dumps(out))
"""


def _resueltos(nombres):
    r = subprocess.run([sys.executable, "-c", _LEER, json.dumps(sorted(nombres))], capture_output=True, text=True,
                       cwd=ROOT, env=dict(os.environ, PYTHONIOENCODING="utf-8"), check=True)
    return json.loads([ln for ln in r.stdout.splitlines() if ln.startswith("@@")][0][2:])


def test_produccion_corre_la_via_de_modis():
    env = dict(os.environ, VRP_PROFILE="mirova_equivalent", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-c", "import pipeline.profile as p; print(p.ENABLE_MODIS_CODIGO_MIROVA)"],
                       cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip().splitlines()[-1] == "True"


def test_la_via_de_viirs_y_los_flags_de_mxd03_siguen_apagados_en_produccion():
    """El PR B enciende MODIS y nada más (regla §2): VIIRS 375, VIIRS 750 y MxD03 van aparte."""
    env = dict(os.environ, VRP_PROFILE="mirova_equivalent", PYTHONIOENCODING="utf-8")
    codigo = ("import pipeline.profile as p; print([p.ENABLE_V750_CODIGO_MIROVA, p.ENABLE_V375_CODIGO_MIROVA, "
              "p.ENABLE_MODIS_GEO_MXD03, p.ENABLE_MODIS_CRATER_SIN_DATO, p.ENABLE_MODIS_DIST_DESDE_CRATER])")
    r = subprocess.run([sys.executable, "-c", codigo], cwd=ROOT, env=env, capture_output=True, text=True,
                       encoding="utf-8")
    assert r.stdout.strip().splitlines()[-1] == "[False, False, False, False, False]"


def test_cada_perfil_vivo_resuelve_el_valor_que_le_corresponde():
    res = _resueltos(VIVOS)
    malos = {n: (res[n], esperado) for n, esperado in VIVOS.items() if res[n] is not esperado}
    assert not malos, f"(resuelto, esperado): {malos}"


def test_los_laboratorios_lo_declaran_en_su_yaml_y_en_thresholds():
    """Declarado donde lo lee el código (A89): en otra sección no cuenta y el perfil heredaría la vía."""
    for n in ("experimental", "experimental_ndc_focus", "guardia_k_modis"):
        cfg = yaml.safe_load((PERFILES / f"{n}.yaml").read_text(encoding="utf-8"))
        assert (cfg.get("thresholds") or {}).get("enable_modis_codigo_mirova") is False, n


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
    assert not sin_decidir, f"perfiles vivos sin valor decidido de la vía de MODIS: {sorted(sin_decidir)}"


def test_control_el_instrumento_ve_un_perfil_que_hereda():
    """Si `experimental` no declarara el flag, lo resolvería igual que producción: True."""
    res = _resueltos(["mirova_equivalent", "_s146_ab_sin_test1"])   # un brazo viejo de A/B que no lo declara
    assert res["mirova_equivalent"] is True and res["_s146_ab_sin_test1"] is True


def test_la_sombra_de_los_34_entra_a_vivos_solo_si_existe():
    """S173 (hallazgo 201, experiments/_s173_aud/f2/INFORME.md; confirmado por V2): #932 agrega `sombra_34`, un perfil
    derivado programado (sombra-34.yml) que declara la vía de MODIS encendida a propósito, igual que la sombra de los
    11. Sin esta entrada, el segundo de B y #932 en entrar dejaba este guard en rojo en main. Si #932 no entró, el
    perfil no existe y no se exige: el guard no puede depender del orden de los merges."""
    existe = (PERFILES / "sombra_34.yaml").exists()
    assert ("sombra_34" in VIVOS) is existe
    if existe:
        assert VIVOS["sombra_34"] is True
