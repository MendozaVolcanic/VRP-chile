# -*- coding: utf-8 -*-
"""F3 R8. P2 del pre-registro (razon de tasa falsa borde/nadir, la estructura de A114 y de S150 §2) mezcla
satelites, y la tabla de MIROVA lista Suomi NPP sesgado al borde (S149 frente B). ¿La estructura borde > nadir
del control B existe DENTRO de cada satelite, o es composicion?
Sobre las tablas por pasada de r1 (abril a agosto, referencia congelada), negativos limpios de VIIRS 375.
P1: si fuera composicion, dentro de cada satelite la razon seria ~1. P2: control: el agregado sin estratificar
tiene que reproducir el orden de magnitud publicado (control B: borde/nadir 1,9 a 3,6 por mes)."""
import json, sys, collections
from pathlib import Path
tmp = Path(sys.argv[1])
def zona(z): return None if z is None else ("nadir" if z < 36 else ("medio" if z < 52 else "borde"))
for mes in ("abril", "mayo", "junio", "julio", "agosto"):
    T = json.loads((tmp / ("tabla_%s.json" % mes)).read_text(encoding="utf-8"))
    c = collections.defaultdict(lambda: [0, 0, 0, 0])
    for k, v in T["pasadas"].items():
        if k.split("|")[1] != "VIIRS375" or len(v) != 2: continue
        B, F = v["control"], v["brazo"]
        if B["lab"] != "neg_limpio": continue
        zn = zona(B["z"])
        if zn is None: continue
        for p in (str(B["plataforma"]).replace("VIIRS_", ""), "TODOS"):
            x = c[(p, zn)]; x[0] += 1; x[1] += B["pub"]; x[2] += F["pub"]
    linea = []
    for p in ("TODOS", "NOAA20", "NOAA21", "SNPP"):
        n_n, b_n, f_n, _ = c[(p, "nadir")]; n_b, b_b, f_b, _ = c[(p, "borde")]
        if n_n and n_b:
            linea.append("%s nadir %d/%d borde %d/%d razonB %.2f" % (p, b_n, n_n, b_b, n_b, (b_b / n_b) / max(b_n / n_n, 1e-9)))
        else:
            linea.append("%s nadir n%d borde n%d (sin sustrato)" % (p, n_n, n_b))
    print(mes, " | ".join(linea))
