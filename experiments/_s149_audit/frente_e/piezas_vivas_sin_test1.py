# Frente E S149. Que piezas PROPIAS siguen dejando huella en los records cuando el Test 1 integrado esta apagado.
# Fuente: run 35599902448 (mayo 2026, 2026-05-01 a 2026-05-31, 11 Tier A), brazos B (_s146_ab_sin_test1, conectiva min)
# y F (_s147_ab_sin_test1_max). Denominador: records con primary_cluster y pc.vrp_mw > 0 (lo que podria publicarse).
# P1 (si lo medido estuviera roto, lo veria?): mido MARCAS persistidas, no comportamiento; una pieza que actua sin dejar
#     marca (compuerta de 3 K, recorte a cero, mediana del anillo) NO se ve aca y se declara aparte.
# P2 (instrumento muerto?): control positivo = triggered_test1 debe ser 0 en ambos brazos (el flag esta apagado) y
#     diag_n_first_pass_pixels debe caer de B a F (max es mas estricto). Si no, el instrumento no lee lo que dice.
import json, glob, sys, io, os, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
base = sys.argv[1]
def bucket(s):
    s = (s or "").upper()
    if s.startswith("MODIS"): return "MODIS"
    return "V750" if s.endswith("_750") else "V375"
out = {}
for brazo in ("_s146_ab_sin_test1", "_s147_ab_sin_test1_max"):
    C = collections.defaultdict(collections.Counter)
    for f in sorted(glob.glob(os.path.join(base, brazo, "*.json"))):
        for r in json.load(open(f, encoding="utf-8"))["records"]:
            b = bucket(r.get("sensor")); c = C[b]; c["records"] += 1
            if r.get("triggered_test1"): c["triggered_test1 (control, debe ser 0)"] += 1
            if r.get("final_hotspot_source") == "test1": c["source=test1 (control, debe ser 0)"] += 1
            if (r.get("diag_n_first_pass_pixels") or 0) > 0: c["con pixeles de 1er pase"] += 1
            if (r.get("diag_n_first_pass_pixels") or 0) == 0 and (r.get("diag_n_second_pass_recapture") or 0) > 0: c["deteccion SOLO del 2do pase (2do pase sin condicionar)"] += 1
            pc = r.get("primary_cluster")
            if not pc or (pc.get("vrp_mw") or 0) <= 0: continue
            c["con cumulo y vrp>0 (DENOMINADOR)"] += 1
            if r.get("distance_class") == "summit": c["  summit (publicable por mirovaEqVrp, sin mirar inner)"] += 1
            if pc.get("single_pixel_mode"): c["  single_pixel_mode"] += 1
            if pc.get("focal_magnitude"): c["  focal_magnitude"] += 1
            if pc.get("d9_capped"): c["  d9_capped (tope 5 MW)"] += 1
            if abs((pc.get("vrp_mw") or 0) - (r.get("vrp_mir_mw") or 0)) > 1e-3: c["  pc.vrp != suma de escena (vrp_mir_mw)"] += 1
            f5 = r.get("f5_core_vrp_mw")
            if isinstance(f5, (int, float)):
                c["  con f5_core"] += 1
                if abs(f5 - pc["vrp_mw"]) > 1e-3: c["  f5_core != pc.vrp"] += 1
            if r.get("discarded_reason"): c["  discarded_reason no nulo: " + str(r["discarded_reason"])] += 1
            if (r.get("diag_n_first_pass_pixels") or 0) == 0: c["  publicable y SOLO 2do pase"] += 1
    out[brazo] = {b: dict(c) for b, c in C.items()}
    print("=====", brazo)
    for b in ("V375", "V750", "MODIS"):
        print("--", b)
        for k, v in C[b].items(): print(f"   {k}: {v}")
json.dump(out, open("experiments/_s149_audit/frente_e/piezas_vivas_sin_test1.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
