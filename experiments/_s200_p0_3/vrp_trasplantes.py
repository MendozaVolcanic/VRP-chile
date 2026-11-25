"""VRP que la vía mide (vrp_mirova sobre la máscara de detectar_mirova) para cada brazo con anomalía, sin foco."""
import numpy as np
import comun as C
import medir as M
import medir_posthoc as P
C.utf8()
MV = C.MV
par = M.parche_fuente(); parp = P.parche_positivo()
print("| escena | brazo | celdas alertadas | VRP medido (MW) |")
print("|---|---|---|---|")
for esc in C.escenas():
    E = C.Escena(esc)
    crat = (int(round(E.pos[0])), int(round(E.pos[1])))
    br = {"tal cual": (E.m13g, E.m15g)}
    if esc["clave"] != M.CLAVE_FUENTE:
        for s in (1, 3, 10):
            br[f"T-con-{s}"] = M.aplicar_parche(E.m13g, E.m15g, par, crat, s)
        for s in (1, 3, 10, 30):
            br[f"T+-con-{s}"] = M.aplicar_parche(E.m13g, E.m15g, parp, crat, s)
    for nb, (a, b) in br.items():
        m, _ = E.detectar(a, b)
        v = MV.vrp_mirova(a, m)
        print(f"| {esc['clave']} | {nb} | {int(m.sum())} | {(v['VRP_MW'] if v['npix'] else 0):.2f} |")
