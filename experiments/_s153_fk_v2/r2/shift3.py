import sys, json, numpy as np
sys.path.insert(0, "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/experiments/_s151_seleccion_mirova")
import comun_tif as ct
import analizar as A
R = ct.leer("C:/Users/nmend/AppData/Local/Temp/claude/r2_fk/tif/data_tif_Lascar_20260602_054201_VIIRS375.tif", "VIIRS375")
r = A.record("V2", A.C0, "Lascar", "VIIRS_NOAA20", "2026-06-02 05:42")
ap = r["anomaly_pixels"] + (r.get("discarded_anomaly_pixels") or [])
print("pixeles nuestros con bt:", len(ap))
dlat, dlon = -23.4433 - (-23.3617), -67.8790 - (-67.7317)
for nombre, (sa, so) in (("sin desplazar", (0, 0)), ("desplazado al foco", (dlat, dlon))):
    q = [dict(p, lat=p["lat"] + sa, lon=p["lon"] + so) for p in ap]
    print(nombre, ct.dbt_mediana(R, q))
    for p in q[:8]:
        rc = ct.celda(R, p["lat"], p["lon"])
        print("   bt nuestro", p.get("bt_k"), "BT TIF", None if rc is None else round(ct.bt_k(float(R["a"][rc]), "VIIRS375"), 1))
