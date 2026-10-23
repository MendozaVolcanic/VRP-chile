# -*- coding: utf-8 -*-
"""S158: el vigilante de OSF del grupo MIROVA avisa lo nuevo y no queda en verde cuando está ciego.

POR QUÉ: el código operacional de MIROVA estuvo tres meses publicado sin que nadie se enterara. El vigilante sólo
sirve si (a) detecta actividad nueva y proyectos nuevos, y (b) avisa cuando no puede leer OSF, en vez de dar verde
(lección S156: un vigilante ciego da VERDE). Sin red: OSF se reemplaza por un diccionario.
"""
import json
import os
import sys

import yaml

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import vigilar_osf_mirova as v  # noqa: E402


def _osf_falso(nodos_por_autor, logs):
    """get() falso: nodos públicos por autor y último log por nodo."""
    def get(url):
        for uid in v.AUTORES:
            if f"/users/{uid}/nodes/" in url:
                return {"data": [{"id": n, "attributes": {"public": True, "title": f"t {n}"}}
                                 for n in nodos_por_autor.get(uid, [])], "links": {"next": None}}
        for n, (fecha, accion) in logs.items():
            if f"/nodes/{n}/logs/" in url:
                return {"data": [{"attributes": {"date": fecha, "action": accion}}], "links": {"next": None}}
        raise AssertionError(f"url inesperada {url}")
    return get


BASE_NODOS = {"ws5y3": ["zm62w", "jepv6"]}
BASE_LOGS = {"zm62w": ("2026-08-19T08:05:35", "custom_citation_edited"), "jepv6": ("2025-04-09T15:27:53", "x")}


def _base(tmp_path):
    p = tmp_path / "base.json"
    assert v.main(["--generar-linea-base"], get=_osf_falso(BASE_NODOS, BASE_LOGS), linea_base=str(p)) == 0
    return str(p)


def test_sin_novedades_da_cero(tmp_path):
    p = _base(tmp_path)
    assert v.main([], get=_osf_falso(BASE_NODOS, BASE_LOGS), linea_base=p) == 0


def test_actividad_nueva_da_uno(tmp_path, capsys):
    p = _base(tmp_path)
    logs = dict(BASE_LOGS, zm62w=("2026-11-02T10:00:00", "osf_storage_file_added"))
    assert v.main([], get=_osf_falso(BASE_NODOS, logs), linea_base=p) == 1
    assert "osf_storage_file_added" in capsys.readouterr().out


def test_proyecto_nuevo_da_uno(tmp_path, capsys):
    p = _base(tmp_path)
    nodos = {"ws5y3": ["zm62w", "jepv6"], "rm7t4": ["nuevo"]}
    logs = dict(BASE_LOGS, nuevo=("2026-11-02T10:00:00", "project_created"))
    assert v.main([], get=_osf_falso(nodos, logs), linea_base=p) == 1
    assert "proyecto OSF nuevo: nuevo" in capsys.readouterr().out


def test_proyecto_que_desaparece_da_uno(tmp_path):
    p = _base(tmp_path)
    assert v.main([], get=_osf_falso({"ws5y3": ["zm62w"]}, BASE_LOGS), linea_base=p) == 1


def test_osf_caido_da_ciego(tmp_path):
    p = _base(tmp_path)

    def caido(url):
        raise RuntimeError("HTTP 503")
    assert v.main([], get=caido, linea_base=p) == 2


def test_osf_sin_proyectos_da_ciego(tmp_path):
    """Un cambio de formato que devuelve listas vacías no puede leerse como «sin novedades»."""
    p = _base(tmp_path)
    assert v.main([], get=_osf_falso({}, {}), linea_base=p) == 2


def test_sin_linea_base_da_ciego(tmp_path):
    assert v.main([], get=_osf_falso(BASE_NODOS, BASE_LOGS), linea_base=str(tmp_path / "no.json")) == 2


def test_linea_base_versionada_cubre_zm62w_y_el_codigo():
    base = json.load(open(v.LINEA_BASE, encoding="utf-8"))
    assert "zm62w" in base["nodos"]
    # la línea base es posterior a la publicación del código (2026-07-24): si no, el aviso ya habría saltado
    assert base["nodos"]["zm62w"]["ultimo_log"] >= "2026-07-24"


def test_workflow_abre_issue_sin_empujar():
    wf = os.path.join(RAIZ, ".github", "workflows", "vigilar-osf-mirova.yml")
    texto = open(wf, encoding="utf-8").read()
    y = yaml.safe_load(texto)
    assert "on" in y, "A43: la clave on va entre comillas"
    assert "schedule" in y["on"] and "workflow_dispatch" in y["on"]
    assert y["permissions"] == {"contents": "read", "issues": "write"}
    assert "git push" not in texto
    assert "scripts/vigilar_osf_mirova.py" in texto
    # las dos salidas que no son verde abren issue (novedad y ciego). S161: mira el `if` del paso que abre el
    # issue, con comillas SIMPLES; antes exigía '"1"' y '"2"' en el texto y así fijaba la forma que GitHub rechaza
    # (comillas dobles en una expresión: el workflow nunca corrió en main, tests/test_guard_expresiones_workflows_s161.py)
    paso = next(p for p in y["jobs"]["vigilar"]["steps"] if p.get("name", "").startswith("Abrir issue"))
    assert "codigo == '1'" in paso["if"] and "codigo == '2'" in paso["if"], paso["if"]
