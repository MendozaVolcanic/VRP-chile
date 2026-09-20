# Simulacion de la regla de veredicto de la v6 (contra el nivel R, con la incertidumbre de R),
# sobre un nulo con la estructura REAL de noches de la muestra del veredicto (ventana 45-120).
import os, sys, math, pickle
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

D = pickle.load(open(HERE + "/c6.pkl", "rb"))
E = pickle.load(open(HERE + "/e6.pkl", "rb"))
F = E[(E.est == "ok") & (E.n_ref >= 3)]
NN = F.groupby("vol").noche.nunique().to_dict()
ELIG = [v for v, n in NN.items() if n >= 20]
print("noches por volcan (muestra v6):", NN, "total", sum(NN.values()))
print("elegibles (>=20 noches):", ELIG)

# --- generador de nulo: bloques (vol, noche) del nulo mas limpio disponible con la ventana v6
na = D["N1a"]; na = na[na.estado == "ok"]
nc = na[(na.vol != "Lastarria") & (na.lab == "neg_limpio")]      # lectura de la v5, ventana v6
blk = {}
for (v, n), g in nc.groupby(["vol", "noche"]):
    blk.setdefault(v, []).append(g.d.values)
todos = [b for v in blk for b in blk[v]]
print("bloques de nulo por volcan:", {v: len(b) for v, b in blk.items()}, " D del nulo %+.4f" % nc.d.mean())

# --- muestra de R: bloques (vol, noche) del estrato hermano con la ventana v6
ro = D["R"]; ro = ro[ro.estado == "ok"]
rblk = [g.d.values for _, g in ro.groupby([ro.vol, ro.noche])]
print("bloques de R:", len(rblk), " R agrupado %+.4f" % ro.d.mean())


def boot_ic(vals_por_vol, Bn=300, rng=None):
    out = []
    for _ in range(Bn):
        allv = []
        for v, blocks in vals_por_vol.items():
            sel = rng.integers(0, len(blocks), len(blocks))
            allv.append(np.concatenate([blocks[i] for i in sel]))
        out.append(float(np.mean(np.concatenate(allv))))
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def boot_simple(blocks, Bn=300, rng=None, shift=0.0):
    out = []
    n = len(blocks)
    for _ in range(Bn):
        sel = rng.integers(0, n, n)
        out.append(float(np.mean(np.concatenate([blocks[i] for i in sel]))) + shift)
    return float(np.mean(out)), float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def sim(rep=200, delta_D=0.0, delta_R=0.0, seed=7, r_blocks=None, r_scale=1,
        orden="positivo_primero"):
    """delta_D: senal inyectada en la muestra del veredicto. delta_R: senal en el estrato hermano.
    r_scale: submuestrea los bloques de R para ensanchar su intervalo."""
    rng = np.random.default_rng(seed)
    rb = r_blocks if r_blocks is not None else rblk
    if r_scale > 1:
        rb = rb[::r_scale]
    res = []
    for _ in range(rep):
        vals = {}
        for v, nn in NN.items():
            pool = blk.get(v) or todos
            if len(pool) < 3:
                pool = todos
            sel = rng.integers(0, len(pool), nn)
            bs = []
            for i in sel:
                d = pool[i].copy()
                if delta_D > 0:
                    fl = rng.random(len(d)) < delta_D
                    d = np.clip(np.where(fl, np.minimum(1.0, d + 1.0), d), -1, 1)
                bs.append(d)
            vals[v] = bs
        lo, hi = boot_ic(vals, rng=rng)
        Dm = float(np.mean(np.concatenate([np.concatenate(b) for b in vals.values()])))
        Dv = {v: float(np.mean(np.concatenate(b))) for v, b in vals.items()}
        # R con su propio error, remuestreado en la misma corrida
        sel = rng.integers(0, len(rb), len(rb))
        rsamp = [rb[i] for i in sel]
        Rp, Rlo, Rhi = boot_simple(rsamp, rng=rng, shift=delta_R)
        c2 = (sum(1 for v in ELIG if Dv[v] > 0) >= math.ceil(2 / 3 * len(ELIG))) if ELIG else None
        pos = (lo > max(0.05, Rhi)) and bool(c2)
        equ = (lo >= Rp - 0.05) and (hi <= Rp + 0.05)
        if orden == "positivo_primero":
            ver = "cae sobre un exceso" if pos else ("no se distingue" if equ else "INCONCLUSO")
        else:
            ver = "no se distingue" if equ else ("cae sobre un exceso" if pos else "INCONCLUSO")
        res.append((ver, Dm, lo, hi, hi - lo, Rp, Rlo, Rhi, Rhi - Rlo, pos, equ))
    return pd.DataFrame(res, columns=["ver", "D", "lo", "hi", "ancho", "Rp", "Rlo", "Rhi", "Ranch", "pos", "equ"])


print("\n== 1. NULO puro (sin senal en ninguno de los dos), regla v6 ==")
r = sim(rep=200)
print("  ", r.ver.value_counts().to_dict(),
      " D %+.4f ancho %.4f | R %+.4f ancho %.4f | ambas condiciones a la vez: %d" %
      (r.D.mean(), r.ancho.mean(), r.Rp.mean(), r.Ranch.mean(), int((r.pos & r.equ).sum())))

print("\n== 2. potencia: senal SOLO en la muestra del veredicto (R limpio) ==")
for dl in (0.02, 0.05, 0.08, 0.10, 0.15, 0.20):
    r = sim(rep=120, delta_D=dl, seed=11)
    vc = r.ver.value_counts()
    print("  dD=%.3f D=%+.3f -> exceso %3d%%  no se distingue %3d%%  INCONCLUSO %3d%%  (ambas %d)"
          % (dl, r.D.mean(), vc.get("cae sobre un exceso", 0) * 100 // 120,
             vc.get("no se distingue", 0) * 100 // 120, vc.get("INCONCLUSO", 0) * 100 // 120,
             int((r.pos & r.equ).sum())))

print("\n== 3. el fenomeno esta en los DOS estratos por igual (senal uniforme) ==")
for dl in (0.02, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30):
    r = sim(rep=100, delta_D=dl, delta_R=dl, seed=13)
    vc = r.ver.value_counts()
    print("  dD=dR=%.3f D=%+.3f R=%+.3f -> exceso %3d%%  no se distingue %3d%%  INCONCLUSO %3d%%"
          % (dl, r.D.mean(), r.Rp.mean(), vc.get("cae sobre un exceso", 0),
             vc.get("no se distingue", 0), vc.get("INCONCLUSO", 0)))

print("\n== 4. que pasa si el intervalo de R es ancho (submuestreo de sus bloques) ==")
for sc in (1, 3, 6, 12, 25):
    r = sim(rep=100, r_scale=sc, seed=17)
    vc = r.ver.value_counts()
    print("  1 de cada %2d bloques de R (n=%3d): ancho de R %.3f  ->  nulo: %s"
          % (sc, len(rblk[::sc]), r.Ranch.mean(), vc.to_dict()))
    r2 = sim(rep=100, r_scale=sc, delta_D=0.15, seed=19)
    print("      con senal 0,15 solo en el veredicto: %s" % r2.ver.value_counts().to_dict())

print("\n== 5. que pasa si R esta desplazado hacia arriba (residuo real del instrumento) ==")
for dR in (0.0, 0.03, 0.05, 0.08, 0.12):
    r = sim(rep=100, delta_R=dR, seed=23)
    r2 = sim(rep=100, delta_R=dR, delta_D=dR, seed=29)
    print("  R=+%.2f  nulo puro (D=0): %-60s | D=R=+%.2f: %s"
          % (dR, str(r.ver.value_counts().to_dict()), dR, str(r2.ver.value_counts().to_dict())))

print("\n== 6. orden de las dos condiciones (zona donde las dos se cumplen) ==")
for dl in (0.06, 0.08, 0.10):
    a = sim(rep=100, delta_D=dl, delta_R=0.03, seed=31, orden="positivo_primero")
    b = sim(rep=100, delta_D=dl, delta_R=0.03, seed=31, orden="equivalencia_primero")
    print("  dD=%.2f dR=0,03: positivo primero %-55s | equivalencia primero %s"
          % (dl, str(a.ver.value_counts().to_dict()), str(b.ver.value_counts().to_dict())))
    print("      repeticiones donde las DOS condiciones se cumplen: %d de 100" % int((a.pos & a.equ).sum()))
