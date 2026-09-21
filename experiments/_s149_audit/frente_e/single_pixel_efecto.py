# Frente E S149: en el brazo F (sin Test 1, max), mayo 2026, cuantos cumulos publicables tienen >1 pixel, que es donde
# "publicar el maximo" (single_pixel_mode) difiere de "sumar" (Ec. 8 del paper). Denominador: summit con pc.vrp>0.
# P1: si single_pixel_mode no actuara, n_pixels>1 con marca seria 0 -> lo veria. P2: control = n total por sensor impreso.
import json, glob, sys, io, os, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
base = sys.argv[1]
for brazo in ("_s146_ab_sin_test1", "_s147_ab_sin_test1_max"):
    C = collections.defaultdict(collections.Counter)
    for f in glob.glob(os.path.join(base, brazo, "*.json")):
        for r in json.load(open(f, encoding="utf-8"))["records"]:
            s = (r.get("sensor") or "").upper()
            b = "MODIS" if s.startswith("MODIS") else ("V750" if s.endswith("_750") else "V375")
            pc = r.get("primary_cluster")
            if not pc or (pc.get("vrp_mw") or 0) <= 0 or r.get("distance_class") != "summit": continue
            C[b]["summit con vrp>0"] += 1
            n = pc.get("n_pixels") or 0
            C[b][f"n_pixels={'1' if n==1 else '2-3' if n<=3 else '4+'}"] += 1
            if pc.get("single_pixel_mode") and n > 1: C[b]["single_pixel_mode Y n>1 (publica max, no suma)"] += 1
    print("==", brazo)
    for b in C: print("  ", b, dict(C[b]))
