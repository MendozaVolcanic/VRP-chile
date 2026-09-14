# -*- coding: utf-8 -*-
"""Fase 0 tarea 4 (S139/S140): descomposicion de la magnitud contra el OSF v2.5.

POR QUE: nuestra magnitud V375 queda en ~0,7 de la de MIROVA. S139 la separo, pasada a pasada,
en conteo de pixeles (F_n: integramos 1 donde MIROVA integra 3) y exceso por pixel (F_ex, que a su
vez se parte en nivel caliente y fondo). Cuando contamos el mismo numero de pixeles la razon es
0,995: k, area y banda estan bien, lo que falta es seleccion. Este test congela esa medicion.

Numeros de experiments/_s139_audit/magnitud/02_salida.txt (n, R_gm, Fn_gm, control 6 h) y
04_salida.txt (igual conteo, n 342). El OSF (98 MB) no esta en git: en el CI el test se salta.
Si se reprocesan los records de 2025 el n puede cambiar sin que haya defecto: volver a medir.
"""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OSF = os.path.join(ROOT, "data", "mirova_reference", "VRP_GLOBAL_ARCHIVE_2025.csv")


@pytest.mark.skipif(not os.path.exists(OSF), reason="OSF no descargado")
def test_reproduce_descomposicion_s139(tmp_path):
    out = tmp_path / "mag.json"
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "descomponer_magnitud_osf.py"),
                        "--out", str(out)],
                       capture_output=True, text=True, timeout=900,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 0, r.stderr[-1500:]
    with open(out, encoding="utf-8") as fh:
        m = json.load(fh)
    t = m["VIIRS375"]["total"]
    assert t["n"] == 1499, f"n={t['n']}: si se reprocesaron records de 2025, re-medir"
    assert abs(t["R_gm"] - 0.659) < 0.01 and abs(t["Fn_gm"] - 0.553) < 0.01, t
    ic = m["VIIRS375"]["igual_conteo"]
    assert ic["n"] == 342 and abs(ic["R"] - 0.995) < 0.01, ic
    # control negativo: pareo desplazado 6 h da 0 pares
    assert m["controles"]["pares_desplazados_6h"] == 0
    # control de replica del nucleo F5' contra el valor persistido por el pipeline
    assert m["controles"]["replica_f5_discrepa"] == 0
    for b in ("por_volcan", "por_cenit"):
        assert m["VIIRS375"][b], b
