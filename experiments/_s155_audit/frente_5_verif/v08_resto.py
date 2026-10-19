# -*- coding: utf-8 -*-
"""Verificador F5, paso 8: F5-05 (MODIS protegidas no detectadas), F5-06 (tope D9), F5-07 (lambda B21 con
B22 primaria), F5-08 (records C0 en la ventana K). Ventana de observacion 2026-09-28..2026-10-19.
Cada bloque imprime su denominador. Controles: F5-06 cuenta tambien records con d9_capped en TODO el
archivo (si da 0 en todo el corpus, el instrumento no ve el tope y se dice); F5-08 cuenta records con
processed_utc posterior al PR #850 (control positivo: deben ser mayoria)."""
import io, json, math, os, sys
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(AQUI, "..", "..", "..", "data", "mirova_equivalent", "NevadosDeChillan.json"), encoding="utf-8"))
todos = d["records"]
w = [r for r in todos if "2026-09-28" <= r["datetime_utc"][:10] <= "2026-10-19"]
print("records ventana=%d" % len(w))
print("\n[F5-05]")
for t in ("2026-10-12 07:20", "2026-10-15 01:05"):
    for r in w:
        if r["datetime_utc"][:16] == t and "MODIS" in r["sensor"]:
            print(" ", t, r["sensor"], "cenit", r.get("sensor_zenith_deg"), "solar", r.get("solar_zenith_deg"), "n_anom", r.get("n_anomalous_pixels"),
                  "t_bg", r.get("t_bg_k"), "t_max", r.get("t_max_k"), "nti_max", r.get("nti_max"), "pc", r.get("primary_cluster"),
                  "diag_t_max_dist", r.get("diag_t_max_dist_km"), "processed", r.get("processed_utc"))
    noche = t[:10]
    pub375 = [(r["datetime_utc"][11:16], r.get("f5_core_vrp_mw")) for r in w if r["datetime_utc"][:10] == noche and r["sensor"].startswith("VIIRS")
              and not r["sensor"].endswith("_750") and r.get("distance_class") == "summit" and (r.get("f5_core_vrp_mw") or 0) > 0]
    print("   V375 publicados ese dia UTC:", pub375)
print("\n[F5-06] condicion del tope D9 (n_bt_path==0, n_nti_path==0, t_bg<270) en records con deteccion")
cond = [r for r in w if (r.get("n_anomalous_pixels") or 0) > 0 and r.get("n_bt_path", r.get("diag_n_bt_path")) == 0
        and r.get("n_nti_path", r.get("diag_n_nti_path")) == 0 and r.get("t_bg_k") is not None and r["t_bg_k"] < 270]
print("  con condicion=%d de %d con deteccion; por sensor %s" % (len(cond), sum(1 for r in w if (r.get('n_anomalous_pixels') or 0) > 0), Counter(r["sensor"] for r in cond)))
print("  de ellos con pc.vrp_mw >= 5 (donde el tope podria actuar): %d" % sum(1 for r in cond if ((r.get("primary_cluster") or {}).get("vrp_mw") or 0) >= 5))
print("  d9_capped en ventana=%d; en todo el archivo=%d de %d records" % (sum(1 for r in w if (r.get("primary_cluster") or {}).get("d9_capped")),
      sum(1 for r in todos if (r.get("primary_cluster") or {}).get("d9_capped")), len(todos)))
print("\n[F5-07] exceso de radiancia con lambda B21 (3,929) sobre BT de B22 (3,959)")
C1, C2 = 1.191042e8, 14388.0
L = lambda lam, t: C1 / (lam ** 5 * (math.exp(C2 / (lam * t)) - 1))
for th, tb in ((300, 265), (320, 270), (350, 270), (400, 270)):
    print("  T=%d Tbg=%d  dL21/dL22 = %.3f" % (th, tb, (L(3.929, th) - L(3.929, tb)) / (L(3.959, th) - L(3.959, tb))))
print("\n[F5-08] processed_utc frente al PR #850 (2026-10-18T09:57:30Z)")
def proc(r):
    return (r.get("processed_utc") or "")[:19].replace(" ", "T")
k = [r for r in w if r["datetime_utc"][:10] >= "2026-09-18"]
viejos = [r for r in k if proc(r) and proc(r) < "2026-10-18T09:57:30"]
print("  records ventana con obs>=09-18: %d; procesados antes de #850: %d; sin processed_utc: %d" % (len(k), len(viejos), sum(1 for r in k if not proc(r))))
for r in viejos:
    print("   ", r["datetime_utc"], r["sensor"], proc(r), r.get("distance_class"), (r.get("primary_cluster") or {}).get("vrp_mw"))
