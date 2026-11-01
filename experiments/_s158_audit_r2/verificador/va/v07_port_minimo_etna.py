# -*- coding: utf-8 -*-
"""VA, hallazgo 9 (y base del 10): port minimo propio del .m de MIROVA V750 sobre la matriz de ejemplo de Etna,
escrito desde MIROVA_VIIRS750_hotspot_detection.m y MIROVA_VIIRS750_VRP.m (no desde mirova_v750_r2.py).

Pregunta 1: si mi port estuviera roto, Npix y Tot_Lmir_hot no coincidirian con la fila del OSF (Etna 19/05/2023 00:54,
Resolution 750, Satellite 4: Npix 5, hot 1,96534218, bk 1,072886152, VRP 9.889.528,362 W). Control negativo: con el
segundo pase apagado o con los ROI intercambiados se imprime cuanto cambia.
Pregunta 2: un port muerto daria alert vacio (VRP NaN), no un numero: se imprime Npix.
Fondo: interpolacion lineal sobre Delaunay (scipy LinearNDInterpolator, Qhull) con y sin perturbacion de la
triangulacion (las coordenadas se perturban solo para triangular; se interpola con las exactas).
"""
import sys
import numpy as np
import scipy.io as sio
from scipy.ndimage import binary_dilation, generic_filter
from scipy.spatial import Delaunay
from scipy.interpolate import LinearNDInterpolator

sys.stdout.reconfigure(encoding="utf-8")
S = sio.loadmat("experiments/_s158_d17_diseno/osf_codigo_mirova/Example/VIIRS750_example.mat", squeeze_me=True)
M13 = S["ZI_M13"].astype(float); M15 = S["ZI_M15"].astype(float); BOX0 = S["BOX"].astype(float)
OSF = dict(npix=5, hot=1.96534218, bk=1.072886152, vrp=9889528.362)
h, c, k = 6.6256e-34, 2.9979e8, 1.38e-23


def rad2bt(L, lam):
    w = lam * 1e-6
    return (h * c / k) / w / np.log(2 * h * c ** 2 / (w ** 5 * (L * 1e6)) + 1)


def bt2rad(T, lam):
    w = lam * 1e-6
    return (2 * 3.14 * h * c ** 2) / (w ** 5 * (np.exp((h * c / k) / (w * T)) - 1)) * 1e-6 / 3.14


def nanmean3(A):
    # colfilt sliding 3x3, media omitnan; borde: colfilt rellena con 0 (no NaN). Se replica con cval=0 y contando.
    def f(v):
        v = v[np.isfinite(v)]
        return v.mean() if v.size else np.nan
    return generic_filter(A, f, size=3, mode="constant", cval=0.0)


def deteccion(M13, M15, BOX, swap=False, segundo=True):
    BOX = BOX.copy(); BOX[:, [0, -1]] = np.nan; BOX[[0, -1], :] = np.nan
    if swap:
        B = BOX.copy(); BOX[B == 1] = 2; BOX[B == 2] = 1
    m0 = np.where(BOX == 0, 1.0, np.nan); m1 = np.where(BOX == 1, 1.0, np.nan); m2 = np.where(BOX == 2, 1.0, np.nan)
    excl = np.isnan(BOX)
    bt15 = rad2bt(M15, 10.763); cold = bt15 <= 200
    bt15[cold] = np.nan; L15 = M15.copy(); L15[cold] = np.nan
    nti = (M13 - L15) / (M13 + L15)
    if np.isnan(nti).sum() >= nti.size // 2:
        return np.array([], int)
    ntir = nti.copy(); ntir[excl] = np.nan
    s1, s2, n1, n2, e1, e2 = 10, 5, 0.02, 0.003, 0.01, 0.003  # noche (dayflag 0)
    absol = np.flatnonzero((ntir > -0.7).ravel(order="F"))

    def paso(prev):
        pop = ntir.copy().ravel(order="F"); pop[absol] = np.nan; pop[prev] = np.nan; pop = pop.reshape(ntir.shape, order="F")
        loc = nanmean3(pop); loc[excl] = np.nan
        dn = pop - loc; dn[dn < -0.1] = np.nan
        mu, sd = np.nanmean(dn), np.nanstd(dn, ddof=1)
        t1, t2 = max(mu + s1 * sd, n1), max(mu + s2 * sd, n2)
        exp = bt2rad(bt15, 4.05)
        napp = ((exp - L15) / (exp + L15)).ravel(order="F"); napp[absol] = np.nan; napp[prev] = np.nan
        napp[excl.ravel(order="F")] = np.nan; napp = napp.reshape(ntir.shape, order="F")
        ok = np.isfinite(napp) & np.isfinite(pop)
        if ok.sum() < 3:
            return np.array([], int)
        p = np.polyfit(napp[ok], pop[ok], 2)
        eti = pop - np.polyval(p, napp)
        de = eti - nanmean3(eti); de[excl] = np.nan
        mue, sde = np.nanmean(de), np.nanstd(de, ddof=1)
        u1, u2 = max(mue + s1 * sde, e1), max(mue + s2 * sde, e2)
        F = lambda A: A.ravel(order="F")
        a0 = np.flatnonzero(F((dn * m0 > t1) & (de * m0 > u1)))
        a1 = np.flatnonzero(F((dn * m1 > t1) & (de * m1 > u1)))
        a2 = np.flatnonzero(F((dn * m2 > t2) & (de * m2 > u2)))
        return np.concatenate([a0, a1, a2])
    p1 = paso(np.array([], int))
    al = [p1, absol]
    if segundo:
        al.append(paso(p1))
    return np.concatenate(al).astype(int)


def fondo(M13, alert, jitter=None, rng=None):
    npix = alert.size
    ks = 3 if npix <= 4 else (5 if npix <= 30 else 7)
    m = M13.ravel(order="F").copy(); m[alert] = np.nan; m = m.reshape(M13.shape, order="F")
    ex = binary_dilation(np.isnan(m), structure=np.ones((ks, ks), bool))
    m[ex] = np.nan
    yy, xx = np.mgrid[0:m.shape[0], 0:m.shape[1]]
    ok = np.isfinite(m)
    pts = np.c_[yy[ok], xx[ok]].astype(float)
    tri_pts = pts if jitter is None else pts + rng.normal(0, jitter, pts.shape)
    tri = Delaunay(tri_pts)
    # interpolar con coordenadas exactas sobre la topologia elegida: reemplazar puntos
    tri.points[:] = pts  # LinearNDInterpolator usa tri.points y tri.simplices
    f = LinearNDInterpolator(tri, m[ok])
    bk = m.copy()
    q = ~ok
    bk[q] = f(np.c_[yy[q], xx[q]].astype(float))
    return bk


alert = deteccion(M13, M15, BOX0)
au = np.unique(alert)
r, cc = np.unravel_index(au, M13.shape, order="F")
hot = M13.ravel(order="F")[alert].sum()
print("Npix (con repeticiones, como el .m) =", alert.size, "unicos =", au.size, "BOX de los alertados:", BOX0[r, cc])
print("Tot_Lmir_hot = %.9f (OSF %.9f)" % (hot, OSF["hot"]))
print("control: sin segundo pase Npix=%d ; ROI intercambiados Npix=%d" % (deteccion(M13, M15, BOX0, segundo=False).size,
                                                                     deteccion(M13, M15, BOX0, swap=True).size))
bk0 = fondo(M13, alert)
L0 = bk0.ravel(order="F")[alert].sum()
print("fondo Qhull sin perturbar: %.9f -> VRP %.1f W (razon VRP %.4f)" % (L0, (hot - L0) * 1.97e7 * 0.5625, (hot - L0) * 1.97e7 * 0.5625 / OSF["vrp"]))
rng = np.random.default_rng(12345)
vals = []
for s in range(300):
    try:
        b = fondo(M13, alert, jitter=1e-3, rng=rng)
        vals.append(round(b.ravel(order="F")[alert].sum(), 9))
    except Exception as e:
        pass
u = sorted(set(vals))
best = min(u, key=lambda v: abs(v - OSF["bk"]))
print("triangulaciones perturbadas validas: %d ; valores distintos de Tot_Lmir_bk: %d ; rango %.9f a %.9f" % (len(vals), len(u), u[0], u[-1]))
print("rango de VRP: %.0f a %.0f W (razones %.4f a %.4f)" % ((hot - u[-1]) * 1.97e7 * 0.5625, (hot - u[0]) * 1.97e7 * 0.5625,
      (hot - u[-1]) * 1.97e7 * 0.5625 / OSF["vrp"], (hot - u[0]) * 1.97e7 * 0.5625 / OSF["vrp"]))
print("mas cercano al OSF: %.9f (dif %.2e) ; veces que aparece: %d" % (best, abs(best - OSF["bk"]), vals.count(best)))
# control: el recorte por pixel (produccion) no cambia nada aqui si todos los dL > 0
dl = M13.ravel(order="F")[alert] - bk0.ravel(order="F")[alert]
print("dL por pixel (Qhull):", np.round(dl, 4), "-> pixeles con dL<0:", int((dl < 0).sum()))
