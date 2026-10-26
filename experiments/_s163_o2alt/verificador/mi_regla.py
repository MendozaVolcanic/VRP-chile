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

def rellenar(masked, s):
    n, m = masked.shape
    rr, cc = np.indices((n, m)); ok = np.isfinite(masked)
    P = [(int(r), int(c)) for r, c in zip(rr[ok], cc[ok])]; val = masked[ok]
    if ok.all(): return masked.copy(), {}
    T, info = triangular(P, s)
    Pa = np.array(P); Ta = np.array(T)
    B = masked.copy(); holes = np.argwhere(~ok)
    # localizacion vectorizada por triangulo-candidato (caja)
    tx = Pa[Ta, 0]; ty = Pa[Ta, 1]
    x0, x1, y0, y1 = tx.min(1), tx.max(1), ty.min(1), ty.max(1)
    tree = cKDTree(Pa); fuera = 0
    for (qx, qy) in holes:
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
        B[qx, qy] = v
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

if __name__ == "__main__":
    R, E, etq = cargar()
    K = R["VRP"].shape[0]; print("escenas totales", K, "etiquetas", len(etq), "forma M13", E["M13"].shape)
    res = {}
    for s in (+1, -1):
        rel = []; bkmax = []; emp = 0; sinres = 0; fuera = 0; ids = []; sin_alerta_matlab = 0
        for k in range(K):
            e = escena(R, E, k)
            if e is None: sin_alerta_matlab += 1; continue
            a, m13, ma, flat, mk = e
            B, info = rellenar(ma, s)
            lhot = float(np.nansum(flat[a-1])); lbk = float(np.nansum(B.ravel(order="F")[a-1]))
            vrp = (lhot - lbk) * 1.97e7 * 0.5625 / 1e6
            vm = float(R["VRP"][k, 0]); rel.append(abs(vrp/vm - 1) if vm != 0 else abs(vrp)); ids.append(k)
            emp += info.get('empates', 0); sinres += info.get('sin_resolver', 0); fuera += info.get('fuera_envolvente', 0)
            bk = R["BK"][k, 0]
            if bk.size:
                falt = np.isnan(ma); bkmax.append(float(np.nanmax(np.abs(B - bk)[falt])))
        rel = np.array(rel)
        print(f"s={s:+d}: escenas con alerta {len(rel)} (sin alerta en MATLAB {sin_alerta_matlab}); calzan a 1e-9: {(rel<1e-9).sum()}; "
              f"a 1e-12: {(rel<1e-12).sum()}; max rel {rel.max():.2e}; BK completo: {len(bkmax)} escenas, "
              f"max {max(bkmax) if bkmax else float('nan'):.2e}, <1e-9: {sum(b<1e-9 for b in bkmax)}; "
              f"empates evaluados {emp}, sin resolver {sinres}, celdas fuera de envolvente {fuera}")
        res[s] = dict(ids=ids, rel=rel.tolist(), bkmax=bkmax)
    json.dump(res, open("mi_regla_resultado.json", "w"))
