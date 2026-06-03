#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verify that numbers cited in tupun_mechanism.md match canonical JSON sources.
Fails loudly if any drift. (Regla S91: no numeros transcritos a mano sin verificacion.)"""
import sys, io, json, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
md = open(os.path.join(HERE, 'tupun_mechanism.md'), encoding='utf-8').read()
can = json.load(open(os.path.join(HERE, 'canonical_numbers.json')))
tif = json.load(open(os.path.join(HERE, 'tif_analysis.json')))

checks = []
def chk(name, cond):
    checks.append((name, bool(cond)))

# Monthly medians cited in table
chk("v375_n=514", "514" in md and can['v375_n'] == 514)
chk("mar pc_npx_med=2", can['monthly']['2026-03']['pc_npx_med'] == 2)
chk("apr pc_npx_med=23", can['monthly']['2026-04']['pc_npx_med'] == 23 and "23" in md)
chk("may pc_npx_med=45", can['monthly']['2026-05']['pc_npx_med'] == 45 and "45" in md)
chk("may pc_vrp_med=1.82", abs(can['monthly']['2026-05']['pc_vrp_med'] - 1.824) < 1e-3 and "1.82" in md)
chk("big_n=258", can['big_n'] == 258 and "258" in md)
chk("big_test1_all", can['big_test1_true'] == can['big_n'])
chk("tbg min 261.1", abs(can['big_tbg']['min'] - 261.1) < 0.05 and "261.1" in md)
chk("tbg med 266.1", abs(can['big_tbg']['med'] - 266.1) < 0.05 and "266.1" in md)
chk("tbg max 273.6", abs(can['big_tbg']['max'] - 273.6) < 0.05 and "273.6" in md)
chk("tbg below270=235", can['big_tbg']['below270'] == 235 and "235" in md)
chk("tbg 270-290=23", can['big_tbg']['r270_290'] == 23)
# TIF: ~17900 positives, peak far
chk("TIF n_pos ~17900", any(t.get('n_positive', 0) > 17000 for t in tif) and "17,900" in md)
chk("TIF peak far (>13km)", any(t.get('peak_dist_crater_km', 0) > 13 for t in tif))
chk("TIF within7km ~1095", any(t.get('n_pos_within_7km') == 1095 for t in tif) and "1095" in md)

ok = all(c for _, c in checks)
for name, c in checks:
    print(("PASS" if c else "FAIL"), name)
print("\nALL PASS" if ok else "\n*** SOME CHECKS FAILED ***")
sys.exit(0 if ok else 1)
