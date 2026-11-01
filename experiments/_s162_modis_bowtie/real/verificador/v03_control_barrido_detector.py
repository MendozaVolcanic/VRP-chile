# -*- coding: utf-8 -*-
"""Verificador B2/B4, camino «el recorte no empieza en una frontera de barrido»: comun.geometria asigna barrido y
detector con `linea // 10` y `linea % 10` sobre el indice de LINEA DEL GRANULO guardado en el npz, no sobre la fila del
recorte. Si usara la fila del recorte, en los recortes que no empiezan en multiplo de 10 (linea[0,0] % 10 != 0) los
detectores quedarian corridos y los metodos A/B quitarian otras filas.
Mide: (a) cuantos recortes empiezan fuera de frontera; (b) control positivo: con `linea` corrida en +1 (la mutacion
`linea_mas_uno` que el envoltorio del lote preve), la mascara de A_centro_cubierto_ant cambia en las pasadas oblicuas
(si no cambiara, la asignacion de barrido no estaria entrando al metodo); (c) que `linea` es consistente con la
geometria: el salto de posicion entre la fila 9 y la fila 0 del barrido siguiente (frontera) es distinto del salto
entre detectores vecinos del mismo barrido en las pasadas oblicuas (hacia el borde, el detector 0 del barrido s+1
RETROCEDE sobre el 9 del barrido s: salto negativo en u), y es ~igual al nadir.
Denominador: 403 pasadas evaluables; (b) y (c) en el estrato z>=50 (156) y z<15 (55).
Uso: python -I v03_control_barrido_detector.py
"""
from __future__ import annotations

import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np  # noqa: E402
import comun as CM  # noqa: E402

AQUI = Path(__file__).resolve().parent


def main():
    pr, L = CM.pr_factory()
    obj, res = CM.objetivos(), CM.resultados()
    ids = [i for i in sorted(obj) if CM.evaluable(res.get(i))]
    offs = collections.Counter()
    cambia, n_obl, iguales_nadir, n_nad = 0, 0, 0, 0
    saltos = collections.defaultdict(list)
    for i in ids:
        o, g = obj[i], obj[i]["grilla"]
        n = CM.cargar_nativo(i)
        offs[int(n["linea"][0, 0]) % 10] += 1
        G = CM.geometria(n, g["epsg"])
        q0 = CM.mascara_quitar(G, "A_centro_cubierto_ant")
        # (c) salto en u entre filas consecutivas, en el frame del crater, separando frontera de barrido e interior
        ci, cj, _ = CM.pixel_crater(G, g)
        du = np.diff(G["u"][:, cj])
        det = G["det"][:-1, cj]
        front = det == 9          # de la fila con detector 9 a la siguiente (detector 0 del barrido s+1)
        e = "z>=50" if o["z"] >= 50 else ("z<15" if o["z"] < 15 else "otro")
        if front.any() and (~front).any():
            saltos[e].append((float(np.median(du[~front])), float(np.median(du[front]))))
        if o["z"] >= 50 or o["z"] < 15:
            n2 = {k: v.copy() for k, v in n.items()}
            n2["linea"] = n2["linea"] + 1
            G2 = CM.geometria(n2, g["epsg"])
            q1 = CM.mascara_quitar(G2, "A_centro_cubierto_ant")
            if o["z"] >= 50:
                n_obl += 1
                cambia += not np.array_equal(q0, q1)
            else:
                n_nad += 1
                iguales_nadir += np.array_equal(q0, q1)
    pr(f"(a) linea[0,0] % 10 de los {len(ids)} recortes evaluables: {dict(sorted(offs.items()))} -> "
       f"{sum(v for k, v in offs.items() if k)} recortes NO empiezan en frontera de barrido; comun.geometria usa la "
       f"linea del granulo, asi que la asignacion no depende de donde empieza el recorte")
    pr(f"(b) control positivo: con linea + 1, la mascara de A_centro_cubierto_ant cambia en {cambia} de {n_obl} pasadas "
       f"z>=50 (tiene que ser ~todas); en el nadir (z<15) queda igual (vacia) en {iguales_nadir} de {n_nad}")
    for e in ("z<15", "z>=50"):
        v = np.array(saltos[e])
        pr(f"(c) {e}: salto en u entre detectores vecinos del mismo barrido, mediana {np.median(v[:, 0]):.0f} m; salto "
           f"del detector 9 al detector 0 del barrido siguiente, mediana {np.median(v[:, 1]):.0f} m (n {len(v)}); "
           f"negativo = el barrido siguiente arranca ATRAS del anterior (bow tie)")
    (AQUI / "v03_control_barrido_detector_salida.txt").write_bytes(("\n".join(L) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
