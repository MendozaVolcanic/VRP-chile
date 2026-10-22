"""VB v08: el tope de cordura de store.append_record frente a un record VIIRS 375 de magnitud enorme y temperatura
plausible. Camino: llamo a append_record REAL (no a _apply_sanity_cap suelto), con DATA_DIR apuntado a una carpeta
temporal de esta verificacion (no toca data/).
Casos: (a) VIIRS_SNPP (375) con t_max_i04_k=420 K y pc.vrp_mw=60.000 MW; (b) CONTROL VIIRS_SNPP_750 con t_max_k=420 K,
misma magnitud (debe conservarse con vrp_exceeds_sanity_cap); (c) CONTROL VIIRS_SNPP con t_max_i04_k=600 K (debe anularse).
Pregunta 1: si el tope mirara la temperatura en VIIRS 375, (a) se conservaria como (b). Pregunta 2: si append_record no
corriera el tope, (c) tampoco se anularia (eso seria SIN DATO).
"""
import os, sys, io, json, tempfile
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ["VRP_PROFILE"] = "mirova_equivalent"
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
sys.path.insert(0, REPO)
from pipeline import store
tmp = Path(tempfile.mkdtemp(prefix="vb_v08_"))
store.DATA_DIR = tmp
def rec(sensor, tkey, t, minuto):
    return {"datetime_utc": f"2026-10-15T05:{minuto:02d}:00Z", "sensor": sensor, "granule": "x", "vrp_mw": 60000.0,
            tkey: t, "t_bg_k": 270.0, "n_anomalous_pixels": 5, "distance_class": "summit",
            "final_hotspot_dist_km": 0.5, "final_hotspot_lat": -36.86, "final_hotspot_lon": -71.38,
            "primary_cluster": {"n_pixels": 5, "vrp_mw": 60000.0, "centroid_lat": -36.86, "centroid_lon": -71.38,
                                "centroid_dist_km": 0.5}}
for nombre, r in (("(a) V375 t_max_i04_k=420", rec("VIIRS_SNPP", "t_max_i04_k", 420.0, 10)),
                  ("(b) CONTROL V750 t_max_k=420", rec("VIIRS_SNPP_750", "t_max_k", 420.0, 20)),
                  ("(c) CONTROL V375 t_max_i04_k=600", rec("VIIRS_SNPP", "t_max_i04_k", 600.0, 30))):
    try:
        store.append_record("Prueba", r, volcano_lat=-36.86, volcano_lon=-71.38, inner_radius_km=5)
    except Exception as e:
        print(nombre, "EXCEPCION", type(e).__name__, e); continue
    out = json.load(open(tmp / "Prueba.json"))["records"]
    o = [x for x in out if x["datetime_utc"] == r["datetime_utc"] and x["sensor"] == r["sensor"]][0]
    print(f"{nombre}: vrp_mw={o.get('vrp_mw')} pc.vrp_mw={o['primary_cluster'].get('vrp_mw')} t_max_k={o.get('t_max_k')} "
          f"exceeds_flag={o.get('vrp_exceeds_sanity_cap')} rejected={o.get('diag_rejected_sanity_cap_mw')} "
          f"pc_rejected={o.get('diag_pc_rejected_sanity_cap_mw')} discarded={o.get('discarded_reason')}")
print("carpeta temporal:", tmp)
