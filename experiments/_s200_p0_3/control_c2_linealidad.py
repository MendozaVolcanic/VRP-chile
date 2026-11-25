"""C2: el foco por la matriz de interpolación da la misma máscara que insertarlo en el gránulo y llamar a
remuestrear_grilla de producción. 20 casos al azar (semilla 7) con vrp_min, a vrp_min y a 0,95 vrp_min (40 pruebas).
Para brazos cuya base no es la grilla remuestreada tal cual (quitada, trasplante, ruido) se usa
base del brazo + (remuestrear(gránulo con foco) - remuestrear(gránulo)), que prueba lo mismo: la linealidad de la
inserción. Salida: control_c2_salida.txt
"""
import json
import random

import numpy as np

import comun as C
import medir as M

C.utf8()
MV = C.MV
regs = [json.loads(x) for x in open(C.AQUI / "resultados.jsonl", encoding="utf-8")]
cand = [r for r in regs if r.get("vrp_min") is not None and r["T"] == 1000.0]
random.seed(7)
casos = random.sample(cand, 20)
escs = {e["clave"]: e for e in C.escenas()}
n_ok = n_tot = 0
cache = {}
for r in casos:
    if r["escena"] not in cache:
        E = C.Escena(escs[r["escena"]])
        mask, d = E.detectar(E.m13g, E.m15g)
        cache[r["escena"]] = (E, mask, d)
    E, mask, d = cache[r["escena"]]
    b = r["brazo"]
    if b in ("R-con", "T-sin", "N-sin"):
        a13, a15 = E.m13g, E.m15g
    elif b == "R-sin":
        a13, a15, _ = M.quitar_anomalia(E, E.m13g, E.m15g, mask)
    elif b == "R-sin9":
        a13, a15, _ = M.quitar_anomalia(E, E.m13g, E.m15g, mask, k=9)
    elif b == "N-con":
        a13, a15 = M.ruido(E, E.m13g, E.m15g, d["pasada1"]["sd_nti"])
    else:
        crat = (int(round(E.pos[0])), int(round(E.pos[1])))
        a13, a15 = M.aplicar_parche(E.m13g, E.m15g, M.parche_fuente(), crat, int(b.split("-")[-1]))
    origen = M.celda_pico(E, mask) if r["serie"] in ("R", "N") else (int(round(E.pos[0])), int(round(E.pos[1])))
    p = [q for q in M.puntos(E, origen) if q["d"] == r["d"] and q["az"] == r["az"]][0]
    for vrp in (r["vrp_min"], 0.95 * r["vrp_min"]):
        al_mat, f, _ = M.alerta(E, a13, a15, p, vrp, r["T"])
        i = p["i"]
        B13 = float(MV.temperatura_a_radiancia(np.array([r["T"]]), MV.LAMBDA_M13)[0])
        B15 = float(MV.temperatura_a_radiancia(np.array([r["T"]]), MV.LAMBDA_M15)[0])
        m13 = E.d["m13"].copy()
        m15 = E.d["m15"].copy()
        m13[i] = (1 - f) * m13[i] + f * B13
        m15[i] = (1 - f) * m15[i] + f * B15
        g13, g15 = MV.remuestrear_grilla(E.d["lat"], E.d["lon"], m13, m15, E.g)
        full13, full15 = a13 + (g13 - E.m13g), a15 + (g15 - E.m15g)
        mfull, _ = E.detectar(full13, full15)
        al_full = bool(mfull[M.huella(p)].any())
        mat13 = M.grillas_con_foco(E, a13, a15, p, vrp, r["T"])[0]
        dif = float(np.nanmax(np.abs(full13 - mat13)))
        n_tot += 1
        n_ok += al_full == al_mat
        print(f"{r['escena']:38s} {b:9s} d={r['d']:4.0f} az={r['az']:3d} VRP={vrp:8.4f} matriz={al_mat} "
              f"gránulo={al_full} max|dM13|={dif:.1e}")
print(f"C2: {n_ok} de {n_tot} iguales:", "PASA" if n_ok == n_tot == 40 else "NO PASA")
