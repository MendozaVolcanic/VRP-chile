"""VS34 V-4 parte C: con datos existentes de los 11 (origin/main 14fb62030, data/mirova_equivalent/<volcan>.json, detector K,
records de noche), cuanto del tiempo estan activos los 4 vecinos Tier A de los 34 (Villarrica->Quetrupillan, Chaiten->Michinmahuida,
PuyehueCordonCaulle->Antillanca, Copahue->Callaqui) y que tan seguro es que su calor pasaria los pisos de la via en una BOX 0.
Q1: si el vecino estuviera activo, esto lo ve (control positivo: Villarrica tiene pasadas con pc.vrp>0). Q2: si el archivo
estuviera vacio/ilegible, n=0 y se imprime.
Limite (ESTIMACION): K mide pixeles de barrido, la via mide una grilla interpolada (V750-C: la interpolacion diluye un pixel
aislado). Los pisos de la via en BOX 0 son dNTI>=0.02 y dETI>=0.01, mas mu+10*sd de la grilla; aqui se usa como proxy
dNTI = nti_max - nti_bg y sd = diag_nti_std. NTI absoluto > -0.7 (Test 1 de la via) alerta en cualquier celda no-NaN."""
import json, subprocess, statistics as st, collections
R = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
VENTANA = ("2026-08-01", "2026-10-31")
def fam(s):
    if s.startswith("MODIS"): return "MODIS"
    return "VIIRS750" if s.endswith("_750") else "VIIRS375"
for vol, vecino in (("Villarrica", "Quetrupillan"), ("Chaiten", "Michinmahuida"), ("PuyehueCordonCaulle", "AntillancaCasablanca"), ("Copahue", "Callaqui")):
    p = subprocess.run(["git", "-C", R, "show", f"14fb62030:data/mirova_equivalent/{vol}.json"], capture_output=True)
    d = json.loads(p.stdout)
    recs = [r for r in d["records"] if VENTANA[0] <= r["datetime_utc"][:10] <= VENTANA[1]]
    print(f"\n== {vol} (vecino de {vecino}): {len(recs)} records en {VENTANA} (denominador: pasadas nocturnas procesadas por K)")
    por = collections.defaultdict(list)
    for r in recs: por[fam(r["sensor"])].append(r)
    for f, rs in sorted(por.items()):
        def vrp(r):
            if f == "VIIRS375" and r.get("f5_core_vrp_mw") is not None: return r["f5_core_vrp_mw"]
            return (r.get("primary_cluster") or {}).get("vrp_mw") or 0.0
        pos = [vrp(r) for r in rs if vrp(r) > 0]
        t1 = [r for r in rs if (r.get("diag_nti_max") if r.get("diag_nti_max") is not None else -9) > -0.7]
        floor = []
        for r in rs:
            m, b, s = r.get("diag_nti_max"), r.get("diag_nti_bg"), r.get("diag_nti_std")
            if None in (m, b, s): continue
            floor.append((m - b) > max(0.02, 10 * s))
        print(f"  {f:8s} n={len(rs):4d} | con VRP>0: {len(pos):4d} ({100*len(pos)/len(rs):4.1f} %) mediana VRP>0: {st.median(pos) if pos else float('nan'):6.3f} MW"
              f" | NTI abs > -0.7 (Test 1): {len(t1):4d} ({100*len(t1)/len(rs):4.1f} %)"
              f" | proxy piso BOX0 (dNTI>max(0.02,10sd)): {sum(floor):4d} de {len(floor)} con dato ({100*sum(floor)/max(len(floor),1):4.1f} %)")
