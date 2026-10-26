# Tasa real de falsos del placebo c (D-44) sobre la estructura de bloques de W2..W6 con un brazo diurno ruidoso.
import os, sys, random, collections
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
R = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s163-diurno-k-prereg-5c4f44"
sys.path[:0] = [R, R + r"\scripts", R + r"\experiments\_s163_diurno_k"]
import evaluar_diurno_k as ev, nulo_estructural as nu, evaluador_comun as ec
T, sint = nu.armar(sys.argv[1])
rng = random.Random(7)
for q in (0.05, 0.2, 0.5):
    for r in sint:
        p = rng.random() < q
        r["pub"], r["disp"] = p, (0.3 if p else 0.0)
    # re-sincronizar: el brazo diurno de T apunta a los mismos dicts de sint (armar los comparte)
    for s in ev.SENSORES_DIA:
        excl = lambda f, s=s: not ev._sensor_dia(f, s)
        c = collections.Counter()
        B = None
        for sem in range(161, 161 + 400):
            res, det = ec.placebo_p2(T, "diurno", "c", 1.0, sem, excluir=excl)
            c[res] += 1; B = det["B"]
        falsos40 = sum(1 for sem in ev.SEMILLAS_C if True)  # solo para tener el nombre
        # los 40 oficiales
        f40 = 0
        for sem in ev.SEMILLAS_C:
            res, _ = ec.placebo_p2(T, "diurno", "c", 1.0, sem, excluir=excl)
            f40 += res in ("GANA", "PIERDE")
        tasa = (c["GANA"] + c["PIERDE"]) / 400
        from scipy.stats import binom
        print("q=%.2f %s: B=%d | 400 semillas %s | tasa GANA o PIERDE %.3f | las 40 oficiales: %d falsos (max permitido 4) | P(I6 falla) si la tasa fuera esa = %.3f"
              % (q, s, B, dict(c), tasa, f40, binom.sf(4, 40, tasa)))
