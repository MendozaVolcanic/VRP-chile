# -*- coding: utf-8 -*-
"""S192: reemplazo de datos que sigue a #1065 (fondo nulo en MODIS, opción a de Nicolás del 2026-11-20).

POR QUÉ. #1065 hace que la vía «código MIROVA» trate como escena no medida una pasada MODIS en que ningún alertado tiene
fondo estimable, pero sólo en las pasadas nuevas. experiments/_s192_fondo_nulo/reemplazo_fondo_nulo.py lleva los
records ya guardados a la forma que la vía nueva habría escrito, sin reprocesar. Estas pruebas fijan que eso es lo
mismo que reprocesar y que no toca nada más:

1. Pasada real 3933 (Cordón Caulle 2026-03-16 03:10 MODIS Terra): el record del código del tag pre-s192-fondo-nulo,
   transformado por el script, es igual (claves y valores) al que da procesar_grilla de hoy. La única clave que el
   código viejo no producía es diag_codigo_mirova.alertados_sin_fondo, y el script la escribe con el mismo valor.
2. No toca VIIRS (MIROVA sí publica con fondo 0 en VIIRS), ni MODIS con fondo, ni K, ni escenas ya vacías.
3. Idempotente, y deja cada archivo con su mismo formato; un archivo sin objetivos no se reescribe.
4. Tablero: en las funciones reales de index, diario y mosaico la pasada deja de publicar 2,535 MW y se rotula
   «fondo no estimado».

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría con el script mal? Cada prueba compara contra el record de hoy o
contra el archivo original byte a byte, y las de «no toca» traen el control de que el objetivo sí cambia. (2) ¿Y si
el dato muriera? Las pruebas afirman el estado de partida (2,535 MW, 1 alertado, L_bk 0) antes de transformar.
"""
from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tests"))
sys.path.insert(0, str(RAIZ / "experiments" / "_s192_fondo_nulo"))

import armar_fixture_pre as F  # noqa: E402
import reemplazo_fondo_nulo as R  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402

DATOS = RAIZ / "tests" / "datos_s192_fondo_nulo"


def _dato(nombre):
    return json.loads((DATOS / nombre).read_text(encoding="utf-8"))["record"]


def _hoy(pid):
    """El record que escribe hoy procesar_grilla sobre la pasada real."""
    p, mir, tir, g, box, pos = F.entradas(pid)
    return F.normalizar(MV.procesar_grilla(mir, tir, g, box, p["dayflag"], p["sunglint"], pos, p["inner"],
                                           F.PASADAS[pid], familia="MODIS"))


# ------------------------------------------------------------------------------------------------ 1. equivalencia
def test_el_record_viejo_es_el_de_partida():
    viejo = _dato("pre_s192_3933.json")
    assert viejo["vrp_mw"] == 2.535 and viejo["n_anomalous_pixels"] == 1
    assert viejo["diag_codigo_mirova"]["L_bk"] == 0 and viejo["diag_codigo_mirova"]["motivo_vacio"] is None
    assert "alertados_sin_fondo" not in viejo["diag_codigo_mirova"]
    assert R.es_objetivo(viejo)


def test_viejo_transformado_es_lo_que_escribe_hoy_la_via():
    viejo = _dato("pre_s192_3933.json")
    hoy = _hoy(3933)
    # las claves que el código viejo no producía: sólo la marca nueva del diagnóstico
    assert set(hoy) == set(viejo)
    assert set(hoy["diag_codigo_mirova"]) - set(viejo["diag_codigo_mirova"]) == {"alertados_sin_fondo"}
    assert set(viejo["diag_codigo_mirova"]) <= set(hoy["diag_codigo_mirova"])
    t = R.transformar(copy.deepcopy(viejo))
    assert t == hoy
    # también el orden de las claves del diagnóstico (el JSON guardado se lee igual que uno nuevo)
    assert list(t["diag_codigo_mirova"]) == list(hoy["diag_codigo_mirova"])
    # control: sin transformar, el viejo no es el de hoy
    assert viejo != hoy


def test_el_dato_viejo_es_el_del_tag():
    """El record fijo es el que da el código del tag (Actions no trae tags: ahí se salta, no se da por bueno)."""
    viejo = F.modulo_viejo()
    if viejo is None:
        pytest.skip(f"git no tiene el tag {F.TAG}")
    for pid in F.PASADAS:
        assert F.record(viejo, pid) == _dato(f"pre_s192_{pid}.json")


def test_el_guardado_de_produccion_es_la_misma_deteccion():
    """El record que producción guardó para esa pasada es la misma detección del record viejo, y transformado queda
    con la forma de una escena vacía guardada (más alertados_sin_fondo y el motivo)."""
    g = _dato("guardado_pcc_modis_20260316_0310.json")
    viejo = _dato("pre_s192_3933.json")
    for k in ("L_bk", "n_abs", "n_p1", "n_p2", "roi"):
        assert g["diag_codigo_mirova"][k] == viejo["diag_codigo_mirova"][k], k
    # la grilla de tests/datos_s164_modis se guardó en float32: la radiancia coincide a 1e-9 relativo, no al bit
    assert g["diag_codigo_mirova"]["L_hot"] == pytest.approx(viejo["diag_codigo_mirova"]["L_hot"], rel=1e-6)
    # el mismo píxel alertado (s1 no se compara: el record guardado es de un código anterior al diagnóstico de hoy)
    assert [(p["fila"], p["col"], p["bt_k"]) for p in g["anomaly_pixels"]] == \
           [(p["fila"], p["col"], p["bt_k"]) for p in viejo["anomaly_pixels"]]
    assert g["vrp_mw"] == viejo["vrp_mw"] and R.es_objetivo(g)
    t = R.transformar(copy.deepcopy(g))
    assert t["vrp_mw"] == 0 and type(t["vrp_mw"]) is int          # como store.py guarda toda escena vacía de la vía
    assert t["n_anomalous_pixels"] == 0 and t["anomaly_pixels"] == []
    assert all(t[k] is None for k in R.NULAS)
    dg = t["diag_codigo_mirova"]
    assert dg["motivo_vacio"] == "fondo_no_estimado" and dg["alertados_sin_fondo"] == 1
    assert dg["L_hot"] == g["diag_codigo_mirova"]["L_hot"] and dg["L_bk"] == 0
    for k in ("granule", "datetime_utc", "processed_utc", "regimen", "solar_zenith_deg", "sensor"):
        assert t[k] == g[k], k
    assert set(t) == set(g) and not R.es_objetivo(t)


# ------------------------------------------------------------------------------------------------ 2. qué no toca
def _no_objetivos():
    viejo = _dato("pre_s192_3933.json")
    viirs = dict(copy.deepcopy(viejo), sensor="VIIRS_NOAA20_750")
    viirs375 = dict(copy.deepcopy(viejo), sensor="VIIRS_SNPP")
    con_fondo = _dato("pre_s192_1611.json")
    k = dict(copy.deepcopy(viejo), via_codigo_mirova="sin_grilla")
    k_sin_marca = {k2: v for k2, v in copy.deepcopy(viejo).items() if k2 != "via_codigo_mirova"}
    vacio = copy.deepcopy(_hoy(1611))
    vacio.update({"n_anomalous_pixels": 0, "vrp_mw": 0, "anomaly_pixels": []})
    vacio["diag_codigo_mirova"].update({"L_hot": None, "L_bk": None, "alertados_sin_fondo": None})
    ya = R.transformar(copy.deepcopy(viejo))
    return {"viirs750": viirs, "viirs375": viirs375, "modis_con_fondo": con_fondo, "k": k, "k_sin_marca": k_sin_marca,
            "vacio": vacio, "ya_transformado": ya}


@pytest.mark.parametrize("caso", sorted(_no_objetivos()))
def test_no_es_objetivo(caso):
    assert not R.es_objetivo(_no_objetivos()[caso])


def test_modis_con_fondo_es_real():
    """Control: la pasada 1611 tiene fondo (L_bk > 0) y su VRP es la protegida de 1,112 MW."""
    r = _dato("pre_s192_1611.json")
    assert r["diag_codigo_mirova"]["L_bk"] > 0 and r["vrp_mw"] == 1.112


def test_rehusa_claves_que_una_escena_vacia_no_tiene():
    r = dict(_dato("guardado_pcc_modis_20260316_0310.json"), diag_vrp_raw_mw=2.535)
    with pytest.raises(R.Rehusado):
        R.transformar(r)


# ------------------------------------------------------------------------------------------------ 3. archivos
def _escribir(ruta, obj, salto, **fmt):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps(obj, **fmt).replace("\n", salto) + salto)


def _arbol(tmp_path, salto="\n"):
    g = _dato("guardado_pcc_modis_20260316_0310.json")
    otros = _no_objetivos()
    me = {"volcano": "PuyehueCordonCaulle", "updated": "2026-11-20T00:00:00Z",
          "records": [otros["viirs750"], g, otros["modis_con_fondo"], otros["vacio"]]}
    hi = {"volcano": "Ñuble", "perfil": "_s172_retro_paquete", "hasta_utc": "2026-11-03 00:00",
          "records": [otros["k"], copy.deepcopy(g), otros["viirs375"]]}
    so = {"volcano": "MacaCay", "records": [otros["viirs750"], otros["vacio"]]}
    _escribir(tmp_path / "data/mirova_equivalent/PuyehueCordonCaulle.json", me, salto, indent=2)
    _escribir(tmp_path / "data/historia_34/Nuble.json", hi, salto, indent=1, ensure_ascii=False)
    _escribir(tmp_path / "data/sombra_34/MacaCay.json", so, salto, indent=2)
    return me, hi, so


def _bytes(tmp_path):
    return {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in sorted(tmp_path.rglob("*.json"))}


@pytest.mark.parametrize("salto", ["\n", "\r\n"])
def test_ensayo_cuenta_y_no_escribe(tmp_path, salto):
    _arbol(tmp_path, salto)
    antes = _bytes(tmp_path)
    inf = R.correr(tmp_path, aplicar=False)
    assert _bytes(tmp_path) == antes
    assert inf["total"] == 2 and not inf["aplicado"]
    assert inf["carpetas"]["data/mirova_equivalent"]["por_volcan"] == {"PuyehueCordonCaulle": 1}
    assert inf["carpetas"]["data/historia_34"]["por_volcan"] == {"Nuble": 1}
    assert inf["carpetas"]["data/sombra_34"]["records"] == 0


@pytest.mark.parametrize("salto", ["\n", "\r\n"])
def test_aplica_solo_el_objetivo_conserva_formato_y_es_idempotente(tmp_path, salto):
    me, hi, so = _arbol(tmp_path, salto)
    antes = _bytes(tmp_path)
    mtime_sombra = (tmp_path / "data/sombra_34/MacaCay.json").stat().st_mtime_ns
    inf = R.correr(tmp_path, aplicar=True)
    assert inf["aplicado"] and inf["total"] == 2
    despues = _bytes(tmp_path)
    # el archivo sin objetivos no se tocó
    assert despues["data/sombra_34/MacaCay.json"] == antes["data/sombra_34/MacaCay.json"]
    assert (tmp_path / "data/sombra_34/MacaCay.json").stat().st_mtime_ns == mtime_sombra
    # en los otros, cambió sólo el record objetivo, y el archivo es el original con ese record transformado,
    # en el mismo formato (sangría, ASCII y salto de línea)
    for rel, obj, i, fmt in (("data/mirova_equivalent/PuyehueCordonCaulle.json", me, 1, {"indent": 2}),
                             ("data/historia_34/Nuble.json", hi, 1, {"indent": 1, "ensure_ascii": False})):
        esperado = copy.deepcopy(obj)
        R.transformar(esperado["records"][i])
        assert despues[rel] == (json.dumps(esperado, **fmt).replace("\n", salto) + salto).encode("utf-8"), rel
        nuevo = json.loads(despues[rel])
        assert [r for j, r in enumerate(nuevo["records"]) if j != i] == \
               [r for j, r in enumerate(obj["records"]) if j != i]
    assert "Ñuble".encode("utf-8") in despues["data/historia_34/Nuble.json"]
    # idempotente: una segunda pasada no encuentra nada y no cambia ni un byte
    inf2 = R.correr(tmp_path, aplicar=True)
    assert inf2["total"] == 0 and _bytes(tmp_path) == despues


def test_rehusa_un_formato_que_no_reproduce_el_archivo(tmp_path):
    g = _dato("guardado_pcc_modis_20260316_0310.json")
    _escribir(tmp_path / "data/mirova_equivalent/X.json", {"records": [g]}, "\n", indent=4)
    antes = _bytes(tmp_path)
    with pytest.raises(R.Rehusado):
        R.correr(tmp_path, aplicar=True)
    assert _bytes(tmp_path) == antes


def test_main_escribe_informe_y_codigo(tmp_path):
    _arbol(tmp_path)
    inf_p = tmp_path / "inf" / "informe.json"
    assert R.main(["--raiz", str(tmp_path), "--informe", str(inf_p)]) == 0
    inf = json.loads(inf_p.read_text(encoding="utf-8"))
    assert inf["total"] == 2 and inf["records"][0]["vrp_mw_antes"] == 2.535
    _escribir(tmp_path / "data/sombra_34/Malo.json", {"records": [_dato("guardado_pcc_modis_20260316_0310.json")]},
              "\n", indent=3)
    assert R.main(["--raiz", str(tmp_path), "--informe", str(inf_p), "--aplicar"]) == 2
    assert "rehusado" in json.loads(inf_p.read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------ 4. tablero
def _fuente(src, nombre):
    """Texto completo de `function nombre(...) {...}`. Copia de la de test_tablero_escenas_invalidas_s183.py."""
    m = re.search(r"(?<![A-Za-z0-9_])function\s+" + re.escape(nombre) + r"\s*\(", src)
    if not m:
        raise AssertionError("no encontré " + nombre)
    i = src.index(") {", m.end()) + 2
    prof = 0
    for j in range(i, len(src)):
        prof += {"{": 1, "}": -1}.get(src[j], 0)
        if prof == 0:
            return src[m.start():j + 1]
    raise AssertionError("llave sin cerrar en " + nombre)


def _node(tmp_path, pagina, nombres, prefijo, cuerpo, datos):
    src = (RAIZ / "frontend" / pagina).read_text(encoding="utf-8")
    js = prefijo + "\n" + "\n".join(_fuente(src, n) for n in nombres) + "\nconst DATOS = " + json.dumps(datos) + \
        ";\n" + cuerpo
    f = tmp_path / f"t_{pagina}.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", str(f)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


@pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")
def test_tablero_deja_de_publicar_y_rotula(tmp_path):
    g = _dato("guardado_pcc_modis_20260316_0310.json")
    datos = [g, R.transformar(copy.deepcopy(g))]
    inner = 20   # inner_radius_km de PuyehueCordonCaulle (KML de MIROVA)
    out = _node(tmp_path, "index.html", ["mirovaEqVrp", "escenaSinDato", "rotuloPasadaSinPublicar", "isValidDetection"],
                "", f"process.stdout.write(JSON.stringify(DATOS.map(r => [mirovaEqVrp(r, {inner}), escenaSinDato(r), "
                "rotuloPasadaSinPublicar(r).texto])));", datos)
    assert out[0][:2] == [2.535, None]                       # antes: se publica
    assert out[1] == [0, "fondo no estimado", "fondo no estimado"]
    mos = _node(tmp_path, "mosaico.html", ["mirovaEqVrp"], "",
                f"process.stdout.write(JSON.stringify(DATOS.map(r => mirovaEqVrp(r, {inner}))));", datos)
    assert mos == [2.535, 0]
    dia = _node(tmp_path, "diario.html", ["mirovaEqVrp"],
                f"const includeFarDistance = false; const INNER_RADIUS_KM = {{PuyehueCordonCaulle: {inner}}};",
                "process.stdout.write(JSON.stringify(DATOS.map(r => mirovaEqVrp(r, 'PuyehueCordonCaulle'))));", datos)
    assert dia == [2.535, 0]
