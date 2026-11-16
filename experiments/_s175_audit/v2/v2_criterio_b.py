#!/usr/bin/env python
"""V2: F2-205 por otro camino. Llama las funciones del lector del tag (copia byte a byte, sha 903a4315...) con mis entradas.
P1 (si estuviera roto, lo veria): el control es que criterios_sombra SI de NO CUMPLE (b) cuando silencio = ENCIENDE DE MAS o
P2-L = PIERDE, y control_s7 SI cae cuando una clase que decide tiene n>0 y todo sin dato.
P2: se imprimen las entradas de cada llamada."""
import importlib.util, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
T = Path(sys.argv[1]); p = T / "experiments" / "_s168" / "v375e_sombra" / "leer_sombra_v375e.py"
spec = importlib.util.spec_from_file_location("lector", p); L = importlib.util.module_from_spec(spec); spec.loader.exec_module(L)
out = []
def P(s): out.append(s); print(s)
P(f"CLASES_DECIDEN {L.CLASES_DECIDEN} UMBRAL_COBERTURA {L.UMBRAL_COBERTURA}")
for p2k, sil, p2l in (("SIN SUSTRATO", "SIN SUSTRATO (faltan negativos de alguna clase)", "SIN SUSTRATO"),
                      ("SIN SUSTRATO", "ENCIENDE DE MAS", "SIN SUSTRATO"), ("SIN SUSTRATO", "SIN SUSTRATO", "PIERDE"),
                      ("PIERDE", "APAGA", "GANA"), ("GANA", "SIN SUSTRATO", "SIN SUSTRATO")):
    c = L.criterios_sombra([], p2k, sil, p2l, L.CUMPLE, False, L.CUMPLE)
    P(f"criterios_sombra(p2k={p2k!r}, silencio={sil!r}, p2l={p2l!r}) -> b={c['b']} estado={c['estado']}")
c = L.criterios_sombra([], "SIN SUSTRATO", "SIN SUSTRATO", "SIN SUSTRATO", L.CUMPLE, False, L.CUMPLE, regimen_ok=False)
P(f"  con regimen_ok=False -> b={c['b']} estado={c['estado']}")
P(f"estado_c_sombra('SIN SUSTRATO') = {L.estado_c_sombra('SIN SUSTRATO', type('LP', (), {'estado_c': staticmethod(lambda v: 'x')}))}")
# S7: clases
pos = {"clase": "pos_prot", "id": 0, "volcan": "X", "hora_utc": "h"}
ok, por = L.control_s7([pos], {0: {}}); P(f"control_s7(1 pos_prot con dato, 0 negativos): ok={ok}")
for cl in L.CLASES_DECIDEN:
    pob = [{"clase": cl, "id": i, "volcan": "X", "hora_utc": "h"} for i in range(10)]
    ok, por = L.control_s7(pob, {}); P(f"control_s7(10 de {cl} todos SIN DATO): ok={ok}   [control positivo: tiene que ser False]")
ok, por = L.control_s7([], {}); P(f"control_s7(poblacion vacia): ok={ok}")
Path(sys.argv[2]).write_text("\n".join(out) + "\n", encoding="utf-8")
