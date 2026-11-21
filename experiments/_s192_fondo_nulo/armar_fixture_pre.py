# -*- coding: utf-8 -*-
"""S192: arma tests/datos_s192_fondo_nulo/pre_s192_<pid>.json, el record que daba procesar_grilla ANTES de #1065.

POR QUÉ. La prueba del reemplazo (tests/test_reemplazo_fondo_nulo_s192.py) tiene que comparar lo que el script hace
con un record guardado por el código viejo contra lo que el código de hoy escribiría. El código viejo vive en el tag
`pre-s192-fondo-nulo`; en Actions el checkout es de profundidad 1 y sin tags, así que el record viejo va como dato
fijo y la prueba lo regenera desde el tag sólo cuando git lo tiene (si no, salta esa parte, no la da por buena).

Entradas: las grillas reales de tests/datos_s164_modis (pasada 3933, Cordón Caulle 2026-03-16 03:10 MODIS Terra, sin
fondo; pasada 1611, Láscar 2026-04-25 07:35 MODIS Aqua, con fondo), con la grilla, la caja y la posición del cráter
del código de hoy (no cambiaron en #1065: sólo cambió procesar_grilla, vrp_mirova y t_bg_de).

USO: python experiments/_s192_fondo_nulo/armar_fixture_pre.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import types
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
TAG = "pre-s192-fondo-nulo"
SALIDA = RAIZ / "tests" / "datos_s192_fondo_nulo"
PASADAS = {3933: "MODIS_TERRA", 1611: "MODIS_AQUA"}
COMMIT_GUARDADO = "fd73d5328cad1e072f4fe90ef07afee0dcbc93c3"   # origin/main del 2026-11-20 al armar el dato


def a_json(o):
    """Conversor para json: tipos de numpy a tipos de Python (el record del pipeline los mezcla)."""
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


def normalizar(rec):
    """El record como quedaría escrito en JSON y leído de vuelta (tuplas a listas, numpy a Python)."""
    return json.loads(json.dumps(rec, default=a_json))


def modulo_viejo(raiz: Path = RAIZ):
    """pipeline/mirova_v750_codigo.py del tag, cargado como submódulo de pipeline (para sus imports relativos) sin
    pisar el de hoy. None si git no tiene el tag."""
    r = subprocess.run(["git", "-C", str(raiz), "show", f"{TAG}:pipeline/mirova_v750_codigo.py"],
                       capture_output=True)
    if r.returncode != 0:
        return None
    import pipeline  # noqa: F401  (el paquete padre tiene que existir para el import relativo)
    m = types.ModuleType("pipeline._mv_pre_s192")
    m.__file__ = str(raiz / "pipeline" / "mirova_v750_codigo.py")
    m.__package__ = "pipeline"
    sys.modules[m.__name__] = m
    exec(compile(r.stdout.decode("utf-8"), f"{TAG}:pipeline/mirova_v750_codigo.py", "exec"), m.__dict__)
    return m


def entradas(pid):
    """Grilla, caja y posición del cráter de la pasada, con el código de hoy (las mismas que usa la prueba de #1065)."""
    sys.path.insert(0, str(RAIZ))
    sys.path.insert(0, str(RAIZ / "tests"))
    from pipeline import mirova_v750_codigo as MV
    import test_mirova_modis_codigo_s164 as T164
    p, mir, tir, g, box, _mask, _d = T164._via_sobre_grilla(pid)
    vl = T164._yaml_volcan(p["vol"])
    return p, mir, tir, g, box, MV.posicion_de(g, vl["lat"], vl["lon"])


def record(mod, pid):
    p, mir, tir, g, box, pos = entradas(pid)
    return normalizar(mod.procesar_grilla(mir, tir, g, box, p["dayflag"], p["sunglint"], pos, p["inner"],
                                          PASADAS[pid], familia="MODIS"))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, str(RAIZ))
    viejo = modulo_viejo()
    if viejo is None:
        print(f"git no tiene el tag {TAG}", file=sys.stderr)
        return 2
    SALIDA.mkdir(parents=True, exist_ok=True)
    for pid in PASADAS:
        rec = record(viejo, pid)
        ruta = SALIDA / f"pre_s192_{pid}.json"
        with open(ruta, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({"tag": TAG, "pasada": pid, "record": rec}, indent=1, ensure_ascii=False) + "\n")
        print(ruta.relative_to(RAIZ).as_posix(), "vrp_mw", rec["vrp_mw"], "n", rec["n_anomalous_pixels"],
              "L_bk", rec["diag_codigo_mirova"]["L_bk"])
    # El mismo record tal como lo guardó producción (con lo que agregan calcular_vrp_granulo, process_modis y
    # store.py), para la prueba del tablero y la de forma guardada. Commit fijo: el archivo vivo lo reescribe el NRT.
    r = subprocess.run(["git", "-C", str(RAIZ), "show", f"{COMMIT_GUARDADO}:data/mirova_equivalent/PuyehueCordonCaulle.json"],
                       capture_output=True)
    if r.returncode != 0:
        print(f"git no tiene el commit {COMMIT_GUARDADO}", file=sys.stderr)
        return 2
    recs = [x for x in json.loads(r.stdout)["records"]
            if x["sensor"] == "MODIS_TERRA" and x["datetime_utc"] == "2026-03-16 03:10"]
    assert len(recs) == 1, len(recs)
    ruta = SALIDA / "guardado_pcc_modis_20260316_0310.json"
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"commit": COMMIT_GUARDADO, "archivo": "data/mirova_equivalent/PuyehueCordonCaulle.json",
                            "record": recs[0]}, indent=1, ensure_ascii=False) + "\n")
    print(ruta.relative_to(RAIZ).as_posix(), "vrp_mw", recs[0]["vrp_mw"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
