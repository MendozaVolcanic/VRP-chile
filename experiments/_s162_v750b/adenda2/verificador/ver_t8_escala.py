# -*- coding: utf-8 -*-
"""T8: escala. El lector con ~5.900 pasadas selladas + 20 suplementarias, con cúmulos de 0 a 40 píxeles por caja, para
descartar que se cuelgue o tarde horas con el tamaño del run. Mide el tiempo del lector y la salida. Pregunta 1: si el
lector fuera cuadrático o se colgara, el tiempo lo vería. Pregunta 2: instrumento muerto: se exige rc 0 y controles en verde."""
import random
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ver_comun import Pob, TMP, lector  # noqa: E402

rng = random.Random(7)
d = TMP / "t8"
if d.exists():
    shutil.rmtree(d)
d.mkdir(parents=True)
p = Pob()
vols = ["Lascar", "Villarrica", "Llaima", "Isluga", "Lastarria", "Copahue", "Chaiten", "PuyehueCordonCaulle", "Tupungatito"]


def pix():
    n = rng.choice([0, 0, 0, 1, 1, 2, 5, 15, 40])
    c0, r0 = rng.randint(20, 46), rng.randint(20, 46)
    out = {(r0 + rng.randint(-3, 3), c0 + rng.randint(-3, 3)) for _ in range(n)}
    return [(a, b, round(rng.uniform(0.5, 6.0), 5)) for a, b in sorted(out)]


for n in range(5841):
    lab = "pos" if n % 20 == 0 else "neg_limpio"
    h = f"2026-{4 + (n // 900):02d}-{1 + (n % 28):02d} {(n // 28) % 7:02d}:{(n * 7) % 60:02d}"
    p.pasada(h, lab, pix(), 2.0 if lab == "pos" else 0.0, volcan=vols[n % len(vols)], dist_mirova=1.0 if lab == "pos" else None,
             pub_prod=lab == "pos")
for n in range(20):
    p.pasada(f"2026-0{5 + n % 5}-{1 + n:02d} 05:00", "far_ref", pix(), 3.0, volcan=vols[n % len(vols)], dist_mirova=13.0)
p.escribir(d)
t = time.time()
rc, out = lector(d)
print(f"lector sobre {len(p.sell)} + {len(p.supl)} pasadas: rc={rc}, {time.time() - t:.0f} s, traceback={'Traceback' in out}")
print([l for l in out.splitlines() if l.startswith("== C") or "controles" in l][:6])
