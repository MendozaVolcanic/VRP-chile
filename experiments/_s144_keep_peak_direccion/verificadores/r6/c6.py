# Verificador v6 S144: instrumento con la regla LITERAL de la v6 (ventana 45-120 min,
# pasada cruzada nocturna) sobre el estrato hermano (R) y sobre el nulo N1 (sin patron).
# Solo lectura. NO evalua Z en el P de ninguna pasada de la muestra del veredicto.
import os, sys, math, pickle, time, random
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3"); V4 = os.path.abspath(HERE + "/../v4"); V5 = os.path.abspath(HERE + "/../v5")
for p in (V3, V4, V5, HERE):
    sys.path.insert(0, p)
from common3 import *  # noqa
import base4 as B  # noqa

sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/scripts")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp  # noqa

df = B.df.copy()
df["t"] = pd.to_datetime(df.dt, utc=True)
df["noche"] = df.t.dt.strftime("%Y-%m-%d")
idx_v = B.idx_v
Zc = pickle.load(open(V5 + "/zc5.pkl", "rb"))
zc = Zc["zc"]
COORD = bp._coords_por_volcan()

SEP_KM = 1.5
GAP_D = 3.0
NREF = 5
MINREF = 3
GMIN = 45 * 60.0     # v6
GMAX = 120 * 60.0    # v6

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
    orden = sorted(cand, key=lambda i: (abs(dt_s[i]), dt_s[i]))
    return [(g.P.iloc[i], float(dt_s[i] / 86400.0)) for i in orden[:NREF]]


def es_nocturna(vol, t):
    la, lo = COORD[vol]
    return not bp.es_pasada_diurna_descartada("VIIRS375", la, lo, pd.Timestamp(t).to_pydatetime())


def cruzada_v6(vol, t_p, gmin=GMIN, gmax=GMAX, solo_conteo=False):
    """Regla LITERAL v6: otra pasada del mismo volcan, 45<=|dt|<=120 min, TIF usable,
    ella misma nocturna. La mas cercana en el tiempo; empate, la anterior."""
    g = idx_v.get(vol)
    if g is None:
        return None, "sin_idx"
    dd = (g.acquisition_utc - t_p).dt.total_seconds()
    m = (dd.abs() >= gmin) & (dd.abs() <= gmax)
    cand = g[m]
    if len(cand) == 0:
        return None, "sin_cruzada"
    dds = dd[m]
    orden = sorted(range(len(cand)), key=lambda i: (abs(dds.iloc[i]), dds.iloc[i]))
    hubo_diurna = False
    for i in orden:
        r = cand.iloc[i]
        if not es_nocturna(vol, r["acquisition_utc"]):
            hubo_diurna = True
            continue
        Rr, why = usable({"own": bool(r["own"]), "path": r["path"]}, vol)
        if Rr is not None:
            return (Rr, float(dds.iloc[i]), r["path"]), "ok"
    return None, ("cruzada_diurna" if hubo_diurna else "cruzada_no_usable")


def medir(sub, modo, rng=None, gmin=GMIN, gmax=GMAX):
    out = []
    for vol, g in sub.groupby("vol"):
        if vol not in zc.index:
            continue
        v = vent(vol)
        for _, r in g.sort_values("t").iterrows():
            t_p = r["t"]
            if modo == "P":
                X = r["P"]
                if X is None or X[0] is None:
                    out.append(dict(vol=vol, t=t_p, lab=r["lab"], noche=r["noche"], tramo=r["tramo"],
                                    estado="sin_P")); continue
            else:
                u = rng.random()
                rr = math.sqrt(1.5 ** 2 + u * (3.0 ** 2 - 1.5 ** 2))
                az = rng.uniform(0, 2 * math.pi)
                X = desplazar(v[0], v[1], rr * math.cos(az), rr * math.sin(az))
            R = refs_de(vol, t_p, r["noche"], X)
            if len(R) < MINREF:
                out.append(dict(vol=vol, t=t_p, lab=r["lab"], noche=r["noche"], tramo=r["tramo"],
                                estado="pocas_refs", n_ref=len(R))); continue
            cr, why = cruzada_v6(vol, t_p, gmin, gmax)
            if cr is None:
                out.append(dict(vol=vol, t=t_p, lab=r["lab"], noche=r["noche"], tramo=r["tramo"],
                                estado=why, n_ref=len(R))); continue
            Rr, dsep, _p = cr
            zo = Z(Rr, X)
            if zo is None:
                out.append(dict(vol=vol, t=t_p, lab=r["lab"], noche=r["noche"], tramo=r["tramo"],
                                estado="sin_dl0", n_ref=len(R))); continue
            zr = [Z(Rr, p) for p, _g in R]
            zr = [x for x in zr if x is not None]
            if len(zr) < MINREF:
                out.append(dict(vol=vol, t=t_p, lab=r["lab"], noche=r["noche"], tramo=r["tramo"],
                                estado="refs_sin_dl0", n_ref=len(zr))); continue
            e = 1.0 * (zo >= zc[vol])
            rr_ = float(np.mean([x >= zc[vol] for x in zr]))
            out.append(dict(vol=vol, t=t_p, lab=r["lab"], noche=r["noche"], tramo=r["tramo"],
                            estado="ok", e=e, r=rr_, d=e - rr_, n_ref=len(zr),
                            dsep_min=dsep / 60.0, zobs=zo, zref=zr))
        raster.cache_clear()
        print("   ...%s" % vol, flush=True)
    return pd.DataFrame(out)


if __name__ == "__main__":
    t0 = time.time()
    HER = df[df.patron & df.pub & (df.vol != "Lastarria") & df.lab.isin(["far_ref", "sin_info"])].copy()
    print("== estrato hermano (R): %d pasadas ==" % len(HER), flush=True)
    R_ = medir(HER, "P")
    print("R estados:", R_.estado.value_counts().to_dict(), "  %.0fs" % (time.time() - t0), flush=True)

    # N1 con la lectura literal de la v6: "pasadas sin patron"
    N_all = df[~(df.patron & df.pub)].copy()
    print("\n== N1 lectura A: TODAS las pasadas sin patron: %d ==" % len(N_all), flush=True)
    N1a = medir(N_all, "null", rng=random.Random(2144))
    print("N1a estados:", N1a.estado.value_counts().to_dict(), "  %.0fs" % (time.time() - t0), flush=True)

    pickle.dump(dict(R=R_, N1a=N1a), open(HERE + "/c6.pkl", "wb"))
    print("\nlisto en %.0f s" % (time.time() - t0))
