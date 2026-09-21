# -*- coding: utf-8 -*-
"""V5: recall V375 por zona del barrido y por fondo frio, en los dos brazos."""
import sys
from verif_base import B, F, cargar_brazo, cargar_ref, etiquetar, zona
D, CONG, FIN = sys.argv[1], sys.argv[2], sys.argv[3]
rb, _ = cargar_brazo(D + "/" + B); rf, _ = cargar_brazo(D + "/" + F)
lab, _ = etiquetar(rb, cargar_ref(CONG), "2026-09-01", FIN)
pos = [k for k in lab if k[1] == "VIIRS375" and lab[k] == "pos"]
for z in ("nadir", "medio", "borde"):
    s = [k for k in pos if zona(rb[k]["sensor_zenith_deg"]) == z]
    fr = [k for k in s if rb[k]["t_bg_k"] < 260]
    print(z, "n", len(s), "B", sum(rb[k]["_pub"] for k in s), "F", sum(rf[k]["_pub"] for k in s),
          "| con fondo bajo 260 K: n", len(fr), "B", sum(rb[k]["_pub"] for k in fr), "F", sum(rf[k]["_pub"] for k in fr))
