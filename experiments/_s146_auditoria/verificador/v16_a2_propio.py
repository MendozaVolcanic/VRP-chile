# -*- coding: utf-8 -*-
"""V-16 camino propio: lee los resultado_apendice.json crudos (sin importar el evaluador del agente) y mide
   (a) barrido de radio, (b) separacion contra DOS anclas (GVP y mascara medida por v16_figA2.py),
   (c) nulo fino: caja a 9,53 km girada cada 30 grados, (d) que pasa en A2 con todos los brazos con posicion.
(1) Si lo medido estuviera roto, fallaria? Control: radio 0.01 -> 0 aciertos; radio 50 -> todas las pasadas con magnitud.
(2) Instrumento muerto? imprime n de pasadas con magnitud y con posicion por brazo; si 0, se ve."""
import json, math, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
EXP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
BR = {"prod B21min": "_s136/out_apendice", "B22sinBT min": "_s137/out_apendice_b22_sincompuerta",
      "B22sinBT max": "_s137/out_apendice_b22_sincompuerta_prosa", "B22sinBTloc min": "_s137/out_apendice_b22_sincompuerta_fondolocal",
      "B22sinBTloc max": "_s137/out_apendice_b22_sincompuerta_fondolocal_prosa"}
def gc(a, b, c, d):
    R = 6371.0088; r = math.radians
    h = math.sin(r(c-a)/2)**2 + math.cos(r(a))*math.cos(r(c))*math.sin(r(d-b)/2)**2
    return 2*R*math.asin(math.sqrt(h))
def dest(lat, lon, km, az):
    R = 6371.0088; dd = km/R; z = math.radians(az); la = math.radians(lat); lo = math.radians(lon)
    la2 = math.asin(math.sin(la)*math.cos(dd)+math.cos(la)*math.sin(dd)*math.cos(z))
    lo2 = lo+math.atan2(math.sin(z)*math.sin(dd)*math.cos(la), math.cos(dd)-math.sin(la)*math.sin(la2))
    return math.degrees(la2), math.degrees(lo2)
CUMBRE = (63.633, -19.633); GVP = (63+38.1/60, -(19+26.4/60))
MASK = dest(*CUMBRE, 9.65, 83.4)   # medido en v16_figA2.py, suponiendo centro de grilla = cumbre catalogo
print("sep GVP-mascara medida km", round(gc(*GVP, *MASK), 2))
for nom, ruta in BR.items():
    J = json.load(open(os.path.join(EXP, ruta, "resultado_apendice.json"), encoding="utf-8"))
    a2 = [c for c in J if c["caso"] == "A2"][0]
    mag = [p for p in a2["pasadas"] if (p.get("vrp_pc_mw") or 0) > 0]
    pos = [p for p in mag if p.get("pc_lat") is not None]
    print(f"\n{nom}: pasadas {len(a2['pasadas'])} con magnitud {len(mag)} con posicion {len(pos)}")
    for p in pos:
        print("  ", p["inicio"][11:16], "vrp", round(p["vrp_pc_mw"], 2), "d_cumbre", round(gc(*CUMBRE, p["pc_lat"], p["pc_lon"]), 2),
              "sep_GVP", round(gc(*GVP, p["pc_lat"], p["pc_lon"]), 2), "sep_mascara", round(gc(*MASK, p["pc_lat"], p["pc_lon"]), 2))
    if not pos: continue
    print("   barrido radio (n pasadas dentro, ancla GVP):", {r: sum(gc(*GVP, p["pc_lat"], p["pc_lon"]) <= r for p in pos) for r in (0.01, 1, 2, 3, 4, 5, 7, 10, 50)})
    print("   nulo fino, caja 5 km a 9.53 km, rumbo->n dentro:", {az: sum(gc(*dest(*CUMBRE, 9.53, az), p["pc_lat"], p["pc_lon"]) <= 5 for p in pos) for az in range(0, 360, 30)})
    # otros 8 casos: cuantas pasadas con magnitud y posicion caen >5 km de SU cumbre (sustrato del nulo N2)
    lej = [(c["caso"], p["inicio"][11:16], round(p["dist_crater_km"], 2)) for c in J if c["caso"] != "A2" for p in c["pasadas"]
           if (p.get("vrp_pc_mw") or 0) > 0 and (p.get("dist_crater_km") or 0) > 4.53]
    print("   sustrato N2 (otros 8, primario a >4.53 km):", lej)
