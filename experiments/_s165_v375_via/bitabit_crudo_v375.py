# -*- coding: utf-8 -*-
"""S165 V375-E: con el flag apagado, calculate_vrp de VIIRS 375 da lo mismo que antes del cambio, SIN redondeo.

POR QUÉ. El golden de pytest (tests/datos_s165_v375/v375_k_antes.json) se compara tras el redondeo a 9 cifras del arnés
S142, así que allí "bit a bit" quiere decir "igual a 9 cifras". Aquí cada float se serializa con repr (ida y vuelta
exacta) y se comparan los textos, como el A1 del verificador de #919. Se corre una vez con el árbol del tag
pre-s165-via-375 (extraído con git archive a un directorio aparte) y otra con el worktree de HEAD, en los tres perfiles,
y se compara el sha256 de las salidas.

Uso: python bitabit_crudo_v375.py <raiz_del_arbol> <perfil> <salida.json> [--control-flag-encendido]
     --control-flag-encendido enciende ENABLE_V375_CODIGO_MIROVA en el procesador (sólo existe en HEAD): la comparación
     contra el tag TIENE que dar distinto (el arnés no está en un volcán con grilla, así que el record de K lleva la
     marca "sin_grilla"). Si diera igual, la comparación no podría fallar (A116).
"""
import json
import os
import sys
from pathlib import Path

import numpy as np

raiz, perfil, salida = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
control = "--control-flag-encendido" in sys.argv[4:]
os.environ["VRP_PROFILE"] = perfil
sys.path.insert(0, str(raiz))
sys.path.insert(0, str(raiz / "tests"))
import arnes_sintetico_s142 as arnes  # noqa: E402
if control:
    import pipeline.process_viirs as _pv  # noqa: E402
    _pv.ENABLE_V375_CODIGO_MIROVA = True


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
for tipo in arnes.ESCENAS_V375:
    for k in (False, True):
        r = arnes.correr_v375(tipo, k, {})
        res[f"{tipo}|kernel={k}"] = crudo(r)
        res[f"{tipo}|kernel={k}__claves"] = sorted(r.keys()) if isinstance(r, dict) else None
import pipeline.profile as p  # noqa: E402
import pipeline.process_viirs as pv  # noqa: E402
assert Path(pv.__file__).resolve().is_relative_to(raiz.resolve()), (pv.__file__, raiz)   # el árbol que se dice
res["__flag_ENABLE_V375_CODIGO_MIROVA"] = getattr(p, "ENABLE_V375_CODIGO_MIROVA", "NO EXISTE EN ESTE ARBOL")
res["__perfil"] = perfil
salida.write_text(json.dumps(res, sort_keys=True, indent=1, ensure_ascii=False), encoding="utf-8")
print(perfil, raiz, "flag:", res["__flag_ENABLE_V375_CODIGO_MIROVA"],
      "control:", control, "vrp_mir_mw foco_3x3:", res["foco_3x3|kernel=False"].get("vrp_mir_mw"))
