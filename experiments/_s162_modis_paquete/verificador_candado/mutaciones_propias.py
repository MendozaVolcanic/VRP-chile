# -*- coding: utf-8 -*-
"""Verificador del candado MOD-D: mutaciones que la lista de mutar_evaluar_paquete.py no trae, probadas sobre una
COPIA de evaluar_paquete.py (nunca sobre el original), con la misma batería probar_evaluar_paquete.py y el mismo
criterio S156 (atrapada sólo si alguna prueba FALLA por aserción; una caída no cuenta).

Cada mutación rompe UNA regla sellada o una elección de la adenda 3:
  bloque_por_pasada         P2 suma por pasada y no por bloque noche-volcán (§4, D-45)
  chillan_p_flojo           regla 3 de Chillán acepta p <= 0,10 en vez de p <= 0,05 (§5.3)
  p1_sin_mirar_k            P1 cuenta protegidas que K tampoco publica (§4: «protegidas que K publica y el brazo no»)
  error_bajo1_al_reves      una alerta bajo 1 MW PUBLICADA cuenta como error (§4 P2: el error es no publicarla)
  grilla_incompleta_cuenta  la grilla con más de la mitad vacía queda en el denominador (adenda 3.6)
  chillan_regla4_sin_bajo   ES DEL SENSOR sin exigir que los pares de cenit <= 30 estén en [0,8; 1,25] (§5.4)
  soporte_mismo_modis       el mismo satélite MODIS cuenta como soporte independiente (adenda 1, A109)
  p1b_contraria_decide      control positivo del corredor: la dirección contraria de P1b decide (§4 P1b); t07 la atrapa
Uso: python -I mutaciones_propias.py [nombre ...]
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent          # verificador_candado/
CANDADO = AQUI.parent                           # _s162_modis_paquete/
RAIZ = CANDADO.parents[1]
FUENTE = CANDADO / "evaluar_paquete.py"

MUTACIONES = {
    "bloque_por_pasada": ('    return "%s|%s" % (f["vol"], f.get("noche") or f["dt"][:10])',
                          '    return "%s|%s" % (f["vol"], f["dt"])'),
    "chillan_p_flojo": ("elif med is not None and 0.8 <= med <= 1.25 and 20 * num <= den:",
                        "elif med is not None and 0.8 <= med <= 1.25 and 10 * num <= den:"),
    "p1_sin_mirar_k": ('if f["lab"] == "protegida" and _pub(f, "K") == 1 and _pub(f, b) == 0]',
                       'if f["lab"] == "protegida" and _pub(f, b) == 0]'),
    "error_bajo1_al_reves": ('    if f["lab"] == "bajo1":\n        return _pub(f, b) == 0',
                             '    if f["lab"] == "bajo1":\n        return _pub(f, b) == 1'),
    "grilla_incompleta_cuenta": ('or f.get("port_grilla") == "grilla_incompleta":',
                                 'or f.get("port_grilla") == "grilla_x":'),
    "chillan_regla4_sin_bajo": (
        "    elif med_bajo is not None and med_sobre is not None and med_sobre < 0.8 and 0.8 <= med_bajo <= 1.25:",
        "    elif med_sobre is not None and med_sobre < 0.8:"),
    "soporte_mismo_modis": ('and abs(r["dt"] - t) <= w and (r["b"] != "MODIS" or r.get("sensor") != f["sensor"])]',
                            'and abs(r["dt"] - t) <= w]'),
    "p1b_contraria_decide": ('        elif _mag(f, "K") < 1.0 <= _mag(f, b):\n            sube.append(fila)',
                             '        elif _mag(f, "K") < 1.0 <= _mag(f, b):\n            baja.append(fila)'),
}


def correr(modulo, salida_json, bateria):
    env = dict(os.environ, MODD_RAIZ=str(RAIZ), PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, "-I", str(bateria), "--modulo", str(modulo), "--json", str(salida_json)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    res = json.loads(Path(salida_json).read_text(encoding="utf-8")) if Path(salida_json).exists() else None
    return res, p.stdout[-800:] + p.stderr[-800:]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    bateria = CANDADO / "probar_evaluar_paquete.py"
    if args and args[0] == "--bateria":
        bateria = Path(args[1]).resolve()
        args = args[2:]
    solo = set(args)
    src = FUENTE.read_text(encoding="utf-8")
    tabla = {}
    with tempfile.TemporaryDirectory(dir=AQUI) as td:
        td = Path(td)
        for nombre, (viejo, nuevo) in MUTACIONES.items():
            if solo and nombre not in solo:
                continue
            if src.count(viejo) != 1:
                tabla[nombre] = "SUSTITUCION INVALIDA (el texto aparece %d veces)" % src.count(viejo)
                continue
            mut = td / ("mut_%s" % nombre)
            mut.mkdir()
            for a in ("evaluar_d25_ded217af4.py", "grillas.json"):
                shutil.copy2(CANDADO / a, mut / a)
            (mut / "evaluar_paquete.py").write_text(src.replace(viejo, nuevo), encoding="utf-8")
            r, log = correr(mut / "evaluar_paquete.py", mut / "r.json", bateria)
            if r is None:
                tabla[nombre] = "CAE (sin resultado): " + log[-300:]
                continue
            fallan = [k for k, v in r.items() if v == "falla"]
            caen = [k for k, v in r.items() if v == "cae"]
            if fallan:
                tabla[nombre] = "ATRAPADA por %s" % ", ".join(fallan[:4]) + (" (ademas caen %s)" % caen if caen else "")
            elif caen:
                tabla[nombre] = "CAE (%s)" % ", ".join(caen[:3])
            else:
                tabla[nombre] = "VIVA"
            print("  %-26s %s" % (nombre, tabla[nombre]), flush=True)
    print("bateria usada:", bateria.name)
    print("vivas: %d de %d probadas" % (sum(1 for v in tabla.values() if v == "VIVA"), len(tabla)))


if __name__ == "__main__":
    main()
