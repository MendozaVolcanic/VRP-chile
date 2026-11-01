"""Verificador S163: implementacion INDEPENDIENTE de la regla de relleno de fillmissing2.
Idea distinta a la de delaunay_perturbado.py: en vez de la perturbacion simbolica de CGAL (orden lexicografico),
el empate de cuatro puntos cocirculares se rompe levantando la parabola con z += s*eps*x*y (x=fila, y=columna).
Candidatos: s=+1, s=-1 (x*y es simetrico, asi que cambiar de marco equivale a cambiar s).
Triangulacion inicial: scipy/Qhull; luego volteos de Lawson con predicado entero exacto. Interpolacion lineal baricentrica
mia, y vecino mas cercano fuera de la envolvente (solo si hace falta). No lee BK/LBK/VRP de MATLAB salvo para comparar."""
import hashlib, json, sys
from pathlib import Path
import numpy as np, scipy.io as sio
from scipy.spatial import Delaunay, cKDTree

O2 = Path(r"C:\vrp-trabajo\s159-pruebas\experiments\_s159\o1\o2_paquete")
assert hashlib.md5((O2 / "resultado_o2.mat").read_bytes()).hexdigest() == "1f7fdc4bed0f8cb6223204bbce42ba43"

def det3(m):
    return (m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1]) - m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])
            + m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))

def incircle_sign(a, b, c, d, s):
    """a,b,c antihorarios en (x=fila,y=col). +1 si d dentro. Empate -> perturbacion z += s*eps*x*y."""
    rows = [(p[0]-d[0], p[1]-d[1]) for p in (a, b, c)]
    z = [r[0]**2 + r[1]**2 for r in rows]
    v = det3([[rows[i][0], rows[i][1], z[i]] for i in range(3)])
    if v != 0:
        return (v > 0) - (v < 0), False
    for f in MONOMIOS:   # perturbacion simbolica jerarquica: eps, eps^2, ... con monomios distintos
        w = [f(p[0], p[1]) - f(d[0], d[1]) for p in (a, b, c)]
        v2 = det3([[rows[i][0], rows[i][1], w[i]] for i in range(3)]) * s
        if v2 != 0:
            return (v2 > 0) - (v2 < 0), True
    return 0, True   # empate sin resolver

MONOMIOS = [lambda x, y: x*y, lambda x, y: x*x*y, lambda x, y: x*y*y, lambda x, y: x**3*y, lambda x, y: x*y**3,
            lambda x, y: x*x*y*y, lambda x, y: x**3*y*y, lambda x, y: x*x*y**3]

MODO = {"m": "mono"}

def orient(a, b, c):
    v = (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0]); return (v > 0) - (v < 0)

def incircle_cgal(p0, p1, p2, p):
    rows = [(q[0]-p[0], q[1]-p[1]) for q in (p0, p1, p2)]
    z = [r[0]**2 + r[1]**2 for r in rows]
    v = det3([[rows[i][0], rows[i][1], z[i]] for i in range(3)])
    if v != 0: return (v > 0) - (v < 0), False
    pts = sorted([(p0, 0), (p1, 1), (p2, 2), (p, 3)], key=lambda t: t[0])  # orden lexicografico en el marco vigente
    for i in (3, 2, 1):
        quien = pts[i][1]
        if quien == 3: return -1, True
        if quien == 2:
            o = orient(p0, p1, p)
            if o: return o, True
        if quien == 1:
            o = orient(p0, p, p2)
            if o: return o, True
        if quien == 0:
            o = orient(p, p1, p2)
            if o: return o, True
    return 0, True

_incircle_mono = incircle_sign
def incircle_sign(a, b, c, d, s):
    return incircle_cgal(a, b, c, d) if MODO["m"] == "cgal" else _incircle_mono(a, b, c, d, s)

def ccw(P, i, j, k):
    return (P[j][0]-P[i][0])*(P[k][1]-P[i][1]) - (P[j][1]-P[i][1])*(P[k][0]-P[i][0])

def triangular(P, s):
    n = len(P)
    tri = Delaunay(np.array(P, float))
    assert len(tri.coplanar) == 0
    T = []
    for t in tri.simplices:
        i, j, k = map(int, t)
        T.append([i, j, k] if ccw(P, i, j, k) > 0 else [i, k, j])
    E = {}
    def reg(t):
        i, j, k = T[t]; E[(i, j)] = t; E[(j, k)] = t; E[(k, i)] = t
    for t in range(len(T)): reg(t)
    work = list(E.keys()); empates = 0; nsin = 0; flips = 0
    while work:
        a, b = work.pop()
        t1 = E.get((a, b)); t2 = E.get((b, a))
        if t1 is None or t2 is None: continue
        c = next(v for v in T[t1] if v not in (a, b)); d = next(v for v in T[t2] if v not in (a, b))
        sg, emp = incircle_sign(P[a], P[b], P[c], P[d], s)
        if emp: empates += 1
        if sg == 0: nsin += 1
        if sg > 0:
            for e in ((a,b),(b,c),(c,a),(b,a),(a,d),(d,b)): E.pop(e, None)
            T[t1] = [c, a, d]; T[t2] = [d, b, c]; reg(t1); reg(t2); flips += 1
            work += [(a,d),(d,b),(b,c),(c,a)]
    return T, dict(flips=flips, empates=empates, sin_resolver=nsin)

def dilatar(mask, k):
    r = k // 2; n, m = mask.shape; out = np.zeros_like(mask)
    for di in range(-r, r+1):
        for dj in range(-r, r+1):
            sl_o = (slice(max(0,di), n+min(0,di)), slice(max(0,dj), m+min(0,dj)))
            sl_i = (slice(max(0,-di), n+min(0,-di)), slice(max(0,-dj), m+min(0,-dj)))
            out[sl_o] |= mask[sl_i]
    return out

def rellenar(masked, s, marco=(0,1,1)):  # marco=(swap, sx, sy)
    n, m = masked.shape
    rr, cc = np.indices((n, m)); ok = np.isfinite(masked)
    sw, sx, sy = marco
    X, Y = (cc, rr) if sw else (rr, cc)
    P = [(int(sx*x), int(sy*y)) for x, y in zip(X[ok], Y[ok])]; val = masked[ok]
    hq = [(int(sx*x), int(sy*y)) for x, y in zip(X[~ok], Y[~ok])]
    if ok.all(): return masked.copy(), {}
    T, info = triangular(P, s)
    Pa = np.array(P); Ta = np.array(T)
    B = masked.copy(); holes = np.array(hq); hole_idx = np.argwhere(~ok)
    # localizacion vectorizada por triangulo-candidato (caja)
    tx = Pa[Ta, 0]; ty = Pa[Ta, 1]
    x0, x1, y0, y1 = tx.min(1), tx.max(1), ty.min(1), ty.max(1)
    tree = cKDTree(Pa); fuera = 0
    for (qx, qy), (hi, hj) in zip(holes, hole_idx):
        cand = np.nonzero((x0 <= qx) & (qx <= x1) & (y0 <= qy) & (qy <= y1))[0]
        v = None
        for t in cand:
            i, j, k = Ta[t]; A, Bp, C = Pa[i], Pa[j], Pa[k]
            den = ccw(P, i, j, k)
            l1 = ((Bp[0]-qx)*(C[1]-qy) - (Bp[1]-qy)*(C[0]-qx))
            l2 = ((C[0]-qx)*(A[1]-qy) - (C[1]-qy)*(A[0]-qx))
            l3 = ((A[0]-qx)*(Bp[1]-qy) - (A[1]-qy)*(Bp[0]-qx))
            if min(l1, l2, l3) >= 0:
                v = (l1*val[i] + l2*val[j] + l3*val[k]) / den; break
        if v is None:
            _, ix = tree.query([qx, qy]); v = val[ix]; fuera += 1
        B[hi, hj] = v
    info['fuera_envolvente'] = fuera
    return B, info

def cargar():
    R = sio.loadmat(O2 / "resultado_o2.mat"); E = sio.loadmat(O2 / "entradas_o2.mat")
    etq = json.loads((O2 / "entradas_o2_etiquetas.json").read_text(encoding="utf-8"))
    return R, E, etq

def escena(R, E, k):
    a = np.asarray(R["ALERTAS"][k, 0]).ravel().astype(np.int64)
    if a.size == 0: return None
    m13 = E["M13"][:, :, k].astype(float)
    flat = m13.ravel(order="F")  # indices MATLAB lineales base 1, columna mayor
    ma = m13.copy(); ma.ravel(order="F")[a-1] if False else None
    mk = np.zeros(m13.size, bool); mk[a-1] = True; mk = mk.reshape(m13.shape, order="F")
    ma = m13.copy(); ma[mk] = np.nan
    kk = 3 if a.size <= 4 else (5 if a.size <= 30 else 7)
    ma[dilatar(np.isnan(ma), kk)] = np.nan
    return a, m13, ma, flat, mk


def correr(modo, marco, s=1, quiet=False):
    MODO["m"] = modo
    R, E, etq = cargar(); K = R["VRP"].shape[0]; rel = []; bkmax = []; ids = []
    for k in range(K):
        e = escena(R, E, k)
        if e is None: continue
        a, m13, ma, flat, mk = e
        B, info = rellenar(ma, s, marco)
        lhot = float(np.nansum(flat[a-1])); lbk = float(np.nansum(B.ravel(order="F")[a-1]))
        vrp = (lhot - lbk) * 1.97e7 * 0.5625 / 1e6; vm = float(R["VRP"][k, 0])
        rel.append(abs(vrp/vm - 1)); ids.append(k)
        bk = R["BK"][k, 0]
        if bk.size: bkmax.append(float(np.nanmax(np.abs(B - bk)[np.isnan(ma)])))
    rel = np.array(rel)
    print(f"modo={modo} marco(swap,sx,sy)={marco}: calzan 1e-9 {(rel<1e-9).sum()} de {len(rel)}; max rel {rel.max():.2e}; "
          f"BK completo <1e-9 en {sum(b<1e-9 for b in bkmax)} de {len(bkmax)}, max {max(bkmax):.2e}", flush=True)
    return ids, rel

if __name__ == "__main__":
    out = {}
    for marco in [(0,1,1),(1,1,1),(0,1,-1),(0,-1,1),(0,-1,-1),(1,1,-1),(1,-1,1),(1,-1,-1)]:
        ids, rel = correr("cgal", marco)
        out[str(marco)] = rel.tolist()
    json.dump(out, open("mi_cgal_resultado.json", "w"))
