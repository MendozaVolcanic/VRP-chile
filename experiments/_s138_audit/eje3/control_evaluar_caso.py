"""S138 eje 3 - control de evaluar_caso (instrumento 2) con pasadas sinteticas.

Se importa la funcion REAL desde experiments/_s136/conformidad_apendice.py (no se retipa).
Pregunta 1: un cumulo a 4 km y otro a 6 km del centro cambian el veredicto con INNER_KM = 5?
Pregunta 2: un cumulo con VRP 0,0 dentro del inner cuenta como 'publica'? (que ve el operador: no)
Pregunta 3: el control de validez por NTI del paper detiene el caso cuando ninguna pasada cae en banda?
"""
import os, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "experiments" / "_s136"))
import conformidad_apendice as ca

def pasada(vrp, d, nti=-0.93):
    return {"granule": "g", "inicio": "t", "nti_max": nti, "vrp_pc_mw": vrp, "n_pixels_pc": 1,
            "pc_lat": 0, "pc_lon": 0, "dist_crater_km": d, "distance_class": None, "t_bg_k": 270,
            "diag_n_first_pass_pixels": 1, "diag_n_nti_path": 0, "triggered_test1": False}
pos = {"caso": "X", "name": "x", "veredicto": "detecta"}
neg = {"caso": "Y", "name": "y", "veredicto": "no_detecta"}
print("INNER_KM =", ca.INNER_KM, " TOL_NTI =", ca.TOL_NTI)
for etiqueta, caso, pas in [
    ("positivo, cumulo 0,5 MW a 4 km", pos, [pasada(0.5, 4.0)]),
    ("positivo, cumulo 0,5 MW a 6 km", pos, [pasada(0.5, 6.0)]),
    ("positivo, cumulo 0,5 MW a 5,0 km (borde)", pos, [pasada(0.5, 5.0)]),
    ("positivo, cumulo 0,5 MW a 5,001 km", pos, [pasada(0.5, 5.001)]),
    ("negativo, cumulo 0,5 MW a 4 km", neg, [pasada(0.5, 4.0)]),
    ("negativo, cumulo 0,5 MW a 6 km", neg, [pasada(0.5, 6.0)]),
    ("positivo, cumulo VRP 0,0 a 0,8 km (caso A6 B22 sin compuerta)", pos, [pasada(0.0, 0.8)]),
    ("positivo, cumulo None (sin cluster)", pos, [pasada(None, None)]),
    ("positivo, sin pasadas", pos, []),
    ("negativo, sin pasadas", neg, []),
    ("positivo con nti_paper -0,93, pasada con NTI -0,80 (fuera de banda)", {**pos, "nti_paper": -0.93}, [pasada(0.5, 1.0, nti=-0.80)]),
    ("positivo con nti_paper -0,93, dos pasadas: una en banda sin cumulo, otra fuera de banda con cumulo", {**pos, "nti_paper": -0.93}, [pasada(None, None, nti=-0.93), pasada(0.5, 1.0, nti=-0.80)]),
    ("negativo, cumulo 5,0 MW (valor censurado del cap) a 2 km", neg, [pasada(5.0, 2.0)]),
]:
    ver, det = ca.evaluar_caso(caso, pas)
    print(f"  {etiqueta:75s} -> {ver} | {det[:80]}")
# post hoc A2
c = {"caso": "A2", "name": "Eyjafjallajokull", "veredicto": "detecta", "lat": 63.633, "lon": -19.633}
plat, plon = ca.punto_desde(c["lat"], c["lon"], 9.6, 83.0)
print("\npunto del autor A2 segun POSICION_AUTOR:", round(plat, 5), round(plon, 5),
      " dist de vuelta =", round(ca.hav(plat, plon, c["lat"], c["lon"]), 3), "km")
for d_ok in [2.9, 3.1]:
    q = ca.punto_desde(plat, plon, d_ok, 0.0)
    p = pasada(0.5, 9.0); p["pc_lat"], p["pc_lon"] = q
    print(f"  cumulo a {d_ok} km del punto del autor ->", ca.evaluar_posicion_autor(c, [p]))
