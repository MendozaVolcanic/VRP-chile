# -*- coding: utf-8 -*-
"""S149, frente D. Las 6 positivas VIIRS 375 que el brazo sin Test 1 deja de publicar: en el brazo,
el record NO DETECTA nada, o detecta y el predicado del tablero lo esconde (far, magnitud nula)?
Control positivo: las mismas pasadas en el control deben traer cumulo primario y summit.
Uso: python d3_las_seis_perdidas.py DIR_SALIDAS"""
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = Path(sys.argv[1])
SEIS = [("NevadosDeChillan", "2026-09-05 05:48"), ("NevadosDeChillan", "2026-09-14 05:42"), ("Isluga", "2026-09-13 05:12"),
        ("Isluga", "2026-09-19 05:42"), ("Tupungatito", "2026-09-17 04:48"), ("NevadosDeChillan", "2026-09-18 05:24")]
for vol, dt in SEIS:
    print("\n", vol, dt)
    for brazo in ("_s146_ab_control", "_s146_ab_sin_test1"):
        recs = [r for r in json.load(open(D / brazo / (vol + ".json"), encoding="utf-8"))["records"]
                if r["datetime_utc"][:16] == dt and str(r.get("sensor", "")).startswith("VIIRS") and not str(r.get("sensor")).endswith("_750")]
        for r in recs:
            pc = r.get("primary_cluster") or {}
            print("   %-20s dc=%-7s fuente=%-12s n_anom=%s pc_n=%s pc_vrp=%s pc_dist=%s f5=%s vrp_mw=%s t1=%s k_obs=%s paths(bt,nti,dnti,eti)=%s" % (
                brazo, r.get("distance_class"), r.get("final_hotspot_source"), r.get("n_anomalous_pixels"), pc.get("n_pixels"), pc.get("vrp_mw"),
                pc.get("centroid_dist_km"), r.get("f5_core_vrp_mw"), r.get("vrp_mw"), r.get("triggered_test1"), r.get("test1_k_observed"),
                (r.get("diag_n_bt_path"), r.get("diag_n_nti_path"), r.get("diag_n_dnti_ctx_path"), r.get("diag_n_eti_path"))))
