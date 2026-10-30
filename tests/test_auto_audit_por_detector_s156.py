# -*- coding: utf-8 -*-
"""S156 (arreglos 2 y 3 de docs/AUDIT_S155.md §5): el auto-audit separa los dos detectores y lista las
alertas protegidas sin publicar.

POR QUE: desde la fecha de observacion 2026-09-18 los records son del detector K y antes, de C0. La ventana
rodante de 60 dias juntaba las dos mitades: VIIRS 375 publicaba en negativos limpios 86,5 % con C0 y 1,8 %
con K, y el audit escribia una mezcla (31 a 33 %) que no es de ningun detector (F3-02); el recall de K en
VIIRS 375 quedaba tapado por el de C0 (F3-01). Y el criterio de victoria de la replica, ninguna alerta
protegida perdida, no tenia instrumento: dos protegidas MODIS de Chillan se perdieron sin aviso (F3-04).
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.auto_audit_weekly as aa  # noqa: E402

FRONTERA = "2026-09-18"


def _rec(fecha, sensor="VIIRS_SNPP", vrp=1.0, dist=1.0, dc="summit", core=None, sha="abc", npix=1):
    r = {"datetime_utc": fecha, "sensor": sensor, "distance_class": dc,
         "primary_cluster": {"vrp_mw": vrp, "centroid_dist_km": dist},
         "anomaly_pixels": [{}] * npix}
    if core is not None:
        r["f5_core_vrp_mw"] = core
    if sha:
        r["regimen"] = {"perfil": "mirova_equivalent", "codigo_sha": sha, "origen": "actions"}
    return r


# ------------------------------------------------------------------ frontera y detector
def test_la_frontera_sale_del_js_del_tablero():
    """Una sola fuente: la que vigila tests/test_cambio_detector_frontera_s155.py contra los JSON."""
    js = (ROOT / "frontend" / "cambio_detector.js").read_text(encoding="utf-8")
    f = aa.leer_frontera_k()
    assert f is not None and len(f) == 10
    assert f'DATOS_K_DESDE_UTC = "{f}T' in js


def test_frontera_null_en_el_js_da_none(tmp_path):
    p = tmp_path / "cambio_detector.js"
    p.write_text('  const DATOS_K_DESDE_UTC = null;\n', encoding="utf-8")
    assert aa.leer_frontera_k(p) is None


def test_detector_de_record():
    assert aa.detector_de_record(_rec("2026-10-01 05:00"), FRONTERA) == "K"
    assert aa.detector_de_record(_rec("2026-09-17 05:00", sha=None), FRONTERA) == "C0"
    # sin marca despues de la frontera (los MODIS Terra que no se reprocesaron, F2-08): estrato propio
    assert aa.detector_de_record(_rec("2026-09-20 05:00", sha=None), FRONTERA) == "sin_marca"
    # sin frontera declarada no hay K todavia
    assert aa.detector_de_record(_rec("2026-09-20 05:00", sha=None), None) == "C0"


def test_detector_de_noche():
    assert aa.detector_de_noche("2026-09-17", FRONTERA) == "C0"
    assert aa.detector_de_noche("2026-09-18", FRONTERA) == "K"
    assert aa.detector_de_noche("2026-09-18", None) == "C0"


# ------------------------------------------------------------------ nuestros records por noche
def test_una_noche_se_evalua_solo_con_records_de_su_detector():
    recs = {"Villarrica": [
        _rec("2026-09-20 05:00", vrp=2.0),                      # K, noche K: cuenta
        _rec("2026-09-20 06:00", vrp=9.0, sha=None),            # sin marca en noche K: fuera
        _rec("2026-09-10 05:00", vrp=3.0, sha=None),            # C0 en noche C0: cuenta
        _rec("2026-09-11 05:00", vrp=4.0),                      # K antes de la frontera: fuera
    ]}
    res = aa.nuestros_por_noche(recs, ("2026-09-01", "2026-10-19"), FRONTERA)
    ours, vistos = res["ours"], res["vistos"]
    assert ours[("Villarrica", "VIIRS375", "2026-09-20")]["crater"] == [2.0]
    assert ours[("Villarrica", "VIIRS375", "2026-09-10")]["crater"] == [3.0]
    assert ("Villarrica", "VIIRS375", "2026-09-11") not in ours
    assert ("Villarrica", "VIIRS375", "2026-09-11") not in vistos
    assert res["fuera_de_detector"] == {"sin_marca en noche K": 1, "K en noche C0": 1}


def test_magnitud_publicada_usa_el_nucleo_en_viirs375_y_pc_en_los_otros():
    recs = {"Villarrica": [_rec("2026-09-20 05:00", vrp=2.0, core=0.5),
                           _rec("2026-09-20 05:30", sensor="VIIRS_SNPP_750", vrp=3.0, core=0.1)]}
    ours = aa.nuestros_por_noche(recs, ("2026-09-01", "2026-10-19"), FRONTERA)["ours"]
    assert ours[("Villarrica", "VIIRS375", "2026-09-20")]["pub"] == [0.5]
    assert ours[("Villarrica", "VIIRS750", "2026-09-20")]["pub"] == [3.0]


# ------------------------------------------------------------------ D-9
def test_d9_sn_quita_la_pasada_minima_de_viirs375_y_deja_las_demas():
    alertas = [
        {"volcano": "Villarrica", "sensor_bucket": "VIIRS375", "fecha_utc": "2026-09-20 05:00:00", "vrp_mw": 0.04},
        {"volcano": "Villarrica", "sensor_bucket": "VIIRS375", "fecha_utc": "2026-09-21 05:00:00", "vrp_mw": 0.30},
        {"volcano": "Villarrica", "sensor_bucket": "MODIS", "fecha_utc": "2026-09-22 05:00:00", "vrp_mw": 0.04},
    ]
    sn = aa.aplicar_d9(alertas, "SN")
    assert [a["fecha_utc"][:10] for a in sn] == ["2026-09-21", "2026-09-22"]
    assert aa.aplicar_d9(alertas, "original") == alertas


# ------------------------------------------------------------------ evaluacion y flags
def _escenario():
    """MIROVA alerta 20 noches VIIRS 375 en Villarrica: 10 C0 (las vemos todas) y 10 K (vemos 5)."""
    mir, recs = {}, []
    for i in range(10):
        d0, d1 = f"2026-09-{i + 1:02d}", f"2026-09-{i + 20:02d}"
        mir[("Villarrica", "VIIRS375", d0)] = 1.0
        mir[("Villarrica", "VIIRS375", d1)] = 1.0
        recs.append(_rec(d0 + " 05:00", sha=None, vrp=1.0, core=1.0))
        recs.append(_rec(d1 + " 05:00", vrp=(1.0 if i < 5 else 0.0), core=1.0))
    return mir, {"Villarrica": recs}


def test_el_recall_se_separa_por_detector():
    mir, recs = _escenario()
    res = aa.nuestros_por_noche(recs, ("2026-09-01", "2026-10-19"), FRONTERA)
    c0 = aa.evaluar_detector(mir, res["ours"], res["vistos"], "C0", FRONTERA)
    k = aa.evaluar_detector(mir, res["ours"], res["vistos"], "K", FRONTERA)
    assert c0["recall"]["VIIRS375"]["recall_crater_pct"] == 100.0
    assert k["recall"]["VIIRS375"]["recall_crater_pct"] == 50.0
    assert k["recall"]["VIIRS375"]["n_noches"] == 10


def test_flags_solo_del_detector_vigente():
    mir, recs = _escenario()
    # 16 noches K para pasar MIN_N_RECALL: se agregan 6 noches K vistas
    for i in range(6):
        d = f"2026-10-{i + 1:02d}"
        mir[("Villarrica", "VIIRS375", d)] = 1.0
        recs["Villarrica"].append(_rec(d + " 05:00", vrp=1.0, core=1.0))
    res = aa.nuestros_por_noche(recs, ("2026-09-01", "2026-10-19"), FRONTERA)
    k = aa.evaluar_detector(mir, res["ours"], res["vistos"], "K", FRONTERA)
    c0 = aa.evaluar_detector(mir, res["ours"], res["vistos"], "C0", FRONTERA)
    fk = aa.flags_de_evaluacion(k)
    assert any("recall VIIRS375" in f for f in fk)
    # C0 viene perfecto: si se mezclara, 21/26 = 80,8 % igual daria flag; la prueba de que no se mezcla es la n
    assert any("n=16" in f for f in fk)
    assert aa.flags_de_evaluacion(c0) == []


def test_magnitud_por_volcan_y_sensor_con_lo_publicado():
    mir, recs = {}, {"Villarrica": []}
    for i in range(6):
        d = f"2026-10-{i + 1:02d}"
        mir[("Villarrica", "VIIRS375", d)] = 1.0
        recs["Villarrica"].append(_rec(d + " 05:00", vrp=1.0, core=0.4))   # publica 0,4 de MIROVA
        mir[("Villarrica", "MODIS", d)] = 1.0
        recs["Villarrica"].append(_rec(d + " 05:30", sensor="MODIS_AQUA", vrp=1.0))
    res = aa.nuestros_por_noche(recs, ("2026-09-01", "2026-10-19"), FRONTERA)
    k = aa.evaluar_detector(mir, res["ours"], res["vistos"], "K", FRONTERA)
    m = k["magnitud_publicada_by_vol_sensor"]
    assert m["Villarrica|VIIRS375"]["ratio_mediano"] == 0.4
    assert m["Villarrica|MODIS"]["ratio_mediano"] == 1.0
    assert m["Villarrica|VIIRS375"]["pasadas_publicadas_por_noche"] == 1
    fk = aa.flags_de_evaluacion(k)
    assert any("Villarrica VIIRS375" in f and "0.4" in f for f in fk)
    assert not any("MODIS" in f for f in fk)
    # la mediana por volcan con pc.vrp_mw (todos los sensores) queda como informacion
    assert k["magnitud_ratio_by_vol"]["Villarrica"]["ratio_mediano"] == 1.0


def test_el_flag_sub_banda_no_atribuye_la_causa():
    v = aa.evaluar_ratio_mediano("Villarrica", 0.4, n_noches=10)
    assert "sin medir" in v and "S124" in v


# ------------------------------------------------------------------ alertas protegidas
def _fila(vol, b, fecha, vrp, tipo="ALERTA_TERMICA"):
    return {"volcano": vol, "sensor_bucket": b, "fecha_utc": fecha, "vrp_mw": vrp, "tipo": tipo}


def _brec(vol, b, fecha, pub, sha="abc"):
    from datetime import datetime, timezone
    dt = datetime.strptime(fecha, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": vol, "b": b, "dt": dt, "noche": fecha[:10], "pub": pub, "sha": sha}


def test_protegidas_listadas_con_su_estado_y_flag_solo_sin_publicar_del_vigente():
    filas = [
        _fila("NevadosDeChillan", "MODIS", "2026-10-12 07:20:00", 2.18),       # K, sin publicar
        _fila("NevadosDeChillan", "VIIRS375", "2026-10-12 06:00:00", 5.0),     # K, publicada
        _fila("NevadosDeChillan", "MODIS", "2026-10-13 07:20:00", 1.5),        # K, sin record
        _fila("NevadosDeChillan", "MODIS", "2026-09-05 07:20:00", 3.0),        # C0, sin publicar
        _fila("NevadosDeChillan", "MODIS", "2026-10-14 07:20:00", 0.9),        # bajo 1 MW: no protegida
        _fila("NevadosDeChillan", "MODIS", "2026-10-15 07:20:00", 4.0, tipo="FALSO_POSITIVO"),  # lectura A: no
    ]
    recs = [_brec("NevadosDeChillan", "MODIS", "2026-10-12 07:21", False),
            _brec("NevadosDeChillan", "VIIRS375", "2026-10-12 06:00", True),
            _brec("NevadosDeChillan", "MODIS", "2026-09-05 07:20", False, sha=None)]
    lista = aa.alertas_protegidas(filas, recs, ("2026-08-20", "2026-10-19"), FRONTERA, diurna=lambda *a: False)
    estado = {(p["sensor"], p["fecha_utc"][:10]): (p["detector"], p["estado"]) for p in lista}
    assert estado == {("MODIS", "2026-10-12"): ("K", "sin_publicar"),
                      ("VIIRS375", "2026-10-12"): ("K", "publicada"),
                      ("MODIS", "2026-10-13"): ("K", "sin_record"),
                      ("MODIS", "2026-09-05"): ("C0", "sin_publicar")}
    sin_pub = [p for p in lista if p["estado"] == "sin_publicar" and p["detector"] == "K"]
    assert sin_pub[0]["noche_publicada_otra_pasada"] is True
    flags = aa.flags_protegidas(lista, "K")
    assert len(flags) == 1
    assert "NevadosDeChillan MODIS 2026-10-12 07:20" in flags[0] and "2.18" in flags[0]


def test_protegida_solo_ocr_de_suomi_npp_antes_del_hito_se_marca_sospechosa():
    """A119: antes del hito, la distancia de una fila sólo OCR de Suomi NPP puede ser de otra pasada."""
    hito = aa.HITO_OCR_SUOMI_NPP
    assert hito == "2026-10-09"
    filas = [dict(_fila("Tupungatito", "VIIRS375", "2026-09-28 05:18:00", 2.51, tipo="ALERTA_TERMICA_OCR"),
                  source="OCR"),
             dict(_fila("Tupungatito", "VIIRS375", "2026-09-29 04:54:00", 1.86), source="CONS"),
             dict(_fila("Tupungatito", "VIIRS375", "2026-10-12 04:54:00", 1.5, tipo="ALERTA_TERMICA_OCR"),
                  source="OCR")]
    recs = [dict(_brec("Tupungatito", "VIIRS375", "2026-09-28 05:18", False), sensor="VIIRS_SNPP"),
            dict(_brec("Tupungatito", "VIIRS375", "2026-09-29 04:54", False), sensor="VIIRS_SNPP"),
            dict(_brec("Tupungatito", "VIIRS375", "2026-10-12 04:54", False), sensor="VIIRS_SNPP")]
    lista = aa.alertas_protegidas(filas, recs, ("2026-08-20", "2026-10-19"), FRONTERA, diurna=lambda *a: False)
    assert [p["referencia_sospechosa"] for p in lista] == [True, False, False]
    flags = aa.flags_protegidas(lista, "K")
    # S166 (issue #915, decisión de Nicolás): la sospechosa ya no es flag, se informa aparte
    # (tests/test_auto_audit_referencia_s166.py); las otras dos siguen siéndolo.
    assert [f.split(" UTC")[0][-16:] for f in flags] == ["2026-09-29 04:54", "2026-10-12 04:54"]
    assert not any("referencia sospechosa" in f for f in flags)
    assert "referencia sospechosa" in aa.protegidas_aparte(lista, "K")[0]


def test_protegidas_diurnas_no_entran():
    filas = [_fila("Lascar", "VIIRS375", "2026-10-12 17:00:00", 3.0)]
    assert aa.alertas_protegidas(filas, [], ("2026-08-20", "2026-10-19"), FRONTERA,
                                 diurna=lambda *a: True) == []


# ------------------------------------------------------------------ historial
def test_la_linea_del_historial_dice_de_que_detector_es():
    out = {"generated_utc": "2026-10-19T12:00:00Z", "verdict": "VERDE",
           "recall": {s: {"recall_crater_pct": 99.0} for s in aa.SENSORS},
           "falsas_publicaciones": {"por_sensor": {s: {"n_neg_limpio": 10, "falsas_pub_pct": 2.0}
                                                   for s in aa.SENSORS}, "alarma": False},
           "detector": {"vigente": "K", "frontera_datos": FRONTERA, "regla_minimas": "SN"},
           "flags": []}
    linea = aa.linea_historial(out, cobertura_pct=100.0, gt_stale_dias=0)
    assert linea["detector"] == {"vigente": "K", "frontera_datos": FRONTERA, "regla_minimas": "SN"}
    assert linea["falsas_pub_pct"] == {s: 2.0 for s in aa.SENSORS}


@pytest.mark.parametrize("frontera,esperado", [("2026-09-18", "K"), (None, "C0")])
def test_detector_vigente(frontera, esperado):
    assert aa.detector_vigente(frontera) == esperado
