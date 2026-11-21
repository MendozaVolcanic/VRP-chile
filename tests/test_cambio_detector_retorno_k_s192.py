# -*- coding: utf-8 -*-
"""S192 (F11-102, auditoría Codex ronda 2, frente 11): el tablero marca también el paso de la vía «código MIROVA» a K.

POR QUÉ: desde el reemplazo del 2026-11-12 toda la historia publicada es de la vía, y `primeraVia` sólo marca K seguido
de la vía. Si un sensor se revirtiera, su serie pasaría de la vía a K y la potencia caería a cerca de la mitad (la vía
suma todos los píxeles alertados, K publicaba el núcleo del cúmulo) sin ninguna línea: el operador leería un cambio de
método como una baja de actividad del volcán. Nicolás suspendió la reversión pre-autorizada (2026-11-21) hasta que esta
marca exista. La marca sale de los datos, como la de la vía: cada cambio de detector en la serie de un sensor, en las dos
direcciones, con su línea. Se prueba con node, como las otras marcas.
"""
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "tests"))
from test_cambio_detector_s153 import DOM_FALSO, HAY_NODE, node  # noqa: E402,F401

MODULO = RAIZ / "frontend" / "cambio_detector.js"
pytestmark = pytest.mark.skipif(not HAY_NODE, reason="el módulo se prueba con node")
REQ = f"const M = require({json.dumps(str(MODULO))});"


def _r(sensor, dt, via):
    r = {"sensor": sensor, "datetime_utc": dt}
    if via is not None:
        r["via_codigo_mirova"] = via
    return r


def vm(dt):
    return _r("MODIS_AQUA", dt, True)


def km(dt):
    return _r("MODIS_AQUA", dt, None)


def _dibuja(recs_por_volcan, familia="MODIS", etiqueta="MODIS (1km)", desde="2026-10-01", hasta="2026-12-31"):
    """Pasa los records de cada volcán a notarRecords (como las vistas) y dibuja el plugin de la familia."""
    llamadas = "".join(f"M.notarRecords({json.dumps(recs)}, d);" for recs in recs_por_volcan)
    js = REQ + f"""
    const d = docFalso();
    {llamadas}
    const c = chartFalso("time", Date.parse("{desde}T00:00:00Z"), Date.parse("{hasta}T00:00:00Z"));
    c.data = {{ datasets: [{{ label: {json.dumps(etiqueta)} }}] }};
    const r = M.crearPluginVia({json.dumps(familia)}).afterDatasetsDraw(c);
    const textos = c.trazos.filter(x => x[0] === "fillText").map(x => x[1]);
    process.stdout.write(JSON.stringify([r, textos, M.cambiosDetector({json.dumps(familia)})]));
    """
    return node(js)


def test_la_via_seguida_de_k_dibuja_la_vuelta_a_k():
    """El caso de F11-102: la historia es toda de la vía y después del revert llega K."""
    r, textos, cambios = _dibuja([[vm("2026-11-10 07:20"), vm("2026-11-12 07:20"), km("2026-11-14 07:20"),
                                   km("2026-11-15 07:20")]])
    assert r is True
    assert textos == ["MODIS: vuelve a K"]
    assert cambios == [{"utc": "2026-11-14T07:20:00.000Z", "hacia": "K"}]


def test_k_via_k_via_marca_los_tres_cambios_en_orden():
    recs = [km("2026-10-05 07:20"), vm("2026-10-20 07:20"), km("2026-11-05 07:20"), vm("2026-11-25 07:20")]
    r, textos, cambios = _dibuja([recs])
    assert r is True
    assert textos == ["MODIS: vía MIROVA", "MODIS: vuelve a K", "MODIS: vía MIROVA"]
    assert [c["hacia"] for c in cambios] == ["via", "K", "via"]


def test_k_seguido_de_la_via_sigue_igual():
    r, textos, cambios = _dibuja([[km("2026-11-01 07:20"), vm("2026-11-02 07:20")]])
    assert r is True and textos == ["MODIS: vía MIROVA"]
    assert cambios == [{"utc": "2026-11-02T07:20:00.000Z", "hacia": "via"}]


def test_sin_cambio_de_detector_no_hay_linea():
    for recs in ([vm("2026-11-10 07:20"), vm("2026-11-12 07:20")], [km("2026-11-10 07:20"), km("2026-11-12 07:20")], []):
        r, textos, cambios = _dibuja([recs])
        assert r is False and textos == [] and cambios == []


def test_una_caida_a_k_de_la_via_no_es_vuelta_a_k():
    """La clave con texto ("sin_mxd03", "sin_grilla") es K que corrió con la vía encendida en una pasada suelta (A118):
    no es un cambio de método de la serie y no lleva línea."""
    recs = [vm("2026-11-10 07:20"), _r("MODIS_AQUA", "2026-11-11 07:20", "sin_mxd03"), vm("2026-11-12 07:20")]
    r, textos, cambios = _dibuja([recs])
    assert r is False and cambios == []


def test_el_orden_de_los_records_no_importa():
    recs = [km("2026-11-15 07:20"), vm("2026-11-10 07:20"), km("2026-11-14 07:20"), vm("2026-11-12 07:20")]
    _, _, cambios = _dibuja([recs])
    assert cambios == [{"utc": "2026-11-14T07:20:00.000Z", "hacia": "K"}]


def test_los_volcanes_de_un_mismo_revert_dan_una_sola_linea():
    """Tras un revert, cada volcán pasa a K en su primera pasada nueva: días distintos para el mismo cambio. Una línea por
    volcán llenaría el gráfico de rayas; se funden en la más temprana."""
    a = [vm("2026-11-10 07:20"), km("2026-11-14 07:20")]
    b = [vm("2026-11-10 03:00"), km("2026-11-17 03:00")]
    r, textos, cambios = _dibuja([a, b])
    assert textos == ["MODIS: vuelve a K"]
    assert cambios == [{"utc": "2026-11-14T07:20:00.000Z", "hacia": "K"}]
    _, _, cambios_al_reves = _dibuja([b, a])
    assert cambios_al_reves == cambios, "el orden en que llegan los volcanes no cambia la marca"


def test_cada_sensor_marca_solo_su_serie():
    recs = [_r("VIIRS_NOAA20", "2026-11-10 05:00", True), _r("VIIRS_NOAA20", "2026-11-14 05:00", None)]
    r, textos, _ = _dibuja([recs], familia="VIIRS375", etiqueta="VIIRS 375m")
    assert r is True and textos == ["VIIRS 375: vuelve a K"]
    r, textos, cambios = _dibuja([recs], familia="VIIRS750", etiqueta="VIIRS 750m")
    assert r is False and textos == [] and cambios == []
    r, textos, _ = _dibuja([recs], familia="VIIRS375", etiqueta="MODIS (1km)")
    assert r is False, "la línea de VIIRS 375 no va en un gráfico que no muestra VIIRS 375"


def test_fuera_del_rango_visible_no_se_dibuja():
    r, textos, _ = _dibuja([[vm("2026-11-10 07:20"), km("2026-11-14 07:20")]], desde="2026-12-01", hasta="2026-12-31")
    assert r is False and textos == []


def test_la_vuelta_a_k_no_mueve_la_fecha_de_la_via():
    """viaDesde y lo que devuelve notarRecords siguen siendo la primera pasada de la vía con K antes (la frontera del
    auto-audit y de las vistas): la vuelta a K se agrega, no reemplaza."""
    js = REQ + f"""
    const d = docFalso();
    const r = M.notarRecords({json.dumps([km("2026-10-05 07:20"), vm("2026-10-20 07:20"), km("2026-11-05 07:20")])}, d);
    process.stdout.write(JSON.stringify([r, M.viaModisDesde()]));
    """
    assert node(js) == ["2026-10-20T07:20:00.000Z", "2026-10-20T07:20:00.000Z"]
