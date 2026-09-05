# -*- coding: utf-8 -*-
"""S134 F3 - Tabla etapa x pasada: 3 Villarrica (d_pc 2-3 km, f5>0.05) + 3 Lascar (control).

Para cada pasada: pico, centroide geometrico, centroide ponderado por vrp, centroide del record
(pc) y final_hotspot, con su d_crater (vent_lat/lon), mas los conteos por camino y la lista
de pixeles persistidos. Read-only.
"""
import io, json, math, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
res = json.load(io.open(os.path.join(HERE, "resultados.json"), encoding="utf-8"))
DATA = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/data/mirova_equivalent"

def hav(a,b,c,d):
    p=math.pi/180
    x=math.sin((c-a)*p/2)**2+math.cos(a*p)*math.cos(c*p)*math.sin((d-b)*p/2)**2
    return 2*6371*math.asin(math.sqrt(x))

sel = {}
fv = [f for f in res["por_volcan"]["Villarrica"]["filas"] if f["d_pc"] and 2 <= f["d_pc"] <= 3 and (f["f5_core_vrp_mw"] or 0) > 0.05]
fv.sort(key=lambda f: -(f["f5_core_vrp_mw"] or 0))
sel["Villarrica"] = fv[:3]
fl = [f for f in res["por_volcan"]["Lascar"]["filas"] if f["d_pc"] is not None and f["d_pc"] < 0.5 and (f["f5_core_vrp_mw"] or 0) > 0.05 and (f["pc_n"] or 0) > 1]
fl.sort(key=lambda f: -(f["pc_n"] or 0))
sel["Lascar"] = fl[:3]
print("candidatos Villarrica d_pc 2-3 & f5>0.05:", len(fv), " | Lascar d<0.5 & f5>0.05 & pc_n>1:", len(fl))
tabla = []
for vol, fs in sel.items():
    vlat, vlon = res["por_volcan"][vol]["ancla"]
    d = json.load(io.open(os.path.join(DATA, vol + ".json"), encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    idx = {(r.get("datetime_utc"), r.get("sensor")): r for r in recs if isinstance(r, dict)}
    for f in fs:
        r = idx[(f["datetime_utc"], f["sensor"])]
        px = r.get("anomaly_pixels") or []
        row = {"volcan": vol, "pasada_utc": f["datetime_utc"], "sensor": f["sensor"], "source": f["source"],
               "d_peak": f["d_peak"], "d_geo": f["d_geo"], "d_w": f["d_w"], "d_pc": f["d_pc"], "d_final": f["d_final"],
               "pc_n": f["pc_n"], "pc_vrp": f["pc_vrp"], "f5": f["f5_core_vrp_mw"], "vrp_mw": f["vrp_mw"],
               "n_test1": f["n_test1_pixels"], "n_ap": f["n_ap"], "n_fp": f["n_fp"], "n_sp": f["n_sp"], "n_bt": f["n_bt"], "n_dnti": f["n_dnti"],
               "t_bg": f["t_bg_k"], "t_max": f["t_max_k"], "bt_peak": f.get("bt_peak"), "frac_E_075": f["frac_E_075"],
               "single_pixel_mode": f["single_pixel_mode"], "triggered_test1": r.get("triggered_test1"),
               "test1_k_observed": r.get("test1_k_observed"), "nti_max": r.get("nti_max"),
               "pixels": [{"lat": p["lat"], "lon": p["lon"], "bt_k": p["bt_k"], "vrp_mw": p["vrp_mw"],
                           "d_vent": round(hav(p["lat"], p["lon"], vlat, vlon), 3), "dist_km_campo": p["dist_km"]} for p in px]}
        tabla.append(row)
        print("\n%s %s %s src=%s trig_t1=%s k_obs=%s nti_max=%s" % (vol, row["pasada_utc"], row["sensor"], row["source"], row["triggered_test1"], row["test1_k_observed"], row["nti_max"]))
        print("  d_crater [km]: pico=%s  geo=%s  pond=%s  pc=%s  final=%s   | pc_n=%s pc_vrp=%s f5=%s vrp_mw=%s spm=%s" % (
            row["d_peak"], row["d_geo"], row["d_w"], row["d_pc"], row["d_final"], row["pc_n"], row["pc_vrp"], row["f5"], row["vrp_mw"], row["single_pixel_mode"]))
        print("  caminos: n_test1=%s n_ap=%s n_fp=%s n_sp=%s n_bt=%s n_dnti=%s | t_bg=%s t_max=%s bt_peak=%s fracE<0.75=%s" % (
            row["n_test1"], row["n_ap"], row["n_fp"], row["n_sp"], row["n_bt"], row["n_dnti"], row["t_bg"], row["t_max"], row["bt_peak"], row["frac_E_075"]))
        for p in row["pixels"][:12]:
            print("    px lat=%.5f lon=%.5f bt=%.2f vrp=%.4f d_vent=%.3f (dist_km campo=%s)" % (p["lat"], p["lon"], p["bt_k"], p["vrp_mw"], p["d_vent"], p["dist_km_campo"]))
        if len(row["pixels"]) > 12: print("    ... %d pixeles mas" % (len(row["pixels"]) - 12))
json.dump(tabla, io.open(os.path.join(HERE, "tabla_6_pasadas.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
