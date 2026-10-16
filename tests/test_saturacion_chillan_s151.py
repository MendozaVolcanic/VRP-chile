# -*- coding: utf-8 -*-
"""Tarea 1.18 del loop: tests del probe que cuenta pixeles saturados en el L1B de Nevados de Chillan.

POR QUE. Un pixel saturado lo borra el pipeline antes de detectar y no deja rastro en `t_max_k`; solo el
L1B lo puede contar. Antes de gastar una corrida en GitHub Actions estos tests fijan que:

  1. el conteo encuentra EXACTAMENTE los pixeles saturados sembrados en un granulo sintetico, separados por
     motivo (bit de calidad contra techo del pipeline), y no cuenta los centinelas de DN (bowtie, relleno);
  2. "borrado" sale de comparar el L1B crudo con la lectura de PRODUCCION (`read_viirs_l1b` llamado,
     no copiado), asi que si produccion deja de borrar, el conteo baja solo;
  3. el brazo "con" solo cambia los pixeles borrados, y los deja en el piso declarado;
  4. de punta a punta, con el `calculate_vrp` real sobre un granulo sintetico, el brazo "con" tiene mas
     magnitud que el "sin" cuando hay saturados, y lo mismo que el "sin" cuando no los hay (control);
  5. el probe llama a `calculate_vrp` con los MISMOS argumentos que `scripts/run_pipeline.py` (AST, A92);
  6. MODIS: SI = 65533 se cuenta como saturado y los demas SI > 32767 aparte;
  7. el workflow autentica solo por token (A71) y lleva "on" entre comillas (A43).
"""
import ast
import json
import math
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "_s151_saturacion_chillan"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(EXP))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

h5py = pytest.importorskip("h5py")

import saturacion as S  # noqa: E402
import probe_saturacion as P  # noqa: E402
import evaluar_saturacion as E  # noqa: E402
from pipeline import process_viirs as pv  # noqa: E402

# LUT sintetica: lineal en DN, clampeada al techo (como hace el L1B, Tabla C.1)
TECHO_I04, TECHO_I05 = 361.77, 423.33


def _lut(t0, paso, techo):
    lut = (t0 + np.arange(65536, dtype=np.float64) * paso).astype(np.float32)
    lut = np.minimum(lut, np.float32(techo))
    lut[65532:] = -999.9
    return lut


LUT_I04 = _lut(180.0, 0.003, TECHO_I04)
LUT_I05 = _lut(150.0, 0.005, TECHO_I05)


def _dn(lut, t):
    """El DN mas chico cuya BT es >= t (para el techo devuelve el primer DN clampeado)."""
    return int(np.argmax(lut >= np.float32(t) - 1e-3))


def _volcan():
    import run_pipeline as rp
    return rp.load_volcanoes("NevadosDeChillan")[0]


def _granulo(tmp, n=200, sembrar=True, nombre="VNP02IMG.A2026280.0600.002.2026280120000.nc", semilla=7):
    """L1B + geo VIIRS 375 sinteticos alrededor del ancla de Chillan.

    Siembra (si `sembrar`): 3 pixeles I04 saturados con bit de calidad en el ancla, 1 pixel I04 en el
    techo SIN bit (lo borra la defensa secundaria del pipeline), 1 pixel I05 saturado con bit, y un
    centinela 65533 (bowtie) que NO es saturacion. Debajo, un foco en campana (348 K en el centro).
    Devuelve (l1b, geo, dict de las posiciones sembradas).
    """
    from pipeline.geo_utils import get_detection_anchor
    vlat, vlon = get_detection_anchor(_volcan())
    rng = np.random.default_rng(semilla)
    i0 = j0 = n // 2
    dy = 0.375 / 111.32
    dx = 0.375 / (111.32 * math.cos(math.radians(vlat)))
    ii, jj = np.mgrid[0:n, 0:n]
    lat = (vlat - (ii - i0) * dy).astype(np.float32)
    lon = (vlon + (jj - j0) * dx).astype(np.float32)
    # foco con forma de campana (centro mas caliente, cae hacia afuera), no una meseta: una meseta
    # uniforme no tiene contraste contextual en su interior y el detector la ve mal (no es lo que se mide aca)
    r2 = (ii - i0) ** 2 + (jj - j0) ** 2
    t4 = 268.0 + 80.0 * np.exp(-r2 / 2.0) + rng.normal(0, 0.6, (n, n))
    t5 = 262.0 + 25.0 * np.exp(-r2 / 2.0) + rng.normal(0, 0.6, (n, n))
    dn4 = np.array([[_dn(LUT_I04, t) for t in fila] for fila in t4], dtype=np.uint16)
    dn5 = np.array([[_dn(LUT_I05, t) for t in fila] for fila in t5], dtype=np.uint16)
    qf4 = np.zeros((n, n), np.uint8)
    qf5 = np.zeros((n, n), np.uint8)
    sem = {"i04_bit": [], "i04_techo": [], "i05_bit": [], "centinela": []}
    if sembrar:
        for (a, b) in ((i0, j0), (i0, j0 + 1), (i0 + 1, j0)):
            dn4[a, b] = _dn(LUT_I04, TECHO_I04)
            qf4[a, b] = S.SAT_BIT | 0b1          # otro bit encendido no debe confundir el conteo
            sem["i04_bit"].append((a, b))
        dn4[i0 - 1, j0 - 1] = _dn(LUT_I04, TECHO_I04) + 50   # en el techo, sin bit
        sem["i04_techo"].append((i0 - 1, j0 - 1))
        dn5[i0, j0] = _dn(LUT_I05, TECHO_I05)
        qf5[i0, j0] = S.SAT_BIT
        sem["i05_bit"].append((i0, j0))
        dn4[i0 + 30, j0 + 30] = 65533                       # bowtie: centinela, no saturacion
        qf4[i0 + 30, j0 + 30] = S.SAT_BIT                   # aunque traiga el bit, no es un pixel medido
        sem["centinela"].append((i0 + 30, j0 + 30))
    l1b = Path(tmp) / nombre
    geo = Path(tmp) / nombre.replace("02IMG", "03IMG")
    with h5py.File(l1b, "w") as f:
        o = f.create_group("observation_data")
        o["I04"], o["I04_quality_flags"], o["I04_brightness_temperature_lut"] = dn4, qf4, LUT_I04
        o["I05"], o["I05_quality_flags"], o["I05_brightness_temperature_lut"] = dn5, qf5, LUT_I05
    with h5py.File(geo, "w") as f:
        g = f.create_group("geolocation_data")
        g["latitude"], g["longitude"] = lat, lon
        g["sensor_zenith"] = np.full((n, n), 10.0, np.float32)
    return l1b, geo, sem


# ------------------------------------------------------------------ 1-3: conteo y brazo "con"
def test_conteo_encuentra_exactamente_los_saturados_sembrados(tmp_path):
    l1b, geo, sem = _granulo(tmp_path)
    p = P.preparar("V375", l1b, geo)
    m4, m5 = p["mascaras"]["I04"], p["mascaras"]["I05"]
    assert sorted(zip(*np.where(m4["bit"]))) == sorted(sem["i04_bit"])
    assert sorted(zip(*np.where(m4["techo"]))) == sorted(sem["i04_techo"])
    assert sorted(zip(*np.where(m5["bit"]))) == sorted(sem["i05_bit"])
    assert int(m5["techo"].sum()) == 0
    a, b = sem["centinela"][0]
    assert not m4["borrado"][a, b], "un centinela de DN no es un pixel saturado"
    assert p["mascaras"]["MIR"] is p["mascaras"]["I04"]


def test_sin_saturados_el_conteo_da_cero(tmp_path):
    l1b, geo, _ = _granulo(tmp_path, sembrar=False)
    p = P.preparar("V375", l1b, geo)
    assert all(int(m["borrado"].sum()) == 0 for m in p["mascaras"].values())


def test_borrado_sale_de_la_lectura_de_produccion(tmp_path):
    """Si produccion dejara de borrar, el conteo bajaria a cero: no hay una regla paralela escondida."""
    l1b, geo, _ = _granulo(tmp_path)
    crudo = S.leer_viirs_crudo(l1b, ("I04",), pv.FLAG_DNS)
    no_borra = {"I04": crudo["I04"]["bt"].copy()}
    m = S.mascaras_borrado(crudo["I04"]["bt"], no_borra["I04"], crudo["I04"]["qf"])
    assert int(m["borrado"].sum()) == 0
    prod = pv.read_viirs_l1b(l1b)
    m = S.mascaras_borrado(crudo["I04"]["bt"], prod["I04"], crudo["I04"]["qf"])
    assert int(m["borrado"].sum()) == 4


def test_brazo_con_solo_cambia_los_borrados_y_los_deja_en_el_piso(tmp_path):
    l1b, geo, sem = _granulo(tmp_path)
    p = P.preparar("V375", l1b, geo)
    prod, con = p["prod"], p["con"]
    for b in ("I04", "I05"):
        distinto = ~((prod[b] == con[b]) | (np.isnan(prod[b]) & np.isnan(con[b])))
        assert np.array_equal(distinto, p["mascaras"][b]["borrado"])
    assert p["pisos"]["I04"] == pytest.approx(TECHO_I04, abs=1e-3)
    assert p["origen_pisos"]["I04"] == "lut_del_granulo"
    for a, b in sem["i04_bit"]:
        assert con["I04"][a, b] == pytest.approx(TECHO_I04, abs=1e-3)
    a, b = sem["i04_techo"][0]
    assert con["I04"][a, b] == pytest.approx(TECHO_I04, abs=1e-3)   # la BT que el sensor reporto


def test_techo_declarado_cuando_no_hay_lut():
    t, origen = S.techo_banda("V375", "I04", {"techo_lut": float("nan")})
    assert (t, origen) == (361.77, "declarado_process_viirs_373")
    from pipeline.process_viirs_mod import BT_LUT_MAX_MBAND
    assert S.techo_banda("V750", "M13", None)[0] == BT_LUT_MAX_MBAND["M13"]


def test_techos_i_coinciden_con_el_pipeline():
    """Los techos I04/I05 son variables locales de read_viirs_l1b; si el fuente cambia, este test cae."""
    src = (ROOT / "pipeline" / "process_viirs.py").read_text(encoding="utf-8")
    m = re.search(r'BT_LUT_MAX\s*=\s*\{"I04":\s*([\d.]+),\s*"I05":\s*([\d.]+)\}', src)
    assert m, "no encontre BT_LUT_MAX en process_viirs.py"
    assert (float(m.group(1)), float(m.group(2))) == (S.TECHO_I_DECLARADO["I04"], S.TECHO_I_DECLARADO["I05"])


def test_conteo_por_region(tmp_path):
    l1b, geo, _ = _granulo(tmp_path)
    p = P.preparar("V375", l1b, geo)
    interior = np.zeros(p["mascaras"]["I04"]["bit"].shape, bool)
    interior[90:110, 90:110] = True
    c = S.contar(p["mascaras"], {"interior": interior, "todo": np.ones_like(interior)})
    assert c["I04"]["interior"]["bit"] == 3 and c["I04"]["interior"]["techo"] == 1
    assert c["I05"]["todo"]["bit"] == 1


# ------------------------------------------------------------------ 4: de punta a punta
def test_punta_a_punta_el_brazo_con_recupera_magnitud(tmp_path):
    l1b, geo, _ = _granulo(tmp_path)
    med, rs, rc = P.medir_granulo("V375", l1b, geo, _volcan())
    assert med["conteo"]["MIR"]["interior"]["bit"] == 3
    assert med["conteo"]["MIR"]["interior"]["techo"] == 1
    assert med["cota_aditiva"]["n_mir_borrados_interior"] == 4
    assert rs is not None and rc is not None
    assert (rc["vrp_mir_mw"] or 0) > (rs["vrp_mir_mw"] or 0)
    assert med["cota_aditiva"]["mw_piso_declarado"] > 0


def test_punta_a_punta_control_sin_saturados_los_brazos_coinciden(tmp_path):
    l1b, geo, _ = _granulo(tmp_path, sembrar=False)
    med, rs, rc = P.medir_granulo("V375", l1b, geo, _volcan())
    assert med["conteo"]["MIR"]["interior"] == {"borrado": 0, "bit": 0, "techo": 0}
    assert med["sin"] == med["con"]
    assert med["cota_aditiva"]["mw_piso_declarado"] == 0.0


@pytest.mark.skipif(shutil.which("node") is None, reason="sin node")
def test_tablero_evalua_los_dos_brazos(tmp_path):
    l1b, geo, _ = _granulo(tmp_path)
    _, rs, rc = P.medir_granulo("V375", l1b, geo, _volcan())
    out = P.tablero([rs, None, rc], 5.0)
    assert out[1] == [None, 0]
    assert all(isinstance(x[1], int) for x in out)


# ------------------------------------------------------------------ cota aditiva
def test_cota_aditiva_a_mano():
    from pipeline.process_modis import bt_to_radiance
    dl = float(bt_to_radiance(361.77, 3.74)) - float(bt_to_radiance(270.0, 3.74))
    esperado = round(2 * 140625.0 * 18.0 * dl / 1e6, 4)
    assert S.cota_aditiva_mw(2, 361.77, 270.0, 3.74, 18.0, 140625.0) == esperado
    assert S.cota_aditiva_mw(0, 361.77, None, 3.74, 18.0, 140625.0) == 0.0
    assert S.cota_aditiva_mw(1, 361.77, None, 3.74, 18.0, 140625.0) is None
    assert S.cota_aditiva_mw(1, 250.0, 270.0, 3.74, 18.0, 140625.0) == 0.0   # sin exceso no hay energia


# ------------------------------------------------------------------ 6: MODIS
def test_modis_65533_es_saturado_y_los_otros_invalidos_aparte():
    si = np.array([[100, 65533, 65535], [32767, 32768, 65533]], dtype=np.uint16)
    m = S.mascaras_modis(si)
    assert int(m["bit"].sum()) == 2
    assert int(m["otros_invalidos"].sum()) == 2
    assert int(m["borrado"].sum()) == 4
    assert not m["borrado"][1, 0], "32767 es el ultimo SI valido"


def test_modis_preparar_cuenta_y_restituye_al_piso():
    from pipeline import process_modis as pm
    n = 40
    rad = lambda t, lam: np.full((n, n), pm.bt_to_radiance(t, lam), np.float32)  # noqa: E731
    datos = {"band21": rad(280.0, pm.BAND21_LAMBDA), "band22": rad(280.0, pm.BAND22_LAMBDA),
             "band31": rad(275.0, pm.BAND31_LAMBDA),
             "lat": np.zeros((n, n), np.float32), "lon": np.zeros((n, n), np.float32), "angles": {}}
    si = {b: np.full((n, n), 1000, np.uint16) for b in ("B21", "B22", "B31")}
    for b in ("B21", "B22"):
        si[b][20, 20] = 65533
    si["B22"][5, 5] = 65533          # solo B22: la MIR combinada no se pierde (B21 la cubre)
    datos["band21"][20, 20] = np.nan
    datos["band22"][20, 20] = np.nan
    datos["band22"][5, 5] = np.nan
    with patch.object(pm, "read_modis_l1b", lambda _p: {k: (v.copy() if isinstance(v, np.ndarray) else v)
                                                         for k, v in datos.items()}):
        p = P.preparar("MODIS", "x.hdf", "y.hdf", lector_si=lambda _p: si)
    assert int(p["mascaras"]["B21"]["bit"].sum()) == 1
    assert int(p["mascaras"]["B22"]["bit"].sum()) == 2
    assert int(p["mascaras"]["MIR"]["bit"].sum()) == 1
    bt = pm.radiance_to_bt(p["con"]["band21"][20, 20], pm.BAND21_LAMBDA)
    assert bt == pytest.approx(499.9, abs=0.05)
    assert np.isnan(p["prod"]["band21"][20, 20])
    assert p["con"]["band21"][0, 0] == p["prod"]["band21"][0, 0]


# ------------------------------------------------------------------ 5: argumentos de produccion
def _llamadas_run_pipeline():
    arbol = ast.parse((ROOT / "scripts" / "run_pipeline.py").read_text(encoding="utf-8"))
    return [n for n in ast.walk(arbol) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "calculate_vrp" and isinstance(n.func.value, ast.Name)]


@pytest.mark.parametrize("familia,modulo", [("V375", "process_viirs"), ("V750", "process_viirs_mod"),
                                            ("MODIS", "process_modis")])
def test_calculate_vrp_con_los_mismos_argumentos_que_run_pipeline(familia, modulo):
    c = [x for x in _llamadas_run_pipeline() if x.func.value.id == modulo]
    assert len(c) == 1
    assert set(P.argumentos_calculate_vrp(familia, _volcan())) == {k.arg for k in c[0].keywords}
    assert P.MODULO[familia][0] == "pipeline." + modulo


def test_append_record_con_los_mismos_argumentos_que_run_pipeline():
    arbol = ast.parse((ROOT / "scripts" / "run_pipeline.py").read_text(encoding="utf-8"))
    c = [n for n in ast.walk(arbol) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
         and n.func.attr == "append_record"]
    assert c
    for x in c:
        assert set(P.argumentos_append_record(_volcan(), True)) == {k.arg for k in x.keywords}


# ------------------------------------------------------------------ granulos y tramos
def test_tramos_cubren_todos_los_dias_sin_solaparse():
    todos = []
    for i in range(6):
        todos += S.dias_del_tramo("2026-09-28", "2026-10-16", i, 6)
    assert todos == S.dias_del_tramo("2026-09-28", "2026-10-16", 0, 1)
    assert len(todos) == 19


def test_hora_y_tipo_de_granulo():
    assert S.hora_granulo("MOD021KM.A2026271.0125.061.2026271051005.NRT.hdf") == datetime(2026, 9, 28, 1, 25)
    assert P.es_l1b("VJ102IMG.A2026280.0600.021.nc") and not P.es_l1b("VJ103IMG.A2026280.0600.021.nc")
    assert P.es_l1b("MYD021KM.A2026280.0600.061.hdf") and not P.es_l1b("MYD03.A2026280.0600.061.hdf")


# ------------------------------------------------------------------ evaluador
def _pasada(dt, fam="V375", bit=2, sin=1.0, con=3.0):
    return {"familia": fam, "plataforma": "VIIRS_SNPP", "l1b": "L.%s" % dt, "datetime_utc": dt, "noche": True,
            "estado": "ok", "conteo": {"MIR": {"interior": {"borrado": bit, "bit": bit, "techo": 0},
                                               "escena": {"borrado": bit, "bit": bit, "techo": 0}},
                                       "I05": {"interior": {"borrado": 0, "bit": 0, "techo": 0}}},
            "sin": {"pc_vrp": sin}, "con": {"pc_vrp": con}, "tablero_sin": [sin, 1], "tablero_con": [con, 1],
            "cota_aditiva": {"mw_piso_declarado": 2.5, "mw_piso_empirico": 1.0}}


def test_evaluador_parea_con_mirova_y_resume(tmp_path):
    ref = [{"volcano": "NevadosDeChillan", "sensor_bucket": "VIIRS375", "fecha_utc": "2026-10-10 06:01:00",
            "source": "CONS", "tipo": "ALERTA_TERMICA", "vrp_mw": 9.0, "dist_km": 1.1},
           {"volcano": "NevadosDeChillan", "sensor_bucket": "VIIRS375", "fecha_utc": "2026-10-11 05:00:00",
            "source": "CONS", "tipo": "ALERTA_TERMICA", "vrp_mw": 8.24, "dist_km": 1.0},
           {"volcano": "Llaima", "sensor_bucket": "VIIRS375", "fecha_utc": "2026-10-10 06:00:00",
            "source": "CONS", "tipo": "ALERTA_TERMICA", "vrp_mw": 1.0, "dist_km": 1.0}]
    import banco_paridad as bp
    por_b = E.indexar(ref, "2026-10-01", "2026-10-16")
    p = _pasada("2026-10-10 06:00")
    fila = E.fila_tabla(p, bp.parear(por_b["VIIRS375"], datetime(2026, 10, 10, 6, 0)))
    assert [m["vrp_mw"] for m in fila["mirova"]] == [9.0]
    r = E.resumir([fila])
    assert r["V375_noche"]["pasadas_con_mir_borrado_interior"] == 1
    assert r["V375_noche"]["pixeles_mir_borrados_interior_bit"] == 2
    assert r["V375_noche"]["suma_mirova_vrp_alertas_mw"] == 9.0
    falta, _ = E.mirova_sin_pasada(por_b, [fila])
    assert [x["vrp_mw"] for x in falta] == [8.24], "la alerta sin pasada medida queda a la vista (A108)"


def test_evaluador_main_avisa_calidad_y_escribe(tmp_path, capsys):
    d = tmp_path / "salidas" / "a"
    d.mkdir(parents=True)
    (d / "sat_V375_t0.json").write_text(json.dumps({"pasadas": [_pasada("2026-10-10 06:00"),
                                                                 _pasada("2026-10-10 06:00")]}))
    with patch("calidad_referencia_mirova.avisar", wraps=__import__("calidad_referencia_mirova").avisar) as av:
        E.main([str(tmp_path / "salidas"), "--salida", str(tmp_path / "r.json"),
                "--tabla", str(tmp_path / "t.md"), "--snapshot"])
    assert av.call_count == 1
    out = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert len(out["pasadas"]) == 1, "un L1B repetido entre tramos se cuenta una vez"
    assert out["procedencia_referencia"]["fuente"] == "snapshot"
    assert "|" in (tmp_path / "t.md").read_text(encoding="utf-8")


# ------------------------------------------------------------------ 7: workflow
def test_workflow_token_unico_on_entre_comillas_y_timeout():
    import yaml
    p = ROOT / ".github" / "workflows" / "probe-s151-saturacion-chillan.yml"
    txt = p.read_text(encoding="utf-8")
    y = yaml.safe_load(txt)
    assert "on" in y and True not in y, "on sin comillas se parsea como booleano (A43)"
    assert "EARTHDATA_TOKEN" in txt
    assert "EARTHDATA_USERNAME" not in txt and "EARTHDATA_PASSWORD" not in txt
    assert re.search(r'if \[ -z "\$EARTHDATA_TOKEN" \]', txt), "debe fallar si el token viene vacio"
    for job in y["jobs"].values():
        assert job.get("timeout-minutes"), "cada job con timeout (A15)"
        assert job.get("permissions", {}).get("contents") == "read", "solo lectura: no escribe en el repo"
    assert "git push" not in txt
