"""208: fraccion de records donde el predicado del tope D9 queda activo (n_bt_path==0, n_nti_path==0,
t_bg_k<270) y cuantos cumulos quedan topados (primary_cluster.d9_capped). Tier A, por sensor, dos
ventanas. Control: t_bg<0 debe dar 0; t_bg<400 debe dar ~100 %."""
import json, glob, sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
VOLS = ["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]
def b(s): return "MODIS" if s.startswith("MODIS") else "V750" if s.endswith("_750") else "V375"
c = Counter(); caps = []
for v in VOLS:
    for r in json.load(open(rf"D:\vrp-trabajo\temporales\s160_audit\main\data\mirova_equivalent\{v}.json", encoding="utf-8"))["records"]:
        if r.get("t_bg_k") is None: continue
        dt = r.get("datetime_utc", "")
        for w in ["todo"] + (["desde0918"] if dt >= "2026-09-18" else []):
            k = (w, b(r.get("sensor", "")))
            c[k+("n",)] += 1
            if r["t_bg_k"] < 270: c[k+("tbg<270",)] += 1
            if r["t_bg_k"] < 270 and (r.get("n_bt_path") or 0) == 0 and (r.get("n_nti_path") or 0) == 0: c[k+("predicado",)] += 1
            if r["t_bg_k"] < 0: c[k+("CTRL_neg",)] += 1
            if r["t_bg_k"] < 400: c[k+("CTRL_pos",)] += 1
            if (r.get("n_nti_path") or 0) > 0: c[k+("con_nti_path",)] += 1
            pc = r.get("primary_cluster") or {}
            if pc.get("d9_capped"):
                c[k+("d9_capped",)] += 1
                if w == "desde0918": caps.append((v, dt, r.get("sensor"), r.get("distance_class"), pc.get("centroid_dist_km"), pc.get("vrp_mw")))
out = []
for k in sorted({x[:2] for x in c}):
    n = c[k+("n",)]
    out.append(f"{k} n={n} " + " ".join(f"{m}={c[k+(m,)]}({100*c[k+(m,)]/n:.1f}%)" for m in ["tbg<270","predicado","con_nti_path","d9_capped","CTRL_neg","CTRL_pos"]))
out.append("topados desde 2026-09-18: " + repr(caps))
print("\n".join(out))
open(__file__.replace(".py", "_salida.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
