# -*- coding: utf-8 -*-
"""Verificador B4: ¿«crater en detector 0 o 9» delimita la franja duplicada?, ¿«crater cubierto por 2+ huellas» es el
estrato util? Cruza, desde MI re-corrida de 02 (02_cobertura.json) y de 03 (03_ablacion.json) en esta carpeta:
  - por estrato de cenit: pasadas con crater en det 0/9, con 2+ huellas sobre el crater, y con el pixel del crater
    QUITADO por A_ant (lo que de verdad decide si el crater pierde una copia);
  - tabla 2 x 2 en z>=50: det 0/9 contra "A quita el pixel del crater" y "2+ huellas" contra lo mismo;
  - donde caen los cambios de publicacion y de npix (A_ant, A_sig) segun cada estrato, con la fraccion;
  - cuantos detectores por barrido quita A en z>=50 (si quita hasta el det 3, «0 o 9» no puede delimitar).
Pregunta 1: si det 0/9 delimitara la franja, casi todos los "A quita el crater" caerian en det 0/9. Pregunta 2: el
estrato "2+ huellas" se construye con la misma huella nominal que la cobertura; se contrasta con "A quita el pixel del
crater", que no depende de la huella sino de los centros.
Denominador: 403 pasadas evaluables; estrato z>=50 n 156.
Uso: python -I v05_estratos_crater.py  (despues de rerun_02_cobertura.py y rerun_03_ablacion.py)
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import comun as CM  # noqa: E402

AQUI = Path(__file__).resolve().parent


def main():
    pr, L = CM.pr_factory()
    cob = {int(k): v for k, v in json.loads((AQUI / "02_cobertura.json").read_text("utf-8")).items()}
    ab = {int(k): v for k, v in json.loads((AQUI / "03_ablacion.json").read_text("utf-8")).items()}
    obj = CM.objetivos()
    ids = sorted(cob)
    pr(f"pasadas: {len(ids)} (02) / {len(ab)} (03)")
    orden = ["z<15", "15-25", "25-40", "40-50", "z>=50"]
    pr("\nestrato  n   det0/9  2+huellas  A_ant quita el pixel del crater  A_sig quita el pixel del crater")
    for e in orden:
        g = [i for i in ids if cob[i]["estrato"] == e]
        d09 = sum(cob[i]["det_crater"] in (0, 9) for i in g)
        h2 = sum(cob[i]["huellas_en_crater_todos"] >= 2 for i in g)
        qa = sum(cob[i]["metodos"]["A_centro_cubierto_ant"]["quita_det_crater"] for i in g)
        qs = sum(cob[i]["metodos"]["A_centro_cubierto_sig"]["quita_det_crater"] for i in g)
        pr(f"{e:7s} {len(g):3d}  {d09:4d}    {h2:4d}       {qa:4d}                             {qs:4d}")
    z50 = [i for i in ids if cob[i]["estrato"] == "z>=50"]
    pr("\nz>=50, tabla 2x2: filas = crater en det 0/9; columnas = A_ant o A_sig quita el pixel del crater")
    t = collections.Counter((cob[i]["det_crater"] in (0, 9),
                             cob[i]["metodos"]["A_centro_cubierto_ant"]["quita_det_crater"] or
                             cob[i]["metodos"]["A_centro_cubierto_sig"]["quita_det_crater"]) for i in z50)
    for k in sorted(t):
        pr(f"   det0/9={k[0]!s:5s} quitado={k[1]!s:5s} n {t[k]}")
    pr("z>=50, tabla 2x2: filas = 2+ huellas sobre el crater; columnas = A quita el pixel del crater")
    t = collections.Counter((cob[i]["huellas_en_crater_todos"] >= 2,
                             cob[i]["metodos"]["A_centro_cubierto_ant"]["quita_det_crater"] or
                             cob[i]["metodos"]["A_centro_cubierto_sig"]["quita_det_crater"]) for i in z50)
    for k in sorted(t):
        pr(f"   2+huellas={k[0]!s:5s} quitado={k[1]!s:5s} n {t[k]}")
    pr("\nz>=50: detector del crater cuando A quita el pixel del crater (A_ant | A_sig):")
    for m in ("A_centro_cubierto_ant", "A_centro_cubierto_sig"):
        c = collections.Counter(cob[i]["det_crater"] for i in z50 if cob[i]["metodos"][m]["quita_det_crater"])
        pr(f"   {m}: {dict(sorted(c.items()))}")
    pr("\ncambios de publicacion / de npix contra 'todos' por estrato (A_ant y A_sig), todas las pasadas:")
    for nombre, f in {"det 0/9": lambda i: cob[i]["det_crater"] in (0, 9),
                      "2+ huellas": lambda i: cob[i]["huellas_en_crater_todos"] >= 2,
                      "A quita pixel crater": lambda i: cob[i]["metodos"]["A_centro_cubierto_ant"]["quita_det_crater"]
                      or cob[i]["metodos"]["A_centro_cubierto_sig"]["quita_det_crater"],
                      "z>=50": lambda i: cob[i]["estrato"] == "z>=50"}.items():
        for k in (True, False):
            g = [i for i in ids if f(i) == k]
            fila = []
            for m in ("A_centro_cubierto_ant", "A_centro_cubierto_sig"):
                dp = [i for i in g if ab[i][m]["publica"] != ab[i]["todos"]["publica"]]
                dn = [i for i in g if ab[i][m]["npix"] != ab[i]["todos"]["npix"]]
                dv = [i for i in g if (ab[i][m]["vrp_mw"] or 0) != (ab[i]["todos"]["vrp_mw"] or 0)]
                fila.append(f"{m[-3:]}: pub {len(dp)} {dp} npix {len(dn)} {dn} vrp {len(dv)}")
            pr(f"   {nombre:22s}={k!s:5s} n {len(g):3d} | " + " | ".join(fila))
    (AQUI / "v05_estratos_crater_salida.txt").write_bytes(("\n".join(L) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
