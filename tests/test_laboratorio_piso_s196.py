# -*- coding: utf-8 -*-
"""S196: el piso del umbral contextual nocturno en la zona A del laboratorio (pre-registro sellado
experiments/_s196_lab_piso/PREREGISTRO.md, §3, §5 y §9; A45 de Nicolás del 2026-11-23, «Sí, A45 (Recomendado)»).

EL FENÓMENO. En la región sensible, de noche, el umbral es max(mu + s·sd, piso) en NTI y en ETI. En una escena quieta
(fondo parejo, sd chica) manda el piso fijo de 0,003 y un foco que contrasta 0,002 queda fuera. La palanca baja ese
piso, a p_A, sólo en la zona A (región sensible a no más de inner_radius_km del cráter), sólo de noche, con s = s_A, y
nunca por encima del piso de producción. Con s_A = 5 y p_A = 0,003 el detector es producción bit a bit.

QUÉ VIGILA.
  Q1 identidad: el brazo sin zona y el control (s = 5, piso 0,003) son producción byte a byte en tres escenas y tres
     sensores; el brazo (s_A, 0,003) es el brazo s = 3,0 del barrido S195 byte a byte.
  Q2 efecto: en la escena quieta el piso menor alerta el foco del cráter, nunca el del anillo (fuera de la región
     sensible), nunca pierde un alertado de producción, y es monótono a lo largo de la grilla sellada.
  Q3 diagnóstico: u_ntiA y u_etiA quedan en el record cuando difieren de u_nti2 y u_eti2, y no cuando son iguales
     (así el control sigue siendo producción byte a byte).
  Q4 detector puro: no actúa de día; un piso mayor que el de producción o no positivo es error; fuera de la zona
     nada cambia en el primer pase.
  Q5 perfil: la clave piso se valida, se resuelve por volcán (Cordón Caulle fuera) y ningún perfil operacional la
     declara.
  Q6 los perfiles del barrido difieren del laboratorio sólo en lo declarado; Q7 el workflow es manual y no publica.
  Q8 el comparador «donde la zona no actúa» ve identidad, diferencia y vacío.

LAS DOS PREGUNTAS DEL INSTRUMENTO. Cada igualdad tiene su control de que no es la de dos escenas vacías (la escena con
calor detecta en todos los perfiles; el foco quieto alerta con el piso menor) y la zona se calcula con las funciones
de producción en el ayudante de la pasada, no con la de la vía.
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
FLUJO = RAIZ / ".github" / "workflows" / "reproc-s196-lab-piso.yml"
FAMILIAS = ("MODIS", "VIIRS750", "VIIRS375")
SINZONA = "_s196_lab_sinzona"
CONTROL = "_s196_lab_control"
COD = ("import json, pipeline.profile as p; print('@@' + json.dumps({k: repr(getattr(p, k)) for k in dir(p) "
       "if k.isupper() and k != 'VALID_PROFILES'}))")


def _cargar(ruta, nombre):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


EV = _cargar(RAIZ / "experiments" / "_s196_lab_piso" / "evaluar.py", "evaluar_piso_s196_para_codigo")
S_A, GRILLA, PISO_PROD = EV.S_A, EV.GRILLA_PISO, EV.PISO_PROD


def brazo(p: float) -> str:
    return "_s196_lab_p%03d" % round(p * 1e5)


BRAZOS = tuple(brazo(p) for p in GRILLA)


def _correr(args, perfil):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, cwd=RAIZ, timeout=900,
                          env=dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8"))


def _arroba(salida, quien):
    assert salida.returncode == 0, f"{quien} no corrió: {salida.stderr[-800:]}"
    lineas = [l for l in salida.stdout.splitlines() if l.startswith("@@")]
    assert lineas, f"{quien} no imprimió su volcado: {salida.stdout[-300:]}"
    return json.loads(lineas[-1][2:])


def _rec(salida, familia):
    v = salida[familia]
    return v["record"] if isinstance(v, dict) and "record" in v else v


def _alertados(rec):
    return {(p["fila"], p["col"]) for p in (rec.get("anomaly_pixels") or [])}


def _bytes(rec):
    return json.dumps(rec, sort_keys=True, default=float)


# ------------------------------------------------------------------------------------------------ Q1 identidad
@pytest.fixture(scope="module")
def escenas():
    perfiles = ("mirova_equivalent", SINZONA, CONTROL, brazo(PISO_PROD), "_s195_lab_s30", brazo(GRILLA[-1]))
    out = {}
    for escena in ("calor", "debil", "quieta"):
        args = [str(SCRIPT)] + ([] if escena == "calor" else [escena])
        out[escena] = {p: _arroba(_correr(args, p), f"la pasada {escena} ({p})") for p in perfiles}
    return out


@pytest.mark.parametrize("familia", FAMILIAS)
def test_q1_control_la_escena_con_calor_detecta_en_todos_los_perfiles(escenas, familia):
    for perfil, rs in escenas["calor"].items():
        r = _rec(rs, familia)
        assert r.get("via_codigo_mirova") is True and (r.get("vrp_mw") or 0) > 0, (perfil, familia, r.get("vrp_mw"))


@pytest.mark.parametrize("escena", ("calor", "debil", "quieta"))
@pytest.mark.parametrize("perfil", (SINZONA, CONTROL))
@pytest.mark.parametrize("familia", FAMILIAS)
def test_q1_sin_zona_y_control_son_produccion_byte_a_byte(escenas, escena, perfil, familia):
    assert _bytes(_rec(escenas[escena][perfil], familia)) == _bytes(_rec(escenas[escena]["mirova_equivalent"], familia))


@pytest.mark.parametrize("escena", ("calor", "debil", "quieta"))
@pytest.mark.parametrize("familia", FAMILIAS)
def test_q1_el_brazo_del_piso_de_hoy_es_el_brazo_s3_del_barrido_s195(escenas, escena, familia):
    """(s_A, 0,003) es el último punto del tramo de s y el primero del tramo de piso: tiene que ser el brazo s = 3,0
    del barrido S195 (el record sale de calculate_vrp, antes del almacén, así que no lleva el nombre del perfil)."""
    assert S_A == 3.0, "esta prueba nombra el brazo s = 3,0 del S195; con otro S_A, cambiarla"
    assert _bytes(_rec(escenas[escena][brazo(PISO_PROD)], familia)) == _bytes(
        _rec(escenas[escena]["_s195_lab_s30"], familia))


# ------------------------------------------------------------------------------------------------ Q2 efecto
@pytest.mark.parametrize("familia", FAMILIAS)
def test_q2_el_piso_menor_alerta_el_foco_quieto_del_crater_y_solo_en_la_zona(escenas, familia):
    q = escenas["quieta"]
    prod = _alertados(_rec(q["mirova_equivalent"], familia))
    hoy = _alertados(_rec(q[brazo(PISO_PROD)], familia))
    bajo = _alertados(_rec(q[brazo(GRILLA[-1])], familia))
    zona = {tuple(c) for c in q[brazo(GRILLA[-1])][familia]["zona"]}
    assert zona, f"control: la intersección de {familia} no puede ser vacía en Villarrica"
    assert hoy == prod, f"{familia}: con el piso de hoy la escena quieta no tiene que cambiar (manda el piso)"
    nuevos = bajo - prod
    assert nuevos, f"{familia}: con el piso {GRILLA[-1]} el foco quieto del cráter no alertó (nulo silencioso, A87)"
    assert nuevos <= zona, f"{familia}: alertados nuevos fuera de la zona A: {sorted(nuevos - zona)}"
    assert prod <= bajo, f"{familia}: con el piso menor se perdió un alertado de producción: {sorted(prod - bajo)}"


@pytest.fixture(scope="module")
def grilla_quieta():
    return {p: _arroba(_correr([str(SCRIPT), "quieta"], brazo(p)), f"la pasada quieta ({brazo(p)})") for p in GRILLA}


@pytest.mark.parametrize("familia", FAMILIAS)
def test_q2_monotono_a_lo_largo_de_la_grilla_sellada(grilla_quieta, familia):
    previo = None
    for p in GRILLA:
        a = _alertados(_rec(grilla_quieta[p], familia))
        if previo is not None:
            assert previo <= a, f"{familia}: el piso {p} perdió alertados del piso anterior"
        previo = a
    assert previo != _alertados(_rec(grilla_quieta[GRILLA[0]], familia)), f"control: {familia} no cambió en la grilla"


# ------------------------------------------------------------------------------------------------ Q3 diagnóstico
@pytest.mark.parametrize("familia", FAMILIAS)
def test_q3_el_umbral_de_la_zona_queda_en_el_record_solo_si_difiere(escenas, familia):
    s1 = _rec(escenas["quieta"][brazo(GRILLA[-1])], familia)["diag_codigo_mirova"]["s1"]["pasada1"]
    assert s1.get("u_etiA") is not None and s1["u_etiA"] < s1["u_eti2"], s1
    assert s1["u_etiA"] == pytest.approx(GRILLA[-1]), s1          # escena quieta: manda el piso de la zona
    ctl = _rec(escenas["quieta"][CONTROL], familia)["diag_codigo_mirova"]["s1"]["pasada1"]
    assert "u_ntiA" not in ctl and "u_etiA" not in ctl, ctl


# ------------------------------------------------------------------------------------------------ Q4 detector puro
def _escena_quieta(n=40, dt_foco=0.7, semilla=7):
    from pipeline import mirova_v750_codigo as MV
    rng = np.random.default_rng(semilla)
    t = 268.0 + rng.normal(0, 0.05, (n, n))
    m15 = MV.temperatura_a_radiancia(t - 3.0, MV.LAMBDA_M15)
    t_mir = t + rng.normal(0, 0.1, (n, n))
    t_mir[20, 20] += dt_foco
    m13 = MV.temperatura_a_radiancia(t_mir, MV.LAMBDA_M13)
    box = MV.caja_roi("def", n=n, lado_sensible=7, lado_anillo=21)
    r, q = np.indices(box.shape)
    zona = (box == 2) & (np.hypot(r - 20, q - 20) <= 2.5)
    return MV, m13, m15, box, zona


def test_q4_control_la_escena_pura_quieta_responde_al_piso():
    MV, m13, m15, box, zona = _escena_quieta()
    base = MV.detectar_mirova(m13, m15, box, 0, 90.0)
    bajo = MV.detectar_mirova(m13, m15, box, 0, 90.0, zona_a=zona, s_a=S_A, piso_a=GRILLA[-1])
    assert not base[20, 20] and bajo[20, 20], "control: el foco quieto alerta sólo con el piso menor"
    hoy = MV.detectar_mirova(m13, m15, box, 0, 90.0, zona_a=zona, s_a=S_A, piso_a=PISO_PROD)
    assert np.array_equal(hoy, MV.detectar_mirova(m13, m15, box, 0, 90.0, zona_a=zona, s_a=S_A)), (
        "piso_a igual al de producción tiene que ser lo mismo que no pasarlo")
    assert np.array_equal(MV.detectar_mirova(m13, m15, box, 0, 90.0, zona_a=zona, s_a=5.0, piso_a=PISO_PROD), base)


def test_q4_el_piso_no_actua_de_dia():
    MV, m13, m15, box, zona = _escena_quieta()
    sin = MV.detectar_mirova(m13, m15, box, 1, 90.0)
    con = MV.detectar_mirova(m13, m15, box, 1, 90.0, zona_a=zona, s_a=S_A, piso_a=GRILLA[-1])
    assert np.array_equal(sin, con)


def test_q4_fuera_de_la_zona_el_umbral_no_cambia():
    """El umbral sólo cambia en la zona; fuera, el resultado puede moverse por arrastre al segundo pase, así que se
    compara el umbral de cada celda y no la máscara."""
    MV, m13, m15, box, zona = _escena_quieta()
    _, d = MV.detectar_mirova(m13, m15, box, 0, 90.0, devolver_diag=True, zona_a=zona, s_a=S_A, piso_a=GRILLA[-1])
    _, b = MV.detectar_mirova(m13, m15, box, 0, 90.0, devolver_diag=True)
    for pase in ("pasada1",):
        assert d[pase]["u_nti1"] == b[pase]["u_nti1"] and d[pase]["u_eti1"] == b[pase]["u_eti1"]
        assert d[pase]["u_nti2"] == b[pase]["u_nti2"] and d[pase]["u_eti2"] == b[pase]["u_eti2"]
        assert d[pase]["u_etiA"] < d[pase]["u_eti2"], "control: dentro de la zona el umbral sí bajó"


def _tupla_nocturna():
    src = (RAIZ / "pipeline" / "mirova_v750_codigo.py").read_text(encoding="utf-8")
    m = re.search(r"if dayflag == 0:[^\n]*\n\s*u_abs, s1, s2, n1, n2, e1, e2 = ([^\n#]+)", src)
    return ast.literal_eval("(" + m.group(1).strip() + ")")


@pytest.mark.parametrize("pase", ("pasada1", "pasada2"))
def test_q4_fuera_de_la_zona_cada_umbral_es_la_formula_del_m(pase):
    """S196 (mutación piso_fuera_de_la_zona_u_nti1, que la prueba de arriba no atrapó): comparar con el detector sin
    piso no ve una fuga del piso al umbral del anillo cuando mu + 10·sd supera el piso de producción. Aquí cada umbral
    de fuera de la zona se recalcula con la fórmula del .m (l. 306-308 y 376-382) desde los mu y sd que el mismo pase
    guardó, con los pisos de producción: un piso que se cuela en cualquiera de los cuatro lo cambia."""
    MV, m13, m15, box, zona = _escena_quieta()
    _, s1, s2, n1, n2, e1, e2 = _tupla_nocturna()
    _, d = MV.detectar_mirova(m13, m15, box, 0, 90.0, devolver_diag=True, zona_a=zona, s_a=S_A, piso_a=GRILLA[-1])
    dp = d[pase]
    esperado = {"u_nti1": max(dp["mu_nti"] + s1 * dp["sd_nti"], n1), "u_nti2": max(dp["mu_nti"] + s2 * dp["sd_nti"], n2),
                "u_eti1": max(dp["mu_eti"] + s1 * dp["sd_eti"], e1), "u_eti2": max(dp["mu_eti"] + s2 * dp["sd_eti"], e2)}
    for k, v in esperado.items():
        assert dp[k] == v, (pase, k, dp[k], v)
    # control: el piso de la zona sí es menor que los de fuera, así que una fuga cambiaría al menos un umbral
    assert GRILLA[-1] < min(n1, n2, e1, e2) and dp["u_etiA"] < dp["u_eti2"], dp


@pytest.mark.parametrize("piso", (0.0031, 0.0, -0.001))
def test_q4_un_piso_mayor_que_el_de_produccion_o_no_positivo_es_error(piso):
    MV, m13, m15, box, zona = _escena_quieta()
    MV.detectar_mirova(m13, m15, box, 0, 90.0, zona_a=zona, s_a=S_A, piso_a=PISO_PROD)   # control: el tope pasa
    with pytest.raises(ValueError, match="piso"):
        MV.detectar_mirova(m13, m15, box, 0, 90.0, zona_a=zona, s_a=S_A, piso_a=piso)


def test_q4_la_celda_decisiva_se_mide_contra_el_piso_de_la_zona():
    MV, m13, m15, box, zona = _escena_quieta()
    _, d = MV.detectar_mirova(m13, m15, box, 0, 90.0, devolver_diag=True, zona_a=zona, s_a=S_A, piso_a=GRILLA[-1])
    cd = MV.celda_decisiva(d, (20, 20), radio=1)
    dp = d["pasada%d" % cd["pase"]]
    assert zona[cd["fila"], cd["col"]] and (cd["u_nti"], cd["u_eti"]) == (dp["u_ntiA"], dp["u_etiA"]), cd


# ------------------------------------------------------------------------------------------------ Q5 perfil
def _piso_zona_a(perfil, volcan):
    cod = ("import json; from pipeline import mirova_v750_codigo as MV; "
           f"print('@@' + json.dumps([MV.s_zona_a({volcan!r}), MV.piso_zona_a({volcan!r})]))")
    return _arroba(_correr(["-c", cod], perfil), f"piso_zona_a ({perfil}, {volcan})")


def test_q5_el_piso_se_resuelve_por_perfil_y_volcan():
    assert _piso_zona_a(brazo(GRILLA[-1]), "Villarrica") == [S_A, GRILLA[-1]]
    assert _piso_zona_a(CONTROL, "Villarrica") == [5.0, PISO_PROD]
    assert _piso_zona_a(brazo(GRILLA[-1]), "PuyehueCordonCaulle") == [None, None]
    assert _piso_zona_a("_s195_lab_s30", "Villarrica") == [3.0, None]          # sin la clave: piso de producción
    for perfil in ("mirova_equivalent", "laboratorio", SINZONA, "guardia_k_modis", "guardia_k_viirs", "sombra_34"):
        assert _piso_zona_a(perfil, "Villarrica") == [None, None], perfil


@pytest.mark.parametrize("piso", (-0.001, 0, "0,002", True))
def test_q5_el_perfil_rechaza_un_piso_invalido(piso):
    from pipeline import profile as P
    zona = {"radio": "inner_radius_km", "parametro": "sigma_contextual_nocturno", "valor": 3.0, "piso": piso}
    with pytest.raises(ValueError, match="piso"):
        P._zona_a_de({"enable_lab_zona_a": True}, {"laboratorio_zona_a": zona})
    zona["piso"] = 0.0015                                                     # control: uno válido pasa
    assert P._zona_a_de({"enable_lab_zona_a": True}, {"laboratorio_zona_a": zona})[1]["piso"] == 0.0015


def test_q5_ningun_perfil_operacional_declara_el_piso():
    for y in PERFILES.glob("*.yaml"):
        if y.stem.startswith("_s196_lab_"):
            continue
        assert not re.search(r"^\s*piso\s*:", y.read_text(encoding="utf-8"), re.M), y.name


@pytest.mark.parametrize("perfil", BRAZOS + (CONTROL,))
def test_q5_guard_s147_ningun_brazo_pasa_del_piso_ni_del_s_de_produccion(perfil):
    g = _cargar(RAIZ / "tests" / "test_guard_laboratorio_no_mas_ciego_s147.py", "guard_s147_para_s196")
    src = (RAIZ / "pipeline" / "mirova_v750_codigo.py").read_text(encoding="utf-8")
    m = re.search(r"if dayflag == 0:[^\n]*\n\s*u_abs, s1, s2, n1, n2, e1, e2 = ([^\n#]+)", src)
    _, _, s2, _, n2, _, e2 = ast.literal_eval("(" + m.group(1).strip() + ")")
    zona = g._zona_a_del_laboratorio(perfil)
    assert zona.get("valor") is not None and zona.get("piso") is not None, (perfil, zona)
    assert zona["valor"] <= s2 and 0 < zona["piso"] <= min(n2, e2), (perfil, zona, s2, n2, e2)


# ------------------------------------------------------------------------------------------------ Q6 perfiles
@pytest.fixture(scope="module")
def resueltos():
    return {p: _arroba(_correr(["-c", COD], p), f"el perfil {p}") for p in ("laboratorio", SINZONA, CONTROL, *BRAZOS)}


def test_q6_los_brazos_son_la_grilla_sellada():
    existen = sorted(p.stem for p in PERFILES.glob("_s196_lab_*.yaml"))
    assert existen == sorted((SINZONA, CONTROL, *BRAZOS)), existen
    assert len(BRAZOS) == 7 and brazo(0.003) == "_s196_lab_p300" and brazo(0.0015) == "_s196_lab_p150"


def test_q6_el_brazo_sin_zona_es_el_laboratorio_en_otra_carpeta(resueltos):
    lab, sz = resueltos["laboratorio"], resueltos[SINZONA]
    assert {k for k in set(lab) | set(sz) if lab.get(k) != sz.get(k)} == {"PROFILE_NAME", "DATA_SUBDIR"}
    assert ast.literal_eval(sz["DATA_SUBDIR"]) == SINZONA


@pytest.mark.parametrize("perfil", (CONTROL,) + BRAZOS)
def test_q6_cada_brazo_difiere_del_laboratorio_solo_en_la_zona(resueltos, perfil):
    lab, b = resueltos["laboratorio"], resueltos[perfil]
    difieren = {k for k in set(lab) | set(b) if lab.get(k) != b.get(k)}
    assert difieren == {"PROFILE_NAME", "DATA_SUBDIR", "ENABLE_LAB_ZONA_A", "LAB_ZONA_A"}, difieren
    assert ast.literal_eval(b["DATA_SUBDIR"]) == perfil and b["ENABLE_LAB_ZONA_A"] == "True"
    z_lab, z_b = ast.literal_eval(lab["LAB_ZONA_A"]), ast.literal_eval(b["LAB_ZONA_A"])
    assert {k for k in set(z_lab) | set(z_b) if z_lab.get(k) != z_b.get(k)} == {"valor", "piso"}
    esperado = (5.0, PISO_PROD) if perfil == CONTROL else (S_A, GRILLA[BRAZOS.index(perfil)])
    assert (z_b["valor"], z_b["piso"]) == esperado


# ------------------------------------------------------------------------------------------------ Q7 workflow
def test_q7_el_workflow_del_barrido_es_manual_no_publica_y_corre_los_nueve_perfiles():
    texto = FLUJO.read_text(encoding="utf-8")
    import yaml
    doc = yaml.safe_load(texto)
    assert list(doc["on"]) == ["workflow_dispatch"], doc["on"]          # A43: "on" entre comillas
    assert not re.search(r"git push[^\n]*\bmain\b", texto), "el barrido no pushea a main"
    assert not re.search(r"git add[^\n]*data/", texto), "el barrido no agrega records al árbol de datos"
    assert not re.search(r"\b(?:mirova_equivalent|laboratorio_v1)/", texto), "el barrido no toca carpetas publicadas"
    assert "scripts/reproc_brazos.py" in texto
    for p in (SINZONA, CONTROL, *BRAZOS):
        assert re.search(rf"\b{p}\b", texto), f"el workflow no nombra {p}"
    assert "EARTHDATA_TOKEN" in texto and "EARTHDATA_PASSWORD" not in texto, "A71: sólo el token"
    # los comparadores se buscan en líneas que se ejecutan, no en la cabecera de comentarios que los nombra
    codigo = "\n".join(l for l in texto.splitlines() if not l.lstrip().startswith("#"))
    assert re.search(r"python experiments/_s195_lab_paso3/comparar_control\.py[^\n]*\n[^\n]*--control "
                     r"salidas/_s196_lab_sinzona --brazo salidas/_s196_lab_control", codigo), (
        "COMPARAR: control contra el brazo sin zona")
    assert re.search(r"python experiments/_s196_lab_piso/comparar_donde_no_actua\.py[^\n]*\n[^\n]*--sin-zona "
                     r"salidas/_s196_lab_sinzona", codigo), "COMPARAR: donde la zona no actúa"
    assert doc["concurrency"]["group"] == "s196-lab-piso"


# ------------------------------------------------------------------------------------------------ Q8 comparador
def _store(d, nombre, recs):
    d.mkdir(parents=True, exist_ok=True)
    (d / nombre).write_text(json.dumps({"volcano": nombre[:-5], "records": recs}), encoding="utf-8")


def test_q8_el_comparador_donde_no_actua_ve_identidad_diferencia_y_vacio(tmp_path):
    m = _cargar(RAIZ / "experiments" / "_s196_lab_piso" / "comparar_donde_no_actua.py", "comparar_no_actua_s196")
    noche = {"granule": "g1", "sensor": "VIIRS_SNPP", "datetime_utc": "t1", "vrp_mw": 0.0, "via_codigo_mirova": True,
             "diag_codigo_mirova": {"dayflag": 0}}
    dia = {"granule": "g2", "sensor": "MODIS_AQUA", "datetime_utc": "t2", "vrp_mw": 0.0, "via_codigo_mirova": True,
           "diag_codigo_mirova": {"dayflag": 1}, "processed_utc": "a"}
    _store(tmp_path / "sz", "Villarrica.json", [noche, dia])
    # la noche cambia (es lo que la palanca hace) y processed_utc también (lo escribe el almacén): igual pasa
    _store(tmp_path / "b1", "Villarrica.json", [dict(noche, vrp_mw=0.4), dict(dia, processed_utc="b")])
    assert m.main(["--sin-zona", str(tmp_path / "sz"), "--brazo", str(tmp_path / "b1")]) == 0
    _store(tmp_path / "b2", "Villarrica.json", [noche, dict(dia, vrp_mw=0.4)])     # el día cambia: falla
    assert m.main(["--sin-zona", str(tmp_path / "sz"), "--brazo", str(tmp_path / "b2")]) == 1
    _store(tmp_path / "b3", "Villarrica.json", [noche])                             # falta el día: falla
    assert m.main(["--sin-zona", str(tmp_path / "sz"), "--brazo", str(tmp_path / "b3")]) == 1
    _store(tmp_path / "v1", "Villarrica.json", [noche])
    _store(tmp_path / "v2", "Villarrica.json", [dict(noche, vrp_mw=1.0)])
    assert m.main(["--sin-zona", str(tmp_path / "v1"), "--brazo", str(tmp_path / "v2")]) == 2   # nada donde no actúa
    assert m.main(["--sin-zona", str(tmp_path / "sz"), "--brazo", str(tmp_path / "no_existe")]) == 2
