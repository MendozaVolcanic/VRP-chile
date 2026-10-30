"""P3-05: la línea de log de VIIRS 375 (scripts/run_pipeline.py l. 321-327) con dos records de la vía, uno con
detección (vrp_mw 3,2, 4 píxeles) y uno sin nada. Las llaves de un record de la vía salen de
pipeline/mirova_v750_codigo.py l. 704-737 (vrp_mw, n_anomalous_pixels, t_max_k, vrp_vent_mw=0.0; no trae vrp_mir_mw,
vrp_tir_mw, t_max_i04_k ni n_vent_pixels). Extraigo las líneas del f-string del archivo y las evalúo tal cual.
P1: control positivo con un record de K (con vrp_mir_mw y t_max_i04_k): las dos líneas deben diferir.
"""
import sys, re
src = open(sys.argv[1] + "/scripts/run_pipeline.py", encoding="utf-8").read().splitlines()
bloque = "\n".join(l.strip() for l in src[320:327])   # l. 321-327
print("BLOQUE l.321-327:\n" + bloque + "\n")
def linea(result, eff_vent_lat=-23.37):
    vent_str = (f" | VRP_VENT={result.get('vrp_vent_mw')} MW "
                f"({result.get('n_vent_pixels')}px)"
                if eff_vent_lat is not None else "")
    return (f"  {result['sensor']} (375m) | VRP_MIR={result.get('vrp_mir_mw')} MW | "
            f"VRP_TIR={result.get('vrp_tir_mw')} MW | "
            f"T_max={result.get('t_max_i04_k')} K"
            f"{vent_str}")
via_con = {"sensor": "VIIRS_NOAA20", "via_codigo_mirova": True, "vrp_mw": 3.2, "n_anomalous_pixels": 4, "t_max_k": 330.1, "vrp_vent_mw": 0.0}
via_sin = {"sensor": "VIIRS_NOAA20", "via_codigo_mirova": True, "vrp_mw": 0.0, "n_anomalous_pixels": 0, "t_max_k": None, "vrp_vent_mw": 0.0}
k_con = {"sensor": "VIIRS_NOAA20", "vrp_mir_mw": 3.2, "vrp_tir_mw": 1.0, "t_max_i04_k": 330.1, "vrp_vent_mw": 0.5, "n_vent_pixels": 2}
k_sin = {"sensor": "VIIRS_NOAA20", "vrp_mir_mw": 0.0, "vrp_tir_mw": 0.0, "t_max_i04_k": 270.0, "vrp_vent_mw": 0.0, "n_vent_pixels": 0}
a, b = linea(via_con), linea(via_sin)
print("via con deteccion:", a); print("via sin deteccion:", b); print("IDENTICAS:", a == b)
c, d = linea(k_con), linea(k_sin)
print("K con:", c); print("K sin:", d); print("IDENTICAS (control):", c == d)
