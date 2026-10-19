# -*- coding: utf-8 -*-
"""S156 (arreglo 4 de docs/AUDIT_S155.md §5, V1-04): la vigilancia de la sombra existe y dispara lo que
la regla de adopción de K dice (experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md §4, paso 9, con la lectura
que Nicolás decidió el 2026-10-19: unidad = pasada; cuenta desde la adopción; lo anterior es retrospectivo).

POR QUE: K deja de publicar señal débil que el detector anterior (C0) veía. La sombra es el laboratorio
congelado en C0 (data/experimental_v2/) y su vigilancia es el disparador de la reversión pre-autorizada:
una alerta protegida que MIROVA publica, la sombra publica y producción calla. Hasta S156 la regla existía
y el código no. Dos verificadores limpios mutaron el script (17 y 13 mutaciones): cada prueba marcada
«mutación» nació de una que sobrevivió.
"""
import json
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.vigilancia_sombra as vs  # noqa: E402

ADOP = "2026-10-18 09:57:30"
LEER_JUZGADAS_REAL = vs.leer_juzgadas   # el fixture `insumos` la reemplaza por una lista vacía
NOCHE = lambda *a: False  # noqa: E731
VENTANA = ("2026-09-01", "2026-11-30")


def _fila(vol, b, fecha, vrp, tipo="ALERTA_TERMICA", source="CONS"):
    return {"volcano": vol, "sensor_bucket": b, "fecha_utc": fecha, "vrp_mw": vrp, "tipo": tipo, "source": source}


def _rec(vol, b, hhmm, fecha, pub, sensor="VIIRS_NOAA21", perfil=None, lab="sin_info"):
    dt = datetime.strptime(f"{fecha} {hhmm}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": vol, "b": b, "dt": dt, "noche": fecha, "pub": pub, "sensor": sensor, "perfil": perfil,
            "lab": lab, "lab_original": lab}


def _pasada(vol, b, fecha, protegida, prod, sombra, vrp=None, minima=False):
    return {"volcano": vol, "sensor": b, "fecha_utc": fecha[:16], "instante_utc": fecha[:16] + ":00",
            "vrp_mirova_mw": vrp or (2.0 if protegida else 0.3), "protegida": protegida, "minima": minima,
            "referencia_sospechosa": False, "prod_pub": prod, "sombra_pub": sombra}


def _disp(pas, negs=(), hoy="2026-10-25", adopcion=ADOP):
    return vs.disparadores(list(pas), list(negs), hoy=hoy, adopcion=adopcion)


def _pas(filas, prod=(), sombra=(), win=VENTANA, diurna=NOCHE):
    return vs.pasadas_de_alerta(filas, list(prod), list(sombra), win, diurna=diurna)


# ------------------------------------------------------------------ cotas y fuentes
def test_wilson_reproduce_la_cota_del_ab():
    """La regla cita V1 21 de 832 = [0,0166; 0,0383]."""
    lo, hi = vs.wilson(21, 832)
    assert round(lo, 4) == 0.0166 and round(hi, 4) == 0.0383
    assert vs.wilson(0, 0) == (None, None)


def test_las_cotas_salen_de_los_logs_del_ab():
    """Muy Bajo perdidas y negativos publicados de K, lectura A, de experiments/_s153_fk_v2/v1.log y v2.log §6."""
    assert vs.COTAS_AB["muy_bajo"] == {"VIIRS375": {"V1_SE": (7, 161), "V2_SE": (12, 343)}}
    assert vs.COTAS_AB["negativos"] == {"VIIRS375": {"V1": (21, 832), "V2": (37, 1010)}}
    assert vs.cota_superior("negativos", "VIIRS375") == max(vs.wilson(21, 832)[1], vs.wilson(37, 1010)[1])
    assert vs.cota_superior("muy_bajo", "MODIS") is None and vs.cota_superior("muy_bajo", "VIIRS750") is None
    v1 = (ROOT / "experiments" / "_s153_fk_v2" / "v1.log").read_text(encoding="utf-8")
    v2 = (ROOT / "experiments" / "_s153_fk_v2" / "v2.log").read_text(encoding="utf-8")
    assert "VIIRS375 K   Muy Bajo perdidas   16 de  194 | negativos publicados   21 de   832" in v1
    assert "VIIRS375 C0  Muy Bajo perdidas    0 de  194" in v1   # por eso la de K es la diferencial
    assert "VIIRS375 K   Muy Bajo perdidas   26 de  388 | negativos publicados   37 de  1010" in v2
    assert "VIIRS375 C0  Muy Bajo perdidas    0 de  388" in v2


def test_la_cota_se_de_muy_bajo_se_deriva_de_los_json_del_ab():
    """Decisión de Nicolás (2026-10-19): (i) coherente con D-9. Pérdidas con SE = suma SE menos negativos (SE no
    cambia negativos); denominador = Muy Bajo originales menos las pasadas que pasan de «pos» a «mínima»."""
    for archivo, mb_orig, neg, (k, n) in (("v1", 194, 21, (7, 161)), ("v2", 388, 37, (12, 343))):
        d = json.loads((ROOT / "experiments" / "_s153_fk_v2" / f"{archivo}.json").read_text(encoding="utf-8"))
        se = d["reglas_d9"]["SE"]
        assert se["suma"]["K|VIIRS375|A"] - neg == k
        assert mb_orig - se["cambian"]["pos->minima"] == n
        assert d["reglas_d9"]["original"]["suma"]["K|VIIRS375|A"] - neg in (16, 26)   # las de la etiqueta original


def test_la_adopcion_sale_del_js_del_tablero_con_segundos():
    js = (ROOT / "frontend" / "cambio_detector.js").read_text(encoding="utf-8")
    a = vs.leer_adopcion()
    assert a is not None and len(a) == 19 and f'CAMBIO_DETECTOR_UTC = "{a[:10]}T{a[11:]}' in js


def test_el_workflow_escucha_al_workflow_de_la_sombra():
    """Si alguien renombra experimental-diario, la vigilancia deja de dispararse sin error (verificador 2)."""
    import yaml
    wf = yaml.safe_load((ROOT / ".github" / "workflows" / "vigilancia-sombra.yml").read_text(encoding="utf-8"))
    sombra = yaml.safe_load((ROOT / ".github" / "workflows" / "experimental-diario.yml").read_text(encoding="utf-8"))
    assert wf["on"]["workflow_run"]["workflows"] == [sombra["name"]]
    assert wf["on"].get("schedule"), "falta el cron de respaldo"
    pasos = wf["jobs"]["vigilar"]["steps"]
    issue = next(p for p in pasos if p.get("name") == "Open issue")
    assert issue.get("if") == "always()", "el issue tiene que abrirse aunque falle el push"


# ------------------------------------------------------------------ pasadas
def test_clasifica_pasadas_de_alerta_con_produccion_y_sombra():
    filas = [_fila("NevadosDeChillan", "MODIS", "2026-10-20 07:20:00", 2.18),
             _fila("Villarrica", "VIIRS375", "2026-10-20 05:00:00", 0.3),
             _fila("Villarrica", "VIIRS375", "2026-10-21 05:00:00", 0.04),        # mínima D-9
             _fila("Lascar", "VIIRS375", "2026-10-20 05:00:00", 3.0, tipo="FALSO_POSITIVO")]
    prod = [_rec("NevadosDeChillan", "MODIS", "07:21", "2026-10-20", False),
            _rec("Villarrica", "VIIRS375", "05:00", "2026-10-20", False),
            _rec("Villarrica", "VIIRS375", "05:00", "2026-10-21", False)]
    sombra = [_rec("NevadosDeChillan", "MODIS", "07:21", "2026-10-20", True),
              _rec("Villarrica", "VIIRS375", "05:00", "2026-10-20", True)]
    p = _pas(filas, prod, sombra)
    assert [(x["volcano"], x["fecha_utc"][:10], x["protegida"], x["minima"], x["prod_pub"], x["sombra_pub"])
            for x in p] == [("NevadosDeChillan", "2026-10-20", True, False, False, True),
                            ("Villarrica", "2026-10-20", False, False, False, True),
                            ("Villarrica", "2026-10-21", False, True, False, None)]
    assert p[0]["instante_utc"] == "2026-10-20 07:20:00"


def test_mutacion_el_pareo_es_por_sensor_caso_pcc():
    """PCC 2026-10-10 05:54: K publica en VIIRS 375 y calla en VIIRS 750. Parear sin sensor borra la pérdida."""
    filas = [_fila("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54:02", 1.19),
             _fila("PuyehueCordonCaulle", "VIIRS375", "2026-10-10 05:54:02", 0.39)]
    prod = [_rec("PuyehueCordonCaulle", "VIIRS375", "05:54", "2026-10-10", True),
            _rec("PuyehueCordonCaulle", "VIIRS750", "05:54", "2026-10-10", False)]
    sombra = [_rec("PuyehueCordonCaulle", "VIIRS375", "05:54", "2026-10-10", True),
              _rec("PuyehueCordonCaulle", "VIIRS750", "05:54", "2026-10-10", True)]
    p = {x["sensor"]: x for x in _pas(filas, prod, sombra)}
    assert (p["VIIRS750"]["prod_pub"], p["VIIRS750"]["sombra_pub"], p["VIIRS750"]["protegida"]) == (False, True, True)
    assert p["VIIRS375"]["prod_pub"] is True
    d = _disp(_pas(filas, prod, sombra), adopcion="2026-10-01 00:00:00")
    assert [(x["volcano"], x["sensor"]) for x in d["reversion"]] == [("PuyehueCordonCaulle", "VIIRS750")]


def test_mutacion_umbral_y_lectura_a_de_la_protegida():
    filas = [_fila("V", "MODIS", "2026-10-20 07:00:00", 0.9),                          # Muy Bajo: no protegida
             _fila("V", "MODIS", "2026-10-21 07:00:00", 1.0),                          # 1 MW: protegida
             _fila("V", "MODIS", "2026-10-22 07:00:00", 3.0, tipo="ALERTA_SIN_GEOMETRIA_OCR", source="OCR")]
    p = _pas(filas)
    assert [(x["fecha_utc"][:10], x["protegida"]) for x in p] == [("2026-10-20", False), ("2026-10-21", True)]


def test_mutacion_tolerancia_del_pareo():
    """Un record a 10 minutos es otra pasada: no se parea (±120 s, como el etiquetador)."""
    filas = [_fila("Villarrica", "VIIRS375", "2026-10-20 05:00:00", 0.3)]
    lejos = [_rec("Villarrica", "VIIRS375", "05:10", "2026-10-20", True)]
    p = _pas(filas, lejos, lejos)
    assert (p[0]["prod_pub"], p[0]["sombra_pub"]) == (None, None)


def test_mutacion_publica_si_alguno_de_los_records_publica():
    filas = [_fila("Villarrica", "VIIRS375", "2026-10-20 05:00:00", 0.3)]
    dos = [_rec("Villarrica", "VIIRS375", "05:00", "2026-10-20", False),
           _rec("Villarrica", "VIIRS375", "05:01", "2026-10-20", True)]
    assert _pas(filas, dos)[0]["prod_pub"] is True


def test_mutacion_ventana_y_diurnas():
    filas = [_fila("Villarrica", "VIIRS375", "2026-09-01 05:00:00", 0.3),
             _fila("Villarrica", "VIIRS375", "2026-10-20 17:00:00", 0.3)]
    assert _pas(filas, win=("2026-10-01", "2026-10-25"), diurna=lambda b, v, dt: dt.hour == 17) == []
    assert len(_pas(filas, win=("2026-08-01", "2026-10-25"))) == 2


def test_mutacion_la_diurna_por_defecto_pasa_lat_y_lon_en_orden(monkeypatch):
    vistos = []
    monkeypatch.setattr(vs.aa, "_coords_por_volcan", lambda: {"V": (-39.4, -71.9)})
    monkeypatch.setattr(vs.aa, "es_pasada_diurna_descartada", lambda b, lat, lon, dt: vistos.append((lat, lon)))
    vs._diurna_por_defecto()("VIIRS375", "V", datetime(2026, 10, 20, 5, tzinfo=timezone.utc))
    assert vistos == [(-39.4, -71.9)]


def test_protegida_solo_ocr_de_suomi_npp_antes_del_hito_se_marca():
    hito = vs.aa.HITO_OCR_SUOMI_NPP
    assert hito == "2026-10-09"
    filas = [_fila("Tupungatito", "VIIRS375", "2026-09-28 05:18:00", 2.51, tipo="ALERTA_TERMICA_OCR", source="OCR"),
             _fila("Tupungatito", "VIIRS375", "2026-09-29 04:54:00", 1.86),
             _fila("Tupungatito", "VIIRS375", "2026-10-12 04:54:00", 1.5, tipo="ALERTA_TERMICA_OCR", source="OCR")]
    recs = [_rec("Tupungatito", "VIIRS375", hh, f, False, sensor="VIIRS_SNPP")
            for hh, f in (("05:18", "2026-09-28"), ("04:54", "2026-09-29"), ("04:54", "2026-10-12"))]
    # mutación: después del hito, la misma fila sólo OCR de Suomi NPP ya no es sospechosa
    assert [x["referencia_sospechosa"] for x in _pas(filas, recs)] == [True, False, False]


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
    pas[1]["sombra_pub"] = None
    assert _disp(pas)["duracion"]["protegidas_vistas_en_sombra"] == 3


def test_mutacion_produccion_sin_record_no_es_calla():
    d = _disp([_pasada("C", "MODIS", "2026-10-20 07:20", True, None, True)])
    assert d["reversion"] == [] and d["veredicto"] == "VERDE"


def test_lo_anterior_a_la_adopcion_es_retrospectivo_y_no_dispara():
    """La lectura del 2026-10-19: el caso de PCC (10-oct) va al retrospectivo, no a la reversión."""
    pas = [_pasada("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54", True, False, True),
           _pasada("V", "VIIRS375", "2026-10-18 09:57", True, False, True),            # 09:57:00 < 09:57:30
           _pasada("W", "VIIRS375", "2026-10-18 09:58", True, True, True)]             # posterior
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


def test_mutacion_persistencia_ignora_retro_y_minimas():
    retro = [_pasada("V", "VIIRS375", f"2026-10-1{d} 05:00", False, False, True) for d in (2, 3, 4)]
    assert _disp(retro)["persistencia"] == []
    assert _disp(retro)["retrospectivo"]["persistencia"] == [
        {"volcano": "V", "noches": ["2026-10-12", "2026-10-13", "2026-10-14"]}]
    minimas = [_pasada("V", "VIIRS375", f"2026-10-2{d} 05:00", False, False, True, vrp=0.04, minima=True)
               for d in (2, 3, 4)]
    assert _disp(minimas)["persistencia"] == []


def test_muy_bajo_viirs375_dispara_cuando_wilson_inferior_supera_la_cota():
    fechas = [f"2026-10-{d:02d}" for d in range(19, 32, 2)] + [f"2026-11-{d:02d}" for d in (2, 4, 6)]
    pas = [_pasada("V", "VIIRS375", f + " 05:00", False, False, True) for f in fechas]
    d = _disp(pas, hoy="2026-11-10")
    mb = d["muy_bajo"]["V|VIIRS375"]
    assert (mb["k"], mb["n"], mb["dispara"]) == (10, 10, True)
    assert d["persistencia"] == [] and d["veredicto"] == "INVESTIGAR"
    for x in pas[1:]:
        x["prod_pub"] = True
    assert _disp(pas, hoy="2026-11-10")["muy_bajo"]["V|VIIRS375"]["dispara"] is False


def test_mutacion_muy_bajo_sin_minimas_y_exige_que_la_sombra_publique():
    """Decisión de Nicolás: las mínimas (NONE en el banner) no cuentan; y sólo es pérdida si la sombra publica."""
    pas = [_pasada("V", "VIIRS375", "2026-10-20 05:00", False, False, True, vrp=0.04, minima=True),
           _pasada("V", "VIIRS375", "2026-10-22 05:00", False, False, False),
           _pasada("V", "VIIRS375", "2026-10-24 05:00", False, True, True)]
    mb = _disp(pas)["muy_bajo"]["V|VIIRS375"]
    assert (mb["k"], mb["n"]) == (0, 2)


def test_mutacion_muy_bajo_sin_cota_en_modis_y_viirs750_no_dispara():
    for s in ("MODIS", "VIIRS750"):
        pas = [_pasada("V", s, f"2026-10-{d:02d} 05:00", False, False, True) for d in range(19, 31, 2)]
        d = _disp(pas)
        assert d["muy_bajo"][f"V|{s}"]["dispara"] is False and d["muy_bajo"][f"V|{s}"]["cota_ab"] is None


def test_mutacion_las_protegidas_no_entran_al_conteo_muy_bajo():
    pas = [_pasada("V", "VIIRS375", "2026-10-20 05:00", True, True, True),
           _pasada("V", "VIIRS375", "2026-10-22 05:00", False, True, True)]
    assert _disp(pas)["muy_bajo"]["V|VIIRS375"]["n"] == 1


def test_negativos_viirs375_de_produccion_con_la_etiqueta_original_desde_la_adopcion():
    def negs(n_pub, fecha="2026-10-20", lab="neg_limpio", b="VIIRS375"):
        return [_rec("V", b, "05:00", fecha, i < n_pub, lab=lab) for i in range(100)]
    d = _disp([], negs(30))
    assert (d["negativos_VIIRS375"]["k"], d["negativos_VIIRS375"]["dispara"]) == (30, True)
    assert _disp([], negs(2))["negativos_VIIRS375"]["dispara"] is False
    assert _disp([], negs(30, lab="pos"))["negativos_VIIRS375"]["n"] == 0
    assert _disp([], negs(30, b="VIIRS750"))["negativos_VIIRS375"]["n"] == 0
    assert _disp([], negs(30, fecha="2026-10-10"))["negativos_VIIRS375"]["n"] == 0
    # mutación: cuenta la etiqueta original, no la de D-9 SN
    sn = negs(30)
    for r in sn:
        r["lab"], r["lab_original"] = "neg_limpio", "minima"
    assert _disp([], sn)["negativos_VIIRS375"]["n"] == 0


def test_plazo_de_la_regla():
    """Hasta 29 protegidas vistas en la sombra o 120 días desde la adopción, lo que ocurra primero."""
    assert vs.PROTEGIDAS_OBJETIVO == 29 and vs.DIAS_MAXIMOS == 120
    d = _disp([], hoy="2026-10-25")
    assert d["duracion"]["vence"] == "2027-02-15" and d["duracion"]["cumplida"] is False
    assert _disp([], hoy="2027-02-15")["duracion"]["cumplida"] is True
    pas = [_pasada("V", "MODIS", f"2026-10-20 0{h}:{m:02d}", True, True, True) for h in range(3) for m in range(10)]
    assert _disp(pas, hoy="2026-10-25")["duracion"]["cumplida"] is True


# ------------------------------------------------------------------ avisos
def test_la_frescura_de_la_sombra_es_por_volcan():
    s1 = ["VIIRS375"]
    ok = [_rec(v, "VIIRS375", "05:00", "2026-10-18", True) for v in ("A", "B")]
    assert vs.avisos_sombra(ok, "2026-10-19", vols=["A", "B"], sensores=s1) == []
    viejo = [_rec("A", "VIIRS375", "05:00", "2026-10-18", True), _rec("B", "VIIRS375", "05:00", "2026-10-10", True)]
    av = vs.avisos_sombra(viejo, "2026-10-19", vols=["A", "B"], sensores=s1)
    assert len(av) == 1 and " B " in av[0]
    assert vs.avisos_sombra(ok[:1], "2026-10-19", vols=["A", "B"], sensores=s1)      # B sin ningún record
    assert vs.avisos_sombra([], "2026-10-19", vols=["A"], sensores=s1)
    # el borde: tres días sin datos todavía no es ciega, cuatro sí
    assert vs.avisos_sombra([_rec("A", "VIIRS375", "05:00", "2026-10-16", True)], "2026-10-19",
                            vols=["A"], sensores=s1) == []
    assert vs.avisos_sombra([_rec("A", "VIIRS375", "05:00", "2026-10-15", True)], "2026-10-19",
                            vols=["A"], sensores=s1)


def test_la_frescura_es_tambien_por_sensor():
    """Verificador 3: la sombra sin MODIS dejaba 13 protegidas MODIS sin mirar y daba VERDE."""
    sin_modis = [_rec("A", s, "05:00", "2026-10-18", True) for s in ("VIIRS375", "VIIRS750")]
    av = vs.avisos_sombra(sin_modis, "2026-10-19", vols=["A"], sensores=["MODIS", "VIIRS375", "VIIRS750"])
    assert len(av) == 1 and "MODIS" in av[0]
    assert vs.avisos_produccion(sin_modis, "2026-10-19", vols=["A"], sensores=["MODIS"])


def test_referencia_vacia_o_detenida_es_aviso():
    viva = [_fila("Lascar", "MODIS", "2026-10-18 06:00:00", 0.0, tipo="RUTINA")]
    assert vs.avisos_referencia(viva, "2026-10-19") == []
    assert vs.avisos_referencia([], "2026-10-19")
    assert vs.avisos_referencia([_fila("Lascar", "MODIS", "2026-09-30 06:00:00", 0.0, tipo="RUTINA")], "2026-10-19")


def test_mutacion_una_sombra_que_trae_produccion_es_aviso():
    prod = [_rec("V", "VIIRS375", "05:00", "2026-10-20", True, perfil="mirova_equivalent")]
    assert vs.avisos_perfiles(prod, prod)
    assert vs.avisos_perfiles(prod, [_rec("V", "VIIRS375", "05:00", "2026-10-20", True, perfil="experimental")]) == []
    assert vs.avisos_perfiles(prod, [_rec("V", "VIIRS375", "05:00", "2026-10-20", True, perfil=None)]) == []


# ------------------------------------------------------------------ cargar_insumos (cableado, sin node)
def test_mutacion_cargar_insumos_lee_la_sombra_filtra_k_y_etiqueta_original_y_sn(monkeypatch):
    llamadas = []
    rec_k = {"vol": "V", "sha": "f" * 40, "lab": None}
    rec_c0 = {"vol": "V", "sha": None, "lab": None}
    bp = types.SimpleNamespace(
        inner_desde_html=lambda: {},
        cargar_nuestros=lambda coords, inner, win, data=None: (
            llamadas.append(data) or ([{"vol": "V", "fuente": "sombra"}] if data == vs.SOMBRA else [rec_k, rec_c0])),
        indexar_referencia=lambda filas, coords, win, regla_minimas="original": (regla_minimas, None, None, 0),
        etiquetar=lambda recs, modo, *a: [r.__setitem__("lab", "neg_limpio" if modo == "original" else "sn")
                                         for r in recs])
    ref = types.SimpleNamespace(cargar_referencia_unificada=lambda cons, ocr: ["fila"])
    monkeypatch.setitem(sys.modules, "banco_paridad", bp)
    monkeypatch.setitem(sys.modules, "referencia_mirova_unificada", ref)
    monkeypatch.setattr(vs.aa, "_coords_por_volcan", lambda: {})
    filas, prod, sombra = vs.cargar_insumos(("2026-09-18", "2026-10-19"))
    assert llamadas == [None, vs.SOMBRA]
    assert prod == [rec_k] and sombra == [{"vol": "V", "fuente": "sombra"}]
    assert (rec_k.get("lab_original"), rec_k.get("lab")) == ("neg_limpio", "sn")


# ------------------------------------------------------------------ evaluar() y main() de punta a punta
@pytest.fixture
def insumos(monkeypatch):
    def poner(filas, prod, sombra, frontera="2026-09-18", adopcion=ADOP):
        monkeypatch.setattr(vs, "cargar_insumos", lambda win: (filas, prod, sombra))
        monkeypatch.setattr(vs.aa, "leer_frontera_k", lambda *a: frontera)
        monkeypatch.setattr(vs, "leer_adopcion", lambda *a: adopcion)
        monkeypatch.setattr(vs, "_diurna_por_defecto", lambda: NOCHE)
        monkeypatch.setattr(vs.aa, "VOLS", VOLS_CASO)
        monkeypatch.setattr(vs, "leer_juzgadas", lambda *a: {})
    return poner


VOLS_CASO = ["PuyehueCordonCaulle", "NevadosDeChillan"]


def _relleno(perfil, fecha="2026-10-22"):
    """Un record sin alerta por volcán y sensor: la frescura se mide por volcán Y sensor."""
    return [_rec(v, s, "03:00", fecha, False, perfil=perfil) for v in VOLS_CASO for s in vs.aa.SENSORS]


def _caso_pcc():
    filas = [_fila("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54:02", 1.19),
             _fila("NevadosDeChillan", "MODIS", "2026-10-22 07:20:00", 2.18),
             _fila("Lascar", "MODIS", "2026-10-22 06:00:00", 0.0, tipo="RUTINA")]     # la referencia está viva
    prod = [_rec("PuyehueCordonCaulle", "VIIRS750", "05:54", "2026-10-10", False, perfil="mirova_equivalent"),
            _rec("NevadosDeChillan", "MODIS", "07:20", "2026-10-22", True, perfil="mirova_equivalent")]
    prod += _relleno("mirova_equivalent")
    sombra = [_rec("PuyehueCordonCaulle", "VIIRS750", "05:54", "2026-10-10", True, perfil="experimental"),
              _rec("NevadosDeChillan", "MODIS", "07:20", "2026-10-22", True, perfil="experimental")]
    sombra += _relleno("experimental")
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
    """La única razón para quedar ciega acá es el perfil: los records de producción están frescos en los dos
    volcanes (sin el record del 10-22 en PCC la frescura la dejaba ciega igual y la prueba pasaba por otra cosa)."""
    filas, prod, _ = _caso_pcc()
    assert vs.avisos_sombra(prod, "2026-10-23", vols=VOLS_CASO) == []
    insumos(filas, prod, prod)
    out = vs.evaluar("2026-10-23")
    assert out["veredicto"] == "VIGILANCIA_CIEGA" and any("no es la sombra" in a for a in out["avisos"])


def test_evaluar_sin_adopcion_declarada_queda_ciega(insumos):
    insumos(*_caso_pcc(), adopcion=None)
    assert vs.evaluar("2026-10-23")["veredicto"] == "VIGILANCIA_CIEGA"


def test_mutacion_evaluar_sombra_muerta_en_un_volcan_queda_ciega(insumos):
    """La sombra de Chillán muere: aunque la de PCC siga viva, la vigilancia no es VERDE."""
    filas, prod, sombra = _caso_pcc()
    insumos(filas, prod, sombra)
    assert vs.evaluar("2026-10-25")["veredicto"] == "VERDE"
    for r in sombra:
        if r["vol"] == "NevadosDeChillan":
            r["noche"] = "2026-10-15"
    out = vs.evaluar("2026-10-25")
    assert out["veredicto"] == "VIGILANCIA_CIEGA" and any("NevadosDeChillan" in a for a in out["avisos"])


def test_mutacion_la_frescura_se_mide_en_la_sombra_no_en_produccion(insumos):
    filas, prod, sombra = _caso_pcc()
    for r in sombra:
        r["noche"] = "2026-10-01"
    insumos(filas, prod, sombra)
    assert vs.evaluar("2026-10-23")["veredicto"] == "VIGILANCIA_CIEGA"


def test_main_escribe_latest_y_agrega_al_historial(insumos, monkeypatch, tmp_path):
    insumos(*_caso_pcc())
    monkeypatch.setattr(vs, "OUTDIR", str(tmp_path))
    vs.main([])
    vs.main([])
    out = json.loads((tmp_path / "sombra_latest.json").read_text(encoding="utf-8"))
    lineas = (tmp_path / "sombra_history.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lineas) == 2
    assert out["veredicto"] == json.loads(lineas[-1])["veredicto"]
    assert json.loads(lineas[-1])["adopcion_k_utc"] == ADOP


def test_main_acepta_la_referencia_por_argumento(insumos, monkeypatch, tmp_path):
    """El workflow diario pasa la referencia fresca bajada a una carpeta temporal."""
    insumos(*_caso_pcc())
    monkeypatch.setattr(vs, "OUTDIR", str(tmp_path))
    monkeypatch.setattr(vs.aa, "CONS", vs.aa.CONS)
    monkeypatch.setattr(vs.aa, "OCR", vs.aa.OCR)
    vs.main(["--cons", "x/cons.csv", "--ocr", "x/ocr.csv"])
    assert (vs.aa.CONS, vs.aa.OCR) == ("x/cons.csv", "x/ocr.csv")


# ------------------------------------------------------------------ mutaciones del verificador 3 (N1 a N27)
def test_n1_la_minima_incluye_0_05_exacto():
    """D-9: el umbral es 0,05 MW incluido (clase_mirova.UMBRAL_MINIMA_MW), no 0,04."""
    p = _pas([_fila("V", "VIIRS375", "2026-10-20 05:00:00", 0.05)])
    assert p[0]["minima"] is True


def test_n3_n25_el_corte_es_al_segundo_y_el_instante_exacto_es_posterior():
    filas = [_fila("V", "MODIS", "2026-10-18 09:57:10", 2.0), _fila("W", "MODIS", "2026-10-18 09:57:40", 2.0),
             _fila("X", "MODIS", "2026-10-18 09:57:30", 2.0)]
    prod = [_rec(v, "MODIS", "09:57", "2026-10-18", False) for v in ("V", "W", "X")]
    sombra = [_rec(v, "MODIS", "09:57", "2026-10-18", True) for v in ("V", "W", "X")]
    p = _pas(filas, prod, sombra)
    assert [x["instante_utc"] for x in p] == ["2026-10-18 09:57:10", "2026-10-18 09:57:40", "2026-10-18 09:57:30"]
    d = _disp(p)
    assert sorted(x["volcano"] for x in d["reversion"]) == ["W", "X"]
    assert [x["volcano"] for x in d["retrospectivo"]["protegidas_que_la_sombra_publica_y_k_calla"]] == ["V"]


def test_n5_los_negativos_cuentan_desde_el_instante_de_adopcion_no_desde_medianoche():
    antes = [_rec("V", "VIIRS375", "05:00", "2026-10-18", True, lab="neg_limpio") for _ in range(50)]
    assert _disp([], antes)["negativos_VIIRS375"]["n"] == 0


def test_n9_muy_bajo_exige_record_de_la_sombra():
    pas = [_pasada("V", "VIIRS375", "2026-10-20 05:00", False, False, None),
           _pasada("V", "VIIRS375", "2026-10-22 05:00", False, False, True)]
    assert _disp(pas)["muy_bajo"]["V|VIIRS375"]["n"] == 1


def test_n12_la_persistencia_retrospectiva_tampoco_cuenta_minimas():
    minimas = [_pasada("V", "VIIRS375", f"2026-10-1{d} 05:00", False, False, True, vrp=0.04, minima=True)
               for d in (2, 3, 4)]
    assert _disp(minimas)["retrospectivo"]["persistencia"] == []


def test_n18_un_aviso_no_tapa_una_reversion(insumos):
    filas, prod, sombra = _caso_pcc()
    prod[1]["pub"] = False                                         # Chillán 10-22: K calla
    sombra = [r for r in sombra if not (r["vol"] == "PuyehueCordonCaulle" and r["b"] == "MODIS")]  # aviso
    insumos(filas, prod, sombra)
    out = vs.evaluar("2026-10-23")
    assert out["avisos"] and out["veredicto"] == "REVERSION_CANDIDATA"


def test_n24_la_persistencia_sola_lleva_a_investigar():
    pas = [_pasada("V", "MODIS", f"2026-10-2{d} 05:00", False, False, True) for d in (2, 3, 4)]
    d = _disp(pas)
    assert d["muy_bajo"]["V|MODIS"]["dispara"] is False and not d["negativos_VIIRS375"]["dispara"]
    assert d["veredicto"] == "INVESTIGAR"


def test_n19_main_usa_la_fecha_de_hoy_utc(insumos, monkeypatch, tmp_path):
    insumos(*_caso_pcc())
    monkeypatch.setattr(vs, "OUTDIR", str(tmp_path))
    vs.main([])
    linea = json.loads((tmp_path / "sombra_history.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert linea["date"] == datetime.now(timezone.utc).date().isoformat()


def test_n22_el_pareo_acepta_hasta_120_segundos():
    filas = [_fila("V", "VIIRS375", "2026-10-20 05:00:00", 0.3)]
    p = _pas(filas, [_rec("V", "VIIRS375", "05:02", "2026-10-20", True)])
    assert p[0]["prod_pub"] is True


def test_n23_sospechosa_solo_si_todas_las_filas_protegidas_son_ocr():
    filas = [_fila("T", "VIIRS375", "2026-09-28 05:18:00", 2.5, tipo="ALERTA_TERMICA_OCR", source="OCR"),
             _fila("T", "VIIRS375", "2026-09-28 05:18:30", 2.4)]
    recs = [_rec("T", "VIIRS375", "05:18", "2026-09-28", False, sensor="VIIRS_SNPP")]
    assert _pas(filas, recs)[0]["referencia_sospechosa"] is False


def test_n27_sin_adopcion_todo_es_retrospectivo():
    pas = [_pasada("A", "MODIS", "2026-10-20 07:20", True, False, True)]
    import unittest.mock as um
    with um.patch.object(vs, "leer_adopcion", lambda *a: None):
        d = vs.disparadores(pas, [], hoy="2026-10-25", adopcion=None)
    assert d["reversion"] == [] and d["veredicto"] == "VERDE"
    assert len(d["retrospectivo"]["protegidas_que_la_sombra_publica_y_k_calla"]) == 1


# ------------------------------------------------------------------ decisiones de Nicolás del 2026-10-19
def test_una_pasada_juzgada_no_dispara_pero_cuenta_para_la_duracion():
    pas = [_pasada("A", "MODIS", "2026-10-20 07:20", True, False, True)]
    juz = {("A", "MODIS", "2026-10-20 07:20"): {"decision": "no revertir", "fecha_decision": "2026-10-21"}}
    d = vs.disparadores(pas, [], hoy="2026-10-25", adopcion=ADOP, juzgadas=juz)
    assert d["veredicto"] == "VERDE" and d["reversion"] == []
    assert [p["volcano"] for p in d["juzgadas"]] == ["A"] and d["juzgadas"][0]["juicio"]["decision"] == "no revertir"
    assert d["duracion"]["protegidas_vistas_en_sombra"] == 1
    # otra pasada del mismo volcán, no juzgada, sí dispara
    pas.append(_pasada("A", "MODIS", "2026-10-22 07:20", True, False, True))
    assert vs.disparadores(pas, [], hoy="2026-10-25", adopcion=ADOP, juzgadas=juz)["veredicto"] == "REVERSION_CANDIDATA"


def test_cumplido_el_plazo_la_reversion_ya_no_esta_preautorizada():
    """El plazo se mide PASADA POR PASADA (verificador 4): una candidata posterior al vencimiento es fuera de plazo
    se corra cuando se corra, y una anterior sigue dentro aunque la corrida sea después."""
    tarde = [_pasada("A", "MODIS", "2027-02-16 07:20", True, False, True)]
    d = _disp(tarde, hoy="2027-02-16")
    assert d["veredicto"] == "CANDIDATA_FUERA_DE_PLAZO" and d["reversion"] == []
    assert [p["volcano"] for p in d["fuera_de_plazo"]] == ["A"]      # se sigue informando
    temprana = [_pasada("B", "MODIS", "2027-02-14 07:20", True, False, True)]
    for hoy in ("2027-02-14", "2027-02-16", "2027-03-01"):
        assert _disp(temprana, hoy=hoy)["veredicto"] == "REVERSION_CANDIDATA", hoy


def test_el_plazo_cuenta_las_primeras_29_protegidas_la_29_incluida():
    """«Hasta ver 29 protegidas»: la 29.ª vista todavía está dentro; la 30.ª ya no. Sólo cuentan las protegidas."""
    vistas = [_pasada("V", "VIIRS375", f"2026-10-{19 + i // 10:02d} 0{i % 10}:00", True, True, True)
              for i in range(28)]
    ruido = [_pasada("V", "VIIRS375", "2026-10-19 00:30", False, True, True)]       # no protegida: no cuenta
    la_29 = [_pasada("W", "MODIS", "2026-10-25 07:20", True, False, True)]
    d = _disp(vistas + ruido + la_29, hoy="2026-10-26")
    assert d["duracion"]["protegidas_vistas_en_sombra"] == 29 and d["duracion"]["cumplida"] is True
    assert d["veredicto"] == "REVERSION_CANDIDATA"
    la_30 = [_pasada("X", "MODIS", "2026-10-26 07:20", True, False, True)]
    d = _disp(vistas + ruido + la_29 + la_30, hoy="2026-10-27")
    assert [p["volcano"] for p in d["reversion"]] == ["W"] and [p["volcano"] for p in d["fuera_de_plazo"]] == ["X"]


def test_fuera_de_plazo_exige_una_candidata():
    pas = [_pasada("V", "VIIRS375", f"2026-10-{19 + i // 10:02d} 0{i % 10}:00", True, True, True) for i in range(30)]
    assert _disp(pas, hoy="2027-03-01")["veredicto"] == "VERDE"


def test_la_juzgada_solo_sale_de_la_reversion():
    """Lo que se juzgó fue si revertir: la pasada sigue en la persistencia (verificador 4, hallazgo 2)."""
    pas = [_pasada("V", "MODIS", f"2026-10-2{d} 07:20", True, False, True) for d in (2, 3, 4)]
    juz = {("V", "MODIS", f"2026-10-2{d} 07:20"): {"decision": "x"} for d in (2, 3, 4)}
    d = vs.disparadores(pas, [], hoy="2026-10-25", adopcion=ADOP, juzgadas=juz)
    assert d["reversion"] == [] and d["persistencia"] and d["veredicto"] == "INVESTIGAR"
    # y la clave mira el sensor: juzgar MODIS no juzga la misma pasada en VIIRS 750
    otra = [_pasada("V", "VIIRS750", "2026-10-22 07:20", True, False, True)]
    d = vs.disparadores(otra, [], hoy="2026-10-25", adopcion=ADOP, juzgadas=juz)
    assert d["veredicto"] == "REVERSION_CANDIDATA"


def test_juzgadas_con_formato_invalido_caen(tmp_path):
    for malo in ({"volcano": "Puyehue", "sensor": "VIIRS750", "fecha_utc": "2026-10-10 05:54"},
                 {"volcano": "PuyehueCordonCaulle", "sensor": "V750", "fecha_utc": "2026-10-10 05:54"},
                 {"volcano": "PuyehueCordonCaulle", "sensor": "VIIRS750", "fecha_utc": "2026-10-10T05:54"},
                 {"volcano": "PuyehueCordonCaulle", "sensor": "VIIRS750", "fecha_utc": "2026-10-10 5:54"},
                 {"volcano": "PuyehueCordonCaulle", "sensor": "VIIRS750", "fecha_utc": "2026-10-10 05:54:02"}):
        f = tmp_path / "j.json"
        f.write_text(json.dumps({"pasadas": [malo]}), encoding="utf-8")
        with pytest.raises(ValueError):
            vs.leer_juzgadas(f)


def test_el_archivo_de_juzgadas_trae_el_caso_pcc(tmp_path):
    j = vs.leer_juzgadas()
    reg = j[("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54")]
    assert reg["quien"] and reg["fecha_decision"] == "2026-10-19" and "no revertir" in reg["decision"]
    assert vs.leer_juzgadas(tmp_path / "no_existe.json") == {}
    malo = tmp_path / "malo.json"
    malo.write_text("{no es json", encoding="utf-8")
    with pytest.raises(ValueError):
        vs.leer_juzgadas(malo)


def test_evaluar_con_el_archivo_real_pone_pcc_como_juzgada(insumos, monkeypatch):
    insumos(*_caso_pcc())
    monkeypatch.setattr(vs, "leer_juzgadas", LEER_JUZGADAS_REAL)
    out = vs.evaluar("2026-10-23")
    assert [p["fecha_utc"] for p in out["juzgadas"]] == ["2026-10-10 05:54"]
    # la juzgada sigue en el retrospectivo: lo que se juzgó fue si revertir, no lo que vio la sombra
    assert [p["fecha_utc"] for p in out["retrospectivo"]["protegidas_que_la_sombra_publica_y_k_calla"]] == [
        "2026-10-10 05:54"]
    assert out["veredicto"] == "VERDE"


def test_el_workflow_tiene_el_issue_de_fuera_de_plazo():
    """Su propia clase de issue, con un prefijo que no es prefijo de otro, y sin decir que hay pre-autorización."""
    import re
    wf = (ROOT / ".github" / "workflows" / "vigilancia-sombra.yml").read_text(encoding="utf-8")
    assert "CANDIDATA_FUERA_DE_PLAZO)" in wf and "sombra_pasadas_juzgadas.json" in wf
    titulos = re.findall(r'abrir "([^"]+)"', wf)
    assert "Sombra de K: candidata fuera de plazo" in titulos and "Sombra de K: candidata a reversion" in titulos
    for a in titulos:
        for b in titulos:
            assert a == b or not b.startswith(a), (a, b)
    bloque = wf.split("CANDIDATA_FUERA_DE_PLAZO)", 1)[1].split(";;", 1)[0]
    assert "NO hay reversion pre-autorizada" in bloque and "pre-autoriza revertir" not in bloque


def test_evaluar_referencia_detenida_o_produccion_sin_k_queda_ciega(insumos):
    filas, prod, sombra = _caso_pcc()
    insumos([f for f in filas if f["fecha_utc"] < "2026-10-11"], prod, sombra)
    assert vs.evaluar("2026-10-23")["veredicto"] == "VIGILANCIA_CIEGA"
    filas, prod, sombra = _caso_pcc()
    insumos(filas, [], sombra)
    out = vs.evaluar("2026-10-23")
    assert out["veredicto"] == "VIGILANCIA_CIEGA" and any("producción" in a for a in out["avisos"])
