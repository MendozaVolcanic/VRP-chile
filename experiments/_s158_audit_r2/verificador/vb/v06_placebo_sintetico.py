"""VB v06: la regla M del evaluador de D25 frente a brazos placebo, con pares SINTETICOS (ni A/B ni produccion).

Camino distinto al del auditor (que copio las funciones y uso pares reales de produccion): aca extraigo las funciones
del archivo REAL experiments/_s157_prereg_d25/evaluar_d25.py con ast (si alguien las cambia, esto mide el cambio) y
genero pares con un sesgo de K conocido. La pregunta: el veredicto de M sobre un brazo que SOLO multiplica la magnitud
depende del signo del sesgo de K contra MIROVA, no de ninguna fisica del brazo?

Diseno: 60 bloques noche-volcan, 3 pares por bloque, 4 volcanes; log10(K/M) ~ N(mu, 0.25) con mu en {log10 0.67, 0, log10 1.3}.
Brazos: D = g*K con g en {0.8, 1.0, 1.2}. Calibracion sellada (calibrar) y simetrica (calibrar_simetrico), mas la regla
de >= 2 volcanes con mediana de d negativa (opcion A de la adenda).
Pregunta 1: si M fuera inmune a una ganancia pura, g=1,2 daria NEUTRO para cualquier mu. Pregunta 2: control de
instrumento: g=1,0 tiene que dar d=0 exacto (NEUTRO) y mu=0 con g=1,2 tiene que dar EMPEORA (alejarse de MIROVA).
"""
import ast, sys, io, os, collections, math
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
src = open(os.path.join(REPO, "experiments/_s157_prereg_d25/evaluar_d25.py"), encoding="utf-8").read()
tree = ast.parse(src)
quiero = {"pesos_bloque", "medianas_ponderadas", "regla_m", "d_par", "calibrar", "calibrar_simetrico"}
ns = {"np": np, "collections": collections, "math": math}
for nodo in tree.body:
    if isinstance(nodo, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ("N_BOOT", "SEMILLA", "N_CALIB", "MAX_FALSOS_CALIB")
                                           for t in (nodo.targets[0].elts if isinstance(nodo.targets[0], ast.Tuple) else nodo.targets)):
        exec(compile(ast.Module([nodo], []), "evaluar_d25", "exec"), ns)
    if isinstance(nodo, ast.FunctionDef) and nodo.name in quiero:
        exec(compile(ast.Module([nodo], []), "evaluar_d25", "exec"), ns)
assert quiero <= set(ns), quiero - set(ns)
print("constantes leidas del evaluador:", {k: ns[k] for k in ("N_BOOT", "SEMILLA", "N_CALIB", "MAX_FALSOS_CALIB")})
ns["N_BOOT"] = 2000   # menos replicas para el tiempo; se informa
rng = np.random.default_rng(2026)
def pares(mu):
    out = []
    for b in range(60):
        vol = "V%d" % (b % 4)
        for j in range(3):
            m = 10 ** rng.normal(0, 0.5)
            k = m * 10 ** rng.normal(mu, 0.25)
            out.append({"k": k, "m": m, "bloque": "%s|%d" % (vol, b), "vol": vol})
    return out
for mu_nom, mu in (("K bajo MIROVA (0,67)", math.log10(0.67)), ("K centrado (1,0)", 0.0), ("K sobre MIROVA (1,3)", math.log10(1.3))):
    P0 = pares(mu)
    for g in (0.8, 1.0, 1.2):
        P = [dict(p, d=g * p["k"]) for p in P0]
        d = np.array([ns["d_par"](p["k"], p["d"], p["m"]) for p in P])
        bl = [p["bloque"] for p in P]
        W = ns["pesos_bloque"](bl, n_boot=2000)
        r, lo, hi = ns["regla_m"](d, W)
        fm, fe, pod = ns["calibrar"](P, W, bl, n_rep=200)
        sm, se, spod = ns["calibrar_simetrico"](d, W, bl, n_rep=200)
        vneg = sum(float(np.median([x for x, p in zip(d, P) if p["vol"] == v])) < 0 for v in ("V0", "V1", "V2", "V3"))
        sell = "INDECIDIBLE" if fm + fe > ns["MAX_FALSOS_CALIB"] else r
        sim = ("INDECIDIBLE" if (sm > 0.05 or se > 0.05) else ("NEUTRO" if (r == "MEJORA" and vneg < 2) else r))
        print(f"{mu_nom:22s} g={g:.1f}: regla={r:8s} IC[{lo:+.3f},{hi:+.3f}] | sellada falsos M {fm:.3f} E {fe:.3f} -> {sell:11s} "
              f"| simetrica falsos M {sm:.3f} E {se:.3f}, volcanes d<0 {vneg}/4 -> {sim}")
