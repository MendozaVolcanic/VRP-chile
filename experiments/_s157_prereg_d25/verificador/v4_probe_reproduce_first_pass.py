# -*- coding: utf-8 -*-
"""Verificador S157 1.29, pregunta 7: ¿el diagnóstico de selección del probe (vecinos_no_alertados) reproduce
pipeline/detection_context.py::first_pass_tests_2_and_3 bajo la conectiva max de K? Y ¿qué deja fuera?

Escena sintética con ruido + varios focos. Se corre el first_pass REAL (captura de nti, eti, kwargs y diag como en el
probe) y luego second_pass_adjacent REAL (sin condicionar, como en K). Para cada foco del primer pase se le pasa al
probe un 'hot' que contiene SÓLO ese píxel: los vecinos que el primer pase marcó tienen que salir con T2, T3 y BT en
True, y los que no marcó con alguno en False (reproducción exacta). Después se cuenta, con el hot FINAL (segundo
pase), cuántos vecinos no alertados el probe atribuye a la compuerta de BT, que el segundo pase no aplica.
Uso: python v4_probe_reproduce_first_pass.py > v4_salida.txt
"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "probe_l1b"))
import probe_chillan as pc  # noqa: E402
import pipeline.detection_context as dc  # noqa: E402

rng = np.random.default_rng(7)
n = 60
fallas, n_vec, n_bt_solo, n_recap = 0, 0, 0, 0
for semilla in range(20):
    rng = np.random.default_rng(semilla)
    bt = 272 + rng.normal(0, 1.5, (n, n))
    nti = -0.93 + rng.normal(0, 0.004, (n, n))
    for _ in range(6):
        i, j = rng.integers(5, n - 5, 2)
        nti[i, j] += rng.uniform(0.005, 0.08); bt[i, j] += rng.uniform(-2, 30)
        for di, dj in ((0, 1), (1, 0), (1, 1)):
            nti[i + di, j + dj] += rng.uniform(0, 0.01); bt[i + di, j + dj] += rng.uniform(-3, 6)
    nti_app = -0.93 + rng.normal(0, 0.002, (n, n))
    dist = np.hypot(*np.meshgrid(np.arange(n) - n / 2, np.arange(n) - n / 2, indexing="ij")) * 0.375
    roi = np.ones((n, n), bool)
    kw = dict(c1_dnti_summit=0.003, c1_deti_summit=0.003, c2_dnti_summit=5, c2_deti_summit=5, inner_km=5.0,
              c1_dnti_scene=0.010, c1_deti_scene=0.010, c2_dnti_scene=10, c2_deti_scene=10, use_prose_branch=True)
    hot, diag = dc.first_pass_tests_2_and_3(nti, nti_app, bt, roi, dist, 272.0, 3.0, **kw)
    fp = {"nti": nti, "eti": diag["eti"], "bt": bt, "dist": dist, "t_bg": 272.0, "bt_sanity_k": 3.0, "roi1_mask": None,
          "kw": dict(kw), "diag": {k: v for k, v in diag.items() if k != "eti"}}
    planck = lambda x: pc.vr_planck(x, 3.74)  # noqa: E731
    for (i, j) in zip(*np.where(hot)):
        solo = np.zeros_like(hot); solo[i, j] = True
        out = pc.vecinos_no_alertados(fp, {"hot": solo, "c0": [(int(i), int(j))]}, [], 2531250.0, planck, 5.0)
        for v in out["vecinos"]:
            a, b = v["ij"]; n_vec += 1
            todo = v["pasa_t2"] and v["pasa_t3"] and v["pasa_bt"]
            if todo != bool(hot[a, b]):
                fallas += 1
    fin = dc.second_pass_adjacent(nti=nti, eti=diag["eti"], active_mask=hot, c1_dnti=0.003, c1_deti=0.003, c2_dnti=5,
                                  c2_deti=5, is_summit=dist <= 5.0, c1_dnti_scene=0.010, c1_deti_scene=0.010,
                                  c2_dnti_scene=10, c2_deti_scene=10, conditioned=False, use_prose_branch=True)
    n_recap += int(np.sum(fin & ~hot))
    for (i, j) in zip(*np.where(fin)):
        out = pc.vecinos_no_alertados(fp, {"hot": fin, "c0": [(int(i), int(j))]}, [], 2531250.0, planck, 5.0)
        for v in out["vecinos"]:
            if v["pasa_t2"] and v["pasa_t3"] and not v["pasa_bt"]:
                n_bt_solo += 1
print("vecinos evaluados contra el primer pase real: %d | discrepancias del probe: %d" % (n_vec, fallas))
print("píxeles que el segundo pase (sin compuerta BT, K) agrega al primero: %d" % n_recap)
print("vecinos NO alertados en la máscara final que el probe atribuye SOLO a BT (compuerta que el segundo pase no aplica): %d" % n_bt_solo)
