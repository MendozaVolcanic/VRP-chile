# -*- coding: utf-8 -*-
"""S156 (arreglo 4 de docs/AUDIT_S155.md §5, V1-04): la vigilancia de la sombra existe y dispara lo que
la regla de adopción de K dice (experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md §4, paso 9).

POR QUE: K deja de publicar señal débil que el detector anterior (C0) veía. La sombra es el laboratorio
congelado en C0 (data/experimental_v2/) y su vigilancia es el disparador de la reversión pre-autorizada:
una alerta protegida que MIROVA publica, la sombra publica y producción calla. Hasta S156 la regla existía
y el código no: una pérdida así no la iba a ver nadie.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.vigilancia_sombra as vs  # noqa: E402


def _fila(vol, b, fecha, vrp, tipo="ALERTA_TERMICA"):
    return {"volcano": vol, "sensor_bucket": b, "fecha_utc": fecha, "vrp_mw": vrp, "tipo": tipo, "source": "CONS"}


def _rec(vol, b, hhmm, fecha, pub):
    dt = datetime.strptime(f"{fecha} {hhmm}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": vol, "b": b, "dt": dt, "noche": fecha, "pub": pub}


NOCHE = lambda *a: False  # noqa: E731


def test_wilson_reproduce_la_cota_del_ab():
    """La regla cita V1 21 de 832 = [0,0166; 0,0383]."""
    lo, hi = vs.wilson(21, 832)
    assert round(lo, 4) == 0.0166 and round(hi, 4) == 0.0383
    assert vs.wilson(0, 0) == (None, None)


def test_las_cotas_salen_de_los_logs_del_ab():
    """Muy Bajo perdidas y negativos publicados de K, lectura A, de experiments/_s153_fk_v2/v1.log y v2.log §6."""
    assert vs.COTAS_AB["muy_bajo"]["VIIRS375"] == {"V1": (16, 194), "V2": (26, 388)}
    assert vs.COTAS_AB["negativos"]["VIIRS375"] == {"V1": (21, 832), "V2": (37, 1010)}
    # se usa la mayor de las dos cotas superiores
    assert vs.cota_superior("negativos", "VIIRS375") == max(vs.wilson(21, 832)[1], vs.wilson(37, 1010)[1])
    logs = (ROOT / "experiments" / "_s153_fk_v2" / "v1.log").read_text(encoding="utf-8")
    assert "VIIRS375 K   Muy Bajo perdidas   16 de  194 | negativos publicados   21 de   832" in logs


def test_clasifica_pasadas_de_alerta_con_produccion_y_sombra():
    filas = [_fila("NevadosDeChillan", "MODIS", "2026-10-12 07:20:00", 2.18),
             _fila("Villarrica", "VIIRS375", "2026-10-12 05:00:00", 0.3),
             _fila("Villarrica", "VIIRS375", "2026-10-13 05:00:00", 0.04),        # mínima: D-9 SN la quita
             _fila("Lascar", "VIIRS375", "2026-10-12 05:00:00", 3.0, tipo="FALSO_POSITIVO")]
    prod = [_rec("NevadosDeChillan", "MODIS", "07:21", "2026-10-12", False),
            _rec("Villarrica", "VIIRS375", "05:00", "2026-10-12", False),
            _rec("Villarrica", "VIIRS375", "05:00", "2026-10-13", False)]
    sombra = [_rec("NevadosDeChillan", "MODIS", "07:21", "2026-10-12", True),
              _rec("Villarrica", "VIIRS375", "05:00", "2026-10-12", True)]
    p = vs.pasadas_de_alerta(filas, prod, sombra, ("2026-10-01", "2026-10-19"), diurna=NOCHE)
    assert [(x["volcano"], x["protegida"], x["prod_pub"], x["sombra_pub"]) for x in p] == [
        ("NevadosDeChillan", True, False, True), ("Villarrica", False, False, True)]


def _pasada(vol, b, fecha, protegida, prod, sombra, vrp=None):
    return {"volcano": vol, "sensor": b, "fecha_utc": fecha, "vrp_mirova_mw": vrp or (2.0 if protegida else 0.3),
            "protegida": protegida, "prod_pub": prod, "sombra_pub": sombra}


def test_reversion_solo_con_protegida_que_la_sombra_publica_y_produccion_calla():
    pas = [_pasada("A", "MODIS", "2026-10-12 07:20", True, False, True),     # dispara
           _pasada("B", "MODIS", "2026-10-12 07:20", True, False, False),    # la sombra tampoco: no
           _pasada("C", "MODIS", "2026-10-12 07:20", True, None, True),      # producción sin record: no
           _pasada("D", "MODIS", "2026-10-12 07:20", True, True, True)]      # producción publica: no
    d = vs.disparadores(pas, [], hoy="2026-10-19")
    assert [x["volcano"] for x in d["reversion"]] == ["A"]
    assert d["veredicto"] == "REVERSION_CANDIDATA"
    # las cuatro tienen record de sombra (la de B no publica, pero la sombra la miró)
    assert d["duracion"]["protegidas_vistas_en_sombra"] == 4
    pas[1]["sombra_pub"] = None                                        # sin record de sombra: no cuenta
    assert vs.disparadores(pas, [], hoy="2026-10-19")["duracion"]["protegidas_vistas_en_sombra"] == 3


def test_persistencia_tres_noches_seguidas_en_un_volcan():
    pas = [_pasada("V", "VIIRS375", f"2026-10-1{d} 05:00", False, False, True) for d in (2, 3, 4)]
    assert vs.disparadores(pas, [], hoy="2026-10-19")["persistencia"] == [
        {"volcano": "V", "noches": ["2026-10-12", "2026-10-13", "2026-10-14"]}]
    salteado = [_pasada("V", "VIIRS375", f"2026-10-1{d} 05:00", False, False, True) for d in (2, 3, 5)]
    assert vs.disparadores(salteado, [], hoy="2026-10-19")["persistencia"] == []


def test_muy_bajo_dispara_cuando_wilson_inferior_supera_la_cota():
    # 10 de 10 Muy Bajo perdidas en un volcán: Wilson inferior ~0,72 > cota V375 (~0,13)
    pas = [_pasada("V", "VIIRS375", f"2026-10-{d:02d} 05:00", False, False, True) for d in range(1, 11, 2)]
    pas += [_pasada("V", "VIIRS375", f"2026-10-{d:02d} 05:00", False, False, True) for d in range(2, 12, 2)]
    d = vs.disparadores(pas, [], hoy="2026-10-19")
    mb = d["muy_bajo"]["V|VIIRS375"]
    assert (mb["k"], mb["n"], mb["dispara"]) == (10, 10, True)
    assert d["veredicto"] == "INVESTIGAR"
    # 1 de 10: no
    for x in pas[1:]:
        x["prod_pub"] = True
    assert vs.disparadores(pas, [], hoy="2026-10-19")["muy_bajo"]["V|VIIRS375"]["dispara"] is False


def test_negativos_viirs375_de_produccion():
    negs = [{"b": "VIIRS375", "lab": "neg_limpio", "pub": i < 30} for i in range(100)]
    d = vs.disparadores([], negs, hoy="2026-10-19")
    assert d["negativos_VIIRS375"]["k"] == 30 and d["negativos_VIIRS375"]["dispara"] is True
    negs = [{"b": "VIIRS375", "lab": "neg_limpio", "pub": i < 2} for i in range(100)]
    assert vs.disparadores(negs and [], negs, hoy="2026-10-19")["negativos_VIIRS375"]["dispara"] is False


def test_sombra_detenida_es_aviso():
    assert vs.avisos_sombra(ultima_sombra="2026-10-10", hoy="2026-10-19")
    assert vs.avisos_sombra(ultima_sombra="2026-10-18", hoy="2026-10-19") == []
    assert vs.avisos_sombra(ultima_sombra=None, hoy="2026-10-19")


def test_plazo_de_la_regla():
    """Hasta 29 protegidas vistas en la sombra o 120 días desde la adopción, lo que ocurra primero."""
    assert vs.PROTEGIDAS_OBJETIVO == 29 and vs.DIAS_MAXIMOS == 120
    d = vs.disparadores([], [], hoy="2026-10-19", adopcion="2026-10-18")
    assert d["duracion"]["vence"] == "2027-02-15" and d["duracion"]["cumplida"] is False
