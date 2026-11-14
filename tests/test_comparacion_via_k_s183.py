# -*- coding: utf-8 -*-
"""S183: pruebas de la comparación vía «código MIROVA», K y MIROVA (scripts/comparacion_via_k.py y su pestaña).

POR QUÉ. Nicolás pidió (2026-11-14) una vista que muestre cuál de los dos detectores se parece más a MIROVA. Si las
cuentas se equivocan, la vista diría lo contrario de lo que pasa, con la autoridad de una tabla: un silencio contado como
acierto haría parecer más fiable al detector que calla. Cada prueba fija una regla que, rota, cambia la lectura.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Si la cuenta estuviera rota, ¿lo veríamos? Cada regla tiene un caso donde la
respuesta correcta y la equivocada difieren (un silencio, una falsa alarma, una protegida, una pasada sin par). (2) ¿Puede
dar algo distinto de cero? El caso de punta a punta pasa por node y por el predicado real del tablero y tiene que dar un
acierto de la vía y un silencio de K en la misma noche.
"""
import csv
import json
import os
import shutil
import sys
from datetime import datetime, timezone

import pytest
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import comparacion_via_k as cv  # noqa: E402

node = pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")


def _p(vol="Lascar", b="MODIS", sensor="MODIS_AQUA", dt="2026-05-01 03:00", lab="pos", pub=1, disp=1.0,
       protegida=False, vrp_mirova=1.0, dc="summit", d_mc=0.5):
    t = datetime.strptime(dt, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": vol, "b": b, "sensor": sensor, "dt": t, "noche": dt[:10], "lab": lab, "pub": pub, "disp": disp,
            "protegida": protegida, "vrp_mirova": vrp_mirova, "dc": dc, "d_mc": d_mc, "dist_ref_tabla": None}


# ------------------------------------------------------------------ agregación por noche-satélite
def test_pos_le_gana_a_neg_y_publica_si_alguna_pasada_publica():
    n = cv.agregar_noches([_p(dt="2026-05-01 03:00", lab="neg_limpio", pub=0),
                           _p(dt="2026-05-01 04:40", lab="pos", pub=1, disp=2.0, vrp_mirova=2.0)])
    (e,) = n.values()
    assert e["lab"] == "pos" and e["pub"] == 1 and e["vrp_nuestro"] == 2.0


def test_far_ref_anula_el_negativo_y_sin_info_no_cuenta():
    n = cv.agregar_noches([_p(lab="neg_limpio", pub=1), _p(dt="2026-05-01 04:40", lab="far_ref", pub=0),
                           _p(dt="2026-05-02 03:00", lab="sin_info", pub=1)])
    assert n == {}


def test_satelites_distintos_son_noches_distintas():
    n = cv.agregar_noches([_p(sensor="MODIS_AQUA"), _p(sensor="MODIS_TERRA")])
    assert len(n) == 2


# ------------------------------------------------------------------ métricas
def test_metricas_cuentan_cada_casilla():
    pas = [_p(dt="2026-05-01 03:00", lab="pos", pub=1, protegida=True, disp=2.0, vrp_mirova=2.0),   # TP protegida
           _p(dt="2026-05-02 03:00", lab="pos", pub=0, protegida=True),                             # FN protegida
           _p(dt="2026-05-03 03:00", lab="pos", pub=0),                                             # FN
           _p(dt="2026-05-04 03:00", lab="neg_limpio", pub=1),                                      # FP
           _p(dt="2026-05-05 03:00", lab="neg_limpio", pub=0),                                      # TN
           _p(dt="2026-05-06 03:00", lab="neg_limpio", pub=0)]                                      # TN
    m = cv.metricas(cv.agregar_noches(pas), pas)
    assert (m["TP"], m["FN"], m["FP"], m["TN"]) == (1, 2, 1, 2)
    assert m["recall"] == round(1 / 3, 4) and m["precision"] == 0.5
    assert (m["protegidas"], m["protegidas_perdidas"]) == (2, 1)
    assert m["mediana_cociente"] == 1.0 and m["n_cociente"] == 1


def test_cociente_es_nuestro_sobre_mirova():
    pas = [_p(dt="2026-05-01 03:00", disp=1.0, vrp_mirova=4.0), _p(dt="2026-05-02 03:00", disp=3.0, vrp_mirova=4.0),
           _p(dt="2026-05-03 03:00", disp=2.0, vrp_mirova=4.0)]
    assert cv.metricas(cv.agregar_noches(pas), pas)["mediana_cociente"] == 0.5


def test_sin_casos_da_none_y_no_cero():
    m = cv.metricas({}, [])
    assert m["recall"] is None and m["precision"] is None and m["mediana_cociente"] is None


# ------------------------------------------------------------------ comparación pareada
def _idx(lista):
    return {(p["vol"], p["sensor"], p["dt"]): p for p in lista}


def test_compara_solo_pasadas_comunes_y_cuenta_alertas_sin_par():
    via = _idx([_p(dt="2026-05-01 03:00", pub=1), _p(dt="2026-05-02 03:00", pub=1)])
    k = _idx([_p(dt="2026-05-01 03:00", pub=0), _p(dt="2026-05-03 03:00", pub=0, protegida=True)])
    r = cv.comparar(via, k, "MODIS")
    assert r["n_pasadas_pareadas"] == 1
    assert (r["via"]["TP"], r["k"]["FN"]) == (1, 1)
    assert r["sin_par_via"]["pos"] == 1 and r["sin_par_k"]["pos"] == 1
    assert r["sin_par_k"]["protegidas"] == 1 and r["sin_par_k"]["protegidas_publica"] == 0


def test_protegida_en_desacuerdo_dice_quien_publica():
    via = _idx([_p(pub=1, protegida=True, vrp_mirova=3.0)])
    k = _idx([_p(pub=0, protegida=True, vrp_mirova=3.0, dc=None, d_mc=None)])
    (d,) = cv.comparar(via, k, "MODIS")["protegidas_discordantes"]
    assert d["via_pub"] == 1 and d["k_pub"] == 0 and d["vrp_mirova"] == 3.0


def test_otro_sensor_no_entra():
    via = _idx([_p(b="VIIRS375", sensor="VIIRS_NOAA20")])
    k = _idx([_p(b="VIIRS375", sensor="VIIRS_NOAA20")])
    assert cv.comparar(via, k, "MODIS")["n_pasadas_pareadas"] == 0


# ------------------------------------------------------------------ caché de la historia de K
def test_cache_solo_k_puro_y_antes_de_la_adopcion():
    recs = [{"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-01 07:00"},
            {"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-02 07:00"},                  # día de la adopción
            {"sensor": "MODIS_AQUA", "datetime_utc": "2026-10-30 07:00", "via_codigo_mirova": True},
            {"sensor": "VIIRS_NOAA20", "datetime_utc": "2026-11-10 06:00"},
            {"sensor": "VIIRS_NOAA20", "datetime_utc": "2026-11-11 06:00"},
            {"sensor": "VIIRS_NOAA20", "datetime_utc": "2026-02-28 06:00"},               # antes del inicio
            {"sensor": "VIIRS_NOAA20", "datetime_utc": "2026-03-01 06:00"}]               # el primer día sí entra
    quedan = [(r["sensor"], r["datetime_utc"]) for r in cv.filtrar_records_k(recs)]
    assert quedan == [("MODIS_AQUA", "2026-11-01 07:00"), ("VIIRS_NOAA20", "2026-11-10 06:00"),
                      ("VIIRS_NOAA20", "2026-03-01 06:00")]


def test_serie_k_historia_antes_de_la_adopcion_y_guardia_desde():
    hist = [_p(dt="2026-11-01 07:00"), _p(dt="2026-11-02 07:00"), _p(b="VIIRS375", sensor="VIIRS_NOAA20",
                                                                         dt="2026-11-10 06:00")]
    guar = [_p(dt="2026-10-30 07:00"), _p(dt="2026-11-02 07:00"), _p(b="VIIRS375", sensor="VIIRS_NOAA20",
                                                                        dt="2026-11-10 06:00")]
    s = [(p["b"], p["noche"], any(p is h for h in hist)) for p in cv.serie_k(hist, guar)]
    assert s == [("MODIS", "2026-11-01", True), ("VIIRS375", "2026-11-10", True), ("MODIS", "2026-11-02", False)]


def test_aviso_si_el_predicado_cambio_desde_el_cache():
    assert cv.avisos_cache({"sha_predicado": "aaa"}, "aaa") == []
    (a,) = cv.avisos_cache({"sha_predicado": "aaa"}, "bbb")
    assert "aaa" in a and "bbb" in a


def test_sha_del_predicado_ignora_texto_fuera_de_las_funciones():
    """V183-01: un cambio de texto de la página (un modal, PR #997) no cambia lo que se publica y no debe avisar; un
    cambio dentro de una función del predicado o en cambio_detector.js sí."""
    html = open(os.path.join(ROOT, "frontend", "index.html"), encoding="utf-8").read()
    cd = open(os.path.join(ROOT, "frontend", "cambio_detector.js"), encoding="utf-8").read()
    base = cv.sha_predicado(html, cd)
    assert cv.sha_predicado(html.replace("<title>", "<title>Otro texto ", 1), cd) == base
    dentro = html.replace("function isValidDetection(r) {", "function isValidDetection(r) { /* cambio */", 1)
    assert dentro != html and cv.sha_predicado(dentro, cd) != base
    assert cv.sha_predicado(html, cd + " // cambio") != base
    i = html.index("const F5_R_CORE_KM")
    j = html.index(";", i)
    assert cv.sha_predicado(html[:i] + "const F5_R_CORE_KM = 99" + html[j:], cd) != base


def test_ventanas_cubren_cada_dia_con_una_sola_fuente_de_k():
    """V183-03: la historia llega hasta el día antes de la adopción de cada sensor y la adopción parte ese día; ningún
    día queda fuera de las tarjetas ni con dos K."""
    assert cv.ventanas("2026-11-14") == {
        "historia": {"MODIS": ("2026-03-01", "2026-11-01"), "VIIRS375": ("2026-03-01", "2026-11-10"),
                     "VIIRS750": ("2026-03-01", "2026-11-10")},
        "adopcion": {"MODIS": ("2026-11-02", "2026-11-14"), "VIIRS375": ("2026-11-11", "2026-11-14"),
                     "VIIRS750": ("2026-11-11", "2026-11-14")}}


def test_cociente_es_mediana_y_no_media():
    pas = [_p(dt="2026-05-01 03:00", disp=0.5, vrp_mirova=1.0), _p(dt="2026-05-02 03:00", disp=0.5, vrp_mirova=1.0),
           _p(dt="2026-05-03 03:00", disp=2.0, vrp_mirova=1.0)]
    assert cv.metricas(cv.agregar_noches(pas), pas)["mediana_cociente"] == 0.5


def test_protegida_por_noche_basta_una_pasada():
    pas = [_p(dt="2026-05-01 03:00", protegida=False, pub=0), _p(dt="2026-05-01 04:40", protegida=True, pub=0)]
    m = cv.metricas(cv.agregar_noches(pas), pas)
    assert (m["protegidas"], m["protegidas_perdidas"]) == (1, 1)


def test_filas_noches_dicen_de_donde_sale_k():
    via = [_p(dt="2026-11-01 07:00", pub=1), _p(dt="2026-11-03 07:00", pub=1)]
    k = [_p(dt="2026-11-01 07:00", pub=0), _p(dt="2026-11-03 07:00", pub=1)]
    out = cv.filas_noches({"tabla": (via, k), "combinado": (via, k)}, "2026-11-14")
    filas = [dict(zip(out["campos"], f)) for f in out["filas"]]
    assert [(f["noche"], f["via_pub"], f["k_pub"], f["k_fuente"]) for f in filas] == [
        ("2026-11-01", 1, 0, "historia"), ("2026-11-03", 1, 1, "guardia")]


def test_filas_noches_incluyen_la_falsa_alarma_de_un_solo_detector():
    via = [_p(dt="2026-06-01 07:00", lab="neg_limpio", pub=1)]
    k = [_p(dt="2026-06-01 07:00", lab="neg_limpio", pub=0)]
    out = cv.filas_noches({"tabla": (via, k), "combinado": (via, k)}, "2026-11-14")
    (f,) = [dict(zip(out["campos"], x)) for x in out["filas"]]
    assert (f["lab_tabla"], f["via_pub"], f["k_pub"]) == ("neg", 1, 0)
    out = cv.filas_noches({"tabla": (k, via), "combinado": (k, via)}, "2026-11-14")
    (f,) = [dict(zip(out["campos"], x)) for x in out["filas"]]
    assert (f["via_pub"], f["k_pub"]) == (0, 1)
    nada = cv.filas_noches({"tabla": (k, k), "combinado": (k, k)}, "2026-11-14")
    assert nada["filas"] == [], "una noche tranquila en que nadie publica no se dibuja"


def _fila_ref(source, tipo, vrp, hora="03:00:00"):
    return {"volcano": "Lascar", "sensor_bucket": "MODIS", "sensor_raw": "MODIS", "fecha_utc": "2026-05-01 " + hora,
            "source": source, "origen": "principal", "tipo": tipo, "vrp_mw": vrp, "dist_km": 1.0, "clasificacion": "",
            "ultima_actualizacion": "2026-05-01 05:00:00", "sin_geometria": False}


def test_etiquetar_prefiere_la_tabla_y_marca_protegida_con_cualquier_fila():
    coords = cv.bp._coords_por_volcan()
    filas = [_fila_ref("CONS", "ALERTA_TERMICA", 0.8), _fila_ref("OCR", "ALERTA_TERMICA_OCR", 1.5)]
    pas = [{k: v for k, v in _p(dt="2026-05-01 03:00").items() if k not in ("lab", "vrp_mirova", "protegida")}]
    ref = cv.bp.indexar_referencia(filas, coords, ("2026-05-01", "2026-05-01"), regla_minimas="SN")
    (r,) = cv.etiquetar(pas, ref)
    assert (r["lab"], r["vrp_mirova"], r["protegida"]) == ("pos", 0.8, True)
    ref_tabla = cv.bp.indexar_referencia(filas[:1], coords, ("2026-05-01", "2026-05-01"), regla_minimas="SN")
    (r,) = cv.etiquetar(pas, ref_tabla)
    assert (r["lab"], r["vrp_mirova"], r["protegida"]) == ("pos", 0.8, False)
    assert "lab" not in pas[0], "etiquetar no debe tocar las pasadas de entrada (se etiquetan con dos referencias)"
    dos = [_fila_ref("CONS", "ALERTA_TERMICA", 0.8), _fila_ref("CONS", "ALERTA_TERMICA", 1.2, hora="03:01:00")]
    (r,) = cv.etiquetar(pas, cv.bp.indexar_referencia(dos, coords, ("2026-05-01", "2026-05-01"), regla_minimas="SN"))
    assert r["vrp_mirova"] == 1.2


# ------------------------------------------------------------------ punta a punta con node y el predicado real
REC_PUB = {"sensor": "MODIS_AQUA", "datetime_utc": "2027-01-05 03:00", "distance_class": "summit", "t_max_k": 320.0,
           "vrp_mw": 2.0, "triggered_test1": False, "vrp_vent_mw": 0.0, "f5_core_vrp_mw": None, "anomaly_pixels": [],
           "primary_cluster": {"vrp_mw": 2.0, "centroid_dist_km": 0.7, "n_pixels": 3}, "via_codigo_mirova": True,
           "final_hotspot_lat": -23.37, "final_hotspot_lon": -67.73}
REC_NADA = {"sensor": "MODIS_AQUA", "datetime_utc": "2027-01-05 03:00", "distance_class": None, "t_max_k": 280.0,
            "vrp_mw": 0.0, "triggered_test1": False, "vrp_vent_mw": 0.0, "f5_core_vrp_mw": None, "anomaly_pixels": [],
            "primary_cluster": None}
CAMPOS_CSV = ["Fecha_Satelite_UTC", "Volcan", "Sensor", "VRP_MW", "Distancia_km", "Tipo_Registro",
              "Clasificacion Mirova", "Ultima_Actualizacion", "Nota_Validacion"]


def _carpeta(tmp_path, nombre, rec):
    d = tmp_path / nombre
    d.mkdir()
    for vol in cv.bp.VOLS:
        (d / f"{vol}.json").write_text(json.dumps({"records": [rec] if (vol == "Lascar" and rec) else []}),
                                       encoding="utf-8")
    return d


@node
def test_punta_a_punta_via_acierta_y_k_calla(tmp_path):
    prod = _carpeta(tmp_path, "prod", REC_PUB)
    guardia = _carpeta(tmp_path, "guardia", REC_NADA)
    cons = tmp_path / "cons.csv"
    with open(cons, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS_CSV)
        w.writeheader()
        w.writerow({"Fecha_Satelite_UTC": "2027-01-05 03:00:00", "Volcan": "Lascar", "Sensor": "MODIS",
                    "VRP_MW": "2.1", "Distancia_km": "0.8", "Tipo_Registro": "ALERTA_TERMICA",
                    "Clasificacion Mirova": "", "Ultima_Actualizacion": "2027-01-05 05:00:00", "Nota_Validacion": ""})
    ocr = tmp_path / "ocr.csv"
    with open(ocr, "w", newline="", encoding="utf-8") as fh:
        csv.DictWriter(fh, fieldnames=CAMPOS_CSV).writeheader()
    cache = tmp_path / "cache.json"
    cache.write_text(json.dumps({"meta": {"sha_predicado": cv.sha_predicado_actual()}, "pasadas": []}),
                     encoding="utf-8")
    out = tmp_path / "out.json"
    assert cv.main(["--prod", str(prod), "--guardia-modis", str(guardia), "--guardia-viirs", str(guardia),
                    "--cache-k", str(cache), "--cons", str(cons), "--ocr", str(ocr), "--hoy", "2027-01-10",
                    "--sin-capas-historicas", "--out", str(out)]) == 0
    d = json.loads(out.read_text(encoding="utf-8"))
    r = d["resultados"]["tabla|adopcion|MODIS"]
    assert (r["via"]["TP"], r["k"]["FN"], r["via"]["protegidas"], r["k"]["protegidas_perdidas"]) == (1, 1, 1, 1)
    campos = d["noches"]["campos"]
    (fila,) = d["noches"]["filas"]
    f = dict(zip(campos, fila))
    assert (f["vol"], f["via_pub"], f["k_pub"], f["lab_tabla"], f["prot_tabla"]) == ("Lascar", 1, 0, "pos", 1)
    assert d["meta"]["avisos"] == []


# ------------------------------------------------------------------ la página y el workflow
HTML = os.path.join(ROOT, "frontend", "comparacion.html")


def test_la_pagina_lee_el_json_y_los_campos_que_escribe_el_script():
    html = open(HTML, encoding="utf-8").read()
    assert '<script src="comparacion_via_k.js"></script>' in html
    src = html + open(os.path.join(ROOT, "frontend", "comparacion_via_k.js"), encoding="utf-8").read()
    assert "data/audit_continuous/comparacion_via_k.json" in src
    assert 'data-tab="viak"' in src and 'class="tab-btn active" data-tab="viak"' in src
    for campo in cv.CAMPOS_USADOS_POR_LA_PAGINA:
        assert campo in cv.CAMPOS_NOCHE, campo
        assert f'"{campo}"' in src, campo


def test_workflow_diario_corre_el_script_y_commitea_solo_su_salida():
    path = os.path.join(ROOT, ".github", "workflows", "comparacion-via-k.yml")
    txt = open(path, encoding="utf-8").read()
    wf = yaml.safe_load(txt)
    assert "on" in wf, "A43: quotear \"on\":"
    assert "scripts/comparacion_via_k.py" in txt
    adds = [ln.strip() for ln in txt.splitlines() if ln.strip().startswith("git add")]
    assert adds == ["git add data/audit_continuous/comparacion_via_k.json"]
    assert "group: push-main" not in txt and "pull --rebase" in txt
