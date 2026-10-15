# -*- coding: utf-8 -*-
"""Filas OCR de MIROVA sin geometria propia (V31.1 de Mirova-v1, 2026-10-15).

POR QUE. MIROVA mantiene una sola imagen de distancia (Dist.png) por volcan y sensor y la reemplaza en cada
pasada. Si el OCR de Mirova-v1 corre cuando MIROVA ya proceso la pasada siguiente, esa imagen es de la otra
pasada: la distancia y la clase no sirven, pero el VRP si, porque sale de la celda de la propia pasada en
Latest10NTI. Hasta V31 esas pasadas se perdian; caso: Nevados de Chillan 2026-10-15 05:00 UTC, 22,13 MW en
VIIRS 375, en erupcion, que la tabla latest.php nunca trajo. Desde V31.1 llegan con `Distancia_km` VACIA,
clase SIN_GEOMETRIA y metodo vrp_sin_geometria_propia.

Que se fija aca:
- la referencia las lee como alerta con distancia DESCONOCIDA (None), nunca 0 ni la de la nota;
- la lectura A del criterio de victoria las cuenta (no usa la distancia) y el etiquetador marca "pos";
- la serie de MIROVA del tablero (data/mirova/<Volcan>.json) las incluye con su marca, y las filas de hoy
  quedan byte a byte iguales (la clave nueva solo aparece en estas filas).
Las dos preguntas del instrumento: si la referencia leyera la nota o el 0 como distancia,
test_referencia_distancia_desconocida falla; si el rebuild las siguiera descartando por la clase,
test_rebuild_las_incluye_con_marca falla.
"""
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts import rebuild_mirova_from_consolidado as rb  # noqa: E402
from scripts.clase_mirova import alerta_protegida, pasadas_protegidas  # noqa: E402
from scripts.referencia_mirova_unificada import (cargar_referencia_unificada,  # noqa: E402
                                                 leer_pasadas)

CONS_COLS = ["timestamp", "Fecha_Satelite_UTC", "Fecha_Captura_Chile", "Volcan", "Sensor", "VRP_MW",
             "Distancia_km", "Tipo_Registro", "Clasificacion Mirova", "Ruta Foto", "Fecha_Proceso_GitHub",
             "Ultima_Actualizacion", "Editado"]
OCR_COLS = CONS_COLS + ["Color_Punto_Dist", "Confianza_Validacion", "Requiere_Verificacion", "Metodo_Validacion",
                        "Nota_Validacion", "Version_OCR", "Zenith_Sat_deg", "Azimut_Sat_deg",
                        "Nivel_Anomalia_MIROVA", "Confianza_Geometria"]


def _fila(cols, t, sensor, vrp, tipo, clase, dist="0.5", metodo="", nota=""):
    r = {c: "" for c in cols}
    r.update({"Fecha_Satelite_UTC": t, "Volcan": "Nevados de Chillan", "Sensor": sensor, "VRP_MW": vrp,
              "Distancia_km": dist, "Tipo_Registro": tipo, "Clasificacion Mirova": clase})
    if "Metodo_Validacion" in r:
        r["Metodo_Validacion"] = metodo
        r["Nota_Validacion"] = nota
    return r


def _sin_geo(t="2026-10-15 05:00:00", sensor="VIIRS375", vrp="22.13", nota=""):
    return _fila(OCR_COLS, t, sensor, vrp, "ALERTA_TERMICA_OCR", "SIN_GEOMETRIA", dist="",
                 metodo="vrp_sin_geometria_propia", nota=nota)


def _escribir(path, cols, filas):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)


# ------------------------------------------------------------------ referencia
def test_referencia_distancia_desconocida(tmp_path):
    ocr = tmp_path / "ocr.csv"
    # la nota trae un patron de distancia a proposito: no debe leerse (seria la de otra pasada)
    _escribir(ocr, OCR_COLS, [_sin_geo(nota="Estrella verde en Y=287 -> 1.08 km"),
                              _fila(OCR_COLS, "2026-10-14 13:05:00", "MODIS", "6.0", "ALERTA_TERMICA_OCR", "Bajo",
                                    dist="1.08", metodo="roi_temporal_v26")])
    por = {f["fecha_utc"]: f for f in leer_pasadas(ocr, "OCR", "principal")}
    f = por["2026-10-15 05:00:00"]
    assert f["tipo"] == "ALERTA_TERMICA_OCR" and f["vrp_mw"] == 22.13
    assert f["dist_km"] is None
    assert f["sin_geometria"] is True
    assert por["2026-10-14 13:05:00"]["sin_geometria"] is False
    assert por["2026-10-14 13:05:00"]["dist_km"] == 1.08


def test_lectura_a_la_cuenta_como_alerta_protegida(tmp_path):
    cons, ocr = tmp_path / "cons.csv", tmp_path / "ocr.csv"
    _escribir(cons, CONS_COLS, [_fila(CONS_COLS, "2026-10-15 06:00:00", "VIIRS375", "3.1", "ALERTA_TERMICA", "Bajo")])
    _escribir(ocr, OCR_COLS, [_sin_geo(), _sin_geo(vrp="0.4", t="2026-10-15 04:00:00")])
    ref = cargar_referencia_unificada(cons, ocr, respaldo_path=None, historico_path=None)
    f = next(x for x in ref if x["fecha_utc"].startswith("2026-10-15 05:00"))
    assert alerta_protegida(f, lectura="A")
    pp = pasadas_protegidas(ref)
    assert ("NevadosDeChillan", "VIIRS375", "2026-10-15 05:00") in pp
    assert ("NevadosDeChillan", "VIIRS375", "2026-10-15 04:00") not in pp      # 0,4 MW: alerta, no protegida


def test_el_etiquetador_la_marca_positiva():
    import banco_paridad as bp
    fila = {"volcano": "NevadosDeChillan", "sensor_bucket": "VIIRS375", "sensor_raw": "VIIRS375",
            "fecha_utc": "2026-10-15 05:00:00", "source": "OCR", "origen": "principal",
            "tipo": "ALERTA_TERMICA_OCR", "vrp_mw": 22.13, "dist_km": None, "clasificacion": "SIN_GEOMETRIA",
            "ultima_actualizacion": "", "sin_geometria": True}
    rutina = dict(fila, fecha_utc="2026-10-15 06:30:00", source="CONS", tipo="RUTINA", vrp_mw=0.0,
                  clasificacion="NULO", sin_geometria=False)
    recs = [{"vol": "NevadosDeChillan", "b": "VIIRS375", "noche": "2026-10-15",
             "dt": datetime(2026, 10, 15, h, m, tzinfo=timezone.utc)} for h, m in ((5, 0), (6, 30))]
    por_vb, ns, nv, _ = bp.indexar_referencia([fila, rutina], bp._coords_por_volcan(), ("2026-10-15", "2026-10-15"))
    bp.etiquetar(recs, por_vb, ns, nv)
    # la de las 05:00 es positiva; la RUTINA de las 06:30 ya no es negativo limpio (la noche tiene alerta)
    assert [r["lab"] for r in recs] == ["pos", "sin_info"]
    assert recs[0]["dist_ref"] is None


def test_loader_del_pipeline_tampoco_la_lee_como_cero(tmp_path):
    from pipeline.mirova_csv_loader import load_mirova_alertas
    ocr = tmp_path / "ocr.csv"
    _escribir(ocr, OCR_COLS, [_sin_geo()])
    al = load_mirova_alertas(cons_path=None, ocr_path=ocr)
    assert len(al) == 1 and al[0]["vrp_mw"] == 22.13 and al[0]["dist_km"] is None


# ------------------------------------------------------------------ serie del tablero
def _rebuild(tmp_path, monkeypatch, filas_ocr):
    cons, ocr = tmp_path / "cons.csv", tmp_path / "ocr.csv"
    _escribir(cons, CONS_COLS, [_fila(CONS_COLS, "2026-10-14 06:18:00", "VIIRS375", "2.54", "ALERTA_TERMICA", "Bajo",
                                      dist="0.84")])
    _escribir(ocr, OCR_COLS, filas_ocr)
    monkeypatch.setattr(rb, "REPO", tmp_path)
    rb.rebuild("NevadosDeChillan", "Nevados de Chillan", source=cons, ocr=ocr)
    return json.loads((tmp_path / "data" / "mirova" / "NevadosDeChillan.json").read_text(encoding="utf-8"))


def test_rebuild_las_incluye_con_marca(tmp_path, monkeypatch):
    out = _rebuild(tmp_path, monkeypatch, [_sin_geo(), _sin_geo(sensor="VIIRS", vrp="14.0"),
                                           _sin_geo(t="2026-10-14 18:42:02", vrp="4.24")])   # diurna: fuera
    por = {(r["datetime_utc"], r["sensor"]): r for r in out["records"]}
    r = por[("2026-10-15 05:00", "VIIRS375")]
    assert r["VRP_MW"] == 22.13 and r["source"] == "ocr"
    assert r["distancia_km"] is None and r["sin_geometria"] is True
    assert r["clasificacion"] == "SIN_GEOMETRIA"
    assert por[("2026-10-15 05:00", "VIIRS")]["VRP_MW"] == 14.0
    assert ("2026-10-14 18:42", "VIIRS375") not in por          # el OCR diurno sigue fuera (A76)
    # las filas de siempre no cambian: ni la clave nueva ni la distancia
    assert por[("2026-10-14 06:18", "VIIRS375")] == {
        "datetime_utc": "2026-10-14 06:18", "sensor": "VIIRS375", "VRP_MW": 2.54, "distancia_km": 0.84,
        "clasificacion": "Bajo", "source": "consolidado"}


def test_rebuild_sigue_rechazando_clases_no_alerta(tmp_path, monkeypatch):
    # SIN_GEOMETRIA solo vale con el metodo de V31.1 o en el OCR; una fila de la TABLA con esa clase no entra
    # por la puerta de atras, y un NULO del OCR sigue fuera.
    out = _rebuild(tmp_path, monkeypatch, [
        _fila(OCR_COLS, "2026-10-13 05:00:00", "VIIRS375", "0.3", "ALERTA_TERMICA_OCR", "NULO"),
        _fila(OCR_COLS, "2026-10-13 06:00:00", "VIIRS375", "0.3", "FALSO_POSITIVO_OCR", "SIN_GEOMETRIA",
              metodo="vrp_sin_geometria_propia"),
    ])
    assert {r["datetime_utc"] for r in out["records"]} == {"2026-10-14 06:18"}
