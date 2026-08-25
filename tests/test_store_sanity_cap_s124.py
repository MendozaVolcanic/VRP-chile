"""S124 — el cap de cordura no puede publicar CERO en la erupción más grande.

El cap existe por una razón buena: el 2026-04-23 un granule de Lastarria llegó
con BT = 566 K (flag DN no enmascarado, o sea sensor saturado) y produjo 1.5
millones de MW. Publicar eso habría sido absurdo.

Pero la forma de descartarlo era escribir `vrp_mw = 0.0`, y ahí está el
problema: el umbral son 50 GW, y el récord histórico documentado por MIROVA es
~70 GW. O sea que el rango "por encima del cap" **contiene erupciones reales**,
y para ellas el sistema publicaba un CERO — indistinguible de una noche
tranquila. En monitoreo volcánico un falso negativo no cuesta lo mismo que un
falso positivo, y este era el falso negativo de máxima consecuencia posible.

La discriminación correcta no es por MAGNITUD sino por CAUSA:
  - BT por encima del límite físico del sensor  → el dato es imposible, es
    basura de saturación. Cero, como antes.
  - BT plausible y VRP enorme                   → puede ser una erupción real.
    Se conserva el valor y se marca para revisión.
"""
import pipeline.store as store


def _rec(vrp, t_max, pc_vrp=None):
    r = {"datetime_utc": "2026-04-23T01:50:00Z", "sensor": "MODIS_TERRA",
         "vrp_mw": vrp, "t_max_k": t_max}
    if pc_vrp is not None:
        r["primary_cluster"] = {"vrp_mw": pc_vrp, "centroid_dist_km": 0.5}
    return r


def test_basura_de_sensor_saturado_sigue_yendo_a_cero():
    """El caso Lastarria real: BT=566 K es físicamente imposible → cero."""
    r = _rec(1_500_000.0, 566.0, pc_vrp=1_600_000.0)
    store._apply_sanity_cap(r)
    assert r["vrp_mw"] == 0.0
    assert r["primary_cluster"]["vrp_mw"] == 0.0
    assert r["diag_rejected_sanity_cap_mw"] == 1_500_000.0, "el crudo se preserva"


def test_erupcion_gigante_con_bt_plausible_NO_se_publica_como_cero():
    """60 GW con BT creíble: puede ser real. Publicar 0 sería el peor error."""
    r = _rec(60_000.0, 480.0, pc_vrp=58_000.0)
    store._apply_sanity_cap(r)
    assert r["vrp_mw"] == 60_000.0, (
        "una magnitud enorme con BT físicamente posible NO debe anularse")
    assert r["primary_cluster"]["vrp_mw"] == 58_000.0
    assert r.get("vrp_exceeds_sanity_cap") is True, "debe quedar marcada para revisión"


def test_sin_t_max_se_mantiene_el_comportamiento_conservador():
    """Sin BT no se puede juzgar la causa: se descarta, como antes."""
    r = _rec(80_000.0, None)
    store._apply_sanity_cap(r)
    assert r["vrp_mw"] == 0.0


def test_valores_normales_no_se_tocan():
    r = _rec(12.5, 340.0, pc_vrp=9.1)
    store._apply_sanity_cap(r)
    assert r["vrp_mw"] == 12.5
    assert r["primary_cluster"]["vrp_mw"] == 9.1
    assert "vrp_exceeds_sanity_cap" not in r
    assert "diag_rejected_sanity_cap_mw" not in r
