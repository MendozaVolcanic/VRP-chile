# -*- coding: utf-8 -*-
"""VA: funciones del port minimo propio (copiadas de v07_port_minimo_etna.py, mismas lineas del .m)."""
import numpy as np
from scipy.ndimage import binary_dilation, generic_filter
from scipy.spatial import Delaunay
from scipy.interpolate import LinearNDInterpolator
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


