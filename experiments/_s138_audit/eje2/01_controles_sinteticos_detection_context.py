# -*- coding: utf-8 -*-
"""EJE 2 (S138): controles sinteticos sobre pipeline/detection_context.py.

Las dos preguntas del instrumento, por medicion:
  M1 (compuerta BT en Tests 2/3): si la compuerta NO existiera, el primer pase
     aceptaria el pixel frio-en-BT; si existe, lo rechaza. Control positivo: el
     mismo pixel con BT alta pasa. Ademas se mide si el SEGUNDO pase (tal como se
     llama en produccion: conditioned=False, active_mask vacia) recaptura el
     pixel que la compuerta rechazo. Si el instrumento estuviera muerto (ej. la
     funcion no marcara nada nunca), el control positivo daria 0 y se veria.
  M2 (retiro de pixeles Test 1 K1 del pool mu/sigma): se compara n_bg_used con
     test1_mask=None (produccion) y con la mascara puesta. Si el retiro
     estuviera activo, n_bg_used bajaria en exactamente el numero de pixeles K1.
  M3 (pixeles interiores de un cuerpo caliente extenso): bloque 7x7 uniforme
     muy caliente. El paper los captura por Test 1 (NTI > K1) y los retira; el
     codigo operacional no mete el Test 1 al hot mask (primer pase reemplaza el
     combine). Se cuenta cuantos de los 49 quedan marcados tras primer + segundo
     pase.
  M4 (pool del segundo pase sin filtros de no-aptos): se inyecta un outlier
     negativo fuerte (dNTI < -0.1) y se mide si cambia sigma del segundo pase.

No toca el repo: solo importa funciones puras y escribe a stdout y a un JSON en
este mismo directorio.
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import numpy as np  # noqa: E402

from pipeline.detection_context import (  # noqa: E402
    first_pass_tests_2_and_3, second_pass_adjacent, compute_nti_and_nti_app,
)
from pipeline import profile as P  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "01_controles_sinteticos_resultado.json")
res = {}

# --- escena sintetica: 51x51 (la matriz del paper), fondo homogeneo con ruido chico ---
rng = np.random.default_rng(7)
N = 51
lam_mir, lam_tir = 3.929, 11.03
bt_tir = 280.0 + rng.normal(0, 0.3, (N, N))
# MIR observado consistente con TIR (pixel homogeneo) + ruido pequeno
from pipeline.constants import C1 as PC1, C2 as PC2  # noqa: E402


def planck(lam, T):
    return PC1 / (lam ** 5 * (np.exp(PC2 / (lam * T)) - 1.0))


def bt_from_rad(lam, L):
    return PC2 / (lam * np.log(PC1 / (L * lam ** 5) + 1.0))


bt_mir = bt_tir + rng.normal(0, 0.15, (N, N))
rad_mir = planck(lam_mir, bt_mir)
nti, nti_app = compute_nti_and_nti_app(rad_mir, bt_tir, lam_mir, lam_tir)
roi = np.ones((N, N), dtype=bool)
dist = np.hypot(*np.meshgrid(np.arange(N) - 25, np.arange(N) - 25)).astype(float)
t_bg = float(np.median(bt_mir))
C1s, C1c = P.DNTI_CONTEXTUAL_C1_SUMMIT, P.DNTI_CONTEXTUAL_C1_SCENE
C2s, C2c = P.C2_DNTI_SUMMIT_NIGHT, P.C2_DNTI_SCENE_NIGHT
GATE = P.NTI_BT_SANITY_K


def run_first(bt_arr, nti_arr, test1_mask=None):
    hot, diag = first_pass_tests_2_and_3(
        nti=nti_arr, nti_app=nti_app, bt=bt_arr, roi_mask=roi, dist_km=dist,
        t_bg=t_bg, bt_sanity_k=GATE, c1_dnti_summit=C1s, c1_deti_summit=C1s,
        c2_dnti_summit=C2s, c2_deti_summit=C2s, inner_km=5.0,
        c1_dnti_scene=C1c, c1_deti_scene=C1c, c2_dnti_scene=C2c, c2_deti_scene=C2c,
        test1_mask=test1_mask, use_prose_branch=P.ENABLE_TESTS_23_PROSE_BRANCH)
    return hot, diag


def run_second(nti_arr, eti, active, conditioned):
    return second_pass_adjacent(
        nti=nti_arr, eti=eti, active_mask=active, c1_dnti=C1s, c1_deti=C1s,
        c2_dnti=C2s, c2_deti=C2s, is_summit=(dist <= 5.0), c1_dnti_scene=C1c,
        c1_deti_scene=C1c, c2_dnti_scene=C2c, c2_deti_scene=C2c,
        conditioned=conditioned, use_prose_branch=P.ENABLE_TESTS_23_PROSE_BRANCH)


# ---------------- M1: compuerta BT ----------------
# Pixel central con NTI elevado (dNTI ~ +0.02 >> C1=0.003) pero BT MIR apenas +1 K
# sobre el fondo: lo que produce un foco sub-pixel debil con TIR algo mas frio.
def escena_m1(delta_bt_mir, delta_bt_tir):
    b_mir = bt_mir.copy(); b_tir = bt_tir.copy()
    b_mir[25, 25] = t_bg + delta_bt_mir
    b_tir[25, 25] = 280.0 + delta_bt_tir
    n, _ = compute_nti_and_nti_app(planck(lam_mir, b_mir), b_tir, lam_mir, lam_tir)
    return b_mir, n


m1 = {}
for tag, dmir, dtir in (("gate_rechaza_bt+1K", 1.0, -3.0), ("control_pos_bt+8K", 8.0, -3.0)):
    b, n = escena_m1(dmir, dtir)
    hot1, d1 = run_first(b, n)
    dn = float(n[25, 25] - np.nanmean(np.delete(n[24:27, 24:27].ravel(), 4)))
    sp_uncond = run_second(n, d1["eti"], np.zeros_like(hot1), conditioned=False)
    sp_prod = run_second(n, d1["eti"], hot1, conditioned=False)      # como produccion
    sp_cond = run_second(n, d1["eti"], hot1, conditioned=True)
    m1[tag] = {
        "dNTI_pixel": round(dn, 4), "C1_summit": C1s,
        "mu_dnti": d1["mu_dnti"], "sd_dnti": d1["sd_dnti"],
        "umbral_efectivo_summit": min(C1s, d1["mu_dnti"] + C2s * d1["sd_dnti"]),
        "primer_pase_marca_centro": bool(hot1[25, 25]),
        "n_primer_pase": int(hot1.sum()),
        "segundo_pase_prod_marca_centro": bool(sp_prod[25, 25]),
        "n_tras_segundo_pase_prod": int(sp_prod.sum()),
        "segundo_pase_conditioned_marca_centro": bool(sp_cond[25, 25]),
    }
res["M1_compuerta_bt"] = m1

# ---------------- M2: retiro de pixeles Test 1 K1 del pool ----------------
b, n = escena_m1(8.0, -3.0)
k1_mask = (n > P.NTI_K1_NIGHT)          # en la escena sintetica solo puede ser el centro
n_k1 = int(k1_mask.sum())
if n_k1 == 0:
    # forzar: subir el centro hasta NTI > -0.8 (lava real)
    b[25, 25] = 400.0
    n, _ = compute_nti_and_nti_app(planck(lam_mir, b), bt_tir, lam_mir, lam_tir)
    k1_mask = (n > P.NTI_K1_NIGHT); n_k1 = int(k1_mask.sum())
_, d_sin = run_first(b, n, test1_mask=None)
_, d_con = run_first(b, n, test1_mask=k1_mask)
res["M2_retiro_test1_pool"] = {
    "n_pixeles_K1": n_k1, "nti_centro": float(n[25, 25]),
    "n_bg_used_produccion(test1_mask=None)": d_sin["n_bg_used"],
    "n_bg_used_con_retiro": d_con["n_bg_used"],
    "flag_ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK": P.ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK,
    "flag_ENABLE_TEST1_K1_BG_EXCLUDE": P.ENABLE_TEST1_K1_BG_EXCLUDE,
}

# ---------------- M3: cuerpo caliente extenso 7x7 ----------------
b = bt_mir.copy(); b[22:29, 22:29] = 400.0
n, _ = compute_nti_and_nti_app(planck(lam_mir, b), bt_tir, lam_mir, lam_tir)
hot1, d1 = run_first(b, n)
sp = run_second(n, d1["eti"], hot1, conditioned=False)
blk = np.zeros((N, N), bool); blk[22:29, 22:29] = True
res["M3_bloque_7x7"] = {
    "pixeles_bloque": int(blk.sum()),
    "NTI_min_bloque": float(np.nanmin(n[blk])), "K1": P.NTI_K1_NIGHT,
    "test1_K1_marcaria": int((n[blk] > P.NTI_K1_NIGHT).sum()),
    "primer_pase_marca": int((hot1 & blk).sum()),
    "tras_segundo_pase_marca": int((sp & blk).sum()),
    "interior_3x3_marcado_tras_2do_pase": int(sp[24:27, 24:27].sum()),
}

# ---------------- M4: pool del segundo pase con outlier negativo ----------------
b, n = escena_m1(8.0, -3.0)
hot1, d1 = run_first(b, n)
n_out = n.copy(); n_out[10, 10] = n[10, 10] - 0.5   # dNTI << -0.1 (no apto segun paper)
hot1o, d1o = run_first(b, n_out)
# reproducir la sigma interna del segundo pase (bg = ~active & finito), sin y con outlier
def sigma_segundo(n_arr, eti, active):
    from pipeline.detection_context import _nanmean_8neighbors_fast as m8
    dn = n_arr - m8(np.where(active, np.nan, n_arr))
    de = eti - m8(np.where(active, np.nan, eti))
    bg = (~active) & np.isfinite(dn) & np.isfinite(de)
    return float(np.std(dn[bg])), int(bg.sum())
s_a, nb_a = sigma_segundo(n, d1["eti"], hot1)
s_b, nb_b = sigma_segundo(n_out, d1o["eti"], hot1o)
res["M4_pool_segundo_pase"] = {
    "sd_dnti_primer_pase_sin_outlier": d1["sd_dnti"],
    "sd_dnti_primer_pase_con_outlier(filtro -0.1 activo)": d1o["sd_dnti"],
    "n_bg_primer_pase_con_outlier": d1o["n_bg_used"],
    "sd_dnti_segundo_pase_sin_outlier": s_a,
    "sd_dnti_segundo_pase_con_outlier": s_b,
    "n_bg_segundo_pase_con_outlier(incluye borde y <-0.1)": nb_b,
    "n_total_pixeles": N * N,
}

res["flags_efectivos"] = {
    "ENABLE_FIRST_PASS_TESTS_2_AND_3": P.ENABLE_FIRST_PASS_TESTS_2_AND_3,
    "ENABLE_SECOND_PASS_ADJACENT": P.ENABLE_SECOND_PASS_ADJACENT,
    "ENABLE_SECOND_PASS_CONDITIONED": P.ENABLE_SECOND_PASS_CONDITIONED,
    "ENABLE_UNSUITABLE_FILTERS_267_273": P.ENABLE_UNSUITABLE_FILTERS_267_273,
    "NTI_BT_SANITY_K": P.NTI_BT_SANITY_K,
}
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(json.dumps(res, indent=2, ensure_ascii=False))
