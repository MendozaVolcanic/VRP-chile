# -*- coding: utf-8 -*-
"""S193: guards del perfil `laboratorio` (paso 1 del plan docs/PLAN_EXPERIMENTAL_S190.md, §4 guards 1 a 4).

EL FENÓMENO. Un foco chico en el cráter (lago de lava, campo fumarólico) calienta su píxel lo justo para quedar al
borde del umbral de MIROVA. La réplica copia ese umbral a propósito. El laboratorio existe para bajarlo sólo en la zona
A (el círculo de inner_radius_km alrededor del cráter) y medir lo que aparece contra NHI y persistencia, nunca contra
MIROVA (A115). En este paso la zona A existe en la configuración y está APAGADA: el laboratorio tiene que ser hoy
exactamente la vía de producción, en otra carpeta.

QUÉ VIGILA (G1 a G7 del plan docs/superpowers/plans/2026-11-21-laboratorio-paso1.md; G8 vive en el guard S147):
  G1 difiere de producción sólo en lo declarado (resuelto como lo resuelve el código, VRP_PROFILE, nunca el YAML: A89);
  G2 con la zona apagada, el record de una misma pasada es el de producción en los tres sensores;
  G3 no escribe en data/mirova_equivalent;
  G4 producción no cambia: resuelve la zona apagada y vacía, ningún otro perfil la declara y nadie en pipeline/ la lee
     (S195: salvo la vía, en s_zona_a, y los perfiles del barrido);
  G5 el tablero operacional no lee la carpeta del laboratorio;
  G6 el commit del NRT no la agrega y ningún workflow corre el perfil (el cron es el paso 4, por tandas, D7);
  G7 encender la zona antes de que la vía la implemente es un error, no un nulo silencioso (S195: la vía ya la
     implementa; el error queda para encenderla sin valor).

LAS DOS PREGUNTAS DEL INSTRUMENTO. Cada búsqueda de texto tiene un control que la misma expresión encuentra lo que
debe encontrar (A92, A116), y la comparación de records exige que los tres sean de la vía y con VRP > 0 (dos escenas
vacías serían iguales sin probar nada). Las mutaciones atrapadas están en la descripción del PR.
"""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
PERFILES = RAIZ / "pipeline" / "profiles"
COD = ("import json, pipeline.profile as p; print('@@' + json.dumps({k: repr(getattr(p, k)) for k in dir(p) "
       "if k.isupper() and k != 'VALID_PROFILES'}))")
# G1: lo único que el laboratorio declara distinto. PROFILE_NAME y DATA_SUBDIR son su identidad; LAB_ZONA_A es la
# extensión MEJ-5 (zona A) declarada y apagada. Una segunda diferencia sin declarar pone esto en rojo.
# ⚠️ S193 (A113; A/B #813, decisión de Nicolás del 2026-11-21): producción enciende el día de MODIS y el laboratorio,
# que no se midió de día, lo declara apagado (pipeline/profiles/laboratorio.yaml, `paths`). Texto original: sin
# ENABLE_DAYTIME_MODIS.
DIFERENCIAS_DECLARADAS = {"PROFILE_NAME", "DATA_SUBDIR", "LAB_ZONA_A", "ENABLE_DAYTIME_MODIS"}
CLAVES_ZONA = re.compile(r"\b(?:enable_lab_zona_a|laboratorio_zona_a)\b")
LECTURA_ZONA = re.compile(r"\b(?:ENABLE_LAB_ZONA_A|LAB_ZONA_A)\b")


def _correr(args, perfil, **kw):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, cwd=RAIZ, timeout=600,
                          env=dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8"), **kw)


def _arroba(salida, quien):
    assert salida.returncode == 0, f"{quien} no corrió: {salida.stderr[-600:]}"
    lineas = [l for l in salida.stdout.splitlines() if l.startswith("@@")]
    assert lineas, f"{quien} no imprimió su volcado: {salida.stdout[-300:]}"
    return json.loads(lineas[-1][2:])


def _resolver(perfil):
    return _arroba(_correr(["-c", COD], perfil), f"el perfil {perfil}")


@pytest.fixture(scope="module")
def resueltos():
    return {p: _resolver(p) for p in ("laboratorio", "mirova_equivalent")}


# ------------------------------------------------------------------------------------------------ G1
def test_g1_el_laboratorio_difiere_de_produccion_solo_en_lo_declarado(resueltos):
    lab, prod = resueltos["laboratorio"], resueltos["mirova_equivalent"]
    difieren = {k for k in set(lab) | set(prod) if lab.get(k) != prod.get(k)}
    assert difieren == DIFERENCIAS_DECLARADAS, difieren
    assert (lab["ENABLE_DAYTIME_MODIS"], prod["ENABLE_DAYTIME_MODIS"]) == ("False", "True")


def test_g1_la_via_esta_encendida_en_los_tres_sensores_y_la_zona_apagada(resueltos):
    """D2 (a): la base es la vía de producción. Si producción la apagara, G1 seguiría verde (el laboratorio la sigue);
    esto dice que hoy el laboratorio mide sobre la vía, que es lo que el plan S190 aprobó."""
    lab = resueltos["laboratorio"]
    for flag in ("ENABLE_MODIS_CODIGO_MIROVA", "ENABLE_V375_CODIGO_MIROVA", "ENABLE_V750_CODIGO_MIROVA"):
        assert lab.get(flag) == "True", (flag, lab.get(flag))
    assert lab.get("ENABLE_LAB_ZONA_A") == "False", lab.get("ENABLE_LAB_ZONA_A")
    zona = ast.literal_eval(lab["LAB_ZONA_A"])
    assert zona.get("extension") == "MEJ-5" and zona.get("radio") == "inner_radius_km", zona
    # S195 (paso 3): la zona ya tiene efecto en la vía, pero el laboratorio sigue apagado y sin valor: el valor sale del
    # barrido de 9 brazos (perfiles _s195_lab_*, evaluar.py calibrar) y lo fija el paso 4. Texto anterior del mensaje:
    # «el umbral de la zona A se elige en el paso 3 del plan S190, no antes».
    assert zona.get("valor") is None, f"el valor de la zona A del laboratorio lo fija el paso 4, tras el barrido: {zona}"
    assert "PuyehueCordonCaulle" in zona.get("volcanes_fuera", []), f"D6: Cordón Caulle fuera de la primera tanda: {zona}"


# ------------------------------------------------------------------------------------------------ G2
@pytest.fixture(scope="module")
def records():
    return {p: _arroba(_correr([str(RAIZ / "tests" / "_pasada_sintetica_laboratorio.py")], p), f"la pasada ({p})")
            for p in ("laboratorio", "mirova_equivalent")}


@pytest.mark.parametrize("familia", ("MODIS", "VIIRS750", "VIIRS375"))
def test_g2_control_la_pasada_sintetica_detecta_con_la_via(records, familia):
    """Sin esto, dos escenas vacías (o dos records de K) serían iguales sin probar nada."""
    for perfil, rs in records.items():
        r = rs.get(familia) or {}
        assert r.get("via_codigo_mirova") is True, (perfil, familia, r.get("via_codigo_mirova"))
        assert (r.get("vrp_mw") or 0) > 0, (perfil, familia, r.get("vrp_mw"))


@pytest.mark.parametrize("familia", ("MODIS", "VIIRS750", "VIIRS375"))
def test_g2_con_la_zona_apagada_el_record_es_el_de_produccion(records, familia):
    """Igualdad exacta del JSON: mismo proceso, mismos datos, misma CPU. El almacén agrega después la procedencia
    con el nombre del perfil (pipeline/store.py), que es identidad declarada (G1), no resultado."""
    assert records["laboratorio"][familia] == records["mirova_equivalent"][familia]


# ------------------------------------------------------------------------------------------------ G3
def test_g3_el_laboratorio_escribe_en_su_carpeta_y_no_en_la_de_produccion():
    cod = "import pipeline.store as s; print('@@' + __import__('json').dumps(s.DATA_DIR.as_posix()))"
    lab = _arroba(_correr(["-c", cod], "laboratorio"), "store (laboratorio)")
    prod = _arroba(_correr(["-c", cod], "mirova_equivalent"), "store (producción)")
    assert prod.endswith("/data/mirova_equivalent"), prod   # control: el instrumento ve la de producción
    assert lab.endswith("/data/laboratorio_v1"), lab
    assert lab != prod


# ------------------------------------------------------------------------------------------------ G4
def test_g4_produccion_resuelve_la_zona_apagada_y_vacia(resueltos):
    prod = resueltos["mirova_equivalent"]
    assert prod.get("ENABLE_LAB_ZONA_A") == "False", prod.get("ENABLE_LAB_ZONA_A")
    assert prod.get("LAB_ZONA_A") == "{}", prod.get("LAB_ZONA_A")


# S195 (paso 3): los 10 perfiles del barrido (control y 9 brazos, tests/test_laboratorio_paso3_s195.py P7) también la
# declaran. Texto anterior: sólo laboratorio.yaml.
PERFILES_CON_ZONA = sorted(["laboratorio.yaml", "_s195_lab_control.yaml"]
                           + ["_s195_lab_s%02d.yaml" % t for t in (50, 45, 40, 35, 30, 25, 20, 15, 10)])


def test_g4_ningun_otro_perfil_declara_la_zona():
    declaran = sorted(p.relative_to(PERFILES).as_posix() for p in PERFILES.rglob("*.yaml")
                      if CLAVES_ZONA.search(p.read_text(encoding="utf-8")))
    assert declaran == PERFILES_CON_ZONA, declaran     # control incluido: el laboratorio sí la declara


def test_g4_nadie_en_pipeline_lee_la_zona_fuera_de_profile_py_y_la_via():
    """S195 (paso 3, A45 de Nicolás del 2026-11-22): la vía la lee, en un solo lugar (s_zona_a), y ningún procesador ni
    el almacén. Una lectura nueva es un cambio de detección y tiene que actualizar esta prueba a conciencia (A45).
    Texto anterior: «Mientras la zona no tenga efecto (paso 3), ningún procesador la lee», con sólo profile.py."""
    fuentes = list((RAIZ / "pipeline").glob("*.py")) + [RAIZ / "scripts" / "run_pipeline.py"]
    leen = sorted(p.name for p in fuentes if LECTURA_ZONA.search(p.read_text(encoding="utf-8")))
    assert leen == ["mirova_v750_codigo.py", "profile.py"], leen    # control incluido: profile.py sí la lee
    via = (RAIZ / "pipeline" / "mirova_v750_codigo.py").read_text(encoding="utf-8")
    assert len(LECTURA_ZONA.findall(via)) == 2, "la vía lee el flag y el bloque una sola vez, en s_zona_a"


# ------------------------------------------------------------------------------------------------ G5
@pytest.mark.parametrize("pagina", ("index.html", "diario.html", "mosaico.html"))
def test_g5_el_tablero_operacional_no_lee_el_laboratorio(pagina):
    texto = (RAIZ / "frontend" / pagina).read_text(encoding="utf-8")
    assert re.search(r"\bmirova_equivalent\b", texto), f"control: {pagina} no nombra mirova_equivalent"
    assert not re.search(r"\blaboratorio_v1\b", texto), f"{pagina} lee la carpeta del laboratorio"


# ------------------------------------------------------------------------------------------------ G6
def test_g6_el_commit_del_nrt_no_agrega_el_laboratorio():
    texto = (RAIZ / ".github" / "workflows" / "nrt.yml").read_text(encoding="utf-8")
    rutas = re.findall(r"git add\s+\"?(data/[^\"\s]+)", texto)
    assert rutas, "control: no se encontró ningún git add de data/ en nrt.yml"
    ajenas = [r for r in rutas if not re.match(r"data/(?:mirova_equivalent|experimental|mirova)/", r)]
    assert not ajenas, ajenas


CORRE_PERFIL = r"(?:--profile[\s=]+|VRP_PROFILE\s*[=:]\s*|profile\s*==\s*)['\"]?{}\b"


def test_g6_ningun_workflow_corre_el_laboratorio():
    flujos = sorted((RAIZ / ".github" / "workflows").glob("*.yml"))
    textos = {p.name: p.read_text(encoding="utf-8") for p in flujos}
    assert any(re.search(CORRE_PERFIL.format("experimental"), t) for t in textos.values()), \
        "control: la expresión no encuentra cómo se corre el perfil experimental"
    corren = sorted(n for n, t in textos.items()
                    if re.search(CORRE_PERFIL.format("laboratorio"), t) or re.search(r"\blaboratorio_v1\b", t))
    assert not corren, f"el laboratorio entra al cron por tandas en el paso 4 del plan S190, no antes: {corren}"


# ------------------------------------------------------------------------------------------------ G7
def test_g7_encender_la_zona_sin_valor_es_un_error():
    """S195 (paso 3): la vía ya implementa la zona, así que encenderla deja de ser error; encenderla SIN valor (o sin
    el bloque) sigue siéndolo, porque correría idéntico a producción creyendo medir la extensión (A87). Texto anterior:
    test_g7_encender_la_zona_antes_de_implementarla_es_un_error (encender era siempre error)."""
    from pipeline import profile as P
    zona = {"extension": "MEJ-5", "radio": "inner_radius_km", "parametro": "sigma_contextual_nocturno",
            "valor": None, "volcanes_fuera": ["PuyehueCordonCaulle"]}
    assert P._zona_a_de({"enable_lab_zona_a": False}, {"laboratorio_zona_a": zona}) == (False, zona)  # control
    assert P._zona_a_de({}, {}) == (False, {})
    con_valor = {**zona, "valor": 2.5}
    assert P._zona_a_de({"enable_lab_zona_a": True}, {"laboratorio_zona_a": con_valor}) == (True, con_valor)
    with pytest.raises(ValueError, match="zona A"):
        P._zona_a_de({"enable_lab_zona_a": True}, {"laboratorio_zona_a": zona})
    with pytest.raises(ValueError, match="zona A"):
        P._zona_a_de({"enable_lab_zona_a": True}, {})


@pytest.mark.parametrize("malo", ({"radio": "radius_km"}, {"parametro": "piso_nti"}, {"valor": -1.0},
                                  {"valor": "5"}, {"volcanes_fuera": "PuyehueCordonCaulle"}))
def test_g7_una_zona_mal_escrita_no_carga(malo):
    from pipeline import profile as P
    zona = {"extension": "MEJ-5", "radio": "inner_radius_km", "parametro": "sigma_contextual_nocturno",
            "valor": None, "volcanes_fuera": ["PuyehueCordonCaulle"]}
    with pytest.raises(ValueError):
        P._zona_a_de({"enable_lab_zona_a": False}, {"laboratorio_zona_a": {**zona, **malo}})
