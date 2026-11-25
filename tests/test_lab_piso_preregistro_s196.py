# -*- coding: utf-8 -*-
"""Pruebas del evaluador pre-registrado de la palanca del piso en la zona A del laboratorio (S196).

POR QUÉ. El evaluador se escribió antes de correr ningún brazo de piso. Para creerle hay que mostrar con datos
sintéticos que la regla de calibración puede dar cada uno de sus estados (A116), que el control de identidad atrapa
un brazo de producción que no es producción, y que la vara NHI es la del pre-registro S194 sin copia. Las pruebas
de sello (nombre con «sello») fijan los valores, el sha256 de este evaluador y el del evaluador S194 del que importa;
`experiments/_s196_lab_piso/mutar.py` corre este archivo contra copias mutadas SIN ellas.

`EVALUAR_PISO_PATH` apunta a la copia que se prueba; por defecto, el evaluador del repo.
"""
import ast
import json
import hashlib
import importlib.util
import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUTA_REPO = ROOT / "experiments" / "_s196_lab_piso" / "evaluar.py"
RUTA = Path(os.environ.get("EVALUAR_PISO_PATH", str(RUTA_REPO)))
RUTA_S194 = ROOT / "experiments" / "_s194_lab_zona_a" / "evaluar.py"


def _cargar(ruta, nombre):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M = _cargar(RUTA, "evaluar_lab_piso_s196")


def _sha(ruta):
    return hashlib.sha256(Path(ruta).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _tasas(por_brazo, n=1000):
    """{brazo: tasa} -> la forma de E.tasas_barrido, con la misma tasa en cada sensor y en la noche."""
    return {k: {c: (round(t * n), n) for c in M.E.SENSORES + ("NOCHE",)} for k, t in por_brazo.items()}


BASE = {M.CONTROL: .08, 0.003: .12, 0.00275: .17, 0.0025: .20, 0.00225: .26, 0.002: .35, 0.00175: .48, 0.0015: .62}


# ----------------------------------------------------------------------------------------------- sello
def test_sello_valores():
    assert (M.S_CONTROL, M.PISO_PROD, M.S_A) == (5.0, 0.003, 3.0)
    assert M.GRILLA_PISO == (0.003, 0.00275, 0.0025, 0.00225, 0.002, 0.00175, 0.0015)
    assert (M.TASA_OBJETIVO, M.UNIDAD_TASA, M.N_MIN_NEG) == (0.30, "noche", 30)
    assert M.CAMINO == (M.CONTROL,) + M.GRILLA_PISO


def test_sello_hash_del_evaluador_en_el_preregistro():
    txt = (RUTA_REPO.parent / "PREREGISTRO.md").read_text(encoding="utf-8")
    m = re.search(r"sha256 del evaluador \(fin de línea LF\): `([0-9a-f]{64})`", txt)
    assert m, "el PREREGISTRO.md no declara el sha256 del evaluador"
    assert _sha(RUTA_REPO) == m.group(1), "evaluar.py cambió después del sello"


def test_sello_hash_del_evaluador_s194_del_que_importa_la_vara():
    """La vara se importa del evaluador S194: si ése se re-sella, este pre-registro tiene que re-sellarse también."""
    mio = (RUTA_REPO.parent / "PREREGISTRO.md").read_text(encoding="utf-8")
    suyo = (RUTA_S194.parent / "PREREGISTRO.md").read_text(encoding="utf-8")
    m1 = re.search(r"sha256 del evaluador S194 que importa \(fin de línea LF\): `([0-9a-f]{64})`", mio)
    m2 = re.search(r"sha256 del evaluador \(fin de línea LF\): `([0-9a-f]{64})`", suyo)
    assert m1 and m2
    assert _sha(RUTA_S194) == m1.group(1) == m2.group(1)


def test_sello_piso_y_s_leidos_del_detector():
    """El piso de hoy y el s de producción salen de detectar_mirova, no de una copia: n2 == e2 == primer piso."""
    src = (ROOT / "pipeline" / "mirova_v750_codigo.py").read_text(encoding="utf-8")
    m = re.search(r"if dayflag == 0:[^\n]*\n\s*u_abs, s1, s2, n1, n2, e1, e2 = ([^\n#]+)", src)
    assert m, "no encontré los umbrales nocturnos de detectar_mirova"
    _, _, s2, _, n2, _, e2 = ast.literal_eval("(" + m.group(1).strip() + ")")
    assert n2 == e2 == M.PISO_PROD == M.GRILLA_PISO[0] and s2 == M.S_CONTROL
    assert 0 < M.S_A <= M.S_CONTROL                               # guard S147: nunca más ciego que producción
    assert all(0 < b < a for a, b in zip(M.GRILLA_PISO, M.GRILLA_PISO[1:]))


# ----------------------------------------------------------------------------------------------- la vara
def test_la_vara_es_la_del_s194_sin_copia():
    assert M.veredicto is M.E.veredicto
    assert _sha(M.E.__file__) == _sha(RUTA_S194)                  # el sellado, byte a byte (LF)
    assert M.TASA_OBJETIVO == M.E.TASA_OBJETIVO and M.UNIDAD_TASA == M.E.UNIDAD_TASA


# ----------------------------------------------------------------------------------------------- regla
def test_elige_el_menor_piso_que_cumple_con_30_exacto():
    r = M.elegir_piso(_tasas({**BASE, 0.002: .30}))
    assert r["estado"] == "ELEGIDO" and r["valor"] == {"s_a": M.S_A, "piso_a": 0.002}
    assert r["detalle"] == "menor piso de la grilla que cumple"
    assert M.elegir_piso(_tasas(BASE))["valor"]["piso_a"] == 0.00225
    assert M.elegir_piso(_tasas({**BASE, 0.002: .301}))["valor"]["piso_a"] == 0.00225


def test_sin_valor_si_produccion_ya_supera():
    t = _tasas({k: .31 + .01 * i for i, k in enumerate(M.CAMINO)})
    assert M.elegir_piso(t)["estado"] == "SIN VALOR"


def test_sin_valor_de_piso_si_el_tramo_de_s_ya_supera():
    t = _tasas({k: (.10 if k == M.CONTROL else .31 + .01 * i) for i, k in enumerate(M.CAMINO)})
    r = M.elegir_piso(t)
    assert r["estado"] == "SIN VALOR DE PISO" and r["valor"] is None


def test_piso_de_la_grilla_y_piso_de_hoy_van_rotulados():
    plano = M.elegir_piso(_tasas({k: .05 for k in M.CAMINO}))
    # A92: «piso de la grilla» está también en «menor piso de la grilla que cumple»; se busca la frase del rótulo.
    assert plano["valor"]["piso_a"] == M.GRILLA_PISO[-1] and "no alcanzó la tasa objetivo" in plano["detalle"]
    medio = M.elegir_piso(_tasas(BASE))
    assert "no alcanzó" not in medio["detalle"] and "piso de hoy" not in medio["detalle"]
    hoy = M.elegir_piso(_tasas({k: (.05 if k in (M.CONTROL, 0.003) else .5) for k in M.CAMINO}))
    assert hoy["estado"] == "ELEGIDO" and hoy["valor"]["piso_a"] == 0.003 and "piso de hoy" in hoy["detalle"]


def test_no_monotona_es_invalido_incluido_el_control():
    assert M.elegir_piso(_tasas({**BASE, 0.0025: .16}))["estado"] == M.INVALIDO
    assert M.elegir_piso(_tasas({**BASE, M.CONTROL: .13}))["estado"] == M.INVALIDO   # control sobre (S_A, 0,003)


def test_falta_un_brazo_o_el_control_es_invalido():
    for k in (M.CONTROL, 0.002):
        t = _tasas(BASE)
        del t[k]
        assert M.elegir_piso(t)["estado"] == M.INVALIDO


def test_sin_poder_con_29_negativos_en_un_brazo():
    t = _tasas(BASE)
    t[0.00175]["NOCHE"] = (10, 29)
    assert M.elegir_piso(t)["estado"] == M.SIN_PODER
    t = _tasas(BASE)
    t[0.00175]["NOCHE"] = (10, 30)
    assert M.elegir_piso(t)["estado"] != M.SIN_PODER


def test_rige_la_noche_y_la_pasada_queda_disponible():
    t = _tasas(BASE)
    for k in M.CAMINO:
        for sen in M.E.SENSORES:
            t[k][sen] = (10, 1000)                 # por pasada nunca supera
    assert M.elegir_piso(t)["valor"]["piso_a"] == 0.00225
    assert M.elegir_piso(t, unidad="pasada")["valor"]["piso_a"] == 0.0015


def test_con_s_a_igual_a_produccion_el_primer_piso_es_el_control(monkeypatch):
    monkeypatch.setattr(M, "S_A", M.S_CONTROL)
    t = _tasas({**BASE, 0.003: .08, 0.00275: .5, 0.0025: .5, 0.00225: .5, 0.002: .5, 0.00175: .5, 0.0015: .5})
    assert M.elegir_piso(t)["estado"] == "SIN EXTENSION"
    prod = dict(t[M.CONTROL])
    assert M.control_tasas(t, prod)
    t[0.003] = dict(t[0.003], NOCHE=(81, 1000))
    assert not M.control_tasas(t, prod)


# ----------------------------------------------------------------------------------------------- controles
def test_control_de_tasas_exige_las_cuentas_de_produccion():
    t = _tasas(BASE)
    prod = dict(t[M.CONTROL])
    assert M.control_tasas(t, prod)
    assert not M.control_tasas(t, dict(prod, VIIRS375=(prod["VIIRS375"][0] + 1, prod["VIIRS375"][1])))
    t[0.003] = dict(t[M.CONTROL])                 # con S_A = 1 el primer piso no tiene que ser producción
    assert M.control_tasas(t, prod)


def _rec(vol="Lascar", sensor="MODIS_AQUA", t="2026-03-02 05:00", vrp=0.0, n_p1=0, dc="summit"):
    return {"_vol": vol, "sensor": sensor, "datetime_utc": t, "vrp_mw": vrp, "distance_class": dc,
            "final_hotspot_lat": -23.37, "final_hotspot_lon": -67.73, "final_hotspot_dist_km": 0.4,
            "primary_cluster": {"vrp_mw": vrp, "centroid_dist_km": 0.4, "n_pixels": 1},
            "diag_codigo_mirova": {"n_abs": 0, "n_p1": n_p1, "n_p2": 0, "motivo_vacio": None}}


def test_identidad_record_a_record():
    a = [_rec(), _rec(t="2026-03-03 05:00", vrp=1.2, n_p1=2)]
    assert M.identidad_records(a, [dict(x) for x in a])["identico"]
    otro = [_rec(), _rec(t="2026-03-03 05:00", vrp=1.3, n_p1=2)]
    assert not M.identidad_records(a, otro)["identico"]
    assert not M.identidad_records(a, a[:1])["identico"]                     # falta una pasada
    assert not M.identidad_records(a, [_rec(), _rec(t="2026-03-03 05:00", vrp=1.2, n_p1=3)])["identico"]
    assert not M.identidad_records(a, [_rec(dc="far"), a[1]])["identico"]
    solo_vrp = dict(a[1], vrp_mw=9.9)                                       # sólo el vrp_mw del record
    assert not M.identidad_records(a, [a[0], solo_vrp])["identico"]
    assert not M.identidad_records([], [])["identico"]                       # vacío no es identidad
    r = M.identidad_records(a, otro)
    assert r["n_diferencias"] == 1 and r["diferencias"] == [["Lascar", "MODIS_AQUA", "2026-03-03 05:00"]]


@pytest.mark.parametrize("arg", ["evaluar", "poder"])
def test_evaluar_y_poder_delegan_en_el_s194(monkeypatch, arg):
    visto = {}
    monkeypatch.setattr(M.E, "main", lambda argv: visto.setdefault("argv", argv) and 7)
    assert M.main([arg, "--x"]) == 7 and visto["argv"] == [arg, "--x"]


# ----------------------------------------------------------------------------------------------- calibrar entero
def _escribir(carpeta, recs_por_vol):
    carpeta.mkdir(parents=True, exist_ok=True)
    for vol in M.E.VOLCANES_ZONA_A:
        recs = [{k: v for k, v in r.items() if k != "_vol"} for r in recs_por_vol.get(vol, [])]
        (carpeta / ("%s.json" % vol)).write_text(json.dumps({"records": recs}), encoding="utf-8")
    return str(carpeta)


def _base_recs():
    noche = dict(_rec(), via_codigo_mirova=True)
    noche["diag_codigo_mirova"] = dict(noche["diag_codigo_mirova"], dayflag=0, s1={"pasada1": {"u_nti2": 0.003}})
    dia = dict(_rec(t="2026-03-02 15:00"), via_codigo_mirova=True)
    dia["diag_codigo_mirova"] = dict(dia["diag_codigo_mirova"], dayflag=1)
    # Re-sello S200 (R4FD-102): la identidad donde la zona no actúa necesita N_MIN_FUERA records comparados; con menos
    # el evaluador dice SIN PODER. Se agregan 30 pasadas de día más (la de índice 1 sigue siendo la que se altera).
    mas = []
    for d in range(30):
        x = dict(_rec(t="2026-04-%02d 15:00" % (d + 1)), via_codigo_mirova=True)
        x["diag_codigo_mirova"] = dict(x["diag_codigo_mirova"], dayflag=1)
        mas.append(x)
    return {"Lascar": [noche, dia] + mas}


def _armar(tmp_path, monkeypatch, cambiar=None, prod_igual=True):
    """Barrido sintético: todos los brazos con los records de base; `cambiar(nombre, recs)` altera uno."""
    t = _tasas(BASE)
    # Re-sello S200 (R4FD-106): una sola llamada con todos los brazos y producción (antes eran dos).
    prod_t = dict(t[M.CONTROL]) if prod_igual else dict(t[M.CONTROL], NOCHE=(1, 1000))
    monkeypatch.setattr(M.E, "tasas_barrido", lambda brazos, fin, dest: (
        {k: (prod_t if k == "prod" else t[k]) for k in brazos}))
    dirs = {}
    for nombre in ["sin_zona", M.CONTROL] + [str(p) for p in M.GRILLA_PISO]:
        recs = _base_recs()
        if cambiar:
            cambiar(nombre, recs)
        dirs[nombre] = _escribir(tmp_path / nombre.replace(".", "_"), recs)
    return M.calibrar(dirs["sin_zona"], dirs[M.CONTROL], {p: dirs[str(p)] for p in M.GRILLA_PISO}, "prod", "2026-11-23",
                      str(tmp_path / "ref"))


def test_calibrar_sano_elige(tmp_path, monkeypatch):
    r = _armar(tmp_path, monkeypatch)
    assert r["estado"] == "ELEGIDO" and r["valor"]["piso_a"] == 0.00225


def test_calibrar_control_distinto_del_brazo_sin_zona_es_invalido(tmp_path, monkeypatch):
    def cambiar(nombre, recs):
        if nombre == M.CONTROL:
            recs["Lascar"][0]["diag_codigo_mirova"]["s1"] = {"pasada1": {"u_nti2": 0.0029}}   # sólo el umbral
    r = _armar(tmp_path, monkeypatch, cambiar)
    assert r["estado"] == M.INVALIDO and "record a record" in r["detalle"]


def test_calibrar_brazo_de_piso_que_cambia_el_dia_es_invalido(tmp_path, monkeypatch):
    def cambiar(nombre, recs):
        if nombre == "0.002":
            recs["Lascar"][1]["vrp_mw"] = 0.5                     # de día la zona no actúa
    r = _armar(tmp_path, monkeypatch, cambiar)
    assert r["estado"] == M.INVALIDO and "no actúa" in r["detalle"]


def test_calibrar_brazo_de_piso_que_cambia_la_noche_es_lo_esperado(tmp_path, monkeypatch):
    def cambiar(nombre, recs):
        if nombre == "0.002":
            recs["Lascar"][0]["vrp_mw"] = 0.5                     # de noche en la zona: es lo que la palanca hace
    assert _armar(tmp_path, monkeypatch, cambiar)["estado"] == "ELEGIDO"


def test_calibrar_cuentas_distintas_de_produccion_es_invalido(tmp_path, monkeypatch):
    r = _armar(tmp_path, monkeypatch, prod_igual=False)
    assert r["estado"] == M.INVALIDO and "cuentas de producción" in r["detalle"]
