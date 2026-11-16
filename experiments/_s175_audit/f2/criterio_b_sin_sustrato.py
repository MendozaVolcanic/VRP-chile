#!/usr/bin/env python
"""F2 S175: la regla sellada de la sombra V375-E (leer_sombra_v375e.criterios_sombra, tag s172-v375e-lector-resellado,
fuera de main) con P2 contra K y el silencio en SIN SUSTRATO, que es lo que leer_brazo produce cuando faltan negativos.
Control: la misma llamada con silencio "ENCIENDE DE MAS" tiene que dar NO CUMPLE en (b) (la funcion puede fallar).
Uso: python criterio_b_sin_sustrato.py <arbol_tag> <salida.txt>"""
import importlib.util, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
T = Path(sys.argv[1]); OUT = Path(sys.argv[2])
p = T / "experiments" / "_s168" / "v375e_sombra" / "leer_sombra_v375e.py"
spec = importlib.util.spec_from_file_location("lector", p); L = importlib.util.module_from_spec(spec); spec.loader.exec_module(L)
sin = L.criterios_sombra([], "SIN SUSTRATO", "SIN SUSTRATO (faltan negativos de alguna clase)", "SIN SUSTRATO", L.CUMPLE, False, L.CUMPLE)
ctrl = L.criterios_sombra([], "SIN SUSTRATO", "ENCIENDE DE MAS", "SIN SUSTRATO", L.CUMPLE, False, L.CUMPLE)
s7 = L.control_s7([{"clase": "pos_prot", "id": 0, "volcan": "X", "hora_utc": "h"}], {0: {}})
txt = f"sin negativos: {json.dumps(sin)}\ncontrol ENCIENDE DE MAS: {json.dumps(ctrl)}\nS7 con solo una pos_prot con dato (clases neg con n 0): ok={s7[0]}"
OUT.write_text(txt + "\n", encoding="utf-8"); print(txt)
