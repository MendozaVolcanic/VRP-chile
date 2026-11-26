# -*- coding: utf-8 -*-
"""Re-sello R5C-101 del evaluador del piso de la zona A del laboratorio (S202, decisión de Nicolás del 2026-11-26).

POR QUÉ. Al bajar el piso, un foco débil pegado a un hueco de datos puede quedar alertado sin vecinos para estimar su
fondo; la vía guarda entonces la escena MODIS como «no medida» (`diag_codigo_mirova.motivo_vacio`) sólo en los pisos
bajos, y el evaluador la sacaba del denominador sólo en esos brazos: los brazos se comparaban sobre muestras
distintas sin que ningún control lo viera (ronda 5 de la auditoría externa con Codex, cierre, R5C-101; verificador
Claude de contexto limpio, D:/codex-vrp/_salida/ronda5/cierre_verificacion/VEREDICTO.md). El camino inverso existe en
VIIRS 375 (R5C-V201): una escena que el control no midió («crater_no_evaluado») se vuelve válida y publica con el piso
bajo. Nicolás eligió el arreglo (a) («Sí, re-séllalo así», 2026-11-26): toda escena inválida en ALGUNO de los nueve
brazos se excluye de los nueve brazos Y de producción, declarada y contada en la salida, con dos frenos sellados que
dan INVÁLIDO: (1) alguna excluida decide su noche (era la única negativa limpia o la única pasada con alerta o falso
positivo de MIROVA de esa noche, en algún brazo o en producción); (2) las excluidas pasan del 1 % de las noches
negativas.

El arnés corre `calibrar` en modo real: `E.tasas_barrido`, el cargador, el etiquetador y el predicado Node del
tablero originales; sólo la referencia de MIROVA es sintética (filas explícitas, sin red), como el soporte de casos
del cierre de Codex (D:/codex-vrp/_salida/ronda5/cierre/soporte_casos.py).

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría con el evaluador de antes (sha256 9d3ba4c1..., #1132)? Sí: el
evaluador sellado no excluye nada ni declara la exclusión; las pruebas de exclusión piden la clave `exclusion_comun` y
las de los frenos piden INVÁLIDO donde el sellado daba ELEGIDO (comprobado al escribirlas). (2) ¿Podría pasar sin mirar
nada? Cada freno tiene su gemelo que exige ELEGIDO con el mismo piso que el barrido sano, así que un evaluador que
dijera siempre INVÁLIDO, o que excluyera de más, también cae. `EVALUAR_PISO_PATH` apunta a la copia que se prueba
(mutaciones); por defecto, el del repo.
"""
import importlib.util
import json
import os
import sys
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUTA = Path(os.environ.get("EVALUAR_PISO_PATH", str(ROOT / "experiments" / "_s196_lab_piso" / "evaluar.py")))
LLAIMA = ROOT / "tests" / "datos_s202" / "llaima_20260530_nueve_brazos.json"
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as bp  # noqa: E402


def _cargar(ruta, nombre):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M = _cargar(RUTA, "evaluar_lab_piso_resello_s202")

# 120 noches de Láscar (una pasada MODIS a las 05:00 UTC cada noche): con 120 noches negativas, una excluida es el
# 0,83 % (bajo el tope del 1 %) y dos son el 1,7 %. Las primeras n de cada brazo publican; n crece con el piso, así que
# el barrido sano elige 0,00225 (33 de 120; 0,002 publica 42, sobre el 30 %).
FECHAS = [(datetime(2026, 4, 1, 5) + timedelta(days=i)).strftime("%Y-%m-%d %H:%M") for i in range(120)]
N_PUB = dict(zip(M.CAMINO, [12, 15, 21, 27, 33, 42, 54, 75]))
BRAZOS = ["sin_zona", M.CONTROL] + list(M.GRILLA_PISO) + ["prod"]
PISOS_BAJOS = [p for p in M.GRILLA_PISO if p != 0.00275]   # la escena real de Llaima: inválida en 6 de los 7 pisos
NOCHE_X = 100                                              # una noche que no publica en ningún brazo (100 >= 75)


def _rec(t, pub=False, sensor="MODIS_AQUA", motivo=None, lat=-23.37, lon=-67.73):
    return {"sensor": sensor, "datetime_utc": t, "vrp_mw": 1.0 if pub else 0.0, "distance_class": "summit",
            "via_codigo_mirova": True, "t_max_k": 400, "final_hotspot_lat": lat, "final_hotspot_lon": lon,
            "final_hotspot_dist_km": 0.4,
            "primary_cluster": {"vrp_mw": 1.0 if pub else 0.0, "centroid_dist_km": 0.4, "n_pixels": 1},
            "diag_codigo_mirova": {"n_abs": 0, "n_p1": int(pub), "n_p2": 0, "motivo_vacio": motivo, "dayflag": 0,
                                   "s1": {"pasada1": {"u_nti2": 0.003}}},
            "regimen": {"perfil": "laboratorio", "codigo_sha": "a" * 40}}


def _invalida(r, motivo):
    r.update(vrp_mw=0.0, primary_cluster={"vrp_mw": 0.0, "centroid_dist_km": None, "n_pixels": 0})
    r["diag_codigo_mirova"].update(motivo_vacio=motivo, n_p1=0)


def _fila(vol, t, bucket="MODIS", tipo="RUTINA"):
    return {"volcano": vol, "sensor_bucket": bucket, "fecha_utc": t + ":00", "tipo": tipo, "vrp_mw": 0,
            "source": "CONS", "dist_km": 0}


def _armar():
    d = {}
    for k in BRAZOS:
        n = N_PUB.get(k, N_PUB[M.CONTROL])
        d[k] = {v: [] for v in M.E.VOLCANES_ZONA_A + M.E.VOLCANES_FUERA}
        d[k]["Lascar"] = [_rec(t, i < n) for i, t in enumerate(FECHAS)]
        d[k]["PuyehueCordonCaulle"] = [_rec(t) for t in FECHAS[:40]]   # poder donde la zona no actúa (>= 30)
    return d, [_fila("Lascar", t) for t in FECHAS]


def _correr(tmp_path, monkeypatch, cambiar=None):
    data, filas = _armar()
    if cambiar:
        cambiar(data, filas)

    def referencia(dest):
        dest = Path(dest)
        dest.mkdir(parents=True, exist_ok=True)
        for n in M.CSV_REFERENCIA:
            (dest / n).write_text("referencia sintética\n", encoding="utf-8")
        return {n: {"path": str(dest / n), "sha": "x"} for n in M.CSV_REFERENCIA}

    monkeypatch.setattr(bp, "bajar_remoto", referencia)
    monkeypatch.setattr(bp, "cargar_referencia_unificada", lambda *a, **kw: deepcopy(filas))
    dirs = {}
    for k, vols in data.items():
        p = tmp_path / str(k).replace(".", "_")
        p.mkdir(parents=True, exist_ok=True)
        for v, recs in vols.items():
            (p / (v + ".json")).write_text(json.dumps({"records": recs}, ensure_ascii=False), encoding="utf-8")
        dirs[k] = str(p)
    return M.calibrar(dirs["sin_zona"], dirs[M.CONTROL], {p: dirs[p] for p in M.GRILLA_PISO}, dirs["prod"],
                      M.FIN_SELLADO, str(tmp_path / "ref"))


def _con_viirs(data, filas, i, sensor="VIIRS_NOAA20", minuto="05:30"):
    """Agrega a la noche i una pasada VIIRS 375 limpia en todos los brazos y su fila RUTINA."""
    t = FECHAS[i][:11] + minuto
    for k in data:
        data[k]["Lascar"].append(_rec(t, sensor=sensor))
    filas.append(_fila("Lascar", t, bucket="VIIRS375"))
    return t


def _modis_invalida_en(data, i, brazos, motivo="fondo_no_estimado"):
    for k in brazos:
        _invalida(data[k]["Lascar"][i], motivo)


# ----------------------------------------------------------------------------------------------- sello
def test_sello_tope_del_freno_2():
    assert M.TOPE_EXCLUIDAS == 0.01


def test_freno_2_frontera_entera():
    """«Pasan del 1 %»: estrictamente más que el 1 % de las noches negativas, en enteros."""
    assert not M.supera_tope(1, 100)
    assert M.supera_tope(2, 100)
    assert M.supera_tope(1, 99)
    assert not M.supera_tope(0, 0)


# ----------------------------------------------------------------------------------------------- el caso real
def test_llaima_real_la_unica_escena_de_validez_distinta():
    """Noche real de Llaima del 2026-05-30 en los nueve brazos (tanda de mayo, run 45462562013): la pasada MODIS Terra
    de las 02:55 es «fondo_no_estimado» en seis pisos y válida en sin zona, control y 0,00275 (ahí con 9,685 MW). Es la
    única de las 14 pasadas de la noche con validez distinta; las demás no se tocan."""
    d = json.loads(LLAIMA.read_text(encoding="utf-8"))["brazos"]
    nombres = {"sinzona": "sin_zona", "control": M.CONTROL, "p300": 0.003, "p275": 0.00275, "p250": 0.0025,
               "p225": 0.00225, "p200": 0.002, "p175": 0.00175, "p150": 0.0015}
    recs = {nombres[b]: [dict(r, _vol="Llaima") for r in rs] for b, rs in d.items()}
    x = M.escenas_validez_distinta(recs)
    assert set(x) == {("Llaima", "MODIS_TERRA", "2026-05-30 02:55")}
    motivos = x[("Llaima", "MODIS_TERRA", "2026-05-30 02:55")]
    assert motivos["sin_zona"] is None and motivos[M.CONTROL] is None and motivos[0.00275] is None
    assert all(motivos[p] == "fondo_no_estimado" for p in PISOS_BAJOS)


def test_llaima_real_en_calibrar_se_excluye_de_todos_y_no_decide(tmp_path, monkeypatch):
    """La noche real de Llaima dentro del barrido sintético: se excluye la pasada de las 02:55 de los nueve brazos y de
    producción, se declara, y la elección no cambia (la noche tiene otras 13 pasadas limpias)."""
    d = json.loads(LLAIMA.read_text(encoding="utf-8"))["brazos"]
    nombres = {"sinzona": "sin_zona", "control": M.CONTROL, "p300": 0.003, "p275": 0.00275, "p250": 0.0025,
               "p225": 0.00225, "p200": 0.002, "p175": 0.00175, "p150": 0.0015}

    def cambiar(data, filas):
        for b, rs in d.items():
            data[nombres[b]]["Llaima"] = deepcopy(rs)
        data["prod"]["Llaima"] = deepcopy(d["control"])
        filas.extend(_fila("Llaima", r["datetime_utc"], bucket=bp.bucket(r["sensor"])) for r in d["control"])

    r = _correr(tmp_path, monkeypatch, cambiar)
    assert r["estado"] == "ELEGIDO" and r["valor"]["piso_a"] == 0.00225, r["detalle"]
    ex = r["exclusion_comun"]
    assert ex["n"] == 1 and ex["decisivas"] == []
    assert [e["clave"] for e in ex["escenas"]] == [["Llaima", "MODIS_TERRA", "2026-05-30 02:55"]]
    # Los 9,685 MW de 0,00275 (summit) los publica el tablero: la exclusión le quita a ese brazo esa noche publicada.
    assert ex["publicaciones_quitadas"] == {"0.00275": 1}
    noches ={k: v["NOCHE"][1] for k, v in r["tasas"].items()}
    assert len(set(noches.values())) == 1 and r["tasas_produccion"]["NOCHE"][1] == noches[M.CONTROL]


# ----------------------------------------------------------------------------------------------- exclusión común
def test_gemelo_sano_no_excluye_nada(tmp_path, monkeypatch):
    r = _correr(tmp_path, monkeypatch)
    assert r["estado"] == "ELEGIDO" and r["valor"]["piso_a"] == 0.00225, r["detalle"]
    assert r["exclusion_comun"]["n"] == 0 and r["exclusion_comun"]["escenas"] == []


def test_escena_invalida_en_pisos_bajos_sale_de_todos_y_de_produccion(tmp_path, monkeypatch):
    """Como Llaima: la pasada MODIS de una noche con otra pasada limpia (VIIRS) es inválida en seis pisos, válida y
    publicada en 0,00275. Sale de los nueve brazos y de producción: las cuentas MODIS por pasada quedan iguales en
    todos (119 negativas), la noche sigue (120) y 0,00275 pierde la publicación que sólo él veía."""
    def cambiar(data, filas):
        _con_viirs(data, filas, NOCHE_X)
        _modis_invalida_en(data, NOCHE_X, PISOS_BAJOS)
        data[0.00275]["Lascar"][NOCHE_X].update(_rec(FECHAS[NOCHE_X], pub=True))
    r = _correr(tmp_path, monkeypatch, cambiar)
    assert r["estado"] == "ELEGIDO" and r["valor"]["piso_a"] == 0.00225, r["detalle"]
    ex = r["exclusion_comun"]
    assert ex["n"] == 1 and ex["decisivas"] == []
    assert ex["publicaciones_quitadas"] == {"0.00275": 1}
    assert {v["MODIS"][1] for v in r["tasas"].values()} == {119} and r["tasas_produccion"]["MODIS"][1] == 119
    assert {v["NOCHE"][1] for v in r["tasas"].values()} == {120}


def test_camino_inverso_viirs_375(tmp_path, monkeypatch):
    """R5C-V201: la pasada VIIRS 375 es «crater_no_evaluado» en sin zona, control, producción y los pisos altos, y
    válida y publicada en 0,002 a 0,0015. Sale de todos; los pisos bajos pierden esa publicación (declarada) y las
    cuentas VIIRS 375 quedan iguales en todos los brazos y en producción."""
    def cambiar(data, filas):
        _con_viirs(data, filas, NOCHE_X)
        for k in data:
            v = data[k]["Lascar"][-1]
            if k in (0.002, 0.00175, 0.0015):
                v.update(_rec(v["datetime_utc"], pub=True, sensor="VIIRS_NOAA20"))
            else:
                _invalida(v, "crater_no_evaluado")
    r = _correr(tmp_path, monkeypatch, cambiar)
    assert r["estado"] == "ELEGIDO" and r["valor"]["piso_a"] == 0.00225, r["detalle"]
    ex = r["exclusion_comun"]
    assert ex["n"] == 1 and ex["decisivas"] == []
    assert ex["publicaciones_quitadas"] == {"0.002": 1, "0.00175": 1, "0.0015": 1}
    assert len({v["VIIRS375"] for v in r["tasas"].values()} | {r["tasas_produccion"]["VIIRS375"]}) == 1


def test_invalida_en_los_nueve_no_es_exclusion_nueva(tmp_path, monkeypatch):
    """Una escena inválida en los nueve brazos (y en producción) ya salía de todos: no se declara como exclusión."""
    def cambiar(data, filas):
        _con_viirs(data, filas, NOCHE_X)
        _modis_invalida_en(data, NOCHE_X, list(data), motivo="escena_invalida")
    r = _correr(tmp_path, monkeypatch, cambiar)
    assert r["estado"] == "ELEGIDO", r["detalle"]
    assert r["exclusion_comun"]["n_total"] == 0


def test_hora_sin_cero_a_la_izquierda_es_la_misma_escena(tmp_path, monkeypatch):
    """R5C-108: el almacén acepta «5:00» (strptime lo lee); el banco reescribe la hora desde un datetime. La escena
    excluida tiene que ser la misma en las carpetas y en la réplica por noche (aquí publica en 0,00275: si la réplica
    no la reconociera como excluida, contaría esa publicación y no daría las cuentas de E.tasas_barrido)."""
    def cambiar(data, filas):
        _con_viirs(data, filas, NOCHE_X)
        _modis_invalida_en(data, NOCHE_X, PISOS_BAJOS)
        data[0.00275]["Lascar"][NOCHE_X].update(_rec(FECHAS[NOCHE_X], pub=True))
        for k in data:
            r = data[k]["Lascar"][NOCHE_X]
            r["datetime_utc"] = r["datetime_utc"].replace(" 05:00", " 5:00")
    r = _correr(tmp_path, monkeypatch, cambiar)
    assert r["estado"] == "ELEGIDO" and r["valor"]["piso_a"] == 0.00225, r["detalle"]
    assert r["exclusion_comun"]["n"] == 1 and r["exclusion_comun"]["replica_por_noche_igual"]
    assert r["exclusion_comun"]["publicaciones_quitadas"] == {"0.00275": 1}


def test_fuera_de_la_ventana_se_excluye_pero_no_cuenta_para_el_tope(tmp_path, monkeypatch):
    def cambiar(data, filas):
        for k in data:
            data[k]["Lascar"].append(_rec("2026-02-10 05:00"))
        for k in PISOS_BAJOS:
            _invalida(data[k]["Lascar"][-1], "fondo_no_estimado")
    r = _correr(tmp_path, monkeypatch, cambiar)
    assert r["estado"] == "ELEGIDO", r["detalle"]
    assert r["exclusion_comun"]["n_total"] == 1 and r["exclusion_comun"]["n"] == 0


# ----------------------------------------------------------------------------------------------- freno 1
def test_freno_1_caso_de_codex_unica_negativa_de_su_noche(tmp_path, monkeypatch):
    """El caso del cierre de Codex: la escena inválida en los pisos bajos es la única pasada de su noche. Excluirla
    saca la noche del denominador: decide su noche, INVÁLIDO (el evaluador sellado elegía en silencio)."""
    def cambiar(data, filas):
        _modis_invalida_en(data, NOCHE_X, PISOS_BAJOS)
    r = _correr(tmp_path, monkeypatch, cambiar)
    assert r["estado"] == M.INVALIDO and "decide su noche" in r["detalle"], r["detalle"]
    assert r["exclusion_comun"]["decisivas"]


def test_freno_1_unica_alerta_de_mirova_de_su_noche(tmp_path, monkeypatch):
    """La pasada MODIS es la única alerta de MIROVA de su noche (la VIIRS es limpia). Excluirla mete la noche en el
    denominador: decide su noche, INVÁLIDO."""
    def cambiar(data, filas):
        _con_viirs(data, filas, NOCHE_X)
        filas[NOCHE_X]["tipo"] = "ALERTA"
        _modis_invalida_en(data, NOCHE_X, PISOS_BAJOS)
    r = _correr(tmp_path, monkeypatch, cambiar)
    assert r["estado"] == M.INVALIDO and "decide su noche" in r["detalle"], r["detalle"]


def test_freno_1_gemelo_alerta_acompanada_no_decide(tmp_path, monkeypatch):
    """Gemelo: la noche tiene además otra alerta de MIROVA (una segunda pasada VIIRS): excluir la MODIS no la mete en
    el denominador."""
    def cambiar(data, filas):
        _con_viirs(data, filas, NOCHE_X)
        filas[-1]["tipo"] = "ALERTA"
        _con_viirs(data, filas, NOCHE_X, sensor="VIIRS_SNPP", minuto="06:30")
        filas[NOCHE_X]["tipo"] = "ALERTA"
        _modis_invalida_en(data, NOCHE_X, PISOS_BAJOS)
    r = _correr(tmp_path, monkeypatch, cambiar)
    assert r["estado"] == "ELEGIDO" and r["valor"]["piso_a"] == 0.00225, r["detalle"]
    assert r["exclusion_comun"]["n"] == 1 and r["exclusion_comun"]["decisivas"] == []


# ----------------------------------------------------------------------------------------------- freno 2
def test_freno_2_dos_excluidas_en_120_noches_es_invalido(tmp_path, monkeypatch):
    def cambiar(data, filas):
        for i in (NOCHE_X, NOCHE_X + 1):
            _con_viirs(data, filas, i)
            _modis_invalida_en(data, i, PISOS_BAJOS)
    r = _correr(tmp_path, monkeypatch, cambiar)
    assert r["estado"] == M.INVALIDO and "1 %" in r["detalle"], r["detalle"]
    assert r["exclusion_comun"]["n"] == 2


# ----------------------------------------------------------------------------------------------- réplica por noche
def test_replica_por_noche_que_no_coincide_con_tasas_barrido_invalida(tmp_path, monkeypatch):
    """La regla de los frenos mira las noches con una réplica del conteo de E.tasas_barrido; si la réplica no da las
    mismas cuentas por noche que E.tasas_barrido sobre las carpetas con la exclusión, el instrumento está roto."""
    monkeypatch.setattr(M, "noches_por_brazo", lambda brazos, fin, dest: {k: {} for k in brazos})

    def cambiar(data, filas):
        _con_viirs(data, filas, NOCHE_X)
        _modis_invalida_en(data, NOCHE_X, PISOS_BAJOS)
    r = _correr(tmp_path, monkeypatch, cambiar)
    assert r["estado"] == M.INVALIDO and "réplica" in r["detalle"], r["detalle"]
