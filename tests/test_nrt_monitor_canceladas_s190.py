# -*- coding: utf-8 -*-
"""S190 (auditoría de Codex, ronda 2, F6-106, CONFIRMADO gravedad 3 por el verificador Claude del frente 6,
D:\\codex-vrp\\_salida\\ronda2\\f6_verificacion\\VEREDICTO.md). Una corrida cancelada no dice nada de la salud del NRT.

POR QUÉ: `decidir` contaba como falla sólo `failure` y `timed_out`. Tres corridas `cancelled` seguidas daban «0 de 3
fallaron» y el monitor cerraba el issue del apagón como «recuperado» con el NRT todavía caído; y una cancelada entre
dos fallas impedía abrir la alerta. Pasa en operación: el grupo de concurrencia `push-main` cancela la corrida que
espera cuando llega otra. Una alerta que se cierra sola en falso es lo que S150 ya había corregido por otra vía.

Regla nueva: sólo deciden las corridas con conclusión decisiva (verde: `success`; falla: `failure`, `timed_out`,
`startup_failure`); las demás (`cancelled`, `skipped`, `neutral`, `action_required`, `stale`) se saltan y se toman
las tres decisivas más nuevas. El tope de antigüedad sigue: si las decisivas son viejas, SIN DATO.

Controles, verdes antes y después del arreglo: una cancelada delante de tres verdes no tapa la recuperación, y tres
fallas seguidas alertan. Los casos de S150 siguen en tests/test_nrt_monitor_decision_s150.py.
"""
import json
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
JS = RAIZ / "scripts" / "nrt_monitor_decision.js"
AHORA = "2026-11-19T12:00:00Z"


def decidir(runs, ahora=AHORA, max_horas=12):
    codigo = "const {decidir} = require(%s); console.log(JSON.stringify(decidir(%s, Date.parse(%s), %d)));" % (
        json.dumps(str(JS)), json.dumps(runs), json.dumps(ahora), max_horas)
    out = subprocess.run(["node", "-e", codigo], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def corrida(hora, conclusion):
    creada = f"2026-11-19T{hora}:00Z"
    return {"created_at": creada, "conclusion": conclusion, "event": "workflow_dispatch", "html_url": "https://x/" + creada}


def test_tres_canceladas_no_cierran_la_alerta():
    runs = [corrida("11:10", "cancelled"), corrida("10:10", "cancelled"), corrida("09:10", "cancelled"),
            corrida("08:10", "failure"), corrida("07:10", "failure"), corrida("06:10", "failure")]
    d = decidir(runs)
    assert d["accion"] != "recuperado", d
    assert d["accion"] == "alerta", d


def test_una_cancelada_entre_fallas_no_impide_alertar():
    runs = [corrida("11:10", "failure"), corrida("10:10", "cancelled"), corrida("09:10", "failure"),
            corrida("08:10", "failure")]
    assert decidir(runs)["accion"] == "alerta"


def test_startup_failure_es_falla():
    """Un workflow inválido termina con 0 jobs y conclusión startup_failure (S160): no mide nada."""
    runs = [corrida("11:10", "startup_failure"), corrida("10:10", "startup_failure"),
            corrida("09:10", "startup_failure")]
    assert decidir(runs)["accion"] == "alerta"


def test_solo_canceladas_es_sin_dato():
    runs = [corrida("11:10", "cancelled"), corrida("10:10", "cancelled"), corrida("09:10", "cancelled")]
    assert decidir(runs)["accion"] == "sin_dato"


def test_control_canceladas_no_tapan_tres_verdes():
    runs = [corrida("11:10", "cancelled"), corrida("10:10", "success"), corrida("09:10", "success"),
            corrida("08:10", "success")]
    assert decidir(runs)["accion"] == "recuperado"


def test_control_tres_fallas_alertan():
    runs = [corrida("11:10", "failure"), corrida("10:10", "failure"), corrida("09:10", "failure")]
    assert decidir(runs)["accion"] == "alerta"
