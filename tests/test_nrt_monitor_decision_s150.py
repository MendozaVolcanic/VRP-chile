# -*- coding: utf-8 -*-
"""S150 (auditoria S150, A-2, verificado). El monitor del NRT cerro el issue del apagon (#754) como
"recuperado" el 2026-10-07 06:19 con el sistema todavia caido: la API de GitHub le devolvio corridas del
2026-09-03 y el monitor no comparaba fechas. Ademas filtraba solo corridas `schedule`, asi que con el
disparador externo (workflow_dispatch) no veria la mayoria de las corridas.

La decision vive en scripts/nrt_monitor_decision.js (funcion pura) y la llama .github/workflows/nrt-monitor.yml.
Estos casos la ejecutan con node, sin red.

Las dos preguntas del instrumento: si la decision estuviera rota (cerrar con corridas viejas, ignorar las
despachadas), test_corridas_viejas_no_cierran y test_cuenta_las_despachadas fallan; si node no corriera,
el subprocess falla y el test cae en rojo, no en verde.
"""
import json
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
JS = RAIZ / "scripts" / "nrt_monitor_decision.js"
AHORA = "2026-10-07T06:19:00Z"


def decidir(runs, ahora=AHORA, max_horas=12):
    codigo = "const {decidir} = require(%s); console.log(JSON.stringify(decidir(%s, Date.parse(%s), %d)));" % (
        json.dumps(str(JS)), json.dumps(runs), json.dumps(ahora), max_horas)
    out = subprocess.run(["node", "-e", codigo], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def corrida(creada, conclusion, evento="schedule"):
    return {"created_at": creada, "conclusion": conclusion, "event": evento, "html_url": "https://x/" + creada}


def test_tres_fallas_recientes_alertan():
    runs = [corrida("2026-10-07T00:10:00Z", "failure"), corrida("2026-10-06T19:00:00Z", "failure"),
            corrida("2026-10-06T13:00:00Z", "failure")]
    assert decidir(runs)["accion"] == "alerta"


def test_tres_verdes_recientes_recuperan():
    runs = [corrida("2026-10-07T00:10:00Z", "success"), corrida("2026-10-06T19:00:00Z", "success"),
            corrida("2026-10-06T13:00:00Z", "success")]
    assert decidir(runs)["accion"] == "recuperado"


def test_corridas_viejas_no_cierran():
    """El caso real del 2026-10-07: la API devolvio tres corridas verdes del 2026-09-03."""
    runs = [corrida("2026-09-03T12:00:00Z", "success"), corrida("2026-09-03T08:00:00Z", "success"),
            corrida("2026-09-03T04:00:00Z", "success")]
    d = decidir(runs)
    assert d["accion"] == "sin_dato", d
    assert "vieja" in d["motivo"]


def test_cuenta_las_despachadas():
    """Con el cron externo, las corridas nacen como workflow_dispatch: tienen que contar."""
    runs = [corrida("2026-10-07T05:10:00Z", "failure", "workflow_dispatch"),
            corrida("2026-10-07T04:10:00Z", "failure", "workflow_dispatch"),
            corrida("2026-10-07T03:10:00Z", "failure", "workflow_dispatch")]
    assert decidir(runs)["accion"] == "alerta"


def test_ordena_por_fecha_y_usa_las_tres_mas_nuevas():
    """Si la API entrega desordenado, manda la mas nueva: dos fallas viejas no tapan tres verdes nuevas."""
    runs = [corrida("2026-10-05T00:00:00Z", "failure"), corrida("2026-10-07T00:10:00Z", "success"),
            corrida("2026-10-06T19:00:00Z", "success"), corrida("2026-10-05T06:00:00Z", "failure"),
            corrida("2026-10-06T13:00:00Z", "success")]
    d = decidir(runs)
    assert d["accion"] == "recuperado", d
    assert [r["created_at"] for r in d["usadas"]] == ["2026-10-07T00:10:00Z", "2026-10-06T19:00:00Z", "2026-10-06T13:00:00Z"]


def test_menos_de_tres_es_sin_dato():
    assert decidir([corrida("2026-10-07T00:10:00Z", "failure")])["accion"] == "sin_dato"


def test_mezcla_no_alerta_ni_cierra():
    runs = [corrida("2026-10-07T00:10:00Z", "success"), corrida("2026-10-06T19:00:00Z", "failure"),
            corrida("2026-10-06T13:00:00Z", "failure")]
    assert decidir(runs)["accion"] == "nada"


def test_el_workflow_usa_la_funcion_y_no_filtra_por_evento():
    wf = (RAIZ / ".github" / "workflows" / "nrt-monitor.yml").read_text(encoding="utf-8")
    assert "nrt_monitor_decision.js" in wf
    assert "event: 'schedule'" not in wf
