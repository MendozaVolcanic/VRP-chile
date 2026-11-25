"""C1: sin foco, el arnés da lo mismo que calcular_vrp_granulo de producción (origin/main) con el recorte.

calcular_vrp_granulo recibe arreglos 2-D (fila por píxel) y los cuatro ángulos como arreglos constantes con el valor del
píxel más cercano al centro (lo único que producción lee de ellos). Salida: control_c1_salida.txt
"""
import numpy as np

import comun as C

C.utf8()
MV = C.MV
ok_total = True
for esc in C.escenas():
    E = C.Escena(esc)
    d = E.d
    as2 = lambda a: np.asarray(a, float).reshape(1, -1)  # noqa: E731
    ang = {k: np.full((1, d["lat"].size), float(v)) for k, v in esc["geom"].items()}
    rec = MV.calcular_vrp_granulo({"M13": as2(d["m13"]), "M15": as2(d["m15"])}, as2(d["lat"]), as2(d["lon"]), ang,
                                  esc["volcan"], E.vent_lat, E.vent_lon, E.inner_km, "VIIRS_750")
    mask, _ = E.detectar(E.m13g, E.m15g)
    v = MV.vrp_mirova(E.m13g, mask)
    celdas_h = sorted(zip(*[x.tolist() for x in np.nonzero(mask)]))
    celdas_p = sorted((p["fila"], p["col"]) for p in rec["anomaly_pixels"])
    vrp_h = round(float(v["VRP_MW"]), 3) if v["npix"] else 0.0
    igual = celdas_h == celdas_p and vrp_h == rec["vrp_mw"] and rec["diag_codigo_mirova"]["dayflag"] == E.dayflag
    ok_total &= igual
    print(f"{esc['clave']:40s} prod: {len(celdas_p)} celdas {rec['vrp_mw']:.3f} MW roi={rec['diag_codigo_mirova']['roi']} "
          f"| arnés: {len(celdas_h)} celdas {vrp_h:.3f} MW | {'IGUAL' if igual else 'DISTINTO'}")
print("C1", "PASA" if ok_total else "NO PASA")
