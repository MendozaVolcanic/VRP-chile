# -*- coding: utf-8 -*-
"""S176: el auto-audit semanal y la vigilancia de K separan la vía de cada VIIRS de K.

POR QUÉ (diseño docs/superpowers/specs/2026-11-08-encendido-v375e-design.md, decisiones 4 y 7). El audit llama «K» a todo
record con `codigo_sha`, y lo mismo la vigilancia de K. Los records de la vía de VIIRS también lo traen. Sin un detector
propio la ventana de 60 días promediaría dos detectores como una sola serie (el defecto que S156 arregló para C0 y K) y,
peor, una protegida que la vía calla y el laboratorio publica abriría el issue que pide revertir K, por una pérdida que no
es de K. Las bandas NO se recalibran antes de ver datos (A115). Sin records de la vía en VIIRS, todo sale igual que hoy.
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
import scripts.vigilancia_sombra as vs  # noqa: E402

FRONTERA = "2026-09-18"
SHA = "f" * 40
V375, V750 = "VIIRS_NOAA20", "VIIRS_NOAA20_750"


def _rec(fecha, sensor=V375, vrp=1.0, via=None, sha=True, hora="05:00"):
    r = {"datetime_utc": f"{fecha} {hora}", "sensor": sensor, "distance_class": "summit",
         "primary_cluster": {"vrp_mw": vrp, "centroid_dist_km": 1.0} if vrp else {},
         "anomaly_pixels": [{}] if vrp else []}
    if sha:
        r["regimen"] = {"codigo_sha": SHA}
    if via is not None:
        r["via_codigo_mirova"] = via
    return r


# ------------------------------------------------------------------ piezas
def test_las_fronteras_de_la_via_salen_de_los_datos_por_sensor():
    recs = {"Lascar": [_rec("2026-11-01"), _rec("2026-11-06", via=True), _rec("2026-11-05", via="sin_grilla"),
                       _rec("2026-11-08", sensor=V750, via=True), _rec("2026-11-02", sensor="MODIS_AQUA", via=True)],
            "Isluga": [_rec("2026-11-04", via=True)]}
    assert aa.fronteras_via(recs) == {"VIIRS375": "2026-11-04", "VIIRS750": "2026-11-08", "MODIS": "2026-11-02"}
    assert aa.fronteras_via({"Lascar": [_rec("2026-11-01"), _rec("2026-11-05", via="sin_grilla")]}) == {}
    # la frontera de MODIS sigue sin mirar VIIRS
    assert aa.frontera_via_modis(recs) == "2026-11-02"


def test_claves_de_la_via_de_todos_los_sensores():
    recs = {"Lascar": [_rec("2026-11-06", via=True), _rec("2026-11-07", sensor=V750, via=True),
                       _rec("2026-11-05", via="sin_grilla"), _rec("2026-11-04")]}
    assert aa.claves_via(recs) == {("Lascar", V375, "2026-11-06 05:00"), ("Lascar", V750, "2026-11-07 05:00")}
    assert aa.claves_via_modis(recs) == set()


@pytest.mark.parametrize("sensor,esperado", [(V375, "VIA_V375"), (V750, "VIA_V750"), ("MODIS_AQUA", "VIA_MODIS")])
def test_detector_de_record_distingue_la_via_de_cada_sensor(sensor, esperado):
    assert aa.detector_de_record(_rec("2026-11-06", sensor=sensor, via=True), FRONTERA) == esperado
    assert aa.detector_de_record(_rec("2026-11-06", sensor=sensor), FRONTERA) == "K"
    assert aa.detector_de_record(_rec("2026-11-06", sensor=sensor, via="sin_grilla"), FRONTERA) == "K"


def test_detector_de_noche_por_sensor():
    fr = {"VIIRS375": "2026-11-06"}
    assert aa.detector_de_noche("2026-11-06", FRONTERA, "VIIRS375", fr) == "VIA_V375"
    assert aa.detector_de_noche("2026-11-05", FRONTERA, "VIIRS375", fr) == "K"
    assert aa.detector_de_noche("2026-11-06", FRONTERA, "VIIRS750", fr) == "K", "la vía de 375 no es la de 750"
    assert aa.detector_de_noche("2026-11-06", FRONTERA, "MODIS", fr) == "K"
    assert aa.detector_vigente_de("VIIRS375", "K", fr) == "VIA_V375"
    assert aa.detector_vigente_de("VIIRS750", "K", fr) == "K"
    assert aa.detector_vigente_de("VIIRS750", "K", {"VIIRS750": "2026-11-06"}) == "VIA_V750"


def test_una_frontera_en_texto_sigue_siendo_la_de_modis():
    """Los llamadores de S172 pasan la fecha de MODIS en texto: sigue valiendo."""
    assert aa.detector_de_noche("2026-11-06", FRONTERA, "MODIS", "2026-11-06") == "VIA_MODIS"
    assert aa.detector_de_noche("2026-11-06", FRONTERA, "VIIRS375", "2026-11-06") == "K"
    assert aa.detector_vigente_de("MODIS", "K", "2026-11-06") == "VIA_MODIS"


def test_detector_del_banco_por_clave_de_la_via():
    dt = datetime(2026, 11, 6, 5, 0, tzinfo=timezone.utc)
    r = {"vol": "Lascar", "sensor": V750, "dt": dt, "noche": "2026-11-06", "sha": SHA}
    via = {("Lascar", V750, "2026-11-06 05:00")}
    assert aa._detector_banco(r, FRONTERA, via) == "VIA_V750"
    assert aa._detector_banco(r, FRONTERA) == "K"
    assert aa._detector_banco(dict(r, sensor=V375), FRONTERA, via) == "K"


def test_regimen_de_pasada_con_la_via_de_viirs():
    assert aa.regimen_de_pasada("2026-11-06 05:00", FRONTERA, "VIIRS375", {"VIIRS375": "2026-11-06"}) == "VIA_V375"
    assert aa.regimen_de_pasada("2026-11-06 05:00", FRONTERA, "VIIRS750", {"VIIRS750": "2026-11-06"}) == "VIA_V750"
    assert aa.regimen_de_pasada("2026-11-05 05:00", FRONTERA, "VIIRS375", {"VIIRS375": "2026-11-06"}) == "K"
    assert {"VIA_V375", "VIA_V750"} <= set(aa.REGIMENES), "si faltan, sorted(REGIMENES.index) hace caer el audit (205)"
    assert {"VIA_V375", "VIA_V750"} <= set(aa.DETECTORES)


def test_una_noche_de_la_via_se_evalua_solo_con_records_de_la_via():
    recs = {"Lascar": [_rec("2026-11-06", via=True), _rec("2026-11-06", via="sin_grilla", hora="03:10"), _rec("2026-11-04")]}
    res = aa.nuestros_por_noche(recs, ("2026-10-01", "2026-11-30"), FRONTERA, via_modis={"VIIRS375": "2026-11-06"})
    assert res["fuera_de_detector"] == {"K en noche VIA_V375": 1}
    assert res["n_records_por_detector"] == {"VIA_V375": 1, "K": 2}


def test_evaluacion_vigente_toma_cada_sensor_de_su_detector():
    def ev(tag):
        return {"recall": {s: {"tag": tag} for s in aa.SENSORS},
                "magnitud_publicada_by_vol_sensor": {f"Lascar|{s}": tag for s in aa.SENSORS}}
    por = {"K": ev("k"), "VIA_MODIS": ev("modis"), "VIA_V375": ev("v375")}
    r = aa.evaluacion_vigente(por, "K", {"MODIS": "2026-11-02", "VIIRS375": "2026-11-06"})
    assert r["recall"]["MODIS"]["tag"] == "modis" and r["recall"]["VIIRS375"]["tag"] == "v375"
    assert r["recall"]["VIIRS750"]["tag"] == "k"
    assert r["magnitud_publicada_by_vol_sensor"] == {"Lascar|MODIS": "modis", "Lascar|VIIRS375": "v375", "Lascar|VIIRS750": "k"}
    assert r["detector_por_sensor"] == {"MODIS": "VIA_MODIS", "VIIRS375": "VIA_V375", "VIIRS750": "K"}
    assert aa.evaluacion_vigente(por, "K", {}) is por["K"], "sin vías, el vigente tal cual"


def test_sensores_sin_juzgar_por_la_via_de_viirs():
    rec = {s: {"n_noches": 2} for s in aa.SENSORS}
    e = aa.sensores_sin_juzgar(rec, {}, [], {}, via_modis={"VIIRS375": "2026-11-06", "VIIRS750": "2026-11-07"})
    assert set(e) == {"VIIRS375", "VIIRS750"}
    assert e["VIIRS375"]["detector"] == "VIA_V375" and e["VIIRS750"]["detector"] == "VIA_V750"
    assert "VIA_V375" in e["VIIRS375"]["aviso"]
    assert aa.sensores_sin_juzgar(rec, {}, [], {}, via_modis={}) == {}


# ------------------------------------------------------------------ main() de punta a punta
HOY = datetime.now(timezone.utc).date()


def _dia(n):
    return (HOY - timedelta(days=n)).isoformat()


def _brec(fecha, b, pub, lab, sensor):
    dt = datetime.strptime(f"{fecha} 05:00", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": "Villarrica", "b": b, "dt": dt, "noche": fecha, "pub": pub, "lab": lab, "lab_original": lab,
            "sha": SHA, "z": 20.0, "sensor": sensor}


def _escenario(con_via, sensor=V375, bucket="VIIRS375", n_reciente=16):
    records, alertas = [], []
    for n in range(0, 36):
        d = _dia(n)
        alertas.append({"volcano": "Villarrica", "sensor_bucket": bucket, "fecha_utc": d + " 05:00:00", "vrp_mw": 0.5})
        reciente = n < n_reciente
        records.append(_rec(d, sensor=sensor, vrp=0.0 if reciente else 1.0, via=(True if (reciente and con_via) else None)))
    banco = ([_brec(_dia(2), bucket, False, "pos", sensor)],
             [{"volcano": "Villarrica", "sensor_bucket": bucket, "fecha_utc": _dia(2) + " 05:00:00", "vrp_mw": 2.0,
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


@pytest.mark.parametrize("sensor,bucket,det", [(V375, "VIIRS375", "VIA_V375"), (V750, "VIIRS750", "VIA_V750")])
def test_con_la_via_en_un_viirs_decide_la_via_en_ese_sensor(correr, sensor, bucket, det):
    out = correr(con_via=True, sensor=sensor, bucket=bucket)
    assert out["detector"]["vigente"] == "K"
    assert out["detector"]["vigente_por_sensor"][bucket] == det
    assert out["detector"]["fronteras_via"] == {bucket: _dia(15)}
    assert "frontera_via_modis" not in out["detector"], "esa clave es la de MODIS"
    r = out["recall"][bucket]
    assert (r["recall_crater_pct"], r["n_noches"]) == (0.0, 16)                  # la vía, no la mezcla
    assert out["por_detector"]["K"]["recall"][bucket]["recall_crater_pct"] == 100.0
    assert out["por_detector"][det]["recall"][bucket]["n_noches"] == 16
    assert any(f.startswith(f"recall {bucket}") and f"detector {det}" in f for f in out["flags"])
    assert out["alertas_protegidas"]["lista"][0]["detector"] == det


def test_control_sin_la_via_la_misma_escena_es_k_y_no_hay_claves_nuevas(correr):
    out = correr(con_via=False)
    assert out["detector"] == {"vigente": "K", "frontera_datos": FRONTERA, "regla_minimas": "SN"}
    assert "VIA_V375" not in out["por_detector"] and out["recall"]["VIIRS375"]["n_noches"] == 36
    assert out["alertas_protegidas"]["lista"][0]["detector"] == "K"


def test_con_via_solo_en_modis_no_aparece_la_clave_de_viirs(correr):
    """VPR967-04: la situacion de produccion hoy. Sin via de VIIRS, `fronteras_via` no se escribe y latest.json queda igual."""
    out = correr(con_via=True, sensor="MODIS_AQUA", bucket="MODIS")
    assert out["detector"]["frontera_via_modis"] == _dia(15)
    assert "fronteras_via" not in out["detector"]


def test_las_bandas_no_se_recalibran():
    """A115: un umbral elegido después del dato no es pre-registro. Los valores de hoy, copiados: si cambian, es a propósito
    y con un PR que lo diga, no de pasada con el encendido."""
    assert aa.RECALL_MIN == {"VIIRS375": 93.4, "VIIRS750": 79.5, "MODIS": 95.0}
    assert aa.MIN_N_RECALL == 15 and aa.MIN_N_RATIO == 5
    assert aa.FALSAS_BANDA_TERMINADO == {"focal": 10.0, "nevado": 15.0}


# ------------------------------------------------------------------ vigilancia de K (scripts/vigilancia_sombra.py)
def test_la_vigilancia_de_k_saca_la_via_de_cualquier_sensor():
    recs = {"Lascar": [_rec("2026-11-06", via=True), _rec("2026-11-06", sensor=V750, via=True, hora="05:30")]}
    import types
    aa_falso = types.SimpleNamespace(claves_via=aa.claves_via, cargar_records=lambda: (recs, {}))
    orig, vs.aa = vs.aa, aa_falso
    try:
        assert vs.claves_via() == {("Lascar", V375, "2026-11-06 05:00"), ("Lascar", V750, "2026-11-06 05:30")}
    finally:
        vs.aa = orig


def test_la_frescura_de_k_no_se_exige_en_el_sensor_que_paso_a_la_via():
    assert vs.sensores_de_k(set()) == list(vs.aa.SENSORS)
    assert set(vs.sensores_de_k({("Lascar", V375, "x")})) == {"MODIS", "VIIRS750"}
    assert set(vs.sensores_de_k({("Lascar", V750, "x"), ("Lascar", "MODIS_AQUA", "y")})) == {"VIIRS375"}
