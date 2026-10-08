# -*- coding: utf-8 -*-
"""S150 frente B. El tope D9 de 5,0 MW (pipeline/path_d_cap.py) se activa con un predicado que
el tablero describe como "path D disparo sobre cirrus" (frontend/index.html:1101). El predicado
real (process_modis.py:1009, process_viirs.py:1415, process_viirs_mod.py:987) es:
n_bt_path == 0 y n_nti_path == 0 y t_bg < 270 K. Con ENABLE_BT_PATH_HOT=False, n_bt_path es
siempre 0. Aca se reconstruye el predicado record a record desde los diagnosticos persistidos
(diag_n_bt_path, diag_n_nti_path, t_bg_k) en Nevados de Chillan, y se cruza con MIROVA.

Preguntas del instrumento:
1. Si el predicado estuviera siempre apagado, 'pred_activo' daria 0; si siempre encendido, = n.
   Control positivo: todo record con pc.vrp_mw == 5,000 debe tener el predicado activo (si no,
   la reconstruccion esta mal).
2. Si los diagnosticos no se persistieran, diag_n_nti_path seria None: se cuentan los None.
Ventana: 2026-09-20 a 2026-10-02 07:35 UTC (y, aparte, todo 2026 para el control).
"""
import json, sys, collections
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
d = json.load(open(AQUI / "datos" / "NevadosDeChillan.json", encoding="utf-8"))
t = {(x["dt"], x["sensor"]): x for x in json.load(open(AQUI / "tabla_ndc.json", encoding="utf-8"))["filas"]}


def b(s):
    return "MODIS" if s.startswith("MODIS") else ("V750" if s.endswith("_750") else "V375")


c = collections.Counter()
ctrl = collections.Counter()
for r in d["records"]:
    if r["datetime_utc"] < "2026-01-01":
        continue
    nb, nn, tb = r.get("diag_n_bt_path"), r.get("diag_n_nti_path"), r.get("t_bg_k")
    if nn is None or tb is None:
        c[b(r["sensor"]), "diag_None"] += 1 if r["datetime_utc"] >= "2026-09-20" else 0
        continue
    pred = (nb or 0) == 0 and nn == 0 and tb < 270.0
    pc = (r.get("primary_cluster") or {}).get("vrp_mw")
    if pc is not None and abs(pc - 5.0) < 1e-9:
        ctrl["pc=5.000"] += 1
        ctrl["pc=5.000_y_pred"] += pred
    if r["datetime_utc"] >= "2026-09-20":
        k = b(r["sensor"])
        c[k, "n"] += 1
        c[k, "pred_activo"] += pred
        c[k, "nti_path>0"] += nn > 0
        x = t.get((r["datetime_utc"], r["sensor"]))
        if x and any(m["tipo"].startswith("ALERTA") for m in x["mirova"]):
            c[k, "alerta_MIROVA"] += 1
            c[k, "alerta_MIROVA_y_pred"] += pred
print("control 2026 completo:", dict(ctrl))
print("ventana 09-20 a 10-02:", {f"{a}|{b_}": v for (a, b_), v in sorted(c.items())})
