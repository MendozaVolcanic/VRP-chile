# -*- coding: utf-8 -*-
"""S149, frente D. Para cada perfil de A/B de S124 a S149: el Test 1 integrado estaba encendido?
Se resuelve como lo resuelve el codigo (pipeline.profile en un subproceso por perfil, A89), NO
leyendo el YAML. OJO: resuelve con el codigo de HOY; un perfil viejo puede haber resuelto distinto
el dia de su corrida si un default cambio despues (limite declarado).
Control positivo: _s146_ab_sin_test1 debe dar False y mirova_equivalent True.
Control de instrumento muerto: si todos dieran lo mismo, el subproceso no estaria leyendo el perfil."""
import os, subprocess, sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
PERF = ["mirova_equivalent", "_f70_a", "_f70_b", "_s124_kernelbg_ab", "_s124_villarrica_op_ab", "_s125_mag_control", "_s125_mag_a",
        "_s125_mag_b", "_s125_mag_c", "_s125_cloudmask_on", "_s125_cloudmask_off", "_s126_corona_on", "_s126_corona_off", "_s129_ab_control",
        "_s129_ab_pool", "_s130_d18_caja", "_s130_d18_circulo", "_s133_area_control", "_s133_area_geoloc", "_s133_b22_control",
        "_s133_b22_enabled", "_s135_ab_a_control", "_s135_ab_b_nokeeppeak", "_s142_ab_control", "_s142_ab_literal",
        "_s146_ab_control", "_s146_ab_sin_test1", "_s147_ab_sin_test1_max", "_s147_ab_sin_test1_caja", "experimental"]
COD = ("import json, pipeline.profile as p; print('@@'+json.dumps({k: getattr(p, k, 'NO EXISTE') for k in "
       "['ENABLE_TEST1_PATH','ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK','ENABLE_TESTS_23_PROSE_BRANCH','ENABLE_ROI1_BOX_PAPER','CLOUD_MASK_BT_K','ENABLE_MODIS_B22_PRIMARY']}))")
print("%-28s %-6s %-9s %-6s %-6s %-8s %s" % ("perfil", "TEST1", "keep_peak", "max", "caja", "nube_K", "b22"))
for pf in PERF:
    env = dict(os.environ, VRP_PROFILE=pf, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-c", COD], cwd=str(RAIZ), env=env, capture_output=True, text=True, encoding="utf-8")
    lin = [l for l in r.stdout.splitlines() if l.startswith("@@")]
    if not lin:
        print("%-28s NO RESUELVE: %s" % (pf, (r.stderr or "").strip().splitlines()[-1:] )); continue
    d = json.loads(lin[0][2:])
    print("%-28s %-6s %-9s %-6s %-6s %-8s %s" % (pf, d["ENABLE_TEST1_PATH"], d["ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK"],
          d["ENABLE_TESTS_23_PROSE_BRANCH"], d["ENABLE_ROI1_BOX_PAPER"], d["CLOUD_MASK_BT_K"], d["ENABLE_MODIS_B22_PRIMARY"]))
