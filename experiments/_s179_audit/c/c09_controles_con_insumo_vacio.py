# -*- coding: utf-8 -*-
"""Frente C, auditoria S179. Instrumento c09: los controles del lector con insumo vacio o roto (pendiente de
docs/AUDIT_S175.md §8 decision 3: «si #952 cura 254 es SIN DATO: nadie corrio leer_retro.py con insumo vacio»).

Llama a las funciones de control del lector de la ref de lectura (objeto de la auditoria) con insumos que NO deberian
dar verde, y dice que estado devuelven y a que fila lleva `veredicto`.

LAS DOS PREGUNTAS. (1) Si un control fuera un falso verde con insumo vacio, esto lo ve (imprime OK donde deberia haber
rojo). (2) Instrumento muerto: control positivo, con las filas reales de la lectura (lectura.json) los estados ya son
conocidos; aqui el caso «SIN SUSTRATO» sintetico tiene que NO bloquear y los demas tienen que bloquear.

Uso: python c09_controles_con_insumo_vacio.py
"""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
WT = Path("D:/vrp-trabajo/worktrees/s178-lectura")
sys.path.insert(0, str(WT / "experiments/_s172_retro_paquete"))
import leer_retro as L
R = L.Reglas()
regla_ok = {"_fila_regla": 6}


def fila(ctl):
    return L.veredicto("VIIRS375", regla_ok, ctl, {})[0]


def f(lab, z, pub=1, mag=1.0, noche="2026-02-10", dt="2026-02-10 05:00", vol="Lascar"):
    return {"vol": vol, "sensor": "VIIRS_NOAA20", "b": "VIIRS375", "dt": dt, "noche": noche, "tramo": "F26-V", "z": z,
            "estado": "ok", "_evaluable": True, "lab": lab, "vrp_mirova": 1.0,
            "_t": {b: {"pub": pub, "mag": mag} for b in ("K", "placebo") + L.BRAZOS}}


casos = {
    "controles de cenit, 0 pasadas": L.controles_cenit(R, [], "V"),
    "controles de cenit, 3 alertas sin cenit": L.controles_cenit(R, [f("protegida", None) for _ in range(3)], "V"),
    "controles de cenit, 3 alertas con cenit NaN": L.controles_cenit(R, [f("protegida", float("nan")) for _ in range(3)], "V"),
    "controles de cenit, solo negativos (ninguna alerta)": L.controles_cenit(R, [f("neg_limpio", 30.0, pub=0) for _ in range(5)], "V"),
    "controles de cenit, 2 alertas con cenit en 1 noche (sin sustrato real)": L.controles_cenit(
        R, [f("protegida", 10.0), f("protegida", 60.0, dt="2026-02-10 06:40")], "V"),
    "C-via, 0 pasadas": L.c_via([], "F26-V"),
    "C-cobertura, 0 pasadas": L.c_cobertura([]),
    "C-K, sin K-gemelo": L.c_k([f("neg_limpio", 30.0)], [], L.TIER_A),
    "C-montaje, sin resultado": L.validar_montaje(None),
    "C-montaje, {'estado': 'OK'} suelto": L.validar_montaje({"estado": "OK"}),
    "candado, manifiesto vacio": L.candado({}),
    "C-cenit OSF, sin pares": {"estado": L._estado_cenit([])},
}
for nom, c in casos.items():
    est = str(c.get("estado"))
    print(f"{nom}: estado = {est[:110]} -> fila {fila({'x': c} if not nom.startswith('controles de cenit') else {'controles_cenit': c})}")
