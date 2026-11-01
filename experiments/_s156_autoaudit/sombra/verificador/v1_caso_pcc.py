# Verificador S156: inspecciona los records de produccion y sombra de PCC 2026-10-10 alrededor de 05:54
import json, sys
from pathlib import Path
W = Path(sys.argv[1])
for sub in ("mirova_equivalent", "experimental_v2"):
    d = json.load(open(W/"data"/sub/"PuyehueCordonCaulle.json", encoding="utf-8"))
    print("=====", sub, "n_records", len(d["records"]))
    for r in d["records"]:
        if r.get("datetime_utc","").startswith("2026-10-10 0") and r["datetime_utc"][11:13] in ("04","05","06"):
            pc = r.get("primary_cluster") or {}
            print(r["datetime_utc"], r.get("sensor"), "dc=",r.get("distance_class"), "vrp=",r.get("vrp_mw"),
                  "pc_vrp=",pc.get("vrp_mw"), "pc_dist=",pc.get("centroid_dist_km"), "pc_n=",pc.get("n_pixels"),
                  "n_anom=",r.get("n_anomalous_pixels"), "npix=",len(r.get("anomaly_pixels") or []),
                  "f5=",r.get("f5_core_vrp_mw"), "t1=",r.get("triggered_test1"), "disc=",r.get("discarded_reason"),
                  "sha=",(r.get("regimen") or {}).get("codigo_sha"), "perfil=",(r.get("regimen") or {}).get("perfil"),
                  "granule=", r.get("granule_id") or r.get("granule"), "z=", r.get("sensor_zenith_deg"))
