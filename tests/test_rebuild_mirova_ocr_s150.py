# -*- coding: utf-8 -*-
"""S150 (auditoria S150, B-H4 y B-H5; decision de Nicolas 2026-10-09, opcion a). La linea de MIROVA del
tablero sale de data/mirova/<Volcan>.json, que arma scripts/rebuild_mirova_from_consolidado.py. Ese script
leia solo la tabla de MIROVA (no el OCR de sus imagenes) y solo las clases "Muy Bajo" y "Bajo", asi que en
la erupcion de Nevados de Chillan las dos pasadas mas fuertes del 2026-10-01 (9,0 MW y 10,0 MW "Moderado",
llegadas solo por OCR) no aparecian, aunque el tablero dice "CONS ∪ OCR".

Casos sinteticos con las columnas reales de los dos CSV. Las dos preguntas del instrumento: si el script
siguiera sin leer el OCR o descartara "Moderado", test_entra_el_ocr_y_moderado falla; si dejara pasar NULO
o FALSO_POSITIVO_OCR, test_no_entran_nulo_ni_falso_positivo falla.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import rebuild_mirova_from_consolidado as rb  # noqa: E402

CONS_COLS = ["timestamp", "Fecha_Satelite_UTC", "Fecha_Captura_Chile", "Volcan", "Sensor", "VRP_MW", "Distancia_km",
             "Tipo_Registro", "Clasificacion Mirova", "Ruta Foto", "Fecha_Proceso_GitHub", "Ultima_Actualizacion", "Editado"]
OCR_COLS = CONS_COLS + ["Color_Punto_Dist", "Confianza_Validacion", "Requiere_Verificacion", "Metodo_Validacion",
                        "Nota_Validacion", "Version_OCR", "Zenith_Sat_deg", "Azimut_Sat_deg", "Nivel_Anomalia_MIROVA",
                        "Confianza_Geometria"]


def fila(cols, t, sensor, vrp, tipo, clase, dist="0.5"):
    r = {c: "" for c in cols}
    r.update({"Fecha_Satelite_UTC": t, "Volcan": "Nevados de Chillan", "Sensor": sensor, "VRP_MW": vrp,
              "Distancia_km": dist, "Tipo_Registro": tipo, "Clasificacion Mirova": clase})
    return r


def escribir(path, cols, filas):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(filas)


def armar(tmp_path, monkeypatch):
    cons, ocr = tmp_path / "cons.csv", tmp_path / "ocr.csv"
    escribir(cons, CONS_COLS, [
        fila(CONS_COLS, "2026-10-01 06:18:00", "VIIRS", "7.06", "ALERTA_TERMICA", "Bajo"),
        fila(CONS_COLS, "2026-10-01 06:00:00", "VIIRS", "0", "RUTINA", "NULO"),
        fila(CONS_COLS, "2026-09-30 05:00:00", "VIIRS375", "0.3", "ALERTA_TERMICA", "FALSO POSITIVO"),
    ])
    escribir(ocr, OCR_COLS, [
        fila(OCR_COLS, "2026-10-01 06:00:00", "VIIRS", "10.0", "ALERTA_TERMICA_OCR", "Moderado"),
        fila(OCR_COLS, "2026-10-01 05:24:00", "VIIRS", "9.0", "ALERTA_TERMICA_OCR", "Bajo"),
        fila(OCR_COLS, "2026-10-01 06:18:00", "VIIRS", "7.0", "ALERTA_TERMICA_OCR", "Bajo"),   # la tabla manda
        fila(OCR_COLS, "2026-09-29 05:00:00", "VIIRS375", "0.4", "FALSO_POSITIVO_OCR", "Bajo", dist="19.5"),
        fila(OCR_COLS, "2026-09-28 04:42:00", "VIIRS375", "2.58", "ALERTA_TERMICA_OCR", "Medio"),   # version 21 del OCR
        fila(OCR_COLS, "2026-09-30 18:30:00", "VIIRS375", "760.6", "ALERTA_TERMICA_OCR", "Alto"),   # diurna: fuera (A76)
    ])
    monkeypatch.setattr(rb, "REPO", tmp_path)
    rb.rebuild("NevadosDeChillan", "Nevados de Chillan", source=cons, ocr=ocr)
    return json.loads((tmp_path / "data" / "mirova" / "NevadosDeChillan.json").read_text(encoding="utf-8"))


def test_entra_el_ocr_y_moderado(tmp_path, monkeypatch):
    out = armar(tmp_path, monkeypatch)
    por = {(r["datetime_utc"], r["sensor"]): r for r in out["records"]}
    assert por[("2026-10-01 06:00", "VIIRS")]["VRP_MW"] == 10.0
    assert por[("2026-10-01 06:00", "VIIRS")]["source"] == "ocr"
    assert por[("2026-10-01 06:00", "VIIRS")]["clasificacion"] == "Moderado"
    assert por[("2026-10-01 05:24", "VIIRS")]["source"] == "ocr"


def test_la_tabla_manda_sobre_el_ocr_en_la_misma_pasada(tmp_path, monkeypatch):
    out = armar(tmp_path, monkeypatch)
    r = [r for r in out["records"] if r["datetime_utc"] == "2026-10-01 06:18"]
    assert len(r) == 1 and r[0]["source"] == "consolidado" and r[0]["VRP_MW"] == 7.06


def test_no_entran_nulo_ni_falso_positivo(tmp_path, monkeypatch):
    out = armar(tmp_path, monkeypatch)
    assert {r["datetime_utc"] for r in out["records"]} == {"2026-10-01 06:00", "2026-10-01 05:24", "2026-10-01 06:18", "2026-09-28 04:42"}


def test_sin_ocr_se_comporta_como_antes(tmp_path, monkeypatch):
    cons = tmp_path / "cons.csv"
    escribir(cons, CONS_COLS, [fila(CONS_COLS, "2026-10-01 06:18:00", "VIIRS", "7.06", "ALERTA_TERMICA", "Bajo")])
    monkeypatch.setattr(rb, "REPO", tmp_path)
    rb.rebuild("NevadosDeChillan", "Nevados de Chillan", source=cons)
    out = json.loads((tmp_path / "data" / "mirova" / "NevadosDeChillan.json").read_text(encoding="utf-8"))
    assert [r["source"] for r in out["records"]] == ["consolidado"]


def test_medio_entra_y_la_diurna_no(tmp_path, monkeypatch):
    out = armar(tmp_path, monkeypatch)
    por = {r["datetime_utc"]: r for r in out["records"]}
    assert por["2026-09-28 04:42"]["clasificacion"] == "Medio"
    assert "2026-09-30 18:30" not in por
