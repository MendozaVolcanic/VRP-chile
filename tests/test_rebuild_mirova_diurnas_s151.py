# -*- coding: utf-8 -*-
"""Alertas DIURNAS de MIROVA en el tablero (S151, aprobado por Nicolas el 2026-10-15).

POR QUE. La replica es solo nocturna, pero MIROVA publica alertas de dia (Campus et al. 2022, Sensors 22:1713,
p. 16 a 17). De dia el infrarrojo medio suma luz solar reflejada, y parte de esas alertas son reflejo en nubes y
no calor (A76: Lascar 2026-06-15 17:24, 760 MW; experiments/_s151_alertas_diurnas/README.md). Nicolas aprobo
mostrarlas como referencia marcada "dia", sin tocar el pipeline.

Lo que se fija aca:
- la tabla de MIROVA siempre entro a `records` a cualquier hora: sigue ahi, ahora con `dia: true` en las
  diurnas, y las nocturnas quedan byte a byte iguales (sin la clave);
- las diurnas del OCR (antes descartadas) van a `records_dia_ocr`, NUNCA a `records`: asi ningun consumidor de
  `records` (metricas del tablero, confirmaciones, auditorias, experimentos) ve un numero distinto;
- una diurna del OCR que repite una pasada de la tabla sigue perdiendo contra la tabla;
- una diurna sin geometria (V31.1) entra con sus dos marcas;
- en el frontend, `records_dia_ocr` solo llega al dibujo, no a las metricas.

Las dos preguntas del instrumento: si el script volviera a meter el OCR diurno en `records`,
test_ocr_diurno_va_aparte falla; si lo siguiera descartando, el mismo test falla por el otro lado.
"""
import csv
import json
import re
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

# Nevados de Chillan (-36.9, -71.4): 05:00 UTC es de noche y 18:30 UTC es de dia en cualquier mes.
NOCHE, DIA = "2026-09-30 05:00:00", "2026-09-30 18:30:00"


def fila(cols, t, sensor, vrp, tipo, clase, dist="0.5", metodo=""):
    r = {c: "" for c in cols}
    r.update({"Fecha_Satelite_UTC": t, "Volcan": "Nevados de Chillan", "Sensor": sensor, "VRP_MW": vrp,
              "Distancia_km": dist, "Tipo_Registro": tipo, "Clasificacion Mirova": clase})
    if "Metodo_Validacion" in r:
        r["Metodo_Validacion"] = metodo
    return r


def escribir(path, cols, filas):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)


def armar(tmp_path, monkeypatch, cons_filas, ocr_filas):
    cons, ocr = tmp_path / "cons.csv", tmp_path / "ocr.csv"
    escribir(cons, CONS_COLS, cons_filas)
    escribir(ocr, OCR_COLS, ocr_filas)
    monkeypatch.setattr(rb, "REPO", tmp_path)
    rb.rebuild("NevadosDeChillan", "Nevados de Chillan", source=cons, ocr=ocr)
    return json.loads((tmp_path / "data" / "mirova" / "NevadosDeChillan.json").read_text(encoding="utf-8"))


def test_la_regla_es_la_del_pipeline():
    latlon = rb._coords("NevadosDeChillan")
    from datetime import datetime
    assert rb._es_dia(latlon, datetime(2026, 9, 30, 18, 30)) is True
    assert rb._es_dia(latlon, datetime(2026, 9, 30, 5, 0)) is False
    assert rb._es_dia(None, datetime(2026, 9, 30, 18, 30)) is False   # sin coordenadas: como antes, no se separa


def test_tabla_diurna_sigue_en_records_con_marca(tmp_path, monkeypatch):
    out = armar(tmp_path, monkeypatch, [
        fila(CONS_COLS, NOCHE, "VIIRS375", "2.54", "ALERTA_TERMICA", "Bajo", dist="0.84"),
        fila(CONS_COLS, DIA, "VIIRS375", "6.46", "ALERTA_TERMICA", "Bajo", dist="1.10"),
    ], [])
    por = {r["datetime_utc"]: r for r in out["records"]}
    assert por["2026-09-30 18:30"]["dia"] is True and por["2026-09-30 18:30"]["source"] == "consolidado"
    # la nocturna, byte a byte como antes: sin la clave nueva
    assert por["2026-09-30 05:00"] == {"datetime_utc": "2026-09-30 05:00", "sensor": "VIIRS375", "VRP_MW": 2.54,
                                       "distancia_km": 0.84, "clasificacion": "Bajo", "source": "consolidado"}
    assert out["records_dia_ocr"] == []


def test_ocr_diurno_va_aparte(tmp_path, monkeypatch):
    out = armar(tmp_path, monkeypatch, [], [
        fila(OCR_COLS, NOCHE, "VIIRS375", "3.0", "ALERTA_TERMICA_OCR", "Bajo"),
        fila(OCR_COLS, DIA, "VIIRS375", "760.6", "ALERTA_TERMICA_OCR", "Alto"),
    ])
    assert [r["datetime_utc"] for r in out["records"]] == ["2026-09-30 05:00"]
    assert "dia" not in out["records"][0]
    assert out["records_dia_ocr"] == [{"datetime_utc": "2026-09-30 18:30", "sensor": "VIIRS375", "VRP_MW": 760.6,
                                       "distancia_km": 0.5, "clasificacion": "Alto", "source": "ocr", "dia": True}]
    assert "nota_dia" in out


def test_la_tabla_manda_tambien_de_dia(tmp_path, monkeypatch):
    out = armar(tmp_path, monkeypatch,
                [fila(CONS_COLS, DIA, "VIIRS375", "6.46", "ALERTA_TERMICA", "Bajo")],
                [fila(OCR_COLS, DIA, "VIIRS375", "6.0", "ALERTA_TERMICA_OCR", "Bajo")])
    assert [(r["source"], r["VRP_MW"]) for r in out["records"]] == [("consolidado", 6.46)]
    assert out["records_dia_ocr"] == []


def test_sin_geometria_diurna_entra_con_sus_dos_marcas(tmp_path, monkeypatch):
    out = armar(tmp_path, monkeypatch, [], [
        fila(OCR_COLS, DIA, "VIIRS375", "4.24", rb.TIPO_SIN_GEOMETRIA, rb.CLASE_SIN_GEOMETRIA, dist="",
             metodo=rb.METODO_SIN_GEOMETRIA),
    ])
    assert out["records"] == []
    (r,) = out["records_dia_ocr"]
    assert r["dia"] is True and r["sin_geometria"] is True
    assert r["distancia_km"] is None and r["clasificacion"] == "SIN_GEOMETRIA"


def test_diurnas_no_alerta_siguen_fuera(tmp_path, monkeypatch):
    out = armar(tmp_path, monkeypatch, [], [
        fila(OCR_COLS, DIA, "VIIRS375", "0.3", "ALERTA_TERMICA_OCR", "NULO"),
        fila(OCR_COLS, DIA, "VIIRS375", "0.4", "FALSO_POSITIVO_OCR", "Bajo"),
    ])
    assert out["records"] == [] and out["records_dia_ocr"] == []


# ------------------------------------------------------------------ frontend
def _usos(src, nombre):
    # frontera de palabra (A92): `diaOcr` no debe contar dentro de `mirovaDiaOcr` ni al reves
    return re.findall(r"(?<![A-Za-z0-9_])" + re.escape(nombre) + r"(?![A-Za-z0-9_])", src)


def _codigo(src):
    """El fuente sin las lineas de comentario `//` (los comentarios nombran las claves para explicarlas)."""
    return "\n".join(ln for ln in src.splitlines() if not ln.strip().startswith("//"))


def test_frontend_el_ocr_diurno_solo_llega_al_dibujo():
    idx = _codigo((ROOT / "frontend" / "index.html").read_text(encoding="utf-8"))
    dia = _codigo((ROOT / "frontend" / "diario.html").read_text(encoding="utf-8"))
    # index: records_dia_ocr se carga en mirovaDiaOcr, y mirovaDiaOcr solo entra a mDia (el dibujo del sol)
    assert len(_usos(idx, "records_dia_ocr")) == 1
    usos_idx = [ln.strip() for ln in idx.splitlines() if _usos(ln, "mirovaDiaOcr")]
    assert len(usos_idx) == 3, usos_idx          # los dos objetos de allData y el filtro del dibujo
    assert any("const mDia" in ln for ln in usos_idx)
    assert not any("computeMetrics" in ln or "enrichWithMirovaConfirmation" in ln for ln in usos_idx)
    # las metricas siguen recibiendo mFiltered, que sale de mirovaRecords (= records, sin cambio)
    assert "computeMetrics(filtered, mFiltered," in idx
    # diario: records_dia_ocr viaja en .diaOcr y solo lo lee buildDatasets
    assert len(_usos(dia, "records_dia_ocr")) == 1
    cuerpo_stats = dia.split("function computeStats(", 1)[1].split("\nfunction ", 1)[0]
    assert not _usos(cuerpo_stats, "diaOcr") and not re.search(r"\.dia\b", cuerpo_stats)
    # las demas vistas no lo leen
    for f in ("mosaico.html", "comparacion.html", "experimental/index.html"):
        p = ROOT / "frontend" / f
        if p.exists():
            assert not _usos(p.read_text(encoding="utf-8"), "records_dia_ocr"), f
