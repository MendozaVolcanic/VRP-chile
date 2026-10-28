# -*- coding: utf-8 -*-
"""S166 (issue #915, clasificado en experiments/_s165_issue915/INFORME.md de la rama loop/activo): el
auto-audit deja de levantar flags por artefactos de la referencia y por una pérdida ya decidida.

POR QUÉ: el audit semanal abrió #915 «FUERA DE BANDA» con tres alertas protegidas «sin publicar» y cinco
magnitudes bajas. La clasificación de S165 mostró que ninguna protegida era una pérdida de cráter que el
operador no viera, y que parte de las magnitudes comparaba objetos distintos. Un audit que se dispara cada
semana por eso confunde más de lo que ayuda (decisión de Nicolás, 2026-10-28). Los tres cambios:

1. protegida con `referencia_sospechosa` (sólo OCR de Suomi NPP antes del hito A119): no levanta flag, se
   informa aparte;
2. magnitud por noche: la noche sale de la mediana que decide el flag si la cota inferior de separación
   (diferencia de radios desde el centro de MIROVA, A93) supera el `inner_radius_km` del volcán, o si el
   máximo de MIROVA es una fila sólo OCR de Suomi NPP anterior al hito;
3. pérdida aceptada: PCC VIIRS 750 2026-10-10 05:54 (#865, #881), y ninguna otra pasada.

Cada cambio tiene un control: la protegida normal (tabla, NOAA-20 o posterior al hito) sigue siendo flag, y
la noche del mismo objeto sigue en la mediana. El cambio no puede apagar el audit entero.
"""
import copy
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
WIN = ("2026-08-27", "2026-10-26")


# ------------------------------------------------------------------ ayudas
def _fila(vol, b, fecha, vrp, source="CONS", tipo=None, dist=None):
    tipo = tipo or ("ALERTA_TERMICA_OCR" if source == "OCR" else "ALERTA_TERMICA")
    return {"volcano": vol, "sensor_bucket": b, "fecha_utc": fecha, "vrp_mw": vrp, "tipo": tipo,
            "source": source, "dist_km": dist}


def _brec(vol, b, fecha, pub, sensor, sha="abc"):
    dt = datetime.strptime(fecha, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": vol, "b": b, "dt": dt, "noche": fecha[:10], "pub": pub, "sha": sha, "sensor": sensor}


def _protegidas(filas, recs):
    return aa.alertas_protegidas(filas, recs, WIN, FRONTERA, diurna=lambda *a: False)


# ------------------------------------------------------------------ 1. referencia sospechosa
def test_protegida_con_referencia_sospechosa_no_es_flag_y_se_informa_aparte():
    filas = [_fila("Tupungatito", "VIIRS375", "2026-09-28 05:18:00", 2.51, source="OCR")]
    recs = [_brec("Tupungatito", "VIIRS375", "2026-09-28 05:18", False, "VIIRS_SNPP")]
    lista = _protegidas(filas, recs)
    assert [(p["estado"], p["referencia_sospechosa"]) for p in lista] == [("sin_publicar", True)]
    assert aa.flags_protegidas(lista, "K") == []
    aparte = aa.protegidas_aparte(lista, "K")
    assert len(aparte) == 1
    assert "Tupungatito VIIRS375 2026-09-28 05:18" in aparte[0] and "2.51" in aparte[0]
    assert "referencia sospechosa" in aparte[0] and aa.HITO_OCR_SUOMI_NPP in aparte[0]


@pytest.mark.parametrize("fila,sensor", [
    # control: de la tabla (CONS), aunque sea Suomi NPP y antes del hito
    (_fila("Tupungatito", "VIIRS375", "2026-09-28 05:18:00", 2.51, source="CONS"), "VIIRS_SNPP"),
    # control: sólo OCR antes del hito, pero de NOAA-20
    (_fila("Tupungatito", "VIIRS375", "2026-09-28 05:18:00", 2.51, source="OCR"), "VIIRS_NOAA20"),
    # control: sólo OCR de Suomi NPP, pero posterior al hito
    (_fila("Tupungatito", "VIIRS375", "2026-10-12 05:18:00", 2.51, source="OCR"), "VIIRS_SNPP"),
])
def test_protegida_normal_sigue_siendo_flag(fila, sensor):
    recs = [_brec("Tupungatito", "VIIRS375", fila["fecha_utc"][:16], False, sensor)]
    lista = _protegidas([fila], recs)
    assert lista[0]["referencia_sospechosa"] is False
    flags = aa.flags_protegidas(lista, "K")
    assert len(flags) == 1 and flags[0].startswith("alerta protegida sin publicar: Tupungatito VIIRS375")
    assert aa.protegidas_aparte(lista, "K") == []


def test_aparte_solo_del_detector_vigente_y_solo_sin_publicar():
    filas = [_fila("Tupungatito", "VIIRS375", "2026-09-10 05:18:00", 2.0, source="OCR"),   # C0
             _fila("Tupungatito", "VIIRS375", "2026-09-28 05:18:00", 2.5, source="OCR")]   # K, publicada
    recs = [_brec("Tupungatito", "VIIRS375", "2026-09-10 05:18", False, "VIIRS_SNPP", sha=None),
            _brec("Tupungatito", "VIIRS375", "2026-09-28 05:18", True, "VIIRS_SNPP")]
    lista = _protegidas(filas, recs)
    assert aa.protegidas_aparte(lista, "K") == []
    assert aa.flags_protegidas(lista, "K") == []


# ------------------------------------------------------------------ 3. pérdida aceptada
def test_el_registro_de_perdidas_aceptadas_tiene_una_sola_pasada():
    assert set(aa.PERDIDAS_ACEPTADAS) == {("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54")}
    motivo = aa.PERDIDAS_ACEPTADAS[("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54")]
    assert "#865" in motivo and "#881" in motivo


def test_la_perdida_aceptada_no_es_flag_y_se_informa_como_aceptada():
    filas = [_fila("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54:00", 1.19, dist=7.83)]
    recs = [_brec("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54", False, "VIIRS_NOAA20_750"),
            _brec("PuyehueCordonCaulle", "VIIRS375", "2026-10-10 05:54", True, "VIIRS_NOAA21")]
    lista = _protegidas(filas, recs)
    assert [(p["estado"], p["perdida_aceptada"]) for p in lista] == [("sin_publicar", True)]
    assert aa.flags_protegidas(lista, "K") == []
    aparte = aa.protegidas_aparte(lista, "K")
    assert len(aparte) == 1
    assert "pérdida aceptada" in aparte[0] and "PuyehueCordonCaulle VIIRS750 2026-10-10 05:54" in aparte[0]
    assert "#865" in aparte[0]


@pytest.mark.parametrize("vol,b,fecha,sensor", [
    ("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 04:54:00", "VIIRS_SNPP_750"),   # otra pasada de esa noche
    ("PuyehueCordonCaulle", "VIIRS750", "2026-10-11 05:54:00", "VIIRS_NOAA20_750"),  # otra noche, misma hora
    ("PuyehueCordonCaulle", "VIIRS375", "2026-10-10 05:54:00", "VIIRS_NOAA21"),      # mismo minuto, otro sensor
    ("NevadosDeChillan", "VIIRS750", "2026-10-10 05:54:00", "VIIRS_NOAA20_750"),     # mismo minuto, otro volcán
])
def test_el_registro_no_acepta_ninguna_otra_pasada(vol, b, fecha, sensor):
    lista = _protegidas([_fila(vol, b, fecha, 1.5)], [_brec(vol, b, fecha[:16], False, sensor)])
    assert lista[0]["perdida_aceptada"] is False
    assert len(aa.flags_protegidas(lista, "K")) == 1
    assert aa.protegidas_aparte(lista, "K") == []


# ------------------------------------------------------------------ 2. magnitud con el mismo objeto
CENTRO_PCC = (-40.5903, -72.1187)
CENTRO_TUP = (-33.42694, -69.80039)


def _punto_a(centro, km_norte):
    """Punto a `km_norte` km al norte del centro (1° de latitud = 111,195 km en la esfera de 6371 km)."""
    return (centro[0] + km_norte / 111.195, centro[1])


def _rec(fecha, sensor, vrp, ll, core=None, dist=1.0, sha="abc"):
    r = {"datetime_utc": fecha, "sensor": sensor, "distance_class": "summit",
         "primary_cluster": {"vrp_mw": vrp, "centroid_dist_km": dist,
                             "centroid_lat": ll[0] if ll else None, "centroid_lon": ll[1] if ll else None},
         "anomaly_pixels": [{}], "regimen": {"codigo_sha": sha}}
    if core is not None:
        r["f5_core_vrp_mw"] = core
    return r


def _pcc_seis_noches(lejos_km=18.5):
    """6 noches K de PCC VIIRS 750. MIROVA 1,0 MW a 7,83 km de su centro. Cinco noches nuestro cúmulo está
    a 7,8 km (mismo radio) con 0,6 MW; la sexta está a `lejos_km` con 0,1 MW."""
    mir, recs, alertas = {}, [], []
    for i in range(6):
        d = f"2026-10-{i + 1:02d}"
        mir[("PuyehueCordonCaulle", "VIIRS750", d)] = 1.0
        alertas.append(_fila("PuyehueCordonCaulle", "VIIRS750", d + " 05:54:00", 1.0, dist=7.83))
        lejos = i == 5
        recs.append(_rec(d + " 05:54", "VIIRS_NOAA20_750", 0.1 if lejos else 0.6,
                         _punto_a(CENTRO_PCC, lejos_km if lejos else 7.8)))
    return mir, {"PuyehueCordonCaulle": recs}, alertas


def _evaluar(mir, recs, alertas, centros, filas_ref=None):
    res = aa.nuestros_por_noche(recs, WIN, FRONTERA)
    inst = {k: f"{k[2]} 05:54:00" for k in mir}
    info = aa.info_pasadas_mirova(alertas, inst, recs, filas_ref)
    excl = aa.noches_otro_objeto(mir, res["ours"], info, centros)
    return aa.evaluar_detector(mir, res["ours"], res["vistos"], "K", FRONTERA, excluir=excl), excl


def test_cota_sobre_el_inner_radius_saca_la_noche_de_la_mediana():
    # PCC tiene inner 20 km: con el cúmulo a 30 km del centro y MIROVA a 7,83 la cota es 22,2 km > 20.
    mir, recs, alertas = _pcc_seis_noches(lejos_km=30.0)
    ev, excl = _evaluar(mir, recs, alertas, {"PuyehueCordonCaulle": CENTRO_PCC})
    assert list(excl) == [("PuyehueCordonCaulle", "VIIRS750", "2026-10-06")]
    assert "cota" in excl[("PuyehueCordonCaulle", "VIIRS750", "2026-10-06")]
    m = ev["magnitud_publicada_by_vol_sensor"]["PuyehueCordonCaulle|VIIRS750"]
    assert (m["n_noches"], m["ratio_mediano"]) == (5, 0.6)
    oo = ev["magnitud_otro_objeto"]["PuyehueCordonCaulle|VIIRS750"]
    assert oo["n_noches_excluidas"] == 1
    assert oo["con_todas"] == {"n_noches": 6, "ratio_mediano": 0.6}
    assert oo["noches"][0]["fecha"] == "2026-10-06"
    # control: el flag de sub-banda de las cinco noches del mismo objeto sigue en pie
    assert any("PuyehueCordonCaulle VIIRS750 0.6x" in f for f in aa.flags_de_evaluacion(ev))


def test_cota_bajo_el_inner_radius_no_saca_la_noche():
    # Lo que pasó el 2026-10-10 en #915: cúmulo a 18,5 km, MIROVA a 7,83: cota 10,7 km < 20 (inner de PCC).
    mir, recs, alertas = _pcc_seis_noches(lejos_km=18.5)
    ev, excl = _evaluar(mir, recs, alertas, {"PuyehueCordonCaulle": CENTRO_PCC})
    assert excl == {}
    m = ev["magnitud_publicada_by_vol_sensor"]["PuyehueCordonCaulle|VIIRS750"]
    assert m["n_noches"] == 6
    assert ev["magnitud_otro_objeto"] == {}


def test_sin_centro_de_miroVA_o_sin_centroide_no_se_inventa_la_cota():
    mir, recs, alertas = _pcc_seis_noches(lejos_km=30.0)
    ev, excl = _evaluar(mir, recs, alertas, {})   # sin centro: la cota no se calcula y la noche queda
    assert excl == {}
    assert ev["magnitud_publicada_by_vol_sensor"]["PuyehueCordonCaulle|VIIRS750"]["n_noches"] == 6
    recs["PuyehueCordonCaulle"][5]["primary_cluster"]["centroid_lat"] = None
    ev, excl = _evaluar(mir, recs, alertas, {"PuyehueCordonCaulle": CENTRO_PCC})
    assert excl == {}


def _tup_noches(fuentes_sensor):
    """Una noche K de Tupungatito VIIRS 375 por elemento (fuente de la fila máxima de MIROVA, plataforma de
    nuestro record en esa pasada, fecha). MIROVA 1,0 MW a 5,2 km; nuestro núcleo 0,5 a 5,0 km del centro."""
    mir, recs, alertas = {}, [], []
    for source, sensor, d in fuentes_sensor:
        mir[("Tupungatito", "VIIRS375", d)] = 1.0
        alertas.append(_fila("Tupungatito", "VIIRS375", d + " 05:54:00", 1.0, source=source, dist=5.2))
        recs.append(_rec(d + " 05:54", sensor, 0.5, _punto_a(CENTRO_TUP, 5.0), core=0.5))
    return mir, {"Tupungatito": recs}, alertas


def test_maximo_de_miroVA_solo_ocr_de_suomi_npp_antes_del_hito_sale_de_la_mediana():
    mir, recs, alertas = _tup_noches([("OCR", "VIIRS_SNPP", "2026-09-28")])
    ev, excl = _evaluar(mir, recs, alertas, {"Tupungatito": CENTRO_TUP})
    assert list(excl) == [("Tupungatito", "VIIRS375", "2026-09-28")]
    assert "Suomi NPP" in excl[("Tupungatito", "VIIRS375", "2026-09-28")]
    assert "Tupungatito|VIIRS375" not in ev["magnitud_publicada_by_vol_sensor"]
    assert ev["magnitud_otro_objeto"]["Tupungatito|VIIRS375"]["n_noches_excluidas"] == 1


@pytest.mark.parametrize("source,sensor,d", [
    ("CONS", "VIIRS_SNPP", "2026-09-28"),     # de la tabla
    ("OCR", "VIIRS_NOAA20", "2026-09-28"),    # sólo OCR, pero NOAA-20
    ("OCR", "VIIRS_SNPP", "2026-10-12"),      # sólo OCR de Suomi NPP, posterior al hito
])
def test_maximo_de_miroVA_normal_sigue_en_la_mediana(source, sensor, d):
    mir, recs, alertas = _tup_noches([(source, sensor, d)])
    ev, excl = _evaluar(mir, recs, alertas, {"Tupungatito": CENTRO_TUP})
    assert excl == {}
    assert ev["magnitud_publicada_by_vol_sensor"]["Tupungatito|VIIRS375"]["n_noches"] == 1


def test_pasada_con_tabla_y_ocr_no_es_solo_ocr():
    mir, recs, alertas = _tup_noches([("OCR", "VIIRS_SNPP", "2026-09-28")])
    filas_ref = [_fila("Tupungatito", "VIIRS375", "2026-09-28 05:54:30", 0.8, source="CONS", dist=5.2)]
    _, excl = _evaluar(mir, recs, alertas, {"Tupungatito": CENTRO_TUP}, filas_ref=filas_ref)
    assert excl == {}


def test_la_cota_usa_la_distancia_de_miroVA_mas_cercana_a_la_nuestra():
    # dos filas de MIROVA en la pasada, una a 7,8 km (mismo radio) y otra a 40: la cota es la mínima
    mir, recs, alertas = _pcc_seis_noches(lejos_km=7.8)
    alertas.append(_fila("PuyehueCordonCaulle", "VIIRS750", "2026-10-06 05:54:10", 0.9, source="OCR", dist=40.0))
    _, excl = _evaluar(mir, recs, alertas, {"PuyehueCordonCaulle": CENTRO_PCC})
    assert excl == {}


def test_centros_de_miroVA_salen_de_volcanoes_yaml():
    c = aa._centros_mirova()
    assert c["PuyehueCordonCaulle"] == CENTRO_PCC
    assert c["Tupungatito"] == CENTRO_TUP
    assert set(aa.VOLS) <= set(c)


# ------------------------------------------------------------------ main(): lo aparte llega a latest.json
HOY = datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc)


class _Reloj(datetime):
    @classmethod
    def now(cls, tz=None):
        return HOY


def _correr_main(tmp_path, monkeypatch, con_normal):
    """Escenario de #915 en chico: una protegida sospechosa (Tupungatito), la aceptada de PCC y, si
    `con_normal`, una protegida MODIS de Chillán de la tabla sin publicar (control)."""
    banco_recs = [dict(_brec("Tupungatito", "VIIRS375", "2026-09-28 05:18", False, "VIIRS_SNPP"),
                       lab="pos", lab_original="pos", z=16.0),
                  dict(_brec("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54", False, "VIIRS_NOAA20_750"),
                       lab="pos", lab_original="pos", z=63.0)]
    banco_filas = [_fila("Tupungatito", "VIIRS375", "2026-09-28 05:18:00", 2.51, source="OCR", dist=5.27),
                   _fila("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54:00", 1.19, dist=7.83)]
    if con_normal:
        banco_recs.append(dict(_brec("NevadosDeChillan", "MODIS", "2026-10-12 07:20", False, "MODIS_AQUA"),
                               lab="pos", lab_original="pos", z=50.0))
        banco_filas.append(_fila("NevadosDeChillan", "MODIS", "2026-10-12 07:20:00", 2.18, dist=1.0))
    records = {"Tupungatito": [], "PuyehueCordonCaulle": []}
    for i in range(61):   # un record por día para que la cobertura no degrade
        d = (HOY.date() - timedelta(days=i)).isoformat()
        records["Tupungatito"].append({"datetime_utc": d + " 05:00", "sensor": "VIIRS_NOAA20",
                                       "regimen": {"codigo_sha": "abc"} if d >= FRONTERA else {}})
    out = tmp_path / ("con" if con_normal else "sin")
    monkeypatch.setattr(aa, "OUTDIR", str(out))
    monkeypatch.setattr(aa, "datetime", _Reloj)
    monkeypatch.setattr(aa, "leer_frontera_k", lambda *a, **k: FRONTERA)
    monkeypatch.setattr(aa, "alertas_mirova", lambda *a, **k: [])
    monkeypatch.setattr(aa, "cargar_filas_referencia", lambda: None)
    monkeypatch.setattr(aa, "cargar_records",
                        lambda: (copy.deepcopy(records), {"parse_errors": [], "duplicates_total": 0}))
    monkeypatch.setattr(aa, "banco_ventana", lambda win: (copy.deepcopy(banco_recs), copy.deepcopy(banco_filas)))
    monkeypatch.setattr(aa, "_coords_por_volcan", lambda: {})
    monkeypatch.setattr(aa, "_csv_ultima_fecha", lambda p: "2026-10-25")
    monkeypatch.setattr(aa, "leer_ceses", lambda *a, **k: ([], None))
    aa.main()
    return json.loads((out / "latest.json").read_text(encoding="utf-8"))


def test_main_informa_aparte_sin_cambiar_el_veredicto(tmp_path, monkeypatch):
    out = _correr_main(tmp_path, monkeypatch, con_normal=False)
    aparte = out["informado_aparte"]["protegidas"]
    assert len(aparte) == 2
    assert any("Tupungatito" in a and "referencia sospechosa" in a for a in aparte)
    assert any("PuyehueCordonCaulle" in a and "pérdida aceptada" in a for a in aparte)
    assert not any(f.startswith("alerta protegida") for f in out["flags"])
    assert out["verdict"] == "VERDE"
    assert "magnitud_otro_objeto" in out["informado_aparte"]


def test_main_control_la_protegida_normal_sigue_dando_fuera_de_banda(tmp_path, monkeypatch):
    out = _correr_main(tmp_path, monkeypatch, con_normal=True)
    prot = [f for f in out["flags"] if f.startswith("alerta protegida")]
    assert len(prot) == 1 and "NevadosDeChillan MODIS 2026-10-12 07:20" in prot[0]
    assert out["verdict"] == "FUERA_DE_BANDA"
    assert len(out["informado_aparte"]["protegidas"]) == 2


def test_el_issue_lleva_lo_informado_aparte():
    """El cuerpo del issue (audit-weekly.yml) tiene que traer la lista aparte, para que lo que no decide el
    veredicto siga a la vista de quien lee el issue."""
    yml = (ROOT / ".github" / "workflows" / "audit-weekly.yml").read_text(encoding="utf-8")
    assert "informado_aparte" in yml
    assert "/tmp/aparte.txt" in yml
