"""S163 O2 alternativa: relleno lineal sobre una triangulación de Delaunay ÚNICA por perturbación simbólica.

POR QUÉ EXISTE. En una grilla regular cuatro centros vecinos son cocirculares, así que la triangulación de Delaunay no
es única y cada implementación rompe el empate a su manera (Qhull en scipy y en Octave lo hace según el orden y la
orientación numérica de los datos). El fondo que el `.m` de MIROVA calcula con `fillmissing2(...,'linear')` depende
de esa elección (INFORME S159, H1 y H2). Este módulo agrega UNA familia de candidatos con regla de desempate explícita
y determinista: la perturbación simbólica de CGAL (`Delaunay_triangulation_2::side_of_oriented_circle` con
`perturb=true`, orden lexicográfico xy; Devillers y Teillaud). SOSPECHA, NO DATO: que MATLAB use CGAL en
`delaunayTriangulation`/`scatteredInterpolant` y que `fillmissing2` pase por ahí. Nada de eso está verificado acá; el
candidato se pone a prueba contra el único número de MATLAB conocido a 9 decimales (Etna, OSF v2.5).

Método: triangulación inicial con Qhull (scipy), luego volteos de Lawson con el predicado perturbado, en aritmética
entera exacta (coordenadas de grilla), hasta que ninguna arista viole el predicado. Con un predicado perturbado
consistente la triangulación final es única e independiente de la inicial.

Ejes: `ejes="xy_col_fila"` usa x = columna, y = fila (convención de meshgrid en MATLAB); `ejes="xy_fila_col"` el
cambio. El orden lexicográfico y la orientación se calculan en ese marco. `sx`, `sy` = -1 reflejan un eje (las ocho
simetrías del marco sirven de nulo en `etna_ancla.py`).
"""
from __future__ import annotations

import numpy as np
from scipy.spatial import Delaunay


def _orient(a, b, c):
    v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return (v > 0) - (v < 0)


def _incircle(a, b, c, d):
    """>0 si d está dentro del círculo de a,b,c (a,b,c en sentido antihorario). Entero exacto."""
    adx, ady = a[0] - d[0], a[1] - d[1]
    bdx, bdy = b[0] - d[0], b[1] - d[1]
    cdx, cdy = c[0] - d[0], c[1] - d[1]
    ad, bd, cd = adx * adx + ady * ady, bdx * bdx + bdy * bdy, cdx * cdx + cdy * cdy
    v = adx * (bdy * cd - bd * cdy) - ady * (bdx * cd - bd * cdx) + ad * (bdx * cdy - bdy * cdx)
    return (v > 0) - (v < 0)


def lado_perturbado(p0, p1, p2, p):
    """CGAL side_of_oriented_circle(p0,p1,p2,p,perturb=true). +1 dentro, -1 fuera. p0p1p2 antihorario."""
    s = _incircle(p0, p1, p2, p)
    if s != 0:
        return s
    pts = sorted([(tuple(p0), 0), (tuple(p1), 1), (tuple(p2), 2), (tuple(p), 3)], key=lambda t: t[0])
    for i in (3, 2):
        quien = pts[i][1]
        if quien == 3:
            return -1
        if quien == 2:
            o = _orient(p0, p1, p)
            if o != 0:
                return o
        if quien == 1:
            o = _orient(p0, p, p2)
            if o != 0:
                return o
        if quien == 0:
            o = _orient(p, p1, p2)
            if o != 0:
                return o
    raise RuntimeError("perturbación sin decidir")


def triangular(P):
    """P: (n,2) enteros. Devuelve lista de triángulos (i,j,k) antihorarios, Delaunay perturbado."""
    P = np.asarray(P, dtype=np.int64)
    tri = Delaunay(P.astype(float))
    if len(tri.coplanar):
        raise RuntimeError("Qhull dejó puntos fuera de la triangulación")
    pts = [tuple(int(v) for v in q) for q in P]
    T = []
    for s in tri.simplices:
        i, j, k = (int(x) for x in s)
        o = _orient(pts[i], pts[j], pts[k])
        if o == 0:
            raise RuntimeError("triángulo plano en la triangulación inicial")
        T.append([i, j, k] if o > 0 else [i, k, j])
    # mapa arista dirigida -> triángulo
    ar = {}
    for t, (i, j, k) in enumerate(T):
        ar[(i, j)] = t; ar[(j, k)] = t; ar[(k, i)] = t
    pila = list(ar.keys())
    nvolt = 0
    while pila:
        a, b = pila.pop()
        t1 = ar.get((a, b)); t2 = ar.get((b, a))
        if t1 is None or t2 is None:
            continue
        c = [v for v in T[t1] if v != a and v != b][0]
        d = [v for v in T[t2] if v != a and v != b][0]
        # T[t1] contiene la arista dirigida a->b, así que (a,b,c) es antihorario
        if lado_perturbado(pts[a], pts[b], pts[c], pts[d]) > 0:
            # el cuadrilátero a,d,b,c es convexo si la arista es ilegal (caso no degenerado tras perturbación)
            if _orient(pts[c], pts[a], pts[d]) <= 0 or _orient(pts[d], pts[b], pts[c]) <= 0:
                raise RuntimeError("volteo sobre cuadrilátero no convexo")
            for e in ((a, b), (b, c), (c, a), (b, a), (a, d), (d, b)):
                ar.pop(e, None)
            T[t1] = [c, a, d]; T[t2] = [d, b, c]
            for t in (t1, t2):
                i, j, k = T[t]
                ar[(i, j)] = t; ar[(j, k)] = t; ar[(k, i)] = t
            pila.extend([(a, d), (d, b), (b, c), (c, a)])
            nvolt += 1
    return T, nvolt


def comprobar_delaunay(P, T):
    """Pregunta 1 del instrumento: ¿quedó alguna arista ilegal bajo el predicado perturbado? Devuelve el conteo."""
    pts = [tuple(int(v) for v in q) for q in np.asarray(P)]
    ar = {}
    for t, (i, j, k) in enumerate(T):
        ar[(i, j)] = t; ar[(j, k)] = t; ar[(k, i)] = t
    malas = 0
    for (a, b), t1 in ar.items():
        t2 = ar.get((b, a))
        if t2 is None:
            continue
        c = [v for v in T[t1] if v != a and v != b][0]
        d = [v for v in T[t2] if v != a and v != b][0]
        if lado_perturbado(pts[a], pts[b], pts[c], pts[d]) > 0:
            malas += 1
    return malas


def rellenar(A, ejes="xy_col_fila", sx=1, sy=1):
    """fillmissing2(A,'linear') CANDIDATO: lineal sobre el Delaunay perturbado; vecino más cercano fuera de la envolvente.

    Devuelve (B, info). info['volteos'] y info['ilegales'] sirven de control del instrumento."""
    A = np.asarray(A, float)
    n, m = A.shape
    filas, cols = np.indices((n, m))
    if ejes == "xy_col_fila":
        X, Y = cols, filas
    elif ejes == "xy_fila_col":
        X, Y = filas, cols
    else:
        raise ValueError(ejes)
    X, Y = sx * X, sy * Y  # simetrías del marco: cambian el orden lexicográfico y la orientación (control de Etna)
    ok = np.isfinite(A)
    B = A.copy()
    if ok.all():
        return B, {"volteos": 0, "ilegales": 0}
    P = np.column_stack([X[ok], Y[ok]]).astype(np.int64)
    val = A[ok]
    T, nv = triangular(P)
    # localización: sólo hace falta para los faltantes; recorre triángulos cuyo rectángulo envolvente los contiene
    Q = np.column_stack([X[~ok], Y[~ok]]).astype(np.int64)
    Ta = np.array(T)
    tx, ty = P[Ta, 0], P[Ta, 1]
    xmin, xmax, ymin, ymax = tx.min(1), tx.max(1), ty.min(1), ty.max(1)
    out = np.full(len(Q), np.nan)
    for qi, (qx, qy) in enumerate(Q):
        cand = np.nonzero((xmin <= qx) & (qx <= xmax) & (ymin <= qy) & (qy <= ymax))[0]
        for t in cand:
            i, j, k = T[t]
            a, b, c = P[i], P[j], P[k]
            den = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            w1 = (b[0] - qx) * (c[1] - qy) - (b[1] - qy) * (c[0] - qx)
            w2 = (c[0] - qx) * (a[1] - qy) - (c[1] - qy) * (a[0] - qx)
            w3 = (a[0] - qx) * (b[1] - qy) - (a[1] - qy) * (b[0] - qx)
            if w1 >= 0 and w2 >= 0 and w3 >= 0:
                out[qi] = (w1 * val[i] + w2 * val[j] + w3 * val[k]) / den
                break
    if np.isnan(out).any():
        from scipy.interpolate import griddata
        sin = np.isnan(out)
        out[sin] = griddata(P.astype(float), val, Q[sin].astype(float), method="nearest")
    B[~ok] = out
    return B, {"volteos": nv, "ilegales": comprobar_delaunay(P, T)}
