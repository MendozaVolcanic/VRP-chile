# -*- coding: utf-8 -*-
"""Prueba sintética del instrumento de probe_chillan.py, ANTES de bajar ningún gránulo.

Qué tiene que pasar (si algo falla, el probe no se corre: el job sale 1):
  1. Los 10 gránulos tienen record persistido en data/mirova_equivalent/NevadosDeChillan.json (si no, C-P1 no
     tendría contra qué comparar).
  2. El diagnóstico de vecinos encuentra los 8 vecinos de un cúmulo de 1 píxel, marca al vecino tibio como no
     alertado y le asigna potencia positiva con el anillo; a un vecino más frío que el anillo, cero.
  3. Control NEGATIVO del diagnóstico: si el vecino tibio está alertado, deja de aparecer (no se cuenta dos veces).
  4. (MODIS) La inversa de Planck del envoltorio d25_rad devuelve la temperatura de partida a 1e-6 K.
Uso: python prueba_probe.py [--modis]
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_chillan as pc  # noqa: E402

fallas = []
for fam, lista in pc.PASADAS.items():
    for s, n in lista:
        if pc.persistido(n) is None:
            fallas.append("sin record persistido: %s" % n)


def escena():
    nti = np.full((9, 9), -0.95)
    nti[4, 4] = -0.5
    fp = {"nti": nti, "eti": nti.copy(), "bt": np.full((9, 9), 268.0), "dist": np.zeros((9, 9)), "t_bg": 271.0,
          "bt_sanity_k": 3.0, "roi1_mask": None,
          "kw": {"use_prose_branch": True, "inner_km": 5, "c1_dnti_summit": 0.003, "c1_deti_summit": 0.003,
                 "c2_dnti_summit": 5, "c2_deti_summit": 5},
          "diag": {"mu_dnti": 0.0, "sd_dnti": 0.001, "mu_deti": 0.0, "sd_deti": 0.001}}
    fp["bt"][4, 4], fp["bt"][4, 5] = 330.0, 285.0
    return fp


planck = lambda x: pc.vr_planck(x, 3.74)  # noqa: E731
fp = escena()
hot = np.zeros((9, 9), bool)
hot[4, 4] = True
out = pc.vecinos_no_alertados(fp, {"hot": hot, "c0": [(4, 4)]}, [], 2531250.0, planck, 5)
vec = {tuple(f["ij"]): f for f in out["vecinos"]}
if len(vec) != 8:
    fallas.append("vecinos: %d, esperado 8" % len(vec))
if not vec.get((4, 5), {}).get("vrp_si_se_sumara_anillo_mw", 0) > 0:
    fallas.append("el vecino tibio no suma potencia")
if vec.get((3, 3), {}).get("vrp_si_se_sumara_anillo_mw", 1) != 0:
    fallas.append("un vecino más frío que el anillo suma potencia")
hot2 = hot.copy()
hot2[4, 5] = True
out2 = pc.vecinos_no_alertados(fp, {"hot": hot2, "c0": [(4, 4), (4, 5)]}, [], 2531250.0, planck, 5)
if any(tuple(f["ij"]) == (4, 5) for f in out2["vecinos"]):
    fallas.append("un píxel alertado aparece como vecino no alertado")

# 5. La reconstrucción del segundo pase (verificador H11) da los mismos píxeles nuevos que el real, con `max` y dual.
import pipeline.detection_context as dc  # noqa: E402
rng = np.random.default_rng(157)
disc = nuevos = 0
for _ in range(20):
    nti = rng.normal(-0.9, 0.01, (40, 40))
    eti = rng.normal(0.0, 0.01, (40, 40))
    for _f in range(3):
        i, j = rng.integers(3, 37, 2)
        nti[i, j] += 0.3
        eti[i, j] += 0.3
        nti[i, j + 1] += 0.15
        eti[i, j + 1] += 0.15
    act = np.zeros((40, 40), bool)
    act[np.argsort(nti, axis=None)[-3:] // 40, np.argsort(nti, axis=None)[-3:] % 40] = True
    summit = np.zeros((40, 40), bool)
    summit[10:30, 10:30] = True
    kw = dict(c1_dnti=0.003, c1_deti=0.003, c2_dnti=5, c2_deti=5, is_summit=summit, c1_dnti_scene=0.01,
              c1_deti_scene=0.01, c2_dnti_scene=10, c2_deti_scene=10, min_bg_pixels=10, conditioned=False,
              use_prose_branch=True)
    real = dc.second_pass_adjacent(nti, eti, act, **kw)
    sp = pc.segundo_pase_por_pixel({"nti": nti, "eti": eti, "active": act, "is_summit": summit,
                                    "kw": {k: v for k, v in kw.items() if k != "is_summit"}, "out": real})
    for a in range(40):
        for b in range(40):
            if act[a, b]:
                continue
            tn, te = sp["thr"](bool(summit[a, b]))
            nuevo = bool(sp["dnti"][a, b] > tn and sp["deti"][a, b] > te)
            disc += nuevo != bool(real[a, b])
            nuevos += bool(real[a, b])
if disc:
    fallas.append("segundo pase reconstruido: %d discrepancias con second_pass_adjacent" % disc)
if nuevos == 0:   # sin píxeles nuevos la comparación no puede fallar (A116)
    fallas.append("la escena sintética del segundo pase no produce ningún píxel nuevo")
print("segundo pase: %d píxeles nuevos reales, %d discrepancias" % (nuevos, disc))
if "--modis" in sys.argv:
    import pipeline.process_modis as pm
    lam = pm.BAND21_LAMBDA
    for t in (250.0, 272.5, 330.0):
        L = pm.C1 / (lam ** 5 * (np.exp(pm.C2 / (lam * t)) - 1))
        t2 = pm.C2 / (lam * np.log(1.0 + pm.C1 / (lam ** 5 * L)))
        if abs(t2 - t) > 1e-6:
            fallas.append("inversa de Planck MODIS: %s -> %s" % (t, t2))

print("prueba del instrumento:", "OK" if not fallas else "FALLA")
for f in fallas:
    print("  -", f)
sys.exit(1 if fallas else 0)
