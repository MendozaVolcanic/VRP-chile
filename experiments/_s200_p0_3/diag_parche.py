"""Diagnóstico post hoc del parche de Chillán: cuánto del exceso es negativo (cumbre fría) y qué BT queda al escalarlo."""
import numpy as np
import comun as C
import medir as M
C.utf8()
MV = C.MV
par = M.parche_fuente()
d13 = np.array([v[0] for v in par.values()]); d15 = np.array([v[1] for v in par.values()])
print(f"celdas del parche {len(par)}; exceso M13 positivo en {np.sum(d13 > 0)}, negativo en {np.sum(d13 < 0)}")
print(f"suma M13 positiva {d13[d13 > 0].sum():.4f}, negativa {d13[d13 < 0].sum():.4f} W m-2 sr-1 um-1")
print(f"M13 exceso: min {d13.min():.4f} max {d13.max():.4f}; M15 exceso: min {d15.min():.4f} max {d15.max():.4f}")
for esc in C.escenas():
    if esc["clave"] == M.CLAVE_FUENTE:
        continue
    E = C.Escena(esc)
    crat = (int(round(E.pos[0])), int(round(E.pos[1])))
    for s in (1, 3, 10):
        a, b = M.aplicar_parche(E.m13g, E.m15g, par, crat, s)
        bt13 = MV.radiancia_a_temperatura(a, MV.LAMBDA_M13)
        bt15 = MV.radiancia_a_temperatura(b, MV.LAMBDA_M15)
        dif = a - E.m13g
        print(f"{esc['clave']:38s} x{s:2d}: BT13 máx {np.nanmax(bt13):6.1f} K, BT13 mín en el parche "
              f"{np.nanmin(np.where(dif != 0, bt13, np.nan)):6.1f} K (escena mín {np.nanmin(MV.radiancia_a_temperatura(E.m13g, MV.LAMBDA_M13)):6.1f}), "
              f"celdas M13<=0 {int(np.sum(a <= 0))}, BT15 mín parche {np.nanmin(np.where(dif != 0, bt15, np.nan)):6.1f}")
