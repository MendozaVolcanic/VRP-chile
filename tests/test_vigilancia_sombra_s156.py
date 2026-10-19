# -*- coding: utf-8 -*-
"""S156 (arreglo 4 de docs/AUDIT_S155.md §5, V1-04): la vigilancia de la sombra existe y dispara lo que
la regla de adopción de K dice (experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md §4, paso 9, con la lectura
que Nicolás decidió el 2026-10-19: unidad = pasada; cuenta desde la adopción; lo anterior es retrospectivo).

POR QUE: K deja de publicar señal débil que el detector anterior (C0) veía. La sombra es el laboratorio
congelado en C0 (data/experimental_v2/) y su vigilancia es el disparador de la reversión pre-autorizada:
una alerta protegida que MIROVA publica, la sombra publica y producción calla. Hasta S156 la regla existía
y el código no. El verificador limpio de S156 hizo 17 mutaciones y las pruebas de la primera versión
atraparon 8: cada prueba marcada «mutación» de abajo nació de una que sobrevivió.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.vigilancia_sombra as vs  # noqa: E402

ADOP = "2026-10-18 09:57"
NOCHE = lambda *a: False  # noqa: E731


def _fila(vol, b, fecha, vrp, tipo="ALERTA_TERMICA", source="CONS"):
    return {"volcano": vol, "sensor_bucket": b, "fecha_utc": fecha, "vrp_mw": vrp, "tipo": tipo, "source": source}


def _rec(vol, b, hhmm, fecha, pub, sensor="VIIRS_NOAA21", perfil=None, lab="sin_info"):
    dt = datetime.strptime(f"{fecha} {hhmm}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": vol, "b": b, "dt": dt, "noche": fecha, "pub": pub, "sensor": sensor, "perfil": perfil,
            "lab": lab}


def _pasada(vol, b, fecha, protegida, prod, sombra, vrp=None):
    return {"volcano": vol, "sensor": b, "fecha_utc": fecha, "vrp_mirova_mw": vrp or (2.0 if protegida else 0.3),
            "protegida": protegida, "referencia_sospechosa": False, "prod_pub": prod, "sombra_pub": sombra}


def _disp(pas, negs=(), hoy="2026-10-25", adopcion=ADOP):
    return vs.disparadores(list(pas), list(negs), hoy=hoy, adopcion=adopcion)


# ------------------------------------------------------------------ cotas
def test_wilson_reproduce_la_cota_del_ab():
    """La regla cita V1 21 de 832 = [0,0166; 0,0383]."""
    lo, hi = vs.wilson(21, 832)
    assert round(lo, 4) == 0.0166 and round(hi, 4) == 0.0383
    assert vs.wilson(0, 0) == (None, None)


def test_las_cotas_salen_de_los_logs_del_ab():
    """Muy Bajo perdidas y negativos publicados de K, lectura A, de experiments/_s153_fk_v2/v1.log y v2.log §6."""
    assert vs.COTAS_AB["muy_bajo"] == {"VIIRS375": {"V1": (16, 194), "V2": (26, 388)}}
    assert vs.COTAS_AB["negativos"] == {"VIIRS375": {"V1": (21, 832), "V2": (37, 1010)}}
    assert vs.cota_superior("negativos", "VIIRS375") == max(vs.wilson(21, 832)[1], vs.wilson(37, 1010)[1])
    assert vs.cota_superior("muy_bajo", "MODIS") is None and vs.cota_superior("muy_bajo", "VIIRS750") is None
    v1 = (ROOT / "experiments" / "_s153_fk_v2" / "v1.log").read_text(encoding="utf-8")
    v2 = (ROOT / "experiments" / "_s153_fk_v2" / "v2.log").read_text(encoding="utf-8")
    assert "VIIRS375 K   Muy Bajo perdidas   16 de  194 | negativos publicados   21 de   832" in v1
    assert "VIIRS375 C0  Muy Bajo perdidas    0 de  194" in v1   # por eso la de K es la diferencial
    assert "VIIRS375 K   Muy Bajo perdidas   26 de  388 | negativos publicados   37 de  1010" in v2


def test_la_adopcion_sale_del_js_del_tablero():
    js = (ROOT / "frontend" / "cambio_detector.js").read_text(encoding="utf-8")
    a = vs.leer_adopcion()
    assert a is not None and f'CAMBIO_DETECTOR_UTC = "{a[:10]}T{a[11:]}' in js


# ------------------------------------------------------------------ pasadas
def test_clasifica_pasadas_de_alerta_con_produccion_y_sombra():
    filas = [_fila("NevadosDeChillan", "MODIS", "2026-10-20 07:20:00", 2.18),
             _fila("Villarrica", "VIIRS375", "2026-10-20 05:00:00", 0.3),
             _fila("Villarrica", "VIIRS375", "2026-10-21 05:00:00", 0.04),        # mínima: D-9 SN la quita
             _fila("Lascar", "VIIRS375", "2026-10-20 05:00:00", 3.0, tipo="FALSO_POSITIVO")]
    prod = [_rec("NevadosDeChillan", "MODIS", "07:21", "2026-10-20", False),
            _rec("Villarrica", "VIIRS375", "05:00", "2026-10-20", False),
            _rec("Villarrica", "VIIRS375", "05:00", "2026-10-21", False)]
    sombra = [_rec("NevadosDeChillan", "MODIS", "07:21", "2026-10-20", True),
              _rec("Villarrica", "VIIRS375", "05:00", "2026-10-20", True)]
    p = vs.pasadas_de_alerta(filas, prod, sombra, ("2026-10-01", "2026-10-25"), diurna=NOCHE)
    assert [(x["volcano"], x["protegida"], x["prod_pub"], x["sombra_pub"]) for x in p] == [
        ("NevadosDeChillan", True, False, True), ("Villarrica", False, False, True)]


def test_mutacion_tolerancia_del_pareo():
    """Un record a 10 minutos es otra pasada: no se parea (±120 s, como el etiquetador)."""
    filas = [_fila("Villarrica", "VIIRS375", "2026-10-20 05:00:00", 0.3)]
    lejos = [_rec("Villarrica", "VIIRS375", "05:10", "2026-10-20", True)]
    p = vs.pasadas_de_alerta(filas, lejos, lejos, ("2026-10-01", "2026-10-25"), diurna=NOCHE)
    assert (p[0]["prod_pub"], p[0]["sombra_pub"]) == (None, None)


def test_mutacion_publica_si_alguno_de_los_records_publica():
    filas = [_fila("Villarrica", "VIIRS375", "2026-10-20 05:00:00", 0.3)]
    dos = [_rec("Villarrica", "VIIRS375", "05:00", "2026-10-20", False),
           _rec("Villarrica", "VIIRS375", "05:01", "2026-10-20", True)]
    p = vs.pasadas_de_alerta(filas, dos, [], ("2026-10-01", "2026-10-25"), diurna=NOCHE)
    assert p[0]["prod_pub"] is True


def test_mutacion_ventana_y_diurnas():
    filas = [_fila("Villarrica", "VIIRS375", "2026-09-01 05:00:00", 0.3),
             _fila("Villarrica", "VIIRS375", "2026-10-20 17:00:00", 0.3)]
    p = vs.pasadas_de_alerta(filas, [], [], ("2026-10-01", "2026-10-25"),
                             diurna=lambda b, v, dt: dt.hour == 17)
    assert p == []
    p = vs.pasadas_de_alerta(filas, [], [], ("2026-08-01", "2026-10-25"), diurna=NOCHE)
    assert len(p) == 2


def test_protegida_solo_ocr_de_suomi_npp_antes_del_hito_se_marca():
    filas = [_fila("Tupungatito", "VIIRS375", "2026-09-28 05:18:00", 2.51, tipo="ALERTA_TERMICA_OCR", source="OCR"),
             _fila("Tupungatito", "VIIRS375", "2026-09-29 04:54:00", 1.86)]
    recs = [_rec("Tupungatito", "VIIRS375", "05:18", "2026-09-28", False, sensor="VIIRS_SNPP"),
            _rec("Tupungatito", "VIIRS375", "04:54", "2026-09-29", False, sensor="VIIRS_SNPP")]
    p = vs.pasadas_de_alerta(filas, recs, [], ("2026-09-01", "2026-10-25"), diurna=NOCHE)
    assert [x["referencia_sospechosa"] for x in p] == [True, False]


# ------------------------------------------------------------------ disparadores
def test_reversion_solo_con_protegida_que_la_sombra_publica_y_produccion_calla():
    pas = [_pasada("A", "MODIS", "2026-10-20 07:20", True, False, True),     # dispara
           _pasada("B", "MODIS", "2026-10-20 07:20", True, False, False),    # la sombra tampoco: no
           _pasada("C", "MODIS", "2026-10-20 07:20", True, None, True),      # producción sin record: no
           _pasada("D", "MODIS", "2026-10-20 07:20", True, True, True)]      # producción publica: no
    d = _disp(pas)
    assert [x["volcano"] for x in d["reversion"]] == ["A"]
    assert d["veredicto"] == "REVERSION_CANDIDATA"
    assert d["duracion"]["protegidas_vistas_en_sombra"] == 4
    pas[1]["sombra_pub"] = None                                        # sin record de sombra: no cuenta
    assert _disp(pas)["duracion"]["protegidas_vistas_en_sombra"] == 3


def test_lo_anterior_a_la_adopcion_es_retrospectivo_y_no_dispara():
    """La lectura del 2026-10-19: el caso de PCC (10-oct) va al retrospectivo, no a la reversión."""
    pas = [_pasada("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54", True, False, True),
           _pasada("V", "VIIRS375", "2026-10-18 09:56", True, False, True),            # un minuto antes
           _pasada("W", "VIIRS375", "2026-10-18 09:57", True, True, True)]             # el minuto de la adopción
    d = _disp(pas)
    assert d["veredicto"] == "VERDE" and d["reversion"] == []
    r = d["retrospectivo"]
    assert [p["volcano"] for p in r["protegidas_que_la_sombra_publica_y_k_calla"]] == ["PuyehueCordonCaulle", "V"]
    assert r["protegidas_vistas_en_sombra"] == 2
    assert d["duracion"]["protegidas_vistas_en_sombra"] == 1


def test_persistencia_tres_noches_seguidas_en_un_volcan():
    pas = [_pasada("V", "VIIRS375", f"2026-10-2{d} 05:00", False, False, True) for d in (2, 3, 4)]
    assert _disp(pas)["persistencia"] == [{"volcano": "V", "noches": ["2026-10-22", "2026-10-23", "2026-10-24"]}]
    salteado = [_pasada("V", "VIIRS375", f"2026-10-2{d} 05:00", False, False, True) for d in (2, 3, 5)]
    assert _disp(salteado)["persistencia"] == []


def test_muy_bajo_viirs375_dispara_cuando_wilson_inferior_supera_la_cota():
    # 10 de 10, en noches no consecutivas para aislar el disparador (i) de la persistencia
    pas = [_pasada("V", "VIIRS375", f"2026-10-{d:02d} 05:00", False, False, True) for d in range(19, 39, 2)
           if d <= 31] + [_pasada("V", "VIIRS375", f"2026-11-{d:02d} 05:00", False, False, True) for d in (2, 4, 6)]
    d = _disp(pas, hoy="2026-11-10")
    mb = d["muy_bajo"]["V|VIIRS375"]
    assert (mb["k"], mb["n"], mb["dispara"]) == (10, 10, True)
    assert d["persistencia"] == [] and d["veredicto"] == "INVESTIGAR"
    for x in pas[1:]:
        x["prod_pub"] = True
    assert _disp(pas, hoy="2026-11-10")["muy_bajo"]["V|VIIRS375"]["dispara"] is False


def test_mutacion_muy_bajo_sin_cota_en_modis_y_viirs750_no_dispara():
    for s in ("MODIS", "VIIRS750"):
        pas = [_pasada("V", s, f"2026-10-{d:02d} 05:00", False, False, True) for d in range(19, 31, 2)]
        d = _disp(pas)
        assert d["muy_bajo"][f"V|{s}"]["dispara"] is False and d["muy_bajo"][f"V|{s}"]["cota_ab"] is None


def test_mutacion_las_protegidas_no_entran_al_conteo_muy_bajo():
    pas = [_pasada("V", "VIIRS375", "2026-10-20 05:00", True, True, True),
           _pasada("V", "VIIRS375", "2026-10-22 05:00", False, True, True)]
    assert _disp(pas)["muy_bajo"]["V|VIIRS375"]["n"] == 1


def test_negativos_viirs375_de_produccion_desde_la_adopcion():
    def negs(n_pub, fecha="2026-10-20", lab="neg_limpio", b="VIIRS375"):
        return [_rec("V", b, "05:00", fecha, i < n_pub, lab=lab) for i in range(100)]
    d = _disp([], negs(30))
    assert (d["negativos_VIIRS375"]["k"], d["negativos_VIIRS375"]["dispara"]) == (30, True)
    assert _disp([], negs(2))["negativos_VIIRS375"]["dispara"] is False
    # mutación: sólo cuentan los negativos limpios, de VIIRS 375, posteriores a la adopción
    assert _disp([], negs(30, lab="pos"))["negativos_VIIRS375"]["n"] == 0
    assert _disp([], negs(30, b="VIIRS750"))["negativos_VIIRS375"]["n"] == 0
    assert _disp([], negs(30, fecha="2026-10-10"))["negativos_VIIRS375"]["n"] == 0


def test_plazo_de_la_regla():
    """Hasta 29 protegidas vistas en la sombra o 120 días desde la adopción, lo que ocurra primero."""
    assert vs.PROTEGIDAS_OBJETIVO == 29 and vs.DIAS_MAXIMOS == 120
    d = _disp([], hoy="2026-10-25")
    assert d["duracion"]["vence"] == "2027-02-15" and d["duracion"]["cumplida"] is False
    assert _disp([], hoy="2027-02-15")["duracion"]["cumplida"] is True
    # mutación: también se cumple por protegidas, antes del plazo
    pas = [_pasada("V", "MODIS", f"2026-10-20 0{h}:{m:02d}", True, True, True) for h in range(3) for m in range(10)]
    assert _disp(pas, hoy="2026-10-25")["duracion"]["cumplida"] is True


# ------------------------------------------------------------------ avisos
def test_sombra_detenida_es_aviso():
    assert vs.avisos_sombra(ultima_sombra="2026-10-10", hoy="2026-10-19")
    assert vs.avisos_sombra(ultima_sombra="2026-10-18", hoy="2026-10-19") == []
    assert vs.avisos_sombra(ultima_sombra=None, hoy="2026-10-19")


def test_mutacion_una_sombra_que_trae_produccion_es_aviso():
    prod = [_rec("V", "VIIRS375", "05:00", "2026-10-20", True, perfil="mirova_equivalent")]
    assert vs.avisos_perfiles(prod, prod)
    assert vs.avisos_perfiles(prod, [_rec("V", "VIIRS375", "05:00", "2026-10-20", True, perfil="experimental")]) == []
    assert vs.avisos_perfiles(prod, [_rec("V", "VIIRS375", "05:00", "2026-10-20", True, perfil=None)]) == []


# ------------------------------------------------------------------ evaluar() de punta a punta
@pytest.fixture
def insumos(monkeypatch):
    def poner(filas, prod, sombra, frontera="2026-09-18", adopcion=ADOP):
        monkeypatch.setattr(vs, "cargar_insumos", lambda win: (filas, prod, sombra))
        monkeypatch.setattr(vs.aa, "leer_frontera_k", lambda *a: frontera)
        monkeypatch.setattr(vs, "leer_adopcion", lambda *a: adopcion)
        monkeypatch.setattr(vs, "_diurna_por_defecto", lambda: NOCHE)
    return poner


def _caso_pcc():
    filas = [_fila("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54:02", 1.19),
             _fila("NevadosDeChillan", "MODIS", "2026-10-22 07:20:00", 2.18)]
    prod = [_rec("PuyehueCordonCaulle", "VIIRS750", "05:54", "2026-10-10", False, perfil="mirova_equivalent"),
            _rec("NevadosDeChillan", "MODIS", "07:20", "2026-10-22", True, perfil="mirova_equivalent")]
    sombra = [_rec("PuyehueCordonCaulle", "VIIRS750", "05:54", "2026-10-10", True, perfil="experimental"),
              _rec("NevadosDeChillan", "MODIS", "07:20", "2026-10-22", True, perfil="experimental")]
    return filas, prod, sombra


def test_evaluar_deja_pcc_en_el_retrospectivo(insumos):
    insumos(*_caso_pcc())
    out = vs.evaluar("2026-10-23")
    assert out["veredicto"] == "VERDE"
    assert [p["fecha_utc"] for p in out["retrospectivo"]["protegidas_que_la_sombra_publica_y_k_calla"]] == [
        "2026-10-10 05:54"]
    assert out["duracion"]["protegidas_vistas_en_sombra"] == 1


def test_evaluar_dispara_si_la_perdida_es_posterior(insumos):
    filas, prod, sombra = _caso_pcc()
    prod[1]["pub"] = False
    insumos(filas, prod, sombra)
    out = vs.evaluar("2026-10-23")
    assert out["veredicto"] == "REVERSION_CANDIDATA"
    assert out["reversion"][0]["volcano"] == "NevadosDeChillan"


def test_evaluar_sombra_que_es_produccion_queda_ciega(insumos):
    filas, prod, _ = _caso_pcc()
    insumos(filas, prod, prod)
    out = vs.evaluar("2026-10-23")
    assert out["veredicto"] == "VIGILANCIA_CIEGA"


def test_evaluar_sin_adopcion_declarada_queda_ciega(insumos):
    insumos(*_caso_pcc(), adopcion=None)
    assert vs.evaluar("2026-10-23")["veredicto"] == "VIGILANCIA_CIEGA"


def test_evaluar_sombra_detenida_queda_ciega(insumos):
    filas, prod, sombra = _caso_pcc()
    insumos(filas, prod, sombra)
    assert vs.evaluar("2026-10-30")["veredicto"] == "VIGILANCIA_CIEGA"


def test_main_escribe_latest_e_historial(insumos, monkeypatch, tmp_path):
    insumos(*_caso_pcc())
    monkeypatch.setattr(vs, "OUTDIR", str(tmp_path))
    vs.main([])
    out = json.loads((tmp_path / "sombra_latest.json").read_text(encoding="utf-8"))
    linea = json.loads((tmp_path / "sombra_history.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert out["veredicto"] == linea["veredicto"]
    assert linea["adopcion_k_utc"] == ADOP


def test_main_acepta_la_referencia_por_argumento(insumos, monkeypatch, tmp_path):
    """El workflow diario pasa la referencia fresca bajada a una carpeta temporal."""
    insumos(*_caso_pcc())
    monkeypatch.setattr(vs, "OUTDIR", str(tmp_path))
    monkeypatch.setattr(vs.aa, "CONS", vs.aa.CONS)
    monkeypatch.setattr(vs.aa, "OCR", vs.aa.OCR)
    vs.main(["--cons", "x/cons.csv", "--ocr", "x/ocr.csv"])
    assert (vs.aa.CONS, vs.aa.OCR) == ("x/cons.csv", "x/ocr.csv")
