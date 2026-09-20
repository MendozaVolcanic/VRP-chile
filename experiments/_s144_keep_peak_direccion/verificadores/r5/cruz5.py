# Instrumento de la v5 S5: imagen de pasada cruzada + sitios de referencia (otros P nuestros).
# Mide: (a) OBS fuera de la muestra del veredicto con imagen cruzada y con imagen propia (C2),
#       (b) C1 intercambio de roles, (c) NULO con punto sorteado, (d) embudo de muestra.
# NO evalua Z en el P de ninguna pasada de la muestra del veredicto.
import os, sys, math, pickle, time, random
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3"); V4 = os.path.abspath(HERE + "/../v4")
sys.path.insert(0, V3); sys.path.insert(0, V4); sys.path.insert(0, HERE)
from common3 import *  # noqa
import base4 as B  # noqa

df = B.df.copy()
df["t"] = pd.to_datetime(df.dt, utc=True)
df["noche"] = df.t.dt.strftime("%Y-%m-%d")
idx_v = B.idx_v
Zc = pickle.load(open(HERE + "/zc5.pkl", "rb"))
zc = Zc["zc"]

SEP_KM = 1.5     # 2T
GAP_D = 3.0
NREF = 5
MINREF = 3
MINGAP_S = 900

# ---- pool de sitios de referencia: P publicados con patron
pubP = df[df.patron & df.pub].copy()
POOL = {v: g[["t", "noche", "P"]].sort_values("t").reset_index(drop=True) for v, g in pubP.groupby("vol")}


def refs_de(vol, t_p, noche_p, P_anchor, sep=SEP_KM):
    g = POOL.get(vol)
    if g is None:
        return []
    la = np.array([p[0] for p in g.P]); lo = np.array([p[1] for p in g.P])
    dn = (pd.to_datetime(g.noche) - pd.Timestamp(noche_p)).dt.days.values
    d = hav(la, lo, P_anchor[0], P_anchor[1])
    ok = (np.abs(dn) > GAP_D) & (d > sep)
    if not ok.any():
        return []
    dt_s = (g.t - t_p).dt.total_seconds().values
    cand = np.where(ok)[0]
    # 5 mas cercanas en el tiempo; empate -> la anterior (dt negativo primero)
    orden = sorted(cand, key=lambda i: (abs(dt_s[i]), dt_s[i]))
    return [(g.P.iloc[i], float(dt_s[i] / 86400.0)) for i in orden[:NREF]]


def cruzada_de(vol, t_p):
    """TIF de otra pasada de la misma noche, |dt|>=15 min, usable. Mas cercana; empate, la anterior."""
    g = idx_v.get(vol)
    if g is None:
        return None, "sin_idx"
    dd = (g.acquisition_utc - t_p).dt.total_seconds()
    m = (g.acquisition_utc.dt.strftime("%Y-%m-%d") == t_p.strftime("%Y-%m-%d")) & (dd.abs() >= MINGAP_S)
    cand = g[m]
    if len(cand) == 0:
        return None, "sin_cruzada"
    dds = dd[m]
    orden = sorted(range(len(cand)), key=lambda i: (abs(dds.iloc[i]), dds.iloc[i]))
    for i in orden:
        r = cand.iloc[i]
        Rr, why = usable({"own": bool(r["own"]), "path": r["path"]}, vol)
        if Rr is not None:
            return (Rr, float(dds.iloc[i]), r["path"]), "ok"
    return None, "cruzada_no_usable"


def propia_de(vol, t_p, tif, own):
    if tif is None or (isinstance(tif, float) and np.isnan(tif)):
        return None
    Rr, why = usable({"own": bool(own), "path": tif}, vol)
    return Rr


def medir(sub, modo, rng=None, usar_propia=False):
    """modo: 'P' (observado = nuestro P) o 'null' (observado = punto sorteado en el anillo)."""
    out = []
    for vol, g in sub.groupby("vol"):
        if vol not in zc.index:
            continue
        v = vent(vol)
        for _, r in g.sort_values("t").iterrows():
            t_p = r["t"]
            if modo == "P":
                X = r["P"]
            else:
                u = rng.random()
                rr = math.sqrt(1.5 ** 2 + u * (3.0 ** 2 - 1.5 ** 2))
                az = rng.uniform(0, 2 * math.pi)
                X = desplazar(v[0], v[1], rr * math.cos(az), rr * math.sin(az))
            R = refs_de(vol, t_p, r["noche"], X)
            if len(R) < MINREF:
                out.append(dict(vol=vol, t=t_p, lab=r["lab"], estado="pocas_refs", n_ref=len(R)))
                continue
            if usar_propia:
                Rr = propia_de(vol, t_p, r["tif"], r["own"])
                if Rr is None:
                    out.append(dict(vol=vol, t=t_p, lab=r["lab"], estado="sin_propia", n_ref=len(R)))
                    continue
                dsep = 0.0
            else:
                cr, why = cruzada_de(vol, t_p)
                if cr is None:
                    out.append(dict(vol=vol, t=t_p, lab=r["lab"], estado=why, n_ref=len(R)))
                    continue
                Rr, dsep, _p = cr
            zo = Z(Rr, X)
            if zo is None:
                out.append(dict(vol=vol, t=t_p, lab=r["lab"], estado="sin_dl0", n_ref=len(R)))
                continue
            zr = [Z(Rr, p) for p, _g in R]
            zr = [x for x in zr if x is not None]
            if len(zr) < MINREF:
                out.append(dict(vol=vol, t=t_p, lab=r["lab"], estado="refs_sin_dl0", n_ref=len(zr)))
                continue
            e = 1.0 * (zo >= zc[vol])
            rr_ = float(np.mean([x >= zc[vol] for x in zr]))
            # C1: intercambio de roles, promediado sobre los 5 papeles posibles
            c1 = []
            for i in range(len(zr)):
                otros = [zr[j] for j in range(len(zr)) if j != i] + [zo]
                c1.append((1.0 * (zr[i] >= zc[vol])) - float(np.mean([x >= zc[vol] for x in otros])))
            out.append(dict(vol=vol, t=t_p, lab=r["lab"], noche=r["noche"], estado="ok",
                            e=e, r=rr_, d=e - rr_, n_ref=len(zr), dsep_min=dsep / 60.0,
                            zobs=zo, zref=zr, c1=float(np.mean(c1)),
                            sep_ref_d=float(np.median([abs(gg) for _p, gg in R]))))
        raster.cache_clear()
    return pd.DataFrame(out)


if __name__ == "__main__":
    t0 = time.time()
    # ---------- A. fuera de la muestra del veredicto (far_ref + sin_info, sin Lastarria)
    OUT = df[df.patron & df.pub & (df.vol != "Lastarria") & df.lab.isin(["far_ref", "sin_info"])].copy()
    print("== fuera de la muestra del veredicto (la v5 S5 dice 194): %d ==" % len(OUT))
    print("  ", OUT.groupby(["lab"]).size().to_dict(), OUT.vol.value_counts().to_dict())

    a_cross = medir(OUT, "P", usar_propia=False)
    print("\n-- OBS con imagen CRUZADA --", time.time() - t0)
    print(a_cross.estado.value_counts().to_dict())
    a_own = medir(OUT, "P", usar_propia=True)
    print("-- OBS con imagen PROPIA (C2 otro brazo) --", time.time() - t0)
    print(a_own.estado.value_counts().to_dict())

    # ---------- B. nulo: punto sorteado, imagen cruzada, sobre pasadas fuera de la muestra
    NUL = df[(df.lab == "neg_limpio") & (df.vol != "Lastarria") & ~(df.patron & df.pub)].copy()
    print("\n== pool nulo (neg_limpio fuera de Lastarria, NO (patron y publicado)): %d ==" % len(NUL))
    b = medir(NUL, "null", rng=random.Random(2144), usar_propia=False)
    print("-- NULO con imagen cruzada --", time.time() - t0)
    print(b.estado.value_counts().to_dict())

    pickle.dump(dict(cross=a_cross, own=a_own, null=b), open(HERE + "/cruz5.pkl", "wb"))
    print("\nlisto en %.0f s" % (time.time() - t0))
