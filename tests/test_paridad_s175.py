# -*- coding: utf-8 -*-
"""S175: decisiones 5, 6 y 9 de docs/AUDIT_S175.md §8 en los instrumentos de paridad (Nicolás, 2026-11-07:
«apruebo todo lo que recomiendas»).

POR QUÉ, en el orden de las decisiones:
1. Recall por pasada (hallazgos 304, 308, V2-02). El recall por noche pregunta si esa noche vimos algo dentro
   del círculo, no si vimos lo que MIROVA vio: PCC VIIRS 750 2026-10-10 salía vista por una pasada de las 04:54
   en otro lugar, mientras la alerta de las 05:54 estaba perdida. El audit publica ahora el recall por pasada
   (pareo a ±clase_mirova.VENTANA_S) al lado del de noche, por sensor y por volcán con su n.
2. Posición de MIROVA con la tabla y origen común (301, 303, F2-212). La distancia del OCR difiere de la de la
   tabla en la misma pasada, y restar nuestro radio (desde el vent) al de MIROVA (desde su centro) mezcla dos
   orígenes. El banco mide con la `Distancia_km` de la tabla y con nuestro punto medido desde el centro de
   MIROVA; `banco_paridad.main` y `clasificacion_referencia` usan la regla D-9 decidida.
3. VRP truncado del OCR (decisión 9, 307, V5-01). En MODIS y VIIRS 750 el OCR lee el VRP truncado a entero: si
   la tabla tiene la pasada manda la tabla; si no, el valor real está entre v y v + 1.

Cada prueba dice qué falla si lo que mide se rompe, y lleva su control (el caso que NO tiene que cambiar).
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.auto_audit_weekly as aa  # noqa: E402
import banco_paridad as bp  # noqa: E402
import clase_mirova as cm  # noqa: E402
import clasificacion_referencia as cr  # noqa: E402

WIN = ("2026-09-03", "2026-11-02")
FRONTERA = "2026-09-18"


def _alerta(vol, b, fecha, vrp, source="CONS", tipo=None, dist=None):
    tipo = tipo or ("ALERTA_TERMICA_OCR" if source == "OCR" else "ALERTA_TERMICA")
    return {"volcano": vol, "sensor_bucket": b, "fecha_utc": fecha, "vrp_mw": vrp, "tipo": tipo,
            "source": source, "dist_km": dist}


# ================================================================== 1. recall por pasada en el audit
def _caso_pcc():
    """PCC VIIRS 750 2026-10-10: MIROVA alerta a las 05:54:02; publicamos a las 04:54 (otro lugar) y no a las 05:54.
    Además, Láscar VIIRS 750 2026-10-11: alerta a las 05:30:10 con nuestro record publicado a las 05:30 (control),
    y una alerta a las 07:10:00 de la que no tenemos record (pasada sin record, no cuenta como perdida)."""
    alertas = [_alerta("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54:02", 1.19),
               _alerta("Lascar", "VIIRS750", "2026-10-11 05:30:10", 3.0),
               _alerta("Lascar", "VIIRS750", "2026-10-11 07:10:00", 2.0)]
    mir, _, _ = aa.noches_mirova_con_instante(alertas, {}, WIN)
    pas_mir = aa.pasadas_mirova(alertas, {}, WIN)
    nuestras = {("PuyehueCordonCaulle", "VIIRS750"): [("2026-10-10 04:54", True), ("2026-10-10 05:54", False)],
                ("Lascar", "VIIRS750"): [("2026-10-11 05:30", True)]}
    vistos = {("PuyehueCordonCaulle", "VIIRS750", "2026-10-10"), ("Lascar", "VIIRS750", "2026-10-11")}
    ours = {("PuyehueCordonCaulle", "VIIRS750", "2026-10-10"): {"crater": [0.5], "dash": [0.5]},
            ("Lascar", "VIIRS750", "2026-10-11"): {"crater": [2.0], "dash": [2.0]}}
    return mir, pas_mir, nuestras, vistos, ours


def test_recall_por_pasada_no_cuenta_la_pasada_de_otra_hora():
    """Si el pareo por pasada se rompiera (o contara la noche), PCC saldría acertada como en el recall por
    noche. Control: el recall por noche sigue en 2 de 2, y Láscar (misma pasada) sigue acertada."""
    mir, pas_mir, nuestras, vistos, ours = _caso_pcc()
    noche = aa.recall_por_sensor(mir, vistos, ours, ["VIIRS750"], {"PuyehueCordonCaulle", "Lascar"})
    assert (noche["VIIRS750"]["recall_dash_pct"], noche["VIIRS750"]["n_noches"]) == (100.0, 2)
    rp = aa.recall_por_pasada(mir, pas_mir, nuestras, vistos, ["VIIRS750"], {"PuyehueCordonCaulle", "Lascar"})
    s = rp["por_sensor"]["VIIRS750"]
    assert (s["n_pasadas"], s["pasadas_sin_record"], s["recall_pasada_pct"]) == (2, 1, 50.0)
    assert (s["n_noches"], s["noches_misma_pasada"], s["recall_noche_misma_pasada_pct"]) == (2, 1, 50.0)
    pv = rp["por_volcan_sensor"]
    assert (pv["PuyehueCordonCaulle|VIIRS750"]["n_pasadas"], pv["PuyehueCordonCaulle|VIIRS750"]["recall_pasada_pct"]) \
        == (1, 0.0)
    assert (pv["Lascar|VIIRS750"]["n_pasadas"], pv["Lascar|VIIRS750"]["recall_pasada_pct"],
            pv["Lascar|VIIRS750"]["pasadas_sin_record"]) == (1, 100.0, 1)


def test_pasadas_mirova_junta_tabla_y_ocr_de_la_misma_pasada():
    """La tabla (05:18:02) y el OCR (05:17:58) de una pasada son UNA pasada; si se contaran dos, el n se infla.
    Control: una alerta 40 minutos después es otra pasada."""
    alertas = [_alerta("Lascar", "VIIRS375", "2026-10-11 05:18:02", 1.0),
               _alerta("Lascar", "VIIRS375", "2026-10-11 05:17:58", 1.0, source="OCR"),
               _alerta("Lascar", "VIIRS375", "2026-10-11 05:58:00", 1.0)]
    assert aa.pasadas_mirova(alertas, {}, WIN) == {("Lascar", "VIIRS375"): ["2026-10-11 05:17:58",
                                                                             "2026-10-11 05:58:00"]}


def test_nuestros_por_noche_entrega_cada_pasada_con_su_criterio_dash():
    """Sin esta lista el recall por pasada no tiene con qué parear. Control: el record `far` va con dash False."""
    recs = [{"datetime_utc": "2026-10-11 05:30", "sensor": "VIIRS_NOAA20_750", "distance_class": "summit",
             "primary_cluster": {"vrp_mw": 2.0, "centroid_dist_km": 1.0}, "regimen": {"codigo_sha": "x"}},
            {"datetime_utc": "2026-10-11 06:20", "sensor": "VIIRS_NOAA21_750", "distance_class": "far",
             "primary_cluster": {"vrp_mw": 2.0, "centroid_dist_km": 1.0}, "regimen": {"codigo_sha": "x"}}]
    nu = aa.nuestros_por_noche({"Lascar": recs}, WIN, FRONTERA)
    assert nu["pasadas"] == {("Lascar", "VIIRS750"): [("2026-10-11 05:30", True), ("2026-10-11 06:20", False)]}


def test_evaluar_detector_publica_el_recall_por_pasada_y_la_via_lo_sigue():
    """El recall por pasada sale en la evaluación de cada detector; con la vía, MODIS es el de la vía y VIIRS el
    de K (como el recall por noche). Si la mezcla se rompiera, MODIS saldría con el n de K."""
    mir = {("NevadosDeChillan", "MODIS", "2026-11-03"): 2.0, ("NevadosDeChillan", "MODIS", "2026-10-20"): 2.0}
    pas_mir = {("NevadosDeChillan", "MODIS"): ["2026-10-20 07:20:00", "2026-11-03 07:20:00"]}
    nuestras = {("NevadosDeChillan", "MODIS"): [("2026-10-20 07:20", False), ("2026-11-03 07:20", True)]}
    vistos = {("NevadosDeChillan", "MODIS", "2026-10-20"), ("NevadosDeChillan", "MODIS", "2026-11-03")}
    ours = {k: {"crater": [], "dash": [], "pub": [], "npix": []} for k in vistos}
    via = "2026-11-02"
    pd = {d: aa.evaluar_detector(mir, ours, vistos, d, FRONTERA, via_modis=via, pasadas=(pas_mir, nuestras))
          for d in ("K", "VIA_MODIS")}
    assert pd["K"]["recall_por_pasada"]["por_sensor"]["MODIS"]["recall_pasada_pct"] == 0.0
    ev = aa.evaluacion_vigente(pd, "K", via)
    m = ev["recall_por_pasada"]["por_sensor"]["MODIS"]
    assert (m["n_pasadas"], m["recall_pasada_pct"]) == (1, 100.0)
    assert ev["recall_por_pasada"]["por_volcan_sensor"]["NevadosDeChillan|MODIS"]["recall_pasada_pct"] == 100.0
    # control: sin `pasadas` la salida es la de siempre (sin la clave)
    assert "recall_por_pasada" not in aa.evaluar_detector(mir, ours, vistos, "K", FRONTERA, via_modis=via)


# ================================================================== 3. VRP truncado del OCR (MODIS y VIIRS 750)
def test_techo_del_vrp_solo_en_el_ocr_de_modis_y_viirs750():
    """Si el piso no se aplicara, el techo del OCR MODIS sería 1,0. Controles: la tabla y el OCR de VIIRS 375
    (que sí trae decimales) quedan con su valor."""
    assert cm.techo_vrp(_alerta("NevadosDeChillan", "MODIS", "2026-10-30 07:15:00", 1.0, source="OCR")) == 2.0
    assert cm.techo_vrp(_alerta("Lascar", "VIIRS750", "2026-10-30 05:00:00", 3.0, source="OCR")) == 4.0
    assert cm.techo_vrp(_alerta("NevadosDeChillan", "MODIS", "2026-10-30 07:15:00", 1.0)) == 1.0
    assert cm.techo_vrp(_alerta("Lascar", "VIIRS375", "2026-10-30 05:00:00", 1.0, source="OCR")) == 1.0
    # una fila sin marca de fuente no es OCR
    assert cm.techo_vrp({"sensor_bucket": "MODIS", "vrp_mw": 1.0}) == 1.0


def test_la_tabla_manda_sobre_el_ocr_de_la_misma_pasada():
    """Chillán MODIS 2026-10-30 08:55: tabla 14,39 MW, OCR 14,0. La fila del OCR se va si la tabla tiene la pasada
    (aunque sea una RUTINA, pasada como `tabla`). Controles: el OCR sin pasada en la tabla y el OCR de VIIRS 375
    se quedan."""
    tabla = _alerta("NevadosDeChillan", "MODIS", "2026-10-30 08:55:10", 14.39)
    ocr = _alerta("NevadosDeChillan", "MODIS", "2026-10-30 08:55:05", 14.0, source="OCR")
    solo_ocr = _alerta("NevadosDeChillan", "MODIS", "2026-10-30 07:15:00", 1.0, source="OCR")
    v375 = _alerta("NevadosDeChillan", "VIIRS375", "2026-10-30 08:55:05", 1.2, source="OCR")
    v375_tabla = _alerta("NevadosDeChillan", "VIIRS375", "2026-10-30 08:55:10", 1.25)
    assert cm.tabla_sobre_ocr([tabla, ocr, solo_ocr, v375, v375_tabla]) == [tabla, solo_ocr, v375, v375_tabla]
    rutina = dict(tabla, tipo="RUTINA", vrp_mw=0.0)
    assert cm.tabla_sobre_ocr([ocr], tabla=[rutina]) == []


def _protegidas(filas, recs):
    return aa.alertas_protegidas(filas, recs, WIN, FRONTERA, diurna=lambda *a: False)


def _brec(vol, b, fecha, pub, sensor):
    dt = datetime.strptime(fecha, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": vol, "b": b, "dt": dt, "noche": fecha[:10], "pub": pub, "sha": "abc", "sensor": sensor}


def test_protegida_solo_ocr_truncada_informa_el_intervalo():
    """Chillán MODIS 2026-10-30 07:15, sólo OCR, 1,0 MW: el real está en [1, 2) y sigue siendo protegida (el corte
    es entero). El flag tiene que decir el intervalo; si se leyera 1,0 como el valor, no lo dice."""
    lista = _protegidas([_alerta("NevadosDeChillan", "MODIS", "2026-10-30 07:15:00", 1.0, source="OCR")],
                        [_brec("NevadosDeChillan", "MODIS", "2026-10-30 07:15", False, "MODIS_TERRA")])
    assert [(p["vrp_mirova_mw"], p["vrp_mirova_hasta_mw"], p["estado"]) for p in lista] == [(1.0, 2.0, "sin_publicar")]
    fl = aa.flags_protegidas(lista, "K")
    assert len(fl) == 1 and "MIROVA 1.0 a 2.0 MW (sólo OCR, truncado a entero por MIROVA en MODIS" in fl[0]


def test_protegida_con_tabla_usa_el_vrp_de_la_tabla():
    """Si la tabla tiene la pasada, su VRP es el que vale aunque el OCR diga otro número (antes se tomaba el mayor
    de los dos). Control: VIIRS 375 no cambia (su OCR no se trunca) y no lleva intervalo."""
    filas = [_alerta("NevadosDeChillan", "MODIS", "2026-10-25 07:20:04", 3.79),
             _alerta("NevadosDeChillan", "MODIS", "2026-10-25 07:20:00", 5.0, source="OCR")]
    lista = _protegidas(filas, [_brec("NevadosDeChillan", "MODIS", "2026-10-25 07:20", False, "MODIS_TERRA")])
    assert [(p["vrp_mirova_mw"], "vrp_mirova_hasta_mw" in p) for p in lista] == [(3.79, False)]
    v375 = [_alerta("Lascar", "VIIRS375", "2026-10-25 05:20:04", 1.5, source="OCR")]
    lista = _protegidas(v375, [_brec("Lascar", "VIIRS375", "2026-10-25 05:20", False, "VIIRS_NOAA20")])
    assert [(p["vrp_mirova_mw"], "vrp_mirova_hasta_mw" in p) for p in lista] == [(1.5, False)]
    assert aa.flags_protegidas(lista, "K")[0].count("MIROVA 1.5 MW (detector K") == 1


def test_noche_con_vrp_piso_sale_de_la_magnitud():
    """Una razón contra 1,0 MW puede ser contra 1,99: la noche cuyo máximo de MIROVA es un piso no entra a la
    mediana y se cuenta aparte. Control: la noche con VRP de la tabla sí entra."""
    alertas = [_alerta("NevadosDeChillan", "MODIS", "2026-10-30 07:15:00", 1.0, source="OCR"),
               _alerta("NevadosDeChillan", "MODIS", "2026-10-31 07:15:00", 2.0)]
    techo = {}
    mir, _, _ = aa.noches_mirova_con_instante(alertas, {}, WIN, techo=techo)
    piso = aa.noches_vrp_piso(mir, techo)
    assert piso == {("NevadosDeChillan", "MODIS", "2026-10-30")}
    ours = {("NevadosDeChillan", "MODIS", d): {"crater": [1.0], "dash": [1.0], "pub": [1.0], "npix": [1]}
            for d in ("2026-10-30", "2026-10-31")}
    ev = aa.evaluar_detector(mir, ours, set(ours), "K", FRONTERA, piso=piso)
    assert ev["magnitud_publicada_by_vol_sensor"]["NevadosDeChillan|MODIS"]["n_noches"] == 1
    assert ev["magnitud_publicada_by_vol_sensor"]["NevadosDeChillan|MODIS"]["ratio_mediano"] == 0.5
    assert ev["magnitud_noches_vrp_piso"] == {"NevadosDeChillan|MODIS": 1}
    # el recall no cambia: la noche sigue siendo de alerta
    assert ev["recall"]["MODIS"]["n_noches"] == 2


def test_un_piso_tapado_por_un_valor_de_tabla_mayor_no_es_piso():
    """Si la tabla de la noche ya pasa a v + 1, el OCR truncado no puede ser el máximo: la magnitud es exacta."""
    alertas = [_alerta("NevadosDeChillan", "MODIS", "2026-10-30 07:15:00", 1.0, source="OCR"),
               _alerta("NevadosDeChillan", "MODIS", "2026-10-30 08:55:00", 2.5)]
    techo = {}
    mir, _, _ = aa.noches_mirova_con_instante(alertas, {}, WIN, techo=techo)
    assert aa.noches_vrp_piso(mir, techo) == set()


# ================================================================== 2. banco: tabla, origen común y D-9
def test_centros_de_mirova_de_los_once_tier_a():
    mc = bp.centros_mirova()
    assert set(bp.VOLS) <= set(mc)
    # Cordón Caulle: el centro de MIROVA está a ~7,6 km del vent (volcanoes.yaml), el desfase de 303
    assert 7.0 < bp._hav_km(*mc["PuyehueCordonCaulle"], -40.525499, -72.1187) < 8.0


def _rec_banco(fecha, b="VIIRS750", vol="PuyehueCordonCaulle"):
    dt = datetime.strptime(fecha, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": vol, "b": b, "dt": dt, "noche": fecha[:10]}


def _etiquetar(recs, filas):
    coords = {v: (0.0, 0.0) for v in bp.VOLS}
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, ("2026-06-01", "2026-11-30"))
    bp.etiquetar(recs, por_vb, ns, nv)
    return recs


@pytest.fixture
def sin_filtro_diurno(monkeypatch):
    monkeypatch.setattr(bp, "es_pasada_diurna_descartada", lambda *a: False)


def test_banco_distancia_de_mirova_de_la_tabla_no_del_ocr(sin_filtro_diurno):
    """Cordón Caulle VIIRS 375 2026-06-15 06:24: OCR 4,19 km; la tabla de la misma pasada, 7,6. Con la tabla,
    `dist_ref_tabla` = 7,6. Si sólo hay OCR, no hay distancia de la tabla. Control: `dist_ref` (la de antes, que
    leen evaluadores sellados) no cambia."""
    filas = [_alerta("PuyehueCordonCaulle", "VIIRS375", "2026-06-15 06:24:05", 1.0, source="OCR", dist=4.19),
             _alerta("PuyehueCordonCaulle", "VIIRS375", "2026-06-15 06:24:10", 1.0, dist=7.6)]
    r = _etiquetar([_rec_banco("2026-06-15 06:24", b="VIIRS375")], filas)[0]
    assert (r["lab"], r["dist_ref_tabla"]) == ("pos", 7.6)
    fp_ocr = [_alerta("PuyehueCordonCaulle", "VIIRS750", "2026-07-06 05:54:02", 0.8, source="OCR",
                      tipo="FALSO_POSITIVO_OCR", dist=9.456)]
    r = _etiquetar([_rec_banco("2026-07-06 05:54")], fp_ocr)[0]
    assert (r["lab"], r["dist_ref"], r["dist_ref_tabla"]) == ("far_ref", 9.456, None)
    fp_tabla = [dict(fp_ocr[0], source="CONS", tipo="FALSO_POSITIVO", dist_km=12.3)]
    r = _etiquetar([_rec_banco("2026-07-06 05:54")], fp_tabla)[0]
    assert (r["lab"], r["dist_ref_tabla"]) == ("far_ref", 12.3)


def test_far_ref_compara_radios_desde_el_mismo_origen():
    """Cordón Caulle VIIRS 750 2026-07-06 05:54: tabla 7,83 km; nuestro final_hotspot a 0,31 km del vent y a 7,52
    km del centro de MIROVA. Con dos orígenes la diferencia es 7,5 km (fuera de 2 km); con origen común, 0,31.
    Control: un far_ref sin distancia de la tabla queda fuera del denominador."""
    base = {"vol": "PuyehueCordonCaulle", "b": "VIIRS750", "lab": "far_ref", "dc": "far", "pc_vrp": 0.0,
            "pub": 0, "noche": "2026-07-06"}
    recs = [dict(base, pc_dist=0.31, d_mc=7.52, dist_ref=7.83, dist_ref_tabla=7.83),
            dict(base, pc_dist=0.31, d_mc=7.52, dist_ref=4.59, dist_ref_tabla=None)]
    m = bp.metrica_far_ref(recs, {})["VIIRS750"]
    assert (m["n"], m["n_con_distancia"], m["n_sin_distancia_tabla"], m["frac_radio_a_2km"]) == (2, 1, 1, 1.0)


def test_cargar_nuestros_mide_nuestro_punto_desde_el_centro_de_mirova(tmp_path, monkeypatch):
    """`d_mc` es la distancia de nuestro final_hotspot al centro de MIROVA, no al vent. Control: sin punto, None."""
    mc = bp.centros_mirova()["PuyehueCordonCaulle"]
    rec = {"datetime_utc": "2026-07-06 05:54", "sensor": "VIIRS_SNPP_750", "distance_class": "summit",
           "final_hotspot_lat": mc[0], "final_hotspot_lon": mc[1] + 0.01,
           "primary_cluster": {"vrp_mw": 1.0, "centroid_dist_km": 0.31}}
    for v in bp.VOLS:
        (tmp_path / f"{v}.json").write_text(json.dumps(
            {"records": [rec, dict(rec, datetime_utc="2026-07-06 06:30", final_hotspot_lat=None)]
             if v == "PuyehueCordonCaulle" else []}), encoding="utf-8")
    monkeypatch.setattr(bp, "es_pasada_diurna_descartada", lambda *a: False)
    monkeypatch.setattr(bp, "correr_node", lambda casos: [[1, 1, 0, 1.0, 1] for _ in casos])
    recs = bp.cargar_nuestros({v: (0.0, 0.0) for v in bp.VOLS}, {v: 5.0 for v in bp.VOLS},
                              ("2026-07-01", "2026-07-31"), data=tmp_path)
    assert 0.8 < recs[0]["d_mc"] < 0.9          # 0,01° de longitud a 40,6° S
    assert recs[1]["d_mc"] is None


def test_banco_main_usa_d9(monkeypatch, tmp_path):
    """F2-212: `banco_paridad.main` etiquetaba con la etiqueta original del scraper. Si vuelve a hacerlo, la regla
    capturada no es SN. (El valor por defecto de indexar_referencia sigue en original, a propósito.)"""
    vistas = []

    def _indexar(filas, coords, ventana, regla_minimas="original", umbral_minima_mw=None):
        vistas.append(regla_minimas)
        return {}, {}, {}, 0
    monkeypatch.setattr(bp, "indexar_referencia", _indexar)
    monkeypatch.setattr(bp, "cargar_referencia_unificada", lambda *a: [])
    monkeypatch.setattr(bp, "cargar_nuestros", lambda *a, **k: [])
    monkeypatch.setattr(bp, "control_identidad_predicado", lambda: ([0, 1, 1, 1, 0], [1, 0]))
    monkeypatch.setattr(bp, "sha_git", lambda p: "0" * 40)
    out = tmp_path / "b.json"
    assert bp.main(["--snapshot", "--inicio", "2026-10-01", "--fin", "2026-10-02", "--out", str(out)]) == 0
    assert vistas == ["SN"]
    assert json.loads(out.read_text(encoding="utf-8"))["meta"]["regla_minimas"] == "SN"


def test_clasificacion_referencia_usa_d9():
    """Una alerta VIIRS 375 de 0,04 MW es una pasada que MIROVA dice no ver (banner NONE): con D-9 SN no es
    «MIROVA confirmó». Control: 0,06 MW sigue confirmada."""
    def _clasificar(vrp):
        rec = {"vol": "Villarrica", "b": "VIIRS375", "noche": "2026-09-05",
               "dt": datetime(2026, 9, 5, 5, 0, tzinfo=timezone.utc), "clave": "x"}
        fila = {"volcano": "Villarrica", "sensor_bucket": "VIIRS375", "fecha_utc": "2026-09-05 05:00:00",
                "source": "CONS", "tipo": "ALERTA_TERMICA", "vrp_mw": vrp, "dist_km": 1.0}
        cr.clasificar_pasadas([rec], [fila], {"Villarrica": (-39.42, -71.94)}, ("2026-09-01", "2026-09-30"))
        return rec["valor"]
    assert _clasificar(0.04) == "mirova_silent"
    assert _clasificar(0.06) == "mirova_confirmed"
