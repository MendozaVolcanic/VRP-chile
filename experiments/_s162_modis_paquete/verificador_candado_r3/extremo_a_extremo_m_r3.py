# Verificador r3: corre main() de m_con_regla_matlab.py sobre un directorio de artefactos sintetico (el script no tiene
# prueba de su camino principal; el workflow solo corre --probar)
import sys, json, tempfile, os
from pathlib import Path
import numpy as np
AQUI = Path(r"C:/vrp-trabajo/s162-modd/experiments/_s162_modis_paquete")
sys.path.insert(0, str(AQUI))
import probar_evaluar_paquete as T
import m_con_regla_matlab as M
filas = T.base()
for i, f in enumerate(filas):
    f["id"] = 1000 + i
with tempfile.TemporaryDirectory() as td:
    art = Path(td)
    with open(art / "ab_parte00.jsonl", "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"tipo": "cabecera", "parte": 0, "commit": "x" * 40}) + "\n")
        for f in filas:
            fh.write(json.dumps(f) + "\n")
    rng = np.random.default_rng(1)
    for f in filas:
        if f["lab"] in ("bajo1", "protegida") and f["port"]["fisica"]["npix"]:
            mir = 0.1 + rng.normal(0, 0.002, (51, 51)); mir[25, 25] = 0.1 + f["port"]["fisica"]["vrp_mw"] / 18.9 + 0.002
            np.savez(art / ("grilla_%03d.npz" % f["id"]), mir=mir, tir=mir)
    sys.argv = ["m_con_regla_matlab.py", "--art", str(art), "--commit", "x" * 40]
    try:
        M.main()
        print("main terminó; json escrito:", (art / "m_con_regla_matlab.json").exists())
    except SystemExit:
        pass
    except Exception as e:
        import traceback; traceback.print_exc()
