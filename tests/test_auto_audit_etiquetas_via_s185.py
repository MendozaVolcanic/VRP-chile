# -*- coding: utf-8 -*-
"""S185: el auto-audit semanal nombra al detector vigente por lo que es (la vía «código MIROVA» de cada sensor), no «K».

POR QUÉ (dos verificaciones independientes de la semana del 2026-11-15, D:\\vrp-trabajo\\temporales\\s185_aparte y
s185_audit_verif). Desde 2026-11-02/11 los tres sensores deciden con la vía y K quedó de guardia, pero
`detector_vigente(frontera)` sigue devolviendo «K» y el audit lo copiaba a `detector.vigente`,
`falsas_publicaciones.detector`, `plataformas.aparte.detector`, la consola y el texto del issue. Además la raíz de
latest.json publicaba `magnitud_ratio_by_vol` y `magnitud_ratio_by_npix` vacías porque las copiaba del bloque K, que con
la vía en los tres sensores no tiene noches (un {} se lee como «sin dato»). Los números que deciden flags (recall,
magnitud publicada, protegidas) ya eran los de la vía: este cambio sólo corrige etiquetas y esas dos claves, y los
tests lo fijan con un control (los flags y el recall salen idénticos al camino de por-sensor).
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
SENSOR_DE = {"MODIS": "MODIS_AQUA", "VIIRS375": "VIIRS_NOAA20", "VIIRS750": "VIIRS_NOAA20_750"}
TODAS = {s: "2026-11-01" for s in aa.SENSORS}
HOY = datetime.now(timezone.utc).date()


def _dia(n):
    return (HOY - timedelta(days=n)).isoformat()


# ------------------------------------------------------------------ piezas
def test_etiqueta_sin_via_es_el_vigente_tal_cual():
    assert aa.etiqueta_vigente("K", {}) == "K"
    assert aa.etiqueta_vigente("K", None) == "K"
    assert aa.etiqueta_vigente("C0", {}) == "C0"


def test_etiqueta_con_la_via_en_los_tres_sensores_no_dice_k():
    et = aa.etiqueta_vigente("K", TODAS)
    assert set(et.split("+")) == {"VIA_MODIS", "VIA_V375", "VIA_V750"}
    assert "K" not in et.split("+")


def test_etiqueta_con_la_via_en_algunos_sensores_los_nombra_a_todos():
    assert aa.etiqueta_vigente("K", {"MODIS": "2026-11-01"}) == "VIA_MODIS+K"
    assert aa.etiqueta_vigente("K", "2026-11-01") == "VIA_MODIS+K", "la fecha en texto sigue siendo la de MODIS"
    assert aa.etiqueta_detector({"MODIS": "K", "VIIRS375": "K", "VIIRS750": "K"}) == "K"


def test_evaluacion_vigente_sin_bloque_k_toma_la_base_de_la_via():
    """Con la vía en los tres sensores `por_detector` ya no trae K: no puede caer en un KeyError."""
    def ev(tag):
        return {"detector": tag, "recall": {s: {"tag": tag} for s in aa.SENSORS},
                "magnitud_publicada_by_vol_sensor": {f"Lascar|{s}": tag for s in aa.SENSORS}}
    por = {"VIA_MODIS": ev("modis"), "VIA_V375": ev("v375"), "VIA_V750": ev("v750")}
    r = aa.evaluacion_vigente(por, "K", TODAS)
    assert r["recall"] == {"MODIS": {"tag": "modis"}, "VIIRS375": {"tag": "v375"}, "VIIRS750": {"tag": "v750"}}
    assert set(r["detector"].split("+")) == {"VIA_MODIS", "VIA_V375", "VIA_V750"}


# ------------------------------------------------------------------ evaluar_detector con un detector por sensor
def _records():
    recs = []
    for n in range(0, 20):
        for b, sensor in SENSOR_DE.items():
            r = {"datetime_utc": f"{_dia(n)} 05:00", "sensor": sensor, "distance_class": "summit",
                 "primary_cluster": {"vrp_mw": 1.0, "centroid_dist_km": 1.0}, "anomaly_pixels": [{}],
                 "regimen": {"codigo_sha": SHA}, "via_codigo_mirova": True}
            recs.append(r)
    return {"Villarrica": recs}


def test_evaluar_detector_por_sensor_da_los_mismos_numeros_y_la_etiqueta_de_la_via():
    """`plataformas.aparte` llamaba evaluar_detector con el vigente global (K) y sin via_modis: el número era el de la
    vía y la etiqueta «K». Con `por_sensor` el número no cambia y la etiqueta es la de la vía."""
    records = _records()
    via = aa.fronteras_via(records)
    assert set(via) == set(aa.SENSORS)
    nuestros = aa.nuestros_por_noche(records, (_dia(30), _dia(0)), FRONTERA, via_modis=via)
    mir = {("Villarrica", b, _dia(n)): 0.5 for n in range(0, 20) for b in aa.SENSORS}
    antes = aa.evaluar_detector(mir, nuestros["ours"], nuestros["vistos"], "K", FRONTERA)
    despues = aa.evaluar_detector(mir, nuestros["ours"], nuestros["vistos"], "K", FRONTERA, via_modis=via,
                                  por_sensor={s: aa.VIA_POR_SENSOR[s] for s in aa.SENSORS})
    assert antes["detector"] == "K"
    assert "K" not in despues["detector"].split("+")
    sin_etiqueta = ("recall", "magnitud_ratio_by_vol", "magnitud_ratio_by_npix", "magnitud_publicada_by_vol_sensor")
    assert {k: antes[k] for k in sin_etiqueta} == {k: despues[k] for k in sin_etiqueta}
    assert despues["magnitud_ratio_by_vol"], "el escenario tiene que dar magnitud, si no la comparación no prueba nada"
    # control: pedir un detector que no es el de la noche no deja noche alguna (el filtro por sensor funciona)
    vacio = aa.evaluar_detector(mir, nuestros["ours"], nuestros["vistos"], "K", FRONTERA, via_modis=via,
                                por_sensor={s: "K" for s in aa.SENSORS})
    assert vacio["magnitud_ratio_by_vol"] == {} and vacio["recall"]["MODIS"]["n_noches"] == 0


# ------------------------------------------------------------------ main() de punta a punta
def _brec(fecha, b, pub, lab, sensor):
    dt = datetime.strptime(f"{fecha} 05:00", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": "Villarrica", "b": b, "dt": dt, "noche": fecha, "pub": pub, "lab": lab, "lab_original": lab,
            "sha": SHA, "z": 20.0, "sensor": sensor}


@pytest.fixture
def salida(monkeypatch, tmp_path, capsys):
    records = _records()
    alertas = [{"volcano": "Villarrica", "sensor_bucket": b, "fecha_utc": _dia(n) + " 05:00:00", "vrp_mw": 0.5}
               for n in range(0, 20) for b in aa.SENSORS]
    banco = ([_brec(_dia(n), b, True, "pos", SENSOR_DE[b]) for n in range(0, 20) for b in aa.SENSORS], [])
    monkeypatch.setattr(aa, "leer_frontera_k", lambda *a: FRONTERA)
    monkeypatch.setattr(aa, "alertas_mirova", lambda *a, **k: alertas)
    monkeypatch.setattr(aa, "cargar_filas_referencia", lambda: None)
    monkeypatch.setattr(aa, "cargar_records", lambda: (records, {"parse_errors": [], "duplicates_total": 0}))
    monkeypatch.setattr(aa, "banco_ventana", lambda win: banco)
    monkeypatch.setattr(aa, "_coords_por_volcan", lambda: {"Villarrica": (-39.42, -71.94)})
    monkeypatch.setattr(aa, "es_pasada_diurna_descartada", lambda *a: False)
    monkeypatch.setattr(aa, "_csv_ultima_fecha", lambda p: HOY.isoformat())
    monkeypatch.setattr(aa, "OUTDIR", str(tmp_path))
    monkeypatch.setattr(aa, "leer_ceses", lambda *a, **k: ([], None))
    aa.main()
    return json.loads((tmp_path / "latest.json").read_text(encoding="utf-8")), capsys.readouterr().out


def test_con_la_via_en_los_tres_sensores_las_etiquetas_no_dicen_k(salida):
    out, consola = salida
    vias = {"VIA_MODIS", "VIA_V375", "VIA_V750"}
    assert set(out["detector"]["vigente"].split("+")) == vias
    assert set(out["falsas_publicaciones"]["detector"].split("+")) == vias
    assert out["detector"]["vigente_por_sensor"] == {"MODIS": "VIA_MODIS", "VIIRS750": "VIA_V750", "VIIRS375": "VIA_V375"}
    assert "detector vigente K " not in consola, "la línea de consola sigue llamando K al vigente"
    assert "VIA_MODIS" in consola.splitlines()[0] or any("detector vigente" in l and "VIA_MODIS" in l
                                                         for l in consola.splitlines())


def test_con_la_via_en_los_tres_sensores_no_hay_bloque_k_vacio(salida):
    out, consola = salida
    assert set(out["por_detector"]) == {"VIA_MODIS", "VIA_V375", "VIA_V750"}
    assert "[K]" not in consola


def test_las_magnitudes_de_la_raiz_salen_del_detector_vigente_y_no_vacias(salida):
    out, _ = salida
    por_vol = out["magnitud_ratio_by_vol"]
    assert por_vol and por_vol["Villarrica"]["n_noches"] == 60            # 20 noches x 3 sensores
    assert out["magnitud_ratio_by_npix"] and sum(b["n_noches"] for b in out["magnitud_ratio_by_npix"].values()) == 60
    # es la suma de lo que dice cada detector de la vía: ninguno aporta de más ni de menos
    suma = sum(e["magnitud_ratio_by_vol"]["Villarrica"]["n_noches"] for e in out["por_detector"].values())
    assert suma == por_vol["Villarrica"]["n_noches"]


def test_control_flags_y_recall_no_cambian_con_las_etiquetas(salida):
    """Los números que deciden son los de por-sensor: recall de cada sensor = el de su bloque de la vía."""
    out, _ = salida
    for s, det in aa.VIA_POR_SENSOR.items():
        assert out["recall"][s] == out["por_detector"][det]["recall"][s]
    assert out["magnitud_publicada_by_vol_sensor"]
    for k, m in out["magnitud_publicada_by_vol_sensor"].items():
        assert m == out["por_detector"][aa.VIA_POR_SENSOR[k.split("|")[1]]]["magnitud_publicada_by_vol_sensor"][k]


def test_el_texto_del_issue_ya_no_manda_a_leer_la_clave_detector_como_k():
    yml = (ROOT / ".github" / "workflows" / "audit-weekly.yml").read_text(encoding="utf-8")
    assert "Juzga SOLO el detector vigente de cada sensor" in yml and "vigente_por_sensor" in yml
    assert "(clave detector de latest.json)" not in yml
