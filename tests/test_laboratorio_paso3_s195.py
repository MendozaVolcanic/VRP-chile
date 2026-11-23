# -*- coding: utf-8 -*-
"""S195: la zona A del laboratorio en la vía (paso 3 del plan docs/PLAN_EXPERIMENTAL_S190.md) y el barrido de 9 brazos.

EL FENÓMENO. Un foco chico en el cráter calienta su celda lo justo para quedar bajo el umbral contextual de MIROVA,
max(mu + s2·sd, piso) con s2 = 5 de noche en la región sensible. La zona A cambia sólo ese multiplicador, a s_A, en
las celdas sensibles a no más de inner_radius_km del cráter (decisión (a) de Nicolás, 2026-11-22: el círculo cortado
por la región sensible, para que s_A = 5 sea producción exacta y el control sellado del barrido valga). Mismos pisos,
mismos mu y sd, sólo de noche, Cordón Caulle fuera.

QUÉ VIGILA (P1 a P8 del plan docs/superpowers/plans/2026-11-22-laboratorio-paso3.md):
  P1 con la zona apagada el record es el de producción, byte a byte, en los tres sensores;
  P2 con la zona encendida y s_A = 5 también (escena con calor y escena débil);
  P3 con s_A chico algo cambia de verdad, y sólo dentro de la intersección;
  P4 sólo de noche;  P5 Cordón Caulle fuera;  P6 monótono y con tope s_A <= s2;
  P7 los perfiles del barrido difieren del laboratorio sólo en lo declarado;
  P8 el workflow del barrido no publica nada y corre los 10 perfiles en el mismo job.

LAS DOS PREGUNTAS DEL INSTRUMENTO. Toda igualdad tiene su control de que no es la de dos escenas vacías (VRP > 0 o el
foco débil alertado con s chico); la intersección se calcula en el script de la pasada con las funciones de producción
y no con la de la vía. Las mutaciones atrapadas están en experiments/_s195_lab_paso3/.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[1]
PERFILES = RAIZ / "pipeline" / "profiles"
SCRIPT = RAIZ / "tests" / "_pasada_sintetica_laboratorio.py"
FLUJO = RAIZ / ".github" / "workflows" / "reproc-s195-lab-barrido.yml"
FAMILIAS = ("MODIS", "VIIRS750", "VIIRS375")
CONTROL = "_s195_lab_control"
COD = ("import json, pipeline.profile as p; print('@@' + json.dumps({k: repr(getattr(p, k)) for k in dir(p) "
       "if k.isupper() and k != 'VALID_PROFILES'}))")


def _grilla_sellada():
    spec = importlib.util.spec_from_file_location("evaluar_s194", RAIZ / "experiments" / "_s194_lab_zona_a" / "evaluar.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return tuple(m.GRILLA_S)


GRILLA_S = _grilla_sellada()


def brazo(s: float) -> str:
    return "_s195_lab_s%02d" % round(s * 10)


BRAZOS = tuple(brazo(s) for s in GRILLA_S)


def _correr(args, perfil):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, cwd=RAIZ, timeout=900,
                          env=dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8"))


def _arroba(salida, quien):
    assert salida.returncode == 0, f"{quien} no corrió: {salida.stderr[-800:]}"
    lineas = [l for l in salida.stdout.splitlines() if l.startswith("@@")]
    assert lineas, f"{quien} no imprimió su volcado: {salida.stdout[-300:]}"
    return json.loads(lineas[-1][2:])


def _alertados(rec):
    return {(p["fila"], p["col"]) for p in (rec.get("anomaly_pixels") or [])}


# ------------------------------------------------------------------------------------------------ P1 y P2 (calor)
@pytest.fixture(scope="module")
def calor():
    perfiles = ("mirova_equivalent", "laboratorio", CONTROL, brazo(5.0))
    return {p: _arroba(_correr([str(SCRIPT)], p), f"la pasada con calor ({p})") for p in perfiles}


@pytest.mark.parametrize("familia", FAMILIAS)
def test_p1_p2_control_la_escena_con_calor_detecta_con_la_via(calor, familia):
    for perfil, rs in calor.items():
        r = rs[familia]
        assert r.get("via_codigo_mirova") is True and (r.get("vrp_mw") or 0) > 0, (perfil, familia, r.get("vrp_mw"))


@pytest.mark.parametrize("perfil", ("laboratorio", CONTROL, "_s195_lab_s50"))
@pytest.mark.parametrize("familia", FAMILIAS)
def test_p1_p2_zona_apagada_o_s5_es_produccion_byte_a_byte_con_calor(calor, perfil, familia):
    a = json.dumps(calor[perfil][familia], sort_keys=True, default=float)
    b = json.dumps(calor["mirova_equivalent"][familia], sort_keys=True, default=float)
    assert a == b


# ------------------------------------------------------------------------------------------------ P2 y P3 (débil)
@pytest.fixture(scope="module")
def debil():
    perfiles = ("mirova_equivalent", CONTROL, brazo(5.0), brazo(1.0))
    return {p: _arroba(_correr([str(SCRIPT), "debil"], p), f"la pasada débil ({p})") for p in perfiles}


@pytest.mark.parametrize("perfil", (CONTROL, "_s195_lab_s50"))
@pytest.mark.parametrize("familia", FAMILIAS)
def test_p2_s5_es_produccion_byte_a_byte_con_la_escena_debil(debil, perfil, familia):
    a = json.dumps(debil[perfil][familia]["record"], sort_keys=True, default=float)
    b = json.dumps(debil["mirova_equivalent"][familia]["record"], sort_keys=True, default=float)
    assert a == b


@pytest.mark.parametrize("familia", FAMILIAS)
def test_p3_con_s_chico_aparecen_alertados_nuevos_y_todos_en_la_interseccion(debil, familia):
    prod = _alertados(debil["mirova_equivalent"][familia]["record"])
    lab = _alertados(debil[brazo(1.0)][familia]["record"])
    zona = {tuple(c) for c in debil[brazo(1.0)][familia]["zona"]}
    assert zona, f"control: la intersección de {familia} no puede ser vacía en Villarrica"
    nuevos = lab - prod
    assert nuevos, f"{familia}: con s = 1 la zona A no alertó nada nuevo (nulo silencioso, A87)"
    assert nuevos <= zona, f"{familia}: alertados nuevos fuera de la intersección: {sorted(nuevos - zona)}"
    assert prod <= lab, f"{familia}: con s chico se perdió un alertado de producción: {sorted(prod - lab)}"


def test_p3_control_el_foco_del_anillo_existe_y_no_alerta_en_ningun_perfil(debil):
    """El foco del anillo (dentro del círculo, fuera de la región sensible) es igual al del cráter. Si alertara con
    s = 1, la zona sería el círculo entero (la opción que Nicolás no eligió). Control: el foco del cráter sí alerta con
    s = 1 en los tres sensores (P3), así que el del anillo no alerta porque está fuera, no porque sea frío."""
    for familia in FAMILIAS:
        lab = _alertados(debil[brazo(1.0)][familia]["record"])
        zona = {tuple(c) for c in debil[brazo(1.0)][familia]["zona"]}
        assert lab - zona == _alertados(debil["mirova_equivalent"][familia]["record"]) - zona, familia


# ------------------------------------------------------------------------------------------------ detector puro
def _escena(semilla=5, n=40, ruido=0.004):
    rng = np.random.default_rng(semilla)
    from pipeline import mirova_v750_codigo as MV
    t = 268.0 + rng.normal(0, 0.4, (n, n))
    m15 = MV.temperatura_a_radiancia(t - 3.0, MV.LAMBDA_M15)
    m13 = MV.temperatura_a_radiancia(t + rng.normal(0, 2.0, (n, n)), MV.LAMBDA_M13)
    m13[20, 20] = MV.temperatura_a_radiancia(274.0, MV.LAMBDA_M13)
    box = MV.caja_roi("def", n=n, lado_sensible=7, lado_anillo=21)
    return MV, m13, m15, box


def _zona_del_centro(box, radio_celdas=2.5):
    r, q = np.indices(box.shape)
    c = box.shape[0] // 2
    return (box == 2) & (np.hypot(r - c, q - c) <= radio_celdas)


def test_p4_la_zona_no_actua_de_dia():
    MV, m13, m15, box = _escena()
    zona = _zona_del_centro(box)
    sin = MV.detectar_mirova(m13, m15, box, 1, 90.0)
    con = MV.detectar_mirova(m13, m15, box, 1, 90.0, zona_a=zona, s_a=1.0)
    assert np.array_equal(sin, con)
    # control: de noche la misma zona sí cambia algo
    assert not np.array_equal(MV.detectar_mirova(m13, m15, box, 0, 90.0),
                              MV.detectar_mirova(m13, m15, box, 0, 90.0, zona_a=zona, s_a=1.0))


def test_p6_monotono_al_bajar_s_y_nunca_fuera_de_la_zona():
    MV, m13, m15, box = _escena()
    zona = _zona_del_centro(box)
    base = MV.detectar_mirova(m13, m15, box, 0, 90.0)
    previo = base
    for s in GRILLA_S:
        m = MV.detectar_mirova(m13, m15, box, 0, 90.0, zona_a=zona, s_a=s)
        assert np.all(m >= previo), f"s = {s} perdió alertados respecto del s anterior"
        assert np.array_equal(m & ~zona, base & ~zona), f"s = {s} cambió algo fuera de la zona A"
        previo = m
    assert previo.sum() > base.sum(), "control: con s = 1 la escena debe alertar más que producción"
    assert np.array_equal(MV.detectar_mirova(m13, m15, box, 0, 90.0, zona_a=zona, s_a=5.0), base)


def test_la_celda_decisiva_de_la_zona_se_mide_contra_el_umbral_de_la_zona():
    """El diagnóstico S-1 (diag_codigo_mirova.s1) dice cuánto le faltó al cráter para alertar contra SU umbral. En la
    zona A con s chico ese umbral es u_ntiA y u_etiA; medirlo contra u2 diría «le faltó» a una celda que alertó."""
    MV, m13, m15, box = _escena()
    zona = _zona_del_centro(box)
    _, d = MV.detectar_mirova(m13, m15, box, 0, 90.0, devolver_diag=True, zona_a=zona, s_a=1.0)
    cd = MV.celda_decisiva(d, (20, 20), radio=1)
    assert cd is not None and zona[cd["fila"], cd["col"]], cd
    dp = d["pasada%d" % cd["pase"]]
    assert dp["u_ntiA"] < dp["u_nti2"], "control: con s = 1 el umbral de la zona es menor que u2"
    assert (cd["u_nti"], cd["u_eti"]) == (dp["u_ntiA"], dp["u_etiA"]), cd


def test_p6_un_multiplicador_mayor_que_s2_es_error():
    MV, m13, m15, box = _escena()
    zona = _zona_del_centro(box)
    MV.detectar_mirova(m13, m15, box, 0, 90.0, zona_a=zona, s_a=5.0)   # control: el tope exacto pasa
    with pytest.raises(ValueError, match="s2"):
        MV.detectar_mirova(m13, m15, box, 0, 90.0, zona_a=zona, s_a=6.0)


def test_la_mascara_es_la_interseccion_del_circulo_con_la_region_sensible():
    from pipeline import mirova_v750_codigo as MV
    box = MV.caja_roi("def", n=41, lado_sensible=7, lado_anillo=21)
    pos = (20.0, 20.0)
    m = MV.mascara_zona_a(box, pos, 750.0, 1.6)    # radio de 2,13 celdas: corta la caja de 7 x 7
    r, q = np.indices(box.shape)
    esperado = (box == 2) & (np.hypot(r - 20, q - 20) * 0.75 <= 1.6)
    assert np.array_equal(m, esperado)
    assert 0 < m.sum() < (box == 2).sum(), "control: el círculo corta la caja sensible"
    grande = MV.mascara_zona_a(box, pos, 750.0, 10.0)   # círculo que contiene toda la caja y parte del anillo
    assert np.array_equal(grande, box == 2), "fuera de la región sensible nunca es zona A"


# ------------------------------------------------------------------------------------------------ P5
def _s_zona_a(perfil, volcan):
    cod = ("import json; from pipeline import mirova_v750_codigo as MV; "
           f"print('@@' + json.dumps(MV.s_zona_a({volcan!r})))")
    return _arroba(_correr(["-c", cod], perfil), f"s_zona_a ({perfil}, {volcan})")


def test_p5_cordon_caulle_queda_fuera_y_la_zona_apagada_no_da_multiplicador():
    assert _s_zona_a(brazo(2.0), "Villarrica") == 2.0                  # control: encendida, un volcán dentro
    assert _s_zona_a(brazo(2.0), "PuyehueCordonCaulle") is None
    for perfil in ("mirova_equivalent", "laboratorio", CONTROL, "guardia_k_modis", "guardia_k_viirs", "sombra_34"):
        assert _s_zona_a(perfil, "Villarrica") is None, perfil


# ------------------------------------------------------------------------------------------------ P7
@pytest.fixture(scope="module")
def resueltos():
    return {p: _arroba(_correr(["-c", COD], p), f"el perfil {p}") for p in ("laboratorio", CONTROL, *BRAZOS)}


def test_p7_los_brazos_son_la_grilla_sellada():
    assert GRILLA_S[0] == 5.0 and len(GRILLA_S) == 9, GRILLA_S
    existen = sorted(p.stem for p in PERFILES.glob("_s195_lab_*.yaml"))
    assert existen == sorted((CONTROL, *BRAZOS)), existen


def test_p7_el_control_es_el_laboratorio_en_otra_carpeta(resueltos):
    lab, ctl = resueltos["laboratorio"], resueltos[CONTROL]
    assert {k for k in set(lab) | set(ctl) if lab.get(k) != ctl.get(k)} == {"PROFILE_NAME", "DATA_SUBDIR"}
    assert ast.literal_eval(ctl["DATA_SUBDIR"]) == CONTROL


@pytest.mark.parametrize("s", GRILLA_S)
def test_p7_cada_brazo_difiere_del_laboratorio_solo_en_la_zona(resueltos, s):
    lab, b = resueltos["laboratorio"], resueltos[brazo(s)]
    difieren = {k for k in set(lab) | set(b) if lab.get(k) != b.get(k)}
    assert difieren == {"PROFILE_NAME", "DATA_SUBDIR", "ENABLE_LAB_ZONA_A", "LAB_ZONA_A"}, difieren
    assert ast.literal_eval(b["DATA_SUBDIR"]) == brazo(s)
    assert b["ENABLE_LAB_ZONA_A"] == "True"
    z_lab, z_b = ast.literal_eval(lab["LAB_ZONA_A"]), ast.literal_eval(b["LAB_ZONA_A"])
    assert {k for k in set(z_lab) | set(z_b) if z_lab.get(k) != z_b.get(k)} == {"valor"}
    assert z_b["valor"] == s


# ------------------------------------------------------------------------------------------------ P8
def test_p8_el_workflow_del_barrido_es_manual_no_publica_y_corre_los_diez_perfiles():
    texto = FLUJO.read_text(encoding="utf-8")
    import yaml
    doc = yaml.safe_load(texto)
    assert list(doc["on"]) == ["workflow_dispatch"], doc["on"]          # A43: "on" entre comillas
    assert not re.search(r"git push[^\n]*\bmain\b", texto), "el barrido no pushea a main"
    assert not re.search(r"git add[^\n]*data/", texto), "el barrido no agrega records al árbol de datos"
    assert not re.search(r"\b(?:mirova_equivalent|laboratorio_v1)/", texto), "el barrido no toca carpetas publicadas"
    assert "scripts/reproc_brazos.py" in texto
    for p in (CONTROL, *BRAZOS):
        assert re.search(rf"\b{p}\b", texto), f"el workflow no nombra {p}"
    assert "EARTHDATA_TOKEN" in texto and "EARTHDATA_PASSWORD" not in texto, "A71: sólo el token"


# ------------------------------------------------------------------------------------------------ comparar_control
def _cargar_comparador():
    spec = importlib.util.spec_from_file_location("comparar_control_s195",
                                                  RAIZ / "experiments" / "_s195_lab_paso3" / "comparar_control.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _store(d, nombre, recs):
    d.mkdir(parents=True, exist_ok=True)
    (d / nombre).write_text(json.dumps({"volcano": nombre[:-5], "records": recs}), encoding="utf-8")


def test_el_comparador_del_recolector_ve_identidad_diferencia_y_cobertura(tmp_path):
    m = _cargar_comparador()
    r1 = {"granule": "g1", "sensor": "VIIRS_SNPP", "datetime_utc": "t1", "vrp_mw": 1.0, "processed_utc": "a",
          "regimen": {"perfil": "_s195_lab_control"}}
    r2 = {"granule": "g2", "sensor": "MODIS_AQUA", "datetime_utc": "t2", "vrp_mw": 0.0}
    _store(tmp_path / "c", "Villarrica.json", [r1, r2])
    # el almacén cambia processed_utc y regimen entre perfiles: no cuentan
    _store(tmp_path / "b", "Villarrica.json", [dict(r1, processed_utc="b", regimen={"perfil": "_s195_lab_s50"}), r2])
    assert m.main(["--control", str(tmp_path / "c"), "--brazo", str(tmp_path / "b")]) == 0
    _store(tmp_path / "d", "Villarrica.json", [dict(r1, vrp_mw=1.001), r2])
    assert m.main(["--control", str(tmp_path / "c"), "--brazo", str(tmp_path / "d")]) == 1
    _store(tmp_path / "e", "Villarrica.json", [r1])
    assert m.main(["--control", str(tmp_path / "c"), "--brazo", str(tmp_path / "e")]) == 1
    _store(tmp_path / "v1", "Villarrica.json", [])
    _store(tmp_path / "v2", "Villarrica.json", [])
    assert m.main(["--control", str(tmp_path / "v1"), "--brazo", str(tmp_path / "v2")]) == 2   # nada que comparar
    assert m.main(["--control", str(tmp_path / "c"), "--brazo", str(tmp_path / "no_existe")]) == 2
