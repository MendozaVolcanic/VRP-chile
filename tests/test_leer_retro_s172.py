# -*- coding: utf-8 -*-
"""S173: batería sintética del lector de la prueba retrospectiva del paquete (pre-registro SELLADO
experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md, tag s173-prereg-retro-sellado, §5, §6 y §8.1).

POR QUÉ. El lector convierte miles de pasadas en un nombre de veredicto por sensor. Si una fila del §8.1 estuviera mal
ordenada, si un control no pudiera caer o si la etiqueta del OCR decidiera donde manda la tabla, el veredicto saldría
plausible y equivocado. Cada escenario arma, sin red y sin node (predicado sintético), una población donde la respuesta
correcta se sabe de antemano, y exige esa respuesta.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Control negativo: la vía idéntica a K no puede «ganar» (sale SIN PODER), y un
placebo que no mueve nada no da MEJORA. (2) Control positivo: una protegida que la vía pierde y K publica da la fila 2;
una vía que publica de más en negativos da la fila 3; un control en rojo da la fila 1. El conteo de mutaciones
atrapadas por aserción vive en experiments/_s172_retro_paquete/mutar_leer_retro.py.
"""
import collections
import copy
import csv
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "_s172_retro_paquete"
# mutar_leer_retro.py corre esta batería contra una copia mutada del lector (LEER_RETRO_MODULO)
_RUTA = Path(os.environ.get("LEER_RETRO_MODULO") or EXP / "leer_retro.py")
_spec = importlib.util.spec_from_file_location("leer_retro_bajo_prueba", _RUTA)
L = importlib.util.module_from_spec(_spec)
sys.modules["leer_retro_bajo_prueba"] = L
_spec.loader.exec_module(L)


@pytest.fixture(scope="module")
def R():
    return L.Reglas()


def pred(casos):
    """Predicado sintético: publica un cúmulo de cumbre con energía; la magnitud es la del cúmulo."""
    out = []
    for r, _inner in casos:
        r = r or {}
        pc = r.get("primary_cluster") or {}
        v = float(pc.get("vrp_mw") or 0.0)
        out.append((1 if r.get("distance_class") == "summit" and v > 0 else 0, v))
    return out


def F(vol, dia, lab, k, v, mk=2.0, mv=None, sensor="MODIS_AQUA", b="MODIS", tramo="F26-M", mir=None, z=20.0,
      hora="05:00", lab_union=None, vc=None, vp=None):
    mv = mk if mv is None else mv
    t = {"K": {"pub": k, "mag": mk if k else 0.0}, "placebo": {"pub": k, "mag": mk * 1.2 if k else 0.0},
         "V": {"pub": v, "mag": mv if v else 0.0}}
    t["V-cercano"] = dict(t["V"]) if vc is None else {"pub": vc, "mag": mv if vc else 0.0}
    t["V-pico"] = dict(t["V"]) if vp is None else {"pub": vp, "mag": mv if vp else 0.0}
    f = {"vol": vol, "sensor": sensor, "b": b, "dt": f"{dia} {hora}", "noche": dia, "tramo": tramo, "z": z,
         "inner": 5.0, "estado": "ok", "_evaluable": True, "lab": lab,
         "vrp_mirova": mir if mir is not None else (2.0 if lab == "protegida" else 0.3 if lab == "bajo1" else None),
         "k_rec": {"sensor": sensor}, "via_rec": {"sensor": sensor, "via_codigo_mirova": True}, "via_marca": True,
         "_t": t}
    if lab_union:
        f["lab_union"] = lab_union
    return f


def dias(n, mes="02"):
    return [f"2026-{mes}-{d:02d}" for d in range(1, n + 1)]


def poblacion(b="MODIS", sensor="MODIS_AQUA", tramo="F26-M", gana=8, extra=()):
    """Base: protegidas que los dos publican en 6 noches, 6 alertas bajo 1 MW que los dos publican con la misma
    magnitud (M NEUTRO), `gana` noches con un negativo que K publica y la vía no, y negativos que ninguno publica."""
    fs = []
    vols = ("Lascar", "Isluga", "Lastarria")
    for i, d in enumerate(dias(6)):
        fs.append(F(vols[i % 3], d, "protegida", 1, 1, sensor=sensor, b=b, tramo=tramo, hora="05:10"))
        fs.append(F(vols[i % 3], d, "bajo1", 1, 1, mk=0.2, sensor=sensor, b=b, tramo=tramo, mir=0.3, hora="05:20"))
    for d in dias(gana, "03" if tramo == "F26-V" else "02")[:gana]:
        fs.append(F("Villarrica", d, "neg_limpio", 1, 0, mk=0.1, sensor=sensor, b=b, tramo=tramo, hora="06:00"))
    for d in dias(20):
        fs.append(F("Copahue", d, "neg_limpio", 0, 0, sensor=sensor, b=b, tramo=tramo, hora="06:30"))
    return fs + list(extra)


OK = {"estado": "OK"}
COMUNES = {"candado": OK, "c_cobertura": OK, "c_k": OK, "nulo_runner": OK, "c_montaje": OK}


def leer(R, filas, sensor, **kw):
    return L.leer_sensor(R, filas, sensor, COMUNES, pred, kw.pop("sellado", False), kw.pop("caja", "def"), **kw)


# ------------------------------------------------------------------------------------------- MODIS (MOD-D §7)
def test_modis_via_mejor_que_k_no_se_contradice(R):
    r = leer(R, poblacion(), "MODIS")
    assert r["fila"] == 6, (r["regla"], r["motivos"])
    assert r["veredicto"].startswith("NO SE CONTRADICE") and "Lascar" in r["veredicto"]
    assert r["controles"]["nulo_lector"]["estado"] == "OK", r["controles"]["nulo_lector"]


def test_modis_pierde_protegida_que_k_publica(R):
    fs = poblacion(extra=[F("Lascar", "2026-02-16", "protegida", 1, 0, hora="01:20")])
    r = leer(R, fs, "MODIS")
    assert r["fila"] == 2 and "Lascar" in r["veredicto"]


def test_modis_publica_de_mas_es_peor_que_k(R):
    fs = poblacion(gana=0, extra=[F("Llaima", d, "neg_limpio", 0, 1, mk=0.1, hora="07:00") for d in dias(8)])
    r = leer(R, fs, "MODIS")
    assert r["fila"] == 3, r["regla"]


def test_modis_sin_sustrato_es_sin_poder(R):
    r = leer(R, poblacion(gana=3), "MODIS")
    assert r["fila"] == 5 and r["regla"]["B"] == 3


def test_sin_poder_no_tapa_una_condicion_de_la_fila_4(R):
    """VPR172-03: la fila 4 va antes que la 5. Sin sustrato en P2 y una protegida sólo del OCR que la vía pierde y K
    publica: DECIDE NICOLÁS, no SIN PODER."""
    fs = poblacion(gana=3, extra=[F("Lascar", "2026-02-21", "bajo1", 1, 0, hora="02:30", lab_union="protegida")])
    r = leer(R, fs, "MODIS")
    assert r["regla"]["p2"] == "SIN SUSTRATO"
    assert r["fila"] == 4 and "solo_ocr_que_k_publica" in r["motivos"]


def test_control_negativo_via_identica_a_k_no_gana(R):
    fs = poblacion(gana=0)
    for f in fs:
        for b in L.BRAZOS:
            f["_t"][b] = dict(f["_t"]["K"])
    r = leer(R, fs, "MODIS")
    assert r["fila"] == 5 and r["regla"]["B"] == 0


def test_modis_p1b_lleva_a_nicolas(R):
    fs = poblacion(extra=[F("Lascar", "2026-02-20", "protegida", 1, 1, mk=1.5, mv=0.6, hora="02:00")])
    r = leer(R, fs, "MODIS")
    assert r["fila"] == 4 and r["regla"]["p1b_decide"]


def test_un_control_en_rojo_es_indecidible(R):
    com = dict(COMUNES, c_k={"estado": "ROJO: sin K-gemelo"})
    r = L.leer_sensor(R, poblacion(), "MODIS", com, pred, False, "def")
    assert r["fila"] == 1 and "c_k" in r["motivos"]


def test_protegida_sin_dato_que_k_publica_es_fila_2(R):
    # 10 protegidas más, para que una SIN DATO quede bajo el 10 % de la clase (si no, cae C-cobertura: fila 1)
    fs = poblacion(extra=[F("Lascar", d, "protegida", 1, 1, hora="04:00") for d in dias(10)])
    s = F("Lascar", "2026-02-25", "protegida", 1, 0, hora="03:00")
    s["estado"], s["_evaluable"] = "sin_dato_cobertura", False
    r = leer(R, fs + [s], "MODIS")
    assert r["fila"] == 2
    r = leer(R, poblacion() + [s], "MODIS")             # 1 de 7 protegidas SIN DATO: más de 10 %, C-cobertura cae
    assert r["fila"] == 1 and "c_cobertura" in r["motivos"]


def test_veredicto_cambia_sin_las_pasadas_b_va_a_nicolas(R):
    # sin la pasada nombrada de Lastarria 2026-02-24 07:05 la vía no tiene con qué ganar
    fs = poblacion(gana=4, extra=[F("Lastarria", "2026-02-24", "neg_limpio", 1, 0, mk=0.1, hora="07:05")])
    r = leer(R, fs, "MODIS")
    assert r["regla"]["_fila_regla"] == 6 and r["regla_sin_pasadas_b"] == 5
    assert r["fila"] == 4 and "cambia_sin_pasadas_b" in r["motivos"]


# ------------------------------------------------------------------------------------------- VIIRS 375 (V375-E)
def v375(**kw):
    return poblacion(b="VIIRS375", sensor="VIIRS_NOAA20", tramo="F26-V", **kw)


def test_v375_cumple_con_cercano_y_radiante_iguales(R):
    r = leer(R, v375(), "VIIRS375")
    assert r["brazo"] == "V-cercano"
    assert r["fila"] == 6, (r["regla"], r["motivos"])


def test_v375_cercano_y_radiante_distintos_va_a_nicolas(R):
    fs = v375(extra=[F("Lascar", "2026-02-27", "protegida", 1, 0, vc=1, sensor="VIIRS_NOAA20", b="VIIRS375",
                       tramo="F26-V", hora="02:00")])
    r = leer(R, fs, "VIIRS375")
    assert r["regla"]["_fila_regla"] == 6 and r["otros_brazos"]["radiante"]["_fila_regla"] == 2
    assert r["fila"] == 4 and "cercano_y_radiante_difieren" in r["motivos"]


def test_v375_sin_sustrato_cumple_en_v375e_pero_aqui_es_sin_poder(R):
    r = leer(R, v375(gana=2), "VIIRS375")
    assert r["regla"]["criterios"]["b"] == "CUMPLE" and r["regla"]["p2"] == "SIN SUSTRATO"
    assert r["fila"] == 5


def test_v375_pierde_protegida(R):
    fs = v375(extra=[F("Lascar", "2026-02-27", "protegida", 1, 0, sensor="VIIRS_NOAA20", b="VIIRS375",
                       tramo="F26-V", hora="02:00")])
    assert leer(R, fs, "VIIRS375")["fila"] == 2


def test_solo_ocr_no_decide_y_n3_no_lleva_a_nicolas(R):
    """§4.1: la protegida sólo del OCR no veta; si la vía la pierde y K la publica, DECIDE NICOLÁS, salvo N-3 (Suomi
    NPP antes del 2026-10-09, L4), que se informa."""
    base = dict(sensor="VIIRS_NOAA20", b="VIIRS375", tramo="F26-V", hora="02:00", lab_union="protegida")
    r = leer(R, v375(extra=[F("Lascar", "2026-02-27", "bajo1", 1, 0, **base)]), "VIIRS375")
    assert r["fila"] == 4 and r["extra"]["solo_ocr_que_k_publica"]
    base["sensor"] = "VIIRS_SNPP"
    r = leer(R, v375(extra=[F("Lascar", "2026-02-27", "bajo1", 1, 0, **base)]), "VIIRS375")
    assert not r["extra"]["solo_ocr_que_k_publica"]


# ------------------------------------------------------------------------------------------- VIIRS 750 (V750-A)
def v750(**kw):
    return poblacion(b="VIIRS750", sensor="VIIRS_NOAA20_750", tramo="F26-V", **kw)


def _con_roi(fs, roi):
    for f in fs:
        f["via_rec"]["diag_codigo_mirova"] = {"roi": roi}
    return fs


def test_v750_sin_sello_de_v750a_el_techo_es_nicolas(R):
    r = leer(R, _con_roi(v750(), "def"), "VIIRS750")
    assert r["fila"] == 4 and "v750a_no_sellado" in r["motivos"]


def test_v750_sin_caja_declarada_es_indecidible(R):
    r = leer(R, _con_roi(v750(), "def"), "VIIRS750", caja=None)
    assert r["fila"] == 1 and "c_montaje_caja_v750" in r["motivos"]


def test_v750_records_con_otra_caja_es_indecidible(R):
    r = leer(R, _con_roi(v750(), "sens"), "VIIRS750", caja="def")
    assert r["fila"] == 1


def test_v750_sellado_con_magnitud_fuera_de_banda_es_peor_que_k(R):
    fs = _con_roi(v750(), "def")
    for f in fs:
        if f["lab"] == "protegida":
            for b in L.BRAZOS:
                f["_t"][b]["mag"] = 4.0          # razón 2 contra MIROVA, fuera de [0,9; 1,1]
    r = leer(R, fs, "VIIRS750", sellado=True, separa_v750=lambda R_, filas, b: True)   # VPR940-01: separa es control
    assert r["fila"] == 3 and not r["regla"]["razon_protegidas"]["en_banda_0_9_1_1"]


# ------------------------------------------------------------------------------------------- controles
def test_c_via_f26_cien_por_ciento_y_r25_diez_por_clase():
    fs = [F("Lascar", d, "neg_limpio", 0, 0) for d in dias(20)]
    assert L.c_via(fs, "F26-M")["estado"] == "OK"
    fs[0]["estado"] = "via_sin_marca:sin_grilla"
    assert L.c_via(fs, "F26-M")["estado"].startswith("ROJO")
    assert L.c_via(fs, "R25")["estado"] == "OK"                  # 1 de 20 = 5 %
    fs[1]["estado"] = fs[2]["estado"] = "via_sin_marca:sin_mxd03"
    assert L.c_via(fs, "R25")["estado"].startswith("ROJO")       # 3 de 20 = 15 %


def test_c_cobertura_ve_la_via_vacia_y_las_repetidas():
    fs = [F("Lascar", d, "neg_limpio", 0, 0) for d in dias(20)]
    assert L.c_cobertura(fs)["estado"] == "OK"
    assert L.c_cobertura(fs, repetidas=[("Lascar", "MODIS_AQUA", "2026-02-01 05:00")])["estado"].startswith("ROJO")
    for f in fs:
        f["estado"] = "sin_dato_cobertura"
    assert L.c_cobertura(fs)["estado"].startswith("ROJO")


def _ck_filas(n=6):
    fs = [F("Lascar", d, "neg_limpio", 1, 1, mk=0.4) for d in dias(n)]
    fs += [F("Lascar", d, "bajo1", 1, 1, mk=0.4, mir=0.3, hora="06:00") for d in dias(n)]
    fs += [F("Lascar", f"2026-10-{d:02d}", "neg_limpio", 0, 0, tramo="DM", hora="05:30") for d in (1, 2)]
    for f in fs:
        f["en_kgemelo"] = True
        f["k_rec"] = {"primary_cluster": {"vrp_mw": 0.4}}
        f["kg_rec"] = {"primary_cluster": {"vrp_mw": 0.4}}
        f["_t"]["KG"] = dict(f["_t"]["K"])
    return fs


def test_c_k_tope_de_tres_excepciones_con_empate():
    fs = _ck_filas()
    assert L.c_k(fs)["estado"] == "OK"
    for f in fs[:4]:
        f["kg_rec"] = {"primary_cluster": {"vrp_mw": 0.5}}       # 4 diferencias de magnitud (más de 0,001 MW)
    assert L.c_k(fs)["estado"].startswith("ROJO")
    exc = [{"vol": "Lascar", "dt": f["dt"], "sensor": "MODIS_AQUA", "empate_argsort": "pixeles 12 y 13"} for f in fs[:3]]
    assert L.c_k(fs, exc)["estado"].startswith("ROJO")            # queda una sin nombrar
    exc.append({"vol": "Lascar", "dt": fs[3]["dt"], "sensor": "MODIS_AQUA", "empate_argsort": "x"})
    assert L.c_k(fs, exc)["estado"].startswith("ROJO")            # cuatro superan el tope de 3 (R-15)
    assert L.c_k([f for f in fs if not f.get("en_kgemelo")])["estado"].startswith("ROJO")


def test_nulo_runner_b_cero_y_puede_fallar(R):
    fs = _ck_filas(8)
    assert L.nulo_runner(R, fs)["estado"] == "OK"
    sin_mag = [f for f in fs if f["lab"] == "neg_limpio"]
    assert L.nulo_runner(R, sin_mag)["estado"].startswith("ROJO")   # sin pares el nulo no puede fallar: no sirve
    for f in fs[:6]:
        f["_t"]["KG"] = {"pub": 0, "mag": 0.0}
    assert L.nulo_runner(R, fs)["estado"].startswith("ROJO")


def test_candado_ve_un_archivo_cambiado(tmp_path):
    (tmp_path / "a.py").write_bytes(b"x = 1\r\n")
    ok = {"a.py": L.sha256_lf(tmp_path / "a.py")}
    assert L.candado(ok, tmp_path, requeridos=())["estado"] == "OK"
    (tmp_path / "a.py").write_bytes(b"x = 2\n")
    assert L.candado(ok, tmp_path, requeridos=())["estado"].startswith("ROJO")
    assert L.candado(None)["estado"].startswith("ROJO")


def test_las_reglas_se_cargan_solo_si_son_las_selladas(tmp_path):
    with pytest.raises(SystemExit):
        L.Reglas({"scripts/evaluador_comun.py": "0" * 64})


def test_nulo_del_lector_cae_si_el_predicado_no_publica_lo_inyectado(R):
    fs = poblacion()
    r = L.nulo_lector(R, fs, "MODIS", "V", lambda casos: [(0, 0.0)] * len(casos))
    assert r["estado"].startswith("ROJO") and r["contador"]["despues"] == r["contador"]["antes"]
    assert L.nulo_lector(R, fs, "MODIS", "V", pred)["estado"] == "OK"


# ------------------------------------------------------------------------------------------- de punta a punta
def _rec(dts, sensor, summit, vrp, via=None, z=25.0):
    r = {"datetime_utc": dts, "sensor": sensor, "sensor_zenith_deg": z,
         "distance_class": "summit" if summit else None, "vrp_mw": vrp,
         "primary_cluster": {"vrp_mw": vrp, "centroid_dist_km": 1.0, "n_pixels": 1} if vrp else None,
         "hotspot_dist_km": 1.0 if vrp else None,
         "anomaly_pixels": [{"dist_km": 0.8, "lat": 0, "lon": 0, "vrp_mw": vrp, "bt_k": 300}] if vrp else []}
    if via is not None:
        r["via_codigo_mirova"] = via
    return r


def test_armar_pasadas_tupungatito_tramos_y_estados(tmp_path):
    k = {("Tupungatito", "VIIRS_NOAA20", "2026-02-20 05:00"): _rec("2026-02-20 05:00", "VIIRS_NOAA20", 0, 0),
         ("Tupungatito", "VIIRS_NOAA20", "2026-02-24 05:00"): _rec("2026-02-24 05:00", "VIIRS_NOAA20", 0, 0),
         ("Lascar", "MODIS_AQUA", "2026-03-10 05:00"): _rec("2026-03-10 05:00", "MODIS_AQUA", 0, 0),
         ("Lascar", "VIIRS_NOAA20", "2026-10-12 05:00"): _rec("2026-10-12 05:00", "VIIRS_NOAA20", 0, 0),
         ("Lascar", "MODIS_AQUA", "2026-01-15 05:00"): _rec("2026-01-15 05:00", "MODIS_AQUA", 0, 0),
         ("Lascar", "VIIRS_NOAA20_750", "2026-02-10 05:00"): _rec("2026-02-10 05:00", "VIIRS_NOAA20_750", 0, 0)}
    via = {k_: dict(v, via_codigo_mirova=True) for k_, v in k.items() if k_[0] == "Tupungatito"}
    fs = L.armar_pasadas(via, k)
    clave = {(f["vol"], f["dt"]): f for f in fs}
    assert ("Tupungatito", "2026-02-20 05:00") not in clave                    # antes del 02-23
    assert clave[("Tupungatito", "2026-02-24 05:00")]["estado"] == "ok"
    assert clave[("Lascar", "2026-03-10 05:00")]["tramo"] == "F26-M3"
    assert ("Lascar", "2026-10-12 05:00") not in clave                         # DM sin el 12 en VIIRS
    assert ("Lascar", "2026-01-15 05:00") not in clave                         # enero fuera (A119)
    assert clave[("Lascar", "2026-02-10 05:00")]["estado"] == "sin_dato_cobertura"


CAB = ["Volcan", "Fecha_Satelite_UTC", "Sensor", "Distancia_km", "Tipo_Registro", "VRP_MW", "Clasificacion Mirova",
       "Ultima_Actualizacion", "Nota_Validacion"]


def _csv(ruta, filas):
    with open(ruta, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(CAB)
        for x in filas:
            w.writerow(x)


def test_etiquetar_decide_la_tabla_y_la_union_informa(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import banco_paridad as bp
    from referencia_mirova_unificada import cargar_referencia_unificada
    _csv(tmp_path / "cons.csv", [["Lascar", "2026-02-10 05:00:30", "VIIRS375", "1.0", "ALERTA_TERMICA", "2.5", "MODERATE",
                                  "2026-02-10 06:00", ""],
                                 ["Lascar", "2026-02-11 05:00:10", "VIIRS375", "0", "RUTINA", "0", "", "2026-02-11", ""]])
    _csv(tmp_path / "ocr.csv", [["Lascar", "2026-02-12 05:00:00", "VIIRS375", "0", "ALERTA_TERMICA_OCR", "1.8", "LOW",
                                 "2026-02-12 06:00", "dist 1.2 km"]])
    ref = cargar_referencia_unificada(tmp_path / "cons.csv", tmp_path / "ocr.csv", respaldo_path=None,
                                      historico_path=None)
    fs = [{"vol": "Lascar", "b": "VIIRS375", "dt": d, "noche": d[:10]} for d in
          ("2026-02-10 05:00", "2026-02-11 05:00", "2026-02-12 05:00")]
    L.etiquetar_tabla(fs, ref, bp._coords_por_volcan())
    assert [f["lab"] for f in fs] == ["protegida", "neg_limpio", "sin_info"]
    assert fs[2].get("lab_union") == "protegida" and fs[0].get("lab_union") is None
    assert fs[0]["vrp_mirova"] == 2.5


def test_main_de_punta_a_punta_con_predicado_sintetico(tmp_path, monkeypatch, R, capsys):
    import referencia_mirova_unificada as RMU
    orig = RMU.cargar_referencia_unificada
    monkeypatch.setattr(RMU, "cargar_referencia_unificada",
                        lambda c, o: orig(c, o, respaldo_path=None, historico_path=None))
    via, k = tmp_path / "via", tmp_path / "k"
    via.mkdir()
    k.mkdir()
    rv, rk = [], []
    for d in range(1, 28):
        dts = f"2026-02-{d:02d} 05:00"
        rk.append(_rec(dts, "MODIS_AQUA", 1, 0.4 if d <= 8 else 0))
        rv.append(_rec(dts, "MODIS_AQUA", 1, 0, via=True))
    (via / "Lascar.json").write_text(json.dumps({"volcano": "Lascar", "records": rv}), encoding="utf-8")
    (k / "Lascar.json").write_text(json.dumps({"volcano": "Lascar", "records": rk}), encoding="utf-8")
    _csv(tmp_path / "cons.csv", [["Lascar", f"2026-02-{d:02d} 05:00:00", "MODIS", "0", "RUTINA", "0", "", "x", ""]
                                 for d in range(1, 28)])
    _csv(tmp_path / "ocr.csv", [])
    sal = tmp_path / "out.json"
    cod = L.main(["--via", str(via), "--k", str(k), "--cons", str(tmp_path / "cons.csv"), "--ocr",
                  str(tmp_path / "ocr.csv"), "--v750a-sellado", "no", "--ensayo", "--salida", str(sal)],
                 predicado=pred, reglas=R)
    out = json.loads(sal.read_text(encoding="utf-8"))
    m = out["sensores"]["MODIS"]
    assert m["etiquetas"].get("neg_limpio") == 27
    assert m["regla"]["B"] == 8 and m["regla"]["neto"] == -8          # 8 negativos que K publica y la vía calla
    assert m["fila"] == 1 and "c_k" in m["motivos"]                   # sin K-gemelo, C-K en rojo: no se lee
    assert cod == 3 and out["ensayo"] is True
    # VPR940-15: con --ensayo cada línea de veredicto lo dice
    lineas = [x for x in capsys.readouterr().out.splitlines() if ": fila " in x]
    assert len(lineas) == 3 and all(x.startswith("ENSAYO (NO DECIDE) ") for x in lineas), lineas


# ------------------------------------------------------------------------------------------- R25 contra el OSF
def _osf(vol, b, dts, vrp_mw, clase=1, dist=1.0, inner=5.0, satzen=25.0, noche=True):
    from datetime import datetime, timezone
    return {"vol": vol, "b": b, "dt": datetime.strptime(dts, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc),
            "vrp_w": vrp_mw * 1e6, "class": clase, "noche": noche, "dist_crater_km": dist, "inner": inner,
            "satzen": satzen}


def _r25(vol, dts, k, v, estado="ok", z=25.0, b="VIIRS375", sensor="VIIRS_NOAA20"):
    f = F(vol, dts[:10], "sin_info", k, v, sensor=sensor, b=b, tramo="R25", hora=dts[11:], z=z)
    f["estado"], f["_evaluable"] = estado, estado == "ok"
    return f


def test_p1_osf_candidata_si_la_via_pierde_lo_que_k_publica():
    fs = [_r25("Lascar", "2025-06-01 05:00", 1, 1), _r25("Lascar", "2025-06-02 05:00", 1, 0),
          _r25("PlanchonPeteroa", "2025-06-03 05:00", 1, 0, estado="via_sin_marca:sin_grilla"),
          _r25("Lascar", "2025-06-04 05:00", 0, 0)]
    osf = [_osf("Lascar", "VIIRS375", "2025-06-01 05:01", 3.0), _osf("Lascar", "VIIRS375", "2025-06-02 05:00", 2.0),
           _osf("PlanchonPeteroa", "VIIRS375", "2025-06-03 05:00", 1.5),
           _osf("Lascar", "VIIRS375", "2025-06-04 05:00", 1.2),
           _osf("Lascar", "VIIRS375", "2025-06-05 05:00", 1.1),                     # sin pasada nuestra
           _osf("Lascar", "VIIRS375", "2025-06-06 05:00", 9.0, dist=12.0),          # lejana: no es protegida
           _osf("Lascar", "VIIRS375", "2025-06-07 05:00", 9.0, clase=0),            # ambigua
           _osf("Lascar", "VIIRS375", "2025-06-08 13:00", 9.0, noche=False)]        # diurna: fuera
    r = L.p1_osf(fs, osf)
    s = r["por_sensor"]["VIIRS375"]
    assert s["protegidas"] == 5 and s["pub_via"] == 1
    assert [c[2] for c in s["candidatas"]] == ["via_no_publica", "via_sin_marca:sin_grilla"]
    assert s["ninguno"] == [("Lascar", "2025-06-04 05:00")] and s["sin_record"] == [("Lascar", "2025-06-05 05:00")]
    assert len(r["lejanas"]) == 1 and len(r["ambiguas"]) == 1
    assert r["c_pareo"] == "OK" and r["c_cenit"] == "OK"
    assert s["razon_cota_mediana"]["n"] == 1


def test_p1_osf_controles_de_pareo_y_cenit_pueden_caer():
    fs = [_r25("Lascar", "2025-06-01 05:00", 1, 1, z=40.0), _r25("Lascar", "2025-06-01 05:01", 1, 1)]
    r = L.p1_osf(fs, [_osf("Lascar", "VIIRS375", "2025-06-01 05:00", 3.0, satzen=25.0)])
    assert r["c_pareo"].startswith("ROJO") and r["c_cenit"].startswith("ROJO")


def test_p1_osf_candidata_lleva_el_sensor_a_nicolas(R):
    r25 = [_r25("Lascar", "2025-06-02 05:00", 1, 0)]
    osf_res = L.p1_osf(r25, [_osf("Lascar", "VIIRS375", "2025-06-02 05:00", 2.0)])
    r = L.leer_sensor(R, v375(), "VIIRS375", COMUNES, pred, False, "def", osf_res=osf_res, filas_r25=r25)
    assert r["fila"] == 4 and "candidatas_osf" in r["motivos"]


def test_leer_osf_lee_el_formato_del_osf(tmp_path):
    import yaml
    cab = ["Volc_Name", "Volc_LAT", "Volc_LON", "timeUTC", "Resolution", "VRP", "class", "LAT", "LON", "SatZen",
           "Dayflag", "Satellite", "Max_Dist", "Npix"]
    with open(tmp_path / "osf.csv", "w", encoding="latin-1", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cab)
        w.writerow(["Lascar", "-23.37", "-67.73", "01/06/2025 05:00", "375", "2.0e6", "1", "-23.37", "-67.73", "20", "0",
                    "3", "400", "2"])
        w.writerow(["Lascar", "-23.37", "-67.73", "01/06/2026 05:00", "375", "2.0e6", "1", "-23.37", "-67.73", "20", "0",
                    "3", "400", "2"])                                                # fuera de R25
        w.writerow(["Otro", "10.0", "10.0", "01/06/2025 05:00", "375", "2.0e6", "1", "10", "10", "20", "0", "3", "0", "1"])
    volc = {v["name"]: v for v in yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    o = L.leer_osf(tmp_path / "osf.csv", volc, lambda *a: True)
    assert len(o) == 1 and o[0]["vol"] == "Lascar" and o[0]["b"] == "VIIRS375" and o[0]["vrp_w"] == 2.0e6
    assert o[0]["dist_crater_km"] < 1.5 and o[0]["inner"] == float(volc["Lascar"]["inner_radius_km"])


@pytest.mark.skipif(__import__("shutil").which("node") is None, reason="sin node")
def test_el_predicado_real_del_tablero_publica_el_cumulo_inyectado_y_calla_el_vacio(R):
    """El contador del nulo del lector se apoya en que el predicado de frontend/index.html (node, A97) publique el
    cúmulo inyectado; y un record sin cúmulo no se publica."""
    vacio = {"sensor": "VIIRS_NOAA20", "vrp_mw": 0.0, "primary_cluster": None, "distance_class": None}
    res = R.F4.predicado_node([(L.inyectar_cumulo({"sensor": "VIIRS_NOAA20"}), 5.0), (vacio, 5.0)])
    assert res[0][0] == 1 and res[0][1] > 0 and res[1][0] == 0


@pytest.mark.parametrize("copia,tag,original", [
    ("experiments/_s172_retro_paquete/reglas/evaluar_f4.py", "s170-modd-f4-candado", "experiments/_s166_modd_f4/evaluar_f4.py"),
    ("experiments/_s172_retro_paquete/reglas/leer_posicion_v375e.py", "s170-v375e-lector",
     "experiments/_s162_v375/e_adenda2/leer_posicion_v375e.py"),
])
def test_las_copias_de_las_reglas_son_los_blobs_de_sus_tags(copia, tag, original):
    import hashlib
    import subprocess
    r = subprocess.run(["git", "rev-parse", f"{tag}:{original}"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        pytest.skip(f"el tag {tag} no está en este clon (checkout superficial)")
    b = (ROOT / copia).read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest() == r.stdout.strip()


def test_v750_sin_sello_la_regla_misma_pone_el_techo(R):
    """M9 sobrevivió a la primera ronda de mutaciones: el techo de R-12 estaba puesto dos veces (en la regla y en las
    condiciones de la fila 4) y la batería sólo miraba el resultado final. Se fija cada una por separado."""
    fs = _con_roi(v750(), "def")
    assert L.regla_v750(R, fs, "V", sellado=False)["_fila_regla"] == 4
    assert L.regla_v750(R, fs, "V", sellado=True)["_fila_regla"] != 4 or L.regla_v750(R, fs, "V", True)["p2"] == "BLOQUEA"



# ------------------------------------------------------------------------------------------- arreglos de VPR940
def test_k_de_disco_con_la_marca_de_la_via_es_rojo_en_todas_las_ventanas():
    """VPR940-02 (grav. 3): un record de K de disco con via_codigo_mirova True no es K. Se marca la pasada y el
    control c_k_puro queda en rojo, también en R25, que no tiene C-K."""
    for dts in ("2026-02-10 05:00", "2025-06-10 05:00", "2026-10-05 05:00"):
        key = ("Lascar", "MODIS_AQUA", dts)
        k = {key: dict(_rec(dts, "MODIS_AQUA", 1, 0.4), via_codigo_mirova=True)}
        via = {key: _rec(dts, "MODIS_AQUA", 1, 0.4, via=True)}
        fs = L.armar_pasadas(via, k)
        assert fs[0]["estado"] == "k_con_marca:True", (dts, fs[0]["estado"])
        assert L.c_k_puro(fs)["estado"].startswith("ROJO")
    for marca in (None, False, "sin_grilla"):
        key = ("Lascar", "MODIS_AQUA", "2026-02-10 05:00")
        k = {key: _rec("2026-02-10 05:00", "MODIS_AQUA", 1, 0.4, via=marca)}
        fs = L.armar_pasadas({key: _rec("2026-02-10 05:00", "MODIS_AQUA", 1, 0.4, via=True)}, k)
        assert L.c_k_puro(fs)["estado"] == "OK", marca


def test_k_puro_en_rojo_lleva_el_sensor_a_la_fila_1(R):
    fs = poblacion()
    fs[0]["estado"] = "k_con_marca:True"
    com = dict(COMUNES, c_k_puro=L.c_k_puro(fs))
    r = L.leer_sensor(R, fs, "MODIS", com, pred, False, "def")
    assert r["fila"] == 1 and "c_k_puro" in r["motivos"]


def _kg(vol, dia, tramo, con_kg=True, hora="05:00"):
    f = F(vol, dia, "neg_limpio", 0, 0, tramo=tramo, hora=hora)
    f["k_rec"] = {"primary_cluster": None}
    if con_kg:
        f["en_kgemelo"] = True
        f["kg_rec"] = {"primary_cluster": None}
        f["_t"]["KG"] = dict(f["_t"]["K"])
    return f


def _kg_d3():
    """K de disco de tres volcanes en DM y en F26, con el K-gemelo de D3: DM entero, Láscar y Chillán en F26
    enteros, tres días de F26 de Isluga."""
    fs = []
    for v in ("Lascar", "NevadosDeChillan", "Isluga"):
        fs += [_kg(v, f"2026-10-{d:02d}", "DM") for d in (1, 2, 3)]
        for i, d in enumerate(dias(6)):
            fs.append(_kg(v, d, "F26-M", con_kg=v != "Isluga" or i < 3))
    return fs


def test_c_k_exige_la_cobertura_del_k_gemelo_de_d3():
    """VPR940-03: con un K-gemelo de una pasada C-K daba OK. Ahora tiene que cubrir lo que manda D3."""
    fs = _kg_d3()
    assert L.c_k(fs)["estado"] == "OK", L.c_k(fs)
    una = [dict(f, en_kgemelo=False, kg_rec=None) if i else f for i, f in enumerate(fs)]
    assert L.c_k(una)["estado"].startswith("ROJO")
    for vol, tramo in (("Isluga", "DM"), ("Lascar", "F26-M")):
        sin = copy.deepcopy(fs)
        f = next(x for x in sin if x["vol"] == vol and x["tramo"] == tramo and x["en_kgemelo"])
        f["en_kgemelo"], f["kg_rec"] = False, None
        assert L.c_k(sin)["estado"].startswith("ROJO"), (vol, tramo)
    dos = copy.deepcopy(fs)
    f = next(x for x in dos if x["vol"] == "Isluga" and x["tramo"] == "F26-M" and x["en_kgemelo"])
    f["en_kgemelo"], f["kg_rec"] = False, None
    assert L.c_k(dos)["estado"].startswith("ROJO")                   # Isluga con 2 días de F26, no 3


def test_nulo_runner_descuenta_las_excepciones_nombradas(R):
    """VPR940-04: B = 0 salvo las pasadas nombradas de C-K."""
    fs = _ck_filas(8)
    f = next(x for x in fs if x["lab"] == "neg_limpio")
    f["_t"]["KG"] = {"pub": 0, "mag": 0.0}
    assert L.nulo_runner(R, fs)["estado"].startswith("ROJO")
    exc = [{"vol": f["vol"], "dt": f["dt"], "sensor": "MODIS_AQUA", "empate_argsort": "pixeles 4 y 5"}]
    assert L.nulo_runner(R, fs, exc)["estado"] == "OK"
    exc[0]["empate_argsort"] = ""                                     # sin el empate escrito no cuenta
    assert L.nulo_runner(R, fs, exc)["estado"].startswith("ROJO")


def test_placebo_mira_p1_y_p2_y_acepta_solo_las_dos_causas_de_l7(R):
    """VPR940-05: K×1,2 sin discordancias de publicación salvo las de L7 (t_max de K bajo 278,15 K, o la magnitud
    que cruza el tope de 50.000 MW del tablero)."""
    fs = poblacion()
    assert L.c_placebo(R, fs, "MODIS")["estado"] == "OK"
    d = F("Lascar", "2026-02-22", "neg_limpio", 1, 0, mk=0.3, hora="03:00")
    d["_t"]["placebo"] = {"pub": 0, "mag": 0.0}
    d["k_rec"] = {"t_max_k": 300.0}
    r = L.c_placebo(R, fs + [d], "MODIS")
    assert r["estado"].startswith("ROJO") and r["discordancias_sin_explicar"]
    d["k_rec"] = {"t_max_k": 275.0}
    assert L.c_placebo(R, fs + [d], "MODIS")["estado"] == "OK"
    d["k_rec"] = {"t_max_k": 300.0}
    d["_t"]["K"]["mag"] = 45000.0                                     # ×1,2 = 54.000 MW: cruza el tope
    assert L.c_placebo(R, fs + [d], "MODIS")["estado"] == "OK"
    p = F("Lascar", "2026-02-23", "protegida", 1, 1, hora="03:00")
    p["_t"]["placebo"] = {"pub": 0, "mag": 0.0}
    p["k_rec"] = {"t_max_k": 300.0}
    assert L.c_placebo(R, fs + [p], "MODIS")["estado"].startswith("ROJO")   # P1 también


# Los tags de este ejemplo son nombres de prueba, no los de origen reales (pendientes: PENDIENTES_MONTAJE del lector).
MONTAJE_OK = {"estado": "OK", "tags": {"MOD-D fase 4": "tag-modd", "V375-E": "tag-v375e", "V750-B": "tag-v750b"},
              "diff_listado": "git diff s170-modd-f4-candado s172-retro-d2 -- pipeline/mirova_v750_codigo.py: vacío",
              "diferencias": [{"pasada": "Lascar|MODIS_AQUA|2026-10-05 05:00", "explicada_por": "hunk",
                               "hunk": "@@ -10,3 +10,4 @@ ..."},
                              {"pasada": "Isluga|VIIRS_NOAA20|2026-10-06 05:12", "explicada_por": "otro_granulo"}]}


def test_c_montaje_se_valida_y_no_basta_un_estado_ok():
    """VPR940-06: el JSON de --montaje tiene que traer los tags, el diff listado y cada diferencia explicada por un
    hunk (con el hunk) o por otro_granulo (§6, VPR2-09)."""
    assert L.validar_montaje(copy.deepcopy(MONTAJE_OK))["estado"] == "OK"
    assert L.validar_montaje(None)["estado"].startswith("ROJO")
    assert L.validar_montaje({"estado": "OK"})["estado"].startswith("ROJO")
    for mal in ({"explicada_por": "hunk", "hunk": ""}, {"explicada_por": "parecido"}, {}):
        m = copy.deepcopy(MONTAJE_OK)
        m["diferencias"].append(dict({"pasada": "Llaima|MODIS_TERRA|2026-10-07 02:30"}, **mal))
        assert L.validar_montaje(m)["estado"].startswith("ROJO"), mal
    m = copy.deepcopy(MONTAJE_OK)
    m["estado"] = "ROJO: algo"
    assert L.validar_montaje(m)["estado"].startswith("ROJO")
    m = copy.deepcopy(MONTAJE_OK)
    m["tags"] = []
    assert L.validar_montaje(m)["estado"].startswith("ROJO")


def test_c_cobertura_en_r25_por_clase_del_osf(R):
    """VPR940-09: en R25 el 10 % SIN DATO por clase se mide con la clase del OSF."""
    r25 = [_r25("Lascar", f"2025-06-{d:02d} 05:00", 1, 1) for d in range(1, 11)]
    osf = [_osf("Lascar", "VIIRS375", f"2025-06-{d:02d} 05:00", 2.0) for d in range(1, 11)]
    L.p1_osf(r25, osf)
    assert L.c_cobertura(r25, clave="lab_osf", clases=("protegida_osf",))["estado"] == "OK"
    for f in r25[:2]:
        f["estado"], f["_evaluable"] = "sin_dato_cobertura", False
    assert L.c_cobertura(r25, clave="lab_osf", clases=("protegida_osf",))["estado"].startswith("ROJO")
    osf_res = L.p1_osf(r25, osf)
    r = L.leer_sensor(R, v375(), "VIIRS375", COMUNES, pred, False, "def", osf_res=osf_res, filas_r25=r25)
    assert r["fila"] == 1 and "c_cobertura_r25" in r["motivos"]


def test_el_sorteo_de_etiquetas_baraja_dentro_de_cada_estrato(R):
    """VPR940-11 (§7, GUIA §3b fila 7): el sorteo de etiquetas K contra K baraja dentro de volcán × tramo de cenit y
    dice qué fracción de barajados cumple GANA o EMPATE por azar."""
    import numpy as np
    fs = poblacion()
    for f in fs:                         # el cenit por el día: cada estrato mezcla protegidas y alertas bajo 1 MW
        f["z"] = 15.0 if int(f["dt"][8:10]) % 2 else 45.0
    nuevas = L.barajar_en_estratos(fs, np.random.default_rng(172))
    estrato = lambda f: (f["vol"], int(f["z"] // 10))                                      # noqa: E731
    antes, despues = collections.defaultdict(list), collections.defaultdict(list)
    for f, n in zip(_ev_(fs), nuevas):
        antes[estrato(f)].append(f["lab"])
        despues[estrato(f)].append(n["lab"])
    assert all(sorted(antes[k]) == sorted(despues[k]) for k in antes)
    assert any(a["lab"] != n["lab"] for a, n in zip(_ev_(fs), nuevas))
    s = L.sorteo_etiquetas(R, fs, n=20)
    assert s["n"] == 20 and abs(s["gana_o_empate"] + s["sin_sustrato"] + s["otros"] - 1.0) < 1e-9
    assert s["brazos"] == ("K", "K")                                   # sin K-gemelo, K contra K


def _ev_(fs):
    return [f for f in fs if f.get("_evaluable")]


# ------------------------------------------------------------------------------------------- seguimiento S173
# Lecturas aprobadas por Nicolás (VPR940-01, 07, 10) y hallazgos del segundo verificador de #940
# (experiments/_s173_aud/ver940b/hallazgos.csv en loop/activo, commit 1f32ef1d1).
class _Proxy:
    """Delegación con reemplazos: deja fijar una pieza de una regla sellada sin tocar el módulo."""

    def __init__(self, base, **over):
        self._b = base
        self.__dict__.update(over)

    def __getattr__(self, n):
        return getattr(self._b, n)


def test_v750_separa_es_control_del_placebo_no_parte_de_m(R):
    """VPR940-01 (aprobado): «el comparador separa la vía de K×1,2» es un CONTROL. Si falla, la lectura es
    INDECIDIBLE (fila 1), no PEOR QUE K. Qué es separar lo fija V750-A al sellarse: va como parámetro."""
    fs = _con_roi(v750(), "def")
    no_separa = lambda R_, filas, b: False                                        # noqa: E731
    si_separa = lambda R_, filas, b: True                                         # noqa: E731
    assert L.regla_v750(R, fs, "V", sellado=True)["_fila_regla"] != 3            # M sólo mira la banda
    r = leer(R, copy.deepcopy(fs), "VIIRS750", sellado=True, separa_v750=no_separa)
    assert r["fila"] == 1 and "c_placebo" in r["motivos"], (r["fila"], r["motivos"])
    r = leer(R, copy.deepcopy(fs), "VIIRS750", sellado=True)                     # sellado y sin definición: rojo
    assert r["fila"] == 1 and "c_placebo" in r["motivos"]
    r = leer(R, copy.deepcopy(fs), "VIIRS750", sellado=True, separa_v750=si_separa)
    assert r["controles"]["c_placebo"]["estado"] == "OK" and r["fila"] != 1, r["motivos"]
    r = leer(R, copy.deepcopy(fs), "VIIRS750")                                   # sin sello: la fila 4 lo cubre
    assert r["controles"]["c_placebo"]["estado"] == "OK" and r["fila"] == 4
    assert L.DEFINICIONES_SEPARA_V750 and all(n.startswith("PROVISIONAL") for n in L.DEFINICIONES_SEPARA_V750)


def test_v375_p2_lejana_pierde_y_enciende_de_mas_son_fila_3(R):
    """VPR940-07 (aprobado): se mantiene L1, P2-L PIERDE y el silencio ENCIENDE DE MAS van a la fila 3."""
    fs = v375()
    pierde = _Proxy(R, LP=_Proxy(R.LP, p2_con=lambda *a, **k: {"veredicto": "PIERDE"}))
    assert L.regla_v375(pierde, fs, "V-cercano")["_fila_regla"] == 3
    enciende = _Proxy(R, E=_Proxy(R.E, lecturas=lambda *a, **k: {"silencio": {"veredicto": "ENCIENDE DE MAS"},
                                                                 "P1b": {"baja": 0}}))
    assert L.regla_v375(enciende, fs, "V-cercano")["_fila_regla"] == 3
    assert L.regla_v375(R, fs, "V-cercano")["_fila_regla"] == 6                 # control: sin el reemplazo, fila 6


def test_defecto_del_lector_osf_es_fila_1(R):
    """VPR940-10 (aprobado): la vía publica una protegida OSF que K no publica; no puede ocurrir, es un defecto del
    lector y manda la lectura a la fila 1, no a la 4."""
    r25 = [_r25("Lascar", "2025-06-02 05:00", 0, 1)]
    osf_res = L.p1_osf(r25, [_osf("Lascar", "VIIRS375", "2025-06-02 05:00", 2.0)])
    assert osf_res["por_sensor"]["VIIRS375"]["defecto"]
    r = L.leer_sensor(R, v375(), "VIIRS375", COMUNES, pred, False, "def", osf_res=osf_res, filas_r25=r25)
    assert r["fila"] == 1 and "c_defecto_lector_osf" in r["motivos"], (r["fila"], r["motivos"])
    sano = [_r25("Lascar", "2025-06-02 05:00", 1, 1)]
    osf_ok = L.p1_osf(sano, [_osf("Lascar", "VIIRS375", "2025-06-02 05:00", 2.0)])
    r = L.leer_sensor(R, v375(), "VIIRS375", COMUNES, pred, False, "def", osf_res=osf_ok, filas_r25=sano)
    assert r["controles"]["c_defecto_lector_osf"]["estado"] == "OK" and r["fila"] == 6


def test_excepcion_de_c_k_mal_formada_es_rojo_y_no_cae(R):
    """VPR940b-03: una excepción sin vol, dt o sensor deja C-K en rojo (fila 1), no una traza."""
    fs = _ck_filas()
    for mala in ({"sensor": "MODIS_AQUA", "empate_argsort": "x"}, {"vol": "Lascar", "empate_argsort": "x"},
                 {"vol": "Lascar", "dt": fs[0]["dt"], "empate_argsort": "x"}, "texto suelto"):
        assert L.c_k(fs, [mala])["estado"].startswith("ROJO"), mala
        L.nulo_runner(R, fs, [mala])                                              # no cae
    buena = {"vol": "Lascar", "dt": fs[0]["dt"], "sensor": "MODIS_AQUA", "empate_argsort": "x"}
    assert L.c_k(fs, [buena])["estado"] == "OK"


def test_c_montaje_exige_los_tres_origenes_y_pasadas_de_dm():
    """VPR940b-06: los tags vienen por origen (MOD-D fase 4, V375-E, V750-B) y cada pasada explicada es de DM."""
    m = copy.deepcopy(MONTAJE_OK)
    assert L.validar_montaje(m)["estado"] == "OK"
    m["tags"] = {"MOD-D fase 4": "x", "V375-E": "y"}
    assert L.validar_montaje(m)["estado"].startswith("ROJO")
    m = copy.deepcopy(MONTAJE_OK)
    m["tags"] = list(m["tags"].values())
    assert L.validar_montaje(m)["estado"].startswith("ROJO")
    m = copy.deepcopy(MONTAJE_OK)
    m["diferencias"].append({"pasada": "Lascar|MODIS_AQUA|2026-02-10 05:00", "explicada_por": "otro_granulo"})
    assert L.validar_montaje(m)["estado"].startswith("ROJO")                     # febrero no es DM


def test_cobertura_kgemelo_ve_volcanes_sin_f26_y_lista_sobras():
    """VPR940b-07: un volcán Tier A sin ninguna pasada de K en F26 no cumple D3 (rojo); las pasadas que sólo trae
    el K-gemelo se listan."""
    fs = _kg_d3()
    assert L.c_k(fs)["estado"] == "OK"
    r = L.c_k(fs, tier_a=L.TIER_A)
    assert r["estado"].startswith("ROJO")
    falt = r["cobertura_kgemelo"]["volcanes_sin_f26_en_k"]
    assert "Villarrica" in falt and "Lascar" not in falt and len(falt) == 8
    assert L.c_k(fs, tier_a=("Lascar", "NevadosDeChillan", "Isluga"))["estado"] == "OK"
    k = {("Lascar", "MODIS_AQUA", "2026-02-10 05:00"): {}}
    kg = {("Lascar", "MODIS_AQUA", "2026-02-10 05:00"): {}, ("Lascar", "MODIS_AQUA", "2026-02-11 05:00"): {},
          ("Lascar", "MODIS_AQUA", "2026-01-11 05:00"): {}}
    assert L.sobras_kgemelo(kg, k) == [("Lascar", "MODIS_AQUA", "2026-02-11 05:00")]   # enero fuera de tramo
    assert L.c_k(fs, sobras_kg=[("Lascar", "MODIS_AQUA", "2026-02-11 05:00")])["sobras_kgemelo"]


def test_tier_a_del_lector_es_el_de_plan_trozos():
    spec = importlib.util.spec_from_file_location("plan_trozos_t", EXP / "plan_trozos.py")
    pt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pt)
    assert set(L.TIER_A) == set(pt.TIER_A) and len(L.TIER_A) == 11


def test_sorteo_de_etiquetas_dice_que_no_tiene_poder_con_brazos_identicos(R):
    """VPR940b-01: con K contra K el sorteo da SIN SUSTRATO siempre; el informe tiene que decirlo. Control: con un
    K-gemelo distinto de K el mismo cálculo puede dar otra cosa."""
    fs = poblacion()
    s = L.sorteo_etiquetas(R, fs, n=10)
    assert s["poder"].startswith("SIN PODER") and s["sin_sustrato"] == 1.0
    for f in fs:
        f["_t"]["KG"] = dict(f["_t"]["V"])                    # gemelo distinto: B = 8 en los negativos
    s = L.sorteo_etiquetas(R, fs, n=10)
    assert s["brazos"] == ("KG", "K") and not s["poder"].startswith("SIN PODER") and s["sin_sustrato"] < 1.0


def test_candado_exige_los_archivos_del_manifiesto(tmp_path):
    """§11: un manifiesto vacío o al que le falta un archivo requerido no es un candado."""
    assert L.candado({})["estado"].startswith("ROJO")
    (tmp_path / "a.py").write_bytes(b"x = 1\n")
    m = {"a.py": L.sha256_lf(tmp_path / "a.py")}
    assert L.candado(m, tmp_path, requeridos=("a.py", "b.py"))["estado"].startswith("ROJO")
    assert L.candado(m, tmp_path, requeridos=("a.py",))["estado"] == "OK"
    assert "experiments/_s172_retro_paquete/leer_retro.py" in L.REQUERIDOS_MANIFIESTO
    assert "frontend/index.html" in L.REQUERIDOS_MANIFIESTO


def test_main_avisa_r25_sin_osf_y_el_poder_del_sorteo(tmp_path, monkeypatch, R, capsys):
    """VPR940b-08 y 01: sin --osf, R25 no se lee y se dice; el sorteo sin poder se imprime."""
    test_main_de_punta_a_punta_con_predicado_sintetico(tmp_path, monkeypatch, R, capsys)
    out = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    assert any("R25 sin OSF" in a for a in out["avisos"]), out.get("avisos")
    assert out["sensores"]["MODIS"]["otros_brazos"]["sorteo_etiquetas"]["poder"].startswith("SIN PODER")


# ------------------------------------------------------------------------------------------- verificador de #946
# experiments/_s173_aud/ver946/ en loop/activo (MERGEABLE CON CAMBIOS).
def test_c_cenit_del_osf_en_rojo_lleva_a_la_fila_1(R):
    """VPR946-01: §8.1 fila 1 (algún control del §6 en rojo). C-cenit de R25 se calculaba y no llegaba al veredicto."""
    r25 = [_r25("Lascar", "2025-06-02 05:00", 1, 1, z=40.0)]                     # SatZen 25: 15° de diferencia
    osf_res = L.p1_osf(r25, [_osf("Lascar", "VIIRS375", "2025-06-02 05:00", 2.0, satzen=25.0)])
    assert osf_res["c_cenit"].startswith("ROJO")
    r = L.leer_sensor(R, v375(), "VIIRS375", COMUNES, pred, False, "def", osf_res=osf_res, filas_r25=r25)
    assert r["fila"] == 1 and "c_cenit_osf" in r["motivos"], (r["fila"], r["motivos"])
    ok = [_r25("Lascar", "2025-06-02 05:00", 1, 1, z=26.0)]                       # control: 1° de diferencia
    osf_ok = L.p1_osf(ok, [_osf("Lascar", "VIIRS375", "2025-06-02 05:00", 2.0, satzen=25.0)])
    r = L.leer_sensor(R, v375(), "VIIRS375", COMUNES, pred, False, "def", osf_res=osf_ok, filas_r25=ok)
    assert r["controles"]["c_cenit_osf"]["estado"] == "OK" and r["fila"] == 6
    sin_pares = L.p1_osf([], [_osf("Lascar", "VIIRS375", "2025-06-02 05:00", 2.0)])
    assert sin_pares["c_cenit"].startswith("ROJO")                                # all([]) no es un OK


def test_controles_de_cenit_en_rojo_llevan_a_la_fila_1(R, monkeypatch):
    """VPR946-01: los controles de cenit del §6 (V375-E §4) en rojo dejan el sensor en la fila 1; SIN SUSTRATO no."""
    monkeypatch.setattr(L, "controles_cenit", lambda *a, **k: {"estado": "ROJO"})
    r = leer(R, poblacion(), "MODIS")
    assert r["fila"] == 1 and "controles_cenit" in r["motivos"], (r["fila"], r["motivos"])
    monkeypatch.setattr(L, "controles_cenit", lambda *a, **k: {"estado": "SIN SUSTRATO"})
    r = leer(R, poblacion(), "MODIS")
    assert r["fila"] == 6 and r["controles"]["controles_cenit"]["estado"].startswith("OK")


def test_rutas_de_referencia_dentro_y_fuera_del_repo(tmp_path):
    """VPR946-02: una referencia dentro del repo entra al manifiesto por su ruta relativa; una fuera queda marcada."""
    (tmp_path / "ref").mkdir()
    (tmp_path / "ref" / "cons.csv").write_text("x", encoding="utf-8")
    afuera = tmp_path.parent / "cons_afuera.csv"
    r = L.rutas_referencias([str(tmp_path / "ref" / "cons.csv"), None, str(afuera)], raiz=tmp_path)
    assert r == ["ref/cons.csv", "FUERA_DEL_REPO:" + str(afuera)]


def test_main_con_manifiesto_exige_las_referencias(tmp_path, monkeypatch, R, capsys):
    """VPR946-02: con --manifiesto, el candado exige las rutas de --cons y --ocr; fuera del repo no pueden estar en el
    manifiesto y el candado queda en rojo aunque todo lo demás coincida."""
    test_main_de_punta_a_punta_con_predicado_sintetico(tmp_path, monkeypatch, R, capsys)
    man = {r: L.sha256_lf(L.RAIZ / r) for r in L.REQUERIDOS_MANIFIESTO}
    (tmp_path / "man.json").write_text(json.dumps(man), encoding="utf-8")
    sal = tmp_path / "out2.json"
    L.main(["--via", str(tmp_path / "via"), "--k", str(tmp_path / "k"), "--cons", str(tmp_path / "cons.csv"),
            "--ocr", str(tmp_path / "ocr.csv"), "--v750a-sellado", "no", "--manifiesto", str(tmp_path / "man.json"),
            "--salida", str(sal)], predicado=pred, reglas=R)
    c = json.loads(sal.read_text(encoding="utf-8"))["sensores"]["MODIS"]["controles"]["candado"]
    assert c["estado"].startswith("ROJO") and not c["distintos"], c
    assert len(c["fuera_del_manifiesto"]) == 2 and all(x.startswith("FUERA_DEL_REPO:") for x in c["fuera_del_manifiesto"])


def test_excepcion_de_c_k_con_tipos_malos_o_sin_hora(R):
    """VPR946-04: sensor que no es texto no cae; la hora se lee como fecha, no sólo por su largo; sin hora, rojo."""
    fs = _ck_filas()
    for mala in ({"vol": "Lascar", "dt": fs[0]["dt"], "sensor": 5, "empate_argsort": "x"},
                 {"vol": "Lascar", "dt": fs[0]["dt"], "sensor": ["MODIS_AQUA"], "empate_argsort": "x"},
                 {"vol": "Lascar", "dt": "x" * 16, "sensor": "MODIS_AQUA", "empate_argsort": "x"},
                 {"vol": "Lascar", "sensor": "MODIS_AQUA", "empate_argsort": "x"}):
        assert L.c_k(fs, [mala])["estado"].startswith("ROJO"), mala
        L.nulo_runner(R, fs, [mala])


def test_c_k_sin_pasadas_de_k_en_dm_es_rojo():
    """VPR946-11: si K de disco no trae ninguna pasada de DM, D3 no se cumple."""
    fs = [f for f in _kg_d3() if f["tramo"] != "DM"]
    r = L.c_k(fs)
    assert r["estado"].startswith("ROJO") and "sin pasadas de K en DM" in r["cobertura_kgemelo"]["faltan"]


def test_c_montaje_rechaza_un_tag_vacio():
    """VPR946-05 (X6)."""
    m = copy.deepcopy(MONTAJE_OK)
    m["tags"]["V375-E"] = "   "
    assert L.validar_montaje(m)["estado"].startswith("ROJO")


# ------------------------------------------------------------------------------------------- segunda ronda de #946
# experiments/_s173_aud/ver946/INFORME_R2.md y hallazgos_r2.csv en loop/activo.
def test_main_con_manifiesto_exige_tambien_el_osf(tmp_path, monkeypatch, R, capsys):
    """VPR946R2-01 (X2b): con --osf, el OSF también tiene que estar en el manifiesto (tres referencias, no dos)."""
    test_main_de_punta_a_punta_con_predicado_sintetico(tmp_path, monkeypatch, R, capsys)
    with open(tmp_path / "osf.csv", "w", encoding="latin-1", newline="") as fh:
        csv.writer(fh).writerow(["Volc_Name", "Volc_LAT", "Volc_LON", "timeUTC", "Resolution", "VRP", "class", "LAT",
                                 "LON", "SatZen", "Dayflag", "Satellite", "Max_Dist", "Npix"])
    man = {r: L.sha256_lf(L.RAIZ / r) for r in L.REQUERIDOS_MANIFIESTO}
    (tmp_path / "man.json").write_text(json.dumps(man), encoding="utf-8")
    sal = tmp_path / "out3.json"
    L.main(["--via", str(tmp_path / "via"), "--k", str(tmp_path / "k"), "--cons", str(tmp_path / "cons.csv"),
            "--ocr", str(tmp_path / "ocr.csv"), "--osf", str(tmp_path / "osf.csv"), "--v750a-sellado", "no",
            "--manifiesto", str(tmp_path / "man.json"), "--salida", str(sal)], predicado=pred, reglas=R)
    c = json.loads(sal.read_text(encoding="utf-8"))["sensores"]["MODIS"]["controles"]["candado"]
    assert len(c["fuera_del_manifiesto"]) == 3, c
    assert any(x.endswith("osf.csv") for x in c["fuera_del_manifiesto"])


def test_controles_de_cenit_sin_sustrato_real_cuenta_como_ok(R):
    """VPR946R2-02: SIN SUSTRATO de verdad (la curva no tiene pares) no es un control caído."""
    r = L.controles_cenit(R, poblacion(), "V")
    assert r["estado"] == "SIN SUSTRATO" and "error" not in r
    assert leer(R, poblacion(), "MODIS")["controles"]["controles_cenit"]["estado"].startswith("OK")


def test_controles_de_cenit_con_error_interno_es_rojo(R):
    """VPR946R2-02: un error dentro de los controles de cenit no puede leerse como SIN SUSTRATO ni contar como OK."""
    def revienta(*a, **k):
        raise ZeroDivisionError("simulado")
    malo = _Proxy(R, CC=_Proxy(R.CC, resumen=revienta))
    r = L.controles_cenit(malo, poblacion(), "V")
    assert r["estado"].startswith("ROJO") and "ZeroDivisionError" in r["error"], r
    s = L.leer_sensor(malo, poblacion(), "MODIS", COMUNES, pred, False, "def")
    assert s["fila"] == 1 and "controles_cenit" in s["motivos"], (s["fila"], s["motivos"])


def test_c_cenit_del_osf_se_evalua_por_sensor(R):
    """VPR946R2-03 (§8.1: «algún control del §6 en rojo para ese sensor»): un sensor sin pares de cenit se acusa
    aunque otro sí tenga."""
    r25 = [_r25("Lascar", "2025-06-02 05:00", 1, 1, z=25.0)]                     # pares sólo en VIIRS 375
    osf_res = L.p1_osf(r25, [_osf("Lascar", "VIIRS375", "2025-06-02 05:00", 2.0, satzen=25.0)])
    assert osf_res["c_cenit_por_sensor"]["VIIRS375"] == "OK"
    assert osf_res["c_cenit_por_sensor"]["MODIS"].startswith("ROJO")
    r = L.leer_sensor(R, poblacion(), "MODIS", COMUNES, pred, False, "def", osf_res=osf_res, filas_r25=r25)
    assert r["controles"]["c_cenit_osf"]["estado"].startswith("ROJO")
    r = L.leer_sensor(R, v375(), "VIIRS375", COMUNES, pred, False, "def", osf_res=osf_res, filas_r25=r25)
    assert r["controles"]["c_cenit_osf"]["estado"] == "OK" and r["fila"] == 6
    lejos = [_r25("Lascar", "2025-06-02 05:00", 1, 1, z=25.0), _r25("Lascar", "2025-06-03 05:00", 1, 1, z=40.0,
                                                                   b="VIIRS750", sensor="VIIRS_NOAA20_750")]
    o2 = L.p1_osf(lejos, [_osf("Lascar", "VIIRS375", "2025-06-02 05:00", 2.0, satzen=25.0),
                          _osf("Lascar", "VIIRS750", "2025-06-03 05:00", 6.0, satzen=25.0)])
    assert o2["c_cenit_por_sensor"]["VIIRS375"] == "OK" and o2["c_cenit_por_sensor"]["VIIRS750"].startswith("ROJO")
