# -*- coding: utf-8 -*-
"""Re-sello del evaluador del piso de la zona A del laboratorio (S200, decisión de Nicolás del 2026-11-25).

POR QUÉ. La ronda 4 de la auditoría externa con Codex (frente D) y su verificador Claude de contexto limpio
reprodujeron cuatro defectos de gravedad 3 en `experiments/_s196_lab_piso/evaluar.py`, antes de que nadie mirara un
resultado del barrido (`experiments/_s196_lab_piso/PROPUESTA_RESELLO_S199.md`, #1123). Nicolás decidió re-sellar el
2026-11-25. Cada prueba de este archivo fija un arreglo y FALLA con el evaluador sellado antes del re-sello
(`evaluar.py` sellado en `b39778bb2`, el último commit que lo tocó antes del re-sello; comprobado al escribirlas: 10
fallan y pasan sólo el gemelo sano y la diferencia de noche, que el sellado ya invalidaba):

  R4FD-V201  producción guarda MODIS de día desde el 2026-11-15 y el laboratorio no: el control de cuentas salía
             INVÁLIDO por construcción. Arreglo: producción se cuenta sin lo que el almacén del laboratorio rechaza.
  R4FD-101   un brazo que pierde pasadas cambiaba la elección sin invalidarla. Arreglo: todos los brazos cubren las
             mismas pasadas dentro de la ventana; si no, INVÁLIDO.
  R4FD-102   «idéntico donde la zona no actúa» se declaraba comparando casi nada. Arreglo: con menos de N_MIN_FUERA
             records comparados en algún brazo, SIN PODER.
  R4FD-105   brazos de código distinto se mezclaban sin aviso. Arreglo: en cada pasada todos los brazos traen el mismo
             `regimen.codigo_sha`; los cambios de código entre tandas se declaran en la salida.
  R4FD-106   la referencia de MIROVA se bajaba dos veces y no quedaba su procedencia. Arreglo: una sola bajada y el
             sha256 de los dos CSV en la salida.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría con el evaluador de antes? Sí, cada una (arriba). (2) ¿Podría pasar
sin mirar nada? Cada caso tiene su gemelo sano que exige ELEGIDO, así que un evaluador que dijera siempre INVÁLIDO o
SIN PODER también cae. `EVALUAR_PISO_PATH` apunta a la copia que se prueba (mutaciones); por defecto, el del repo.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUTA = Path(os.environ.get("EVALUAR_PISO_PATH", str(ROOT / "experiments" / "_s196_lab_piso" / "evaluar.py")))


def _cargar(ruta, nombre):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M = _cargar(RUTA, "evaluar_lab_piso_resello_s200")

BASE = {M.CONTROL: .08, 0.003: .12, 0.00275: .17, 0.0025: .20, 0.00225: .26, 0.002: .35, 0.00175: .48, 0.0015: .62}
SHA = "a" * 40


def _rec(t, dayflag, sensor="MODIS_AQUA", sha=SHA, vrp=0.0):
    return {"sensor": sensor, "datetime_utc": t, "vrp_mw": vrp, "distance_class": "summit", "via_codigo_mirova": True,
            "final_hotspot_lat": -23.37, "final_hotspot_lon": -67.73, "final_hotspot_dist_km": 0.4,
            "primary_cluster": {"vrp_mw": vrp, "centroid_dist_km": 0.4, "n_pixels": 1},
            "diag_codigo_mirova": {"n_abs": 0, "n_p1": 0, "n_p2": 0, "motivo_vacio": None, "dayflag": dayflag},
            "regimen": {"perfil": "laboratorio", "codigo_sha": sha}}


def _recs_lab(n_dia=40):
    """Láscar: 40 noches (05:00 UTC, de noche en Láscar) y n_dia pasadas VIIRS de día (dayflag 1: la zona no actúa)."""
    noches = [_rec("2026-03-%02d 05:00" % (d % 28 + 1) if d < 28 else "2026-04-%02d 05:00" % (d - 27), 0)
              for d in range(40)]
    dias = [_rec("2026-05-%02d 17:00" % (d % 28 + 1) if d < 28 else "2026-06-%02d 17:00" % (d - 27), 1,
                 sensor="VIIRS_NOAA20") for d in range(n_dia)]
    return {"Lascar": noches + dias}


def _escribir(carpeta, recs_por_vol):
    carpeta.mkdir(parents=True, exist_ok=True)
    for vol in M.E.VOLCANES_ZONA_A:
        (carpeta / ("%s.json" % vol)).write_text(json.dumps({"records": recs_por_vol.get(vol, [])}), encoding="utf-8")
    return str(carpeta)


def _n_modis(carpeta):
    return sum(1 for r in json.loads((Path(carpeta) / "Lascar.json").read_text(encoding="utf-8"))["records"]
               if r["sensor"].startswith("MODIS"))


def _armar(tmp_path, monkeypatch, cambiar=None, prod_extra=None, n_dia=40):
    """Barrido sintético. Las cuentas falsas dependen de los records: MODIS cuenta cuántos records MODIS trae la
    carpeta (así una pasada MODIS de día de más en producción rompe el control de cuentas, como en R4FD-V201)."""
    llamadas = []

    def tasas_falsas(brazos, fin, dest):
        llamadas.append(sorted(str(k) for k in brazos))
        Path(dest).mkdir(parents=True, exist_ok=True)
        for nombre in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
            (Path(dest) / nombre).write_bytes(("referencia %s\n" % nombre).encode("utf-8"))
        out = {}
        for k, d in brazos.items():
            t = BASE[M.CONTROL] if k == "prod" else BASE[k]
            out[k] = {c: (round(t * 1000), 1000) for c in M.E.SENSORES + ("NOCHE",)}
            out[k]["MODIS"] = (0, 1000 + _n_modis(d))
        return out

    monkeypatch.setattr(M.E, "tasas_barrido", tasas_falsas)
    dirs = {}
    for nombre in ["sin_zona", M.CONTROL] + [str(p) for p in M.GRILLA_PISO]:
        recs = _recs_lab(n_dia)
        if cambiar:
            cambiar(nombre, recs)
        dirs[nombre] = _escribir(tmp_path / nombre.replace(".", "_"), recs)
    prod_recs = _recs_lab(n_dia)
    prod_recs["Lascar"] += prod_extra or []
    prod = _escribir(tmp_path / "prod", prod_recs)
    r = M.calibrar(dirs["sin_zona"], dirs[M.CONTROL], {p: dirs[str(p)] for p in M.GRILLA_PISO}, prod, "2026-11-23",
                   str(tmp_path / "ref"))
    return r, llamadas


def test_gemelo_sano_elige(tmp_path, monkeypatch):
    r, _ = _armar(tmp_path, monkeypatch)
    assert r["estado"] == "ELEGIDO" and r["valor"]["piso_a"] == 0.00225


# ----------------------------------------------------------------------------------------------- R4FD-V201
def test_v201_el_almacen_del_laboratorio_rechaza_modis_de_dia_y_nada_mas():
    # Láscar, 2026-11-20: 15:00 UTC es media mañana (sol arriba); 05:00 UTC es de noche.
    assert M.rechaza_como_laboratorio({"sensor": "MODIS_TERRA", "datetime_utc": "2026-11-20 15:00"}, "Lascar")
    assert not M.rechaza_como_laboratorio({"sensor": "MODIS_TERRA", "datetime_utc": "2026-11-20 05:00"}, "Lascar")
    assert not M.rechaza_como_laboratorio({"sensor": "VIIRS_NOAA20", "datetime_utc": "2026-11-20 15:00"}, "Lascar")
    assert not M.rechaza_como_laboratorio({"sensor": "MODIS_TERRA", "datetime_utc": "sin hora"}, "Lascar")


def test_v201_modis_de_dia_en_produccion_no_invalida_el_control(tmp_path, monkeypatch):
    dia = _rec("2026-11-20 15:00", 1, sensor="MODIS_TERRA")
    r, _ = _armar(tmp_path, monkeypatch, prod_extra=[dia])
    assert r["estado"] == "ELEGIDO", r["detalle"]
    assert r["produccion_como_laboratorio"]["quitados"]["Lascar"] == 1


def test_v201_una_diferencia_de_noche_sigue_invalidando(tmp_path, monkeypatch):
    noche = _rec("2026-11-20 05:00", 0, sensor="MODIS_TERRA")   # el almacén del laboratorio no la rechaza
    r, _ = _armar(tmp_path, monkeypatch, prod_extra=[noche])
    assert r["estado"] == M.INVALIDO and "cuentas de producción" in r["detalle"]


# ----------------------------------------------------------------------------------------------- R4FD-101
def test_101_un_brazo_que_pierde_una_pasada_invalida(tmp_path, monkeypatch):
    def cambiar(nombre, recs):
        if nombre == "0.00175":
            del recs["Lascar"][3]                                 # una noche menos en un brazo
    r, _ = _armar(tmp_path, monkeypatch, cambiar)
    assert r["estado"] == M.INVALIDO and "mismas pasadas" in r["detalle"]
    assert r["cobertura_brazos"]["diferencias"]["0.00175"]["faltan"] == 1


def test_101_fuera_de_la_ventana_no_cuenta(tmp_path, monkeypatch):
    def cambiar(nombre, recs):
        if nombre == "0.00175":
            recs["Lascar"].append(_rec("2026-02-10 05:00", 0))   # antes de VENTANA_CALIBRACION_INICIO
    r, _ = _armar(tmp_path, monkeypatch, cambiar)
    assert r["cobertura_brazos"]["igual"]


# ----------------------------------------------------------------------------------------------- R4FD-102
def test_102_donde_no_actua_con_pocos_records_es_sin_poder(tmp_path, monkeypatch):
    r, _ = _armar(tmp_path, monkeypatch, n_dia=M.N_MIN_FUERA - 1)
    assert r["estado"] == M.SIN_PODER and "no actúa" in r["detalle"]


def test_102_con_el_minimo_exacto_no_es_sin_poder(tmp_path, monkeypatch):
    r, _ = _armar(tmp_path, monkeypatch, n_dia=M.N_MIN_FUERA)
    assert r["estado"] == "ELEGIDO"


def test_102_el_minimo_es_el_umbral_de_poder_del_preregistro():
    assert M.N_MIN_FUERA == M.N_MIN_NEG == 30


# ----------------------------------------------------------------------------------------------- R4FD-105
def test_105_un_brazo_con_otro_codigo_invalida(tmp_path, monkeypatch):
    def cambiar(nombre, recs):
        if nombre == "0.002":
            recs["Lascar"][5]["regimen"]["codigo_sha"] = "b" * 40
    r, _ = _armar(tmp_path, monkeypatch, cambiar)
    assert r["estado"] == M.INVALIDO and "mismo código" in r["detalle"]


def test_105_un_cambio_de_codigo_entre_tandas_se_declara_y_no_invalida(tmp_path, monkeypatch):
    def cambiar(nombre, recs):
        for x in recs["Lascar"]:
            if x["datetime_utc"] >= "2026-04":
                x["regimen"]["codigo_sha"] = "c" * 40             # todos los brazos: la tanda siguiente
    r, _ = _armar(tmp_path, monkeypatch, cambiar)
    assert r["estado"] == "ELEGIDO"
    assert sorted(r["codigo_brazos"]["codigos"]) == ["a" * 40, "c" * 40]


# ----------------------------------------------------------------------------------------------- R4FD-106
def test_106_una_sola_bajada_de_la_referencia_y_su_procedencia(tmp_path, monkeypatch):
    r, llamadas = _armar(tmp_path, monkeypatch)
    assert len(llamadas) == 1 and "prod" in llamadas[0]
    h = hashlib.sha256(b"referencia registro_vrp_ocr.csv\n").hexdigest()
    assert r["referencia_mirova"]["registro_vrp_ocr.csv"] == h
    assert set(r["referencia_mirova"]) == {"registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"}


# ----------------------------------------------------------------------------------------------- re-sello S200b
# Observaciones del verificador independiente de #1129 (D:\vrp-trabajo\temporales\s200\verif_1129\VEREDICTO.md, efectos
# no buscados 1, 2 y 6). Fallan con el evaluador de #1129 (sha256 5493f1a7...) y pasan con el de S200b.
def test_b1_sin_poder_no_tapa_un_invalido_por_tasa_no_monotona(tmp_path, monkeypatch):
    """Tasa no monótona (instrumento roto) y pocos records donde la zona no actúa: manda INVÁLIDO, no SIN PODER."""
    mono = dict(BASE)
    BASE[0.0025] = .16                                           # baja en el camino: no monótona
    try:
        r, _ = _armar(tmp_path, monkeypatch, n_dia=M.N_MIN_FUERA - 1)
    finally:
        BASE.clear()
        BASE.update(mono)
    assert r["estado"] == M.INVALIDO and "monótona" in r["detalle"]


def test_b2_el_poder_cuenta_solo_records_dentro_de_la_ventana(tmp_path, monkeypatch):
    """Los records donde la zona no actúa fuera de la ventana de calibración no dan poder."""
    def cambiar(nombre, recs):
        for x in recs["Lascar"]:
            if x["diag_codigo_mirova"]["dayflag"] == 1:
                # mayo y junio pasan a diciembre de 2025 y enero de 2026, antes de VENTANA_CALIBRACION_INICIO y sin
                # que dos pasadas caigan en la misma hora (las 40 siguen siendo distintas)
                mes = {"2026-05": "2025-12", "2026-06": "2026-01"}[x["datetime_utc"][:7]]
                x["datetime_utc"] = mes + x["datetime_utc"][7:]
    r, _ = _armar(tmp_path, monkeypatch, cambiar)
    assert r["estado"] == M.SIN_PODER and "no actúa" in r["detalle"]


def test_b3_las_coordenadas_se_leen_una_vez_por_corrida(tmp_path, monkeypatch):
    """El filtro de día releía volcanoes.yaml en cada record (unos 82 min sobre producción entera, medido por el
    verificador); ahora una vez por llamada a prod_como_laboratorio."""
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import banco_paridad as bp
    llamadas = []
    real = bp._coords_por_volcan
    monkeypatch.setattr(bp, "_coords_por_volcan", lambda: llamadas.append(1) or real())
    recs = _recs_lab(40)["Lascar"] + [_rec("2026-11-20 15:00", 1, sensor="MODIS_TERRA")]
    prod = _escribir(tmp_path / "prod", {"Lascar": recs})
    _, quitados = M.prod_como_laboratorio(prod, tmp_path / "salida")
    assert quitados["Lascar"] == 1
    assert len(llamadas) == 1
