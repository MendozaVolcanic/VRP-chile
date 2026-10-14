# -*- coding: utf-8 -*-
"""S151 (loop 1.5, arreglo D3 del verificador de #790): el probe no puede salir verde sin datos.

Corre `probe_d25_v750.main()` en subprocesos, sin red:
  1. PROBE_VOL="Isluaga" (mal escrito): tiene que salir con código 2 ANTES de autenticar.
  2. PROBE_VOL="Copahue" (existe): tiene que pasar el chequeo y llegar a auth(); acá auth() está
     reemplazada por una que sale con 7, así que el código esperado es 7. Si diera 2, el chequeo
     estaría cortando también listas buenas.
Sale 2 si alguna de las dos falla. USO: python prueba_probe_lista_vacia.py
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
ENVOLTORIO = (
    "import sys, importlib.util; sys.argv=['probe'];"
    "spec=importlib.util.spec_from_file_location('pr', r'%s');"
    "m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
    "m.auth=lambda: sys.exit(7); m.main()" % (HERE / "probe_d25_v750.py")
)


def correr(vol):
    env = {**os.environ, "PROBE_VOL": vol, "PROBE_MAX": "0", "PYTHONIOENCODING": "utf-8"}
    o = subprocess.run([sys.executable, "-c", ENVOLTORIO], env=env, capture_output=True, text=True,
                       encoding="utf-8", cwd=HERE)
    return o.returncode, (o.stdout.strip().splitlines() or [""])[-1]


fallas = 0
for vol, esperado in (("Isluaga", 2), ("Copahue", 7)):
    rc, ultima = correr(vol)
    ok = rc == esperado
    fallas += not ok
    print(f"{'OK ' if ok else 'FALLA'} PROBE_VOL={vol!r}: código {rc} (esperado {esperado}) | {ultima}")
sys.exit(2 if fallas else 0)
