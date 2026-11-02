# -*- coding: utf-8 -*-
"""S172: el auto-audit semanal separa el detector VIA_MODIS (la vía «código MIROVA» de MODIS) de K.

POR QUÉ (diseño docs/superpowers/specs/2026-11-01-encendido-modd-design.md, decisión 4). `_detector` llama «K» a todo
record con `codigo_sha` (S156). Tras el encendido, los records MODIS de la vía también traen `codigo_sha`: sin un
detector propio se contarían como K, y la ventana de 60 días promediaría dos detectores de MODIS como una sola serie
(el defecto F3-01/F3-02 de AUDIT_S155 que S156 arregló para C0 y K). Ahora cada noche MODIS posterior a la primera
pasada de la vía se evalúa con records de la vía, cada detector se informa entero y en MODIS decide la vía. Las bandas
no se recalibran (A115). Con los datos de hoy (sin records de la vía) el audit tiene que dar exactamente lo mismo que
antes: lo fija la última prueba y la comparación sobre data/ real del INFORME_IMPLEMENTADOR.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.auto_audit_weekly as aa  # noqa: E402

FRONTERA = "2026-09-18"
SHA = "f" * 40


def _rec(fecha, sensor="MODIS_AQUA", vrp=1.0, via=None, sha=True, hora="07:20"):
    r = {"datetime_utc": f"{fecha} {hora}", "sensor": sensor, "distance_class": "summit",
         "primary_cluster": {"vrp_mw": vrp, "centroid_dist_km": 1.0} if vrp else {},
         "anomaly_pixels": [{}] if vrp else []}
    if sha:
        r["regimen"] = {"codigo_sha": SHA}
    if via is not None:
        r["via_codigo_mirova"] = via
    return r


# ------------------------------------------------------------------ piezas
def test_la_frontera_de_la_via_sale_de_los_datos():
    recs = {"Villarrica": [_rec("2026-11-01"), _rec("2026-11-06", via=True), _rec("2026-11-05", via="sin_mxd03"),
                           _rec("2026-11-07", via=True),
                           _rec("2026-11-02", sensor="VIIRS_NOAA20_750", via=True)]}
    assert aa.frontera_via_modis(recs) == "2026-11-06"
    assert aa.frontera_via_modis({"Villarrica": [_rec("2026-11-01")]}) is None


def test_detector_de_record_distingue_la_via_de_modis():
    assert aa.detector_de_record(_rec("2026-11-06", via=True), FRONTERA) == "VIA_MODIS"
    assert aa.detector_de_record(_rec("2026-11-06"), FRONTERA) == "K"
    # la caída a K no es la vía; la vía de VIIRS no es la de MODIS
    assert aa.detector_de_record(_rec("2026-11-06", via="sin_mxd03"), FRONTERA) == "K"
    assert aa.detector_de_record(_rec("2026-11-06", sensor="VIIRS_NOAA20_750", via=True), FRONTERA) == "K"


def test_detector_de_noche_por_sensor():
    assert aa.detector_de_noche("2026-11-06", FRONTERA, "MODIS", "2026-11-06") == "VIA_MODIS"
    assert aa.detector_de_noche("2026-11-05", FRONTERA, "MODIS", "2026-11-06") == "K"
    assert aa.detector_de_noche("2026-11-06", FRONTERA, "VIIRS375", "2026-11-06") == "K"
    assert aa.detector_de_noche("2026-11-06", FRONTERA) == "K"            # sin frontera de la vía, como antes
    assert aa.detector_vigente_de("MODIS", "K", "2026-11-06") == "VIA_MODIS"
    assert aa.detector_vigente_de("VIIRS375", "K", "2026-11-06") == "K"
    assert aa.detector_vigente_de("MODIS", "K", None) == "K"


def test_detector_del_banco_por_clave_de_la_via():
    dt = datetime(2026, 11, 6, 7, 20, tzinfo=timezone.utc)
    r = {"vol": "Villarrica", "sensor": "MODIS_AQUA", "dt": dt, "noche": "2026-11-06", "sha": SHA}
    via = {("Villarrica", "MODIS_AQUA", "2026-11-06 07:20")}
    assert aa._detector_banco(r, FRONTERA, via) == "VIA_MODIS"
    assert aa._detector_banco(r, FRONTERA) == "K"
    assert aa._detector_banco(dict(r, sensor="MODIS_TERRA"), FRONTERA, via) == "K"


def test_una_noche_de_la_via_se_evalua_solo_con_records_de_la_via():
    recs = {"Villarrica": [_rec("2026-11-06", via=True), _rec("2026-11-06", via="sin_mxd03", hora="03:10"),
                           _rec("2026-11-04")]}
    res = aa.nuestros_por_noche(recs, ("2026-10-01", "2026-11-30"), FRONTERA, via_modis="2026-11-06")
    assert res["fuera_de_detector"] == {"K en noche VIA_MODIS": 1}
    assert res["n_records_por_detector"] == {"VIA_MODIS": 1, "K": 2}
    assert len(res["ours"][("Villarrica", "MODIS", "2026-11-06")]["dash"]) == 1


def test_evaluar_detector_via_modis_solo_mira_noches_modis_de_la_via():
    mir = {("Villarrica", "MODIS", "2026-11-06"): 1.5, ("Villarrica", "MODIS", "2026-11-04"): 1.5,
           ("Villarrica", "VIIRS375", "2026-11-06"): 1.5}
    recs = {"Villarrica": [_rec("2026-11-06", via=True), _rec("2026-11-04"),
                           _rec("2026-11-06", sensor="VIIRS_NOAA20", hora="05:00")]}
    res = aa.nuestros_por_noche(recs, ("2026-10-01", "2026-11-30"), FRONTERA, via_modis="2026-11-06")
    v = aa.evaluar_detector(mir, res["ours"], res["vistos"], "VIA_MODIS", FRONTERA, via_modis="2026-11-06")
    k = aa.evaluar_detector(mir, res["ours"], res["vistos"], "K", FRONTERA, via_modis="2026-11-06")
    assert v["recall"]["MODIS"]["n_noches"] == 1 and v["recall"]["VIIRS375"]["n_noches"] == 0
    assert k["recall"]["MODIS"]["n_noches"] == 1 and k["recall"]["VIIRS375"]["n_noches"] == 1


# ------------------------------------------------------------------ main() de punta a punta
HOY = datetime.now(timezone.utc).date()


def _dia(n):
    return (HOY - timedelta(days=n)).isoformat()


def _brec(fecha, b, pub, lab, sensor="MODIS_AQUA"):
    dt = datetime.strptime(f"{fecha} 07:20", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": "Villarrica", "b": b, "dt": dt, "noche": fecha, "pub": pub, "lab": lab, "lab_original": lab,
            "sha": SHA, "z": 20.0, "sensor": sensor}


def _escenario(con_via, via_publica=False, n_reciente=16):
    """MODIS Villarrica: `n_reciente` noches recientes (la vía si `con_via`) y el resto, hasta 36, anteriores de K que
    vemos. Las recientes NO las vemos salvo `via_publica` (S173, hallazgo 205: la vía que publica en una noche con
    alerta es el camino que hacía caer el audit)."""
    records, alertas = [], []
    for n in range(0, 36):
        d = _dia(n)
        alertas.append({"volcano": "Villarrica", "sensor_bucket": "MODIS", "fecha_utc": d + " 07:20:00",
                        "vrp_mw": 0.5})
        reciente = n < n_reciente
        vrp = (1.0 if via_publica else 0.0) if reciente else 1.0
        records.append(_rec(d, vrp=vrp, via=(True if (reciente and con_via) else None)))
    banco = ([_brec(_dia(2), "MODIS", False, "pos")],
             [{"volcano": "Villarrica", "sensor_bucket": "MODIS", "fecha_utc": _dia(2) + " 07:20:00", "vrp_mw": 2.0,
               "tipo": "ALERTA_TERMICA", "source": "CONS"}])
    return records, alertas, banco


@pytest.fixture
def correr(monkeypatch, tmp_path):
    def _correr(con_via, **kw):
        records, alertas, banco = _escenario(con_via, **kw)
        monkeypatch.setattr(aa, "leer_frontera_k", lambda *a: FRONTERA)
        monkeypatch.setattr(aa, "alertas_mirova", lambda *a, **k: alertas)
        monkeypatch.setattr(aa, "cargar_filas_referencia", lambda: None)
        monkeypatch.setattr(aa, "cargar_records",
                            lambda: ({"Villarrica": records}, {"parse_errors": [], "duplicates_total": 0}))
        monkeypatch.setattr(aa, "banco_ventana", lambda win: banco)
        monkeypatch.setattr(aa, "_coords_por_volcan", lambda: {"Villarrica": (-39.42, -71.94)})
        monkeypatch.setattr(aa, "es_pasada_diurna_descartada", lambda *a: False)
        monkeypatch.setattr(aa, "_csv_ultima_fecha", lambda p: HOY.isoformat())
        monkeypatch.setattr(aa, "OUTDIR", str(tmp_path))
        monkeypatch.setattr(aa, "leer_ceses", lambda *a, **k: ([], None))
        aa.main()
        return json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))
    return _correr


def test_con_la_via_en_modis_decide_la_via_y_k_se_informa_aparte(correr):
    out = correr(con_via=True)
    assert out["detector"]["vigente"] == "K"
    assert out["detector"]["vigente_por_sensor"] == {"VIIRS375": "K", "VIIRS750": "K", "MODIS": "VIA_MODIS"}
    assert out["detector"]["frontera_via_modis"] == _dia(15)
    r = out["recall"]["MODIS"]
    assert (r["recall_crater_pct"], r["n_noches"]) == (0.0, 16)                  # la vía, no la mezcla
    assert out["por_detector"]["K"]["recall"]["MODIS"]["recall_crater_pct"] == 100.0
    assert out["por_detector"]["VIA_MODIS"]["recall"]["MODIS"]["n_noches"] == 16
    assert any(f.startswith("recall MODIS") and "detector VIA_MODIS" in f for f in out["flags"])
    prot = [f for f in out["flags"] if f.startswith("alerta protegida sin publicar")]
    assert len(prot) == 1 and "detector VIA_MODIS" in prot[0]
    p = out["alertas_protegidas"]["lista"][0]
    assert p["detector"] == "VIA_MODIS"


def test_mutacion_sin_la_via_la_misma_escena_es_k_y_no_hay_claves_nuevas(correr):
    """Control: sin records de la vía, la salida es la de S156 (las claves nuevas sólo aparecen con la vía)."""
    out = correr(con_via=False)
    assert out["detector"] == {"vigente": "K", "frontera_datos": FRONTERA, "regla_minimas": "SN"}
    assert "VIA_MODIS" not in out["por_detector"]
    r = out["recall"]["MODIS"]
    assert r["n_noches"] == 36
    p = out["alertas_protegidas"]["lista"][0]
    assert p["detector"] == "K"


# ------------------------------------------------------------------ S173, hallazgo 205
# POR QUÉ (experiments/_s173_aud/f2/INFORME.md §3, 205; confirmado por V2): la magnitud por régimen (S157) ordena los
# regímenes con la tupla REGIMENES y `regimen_de_pasada` devuelve "VIA_MODIS" para una pasada MODIS de la vía. Sin
# "VIA_MODIS" en la tupla, la primera noche en que la vía publique MODIS con alerta de MIROVA hacía caer main() con
# ValueError antes de escribir latest.json: sin informe y sin issue. La prueba de punta a punta de arriba no lo veía
# porque en su escena la vía no publica (vrp 0): estas dos sí la hacen publicar.
def test_todo_regimen_que_devuelve_regimen_de_pasada_esta_en_regimenes():
    casos = [("2026-08-28 22:59", None, None), ("2026-08-28 23:00", None, None), ("2026-09-05 05:00", None, None),
             ("2026-10-01 05:00", "MODIS", None), ("2026-11-06 07:20", "MODIS", "2026-11-06"),
             ("2026-11-06 05:00", "VIIRS375", "2026-11-06")]
    vistos = {aa.regimen_de_pasada(dt, FRONTERA, s, v) for dt, s, v in casos}
    assert "VIA_MODIS" in vistos
    assert vistos <= set(aa.REGIMENES), vistos - set(aa.REGIMENES)


def test_magnitud_por_regimen_con_la_via_publicando_en_noche_con_alerta():
    mir = {("Villarrica", "MODIS", "2026-11-06"): 2.0, ("Villarrica", "MODIS", "2026-11-04"): 2.0}
    recs = {"Villarrica": [_rec("2026-11-06", vrp=1.5, via=True), _rec("2026-11-04", vrp=1.0)]}
    res = aa.nuestros_por_noche(recs, ("2026-10-01", "2026-11-30"), FRONTERA, via_modis="2026-11-06")
    est = aa.estratificar_magnitud(mir, res["ours"], FRONTERA, "K", via_modis="2026-11-06")
    reg = est["por_regimen"]["Villarrica|MODIS"]
    assert list(reg) == ["K", "VIA_MODIS"]
    assert reg["VIA_MODIS"]["n_noches"] == 1 and reg["VIA_MODIS"]["ratio_mediano"] == 0.75
    assert reg["K"]["n_noches"] == 1 and reg["K"]["ratio_mediano"] == 0.5


def test_main_no_cae_cuando_la_via_publica_modis_en_noches_con_alerta(correr):
    out = correr(con_via=True, via_publica=True)
    assert out["detector"]["vigente_por_sensor"]["MODIS"] == "VIA_MODIS"
    r = out["recall"]["MODIS"]
    assert (r["recall_crater_pct"], r["n_noches"]) == (100.0, 16)
    reg = out["magnitud_publicada_by_vol_sensor_regimen"]["Villarrica|MODIS"]
    assert list(reg) == ["K", "VIA_MODIS"]
    assert reg["VIA_MODIS"]["n_noches"] == 16 and reg["K"]["n_noches"] == 20
