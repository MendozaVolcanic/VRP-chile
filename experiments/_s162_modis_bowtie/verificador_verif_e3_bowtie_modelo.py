# -*- coding: utf-8 -*-
"""Verificador CDE, E3: ¿el sintético de ablacion_sintetica.py modela el bow tie y el brazo SIN_DUP quita lo que dice?

Las dos preguntas del instrumento:
1. Si el modelo tuviera huecos de cobertura (suelo que ningún píxel conservado ve) o duplicados que no ven el foco,
   ¿esta medición lo vería? Sí: recorre el eje a lo largo de la traza con paso fino y cuenta cuántas huellas conservadas
   contienen cada punto, por brazo y por ángulo (0 = hueco, 1 = una vez, 2 = duplicado).
2. Si el instrumento estuviera muerto, ¿se vería distinto? Control: en el nadir TODOS y SIN_DUP tienen que dar
   cobertura 1 en el 100 % del eje (sin huecos ni duplicados); y en TODOS a 50° la fracción duplicada tiene que ser
   ~70 % (10 a = 17 km por barrido de 10 km).

Además, con las realizaciones guardadas en ablacion_sintetica_*MW.json (foco_xy, npix y vrp por brazo), clasifica cada
foco por cuántas huellas lo contienen en cada brazo y tabula S/T por clase: así se ve de dónde sale la dispersión
p10-p90 que el informe no comenta.

Misma geometría declarada por el script del auditor (R 6371, H 705, IFOV 1/705, detector d del barrido s centrado en
y = 10 s + (d - 4,5) a, SIN_DUP = |y - 10 s| < 5). Denominador y ventana: sintético, 40 realizaciones por ángulo.
Uso: python -I verif_e3_bowtie_modelo.py --json <ablacion_sintetica_3MW.json> [--json ...]
"""
import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

R, H = 6371.0, 705.0
IFOV = 1.0 / H


def geom(t):
    z = math.asin((R + H) / R * math.sin(t))
    r = (R + H) * math.cos(t) - math.sqrt(R * R - (R + H) ** 2 * math.sin(t) ** 2)
    return r, z, R * (z - t)


def huellas(deg, n_barridos=8):
    """Centros y semianchos a lo largo de la traza de los detectores en el frame central, por brazo."""
    t = math.radians(deg)
    r, z, _ = geom(t)
    a = IFOV * r
    todos, sin_dup = [], []
    for sb in range(-n_barridos // 2, n_barridos // 2):
        for d in range(10):
            y = 10.0 * sb + (d - 4.5) * a
            todos.append(y)
            if abs(y - 10.0 * sb) < 5.0:
                sin_dup.append(y)
    return a, np.array(todos), np.array(sin_dup)


def cobertura(centros, a, ys):
    return np.array([((ys_ > centros - a / 2) & (ys_ <= centros + a / 2)).sum() for ys_ in ys])  # semiabierto: sin empates en los bordes


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", nargs="+", required=True)
    a_ = ap.parse_args()
    ys = np.arange(-20.0, 20.0, 0.01)   # 4 barridos centrales, lejos de los bordes del modelo (8 barridos)
    print("== cobertura a lo largo de la traza (frame central), fracción del eje vista 0 / 1 / 2 veces, por brazo")
    print("angulo  cenit  a_km  dets_conservados | TODOS 0/1/2 | SIN_DUP 0/1/2")
    cob = {}
    for deg in (0.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0):
        a, T, S = huellas(deg)
        cT, cS = cobertura(T, a, ys), cobertura(S, a, ys)
        fr = lambda c: " / ".join(f"{(c == k).mean():.3f}" for k in (0, 1, 2))  # noqa: E731
        z = math.degrees(geom(math.radians(deg))[1])
        nd = len(S) // 8
        cob[deg] = (a, T, S)
        print(f"{deg:6.0f} {z:6.1f} {a:5.3f}  {nd:>2} de 10          | {fr(cT)} | {fr(cS)}"
              + ("   <- HUECO en SIN_DUP" if (cS == 0).mean() > 0 else "")
              + ("   <- duplicados que SIN_DUP conserva" if (cS == 2).mean() > 0 else ""))
    print("control nadir: TODOS y SIN_DUP cobertura 1 en el 100 %:",
          "OK" if (cobertura(cob[0.0][1], cob[0.0][0], ys) == 1).all() and (cobertura(cob[0.0][2], cob[0.0][0], ys) == 1).all()
          else "FALLA")

    for jf in a_.json:
        J = json.loads(Path(jf).read_text(encoding="utf-8"))
        print(f"\n== realizaciones de {Path(jf).name}: S/T por clase de cobertura del foco (cT = huellas de TODOS que lo "
              f"contienen, cS = de SIN_DUP)")
        por = defaultdict(list)
        for f in J["filas"]:
            deg = f["angulo"]
            if deg not in cob:
                cob[deg] = huellas(deg)
            a, T, S = cob[deg]
            y = f["foco_xy"][1]
            cT = int((np.abs(y - T) <= a / 2).sum())
            cS = int((np.abs(y - S) <= a / 2).sum())
            vt, vs = f["TODOS"]["vrp_mw"], f["SIN_DUP"]["vrp_mw"]
            dt, ds = bool(f["TODOS"]["npix"]), bool(f["SIN_DUP"]["npix"])
            por[(deg, cT, cS)].append((vt, vs, dt, ds))
        print("angulo cT cS   n  detecta T/S   S/T mediana [n]   min..max")
        for (deg, cT, cS), L in sorted(por.items()):
            st = [vs / vt for vt, vs, dt, ds in L if dt and ds and vt]
            print(f"{deg:6.0f} {cT:>2} {cS:>2} {len(L):>3}   {sum(d for _, _, d, _ in L):>2}/{sum(d for _, _, _, d in L):<2}"
                  f"   {np.median(st) if st else float('nan'):.3f} [{len(st)}]"
                  f"   {min(st) if st else float('nan'):.2f}..{max(st) if st else float('nan'):.2f}"
                  + ("   <- foco en HUECO de SIN_DUP (nadie lo mide)" if cS == 0 and cT > 0 else "")
                  + ("   <- foco DUPLICADO en TODOS" if cT == 2 else ""))
        # lectura agregada: fracción de realizaciones detectadas con |S/T - 1| > 5 %, por ángulo
        print("fracción de realizaciones (detectadas en los dos brazos) con S/T fuera de [0,95; 1,05], por ángulo:")
        for deg in sorted({k[0] for k in por}):
            st = [vs / vt for k, L in por.items() if k[0] == deg for vt, vs, dt, ds in L if dt and ds and vt]
            if st:
                st = np.array(st)
                print(f"   {deg:4.0f}: {((st < 0.95) | (st > 1.05)).mean():.2f} de {len(st)} (bajo 0,95: "
                      f"{(st < 0.95).mean():.2f}; sobre 1,05: {(st > 1.05).mean():.2f})")


if __name__ == "__main__":
    main()
