"""BT M13 máxima de los píxeles del gránulo en cada recorte (para la limitación del corte de banderas)."""
import numpy as np
import comun as C
C.utf8()
for esc in C.escenas():
    d = C.cargar(esc)
    bt = C.MV.radiancia_a_temperatura(d["m13"], C.MV.LAMBDA_M13)
    print(f"{esc['clave']:40s} BT13 máx píxel {np.nanmax(bt):.1f} K")
