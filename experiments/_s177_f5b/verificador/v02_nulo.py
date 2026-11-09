# -*- coding: utf-8 -*-
"""V177 v02. Recalculo independiente del nulo N1 y N3, y tres preguntas que el INFORME no se hizo.

Fenomeno: si el foco es fijo, pasadas con igual visada ponen el pixel casi en el mismo lugar, asi que comparar la mancha de i con
nuestro punto de otra pasada de igual visada casi no se distingue de nuestro punto propio AUNQUE la lamina y nosotros veamos exactamente
el mismo pixel. Por eso hace falta saber que daria N3 si la identidad fuera perfecta (techo), y usar un test sin el techo de la clase binaria.

Pre-registro:
 A. Reproduccion: obs, nulo, dif, AUC de N1 y N3 (C2p) deben dar lo de s04 seccion C.
 B. IC con unidad correcta: bootstrap por dia UTC (cluster) y remuestreando tambien los j. Si el IC se ensancha mucho, el de s04 era optimista.
 C. Techo: reemplazo la mancha por la celda de la grilla que contiene NUESTRO punto (identidad perfecta con la cuantizacion de la lamina),
    con ruido 0, 0,5 y 1 celda. Mismo N3. Si el AUC techo es parecido al observado, N3 no puede decir mas. Si es mucho mayor, el observado es parcial.
 D. Permutacion restringida a geometria: reasigno nuestros puntos solo entre pasadas compatibles (zenit +-5, azimut +-30) con cadena de intercambios
    (uniforme sobre permutaciones validas). Estadistico: distancia media mancha-punto y correlacion E y N. Sin clase binaria.
    Si p chico: la lamina lleva informacion de la pasada mas alla de la geometria (mas alla de lo que dice INFORME sec. 5). Si p grande: confirma.
 E. Lo mismo excluyendo vecinos a menos de 36 h (mismo evento o noche) del conjunto de compatibles.
 F. Composicion temporal y por satelite de los vecinos N3.
Pregunta 1: si la lamina no tuviera informacion, D da p ~ uniforme. Control: D sobre un brazo barajado de antemano (mancha de otra pasada compatible) debe dar p no chico.
Pregunta 2: si el instrumento muriera, C con ruido infinito debe caer a AUC ~0,5 (ruido 3 celdas lo aproxima).
"""
import os, sys, pickle, collections
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from comun import *

R = pickle.load(open(os.path.join(HERE, "v01_manchas.pkl"), "rb"))
GEO = geo_chillan()
rng = np.random.default_rng(20261109)


def dazi(a, b):
    x = abs(a - b) % 360
    return min(x, 360 - x)


def prep(b):
    s = [o for o in R if o["vol"] == CH and o["b"] == b]
    g = grilla(CH, b)
    for o in s:
        r = GEO[(o["sensor"], o["dt"])]
        o["zen"], o["azi"] = r["sensor_zenith_deg"], r["sensor_azimuth_deg"]
        o["t"] = fecha(o["dt"])
    return s, g


def matrices(s, g, m_key="C2", manchas=None):
    n = len(s)
    mla = np.array([o[m_key]["la"] for o in s]) if manchas is None else manchas[0]
    mlo = np.array([o[m_key]["lo"] for o in s]) if manchas is None else manchas[1]
    pla = np.array([o["pt"][0] for o in s])
    plo = np.array([o["pt"][1] for o in s])
    D = hav(mla[:, None], mlo[:, None], pla[None, :], plo[None, :])
    return D


def vecinos(s, fz, fa, excl_h=None):
    n = len(s)
    N = np.zeros((n, n), bool)
    for i in range(n):
        for j in range(n):
            if i != j and abs(s[i]["zen"] - s[j]["zen"]) <= fz and dazi(s[i]["azi"], s[j]["azi"]) <= fa:
                if excl_h is None or abs((s[i]["t"] - s[j]["t"]).total_seconds()) > excl_h * 3600:
                    N[i, j] = True
    return N


def ctrl_ok(s, g):
    return np.array([clase(o["C2"], o["pt"], o["dist"], o["b"], o["celda"], g, "any") != "iv" for o in s])


def stats(D, N, sel, tol, w=None, wj=None):
    """obs, nul, dif, auc, d propia, d otras con pesos por pasada (w sobre i, wj sobre j). sel = bool de pasadas i validas."""
    n = len(D)
    w = np.ones(n) if w is None else w
    wj = w if wj is None else wj
    den = (N * wj).sum(axis=1)
    use = sel & (den > 0) & (w > 0)
    ii = np.where(use)[0]
    C = D <= tol
    d0 = np.diag(D)
    nul = ((C * N * wj).sum(axis=1)[ii]) / den[ii]
    A = ((D > d0[:, None] + 1e-6) + 0.5 * (np.abs(D - d0[:, None]) <= 1e-6))
    auc = ((A * N * wj).sum(axis=1)[ii]) / den[ii]
    do = ((D * N * wj).sum(axis=1)[ii]) / den[ii]
    W = w[ii]
    obs = (d0[ii] <= tol)
    return dict(n=len(ii), obs=np.average(obs, weights=W), nul=np.average(nul, weights=W), auc=np.average(auc, weights=W), dp=np.average(d0[ii], weights=W), do=np.average(do, weights=W))


def bootstrap(D, N, sel, tol, modo, dias, B=2000):
    n = len(D)
    out = {k: [] for k in ("dif", "auc", "dkm")}
    ud = sorted(set(dias))
    idx_d = {d: [i for i in range(n) if dias[i] == d] for d in ud}
    for _ in range(B):
        if modo == "pasada_i":          # como s04: remuestrea i, el nulo de cada i queda fijo
            w = np.bincount(rng.integers(0, n, n), minlength=n).astype(float)
            r = stats(D, N, sel, tol, w, np.ones(n))
        elif modo == "dia_i":           # cluster por dia, nulo de cada i fijo
            w = np.zeros(n)
            for d in rng.choice(ud, len(ud)):
                w[idx_d[d]] += 1
            r = stats(D, N, sel, tol, w, np.ones(n))
        elif modo == "dia_ij":          # cluster por dia, remuestrea tambien los j que entran al nulo
            w = np.zeros(n)
            for d in rng.choice(ud, len(ud)):
                w[idx_d[d]] += 1
            r = stats(D, N, sel, tol, w, w)
        out["dif"].append(r["obs"] - r["nul"])
        out["auc"].append(r["auc"])
        out["dkm"].append(r["do"] - r["dp"])
    return {k: (np.percentile(v, 2.5), np.percentile(v, 97.5)) for k, v in out.items()}


def linea(r):
    return f"n={r['n']:3d} obs {r['obs']:.3f} nulo {r['nul']:.3f} dif {r['obs'] - r['nul']:+.3f} AUC {r['auc']:.3f} d propia {r['dp']:.3f} d otras {r['do']:.3f}"


def cadena(N, T_fn, n_mues=4000, thin=None):
    """Permutaciones uniformes sobre las validas: pi(i) en N(i) o i. Propone intercambios simetricos. Comienza en identidad."""
    n = len(N)
    M = N.copy()
    np.fill_diagonal(M, True)
    pi = np.arange(n)
    thin = thin or 5 * n
    # quemado
    a_b = rng.integers(0, n, size=(200 * n * n, 2))
    for a, b in a_b:
        if M[a, pi[b]] and M[b, pi[a]]:
            pi[a], pi[b] = pi[b], pi[a]
    vals = []
    mov = []
    for k in range(n_mues):
        a_b = rng.integers(0, n, size=(thin, 2))
        for a, b in a_b:
            if M[a, pi[b]] and M[b, pi[a]]:
                pi[a], pi[b] = pi[b], pi[a]
        vals.append(T_fn(pi))
        mov.append(np.mean(pi != np.arange(n)))
    return np.array(vals), float(np.mean(mov))


for nom, b in (("Chillan VIIRS 375", "VIIRS375"), ("Chillan VIIRS 750", "VIIRS750")):
    s, g = prep(b)
    tol = TOL[b]
    D = matrices(s, g)
    ok = ctrl_ok(s, g)
    dias = [o["dt"][:10] for o in s]
    NAll = ~np.eye(len(s), dtype=bool)
    N3 = vecinos(s, 5, 30)
    N3b = vecinos(s, 3, 15)
    print(f"\n======== {nom}: n pasadas {len(s)}, control ok {ok.sum()}, dias distintos {len(set(dias))}, satelites {dict(collections.Counter(o['sensor'] for o in s))}")
    print("A. Reproduccion (C2p, mismo filtro de vecinos >= 2)")
    print("  N1 ", linea(stats(D, NAll, ok, tol)))
    n3sel = ok & (N3.sum(axis=1) >= 2)
    n3bsel = ok & (N3b.sum(axis=1) >= 2)
    print("  N3 ", linea(stats(D, N3, n3sel, tol)))
    print("  N3b", linea(stats(D, N3b, n3bsel, tol)))
    nosel = np.ones(len(s), bool) & (N3.sum(axis=1) >= 2)
    print("  N3 sin control (todas las pasadas con >=2 vecinos)", linea(stats(D, N3, nosel, tol)))
    print("B. IC95 del N3 (C2p): dif de clase | AUC | d otras - d propia (km), segun unidad de remuestreo")
    for modo in ("pasada_i", "dia_i", "dia_ij"):
        ci = bootstrap(D, N3, n3sel, tol, modo, dias)
        print(f"  {modo:9s} dif [{ci['dif'][0]:+.3f}, {ci['dif'][1]:+.3f}] | AUC [{ci['auc'][0]:.3f}, {ci['auc'][1]:.3f}] | km [{ci['dkm'][0]:+.3f}, {ci['dkm'][1]:+.3f}]")
    # C techo
    print("C. Techo: mancha = celda que contiene nuestro punto, con ruido (mismo N3, mismo filtro)")
    plats = np.array([o["pt"][0] for o in s])
    plons = np.array([o["pt"][1] for o in s])
    celda_km = g["celda"]
    for ruido in (0, 0.5, 1, 3):
        rs = []
        for rep in range(1 if ruido == 0 else 50):
            la_r = plats + rng.normal(0, ruido * celda_km / 110.57, len(s)) if ruido else plats
            lo_r = plons + rng.normal(0, ruido * celda_km / (111.32 * np.cos(np.radians(plats))), len(s)) if ruido else plons
            ml, mo = [], []
            for la, lo in zip(la_r, lo_r):
                d = hav(g["lats"], g["lons"], la, lo)
                r_, c_ = np.unravel_index(np.argmin(d), d.shape)
                ml.append(g["lats"][r_, c_])
                mo.append(g["lons"][r_, c_])
            Dt = matrices(s, g, manchas=(np.array(ml), np.array(mo)))
            rs.append(stats(Dt, N3, n3sel, tol))
        print(f"  ruido {ruido} celdas: obs {np.mean([x['obs'] for x in rs]):.3f} nulo {np.mean([x['nul'] for x in rs]):.3f} AUC {np.mean([x['auc'] for x in rs]):.3f} d propia {np.mean([x['dp'] for x in rs]):.3f} d otras {np.mean([x['do'] for x in rs]):.3f}")
    # D permutacion restringida (sin control: posicion pura; y con control)
    E = (np.array([o["C2"]["lo"] for o in s]) - np.median(plons)) * 111.32 * np.cos(np.radians(np.median(plats)))
    Nn = (np.array([o["C2"]["la"] for o in s]) - np.median(plats)) * 110.57
    Ep = (plons - np.median(plons)) * 111.32 * np.cos(np.radians(np.median(plats)))
    Np = (plats - np.median(plats)) * 110.57
    for etq, Nbase, excl in (("N3 zenit 5 azimut 30", N3, None), ("N3b zenit 3 azimut 15", N3b, None), ("N3 sin vecinos a <36 h", vecinos(s, 5, 30, 36), 36)):
        n = len(s)
        fn = lambda pi: (D[np.arange(n), pi].mean(), np.corrcoef(E, Ep[pi])[0, 1], np.corrcoef(Nn, Np[pi])[0, 1])
        obs_T = fn(np.arange(n))
        vals, mov = cadena(Nbase, fn)
        p_d = (1 + (vals[:, 0] <= obs_T[0]).sum()) / (1 + len(vals))
        p_e = (1 + (vals[:, 1] >= obs_T[1]).sum()) / (1 + len(vals))
        p_n = (1 + (vals[:, 2] >= obs_T[2]).sum()) / (1 + len(vals))
        print(f"D. Permutacion restringida a {etq}: fraccion de pasadas que se mueven {mov:.2f}; d media obs {obs_T[0]:.3f} km, bajo perm {vals[:, 0].mean():.3f} (p {p_d:.4f}); r E obs {obs_T[1]:+.2f}, perm {vals[:, 1].mean():+.2f} (p {p_e:.4f}); r N obs {obs_T[2]:+.2f}, perm {vals[:, 2].mean():+.2f} (p {p_n:.4f})")
    # control de la permutacion: partir de un brazo ya barajado dentro de vecinos, debe dar p no chico
    n = len(s)
    fn0 = lambda pi: pi
    M = N3.copy()
    np.fill_diagonal(M, True)
    pis = []
    for rep in range(20):
        pi = np.arange(n)
        for a, b_ in rng.integers(0, n, size=(200 * n * n, 2)):
            if M[a, pi[b_]] and M[b_, pi[a]]:
                pi[a], pi[b_] = pi[b_], pi[a]
        pis.append(pi.copy())
    ps = []
    for pi0 in pis:
        Tobs = D[np.arange(n), pi0].mean()
        fnc = lambda pi: D[np.arange(n), pi].mean()
        vals, _ = cadena(N3, fnc, n_mues=500)
        ps.append((1 + (vals <= Tobs).sum()) / 501)
    print(f"   Control de la permutacion D (20 brazos ya barajados; p debe ser ~ uniforme): p min {min(ps):.3f}, mediana {np.median(ps):.3f}, max {max(ps):.3f}")
    # F composicion
    dt_h = []
    mism = 0
    tot = 0
    for i in range(len(s)):
        if not n3sel[i]:
            continue
        for j in np.where(N3[i])[0]:
            dt_h.append(abs((s[i]["t"] - s[j]["t"]).total_seconds()) / 3600)
            mism += s[i]["sensor"] == s[j]["sensor"]
            tot += 1
    dt_h = np.array(dt_h)
    print(f"F. Vecinos N3: {tot} pares; mismo satelite {mism / tot:.2f}; |dt| p10 {np.percentile(dt_h, 10):.1f} h, p50 {np.percentile(dt_h, 50):.1f} h; a < 36 h {np.mean(dt_h < 36):.2f}; vecinos por pasada p50 {np.median(N3.sum(axis=1)):.0f}")
    print(f"   Varianza E de nuestro punto: total {Ep.std():.3f} km; residual tras la media de vecinos N3: {np.std([Ep[i] - Ep[N3[i]].mean() for i in range(len(s)) if N3[i].sum() >= 2]):.3f} km; mancha: total {E.std():.3f}, residual {np.std([E[i] - E[N3[i]].mean() for i in range(len(s)) if N3[i].sum() >= 2]):.3f}")
    print(f"   Varianza N: total {Np.std():.3f}; residual {np.std([Np[i] - Np[N3[i]].mean() for i in range(len(s)) if N3[i].sum() >= 2]):.3f}; mancha total {Nn.std():.3f}, residual {np.std([Nn[i] - Nn[N3[i]].mean() for i in range(len(s)) if N3[i].sum() >= 2]):.3f}")
    rs_E = np.array([(Ep[i] - Ep[N3[i]].mean(), E[i] - E[N3[i]].mean()) for i in range(len(s)) if N3[i].sum() >= 2])
    rs_N = np.array([(Np[i] - Np[N3[i]].mean(), Nn[i] - Nn[N3[i]].mean()) for i in range(len(s)) if N3[i].sum() >= 2])
    print(f"   Correlacion de residuos respecto de los vecinos N3 (nuestro contra mancha): E {np.corrcoef(rs_E.T)[0, 1]:+.2f}, N {np.corrcoef(rs_N.T)[0, 1]:+.2f}, n={len(rs_E)}")
