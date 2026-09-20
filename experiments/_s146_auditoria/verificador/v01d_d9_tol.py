# -*- coding: utf-8 -*-
"""V-01d: sobre el commit de junio, que tolerancia temporal con CUALQUIER fila (incl. RUTINA) da 207/214?
(1) roto? n=214 debe repetirse. (2) muerto? la curva debe crecer con la tolerancia."""
import io, sys, json, subprocess, csv, datetime as dt
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from vlib import VOLS, ROOT, bucket, bucket_ref, ALIAS
C = "1d6b5b932b9323bc2a7bedcd93574ace8d4bdaee"
def show(p): return subprocess.run(["git", "-C", ROOT, "show", f"{C}:{p}"], capture_output=True).stdout.decode("utf-8", "replace")
ref = {}
for p in ("latest_consolidado.csv", "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"):
    for row in csv.DictReader(io.StringIO(show(p))):
        ref.setdefault(ALIAS.get(row["Volcan"].strip(), row["Volcan"].strip()), []).append((dt.datetime.fromisoformat(row["Fecha_Satelite_UTC"]), bucket_ref(row["Sensor"]), row["Tipo_Registro"].strip(), float(row["VRP_MW"] or 0)))
su = []
for v in VOLS:
    for r in json.loads(show(f"data/mirova_equivalent/{v}.json"))["records"]:
        f = r["datetime_utc"][:10]
        if not ("2026-05-01" <= f <= "2026-06-18"): continue
        pc = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
        d = r.get("diag_n_dnti_ctx_path") or 0; o = sum(r.get(k) or 0 for k in ("diag_n_bt_path", "diag_n_nti_path", "diag_n_eti_path"))
        if pc > 0 and r.get("t_bg_k") is not None and r["t_bg_k"] < 262 and d > o and r.get("distance_class") == "summit":
            su.append((v, dt.datetime.fromisoformat(r["datetime_utc"]), bucket(r["sensor"])))
print("n", len(su))
for tol in (5, 10, 15, 20, 30, 45, 60):
    for sens in (True, False):
        a = sum(1 for v, T, b in su if any((not sens or x[1] == b) and abs((x[0] - T).total_seconds()) <= tol * 60 for x in ref.get(v, [])))
        al = sum(1 for v, T, b in su if any((not sens or x[1] == b) and x[2].startswith("ALERTA") and abs((x[0] - T).total_seconds()) <= tol * 60 for x in ref.get(v, [])))
        vr = sum(1 for v, T, b in su if any((not sens or x[1] == b) and x[3] > 0 and abs((x[0] - T).total_seconds()) <= tol * 60 for x in ref.get(v, [])))
        print(f"tol {tol:3d} min mismo_sensor={sens}: cualquier fila {a}/214 | solo ALERTA* {al}/214 | VRP_MW>0 {vr}/214")
