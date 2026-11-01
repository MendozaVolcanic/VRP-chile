"""Afirmación 1: compuerta bt > t_bg + 3 K del primer pase y segundo pase en VIIRS 750.
Caso sintético que ejercita EXACTAMENTE las dos funciones que process_viirs_mod.py llama (l. 882 y
l. 932) con los flags efectivos de mirova_equivalent (01_flags_efectivos.txt): primer pase
first_pass_tests_2_and_3 (apply_bt_gate por defecto True, el llamador no lo pasa), segundo pase
second_pass_adjacent (conditioned=False, dual ROI, use_prose_branch=True), sin compuerta de BT.

Fenómeno: un píxel de cumbre cuyo MIR está apenas 2 K sobre el anillo (bajo la compuerta de 3 K)
pero con contraste de NTI y ETI claro frente a sus 8 vecinos (su TIR no sube: la lava sub-píxel
brilla en MIR, no en TIR). Escena 67x67 a 270 K con ruido pequeño, ROI 50x50 km, inner 5 km.

Pregunta 1: si la compuerta no actuara, el caso A (bump 2 K) saldría en el primer pase; si el
segundo pase llevara compuerta, el píxel no saldría nunca. Control positivo: caso B (bump 6 K) sale
en el primer pase. Pregunta 2: si las funciones no corrieran, no habría diag (excepción)."""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ["VRP_PROFILE"] = "mirova_equivalent"
sys.path.insert(0, os.getcwd())
import numpy as np
from pipeline.detection_context import first_pass_tests_2_and_3, second_pass_adjacent, roi1_summit_mask, compute_nti_and_nti_app
from pipeline.process_viirs_mod import bt_to_spectral_radiance, M13_LAMBDA, M15_LAMBDA
import pipeline.profile as P

N = 101; r0 = c0 = 50   # 75 km de lado: el ROI de 50x50 km queda adentro y hay sitio fuera del ROI
rng = np.random.default_rng(7)
yy, xx = np.mgrid[0:N, 0:N]
dist_km = np.hypot(yy - r0, xx - c0) * 0.75          # píxel de 750 m
roi_mask = (np.abs(yy - r0) * 0.75 <= 25) & (np.abs(xx - c0) * 0.75 <= 25)
inner_km = 5.0
is_summit = roi1_summit_mask(dist_km, inner_km, None)

def escena(bump_mir_k, bump_tir_k=0.0, sigma_k=0.15, pos=(r0, c0)):
    bt_tir = 270.0 + rng.normal(0, sigma_k, (N, N))
    bt_mir = bt_tir + rng.normal(0, sigma_k, (N, N))
    bt_mir[pos] += bump_mir_k; bt_tir[pos] += bump_tir_k
    L_mir = bt_to_spectral_radiance(bt_mir, M13_LAMBDA); L_tir = bt_to_spectral_radiance(bt_tir, M15_LAMBDA)
    nti = (L_mir - L_tir) / (L_mir + L_tir)
    _, nti_app = compute_nti_and_nti_app(rad_mir=L_mir, bt_tir=bt_tir, lambda_mir_um=M13_LAMBDA, lambda_tir_um=M15_LAMBDA)
    ring = (dist_km >= 5) & (dist_km <= 25)
    t_bg = float(np.median(bt_mir[ring]))      # process_viirs_mod usa compute_bg_stats sobre el anillo 5-25 km
    return nti, nti_app, bt_mir, t_bg

def correr(nombre, bump, apply_gate=True, pos=(r0, c0)):
    nti, nti_app, bt_mir, t_bg = escena(bump, pos=pos)
    kw = dict(c1_dnti_summit=P.DNTI_CONTEXTUAL_C1_SUMMIT, c1_deti_summit=P.DNTI_CONTEXTUAL_C1_SUMMIT,
              c2_dnti_summit=P.C2_DNTI_SUMMIT_NIGHT, c2_deti_summit=P.C2_DNTI_SUMMIT_NIGHT, inner_km=inner_km,
              c1_dnti_scene=P.DNTI_CONTEXTUAL_C1_SCENE, c1_deti_scene=P.DNTI_CONTEXTUAL_C1_SCENE,
              c2_dnti_scene=P.C2_DNTI_SCENE_NIGHT, c2_deti_scene=P.C2_DNTI_SCENE_NIGHT,
              unsuitable_dnti_floor=-0.1, unsuitable_deti_floor=-0.1, use_prose_branch=P.ENABLE_TESTS_23_PROSE_BRANCH)
    fp, diag = first_pass_tests_2_and_3(nti=nti, nti_app=nti_app, bt=bt_mir, roi_mask=roi_mask, dist_km=dist_km,
                                        t_bg=t_bg, bt_sanity_k=P.NTI_BT_SANITY_K, apply_bt_gate=apply_gate, **kw)
    sp = second_pass_adjacent(nti=nti, eti=diag["eti"], active_mask=fp,
                              c1_dnti=P.DNTI_CONTEXTUAL_C1_SUMMIT, c1_deti=P.DNTI_CONTEXTUAL_C1_SUMMIT,
                              c2_dnti=P.C2_DNTI_SUMMIT_NIGHT, c2_deti=P.C2_DNTI_SUMMIT_NIGHT,
                              is_summit=is_summit, c1_dnti_scene=P.DNTI_CONTEXTUAL_C1_SCENE, c1_deti_scene=P.DNTI_CONTEXTUAL_C1_SCENE,
                              c2_dnti_scene=P.C2_DNTI_SCENE_NIGHT, c2_deti_scene=P.C2_DNTI_SCENE_NIGHT,
                              conditioned=P.ENABLE_SECOND_PASS_CONDITIONED, use_prose_branch=P.ENABLE_TESTS_23_PROSE_BRANCH)
    sp_cond = second_pass_adjacent(nti=nti, eti=diag["eti"], active_mask=fp,
                              c1_dnti=P.DNTI_CONTEXTUAL_C1_SUMMIT, c1_deti=P.DNTI_CONTEXTUAL_C1_SUMMIT,
                              c2_dnti=P.C2_DNTI_SUMMIT_NIGHT, c2_deti=P.C2_DNTI_SUMMIT_NIGHT,
                              is_summit=is_summit, c1_dnti_scene=P.DNTI_CONTEXTUAL_C1_SCENE, c1_deti_scene=P.DNTI_CONTEXTUAL_C1_SCENE,
                              c2_dnti_scene=P.C2_DNTI_SCENE_NIGHT, c2_deti_scene=P.C2_DNTI_SCENE_NIGHT,
                              conditioned=True, use_prose_branch=P.ENABLE_TESTS_23_PROSE_BRANCH)
    bt_pix = bt_mir[pos]; gate_ok = bt_pix > t_bg + P.NTI_BT_SANITY_K
    mean8 = np.nanmean(np.delete(nti[pos[0]-1:pos[0]+2, pos[1]-1:pos[1]+2].ravel(), 4))
    dnti_pix = nti[pos] - mean8
    thr_sum = max(P.DNTI_CONTEXTUAL_C1_SUMMIT, diag["mu_dnti"] + P.C2_DNTI_SUMMIT_NIGHT * diag["sd_dnti"])
    print(f"\n{nombre}: bump MIR {bump:+.1f} K en {pos} | bt_pix={bt_pix:.2f} t_bg={t_bg:.2f} compuerta(bt>t_bg+3)={gate_ok} "
          f"| dNTI_pix={dnti_pix:.4f} umbral summit max(C1, mu+5sd)={thr_sum:.4f}")
    print(f"   primer pase: n={int(fp.sum())} (pixel objetivo {'SI' if fp[pos] else 'NO'}) | "
          f"segundo pase (produccion, conditioned=False): n={int(sp.sum())} (pixel objetivo {'SI' if sp[pos] else 'NO'}, nuevos={int((sp & ~fp).sum())}) | "
          f"segundo pase conditioned=True: n={int(sp_cond.sum())} (pixel objetivo {'SI' if sp_cond[pos] else 'NO'})")
    return fp, sp

print("Flags efectivos:", dict(SECOND_PASS=P.ENABLE_SECOND_PASS_ADJACENT, CONDITIONED=P.ENABLE_SECOND_PASS_CONDITIONED,
      PROSE=P.ENABLE_TESTS_23_PROSE_BRANCH, BT_SANITY_K=P.NTI_BT_SANITY_K, NO_BT_GATE_V375=P.ENABLE_TESTS_23_NO_BT_GATE_VIIRS375))
correr("CASO A (bloqueado por la compuerta)", 2.0)
correr("CASO A' (misma escena, compuerta apagada en el primer pase, apply_bt_gate=False)", 2.0, apply_gate=False)
correr("CASO B (CONTROL POSITIVO, pasa la compuerta)", 6.0)
correr("CASO C (bump 2 K FUERA del inner, a 15 km: umbral scene max(0.01, mu+10sd))", 2.0, pos=(r0, c0 + 20))
correr("CASO D (bump 2 K fuera del ROI de 50x50 km, a 30 km)", 2.0, pos=(r0, c0 + 40))
correr("CASO E (nulo: sin bump)", 0.0)
