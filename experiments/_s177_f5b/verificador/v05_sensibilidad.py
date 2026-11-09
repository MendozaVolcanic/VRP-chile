# -*- coding: utf-8 -*-
"""V177 v05. Pregunta: la prueba de sensibilidad de s04 B simula un foco desplazado o desplaza algo que se detecta solo?

Fenomeno que deberia simular: MIROVA marca un foco en otro lugar; en la lamina la mancha se dibuja en otro lugar.
Lo que hace s04 B: suma un vector al punto NUESTRO, deja la mancha y su control intactos, y recalcula d <= tol. Es aritmetica de una distancia.
Pre-registro:
 A. Reproducir la curva de s04 B (control any, centroide).
 B. Lamina muerta: reemplazo el centroide de cada pasada por la mediana de los centroides (la lamina no aporta nada de la pasada). Si la curva queda parecida, s04 B no distingue instrumento vivo de muerto (pregunta 2 de la guia).
 C. Inyeccion de verdad en la imagen: traslado los pixeles de la mancha (C2) k km en 8 direcciones dentro del panel, relleno el hueco con el anillo, y corro el selector completo (sin dato, inner, empates, centroide) y la clase. Control any con Dist sin mover y sin control.
 D. Foco desplazado dentro de la mancha: cuanto se mueve el centroide si el pixel de MIROVA es cualquier celda de la mancha: por construccion 0. Se reporta solo la fraccion de pasadas en que la celda mas lejana queda a mas de 1 km (ya en v03 F).
"""
import os, sys, pickle
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from comun import *
from scipy import ndimage as ni

R = pickle.load(open(os.path.join(HERE, "v01_manchas.pkl"), "rb"))
KS = (0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0)
AN = range(0, 360, 45)
for nom, b in (("Chillan VIIRS 375", "VIIRS375"), ("Chillan VIIRS 750", "VIIRS750")):
    s = [o for o in R if o["vol"] == CH and o["b"] == b]
    g = grilla(CH, b)
    tol = TOL[b]
    ok = [o for o in s if clase(o["C2"], o["pt"], o["dist"], b, o["celda"], g, "any") != "iv"]
    print(f"\n== {nom}, {len(ok)} pasadas con control ok, tolerancia {tol}")
    print("k km                     " + " ".join(f"{k:6.2f}" for k in KS))
    medla, medlo = np.median([o["C2"]["la"] for o in ok]), np.median([o["C2"]["lo"] for o in ok])
    def desplazado(o, k, ang):
        return (o["pt"][0] + k * np.cos(np.radians(ang)) / 110.57, o["pt"][1] + k * np.sin(np.radians(ang)) / (111.32 * np.cos(np.radians(o["pt"][0]))))
    fila = [np.mean([hav(o["C2"]["la"], o["C2"]["lo"], *desplazado(o, k, a)) <= tol for o in ok for a in AN]) for k in KS]
    print("A. s04 B (mi calculo)     " + " ".join(f"{x:6.2f}" for x in fila))
    fila = [np.mean([hav(medla, medlo, *desplazado(o, k, a)) <= tol for o in ok for a in AN]) for k in KS]
    print("B. lamina muerta          " + " ".join(f"{x:6.2f}" for x in fila))
    # C inyeccion
    res_nc, res_any, res_iv = {k: [] for k in KS}, {k: [] for k in KS}, {k: [] for k in KS}
    latc, lonc = np.median(g["lats"]), np.median(g["lons"])
    n2 = g["n"] // 2
    km_fila = abs(g["lats"][n2 + 1, n2] - g["lats"][n2, n2]) * 110.57
    km_col = abs(g["lons"][n2, n2 + 1] - g["lons"][n2, n2]) * 111.32 * np.cos(np.radians(latc))
    for o in ok:
        P = panel(o["x"], g)
        s2 = mancha(P, g, "B", True)
        mk = np.zeros(P["L"].shape, bool)
        for c in s2["comps"]:
            mk |= c["mask"]
        # incluir en el traslado el halo inmediato: pixeles de 1 px alrededor
        halo = ni.binary_dilation(mk, structure=np.ones((3, 3), bool)) & ~mk
        anillo = ni.binary_dilation(mk, structure=np.ones((3, 3), bool), iterations=3) & ~ni.binary_dilation(mk, structure=np.ones((3, 3), bool))
        fondo = np.median(P["a"][anillo], axis=0)
        px_cel_x, px_cel_y = P["W"] / P["n"], P["H"] / P["n"]
        for k in KS:
            for a in AN:
                dy_km = k * np.cos(np.radians(a))   # norte: hacia filas menores
                dx_km = k * np.sin(np.radians(a))
                dy = int(round(-dy_km / km_fila * px_cel_y))
                dx = int(round(dx_km / km_col * px_cel_x))
                A2 = P["a"].copy()
                A2[mk] = fondo
                # pega manchas trasladadas (clip al panel)
                ys, xs = np.where(mk)
                y2, x2 = ys + dy, xs + dx
                ok_ = (y2 >= 0) & (y2 < A2.shape[0]) & (x2 >= 0) & (x2 < A2.shape[1])
                A2[y2[ok_], x2[ok_]] = P["a"][ys[ok_], xs[ok_]]
                Q = dict(P)
                Q["a"] = A2
                Q["L"] = A2.astype(float).mean(axis=2)
                t = mancha(Q, g, "B", True)
                if t is None:
                    res_nc[k].append(False); res_any[k].append(False); res_iv[k].append(False); continue
                r = resumen(t, g)
                res_nc[k].append(clase(r, o["pt"], o["dist"], b, o["celda"], g, "any", True) == "i")
                c_ = clase(r, o["pt"], o["dist"], b, o["celda"], g, "any")
                res_any[k].append(c_ == "i")
                res_iv[k].append(c_ == "iv")
    print("C. inyeccion sin control  " + " ".join(f"{np.mean(res_nc[k]):6.2f}" for k in KS))
    print("C. inyeccion control any  " + " ".join(f"{np.mean(res_any[k]):6.2f}" for k in KS))
    print("   fraccion que cae a iv  " + " ".join(f"{np.mean(res_iv[k]):6.2f}" for k in KS))
