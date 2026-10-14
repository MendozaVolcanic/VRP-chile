# -*- coding: utf-8 -*-
"""Tarea 0.1 del loop (S150): la referencia de MIROVA sale de la UNION historica del consolidado.

POR QUE: el consolidado remoto de Mirova-v1 perdio filas en silencio al menos cinco veces y nunca
las repuso (docs/audit_s150/meta/VERIFICADOR_DATOS.md D1). La ultima caida (06-oct) se llevo 207
filas, 8 de ellas ALERTA_TERMICA. Una referencia congelada desde el remoto de hoy no las tiene, y
toda prueba medida contra ella cuenta como "publicacion de mas" una alerta que MIROVA si dio.

El fixture `tests/datos_s150/perdidas_06oct.csv` se genero comparando el tag
`pre-s150-consolidado-perdida-207` con el remoto, sin pasar por el codigo de la union: si la union
se rompe, el fixture no se rompe con ella.
"""
import csv
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.referencia_mirova_unificada import (clave,  # noqa: E402
                                                 cargar_referencia_unificada,
                                                 leer_pasadas)

FIXTURE = ROOT / "tests" / "datos_s150" / "perdidas_06oct.csv"
TAG = "pre-s150-consolidado-perdida-207"
RUTA_SNAP = "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv"


def _perdidas():
    with open(FIXTURE, encoding="utf-8") as fh:
        lineas = [ln for ln in fh if not ln.startswith("#")]
    return list(csv.DictReader(lineas))


def test_fixture_tiene_las_207_y_las_8_alertas():
    perd = _perdidas()
    assert len(perd) == 207
    assert sum(p["tipo"] == "ALERTA_TERMICA" for p in perd) == 8


def test_toda_perdida_del_06oct_esta_en_la_union_con_su_tipo():
    ref = {clave(f): f for f in cargar_referencia_unificada()}
    faltan, cambian = [], []
    for p in _perdidas():
        k = (p["volcano"], p["sensor_bucket"], p["fecha_utc"], "CONS")
        if k not in ref:
            faltan.append(k)
        elif ref[k]["tipo"] != p["tipo"]:
            cambian.append((k, ref[k]["tipo"], p["tipo"]))
    assert not faltan, f"{len(faltan)} perdidas no estan en la union, p. ej. {faltan[:3]}"
    assert not cambian, cambian[:3]


def test_control_sin_historico_las_perdidas_no_estan():
    # Control de instrumento: sin la union historica, el snapshot de hoy no tiene esas filas. Si
    # este control pasara a verde por si solo, el test anterior dejaria de probar la union.
    ref = {clave(f) for f in cargar_referencia_unificada(historico_path=None)}
    claves = [(p["volcano"], p["sensor_bucket"], p["fecha_utc"], "CONS") for p in _perdidas()]
    ausentes = sum(k not in ref for k in claves)
    assert ausentes > 0, "el snapshot ya tiene todas las perdidas: el test de la union no discrimina"


def _tag_disponible():
    r = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "-q", "--verify", f"refs/tags/{TAG}"],
                       capture_output=True, text=True)
    return r.returncode == 0


@pytest.mark.skipif(not _tag_disponible(), reason="el checkout no trae tags (CI superficial)")
def test_todo_el_snapshot_del_tag_esta_en_la_union(tmp_path):
    destino = tmp_path / "tag.csv"
    contenido = subprocess.run(["git", "-C", str(ROOT), "show", f"{TAG}:{RUTA_SNAP}"],
                               capture_output=True, check=True).stdout
    destino.write_bytes(contenido)
    ref = {clave(f) for f in cargar_referencia_unificada()}
    faltan = [clave(f) for f in leer_pasadas(destino, "CONS", "tag") if clave(f) not in ref]
    assert not faltan, f"{len(faltan)} filas del tag faltan, p. ej. {faltan[:3]}"


def _dias_de_atraso(fecha_commit_union: str, fecha_max_snapshot: str) -> float:
    from datetime import datetime
    u = datetime.fromisoformat(fecha_commit_union.replace("Z", "")[:19])
    s = datetime.fromisoformat(fecha_max_snapshot[:16])
    return (s - u).total_seconds() / 86400


def test_la_union_no_esta_atrasada_respecto_del_snapshot():
    # Alarma de caidas FUTURAS. La union solo sabe de las versiones que recorrio; si el auto-audit
    # refresca el snapshot despues de una caida nueva y la union no se regenero, las filas perdidas
    # no estan en ningun lado y ningun otro test se entera. Tolerancia 8 dias: el snapshot y la
    # union se regeneran juntos cada lunes (audit-weekly.yml), mas un dia de margen.
    import json
    from scripts.referencia_mirova_unificada import HISTORICO_PROCEDENCIA, SNAP_CONS
    proc = json.loads(HISTORICO_PROCEDENCIA.read_text(encoding="utf-8"))
    max_snap = max(f["fecha_utc"] for f in leer_pasadas(SNAP_CONS, "CONS", "principal"))
    atraso = _dias_de_atraso(proc["version_mas_nueva"]["fecha_commit"], max_snap)
    assert atraso <= 8, (f"la union historica termina {atraso:.1f} dias antes que el snapshot: correr "
                         "scripts/referencia_mirova_unificada.py --union-historica")


def test_control_la_alarma_de_atraso_dispara():
    assert _dias_de_atraso("2026-10-01T00:00:00Z", "2026-10-20 00:00") > 8
    assert _dias_de_atraso("2026-10-14T11:06:03Z", "2026-10-13 23:00") <= 8


def test_reintentos_ante_fallo_transitorio(monkeypatch):
    import time
    from scripts.referencia_mirova_unificada import _con_reintentos
    monkeypatch.setattr(time, "sleep", lambda s: None)
    llamadas = []

    def falla_dos_veces():
        llamadas.append(1)
        if len(llamadas) < 3:
            raise OSError("red")
        return "ok"
    assert _con_reintentos(falla_dos_veces) == "ok" and len(llamadas) == 3

    def siempre_falla():
        raise OSError("red caida")
    with pytest.raises(OSError):
        _con_reintentos(siempre_falla)


def test_las_filas_historicas_solo_agregan():
    # La fila del remoto de hoy gana siempre; la union historica solo aporta claves ausentes.
    sin = {clave(f): f for f in cargar_referencia_unificada(historico_path=None, respaldo_path=None)}
    con = {clave(f): f for f in cargar_referencia_unificada(respaldo_path=None)}
    assert set(sin) <= set(con)
    assert all(con[k]["origen"] == "principal" for k in sin)
    assert all(con[k]["origen"] == "historico" for k in set(con) - set(sin))
