# -*- coding: utf-8 -*-
"""S157: con `enable_modis_mir_lambda_por_banda` apagado, ¿calculate_vrp da EXACTAMENTE lo mismo que antes del
cambio? (A45: el flag nace apagado y el procesador apagado no puede moverse ni un bit).

CÓMO. Carga `pipeline/process_modis.py` tal como estaba en el tag `pre-s157-lambda-b22` (git show) como un
módulo hermano, y corre los dos procesadores sobre las mismas escenas sintéticas con los mismos flags,
comparando el record completo serializado. Las combinaciones cubren los sitios tocados: B22 primaria o no,
kernel de fondo local por volcán, magnitud por corona (que llama a `cluster_vrp_per_pixel_with_bg`), camino
de vent, Test 1 integrado y escena con un píxel de B22 saturado.

P1 (si estuviera roto, lo vería): CONTROL con el flag ENCENDIDO en el procesador nuevo; tiene que dar distinto
en las escenas con B22 primaria, si no la comparación no ve la λ.

Uso:  python -I experiments/_s157_lambda_b22/identidad_flag_apagado.py
"""
import io
import json
import subprocess
import sys
import types
from itertools import product
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import pipeline.process_modis as nuevo  # noqa: E402
import pipeline.vrp_regimes as vr_nuevo  # noqa: E402

TAG = "pre-s157-lambda-b22"


def _cargar_viejo(ruta, nombre):
    src = subprocess.run(["git", "show", f"{TAG}:{ruta}"], cwd=ROOT, capture_output=True, text=True,
                         encoding="utf-8", check=True).stdout
    m = types.ModuleType(nombre)
    m.__package__ = "pipeline"
    m.__file__ = str(ROOT / ruta)
    sys.modules[nombre] = m
    exec(compile(src, f"{TAG}:{ruta}", "exec"), m.__dict__)
    return m


vr_viejo = _cargar_viejo("pipeline/vrp_regimes.py", "pipeline._vr_viejo")
viejo = _cargar_viejo("pipeline/process_modis.py", "pipeline._pm_viejo")
t1_viejo = _cargar_viejo("pipeline/test1_integrated.py", "pipeline._t1_viejo")
# el viejo importó la magnitud por corona y el Test 1 de los módulos VIVOS: se los cambiamos por los del tag
viejo.cluster_vrp_per_pixel_with_bg = vr_viejo.cluster_vrp_per_pixel_with_bg
viejo.compute_test1_mir = t1_viejo.compute_test1_mir

from test_lambda_por_banda_modis_s157 import CLAT, CLON, _escena  # noqa: E402


def escena(variante):
    data, p22, p21 = _escena()
    if variante == "sin_saturado":
        data["band22"][p21] = data["band21"][p21] = data["band21"][p22]
    if variante == "debil":
        rng = np.random.default_rng(11)
        data["band21"] = data["band21"] * (1 + rng.normal(0, 0.01, data["band21"].shape)).astype(np.float32)
        data["band22"] = np.where(np.isnan(data["band22"]), np.nan, data["band21"]).astype(np.float32)
    return data


def correr(mod, data, b22, kernel, corona, vent, flag, t1=False):
    pats = [patch.object(mod, "read_modis_l1b", return_value=data),
            patch.object(mod, "ENABLE_MODIS_B22_PRIMARY", b22),
            patch.object(mod, "ENABLE_LOCAL_CLUSTER_MAGNITUDE", corona),
            patch.object(mod, "ENABLE_VENT_PATH_MODIS", vent),
            patch.object(mod, "ENABLE_TEST1_PATH", t1)]
    if hasattr(mod, "ENABLE_MODIS_MIR_LAMBDA_POR_BANDA"):
        pats.append(patch.object(mod, "ENABLE_MODIS_MIR_LAMBDA_POR_BANDA", flag))
    for p in pats:
        p.start()
    try:
        r = mod.calculate_vrp(hdf_path=Path("MOD021KM.A2026290.0300.061.fake.hdf"), geo_path=Path("x"),
                              volcano_lat=CLAT, volcano_lon=CLON, radius_km=25.0, vent_lat=CLAT, vent_lon=CLON,
                              inner_radius_km=5.0, local_kernel_bg_compatible=kernel, lbg_global_compatible=True)
    finally:
        for p in pats:
            p.stop()
    return json.dumps(r, sort_keys=True, default=str)


def main():
    n = iguales = control_distinto = control_n = 0
    for variante, b22, kernel, corona, vent, t1 in product(("base", "sin_saturado", "debil"), (True, False),
                                                           (False, True), (False, True), (False, True),
                                                           (False, True)):
        a = correr(viejo, escena(variante), b22, kernel, corona, vent, None, t1)
        b = correr(nuevo, escena(variante), b22, kernel, corona, vent, False, t1)
        n += 1
        iguales += a == b
        if a != b:
            print("DISTINTO", variante, b22, kernel, corona, vent, t1)
        if b22:
            c = correr(nuevo, escena(variante), b22, kernel, corona, vent, True, t1)
            control_n += 1
            control_distinto += c != a
    # Cobertura (P2): cada camino tocado tiene que CAMBIAR el record cuando se enciende; si no cambia, la
    # escena no lo ejercita y la identidad de arriba no dice nada de él.
    cob = {}
    for nombre, idx in (("kernel_local", 0), ("corona", 1), ("vent", 2), ("test1", 3)):
        cambia = 0
        for variante, b22 in product(("base", "sin_saturado", "debil"), (True, False)):
            base = [False, False, False]
            on = list(base) + [False]
            on[idx] = True
            a0 = correr(nuevo, escena(variante), b22, *base, False)
            a1 = correr(nuevo, escena(variante), b22, *on[:3], False, on[3])
            cambia += a0 != a1
        cob[nombre] = cambia
    print(f"cobertura (de 6 escenas, cuántas cambian al encender el camino): {cob}")
    print(f"flag apagado: {iguales} de {n} combinaciones idénticas al tag {TAG}")
    print(f"control (flag encendido, B22 primaria): {control_distinto} de {control_n} distintas")
    return 0 if iguales == n and control_distinto == control_n else 1


if __name__ == "__main__":
    sys.exit(main())
