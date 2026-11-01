# -*- coding: utf-8 -*-
"""Verificador S164, A1: con el flag apagado, calculate_vrp de MODIS da lo mismo que antes del cambio, SIN redondeo.

El golden del PR (modis_k_antes.json) se compara tras redondear a 9 cifras significativas (arnes_sintetico_s142,
SIGNIFICATIVAS = 9), asi que "bit a bit" alli quiere decir "igual a 9 cifras". Aqui se serializa cada float con repr
(ida y vuelta exacta) y se comparan los textos. Dos arboles: el tag base (extraido con git archive a un directorio
aparte) y el worktree de HEAD. Tres perfiles.

Uso: python a1_bit_a_bit_crudo.py <raiz_del_arbol> <perfil> <salida.json>
     (el driver a1_driver.sh lo corre para los dos arboles y compara sha256)
"""
import json
import os
import sys
from pathlib import Path

import numpy as np

raiz, perfil, salida = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
os.environ["VRP_PROFILE"] = perfil
sys.path.insert(0, str(raiz))
sys.path.insert(0, str(raiz / "tests"))
import arnes_sintetico_s142 as arnes  # noqa: E402


def crudo(o):
    if isinstance(o, dict):
        return {str(k): crudo(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [crudo(v) for v in o]
    if isinstance(o, np.ndarray):
        return crudo(o.tolist())
    if isinstance(o, np.generic):
        return crudo(o.item())
    if isinstance(o, float):
        return repr(o)          # texto exacto del double, NaN incluido
    return o


res = {}
for tipo in ("nevado", "nevado_vecino_tibio", "plana"):
    r = arnes.correr_modis(tipo)
    res[tipo] = crudo(r)
    res[tipo + "__claves"] = sorted(r.keys()) if isinstance(r, dict) else None
import pipeline.profile as p  # noqa: E402
res["__flag_ENABLE_MODIS_CODIGO_MIROVA"] = getattr(p, "ENABLE_MODIS_CODIGO_MIROVA", "NO EXISTE EN ESTE ARBOL")
res["__perfil"] = perfil
res["__raiz"] = str(raiz)
salida.write_text(json.dumps(res, sort_keys=True, indent=1, ensure_ascii=False), encoding="utf-8")
print(perfil, raiz, "flag:", res["__flag_ENABLE_MODIS_CODIGO_MIROVA"], "claves nevado:", len(res["nevado__claves"] or []))
