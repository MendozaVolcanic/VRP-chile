# -*- coding: utf-8 -*-
"""S175 (docs/AUDIT_S175.md §8, decisión 11; hallazgos 151, 152, 153 y V1-01; decisión 3 de S174, hallazgo 253): la
vigilancia de la guardia K de MODIS mira, por volcán y por pasada, si el record de producción es de la vía.

POR QUÉ, COMO GEÓLOGO. La vigilancia existe para ver si la vía «código MIROVA» calla un cráter que K ve. Cuando la vía
no puede correr en un gránulo (volcán sin grilla de MIROVA, MxD03 ausente o de otra forma) el procesador escribe K con
la marca en texto (`via_codigo_mirova`: "sin_grilla", "sin_mxd03", "geo_distinta"). Esa pasada compara K con K: no
dice nada de la vía. Antes de S175 la vigilancia no lo miraba del lado prospectivo:
- una caída a K que calla una protegida que la guardia publica daba REVERSION_CANDIDATA contra la vía (151, mutación
  M6 de experiments/_s175_audit/f1/mutaciones_vigilancia.py);
- si la vía caía a K, o dejaba de escribir, en un solo volcán, la vigilancia daba VERDE sin aviso (152, M2 y M2c),
  porque comparaba la última noche de la vía con la última de MODIS sumando los 11 volcanes;
- las protegidas K contra K avanzaban el plazo de 29 (V1-01).
Decisión 3 de S174 («Sí, a todo», 2026-11-05): esos records se tratan como K y se listan como aviso.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Cada caso nuevo tiene su control: la misma escena con el record de la vía
dispara lo de siempre (reversión, plazo, VERDE), así que la prueba puede dar los dos resultados. (2) Las escenas son
sintéticas, sin red ni node; la corrida de las mutaciones M2, M6 y M2c sobre los datos reales vive en la descripción
del PR.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.vigilancia_guardia_modis as vg  # noqa: E402

ENC = "2026-11-05 22:10:00"
NOCHE = lambda *a: False  # noqa: E731
VOLS_CASO = ["NevadosDeChillan", "Lascar"]


def _fila(vol, fecha, vrp, tipo="ALERTA_TERMICA", b="MODIS", source="CONS"):
    return {"volcano": vol, "sensor_bucket": b, "fecha_utc": fecha, "vrp_mw": vrp, "tipo": tipo, "source": source}


def _rec(vol, fecha, hhmm, pub, via=None, caida=None, lab="sin_info", sensor="MODIS_AQUA"):
    dt = datetime.strptime(f"{fecha} {hhmm}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": vol, "b": "MODIS", "dt": dt, "noche": fecha, "pub": pub, "sensor": sensor, "perfil": None,
            "lab": lab, "via": via, "caida_k": caida}


def _pasada(vol, fecha, protegida, prod, guardia, prod_via, vrp=None):
    return {"volcano": vol, "sensor": "MODIS", "fecha_utc": fecha[:16], "instante_utc": fecha[:16] + ":00",
            "vrp_mirova_mw": vrp if vrp is not None else (2.0 if protegida else 0.3), "protegida": protegida,
            "minima": False, "referencia_sospechosa": False, "prod_pub": prod, "guardia_pub": guardia,
            "prod_via": prod_via}


def _disp(pas, prod=(), guardia=(), hoy="2026-11-20"):
    return vg.disparadores(list(pas), list(prod), list(guardia), hoy=hoy, encendido=ENC)


# ------------------------------------------------------------------ 151 / M6: la caída a K no es la vía
def test_m6_una_caida_a_k_que_calla_no_es_reversion_pide_investigar():
    """M6: el record de producción de la protegida es K (la vía cayó) y calla; la guardia publica. La diferencia es
    entre dos corridas de K, no de la vía: investigar, nunca la reversión pre-autorizada."""
    d = _disp([_pasada("NevadosDeChillan", "2026-11-10 07:45", True, False, True, prod_via=False, vrp=25.0)])
    assert d["reversion"] == [] and d["fuera_de_plazo"] == []
    assert d["veredicto"] == "INVESTIGAR"
    assert [p["fecha_utc"] for p in d["protegidas_calladas_por_k_de_produccion"]] == ["2026-11-10 07:45"]
    # control: la misma pasada con el record de la vía sí es la reversión
    d = _disp([_pasada("NevadosDeChillan", "2026-11-10 07:45", True, False, True, prod_via=True, vrp=25.0)])
    assert d["veredicto"] == "REVERSION_CANDIDATA" and d["protegidas_calladas_por_k_de_produccion"] == []


# ------------------------------------------------------------------ V1-01: el plazo de 29 no cuenta K contra K
def test_v1_01_el_plazo_de_29_no_avanza_con_protegidas_k_contra_k():
    k_contra_k = [_pasada("A", f"2026-11-{6 + i // 4:02d} {10 + i % 4:02d}:00", True, True, True, prod_via=False)
                  for i in range(29)]
    calla = _pasada("A", "2026-11-20 07:20", True, False, True, prod_via=True)
    d = _disp(k_contra_k + [calla], hoy="2026-11-21")
    assert d["duracion"]["protegidas_vistas_en_guardia"] == 1
    assert d["veredicto"] == "REVERSION_CANDIDATA" and len(d["reversion"]) == 1
    # control: con las 29 de la vía, la 30.a sí queda fuera de plazo
    de_la_via = [dict(p, prod_via=True) for p in k_contra_k]
    d = _disp(de_la_via + [calla], hoy="2026-11-21")
    assert d["duracion"]["protegidas_vistas_en_guardia"] == 30 and d["veredicto"] == "CANDIDATA_FUERA_DE_PLAZO"


def test_muy_bajo_y_sobrepublicacion_solo_miran_pasadas_de_la_via():
    """(i) y (ii) de §4.4 miden a la vía: tres Muy Bajo K contra K no disparan, y un negativo limpio que la caída a K
    publica no es sobre-publicación de la vía."""
    tres = [_pasada("A", f"2026-11-1{i} 07:20", False, False, True, prod_via=False, vrp=0.3) for i in range(3)]
    d = _disp(tres)
    assert d["muy_bajo"]["k"] == 0 and d["muy_bajo"]["n"] == 0 and d["veredicto"] == "VERDE"
    d = _disp([dict(p, prod_via=True) for p in tres])
    assert d["muy_bajo"]["k"] == 3 and d["muy_bajo"]["dispara"] is True

    def par(i, via, caida):
        f = f"2026-11-1{i}"
        return _rec("A", f, "07:20", True, via=via, caida=caida, lab="neg_limpio"), _rec("A", f, "07:20", False)
    pares = [par(i, False, "sin_grilla") for i in range(4)]
    d = _disp([], [p for p, _ in pares], [g for _, g in pares])
    assert d["sobrepublicacion"]["k"] == 0 and d["sobrepublicacion"]["n"] == 0
    pares = [par(i, True, None) for i in range(4)]
    d = _disp([], [p for p, _ in pares], [g for _, g in pares])
    assert d["sobrepublicacion"]["k"] == 4 and d["sobrepublicacion"]["dispara"] is True


# ------------------------------------------------------------------ 153: el descarte de borde se nombra
def test_el_descarte_de_borde_nombra_cada_pasada():
    guardia = [_rec("Villarrica", "2026-11-11", "07:10", False)]
    d = _disp([], [], guardia)
    assert d["borde_171_01"]["pasadas"] == [{"volcano": "Villarrica", "sensor": "MODIS_AQUA",
                                             "fecha_utc": "2026-11-11 07:10"}]
    assert d["veredicto"] == "VERDE", "sigue sin disparar: la regla no da cota (A115)"


# ------------------------------------------------------------------ 152 / M2 / M2c: por volcán
@pytest.fixture
def insumos(monkeypatch):
    def poner(filas, prod, guardia, enc=ENC, flag=True):
        monkeypatch.setattr(vg, "cargar_insumos", lambda win, via, caidas=None: (filas, prod, guardia, 0))
        monkeypatch.setattr(vg, "leer_encendido", lambda: {"encendido_utc": enc, "primera_observacion": None,
                                                          "via": set(), "caidas": {}})
        monkeypatch.setattr(vg, "flag_produccion_encendido", lambda: flag)
        monkeypatch.setattr(vg.vs, "_diurna_por_defecto", lambda: NOCHE)
        monkeypatch.setattr(vg.aa, "VOLS", VOLS_CASO)
        monkeypatch.setattr(vg, "leer_juzgadas", lambda *a: {})
    return poner


def _caso():
    filas = [_fila("Lascar", "2026-11-19 06:00:00", 0.0, tipo="RUTINA")]
    prod, guardia = [], []
    for v in VOLS_CASO:
        for f in ("2026-11-01",):                        # antes del encendido: K en los dos lados (nulo)
            prod.append(_rec(v, f, "03:00", False))
            guardia.append(_rec(v, f, "03:00", False))
        for f in ("2026-11-08", "2026-11-12", "2026-11-16", "2026-11-19"):
            prod.append(_rec(v, f, "03:00", False, via=True))
            guardia.append(_rec(v, f, "03:00", False))
    return filas, prod, guardia


def test_control_las_dos_vias_frescas_dan_verde(insumos):
    insumos(*_caso())
    out = vg.evaluar("2026-11-20")
    assert out["veredicto"] == "VERDE", out["avisos"]


def test_m2_la_via_cae_a_k_en_un_solo_volcan_da_aviso(insumos):
    """M2: todos los records de la vía de Láscar pasan a K con la marca "sin_grilla"; Chillán sigue con la vía."""
    filas, prod, guardia = _caso()
    for r in prod:
        if r["vol"] == "Lascar" and r["via"] is True:
            r["via"], r["caida_k"] = False, "sin_grilla"
    insumos(filas, prod, guardia)
    out = vg.evaluar("2026-11-20")
    assert out["veredicto"] == "VIGILANCIA_CIEGA"
    assert any("Lascar" in a and "vía" in a for a in out["avisos"]), out["avisos"]
    assert not any("NevadosDeChillan" in a for a in out["avisos"]), out["avisos"]


def test_m2c_la_via_deja_de_escribir_en_un_solo_volcan_da_aviso(insumos):
    """M2c: desde el 2026-11-13 los records de Láscar ya no traen la marca de la vía (K); Chillán sigue con la vía."""
    filas, prod, guardia = _caso()
    for r in prod:
        if r["vol"] == "Lascar" and r["noche"] >= "2026-11-13":
            r["via"] = False
    insumos(filas, prod, guardia)
    out = vg.evaluar("2026-11-20")
    assert out["veredicto"] == "VIGILANCIA_CIEGA"
    assert any("Lascar" in a and "2026-11-12" in a for a in out["avisos"]), out["avisos"]


def test_decision_3_s174_una_caida_a_k_reciente_es_aviso_y_cuenta_como_k(insumos):
    """Una sola pasada que cae a K (la vía siguió escribiendo antes y después) no deja ciego al volcán por frescura,
    pero se lista como aviso (decisión 3 de S174) y no cuenta como la vía."""
    filas, prod, guardia = _caso()
    prod.append(_rec("Lascar", "2026-11-18", "05:00", False, via=False, caida="sin_grilla"))
    guardia.append(_rec("Lascar", "2026-11-18", "05:00", False))
    insumos(filas, prod, guardia)
    out = vg.evaluar("2026-11-20")
    assert out["veredicto"] == "VIGILANCIA_CIEGA"
    assert any("cayeron a K" in a and "Lascar" in a and "sin_grilla" in a for a in out["avisos"]), out["avisos"]
    assert out["caidas_a_k"] == [{"volcano": "Lascar", "sensor": "MODIS_AQUA", "fecha_utc": "2026-11-18 05:00",
                                  "marca": "sin_grilla"}]
    # una caída vieja (fuera de los DIAS_NULO días) queda listada pero ya no es aviso
    filas, prod, guardia = _caso()
    prod.append(_rec("Lascar", "2026-11-06", "05:00", False, via=False, caida="sin_grilla"))
    insumos(filas, prod, guardia)
    out = vg.evaluar("2026-11-21")
    assert len(out["caidas_a_k"]) == 1 and not any("cayeron a K" in a for a in out["avisos"])


def test_las_caidas_salen_de_los_datos_crudos():
    """encendido_desde_datos reúne, además de la vía, las caídas a K (marca en texto) de MODIS."""
    raw = {"Lascar": [
        {"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-06 06:30", "via_codigo_mirova": True,
         "processed_utc": "2026-11-06T09:00:00Z"},
        {"sensor": "MODIS_TERRA", "datetime_utc": "2026-11-07 03:10", "via_codigo_mirova": "sin_grilla"},
        {"sensor": "MODIS_TERRA", "datetime_utc": "2026-11-08 03:10"},
        {"sensor": "VIIRS_NOAA20_750", "datetime_utc": "2026-11-07 05:00", "via_codigo_mirova": "sin_grilla"}]}
    e = vg.encendido_desde_datos(raw)
    assert e["caidas"] == {("Lascar", "MODIS_TERRA", "2026-11-07 03:10"): "sin_grilla"}
