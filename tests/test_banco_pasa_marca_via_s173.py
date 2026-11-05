"""S173 S1 (VPR944-01): el banco de paridad le pasa a node la marca de la via «codigo MIROVA».

POR QUE. Desde el PR #944 el tablero no le aplica los filtros de artefacto termico (S90 cirrus, S93 campo
difuso) a los records de la via: la via no tiene path D y en pasadas oblicuas su celda de 1 km mezcla foco y
nieve, asi que su t_max queda bajo 0 grados con calor real. El banco (`scripts/banco_paridad.py`) es el
predicado del tablero ejecutado con node (A97) para la vigilancia de la reversion de MODIS
(`vigilancia_guardia_modis.py`), la de la sombra y el auto-audit. Pero `cargar_nuestros` recorta cada record a
`CAMPOS_JS` antes de mandarlo a node, y `CAMPOS_JS` no traia `via_codigo_mirova`: la marca no llegaba, y un
record de la via frio y sobre 10 MW que el navegador publica salia NO publicado en el banco. La vigilancia lo
habria leido como «produccion calla» (declarado distinto de efectivo, A116/A118).

QUE VIGILA. El record X2 de Chillan (2026-10-01 08:35, cenit 50,45, t_max 269,57 K, 11,44 MW) pasado por
`cargar_nuestros` sobre una carpeta de datos temporal:
1. con `via_codigo_mirova: true` sale publicado (como en el navegador);
2. el MISMO record sin la marca (K) sale no publicado (el filtro cirrus sigue para K);
3. con la marca en texto (`"sin_grilla"`: K que corrio con la via encendida, A118) sale no publicado.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Con el banco de antes (sin la clave en CAMPOS_JS) el caso 1 falla:
medido, da 0. (2) El control 2 es el mismo record y tiene que dar 0; y el control 0 manda el record completo
a `correr_node` sin pasar por el recorte y tiene que dar 1, asi que el instrumento puede dar 1 y puede dar 0.
"""
import json
import os
import shutil
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import banco_paridad as bp  # noqa: E402

X2_CHILLAN = {"sensor": "MODIS_AQUA", "datetime_utc": "2026-10-01 08:35", "distance_class": "summit",
              "t_max_k": 269.57, "vrp_mw": 11.442, "triggered_test1": False, "vrp_vent_mw": 0.0,
              "f5_core_vrp_mw": None, "anomaly_pixels": [],
              "primary_cluster": {"vrp_mw": 11.442, "centroid_dist_km": 0.708, "n_pixels": 8}}
VENTANA = ("2026-10-01", "2026-10-01")

node = pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")


def _con(**kw):
    r = json.loads(json.dumps(X2_CHILLAN))
    r.update(kw)
    return r


@node
def test_el_banco_pasa_la_marca_de_la_via_a_node(tmp_path):
    inner = bp.inner_desde_html()
    coords = bp._coords_por_volcan()
    # control 0: el record completo, sin el recorte, publica (el instrumento puede dar 1)
    completo = bp.correr_node([[_con(via_codigo_mirova=True), inner["NevadosDeChillan"]]])
    assert completo[0][4] == 1, f"control roto: el record completo de la via no publica en node: {completo}"

    recs = [_con(via_codigo_mirova=True), _con(), _con(via_codigo_mirova="sin_grilla")]
    for vol in bp.VOLS:
        (tmp_path / f"{vol}.json").write_text(
            json.dumps({"records": recs if vol == "NevadosDeChillan" else []}), encoding="utf-8")
    out = bp.cargar_nuestros(coords, inner, VENTANA, data=tmp_path)
    assert len(out) == 3, f"el banco no cargo los 3 records (ventana o filtro diurno): {len(out)}"
    pubs = [r["pub"] for r in out]
    assert pubs[1] == 0, f"control roto: el record de K tendria que caer en el filtro cirrus: {pubs}"
    assert pubs[2] == 0, f"un record de K con aviso de la via no se exenta (A118): {pubs}"
    assert pubs[0] == 1, ("el banco recorta la marca de la via antes de node y no publica lo que el navegador "
                          f"publica (VPR944-01): {pubs}")
