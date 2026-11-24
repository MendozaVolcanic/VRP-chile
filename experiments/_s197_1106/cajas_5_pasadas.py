# S197 #1106: la vía de producción (sin tocar) con tres cajas ROI en MODIS, sobre los recortes nativos del probe
# (run 45290835369). def = producción (5 x 5 al centro de la grilla); crater = 5 x 5 movida a la celda del cráter;
# sens = todo el anillo 15 x 15 sensible. Sólo lectura, local, sin red.
import sys, os, json, numpy as np, yaml
sys.path.insert(0, "D:/vrp-trabajo/worktrees/s197-1106-probe")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from pipeline import mirova_v750_codigo as MV
from pipeline.geo_utils import get_detection_anchor
R = "D:/vrp-trabajo/temporales/s197/probe4/s197-1106-0/"
vols = {v["name"]: v for v in yaml.safe_load(open("D:/vrp-trabajo/worktrees/s197-1106-probe/volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
res = json.load(open(R + "p1_resultados_0.json", encoding="utf-8"))["pasadas"]
for p in res:
    v = vols[p["volcan"]]
    alat, alon = get_detection_anchor(v)
    jd = p["granule"].split(".")[1] + "." + p["granule"].split(".")[2]
    f = R + "nativos/%s_%s_%s.npz" % (p["volcan"], jd, p["granule"].split(".")[0])
    z = np.load(f)
    ang = {k: z[k] for k in z.files if k not in ("mir", "tir", "lat", "lon")}
    nombre = MV.volcan_por_coordenadas(v["lat"], v["lon"])
    sensor = "MODIS_TERRA" if p["granule"].startswith("MOD") else "MODIS_AQUA"
    print("==", p["volcan"], p["dt"], "guardado en produccion (probe):", p["brazos"]["prod"]["vrp_mw"], p["brazos"]["prod"]["n"])
    for t in ("def", "crater", "sens"):
        r = MV.calcular_vrp_granulo({"MIR": z["mir"], "TIR": z["tir"]}, z["lat"], z["lon"], ang, nombre, alat, alon,
                                    v.get("inner_radius_km"), sensor, familia="MODIS", tipo_roi=t)
        pc = r.get("primary_cluster") or {}
        cd = ((r.get("diag_codigo_mirova") or {}).get("s1") or {}).get("celda_decisiva")
        cel = [(a["fila"], a["col"]) for a in (r.get("anomaly_pixels") or [])]
        print("   %-6s vrp %s n %s clase %s dist %s celdas %s decisiva %s" % (t, r.get("vrp_mw"), r.get("n_anomalous_pixels"),
              r.get("distance_class"), r.get("final_hotspot_dist_km"), cel, cd))
