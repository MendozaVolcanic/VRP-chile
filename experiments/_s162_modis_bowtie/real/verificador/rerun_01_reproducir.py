# -*- coding: utf-8 -*-
"""Paso 1, control de que el recorte nativo alcanza: rearmar la grilla del port desde nativo_<id>.npz (MxD03, B22
primaria con B21 donde B22 satura, B31) y correr el port `fisica` sin quitar nada tiene que dar el MISMO npix, el mismo
VRP y los mismos pixeles que el resultado guardado del lote 40120713181 (port.fisica). dayflag y sunglint son los que
el lote guardo para esa pasada.
Pregunta 1 del instrumento: si el recorte no alcanzara (ventana corta, banda equivocada), ¿se veria? Si: el control
negativo de abajo corre lo mismo con la banda B21 primaria y tiene que dar distinto en alguna pasada con deteccion.
Uso: python -I 01_reproducir.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # VERIFICADOR: importa comun.py del auditor; salidas en verificador/
import numpy as np  # noqa: E402
import comun as CM  # noqa: E402


def igual(a, b):
    if a["npix"] != b["npix"]:
        return False
    if (a["vrp_mw"] is None) != (b["vrp_mw"] is None):
        return False
    if a["vrp_mw"] is not None and abs(a["vrp_mw"] - b["vrp_mw"]) > 1e-9:
        return False
    pa = sorted(tuple(p[:2]) for p in a["pixeles"])
    pb = sorted(tuple(p[:2]) for p in b["pixeles"])
    return pa == pb


def main():
    pr, L = CM.pr_factory()
    obj, res = CM.objetivos(), CM.resultados()
    ids = [i for i in sorted(obj) if CM.evaluable(res.get(i))]
    pr("objetivos MODIS (neg_resto + control_s159):", len(obj), "| evaluables:", len(ids),
       "| con nativo:", sum(CM.ruta_nativo(i) is not None for i in ids))
    exactos, distintos, maxdv = 0, [], 0.0
    con_det = []
    for i in ids:
        n = CM.cargar_nativo(i)
        p = CM.correr_port(n, obj[i], res[i])
        ref = res[i]["port"]["fisica"]
        if igual(p, ref):
            exactos += 1
        else:
            distintos.append((i, obj[i]["volcan"], obj[i]["hora_utc"], p["npix"], p["vrp_mw"], ref["npix"],
                              ref["vrp_mw"]))
        if p["vrp_mw"] is not None and ref["vrp_mw"] is not None:
            maxdv = max(maxdv, abs(p["vrp_mw"] - ref["vrp_mw"]))
        if ref["npix"]:
            con_det.append(i)
    pr(f"reproduccion exacta (npix, VRP a 1e-9 MW y mismas celdas): {exactos} de {len(ids)}; max |dVRP| {maxdv:.3e} MW")
    pr("distintos:", distintos)
    pr("pasadas con deteccion del port en el lote:", len(con_det), con_det)

    # control negativo: banda B21 primaria tiene que cambiar algo en las pasadas con deteccion
    cambia = 0
    for i in con_det:
        n = CM.cargar_nativo(i)
        o, r = obj[i], res[i]
        crop = CM.crop_desde_nativo(n)
        crop["mir"] = CM.merge_mir_bands(n["b21"], n["b22"], False)
        g = o["grilla"]
        mir, tir = CM.PP.grillar(crop, g, g["epsg"])
        p = CM.MP.correr(mir, tir, g, g["X0"], g["Y0"], r["dayflag"], r["sunglint"], CM.MP.SENSORES["MODIS"],
                         semillas=0)
        cambia += not igual(p, r["port"]["fisica"])
    pr(f"control negativo (B21 primaria en vez de B22): distinto en {cambia} de {len(con_det)} pasadas con deteccion "
       "(tiene que ser > 0 para que la igualdad de arriba signifique algo)")
    (Path(__file__).with_name("01_reproducir_salida.txt")).write_bytes(("\n".join(L) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
