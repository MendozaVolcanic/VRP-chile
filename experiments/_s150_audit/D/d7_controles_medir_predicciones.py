# -*- coding: utf-8 -*-
"""S150 auditor D, sonda 7: las dos preguntas del instrumento para medir_predicciones.py (P1, P2, P4, P5, C8b),
con brazos SINTETICOS fabricados sobre una tabla real (la de agosto). Produzco el fenomeno a proposito y
miro si el instrumento lo ve.

Brazos:
  identidad   : el brazo publica exactamente lo mismo que el control. Debe dar P1 igual al control, 0 perdidas,
                C8b FALLA (no hay selectividad), P5 FALLA o sin cambio.
  oraculo     : el brazo publica SOLO donde MIROVA alerto (pos). Debe cumplir todo.
  azar_90     : el brazo apaga al azar el 90 % de lo que publica el control. Es el "apagador" sin ninguna
                selectividad: P1 lo cumple por construccion; las demas deben fallar.
  borde_solo  : el brazo apaga TODO lo publicado con cenit >= 52 (sin mirar etiqueta). Debe cumplir P2 sin
                ser selectivo por etiqueta; C8b deberia fallar o quedar cerca del nulo.
  saca_snpp   : apaga todo Suomi NPP. Sin selectividad por etiqueta.

Uso: python d7_controles_medir_predicciones.py tabla.json
"""
import copy, io, json, random, subprocess, sys, tempfile
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
MP = RAIZ / "experiments" / "_s149_prereg_invierno" / "medir_predicciones.py"
T = json.load(open(sys.argv[1], encoding="utf-8"))
rnd = random.Random(150)


def brazo(fn):
    t = copy.deepcopy(T)
    for k, v in t["pasadas"].items():
        if len(v) == 2:
            v["brazo"] = dict(v["control"]); v["brazo"]["pub"] = fn(k, v["control"])
    return t


casos = {
    "identidad": lambda k, c: c["pub"],
    "oraculo": lambda k, c: int(c["pub"] and c["lab"] == "pos"),
    "azar_90": lambda k, c: int(c["pub"] and rnd.random() < 0.10),
    "borde_solo": lambda k, c: int(c["pub"] and (c["z"] is None or c["z"] < 52)),
    "saca_snpp": lambda k, c: int(c["pub"] and c.get("plataforma") != "VIIRS_SNPP"),
}
for nombre, fn in casos.items():
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(brazo(fn), fh); ruta = fh.name
    o = subprocess.run([sys.executable, str(MP), ruta, "VIIRS375"], capture_output=True, text=True, encoding="utf-8").stdout
    lineas = [l for l in o.splitlines() if l.strip().startswith(("CUMPLE", "FALLA", "INDECIDIBLE", "P1.", "razon", "positivas", "con la tabla", "n ", "con tabla y OCR", "con la tabla sola"))]
    print("== %s" % nombre)
    for l in lineas:
        print("   " + l.strip()[:170])
    Path(ruta).unlink()
