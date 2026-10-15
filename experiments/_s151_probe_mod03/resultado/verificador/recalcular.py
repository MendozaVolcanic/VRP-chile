# Recalcula el veredicto del probe S151 MxD03 desde el JSON y separa factores (traza, cruce de scan, terreno).
import json, math, sys
p = sys.argv[1]
d = json.load(open(p, encoding="utf-8"))
F = d["granulos"]
TOL, MIN = 0.3, 1.0
print("veredicto en JSON:", d["veredicto"])
for f in F:
    r = f["obs_barrido_km"] - f["pred_barrido_km"]
    rh = f["obs_hacia_sensor_km"] - f["pred_hacia_sensor_km"]
    i = f["linea"]; c = i * 405 / 2029; n0 = 2 + 5 * math.floor(c); n1 = n0 + 5; fr = c - math.floor(c)
    cruza = (n0 // 10) != (n1 // 10)
    tot = math.hypot(f["obs_barrido_km"], f["obs_traza_km"])
    o2f, o2l = f["offsets_grilla_km"]["frame"]["2"], f["offsets_grilla_km"]["linea"]["2"]
    print(f'{f["granulo"]:24s} cen {f["cenit"]:5.1f} f0 {str(f["volcan_del_lado_del_frame0"]):5s} '
          f'obs {f["obs_barrido_km"]:+.3f} pred {f["pred_barrido_km"]:+.3f} res {r:+.3f} res_hacia {rh:+.3f} '
          f'|total| {tot:.2f} traza obs {f["obs_traza_km"]:+.3f} pred {f["pred_traza_km_offset2"]:+.3f} '
          f'nodos lineas {n0},{n1} frac {fr:.2f} cruza_scan {cruza} off2 f/l {o2f}/{o2l} vent_res {f["ventana_residuo_barrido_mediana_abs_km"]}')
coincide = all(abs(f["obs_barrido_km"] - f["pred_barrido_km"]) <= TOL for f in F)
grandes = [f for f in F if f["volcan_del_lado_del_frame0"] and f["cenit"] >= 30]
hacia = bool(grandes) and all(f["obs_hacia_sensor_km"] >= MIN for f in grandes)
nada = all(math.hypot(f["obs_barrido_km"], f["obs_traza_km"]) < TOL for f in F)
contra = any(abs(f["pred_barrido_km"]) > 1.0 and f["obs_barrido_km"] * f["pred_barrido_km"] < 0 for f in F)
print("cond CONFIRMA 1 (coincide 0,3):", coincide, " cond 2 (>=1 km hacia sensor, f0 y cenit>=30, n=%d):" % len(grandes), hacia)
print("REFUTA 1 (todo <0,3):", nada, " REFUTA 2 (signo contrario):", contra)
v = "REFUTA" if (nada or contra) else ("CONFIRMA" if (coincide and hacia) else "PARCIAL")
print("veredicto recalculado:", v)
for f in F:
    for k in ("pixel_brillante_b22_mxd03_dn_de_km", "pixel_brillante_b22_interp_dn_de_km"):
        n, e = f[k]
        print(f'{f["granulo"]:24s} {k[16:]:22s} N {n:+.2f} E {e:+.2f} dist {math.hypot(n,e):.2f} en_caja_2.5 {abs(n)<=2.5 and abs(e)<=2.5}')
