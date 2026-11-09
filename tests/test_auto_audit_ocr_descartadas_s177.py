# -*- coding: utf-8 -*-
"""S177 (VPR970-03, prueba del verificador del PR #970): la cuenta de OCR descartado llega a latest.json con la
ventana y la tabla correctas, y no cambia veredicto, flags ni historial."""
import copy
import json
from datetime import timedelta

import tests.test_auto_audit_cenit_s157 as t

aa = t.aa


def _correr(tmp_path, monkeypatch, nombre, alertas_extra, ref, anular=False):
    records, alertas, banco = t._insumo()
    alertas = alertas + copy.deepcopy(alertas_extra)
    out = tmp_path / nombre
    monkeypatch.setattr(aa, "OUTDIR", str(out))
    monkeypatch.setattr(aa, "datetime", t._Reloj)
    monkeypatch.setattr(aa, "leer_frontera_k", lambda *a, **k: t.FRONTERA)
    monkeypatch.setattr(aa, "alertas_mirova", lambda *a, **k: copy.deepcopy(alertas))
    monkeypatch.setattr(aa, "_coords_por_volcan",
                        lambda: {"NevadosDeChillan": (-36.86, -71.38), "Villarrica": (-39.42, -71.94)})
    monkeypatch.setattr(aa, "cargar_filas_referencia", lambda: copy.deepcopy(ref))
    monkeypatch.setattr(aa, "cargar_records",
                        lambda: (copy.deepcopy(records), {"parse_errors": [], "duplicates_total": 0}))
    monkeypatch.setattr(aa, "banco_ventana", lambda win: (copy.deepcopy(banco), []))
    monkeypatch.setattr(aa, "_csv_ultima_fecha", lambda p: "2026-10-19")
    if anular:
        monkeypatch.setattr(aa.cm, "contar_ocr_descartadas", lambda *a, **k: {})
    aa.main()
    latest = json.loads((out / "latest.json").read_text(encoding="utf-8"))
    hist = [json.loads(x) for x in (out / "history.jsonl").read_text(encoding="utf-8").splitlines()]
    return latest, hist


def _fila(vol, sensor, fecha, vrp, tipo, source):
    return {"volcano": vol, "sensor_bucket": sensor, "fecha_utc": fecha, "vrp_mw": vrp, "tipo": tipo, "source": source,
            "dist_km": 1.0}


def test_la_cuenta_usa_la_ventana_y_no_cambia_el_veredicto(tmp_path, monkeypatch, capsys):
    hoy = t.HOY.date()
    dentro = (hoy - timedelta(days=10)).isoformat()
    dentro2 = (hoy - timedelta(days=11)).isoformat()
    fuera = (hoy - timedelta(days=aa.WINDOW_DAYS + 20)).isoformat()
    extra = [_fila("NevadosDeChillan", "MODIS", dentro + " 05:00:00", 3.0, "ALERTA_TERMICA_OCR", "OCR"),   # tabla RUTINA
             _fila("NevadosDeChillan", "MODIS", fuera + " 05:00:00", 3.0, "ALERTA_TERMICA_OCR", "OCR"),    # fuera de ventana
             _fila("Villarrica", "VIIRS750", dentro2 + " 05:00:00", 4.0, "ALERTA_TERMICA_OCR", "OCR")]     # tabla de alerta
    ref = [_fila("NevadosDeChillan", "MODIS", dentro + " 05:01:30", 0.0, "RUTINA", "CONS"),
           _fila("NevadosDeChillan", "MODIS", fuera + " 05:01:30", 0.0, "RUTINA", "CONS"),
           _fila("Villarrica", "VIIRS750", dentro2 + " 05:00:30", 4.2, "ALERTA_TERMICA", "CONS")]
    con, h_con = _correr(tmp_path, monkeypatch, "con", extra, ref)
    assert con["cobertura"]["ocr_descartadas_por_tabla"] == {
        "MODIS": {"descartadas": 1, "con_alerta_en_tabla": 0, "sin_alerta_en_tabla": 1, "protegidas_sin_alerta_en_tabla": 1},
        "VIIRS750": {"descartadas": 1, "con_alerta_en_tabla": 1, "sin_alerta_en_tabla": 0, "protegidas_sin_alerta_en_tabla": 0}}
    assert "OCR DESCARTADO CON TABLA SIN ALERTA: MODIS 1 filas, 1 protegidas" in capsys.readouterr().out
    sin, h_sin = _correr(tmp_path, monkeypatch, "sin", extra, ref, anular=True)
    a, b = copy.deepcopy(con), copy.deepcopy(sin)
    for d in (a, b):
        d["cobertura"].pop("ocr_descartadas_por_tabla")
        d.pop("generated_utc", None)
    assert a == b and h_con == h_sin
