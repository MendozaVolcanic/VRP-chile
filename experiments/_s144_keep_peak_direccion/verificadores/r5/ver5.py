# Simulacion de la regla de veredicto de la v5 S7 sobre un nulo con la estructura REAL
# (noches por volcan de la muestra final con imagen cruzada). Solo lectura.
import os, sys, math, pickle
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

D = pickle.load(open(HERE + "/cruz5.pkl", "rb"))
nul = D["null"]; nul = nul[nul.estado == "ok"].copy()
E = pickle.load(open(HERE + "/embudo5.pkl", "rb"))
F = E[(E.est == "ok") & (E.n_ref >= 3)]
NN = F.groupby("vol").noche.nunique().to_dict()
print("noches por volcan en la muestra final:", NN, " total", sum(NN.values()))
print("volcanes con >=20 noches:", [v for v, n in NN.items() if n >= 20])

# bloques del nulo por (vol, noche)
blk = {}
for (v, n), g in nul.groupby(["vol", "noche"]):
    blk.setdefault(v, []).append(g.d.values)
todos = [b for v in blk for b in blk[v]]
print("bloques de nulo por volcan:", {v: len(b) for v, b in blk.items()})


def boot_ic(vals_por_vol, Bn=400, rng=None):
    out = []
    for _ in range(Bn):
        allv = []
        for v, blocks in vals_por_vol.items():
            sel = rng.integers(0, len(blocks), len(blocks))
            allv.append(np.concatenate([blocks[i] for i in sel]))
        out.append(float(np.mean(np.concatenate(allv))))
    return np.percentile(out, [2.5, 97.5])


def simula(rep=200, delta=0.0, vols_senal=None, seed=7, cond2_vacio=False):
    rng = np.random.default_rng(seed)
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
                dl = delta if (vols_senal is None or v in vols_senal) else 0.0
                if dl > 0:
                    # inyecta senal: sube e a 1 con prob dl (d sube en 1-e)
                    fl = rng.random(len(d)) < dl
                    d = np.where(fl, np.minimum(1.0, d + 1.0), d)
                    d = np.clip(d, -1, 1)
                bs.append(d)
            vals[v] = bs
        lo, hi = boot_ic(vals, rng=rng)
        Dv = {v: float(np.mean(np.concatenate(b))) for v, b in vals.items()}
        elig = [v for v in NN if NN[v] >= 20]
        if not elig:
            c2 = cond2_vacio
        else:
            c2 = sum(1 for v in elig if Dv[v] > 0) >= math.ceil(2 / 3 * len(elig))
        Dm = float(np.mean(np.concatenate([np.concatenate(b) for b in vals.values()])))
        ver = ("cae sobre un exceso" if (lo > 0.05 and c2)
               else "no se distingue" if (lo >= -0.05 and hi <= 0.05) else "INCONCLUSO")
        res.append((ver, Dm, lo, hi, hi - lo, c2))
    return pd.DataFrame(res, columns=["ver", "D", "lo", "hi", "ancho", "c2"])


print("\n== la regla de la v5 S7 sobre el NULO, con la estructura real (200 rep) ==")
r0 = simula()
print("  ", r0.ver.value_counts().to_dict(), " D medio %+.4f  ancho medio del IC %.4f" % (r0.D.mean(), r0.ancho.mean()))

print("\n== potencia (senal uniforme en todos los volcanes) ==")
for delta in (0.02, 0.025, 0.05, 0.08, 0.10, 0.15):
    r = simula(rep=120, delta=delta, seed=11)
    vc = r.ver.value_counts()
    print("  delta=%.3f  D=%+.3f  exceso %3d%%  no se distingue %3d%%  INCONCLUSO %3d%%"
          % (delta, r.D.mean(), vc.get("cae sobre un exceso", 0) * 100 // 120,
             vc.get("no se distingue", 0) * 100 // 120, vc.get("INCONCLUSO", 0) * 100 // 120))

print("\n== senal concentrada en 2 volcanes (Villarrica y Chaiten) ==")
for delta in (0.20, 0.40, 0.60):
    r = simula(rep=100, delta=delta, vols_senal={"Villarrica", "Chaiten"}, seed=13)
    print("  delta=%.2f  D=%+.3f -> %s" % (delta, r.D.mean(), r.ver.value_counts().to_dict()))

print("\n== tramo posterior a #535 aislado ==")
NN_post = F[F.tramo == "post"].groupby("vol").noche.nunique().to_dict()
NN_pre = F[F.tramo == "pre"].groupby("vol").noche.nunique().to_dict()
for nom, d_ in (("pre", NN_pre), ("post", NN_post)):
    NN_bak = dict(NN)
    NN.clear(); NN.update(d_)
    for cv in (True, False):
        r = simula(rep=80, seed=5, cond2_vacio=cv)
        print("  tramo %-4s (%d noches, elegibles>=20: %d) cond2_vacia=%s -> %s  ancho %.3f"
              % (nom, sum(d_.values()), sum(1 for x in d_.values() if x >= 20), cv,
                 r.ver.value_counts().to_dict(), r.ancho.mean()))
        if sum(1 for x in d_.values() if x >= 20) > 0:
            break
    NN.clear(); NN.update(NN_bak)
