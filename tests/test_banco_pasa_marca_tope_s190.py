"""S190 (H01, reparo A del verificador del PR #1037): el banco de paridad le pasa a node la marca del tope.

POR QUE. Desde el PR #1037 el tablero muestra un record sobre 50.000 MW si `store.py` lo conservo y marco
(`vrp_exceeds_sanity_cap: true`, BT creible), para no mostrar en cero una erupcion grande. El banco
(`scripts/banco_paridad.py`) ejecuta el predicado del tablero con node para las vigilancias y el auto-audit, pero
`cargar_nuestros` recorta cada record a `CAMPOS_JS` antes de mandarlo a node. Sin la marca en esa lista, el navegador
publicaria la erupcion y el banco la daria por no publicada: una falsa perdida de alerta protegida (mismo patron que
S173 S1 con `via_codigo_mirova`, tests/test_banco_pasa_marca_via_s173.py). Hoy ningun record publicado tiene la
marca, asi que ningun numero del banco cambia.

QUE VIGILA. Un record de la via de Chillan a 60 GW con BT 480 K pasado por `cargar_nuestros`:
1. con `vrp_exceeds_sanity_cap: true` sale publicado (como en el navegador);
2. el MISMO record sin la marca sale no publicado (el tope sigue para el fosil sin marca).

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Sin la clave en CAMPOS_JS el caso 1 da 0 (medido antes del arreglo). (2) El
control 0 manda el record completo a `correr_node` sin el recorte y tiene que dar 1, y el control 2 tiene que dar 0:
el instrumento puede dar 1 y puede dar 0.
"""
import json
import os
import shutil
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import banco_paridad as bp  # noqa: E402

ERUPCION = {"sensor": "MODIS_AQUA", "datetime_utc": "2026-10-01 08:35", "distance_class": "summit",
            "t_max_k": 480.0, "vrp_mw": 60000.0, "triggered_test1": False, "vrp_vent_mw": 0.0,
            "f5_core_vrp_mw": None, "anomaly_pixels": [], "via_codigo_mirova": True,
            "primary_cluster": {"vrp_mw": 60000.0, "centroid_dist_km": 0.708, "n_pixels": 225}}
VENTANA = ("2026-10-01", "2026-10-01")

node = pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")


def _con(**kw):
    r = json.loads(json.dumps(ERUPCION))
    r.update(kw)
    return r


@node
def test_el_banco_pasa_la_marca_del_tope_a_node(tmp_path):
    inner = bp.inner_desde_html()
    coords = bp._coords_por_volcan()
    completo = bp.correr_node([[_con(vrp_exceeds_sanity_cap=True), inner["NevadosDeChillan"]]])
    assert completo[0][4] == 1, f"control roto: el record marcado completo no publica en node: {completo}"

    recs = [_con(vrp_exceeds_sanity_cap=True), _con()]
    for vol in bp.VOLS:
        (tmp_path / f"{vol}.json").write_text(
            json.dumps({"records": recs if vol == "NevadosDeChillan" else []}), encoding="utf-8")
    out = bp.cargar_nuestros(coords, inner, VENTANA, data=tmp_path)
    assert len(out) == 2, f"el banco no cargo los 2 records (ventana o filtro diurno): {len(out)}"
    pubs = [r["pub"] for r in out]
    assert pubs[1] == 0, f"control roto: sin marca, 60 GW tendria que seguir en 0: {pubs}"
    assert pubs[0] == 1, ("el banco recorta la marca del tope antes de node y no publica la erupcion que el "
                          f"navegador publica: {pubs}")
