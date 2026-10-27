# -*- coding: utf-8 -*-
"""S165 (V165-03): arnés que corre el main() REAL de scripts/run_pipeline.py sobre las escenas MODIS sintéticas del
arnés MxD03 (tests/arnes_mxd03_s165.py) y devuelve lo que la corrida escribe: los records que llegan a store y el
JSON de cobertura, con y sin --estricto-cobertura.

POR QUÉ. Con ENABLE_MODIS_CRATER_SIN_DATO encendido, una pasada en que el cráter no tiene posición no deja record. El
verificador de #920 (V165-03) vio que tampoco dejaba rastro en la cobertura: el resumen seguía diciendo «completa».
Lo que se quiere probar está repartido entre calculate_vrp (detecta el caso) y run_pipeline (lo anota), así que el
arnés corre los dos juntos. Sólo se reemplaza lo que no se puede tener en una prueba: la red (fetch_for_volcano
deja dos archivos vacíos en disco), la lectura del HDF (pyhdf no corre en Windows), store (nunca se escribe en
data/) y el reloj solar (la escena se procesa como nocturna).

Uso: python tests/arnes_sin_dato_s165.py --salida X.json [--flag NOMBRE=True ...]
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import arnes_mxd03_s165 as M  # noqa: E402
import arnes_sintetico_s142 as A  # noqa: E402

VOLCAN = "Villarrica"            # la escena está centrada en A.LAT0, A.LON0 (Villarrica)
FECHA = "2026-07-19"             # día 200, el del nombre de los gránulos del arnés MxD03
L1B = "MOD021KM.A2026200.0300.061.hdf"
GEO = "MOD03.A2026200.0300.061.hdf"


def _cargar_run_pipeline():
    spec = importlib.util.spec_from_file_location("run_pipeline_s165", ROOT / "scripts" / "run_pipeline.py")
    rp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rp)
    return rp


def _prohibido(*a, **k):
    raise RuntimeError("el arnés no puede tocar NASA (A71)")


def correr(rp, tipo, flags, estricto, tmp):
    import pipeline.process_modis as pm
    data, mxd, vent_lat, vent_lon = M.escena(tipo)
    records = []

    def fetch_falso(volcano, date, out_dir, **k):
        out_dir.mkdir(parents=True, exist_ok=True)
        rutas = [out_dir / L1B, out_dir / GEO]
        for p in rutas:
            p.write_bytes(b"")
        return {"MODIS_TERRA": rutas}

    def guardar(nombre, result, **k):
        records.append({"volcan": nombre, "record": result})

    cob = Path(tmp) / f"cob_{tipo}_{int(estricto)}.json"
    argv = ["run_pipeline.py", "--volcano", VOLCAN, "--date", FECHA, "--cobertura-json", str(cob)]
    if estricto:
        argv.append("--estricto-cobertura")
    ctx = [patch.object(rp.fetch, "fetch_for_volcano", fetch_falso),
           patch.object(rp.fetch, "auth", lambda: None),
           patch.object(rp.fetch.earthaccess, "login", _prohibido),
           patch.object(rp.fetch.earthaccess, "search_data", _prohibido),
           patch.object(rp.fetch.earthaccess, "download", _prohibido),
           patch.object(rp, "TMP_DIR", Path(tmp) / "tmp"),
           patch.object(rp, "is_nighttime", lambda *a, **k: True),
           patch.object(rp, "get_detection_anchor", lambda v: (vent_lat, vent_lon)),
           patch.object(rp.store, "append_record", guardar),
           patch.object(pm, "read_modis_l1b", return_value=data),
           patch.object(pm, "leer_mxd03", return_value=mxd),
           patch.object(sys, "argv", argv)]
    ctx += [patch.object(pm, k, v) for k, v in flags.items()]
    for p in ctx:
        p.start()
    try:
        rp.fetch.reiniciar_ventana()
        rp.fetch.limpiar_fallas()
        try:
            rp.main()
            codigo = 0
        except SystemExit as e:
            codigo = e.code or 0
    finally:
        for p in reversed(ctx):
            p.stop()
    cobertura = json.loads(cob.read_text(encoding="utf-8"))
    return {"codigo": codigo, "cobertura": cobertura, "records": records}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--flag", action="append", default=[])
    a = ap.parse_args(argv)
    flags = {}
    for s in a.flag:
        k, v = s.split("=", 1)
        flags[k] = ast.literal_eval(v)
    for v in ("VRP_VENTANA_BUSQUEDA", "VRP_CACHE_BUSQUEDA_DIR", "VRP_CONSERVAR_GRANULOS",
              "GITHUB_STEP_SUMMARY", "GITHUB_ACTIONS"):
        os.environ.pop(v, None)
    os.environ["VRP_BUSQUEDA_VENTANA"] = "0"
    rp = _cargar_run_pipeline()
    salida = {}
    with tempfile.TemporaryDirectory() as tmp:
        for tipo in M.ESCENAS:
            for estricto in (False, True):
                salida[f"{tipo}|estricto={estricto}"] = correr(rp, tipo, flags, estricto, tmp)
    texto = A.canonico(salida)
    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(a.salida).write_text(texto, encoding="utf-8")


def correr_en_subproceso(tmp_dir, flags=(), perfil="mirova_equivalent"):
    import subprocess
    salida = Path(tmp_dir) / f"sin_dato_{perfil}_{'_'.join(sorted(flags)) or 'apagado'}.json"
    cmd = [sys.executable, str(ROOT / "tests" / "arnes_sin_dato_s165.py"), "--salida", str(salida)]
    for f in flags:
        cmd += ["--flag", f"{f}=True"]
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=900,
                       env={**os.environ, "VRP_PROFILE": perfil, "PYTHONIOENCODING": "utf-8"})
    # RuntimeError y no assert: un subproceso que muere es una caída, no una aserción (S152, S156).
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-4000:])
    return salida.read_text(encoding="utf-8")


if __name__ == "__main__":
    main()
