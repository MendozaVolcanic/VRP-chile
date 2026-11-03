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
    r = leer(R, fs, "VIIRS750", sellado=True)
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
    assert L.candado(ok, tmp_path)["estado"] == "OK"
    (tmp_path / "a.py").write_bytes(b"x = 2\n")
    assert L.candado(ok, tmp_path)["estado"].startswith("ROJO")
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


def test_main_de_punta_a_punta_con_predicado_sintetico(tmp_path, monkeypatch, R):
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
