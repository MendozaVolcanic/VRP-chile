# Verificador v7 S144: instrumento con la regla LITERAL de la v7 (Delta_p = e_p - x_p,
# pareado dentro del mismo raster cruzado de 45 a 120 min).
# Solo lectura. NO evalua Z en el P de ninguna pasada de la muestra del veredicto.
import os, sys, math, pickle, time, random
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3"); V4 = os.path.abspath(HERE + "/../v4")
V5 = os.path.abspath(HERE + "/../v5"); V6 = os.path.abspath(HERE + "/../v6")
for p in (V3, V4, V5, V6, HERE):
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
zc = pickle.load(open(V5 + "/zc5.pkl", "rb"))["zc"]
COORD = bp._coords_por_volcan()

SEP_KM = 1.5          # 2T
R1, R2 = 1.5, 3.0     # anillo
GMIN, GMAX = 45 * 60.0, 120 * 60.0
VOLS_S = sorted(VOLS)


def es_nocturna(vol, t):
    la, lo = COORD[vol]
    return not bp.es_pasada_diurna_descartada("VIIRS375", la, lo, pd.Timestamp(t).to_pydatetime())


def cruzada(vol, t_p, gmin=GMIN, gmax=GMAX):
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
    diurna = False
    for i in orden:
        r = cand.iloc[i]
        if not es_nocturna(vol, r["acquisition_utc"]):
            diurna = True
            continue
        Rr, why = usable({"own": bool(r["own"]), "path": r["path"]}, vol)
        if Rr is not None:
            return (Rr, float(dds.iloc[i])), "ok"
    return None, ("cruzada_diurna" if diurna else "cruzada_no_usable")


def otra_noche(vol, t_p, gap_d=3.0, ntry=8):
    ix = idx_v.get(vol)
    if ix is None:
        return None, "sin_idx"
    dd = (ix.acquisition_utc - t_p).dt.total_seconds()
    m = dd.abs() > gap_d * 86400
    cand = ix[m]
    if not len(cand):
        return None, "sin_otra"
    orden = np.argsort(dd[m].abs().values)
    for i in orden[:ntry]:
        rr = cand.iloc[i]
        Rq, why = usable({"own": bool(rr["own"]), "path": rr["path"]}, vol)
        if Rq is not None:
            return (Rq, float(dd[m].iloc[i])), "ok"
    return None, "otra_no_usable"


def sortear(rng, v, r1=R1, r2=R2):
    """Un punto uniforme en area en el anillo: dos numeros, primero u, despues el acimut."""
    u = rng.random()
    rr = math.sqrt(r1 ** 2 + u * (r2 ** 2 - r1 ** 2))
    az = rng.uniform(0, 2 * math.pi)
    return desplazar(v[0], v[1], rr * math.cos(az), rr * math.sin(az)), rr, az


def sortear_sep(rng, v, ancla, sep=SEP_KM, modo="par", maxit=200):
    """Sorteo con la restriccion de separacion. modo 'par' = se re-sortean los dos numeros;
    modo 'az' = se conserva el radio y se re-sortea solo el acimut."""
    X, rr, az = sortear(rng, v)
    it = 0
    while ancla is not None and hav(X[0], X[1], ancla[0], ancla[1]) <= sep and it < maxit:
        it += 1
        if modo == "par":
            X, rr, az = sortear(rng, v)
        else:
            az = rng.uniform(0, 2 * math.pi)
            X = desplazar(v[0], v[1], rr * math.cos(az), rr * math.sin(az))
    return X, rr, az, it


def sortear_mismo_radio(rng, v, ancla, rr, sep=SEP_KM, maxit=200):
    az = rng.uniform(0, 2 * math.pi)
    X = desplazar(v[0], v[1], rr * math.cos(az), rr * math.sin(az))
    it = 0
    while hav(X[0], X[1], ancla[0], ancla[1]) <= sep and it < maxit:
        it += 1
        az = rng.uniform(0, 2 * math.pi)
        X = desplazar(v[0], v[1], rr * math.cos(az), rr * math.sin(az))
    return X, az, it


def radio_az(vol, pt):
    v = vent(vol)
    dn = (pt[0] - v[0]) * 110.574
    de = (pt[1] - v[1]) * 111.320 * math.cos(math.radians(v[0]))
    return math.hypot(dn, de), math.degrees(math.atan2(de, dn)) % 360.0


def boot(vals, key_vol, key_noche, Bn=2000, seed=144):
    """Remuestreo por noche de volcan, estratificado por volcan."""
    vals = np.asarray(vals, float)
    key = np.array([a + "|" + b for a, b in zip(key_vol, key_noche)])
    g = np.random.default_rng(seed)
    vols = sorted(set(key_vol))
    noches = {v: np.array(sorted(set(key[np.array(key_vol) == v]))) for v in vols}
    porn = {}
    for k in set(key):
        porn[k] = vals[key == k]
    out = []
    for _ in range(Bn):
        acc = []
        for v in vols:
            ns = noches[v]
            sel = g.choice(ns, len(ns), True)
            acc.append(np.concatenate([porn[k] for k in sel]))
        out.append(float(np.mean(np.concatenate(acc))))
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def corre(sub, raster_modo="cruzada", etiqueta=""):
    """Evalua, en el MISMO raster, todos los puntos de interes. Un solo recorrido."""
    rng_X = random.Random(7144)     # el X_p literal de la v7
    rng_A = random.Random(90001)    # nulo N1, punto A
    rng_B = random.Random(90002)    # nulo N1, punto B
    rng_S = random.Random(90003)    # mismo radio que P
    rng_Z = random.Random(90004)    # X sin restriccion de separacion
    out = []
    t0 = time.time()
    for vol in VOLS_S:
        g = sub[sub.vol == vol]
        if not len(g) or vol not in zc.index:
            continue
        v = vent(vol)
        for _, r in g.sort_values("t").iterrows():
            P = r["P"]
            rec = dict(vol=vol, t=r["t"], noche=r["noche"], lab=r["lab"], tramo=r["tramo"])
            if P is None or P[0] is None:
                rec["estado"] = "sin_P"; out.append(rec); continue
            rP, aP = radio_az(vol, P)
            # sorteos (siempre, en orden, para no depender del embudo)
            X, rX, aX, itX = sortear_sep(rng_X, v, P, modo="par")
            Xaz, rXaz, aXaz, _ = sortear_sep(rng_Z, v, P, modo="az")
            A, rA, aA = sortear(rng_A, v)
            Bp, rB, aB, itB = sortear_sep(rng_B, v, A, modo="par")
            Bfree, rBf, aBf = sortear(rng_B, v)
            S, aS, _ = sortear_mismo_radio(rng_S, v, P, rP)
            M = reflejo(P, v)
            rec.update(r_P=rP, az_P=aP, r_X=rX, az_X=aX, it_X=itX,
                       d_PX=float(hav(P[0], P[1], X[0], X[1])))
            if raster_modo == "cruzada":
                cr, why = cruzada(vol, r["t"])
            elif raster_modo == "propia":
                if not isinstance(r.get("tif"), str):
                    cr, why = None, "sin_tif_propio"
                else:
                    Rp_, why = usable({"own": bool(r["own"]), "path": r["tif"]}, vol)
                    cr = (Rp_, 0.0) if Rp_ is not None else None
            else:
                cr, why = otra_noche(vol, r["t"])
            if cr is None:
                rec["estado"] = why; out.append(rec); continue
            Rr, dsep = cr
            rec["dsep_min"] = dsep / 60.0
            pts = dict(P=P, X=X, Xaz=Xaz, A=A, B=Bp, Bfree=Bfree, S=S, M=M)
            zz = {k: Z(Rr, p) for k, p in pts.items()}
            for k, val in zz.items():
                rec["z_" + k] = val
            rec["estado"] = "ok"
            out.append(rec)
        raster.cache_clear()
        print("   ...%-22s %s (%.0fs)" % (vol, etiqueta, time.time() - t0), flush=True)
    D = pd.DataFrame(out)
    for k in ["P", "X", "Xaz", "A", "B", "Bfree", "S", "M"]:
        c = "z_" + k
        if c in D:
            D["e_" + k] = [np.nan if (x is None or (isinstance(x, float) and not np.isfinite(x)))
                           else float(x >= zc[v]) for x, v in zip(D[c], D.vol)]
    return D


def herm():
    return df[df.patron & df.pub & (df.vol != "Lastarria") & df.lab.isin(["far_ref", "sin_info"])].copy()


def sinpatron():
    return df[~(df.patron & df.pub)].copy()
