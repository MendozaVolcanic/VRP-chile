"""S148 - demostracion sintetica: la caja actua en el primer pase y el segundo pase la deshace.

FENOMENO. Un pixel apenas tibio en la corona (a 3,5 km del crater: fuera de la caja de 5 x 5 km,
dentro del circulo inner de 5 km), con exceso de 0,006 en dNTI y dETI: sobre el piso permisivo
(0,003) y bajo el estricto (0,010).

QUE HACE. Llama a las funciones REALES del pipeline (no las reimplementa) con los mismos
argumentos que arma pipeline/process_viirs.py: el primer pase recibe roi1_mask; el segundo pase
recibe is_summit = dist <= inner_km, que es lo que el procesador le pasa hoy (process_viirs.py,
linea `is_summit_mask = vent_dist_per_pixel <= inner_radius_km`). El cuarto caso, contrafactual,
le pasa la caja al segundo pase para mostrar que ese es el unico punto donde se pierde.

Solo lee el pipeline. Uso: python experiments/_s148_caja_traza/demo_sintetica_segundo_pase.py
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline.detection_context import first_pass_tests_2_and_3, second_pass_adjacent  # noqa: E402

rng = np.random.default_rng(148)
N, PX = 161, 0.375
yy, xx = np.mgrid[0:N, 0:N]
c = N // 2
dx, dy = (xx - c) * PX, (yy - c) * PX
dist = np.hypot(dx, dy)
INNER = 5.0
caja = (np.abs(dx) <= 2.5) & (np.abs(dy) <= 2.5)
roi = (np.abs(dx) <= 25) & (np.abs(dy) <= 25)

nti_app = -0.95 + rng.normal(0, 0.002, (N, N))
nti = nti_app + rng.normal(0, 0.0004, (N, N))
bt = 270.0 + rng.normal(0, 0.3, (N, N))
r0, c0 = c, c + int(round(3.5 / PX))   # 3,5 km al este: fuera de la caja, dentro del circulo
nti[r0, c0] += 0.006
bt[r0, c0] = 275.0                      # pasa la compuerta de 3 K del primer pase
print(f"pixel de prueba: dist {dist[r0, c0]:.2f} km | en caja {bool(caja[r0, c0])} | en circulo {dist[r0, c0] <= INNER}")

KW = dict(c1_dnti_summit=0.003, c1_deti_summit=0.003, c2_dnti_summit=5, c2_deti_summit=5,
          inner_km=INNER, c1_dnti_scene=0.010, c1_deti_scene=0.010, c2_dnti_scene=10, c2_deti_scene=10,
          unsuitable_dnti_floor=-np.inf, unsuitable_deti_floor=-np.inf)


def corre(nombre, roi1_primer, is_summit_segundo):
    fp, diag = first_pass_tests_2_and_3(nti=nti, nti_app=nti_app, bt=bt, roi_mask=roi, dist_km=dist,
                                        t_bg=270.0, bt_sanity_k=3.0, roi1_mask=roi1_primer, **KW)
    fin = second_pass_adjacent(nti=nti, eti=diag["eti"], active_mask=fp,
                               c1_dnti=0.003, c1_deti=0.003, c2_dnti=5, c2_deti=5,
                               is_summit=is_summit_segundo,
                               c1_dnti_scene=0.010, c1_deti_scene=0.010, c2_dnti_scene=10, c2_deti_scene=10)
    print(f"{nombre:58} mu+10sd dNTI={diag['mu_dnti'] + 10 * diag['sd_dnti']:.4f} | "
          f"1er pase: {bool(fp[r0, c0])} | final: {bool(fin[r0, c0])} | "
          f"n 1er pase {int(fp.sum())} | recaptura {int((fin & ~fp).sum())}")


circulo = dist <= INNER
corre("B  control: circulo en los dos pases", None, circulo)
corre("G  como esta cableado: caja en el 1ro, circulo en el 2do", caja, circulo)
corre("G' contrafactual: caja en los dos pases", caja, caja)
