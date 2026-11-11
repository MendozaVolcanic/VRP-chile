# -*- coding: utf-8 -*-
"""S176: la vigilancia de la guardia K de los dos VIIRS dispara lo que pide el diseño, sensor por sensor.

POR QUÉ. Con la vía «código MIROVA» encendida en VIIRS 375 y en VIIRS 750, K corre aparte como guardia (diseño
docs/superpowers/specs/2026-11-08-encendido-v375e-design.md, decisiones 3 y 7). El peor caso es un foco débil que K
publica y la vía calla. Los dos encendidos se revierten por separado (B1 y B2), así que una alerta callada en un sensor
no puede pedir revertir el otro: cada escena lo controla. Una vigilancia ciega no da error, da VERDE: por eso cada caso
tiene su prueba y su control, el caso vecino que no tiene que disparar.

La vigilancia de MODIS (scripts/vigilancia_guardia_modis.py) sigue con sus pruebas: el sensor es un argumento con MODIS
por defecto y aquí sólo se comprueba que pasándolo cambia de sensor.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.vigilancia_guardia_viirs as vv  # noqa: E402

vg = vv.vg  # el mismo módulo que usa la vigilancia de VIIRS: un monkeypatch sobre otro import no le llegaría

ENC = "2026-11-05 22:10:00"
NOCHE = lambda *a: False  # noqa: E731
VENTANA = ("2026-10-25", "2026-12-31")
VOLS_CASO = ["NevadosDeChillan", "Lascar"]
SENS = {"VIIRS375": "VIIRS_NOAA20", "VIIRS750": "VIIRS_NOAA20_750"}
WF = ROOT / ".github" / "workflows" / "vigilancia-guardia-viirs.yml"
GUARDIA_WF = ROOT / ".github" / "workflows" / "guardia-k-viirs.yml"
COTAS = {"muy_bajo": 2, "sobrepublicacion": 3}


def _fila(vol, fecha, vrp, tipo="ALERTA_TERMICA", b="VIIRS375", source="CONS"):
    return {"volcano": vol, "sensor_bucket": b, "fecha_utc": fecha, "vrp_mw": vrp, "tipo": tipo, "source": source}


def _rec(vol, fecha, hhmm, pub, via=None, perfil=None, b="VIIRS375", lab="sin_info", caida=None):
    dt = datetime.strptime(f"{fecha} {hhmm}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": vol, "b": b, "dt": dt, "noche": fecha, "pub": pub, "sensor": SENS.get(b), "perfil": perfil,
            "lab": lab, "via": via, "caida_k": caida}


def _pasada(sensor, vol, fecha, protegida, prod, guardia, vrp=None, prod_via="auto", minima=False, caida=None):
    if prod_via == "auto":
        prod_via = None if prod is None else True
    return {"volcano": vol, "sensor": sensor, "fecha_utc": fecha[:16], "instante_utc": fecha[:16] + ":00",
            "vrp_mirova_mw": vrp if vrp is not None else (2.0 if protegida else 0.3), "protegida": protegida,
            "minima": minima, "referencia_sospechosa": False, "prod_pub": prod, "guardia_pub": guardia,
            "prod_via": prod_via, "prod_caida_k": caida}


def _disp(sensor, pas, prod=(), guardia=(), hoy="2026-11-20", enc=ENC, juzgadas=None, ahora=None, cotas=COTAS):
    return vg.disparadores(list(pas), list(prod), list(guardia), hoy=hoy, encendido=enc, juzgadas=juzgadas,
                           ahora=ahora, sensor=sensor, cotas=cotas)


# ------------------------------------------------------------------ encendido desde los datos
@pytest.mark.parametrize("sensor,plat,otro", [("VIIRS375", "VIIRS_NOAA20", "VIIRS_NOAA20_750"),
                                              ("VIIRS750", "VIIRS_NOAA21_750", "VIIRS_NOAA21")])
def test_el_encendido_sale_del_primer_record_de_la_via_de_ese_sensor(sensor, plat, otro):
    raw = {"NevadosDeChillan": [
        {"sensor": plat, "datetime_utc": "2026-11-05 06:30"},
        {"sensor": plat, "datetime_utc": "2026-11-04 03:10", "via_codigo_mirova": True,
         "processed_utc": "2026-11-06T22:00:00Z"},
        {"sensor": plat, "datetime_utc": "2026-11-06 06:30", "via_codigo_mirova": True,
         "processed_utc": "2026-11-06T09:00:00Z"},
        {"sensor": plat, "datetime_utc": "2026-11-03 06:30", "via_codigo_mirova": "sin_grilla",
         "processed_utc": "2026-11-01T00:00:00Z"},
        # la vía de otro sensor no enciende éste
        {"sensor": otro, "datetime_utc": "2026-11-01 06:30", "via_codigo_mirova": True,
         "processed_utc": "2026-11-01T00:00:00Z"},
        {"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-01 06:30", "via_codigo_mirova": True,
         "processed_utc": "2026-10-01T00:00:00Z"}]}
    e = vg.encendido_desde_datos(raw, sensor=sensor)
    assert e["encendido_utc"] == "2026-11-06 09:00:00" and e["primera_observacion"] == "2026-11-04 03:10"
    assert e["via"] == {("NevadosDeChillan", plat, "2026-11-04 03:10"), ("NevadosDeChillan", plat, "2026-11-06 06:30")}
    assert e["caidas"] == {("NevadosDeChillan", plat, "2026-11-03 06:30"): "sin_grilla"}


def test_por_defecto_el_encendido_sigue_siendo_el_de_modis():
    raw = {"Lascar": [{"sensor": "VIIRS_NOAA20", "datetime_utc": "2026-11-01 06:30", "via_codigo_mirova": True,
                       "processed_utc": "2026-11-01T00:00:00Z"}]}
    assert vg.encendido_desde_datos(raw)["encendido_utc"] is None


# ------------------------------------------------------------------ pasadas
def test_las_pasadas_se_parean_con_el_mismo_sensor():
    """La misma noche, una alerta de VIIRS 375 y otra de VIIRS 750 a la misma hora: cada una con lo suyo."""
    t = "2026-11-10 05:00"
    filas = [_fila("NevadosDeChillan", t + ":00", 3.0, b="VIIRS375"), _fila("NevadosDeChillan", t + ":00", 4.0, b="VIIRS750")]
    prod = [_rec("NevadosDeChillan", "2026-11-10", "05:00", False, via=True, b="VIIRS375"),
            _rec("NevadosDeChillan", "2026-11-10", "05:00", True, via=True, b="VIIRS750")]
    guardia = [_rec("NevadosDeChillan", "2026-11-10", "05:00", True, b="VIIRS375"),
               _rec("NevadosDeChillan", "2026-11-10", "05:00", False, b="VIIRS750")]
    p375 = vg.pasadas_modis(filas, prod, guardia, VENTANA, diurna=NOCHE, sensor="VIIRS375")
    p750 = vg.pasadas_modis(filas, prod, guardia, VENTANA, diurna=NOCHE, sensor="VIIRS750")
    assert [(p["sensor"], p["prod_pub"], p["guardia_pub"]) for p in p375] == [("VIIRS375", False, True)]
    assert [(p["sensor"], p["prod_pub"], p["guardia_pub"]) for p in p750] == [("VIIRS750", True, False)]


# ------------------------------------------------------------------ disparadores
@pytest.mark.parametrize("s", ["VIIRS375", "VIIRS750"])
def test_una_protegida_que_la_guardia_publica_y_la_via_calla_dispara_la_reversion(s):
    d = _disp(s, [_pasada(s, "NevadosDeChillan", "2026-11-10 05:00", True, False, True)])
    assert d["veredicto"] == "REVERSION_CANDIDATA" and len(d["reversion"]) == 1


@pytest.mark.parametrize("s", ["VIIRS375", "VIIRS750"])
def test_una_protegida_que_las_dos_publican_no_dispara(s):
    assert _disp(s, [_pasada(s, "NevadosDeChillan", "2026-11-10 05:00", True, True, True)])["veredicto"] == "VERDE"


@pytest.mark.parametrize("s", ["VIIRS375", "VIIRS750"])
def test_caida_a_k_que_calla_investiga_y_no_revierte(s):
    p = _pasada(s, "Lascar", "2026-11-10 05:00", True, False, True, prod_via=False, caida="sin_grilla")
    d = _disp(s, [p])
    assert d["reversion"] == [] and d["veredicto"] == "INVESTIGAR"
    assert len(d["protegidas_calladas_por_k_de_produccion"]) == 1


def test_una_protegida_sin_record_de_la_via_investiga_pasada_la_espera():
    p = _pasada("VIIRS375", "Lascar", "2026-11-10 05:00", True, None, True)
    assert _disp("VIIRS375", [p], ahora="2026-11-12 00:00:00")["veredicto"] == "INVESTIGAR"
    assert _disp("VIIRS375", [p], ahora="2026-11-10 09:00:00")["veredicto"] == "VERDE"


def test_las_minimas_de_d9_no_cuentan_como_muy_bajo():
    """D-9: una alerta de 0,05 MW o menos en VIIRS 375 es «MIROVA no vio nada»."""
    pas = [_pasada("VIIRS375", "Lascar", f"2026-11-1{i} 05:00", False, False, True, vrp=0.03, minima=True) for i in range(5)]
    d = _disp("VIIRS375", pas)
    assert d["muy_bajo"]["k"] == 0 and d["veredicto"] == "VERDE"


def test_muy_bajo_perdidas_sobre_la_cota_pide_investigar():
    pas = [_pasada("VIIRS375", "Lascar", f"2026-11-1{i} 05:00", False, False, True, vrp=0.3) for i in range(3)]
    d = _disp("VIIRS375", pas)
    assert d["muy_bajo"]["k"] == 3 and d["muy_bajo"]["dispara"] is True and d["veredicto"] == "INVESTIGAR"
    d = _disp("VIIRS375", pas[:2])
    assert d["muy_bajo"]["dispara"] is False and d["veredicto"] == "VERDE"


def test_una_cota_pendiente_informa_sin_disparar():
    """Sin fuente citable la regla deja la cota PENDIENTE DE NICOLÁS: se cuenta y no se inventa un umbral (A115)."""
    pas = [_pasada("VIIRS750", "Lascar", f"2026-11-1{i} 05:00", False, False, True, vrp=0.3) for i in range(9)]
    d = _disp("VIIRS750", pas, cotas={"muy_bajo": None, "sobrepublicacion": None})
    assert d["muy_bajo"]["k"] == 9 and d["muy_bajo"]["dispara"] is False and d["muy_bajo"]["cota"] is None
    assert d["veredicto"] == "VERDE"


def _par_neg(s, fecha, hhmm, prod_pub, guardia_pub):
    return (_rec("Lascar", fecha, hhmm, prod_pub, via=True, b=s, lab="neg_limpio"),
            _rec("Lascar", fecha, hhmm, guardia_pub, b=s))


def test_sobrepublicacion_cuenta_solo_el_sensor_vigilado():
    pares = [_par_neg("VIIRS750", f"2026-11-1{i}", "05:00", True, False) for i in range(4)]
    prod, guardia = [p[0] for p in pares], [p[1] for p in pares]
    d = _disp("VIIRS750", [], prod, guardia)
    assert d["sobrepublicacion"]["k"] == 4 and d["sobrepublicacion"]["dispara"] is True and d["veredicto"] == "INVESTIGAR"
    # los mismos records vistos desde el otro sensor no cuentan
    d = _disp("VIIRS375", [], prod, guardia)
    assert d["sobrepublicacion"]["k"] == 0 and d["veredicto"] == "VERDE"


def test_la_cota_pendiente_de_sobrepublicacion_no_dispara():
    """VPR967-02: una cota en None significa PENDIENTE DE NICOLAS, no cero. Una sola sobre-publicacion no abre INVESTIGAR."""
    prod, guardia = _par_neg("VIIRS750", "2026-11-10", "05:00", True, False)
    d = _disp("VIIRS750", [], [prod], [guardia], cotas={"muy_bajo": None, "sobrepublicacion": None})
    assert d["sobrepublicacion"]["k"] == 1 and d["sobrepublicacion"]["cota"] is None
    assert d["sobrepublicacion"]["dispara"] is False and d["veredicto"] == "VERDE"


@pytest.mark.parametrize("s", ["VIIRS375", "VIIRS750"])
def test_el_nulo_antes_del_encendido_es_por_sensor(s):
    otro = "VIIRS750" if s == "VIIRS375" else "VIIRS375"
    g = [_rec("Lascar", "2026-11-02", "05:00", True, b=s), _rec("Lascar", "2026-11-02", "05:00", True, b=otro)]
    p = [_rec("Lascar", "2026-11-02", "05:00", False, b=s), _rec("Lascar", "2026-11-02", "05:00", True, b=otro)]
    d = _disp(s, [], p, g, enc=None, hoy="2026-11-03")
    assert d["nulo"]["pares"] == 1 and d["nulo"]["distintas"] == 1 and d["veredicto"] == "INVESTIGAR"
    d = _disp(otro, [], p, g, enc=None, hoy="2026-11-03")
    assert d["nulo"]["pares"] == 1 and d["nulo"]["distintas"] == 0 and d["veredicto"] == "VERDE"


def test_plazo_29_protegidas():
    pas = [_pasada("VIIRS375", "Lascar", f"2026-11-{6 + i // 12:02d} {i % 12 + 1:02d}:00", True, True, True) for i in range(29)]
    calla = _pasada("VIIRS375", "Lascar", "2026-11-19 05:00", True, False, True)
    d = _disp("VIIRS375", pas + [calla], hoy="2026-11-20")
    assert d["duracion"]["protegidas_vistas_en_guardia"] == 30
    assert d["reversion"] == [] and len(d["fuera_de_plazo"]) == 1 and d["veredicto"] == "CANDIDATA_FUERA_DE_PLAZO"


def test_pasada_juzgada_no_dispara_y_la_clave_lleva_el_sensor():
    p = _pasada("VIIRS750", "Lascar", "2026-11-10 05:00", True, False, True)
    j = {("Lascar", "VIIRS750", "2026-11-10 05:00"): {"decision": "no revertir"}}
    assert _disp("VIIRS750", [p], juzgadas=j)["veredicto"] == "VERDE"
    j_otro = {("Lascar", "VIIRS375", "2026-11-10 05:00"): {"decision": "no revertir"}}
    assert _disp("VIIRS750", [p], juzgadas=j_otro)["veredicto"] == "REVERSION_CANDIDATA"


# ------------------------------------------------------------------ flags y avisos
def test_el_flag_de_cada_sensor_se_lee_de_pipeline_profile():
    # S177 B1: la vía de VIIRS 375 pasa a encendida en producción. Texto original: las dos de VIIRS en False.
    assert vg.flag_produccion_encendido("VIIRS375") is True and vg.flag_produccion_encendido("VIIRS750") is False
    assert vg.flag_produccion_encendido("MODIS") is True, "control: la de MODIS está encendida desde #934"
    assert vg.flag_produccion_encendido() is True


@pytest.mark.parametrize("s,etiqueta", [("VIIRS375", "VIIRS 375"), ("VIIRS750", "VIIRS 750")])
def test_los_avisos_nombran_el_sensor_vigilado(s, etiqueta):
    av = vg.avisos_via(True, None, [], sensor=s)
    assert len(av) == 1 and etiqueta in av[0] and "MODIS" not in av[0]
    av = vg.avisos_referencia_modis([], "2026-11-20", sensor=s)
    assert len(av) == 1 and etiqueta in av[0] and "MODIS" not in av[0]


def test_la_via_detenida_en_un_volcan_se_avisa_nombrando_el_sensor():
    prod = [_rec("Lascar", "2026-11-19", "05:00", False, via=False, b="VIIRS750"),
            _rec("Lascar", "2026-11-06", "05:00", False, via=True, b="VIIRS750")]
    av = vg.avisos_via(True, "2026-11-05 22:10:00", prod, vols=["Lascar"], sensor="VIIRS750")
    assert len(av) == 1 and "Lascar" in av[0] and "VIIRS 750" in av[0] and "MODIS" not in av[0]


def test_las_caidas_a_k_son_por_sensor_y_nombran_el_sensor():
    prod = [_rec("Lascar", "2026-11-19", "05:00", False, b="VIIRS375", caida="sin_grilla"),
            _rec("Lascar", "2026-11-19", "05:00", False, b="VIIRS750", caida="sin_grilla")]
    c = vg.caidas_a_k("2026-11-05 22:10:00", prod, sensor="VIIRS375")
    assert [x["sensor"] for x in c] == ["VIIRS_NOAA20"]
    av = vg.avisos_caidas(True, "2026-11-05 22:10:00", prod, "2026-11-20", sensor="VIIRS375")
    assert len(av) == 1 and "VIIRS 375" in av[0] and "MODIS" not in av[0]


def test_avisos_perfiles_con_la_guardia_de_viirs():
    g = [_rec("Lascar", "2026-11-19", "05:00", True, perfil="mirova_equivalent")]
    assert vg.avisos_perfiles([], g, 0, perfil_guardia="guardia_k_viirs")
    p = [_rec("Lascar", "2026-11-19", "05:00", True, perfil="guardia_k_viirs")]
    assert vg.avisos_perfiles(p, [], 0, perfil_guardia="guardia_k_viirs")
    assert not vg.avisos_perfiles([], [_rec("Lascar", "2026-11-19", "05:00", True, perfil="guardia_k_viirs")], 0,
                                  perfil_guardia="guardia_k_viirs")


# ------------------------------------------------------------------ la región sensible de VIIRS 750 (decisión 7)
def test_la_lista_de_volcanes_sensibles_sale_de_la_grilla():
    assert vv.volcanes_sens() == ["PuyehueCordonCaulle", "Tupungatito"]


def test_informe_sens_cuenta_lo_que_la_guardia_publica_y_la_via_no_sin_disparar():
    t = "2026-11-10"
    prod = [_rec("Tupungatito", t, "05:00", False, via=True, b="VIIRS750"),
            _rec("Tupungatito", t, "06:00", True, via=True, b="VIIRS750"),
            _rec("Lascar", t, "05:00", False, via=True, b="VIIRS750")]
    guardia = [_rec("Tupungatito", t, "05:00", True, b="VIIRS750"), _rec("Tupungatito", t, "06:00", True, b="VIIRS750"),
               _rec("Lascar", t, "05:00", True, b="VIIRS750")]
    inf = vv.informe_sens(prod, guardia, ENC, ["Tupungatito"])
    assert inf["Tupungatito"]["pares"] == 2 and inf["Tupungatito"]["solo_guardia"] == 1
    assert inf["Tupungatito"]["solo_via"] == 0 and inf["Tupungatito"]["pasadas_solo_guardia"] == [f"{t} 05:00"]
    assert "Lascar" not in inf


def test_informe_sens_vacio_antes_del_encendido():
    assert vv.informe_sens([], [], None, ["Tupungatito"]) == {}


# ------------------------------------------------------------------ la cadena desde el disco
def _crudo(cuando, publica, marca=None, sensor="VIIRS_NOAA20"):
    r = {"sensor": sensor, "datetime_utc": cuando, "processed_utc": cuando[:10] + "T09:00:00Z",
         "distance_class": "summit" if publica else None, "vrp_mw": 3.0 if publica else 0.0,
         "primary_cluster": {"vrp_mw": 3.0, "centroid_dist_km": 1.0} if publica else None, "anomaly_pixels": []}
    if marca is not None:
        r["via_codigo_mirova"] = marca
    return r


def _node_falso(casos):
    return [[None, None, None, 1.0 if c[0]["distance_class"] == "summit" else 0.0, c[0]["distance_class"] == "summit"]
            for c in casos]


def _disco_base(plat, via=True):
    prod, guardia = {v: [] for v in VOLS_CASO}, {v: [] for v in VOLS_CASO}
    for v in VOLS_CASO:
        prod[v].append(_crudo("2026-11-01 06:00", False, sensor=plat))
        guardia[v].append(_crudo("2026-11-01 06:00", False, sensor=plat))
        for dia in ("06", "12", "16", "19"):
            prod[v].append(_crudo(f"2026-11-{dia} 06:00", False, marca=True if via else None, sensor=plat))
            guardia[v].append(_crudo(f"2026-11-{dia} 06:00", False, sensor=plat))
    return prod, guardia


ALERTA = "2026-11-10 06:00"


def _ref(b):
    return [_fila("Lascar", "2026-11-19 06:00:00", 0.0, tipo="RUTINA", b=b)]


@pytest.fixture
def disco(tmp_path, monkeypatch):
    import banco_paridad as bp
    import referencia_mirova_unificada as rmu

    def poner(prod, guardia, filas, flag=True):
        for nombre, datos in (("prod", prod), ("guardia", guardia)):
            (tmp_path / nombre).mkdir(exist_ok=True)
            for v, recs in datos.items():
                (tmp_path / nombre / f"{v}.json").write_text(json.dumps({"volcano": v, "records": recs}), encoding="utf-8")
        monkeypatch.setattr(vv, "PRODUCCION", str(tmp_path / "prod"))
        monkeypatch.setattr(vv, "GUARDIA", str(tmp_path / "guardia"))
        monkeypatch.setattr(bp, "DATA", tmp_path / "prod")
        monkeypatch.setattr(bp, "VOLS", VOLS_CASO)
        monkeypatch.setattr(vg.aa, "VOLS", VOLS_CASO)
        monkeypatch.setattr(bp, "correr_node", _node_falso)
        monkeypatch.setattr(rmu, "cargar_referencia_unificada", lambda *a, **k: filas)
        monkeypatch.setattr(vg, "flag_produccion_encendido", lambda sensor="MODIS": flag)
        monkeypatch.setattr(vv, "leer_juzgadas", lambda *a: {})
        monkeypatch.setattr(vv, "volcanes_sens", lambda: [])
        for s in vv.COTAS:                      # con la vía encendida la regla exige cotas (test_cadena_cota_pendiente...)
            monkeypatch.setitem(vv.COTAS, s, {"muy_bajo": 7, "sobrepublicacion": 8})   # distintas de las de MODIS
    return poner


CASOS = [("VIIRS375", "VIIRS_NOAA20", "v375"), ("VIIRS750", "VIIRS_NOAA20_750", "v750")]


@pytest.mark.parametrize("b,plat,clave", CASOS)
def test_cadena_control_con_la_via_fresca_da_verde(disco, b, plat, clave):
    disco(*_disco_base(plat), _ref(b))
    out = vv.evaluar("2026-11-20", clave)
    assert out["encendido_utc"] == "2026-11-06 09:00:00" and out["sensor"] == b
    assert out["veredicto"] == "VERDE", out["avisos"]


@pytest.mark.parametrize("b,plat,clave", CASOS)
def test_cadena_produccion_sin_datos_frescos_da_vigilancia_ciega(disco, b, plat, clave):
    """VPR967-03: si el NRT deja de escribir este sensor en un volcan, la vigilancia lo dice. Control: la guardia sigue fresca."""
    prod, guardia = _disco_base(plat)
    prod["Lascar"] = [r for r in prod["Lascar"] if r["datetime_utc"] < "2026-11-01 12:00"]
    disco(prod, guardia, _ref(b))
    out = vv.evaluar("2026-11-20", clave)
    assert out["veredicto"] == "VIGILANCIA_CIEGA", out["avisos"]
    assert any("producción" in a and "Lascar" in a and b in a for a in out["avisos"]), out["avisos"]


@pytest.mark.parametrize("b,plat,clave", CASOS)
def test_cadena_la_via_que_calla_una_protegida_es_candidata(disco, b, plat, clave):
    prod, guardia = _disco_base(plat)
    prod["NevadosDeChillan"].append(_crudo(ALERTA, False, marca=True, sensor=plat))
    guardia["NevadosDeChillan"].append(_crudo(ALERTA, True, sensor=plat))
    disco(prod, guardia, _ref(b) + [_fila("NevadosDeChillan", ALERTA + ":00", 25.0, b=b)])
    out = vv.evaluar("2026-11-20", clave)
    assert out["veredicto"] == "REVERSION_CANDIDATA", out
    assert [p["sensor"] for p in out["reversion"]] == [b]


@pytest.mark.parametrize("b,plat,clave", CASOS)
def test_cadena_un_volcan_sin_archivo_de_guardia_no_tapa_la_candidata_de_otro(disco, b, plat, clave):
    """VPR967-06: si el job de la guardia de un volcán falla y no deja archivo, la alerta callada en otro volcán se sigue viendo.
    El volcán sin archivo sale como aviso de frescura, y la lista de volcanes del banco queda como estaba."""
    import banco_paridad as bp
    prod, guardia = _disco_base(plat)
    prod["NevadosDeChillan"].append(_crudo(ALERTA, False, marca=True, sensor=plat))
    guardia["NevadosDeChillan"].append(_crudo(ALERTA, True, sensor=plat))
    del guardia["Lascar"]
    disco(prod, guardia, _ref(b) + [_fila("NevadosDeChillan", ALERTA + ":00", 25.0, b=b)])
    out = vv.evaluar("2026-11-20", clave)
    assert out["veredicto"] == "REVERSION_CANDIDATA", out
    assert [p["volcano"] for p in out["reversion"]] == ["NevadosDeChillan"]
    assert any("Lascar" in a for a in out["avisos"]), out["avisos"]
    assert bp.VOLS == VOLS_CASO


def test_cadena_la_vigilancia_de_modis_tolera_el_mismo_volcan_sin_archivo(disco, tmp_path, monkeypatch):
    """VPR967-06, A102: la vigilancia de MODIS tenía la misma línea. Control: el volcán con archivo sí trae sus records."""
    prod, guardia = _disco_base("MODIS_AQUA")
    del guardia["Lascar"]
    disco(prod, guardia, _ref("MODIS"))
    monkeypatch.setattr(vg, "GUARDIA", str(tmp_path / "guardia"))
    _filas, _prod, en_guardia, _n = vg.cargar_insumos(VENTANA, set())
    assert en_guardia and {r["vol"] for r in en_guardia} == {"NevadosDeChillan"}


@pytest.mark.parametrize("b,plat,clave", CASOS)
def test_cadena_la_caida_a_k_que_calla_investiga(disco, b, plat, clave):
    prod, guardia = _disco_base(plat)
    prod["NevadosDeChillan"].append(_crudo(ALERTA, False, marca="sin_grilla", sensor=plat))
    guardia["NevadosDeChillan"].append(_crudo(ALERTA, True, sensor=plat))
    disco(prod, guardia, _ref(b) + [_fila("NevadosDeChillan", ALERTA + ":00", 25.0, b=b)])
    out = vv.evaluar("2026-11-20", clave)
    assert out["reversion"] == [] and out["veredicto"] == "INVESTIGAR", out


def test_cadena_una_alerta_del_otro_sensor_no_toca_a_este(disco):
    """La vía de VIIRS 750 calla una protegida: la vigilancia de VIIRS 375, sin nada que ver, no dispara."""
    prod, guardia = _disco_base("VIIRS_NOAA20")
    prod["NevadosDeChillan"].append(_crudo(ALERTA, False, marca=True, sensor="VIIRS_NOAA20_750"))
    guardia["NevadosDeChillan"].append(_crudo(ALERTA, True, sensor="VIIRS_NOAA20_750"))
    disco(prod, guardia, _ref("VIIRS375") + [_fila("NevadosDeChillan", ALERTA + ":00", 25.0, b="VIIRS750")])
    assert vv.evaluar("2026-11-20", "v375")["veredicto"] == "VERDE"


def test_cadena_antes_del_encendido_mide_el_nulo_y_el_flag_apagado_no_da_aviso(disco):
    plat = "VIIRS_NOAA20"
    prod, guardia = _disco_base(plat, via=False)
    disco(prod, guardia, _ref("VIIRS375"), flag=False)
    out = vv.evaluar("2026-11-08", "v375")
    assert out["fase"] == "antes_del_encendido" and out["encendido_utc"] is None
    assert out["nulo"]["pares"] > 0 and out["nulo"]["distintas"] == 0
    assert out["veredicto"] == "VERDE", out["avisos"]


def test_cadena_guardia_sin_datos_frescos_da_vigilancia_ciega(disco):
    plat = "VIIRS_NOAA20"
    prod, guardia = _disco_base(plat)
    guardia["Lascar"] = [r for r in guardia["Lascar"] if r["datetime_utc"] < "2026-11-07"]
    disco(prod, guardia, _ref("VIIRS375"))
    out = vv.evaluar("2026-11-20", "v375")
    assert out["veredicto"] == "VIGILANCIA_CIEGA" and any("guardia" in a and "Lascar" in a for a in out["avisos"])


def test_cadena_guardia_con_records_de_la_via_da_vigilancia_ciega(disco):
    plat = "VIIRS_NOAA20"
    prod, guardia = _disco_base(plat)
    guardia["Lascar"].append(_crudo("2026-11-18 06:00", False, marca=True, sensor=plat))
    disco(prod, guardia, _ref("VIIRS375"))
    out = vv.evaluar("2026-11-20", "v375")
    assert out["veredicto"] == "VIGILANCIA_CIEGA" and any("dejó de ser K" in a for a in out["avisos"])


def test_cadena_flag_encendido_sin_records_de_la_via_da_vigilancia_ciega(disco):
    plat = "VIIRS_NOAA20"
    prod, guardia = _disco_base(plat, via=False)
    disco(prod, guardia, _ref("VIIRS375"), flag=True)
    out = vv.evaluar("2026-11-20", "v375")
    assert out["veredicto"] == "VIGILANCIA_CIEGA" and any("flag" in a and "VIIRS 375" in a for a in out["avisos"])


def test_cadena_referencia_sin_filas_del_sensor_da_vigilancia_ciega(disco):
    plat = "VIIRS_NOAA20"
    disco(*_disco_base(plat), _ref("VIIRS750"))
    out = vv.evaluar("2026-11-20", "v375")
    assert out["veredicto"] == "VIGILANCIA_CIEGA" and any("VIIRS 375" in a for a in out["avisos"])


def test_main_escribe_el_latest_y_el_historial_del_sensor(disco, tmp_path, monkeypatch):
    disco(*_disco_base("VIIRS_NOAA20_750"), _ref("VIIRS750"))
    monkeypatch.setattr(vv, "OUTDIR", str(tmp_path / "salida"))
    monkeypatch.setattr(vv, "_hoy", lambda: "2026-11-20")
    vv.main(["--sensor", "v750"])
    latest = json.loads((tmp_path / "salida" / "guardia_v750_latest.json").read_text(encoding="utf-8"))
    assert latest["sensor"] == "VIIRS750" and latest["veredicto"] == "VERDE"
    linea = json.loads((tmp_path / "salida" / "guardia_v750_history.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert linea["sensor"] == "VIIRS750" and linea["date"] == "2026-11-20"


def test_main_exige_el_sensor():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "vigilancia_guardia_viirs.py")], capture_output=True,
                       text=True, encoding="utf-8")
    assert r.returncode != 0 and "--sensor" in r.stderr


# ------------------------------------------------------------------ archivo de juzgadas y workflow
def test_el_archivo_de_juzgadas_nace_vacio_y_se_lee():
    d = json.loads(Path(vv.JUZGADAS).read_text(encoding="utf-8"))
    assert d["pasadas"] == [] and "esquema" in d
    assert vv.leer_juzgadas(vv.JUZGADAS) == {}


def _wf():
    return yaml.safe_load(WF.read_text(encoding="utf-8")), WF.read_text(encoding="utf-8")


def test_el_workflow_escucha_a_la_guardia_y_cubre_los_dos_sensores():
    d, _ = _wf()
    guardia = yaml.safe_load(GUARDIA_WF.read_text(encoding="utf-8"))
    assert "on" in d and True not in d, "'on' entre comillas (A43)"
    assert d["on"]["workflow_run"]["workflows"] == [guardia["name"]]
    assert d["on"].get("schedule") and "workflow_dispatch" in d["on"]
    assert d["jobs"]["vigilar"]["strategy"]["matrix"]["sensor"] == ["v375", "v750"]
    assert d["jobs"]["vigilar"]["strategy"]["fail-fast"] is False
    assert d["concurrency"]["group"] == "vigilancia-guardia-viirs"


def test_el_workflow_abre_issues_con_prefijo_propio_de_cada_sensor_y_no_revierte():
    d, txt = _wf()
    assert "git revert" not in "".join(s.get("run", "") for s in d["jobs"]["vigilar"]["steps"] if "git push" in s.get("run", ""))
    for clase in ("candidata a reversion", "candidata fuera de plazo", "investigar", "vigilancia ciega", "caidas a K",
                  "el script fallo"):
        assert f'abrir "Guardia K de $ETIQUETA: {clase}"' in txt, clase
    assert "--sensor \"${{ matrix.sensor }}\"" in txt
    assert "guardia_${{ matrix.sensor }}_latest.json" in txt and "guardia_${{ matrix.sensor }}_history.jsonl" in txt
    assert "REGLA_REVERSION_V375E_BORRADOR.md" in txt


def test_no_se_toca_la_regla_sellada_de_modis():
    r = subprocess.run(["git", "diff", "--name-only", "origin/main", "--", "experiments/_s171_modd_adopcion/"], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        pytest.skip("sin origin/main en este checkout")
    assert r.stdout.strip() == ""


def test_cadena_cota_pendiente_con_la_via_encendida_da_vigilancia_ciega(disco, monkeypatch):
    """Una cota PENDIENTE DE NICOLÁS con la vía encendida es un disparador apagado: el encendido exige fijarla."""
    plat = "VIIRS_NOAA20"
    disco(*_disco_base(plat), _ref("VIIRS375"))
    monkeypatch.setitem(vv.COTAS, "VIIRS375", {"muy_bajo": None, "sobrepublicacion": 3})
    out = vv.evaluar("2026-11-20", "v375")
    assert out["veredicto"] == "VIGILANCIA_CIEGA"
    assert any("PENDIENTE" in a and "muy_bajo" in a and "VIIRS 375" in a for a in out["avisos"]), out["avisos"]


def test_una_cota_pendiente_con_la_via_apagada_no_avisa():
    assert vv.avisos_cotas(False, "VIIRS375") == []


def test_cadena_las_cotas_son_las_del_sensor(disco):
    """Las cotas de la regla por sensor llegan a los disparadores (si faltaran, regirían en silencio las de MODIS)."""
    disco(*_disco_base("VIIRS_NOAA20"), _ref("VIIRS375"))
    out = vv.evaluar("2026-11-20", "v375")
    assert out["muy_bajo"]["cota"] == vv.COTAS["VIIRS375"]["muy_bajo"]
    assert out["sobrepublicacion"]["cota"] == vv.COTAS["VIIRS375"]["sobrepublicacion"]


def test_cadena_una_minima_de_d9_cuenta_como_negativo_limpio(disco):
    """D-9: una alerta de 0,05 MW o menos en VIIRS 375 es «MIROVA no vio nada»; la vía que publica ahí sobre-publica."""
    t = "2026-11-10 06:00"
    prod, guardia = _disco_base("VIIRS_NOAA20")
    prod["Lascar"].append(_crudo(t, True, marca=True))
    guardia["Lascar"].append(_crudo(t, False))
    disco(prod, guardia, _ref("VIIRS375") + [_fila("Lascar", t + ":00", 0.03)])
    out = vv.evaluar("2026-11-20", "v375")
    assert out["sobrepublicacion"]["n"] >= 1 and out["sobrepublicacion"]["k"] == 1, out["sobrepublicacion"]


def test_cotas_selladas_son_las_de_la_regla_s178():
    """S178: Nicolás selló la regla de reversión de VIIRS («Sello la regla», 2026-11-10). Las cotas del vigilante son las de
    la tabla §4.4 de experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md (D1 C-rad y D2), y el texto de la
    regla las dice con «más de»: si una cambia en un lado y no en el otro, esta prueba cae."""
    assert vv.COTAS == {"VIIRS375": {"muy_bajo": 14, "sobrepublicacion": 17},
                        "VIIRS750": {"muy_bajo": 12, "sobrepublicacion": 2}}
    regla = (ROOT / "experiments" / "_s176_v375e_adopcion" / "REGLA_REVERSION_V375E_BORRADOR.md").read_text(encoding="utf-8")
    assert "**SELLADA el 2026-11-10" in regla
    fila375 = next(l for l in regla.splitlines() if l.startswith("| VIIRS 375 (S178, D1 contestada) |"))
    fila750 = next(l for l in regla.splitlines() if l.startswith("| VIIRS 750 |"))
    assert "**más de 14**" in fila375 and "**más de 17**" in fila375
    assert "**más de 12**" in fila750 and "**más de 2**" in fila750
