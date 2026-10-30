# -*- coding: utf-8 -*-
"""S169 (P3-09 de experiments/_s169/audit_patrones/f3/INFORME_F3.md, en loop/activo): alguien vigila la sombra.

POR QUÉ. Hasta S169 ningún monitor miraba `.github/workflows/sombra-codigo-mirova.yml`: ni nrt-monitor (sólo
nrt.yml), ni reproc-watchdog (sólo `reproc-*`), ni la medición de cadencia del cron. Un job rojo dejaba una X en
Actions y un cron que no llega no deja nada; sobre esas noches se decide si la vía «código MIROVA» pasa a
producción. Se extiende el mecanismo que ya abre issues para el NRT (nrt-monitor.yml, con la decisión pura en
scripts/nrt_monitor_decision.js): desde el 2026-11-03 15:00 UTC, si no hay una corrida programada verde de la sombra
en las últimas 26 h, se abre (o se refresca) un issue; con una verde se cierra.

Las dos preguntas del instrumento: si la decisión no mirara la edad, test_verde_vieja_alerta fallaría; si alertara
siempre, test_verde_reciente_no_alerta fallaría; si node no corriera, el subprocess cae en rojo, no en verde.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
JS = RAIZ / "scripts" / "nrt_monitor_decision.js"
SOMBRA = RAIZ / ".github" / "workflows" / "sombra-codigo-mirova.yml"
MONITOR = RAIZ / ".github" / "workflows" / "nrt-monitor.yml"
sys.path.insert(0, str(RAIZ))


def decidir(runs, ahora):
    codigo = ("const {decidirSombra} = require(%s); "
              "console.log(JSON.stringify(decidirSombra(%s, Date.parse(%s))));") % (
        json.dumps(str(JS)), json.dumps(runs), json.dumps(ahora))
    out = subprocess.run(["node", "-e", codigo], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def corrida(creada, conclusion, evento="schedule", estado="completed"):
    return {"created_at": creada, "conclusion": conclusion, "event": evento, "status": estado,
            "html_url": "https://x/" + creada}


def test_antes_de_la_primera_corrida_con_datos_no_decide():
    assert decidir([], "2026-11-03T12:30:00Z")["accion"] == "inactivo"


def test_verde_reciente_no_alerta():
    d = decidir([corrida("2026-11-05T15:00:00Z", "success")], "2026-11-05T18:30:00Z")
    assert d["accion"] == "ok", d


def test_verde_vieja_alerta():
    """La de hoy (15:00) falló: la última verde es de ayer a las 15:00, 27,5 h antes del chequeo de las 18:30."""
    runs = [corrida("2026-11-05T15:00:00Z", "failure"), corrida("2026-11-04T15:00:00Z", "success")]
    d = decidir(runs, "2026-11-05T18:30:00Z")
    assert d["accion"] == "alerta", d


def test_el_cron_que_no_llega_alerta():
    """Ninguna corrida: el workflow quedó desactivado o GitHub no entregó el evento."""
    d = decidir([corrida("2026-11-03T15:00:00Z", "success")], "2026-11-05T00:30:00Z")
    assert d["accion"] == "alerta", d
    assert decidir([], "2026-11-05T00:30:00Z")["accion"] == "alerta"


def test_una_corrida_en_curso_o_manual_no_cuenta_como_verde():
    """Un despacho a mano (medir, un solo volcán) no prueba que la corrida diaria completa salió."""
    runs = [corrida("2026-11-05T16:00:00Z", "success", evento="workflow_dispatch"),
            corrida("2026-11-05T15:00:00Z", None, estado="in_progress"),
            corrida("2026-11-04T12:00:00Z", "success")]
    # S169 ronda 2: con la de hoy en curso la respuesta es «pendiente» (VV169-04), nunca «ok»
    assert decidir(runs, "2026-11-05T18:30:00Z")["accion"] != "ok"


def test_la_verde_mas_nueva_manda_aunque_la_api_desordene():
    runs = [corrida("2026-11-03T15:00:00Z", "failure"), corrida("2026-11-05T15:00:00Z", "success"),
            corrida("2026-11-04T15:00:00Z", "failure")]
    d = decidir(runs, "2026-11-05T18:30:00Z")
    assert d["accion"] == "ok" and d["ultima_verde"]["created_at"] == "2026-11-05T15:00:00Z", d


def test_nrt_monitor_vigila_el_workflow_de_la_sombra():
    d = yaml.safe_load(MONITOR.read_text(encoding="utf-8"))
    assert "on" in d and True not in d, "'on' entre comillas (A43)"
    pasos = d["jobs"]["check"]["steps"]
    sombra = [s for s in pasos if "sombra-codigo-mirova.yml" in str((s.get("with") or {}).get("script", ""))]
    assert len(sombra) == 1, "nrt-monitor no tiene un paso que mire la sombra"
    script = sombra[0]["with"]["script"]
    assert "decidirSombra" in script and "issues.create" in script and "state: 'closed'" in script
    assert sombra[0].get("if", "").startswith("always()"), "un paso previo en rojo no debe apagar la vigilancia"
    # el checkout ralo del monitor tiene que traer el módulo que define la decisión
    checkout = next(s for s in pasos if str(s.get("uses", "")).startswith("actions/checkout"))
    assert "scripts/nrt_monitor_decision.js" in checkout["with"]["sparse-checkout"]


def test_vv04_la_corrida_de_hoy_en_curso_es_pendiente():
    """GitHub retrasa el cron del minuto 0: a las 18:30 la de hoy puede seguir corriendo. No se alerta ni se cierra."""
    verde_ayer = corrida("2026-11-04T15:00:00Z", "success")
    for estado in ("in_progress", "queued"):
        d = decidir([corrida("2026-11-05T15:40:00Z", None, estado=estado), verde_ayer], "2026-11-05T18:30:00Z")
        assert d["accion"] == "pendiente", (estado, d)


def test_vv04_una_corrida_en_curso_vieja_no_tapa_la_alerta():
    """Más de 6 h en curso ya no es retraso: es una corrida colgada y la noche no está medida."""
    runs = [corrida("2026-11-05T11:00:00Z", None, estado="in_progress"), corrida("2026-11-04T09:00:00Z", "success")]
    assert decidir(runs, "2026-11-05T18:30:00Z")["accion"] == "alerta"
    # y una despachada a mano en curso tampoco cuenta como la diaria
    runs = [corrida("2026-11-05T17:00:00Z", None, evento="workflow_dispatch", estado="in_progress"),
            corrida("2026-11-04T15:00:00Z", "success")]
    assert decidir(runs, "2026-11-05T18:30:00Z")["accion"] == "alerta"


def test_vv04_el_monitor_no_abre_ni_cierra_con_pendiente():
    d = yaml.safe_load(MONITOR.read_text(encoding="utf-8"))
    script = next(s for s in d["jobs"]["check"]["steps"]
                  if "sombra-codigo-mirova.yml" in str((s.get("with") or {}).get("script", "")))["with"]["script"]
    corte = script.index("const TITLE")
    assert re.search(r"if \(d\.accion === 'inactivo' \|\| d\.accion === 'pendiente'\) return;", script[:corte]), (
        "con «pendiente» el paso tiene que salir antes de tocar el issue")


def test_r_nrt_monitor_tiene_permiso_de_issues_y_de_actions():
    """Sin issues: write el paso cae con 403 el 2026-11-03; sin actions: read no puede listar las corridas."""
    d = yaml.safe_load(MONITOR.read_text(encoding="utf-8"))
    job = d["jobs"]["check"]
    permisos = dict(d.get("permissions") or {})
    permisos.update(job.get("permissions") or {})
    assert permisos.get("issues") == "write", permisos
    assert permisos.get("actions") in ("read", "write"), permisos


def test_la_cadencia_del_cron_cuenta_la_sombra_una_vez_al_dia():
    from scripts.medir_cadencia_cron import ESPERADO_POR_DIA
    wf = yaml.safe_load(SOMBRA.read_text(encoding="utf-8"))
    assert wf["on"]["schedule"] == [{"cron": "0 15 * * *"}]
    assert ESPERADO_POR_DIA.get(wf["name"]) == 1, (wf["name"], ESPERADO_POR_DIA)
