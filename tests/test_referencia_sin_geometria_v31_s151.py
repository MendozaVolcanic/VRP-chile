# -*- coding: utf-8 -*-
"""Filas OCR de MIROVA sin geometria propia (V31.1 de Mirova-v1, 2026-10-15).

POR QUE. MIROVA mantiene una sola imagen de distancia (Dist.png) por volcan y sensor y la reemplaza en cada
pasada. Si el OCR de Mirova-v1 corre cuando MIROVA ya proceso la pasada siguiente, esa imagen es de la otra
pasada: la distancia y la clase no sirven, pero el VRP si, porque sale de la celda de la propia pasada en
Latest10NTI. Hasta V31 esas pasadas se perdian; caso: Nevados de Chillan 2026-10-15 05:00 UTC, 22,13 MW en
VIIRS 375, en erupcion, que la tabla latest.php nunca trajo. Desde V31.1 llegan con tipo propio
ALERTA_SIN_GEOMETRIA_OCR, `Distancia_km` VACIA, clase SIN_GEOMETRIA y metodo vrp_sin_geometria_propia.

Decision (coordinador del loop, 2026-10-15, la conservadora): se publican en el tablero, pero NO son alerta
de la lectura A ("alerta del scraper dentro del radio"), porque no se sabe la distancia. Son un estrato
aparte. Que se fija aca:
- la referencia las lee con distancia DESCONOCIDA (None), nunca 0 ni la de la nota;
- una de 1 MW o mas NO es alerta protegida bajo A (si lo fuera, el criterio cambiaria hacia atras);
- en el etiquetador no le ganan a una alerta, a un FALSO_POSITIVO ni a una RUTINA de la misma pasada, y no
  cambian la noche;
- la serie de MIROVA del tablero (data/mirova/<Volcan>.json) las incluye con su marca, y las filas de hoy
  quedan byte a byte iguales.
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
from scripts.referencia_mirova_unificada import (TIPO_SIN_GEOMETRIA,  # noqa: E402
                                                 cargar_referencia_unificada,
                                                 leer_pasadas)

CONS_COLS = ["timestamp", "Fecha_Satelite_UTC", "Fecha_Captura_Chile", "Volcan", "Sensor", "VRP_MW",
             "Distancia_km", "Tipo_Registro", "Clasificacion Mirova", "Ruta Foto", "Fecha_Proceso_GitHub",
             "Ultima_Actualizacion", "Editado"]
OCR_COLS = CONS_COLS + ["Color_Punto_Dist", "Confianza_Validacion", "Requiere_Verificacion", "Metodo_Validacion",
                        "Nota_Validacion", "Version_OCR", "Zenith_Sat_deg", "Azimut_Sat_deg",
                        "Nivel_Anomalia_MIROVA", "Confianza_Geometria"]


def _fila(cols, t, sensor, vrp, tipo, clase, dist="0.5", metodo="", nota="", volcan="Nevados de Chillan"):
    r = {c: "" for c in cols}
    r.update({"Fecha_Satelite_UTC": t, "Volcan": volcan, "Sensor": sensor, "VRP_MW": vrp,
              "Distancia_km": dist, "Tipo_Registro": tipo, "Clasificacion Mirova": clase})
    if "Metodo_Validacion" in r:
        r["Metodo_Validacion"] = metodo
        r["Nota_Validacion"] = nota
    return r


def _sin_geo(t="2026-10-15 05:00:00", sensor="VIIRS375", vrp="22.13", nota="", tipo=TIPO_SIN_GEOMETRIA,
             volcan="Nevados de Chillan"):
    return _fila(OCR_COLS, t, sensor, vrp, tipo, "SIN_GEOMETRIA", dist="", metodo="vrp_sin_geometria_propia",
                 nota=nota, volcan=volcan)


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
    assert f["tipo"] == TIPO_SIN_GEOMETRIA and f["vrp_mw"] == 22.13
    assert f["dist_km"] is None
    assert f["sin_geometria"] is True
    assert por["2026-10-14 13:05:00"]["sin_geometria"] is False
    assert por["2026-10-14 13:05:00"]["dist_km"] == 1.08


def test_marca_en_fila_alerta_tambien_queda_en_el_estrato(tmp_path):
    """Defensa: una fila con la marca pero tipo ALERTA_TERMICA_OCR (una version del scraper que no pusiera el
    tipo propio) se trata igual. Una con la marca que reconciliar_latest paso a FALSO_POSITIVO_OCR NO: la tabla
    le dio la distancia de esa misma pasada."""
    ocr = tmp_path / "ocr.csv"
    _escribir(ocr, OCR_COLS, [
        _sin_geo(tipo="ALERTA_TERMICA_OCR"),
        _fila(OCR_COLS, "2026-10-14 05:12:00", "VIIRS375", "0.08", "FALSO_POSITIVO_OCR", "SIN_GEOMETRIA",
              dist="9.07", metodo="vrp_sin_geometria_propia", volcan="Isluga")])
    por = {f["fecha_utc"]: f for f in leer_pasadas(ocr, "OCR", "principal")}
    assert por["2026-10-15 05:00:00"]["tipo"] == TIPO_SIN_GEOMETRIA
    assert por["2026-10-14 05:12:00"]["tipo"] == "FALSO_POSITIVO_OCR"
    assert por["2026-10-14 05:12:00"]["sin_geometria"] is False and por["2026-10-14 05:12:00"]["dist_km"] == 9.07


def test_sin_geometria_de_1mw_o_mas_no_es_protegida_bajo_a(tmp_path):
    """Si esta falla, el criterio de victoria cambio hacia atras sin que nadie lo decidiera."""
    cons, ocr = tmp_path / "cons.csv", tmp_path / "ocr.csv"
    _escribir(cons, CONS_COLS, [_fila(CONS_COLS, "2026-10-15 06:00:00", "VIIRS375", "3.1", "ALERTA_TERMICA", "Bajo")])
    _escribir(ocr, OCR_COLS, [
        _sin_geo(),                                                                   # 22,13 MW
        _sin_geo(t="2026-10-11 04:36:00", sensor="VIIRS", vrp="1.0", volcan="Chaiten"),  # caso del verificador
        _sin_geo(t="2026-10-14 06:00:00", tipo="ALERTA_TERMICA_OCR", vrp="5.0"),       # marca con tipo viejo
    ])
    ref = cargar_referencia_unificada(cons, ocr, respaldo_path=None, historico_path=None)
    sg = [x for x in ref if x["sin_geometria"]]
    assert len(sg) == 3 and all((x["vrp_mw"] or 0) >= 1 for x in sg)
    assert not any(alerta_protegida(x, lectura="A") for x in sg)
    assert pasadas_protegidas(ref) == {("NevadosDeChillan", "VIIRS375", "2026-10-15 06:00")}
    # la lectura B (informativa, cualquier distancia) si las cuenta
    assert all(alerta_protegida(x, lectura="B") for x in sg)


# ------------------------------------------------------------------ etiquetador
def _fila_ref(hora, tipo, vrp, source, sin_geo=False):
    return {"volcano": "NevadosDeChillan", "sensor_bucket": "VIIRS375", "sensor_raw": "VIIRS375",
            "fecha_utc": "2026-10-15 " + hora, "source": source, "origen": "principal", "tipo": tipo,
            "vrp_mw": vrp, "dist_km": None, "clasificacion": "", "ultima_actualizacion": "",
            "sin_geometria": sin_geo}


def _etiquetas(filas, horas):
    import banco_paridad as bp
    recs = [{"vol": "NevadosDeChillan", "b": "VIIRS375", "noche": "2026-10-15",
             "dt": datetime(2026, 10, 15, h, m, tzinfo=timezone.utc)} for h, m in horas]
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, bp._coords_por_volcan(), ("2026-10-15", "2026-10-15"))
    bp.etiquetar(recs, por_vb, ns, nv)
    return [r["lab"] for r in recs], ns


def test_etiquetador_estrato_aparte_y_la_noche_no_cambia():
    sg = _fila_ref("05:00:00", TIPO_SIN_GEOMETRIA, 22.13, "OCR", True)
    rutina = _fila_ref("06:30:00", "RUTINA", 0.0, "CONS")
    labs, ns = _etiquetas([sg, rutina], ((5, 0), (6, 30)))
    # la de las 05:00 va al estrato aparte; la RUTINA de las 06:30 sigue siendo negativo limpio
    assert labs == ["sin_geometria", "neg_limpio"]
    assert not ns[("NevadosDeChillan", "VIIRS375", "2026-10-15")]["alerta"]


def test_etiquetador_no_le_gana_a_fp_ni_a_rutina_de_la_misma_pasada():
    sg = _fila_ref("05:00:00", TIPO_SIN_GEOMETRIA, 22.13, "OCR", True)
    fp = _fila_ref("05:00:00", "FALSO_POSITIVO", 22.0, "CONS")
    assert _etiquetas([sg, fp], ((5, 0),))[0] == ["far_ref"]
    rutina = _fila_ref("05:00:00", "RUTINA", 0.0, "CONS")
    assert _etiquetas([sg, rutina], ((5, 0),))[0] == ["neg_limpio"]
    alerta = _fila_ref("05:00:00", "ALERTA_TERMICA", 21.0, "CONS")
    assert _etiquetas([sg, alerta], ((5, 0),))[0] == ["pos"]


def test_metricas_informan_el_estrato_solo_si_existe():
    import banco_paridad as bp
    base = {"vol": "NevadosDeChillan", "b": "VIIRS375", "noche": "2026-10-15", "pub": 1, "neg_estricto": False}
    sin = bp.metricas([dict(base, lab="pos")], {}, lambda r: True)[0]
    assert "n_sin_geometria" not in sin
    con = bp.metricas([dict(base, lab="pos"), dict(base, lab="sin_geometria")], {}, lambda r: True)[0]
    assert con["n_sin_geometria"] == 1 and con["tasa_pub_sin_geometria"] == 1.0 and con["n_pos"] == 1


def test_loader_del_pipeline_no_la_cuenta_como_alerta(tmp_path):
    from pipeline.mirova_csv_loader import load_mirova_alertas
    ocr = tmp_path / "ocr.csv"
    _escribir(ocr, OCR_COLS, [_sin_geo()])
    assert load_mirova_alertas(cons_path=None, ocr_path=ocr) == []


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
    # un NULO del OCR sigue fuera, y una fila con la marca que la reconciliacion paso a FALSO_POSITIVO_OCR tambien
    out = _rebuild(tmp_path, monkeypatch, [
        _fila(OCR_COLS, "2026-10-13 05:00:00", "VIIRS375", "0.3", "ALERTA_TERMICA_OCR", "NULO"),
        _fila(OCR_COLS, "2026-10-13 06:00:00", "VIIRS375", "0.3", "FALSO_POSITIVO_OCR", "SIN_GEOMETRIA",
              metodo="vrp_sin_geometria_propia"),
    ])
    assert {r["datetime_utc"] for r in out["records"]} == {"2026-10-14 06:18"}
