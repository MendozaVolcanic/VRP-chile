# -*- coding: utf-8 -*-
"""F7-318 (auditoría Codex ronda 2) y R3F9-107 (ronda 3): el banco de paridad informa todas las variantes de D-9.

POR QUÉ. La regla D-9 (`docs/MISSION.md`, regla 5 del criterio de victoria) decide SN (una pasada de VIIRS 375 cuyas
alertas son todas de 0,05 MW o menos cuenta como «MIROVA no vio nada») y exige que cada evaluación informe además SE
(estrato aparte), la regla original y la variante con umbral 0,04. `scripts/banco_paridad.py` sólo corría SN. Como ese
archivo está en el manifiesto del candado de la retrospectiva (`experiments/_s172_retro_paquete/leer_retro.py`,
REQUERIDOS_MANIFIESTO), no se le cambian los bytes: las variantes las mide `scripts/banco_paridad_variantes_d9.py`,
que importa el banco y reusa su etiquetador.

Estas pruebas fijan, sobre una noche sintética de Lastarria en VIIRS 375 con una alerta de 0,04, otra de 0,05 y una
RUTINA de la tabla con VRP 0, más una protegida de 2 MW otra noche, lo que cada variante tiene que contar, que la
protegida no cambia en ninguna, y que el anexo al JSON del banco exige que la variante decidida reproduzca al banco.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import banco_paridad as bp  # noqa: E402
import banco_paridad_variantes_d9 as vd  # noqa: E402
import clase_mirova as cm  # noqa: E402

VENTANA = ("2026-09-10", "2026-09-11")


def _f(vrp, tipo="ALERTA_TERMICA", hora="2026-09-10 05:30:00", source="CONS"):
    return {"volcano": "Lastarria", "sensor_bucket": "VIIRS375", "fecha_utc": hora, "source": source, "tipo": tipo,
            "vrp_mw": vrp, "dist_km": 1.0}


def _escenario():
    filas = [_f(0.04, hora="2026-09-10 05:30:00"), _f(0.05, hora="2026-09-10 06:10:00"),
             _f(0.0, tipo="RUTINA", hora="2026-09-10 07:00:00"), _f(2.0, hora="2026-09-11 05:30:00")]
    recs = []
    for (d, h, m), pub in (((10, 5, 30), 1), ((10, 6, 10), 0), ((10, 7, 0), 1), ((11, 5, 30), 1)):
        dt = datetime(2026, 9, d, h, m, tzinfo=timezone.utc)
        recs.append({"vol": "Lastarria", "b": "VIIRS375", "dt": dt, "noche": dt.strftime("%Y-%m-%d"), "pub": pub})
    return filas, recs


@pytest.fixture(scope="module")
def medido():
    filas, recs = _escenario()
    return vd.medir_variantes(filas, recs, bp._coords_por_volcan(), VENTANA)


def test_las_variantes_son_las_que_exige_d9():
    nombres = [v[0] for v in vd.VARIANTES_D9]
    assert nombres == ["SN_005", "SE_005", "original", "SN_004", "SE_004"]
    assert vd.VARIANTE_DECIDIDA == "SN_005"
    # Derivadas de las constantes de la regla, no escritas aparte.
    assert {(m, u) for _, m, u in vd.VARIANTES_D9} == {
        (m, u) for m in cm.MODOS_MINIMAS for u in (cm.UMBRAL_MINIMA_MW, cm.UMBRAL_MINIMA_VARIANTE_MW)
        if not (m == "original" and u != cm.UMBRAL_MINIMA_MW)}


@pytest.mark.parametrize("variante,n_pos,pos_pub,n_neg,neg_pub,n_minima", [
    ("original", 3, 2, 0, 0, 0),
    ("SN_005", 1, 1, 3, 2, 0),   # las dos mínimas pasan a RUTINA y la noche queda limpia
    ("SN_004", 2, 1, 0, 0, 0),   # la de 0,05 sigue siendo alerta: la noche no queda limpia
    ("SE_005", 1, 1, 0, 0, 2),   # estrato aparte; la noche no cambia
    ("SE_004", 2, 1, 0, 0, 1),
])
def test_cada_variante_cuenta_lo_suyo(medido, variante, n_pos, pos_pub, n_neg, neg_pub, n_minima):
    p = medido["variantes"][variante]["por_sensor"]["VIIRS375"]["pasada"]
    assert (p["n_pos"], p["pos_publicados"], p["n_neg_limpio"], p["neg_limpio_publicados"]) == (
        n_pos, pos_pub, n_neg, neg_pub)
    assert medido["variantes"][variante]["etiquetas"].get("minima", 0) == n_minima


def test_la_protegida_no_cambia_en_ninguna_variante(medido):
    for nombre, v in medido["variantes"].items():
        assert v["protegidas"] == {"pasadas_ref": 1, "con_record": 1, "publicadas": 1}, nombre
    assert medido["protegidas_iguales_en_todas"] is True


def test_diferencias_contra_la_decidida(medido):
    d = medido["diferencia_contra_decidida"]["original"]["VIIRS375"]
    assert d["n_neg_limpio"] == -3 and d["neg_limpio_publicados"] == -2 and d["n_pos"] == 2
    assert all(v == 0 for v in medido["diferencia_contra_decidida"]["SN_005"]["VIIRS375"].values())


def test_la_decidida_es_la_regla_del_banco(medido):
    # La variante decidida tiene que reproducir lo que el banco calcula con su propia regla (MODO_MINIMAS).
    filas, recs = _escenario()
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, bp._coords_por_volcan(), VENTANA, regla_minimas=bp.MODO_MINIMAS)
    recs = [dict(r) for r in recs]
    bp.etiquetar(recs, por_vb, ns, nv)
    p, n = bp.metricas(recs, bp.alertas_sin_record(por_vb, recs), bp._filtro(b="VIIRS375"))
    banco = {"por_sensor": {"VIIRS375": {"pasada": p, "noche_volcan": n}}, "meta": {"ventana": list(VENTANA)}}
    out = vd.anexar_al_banco(banco, medido)
    assert out["variantes_d9"]["coincide_con_banco"] is True
    assert set(out["variantes_d9"]["variantes"]) == {v[0] for v in vd.VARIANTES_D9}


def test_anexar_rechaza_un_banco_que_no_coincide(medido):
    banco = {"por_sensor": {"VIIRS375": {"pasada": {"n_pos": 99}, "noche_volcan": {}}},
             "meta": {"ventana": list(VENTANA)}}
    with pytest.raises(ValueError):
        vd.anexar_al_banco(banco, medido)
    banco_otra_ventana = {"por_sensor": {}, "meta": {"ventana": ["2026-03-01", "2026-09-11"]}}
    with pytest.raises(ValueError):
        vd.anexar_al_banco(banco_otra_ventana, medido)


def test_no_muta_los_records_de_entrada():
    filas, recs = _escenario()
    vd.medir_variantes(filas, recs, bp._coords_por_volcan(), VENTANA)
    assert all("lab" not in r for r in recs)
    assert filas[0]["tipo"] == "ALERTA_TERMICA" and filas[0]["vrp_mw"] == 0.04
