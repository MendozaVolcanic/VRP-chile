# Muestra los records MODIS de una fecha en los brazos de las dos corridas. Solo lectura.
import json, sys, math
S = sys.argv[1]; TS = sys.argv[2]
VENT = (-23.37, -67.73)  # sobrescrito abajo con volcanoes.yaml si se pasa
if len(sys.argv) > 4: VENT = (float(sys.argv[3]), float(sys.argv[4]))
def hav(a, b, c, d):
    R = 6371.0; p1, p2 = math.radians(a), math.radians(c); dp = p2 - p1; dl = math.radians(d - b)
    return 2*R*math.asin(math.sqrt(math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2))
for run in ("caja_d1_v3", "caja_d1_rep"):
    for br in ("_s149_ab_sin_test1_b22_max", "_s151_ab_sin_test1_b22_max_caja"):
        d = json.load(open(f"{S}/{run}/todo/{br}/Lascar.json", encoding="utf-8"))
        for r in d["records"]:
            if TS in str(r.get("datetime_utc")) and "MODIS" in str(r.get("sensor")):
                pc = r.get("primary_cluster") or {}
                print("==", run, br[-12:])
                keys = ["datetime_utc","sensor","granule","product_version","vrp_mw","distance_class","final_hotspot_source","final_hotspot_dist_km","n_anomalous_pixels","t_bg_k","t_max_k","diag_n_first_pass_pixels","diag_n_first_pass_summit","diag_n_second_pass_recapture","diag_n_dnti_ctx_path","diag_n_eti_path","diag_n_nti_path","diag_n_bt_path","diag_sd_dnti","diag_sd_deti","diag_mu_dnti","sensor_zenith_deg"]
                print({k: r.get(k) for k in keys})
                print(" pc:", {k: v for k, v in pc.items() if not isinstance(v, list)})
                for p in (r.get("anomaly_pixels") or [])[:8]:
                    lat = p.get("lat"); lon = p.get("lon")
                    dd = hav(VENT[0], VENT[1], lat, lon) if lat is not None else None
                    dN = (lat - VENT[0]) * 111.32 if lat is not None else None
                    dE = (lon - VENT[1]) * 111.32 * math.cos(math.radians(VENT[0])) if lon is not None else None
                    print("  px:", p, "| dist %.2f km, dN %.2f dE %.2f" % (dd, dN, dE) if dd is not None else "")
