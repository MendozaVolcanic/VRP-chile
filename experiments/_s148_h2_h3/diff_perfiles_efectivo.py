# -*- coding: utf-8 -*-
"""Diferencia EFECTIVA entre los brazos B y F: lee pipeline.profile (no el YAML) en dos procesos.

Uso, desde la raiz del repo: python experiments/_s148_h2_h3/diff_perfiles_efectivo.py
"""
import json
import os
import subprocess
import sys

COD = ("import pipeline.profile as p, json, sys;"
       "sys.stdout = sys.__stdout__;"
       "print('@@' + json.dumps({k: repr(getattr(p, k)) for k in dir(p) if k.isupper() and k != 'VALID_PROFILES'}))")
res = {}
for perfil in ("_s146_ab_sin_test1", "_s147_ab_sin_test1_max"):
    env = dict(os.environ, VRP_PROFILE=perfil)
    out = subprocess.run([sys.executable, "-c", COD], env=env, capture_output=True, text=True).stdout
    res[perfil] = json.loads([x for x in out.splitlines() if x.startswith("@@")][0][2:])
a, b = res["_s146_ab_sin_test1"], res["_s147_ab_sin_test1_max"]
print("constantes leidas: B", len(a), "| F", len(b))
for k in sorted(set(a) | set(b)):
    if a.get(k) != b.get(k):
        print("  DISTINTA %-32s B %s | F %s" % (k, a.get(k), b.get(k)))
print("flags del segundo pase y de la compuerta, brazo F:")
for k in ("ENABLE_SECOND_PASS_ADJACENT", "ENABLE_SECOND_PASS_CONDITIONED", "ENABLE_TESTS_23_NO_BT_GATE_VIIRS375",
          "NTI_BT_SANITY_K", "ENABLE_FINAL_PIXEL_FILTER", "ENABLE_DUAL_ROI_SECOND_PASS", "ENABLE_LOCAL_KERNEL_BG",
          "DNTI_CONTEXTUAL_C1", "C2_DNTI_SUMMIT_NIGHT"):
    print("   %-38s %s" % (k, b.get(k, "NO EXISTE")))
