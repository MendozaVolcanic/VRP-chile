"""Medición P0 (3): VRP_eq mínimo con que un foco sub-píxel alerta, con y sin la anomalía fuerte (PREREGISTRO.md).

Escribe resultados.jsonl (un registro por escena, serie, brazo, T_hot, distancia y dirección) y umbrales.json
(umbrales de los dos pases de cada brazo sin foco). Uso: python medir.py
"""
from __future__ import annotations

import json
import math
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from scipy.ndimage import binary_dilation

import comun as C

MV = C.MV
DISTANCIAS = (2.0, 5.0, 10.0, 20.0)
AZIMUTS = tuple(range(0, 360, 45))
T_HOT = (1000.0, 600.0)
VRP_GRUESO = np.logspace(math.log10(0.02), math.log10(200.0), 25)
N_BISECCION = 7
W_HUELLA = 0.25
W_PIXEL_MIN = 0.3
ESCALAS_T = (1, 3, 10)
SEMILLA_RUIDO = 20261125
CLAVE_FUENTE = "NevadosDeChillan_2026-10-10_0554"


# ------------------------------------------------------------------------------------------------ brazos
def quitar_anomalia(E, m13g, m15g, mascara, k=None):
    """Celdas alertadas dilatadas k x k (k del .m si None) a NaN y rellenas con _fillmissing2_lineal, por banda."""
    npix = int(mascara.sum())
    if npix == 0:
        return m13g.copy(), m15g.copy(), np.zeros_like(mascara)
    if k is None:
        k = 3 if npix <= 4 else (5 if npix <= 30 else 7)
    zona = binary_dilation(mascara, structure=np.ones((k, k), bool))
    out = []
    for g in (m13g, m15g):
        a = g.copy()
        a[zona] = np.nan
        out.append(MV._fillmissing2_lineal(a))
    return out[0], out[1], zona


def celda_pico(E, mascara):
    if not mascara.any():
        return int(round(E.pos[0])), int(round(E.pos[1]))
    f, k = np.nonzero(mascara)
    i = int(np.argmax(E.m13g[mascara]))
    return int(f[i]), int(k[i])


def parche_fuente():
    """Exceso de M13 y M15 de la anomalía de Chillán sobre el fondo de R-sin, como dict (df, dc) -> (dL13, dL15)."""
    esc = [e for e in C.escenas() if e["clave"] == CLAVE_FUENTE][0]
    E = C.Escena(esc)
    mask, _ = E.detectar(E.m13g, E.m15g)
    s13, s15, zona = quitar_anomalia(E, E.m13g, E.m15g, mask)
    pf, pk = celda_pico(E, mask)
    parche = {}
    for f, k in zip(*np.nonzero(zona)):
        parche[(int(f - pf), int(k - pk))] = (float(E.m13g[f, k] - s13[f, k]), float(E.m15g[f, k] - s15[f, k]))
    return parche


def aplicar_parche(m13g, m15g, parche, origen, escala):
    a, b = m13g.copy(), m15g.copy()
    n = a.shape[0]
    for (df, dc), (d13, d15) in parche.items():
        f, k = origen[0] + df, origen[1] + dc
        if 0 <= f < n and 0 <= k < n:
            a[f, k] += escala * d13
            b[f, k] += escala * d15
    return a, b


def ruido(E, m13g, m15g, sd_nti):
    """Ruido blanco en M13 con amplitud NTI sqrt(3) sd_nti (C4). dNTI/dM13 = 2 M15 / (M13 + M15)^2."""
    rng = np.random.default_rng(SEMILLA_RUIDO)
    dnti = rng.standard_normal(m13g.shape) * math.sqrt(3.0) * sd_nti
    sens = 2 * m15g / (m13g + m15g) ** 2
    return m13g + dnti / sens, m15g.copy()


# ------------------------------------------------------------------------------------------------ puntos
def puntos(E, origen):
    """Puntos de inserción: (dist, azimut, índice del píxel, distancia real al origen km, offset km, w13, w15)."""
    M13, _ = E.matrices()[0]
    wmax = np.asarray(abs(M13).max(axis=0).todense()).ravel()
    fin = np.isfinite(E.d["m13"]) & np.isfinite(E.d["m15"]) & (wmax >= W_PIXEL_MIN)
    ox, oy = E.xy_celda(*origen)
    out = []
    for d in DISTANCIAS:
        for az in AZIMUTS:
            tx = ox + d * 1000 * math.sin(math.radians(az))
            ty = oy + d * 1000 * math.cos(math.radians(az))
            dd = np.hypot(E.px - tx, E.py - ty)
            dd[~fin] = np.inf
            i = int(np.argmin(dd))
            if not np.isfinite(dd[i]) or dd[i] > 750:
                out.append({"d": d, "az": az, "motivo": "sin_pixel"})
                continue
            w13, w15 = E.pesos_pixel(i)
            out.append({"d": d, "az": az, "i": i, "offset_km": float(dd[i] / 1000),
                        "dist_real_km": float(np.hypot(E.px[i] - ox, E.py[i] - oy) / 1000), "w13": w13, "w15": w15})
    return out


def huella(p):
    return p["w13"] >= W_HUELLA


# ------------------------------------------------------------------------------------------------ barrido
def grillas_con_foco(E, base13, base15, p, vrp, T):
    i = p["i"]
    L13, L15 = E.d["m13"][i], E.d["m15"][i]
    B13 = float(MV.temperatura_a_radiancia(np.array([T]), MV.LAMBDA_M13)[0])
    B15 = float(MV.temperatura_a_radiancia(np.array([T]), MV.LAMBDA_M15)[0])
    dL13 = vrp / MV.COEF_VRP_V750
    f = dL13 / (B13 - L13)
    dL15 = f * (B15 - L15)
    return base13 + dL13 * p["w13"], base15 + dL15 * p["w15"], f, L13 + dL13


def alerta(E, base13, base15, p, vrp, T):
    a, b, f, Lnuevo = grillas_con_foco(E, base13, base15, p, vrp, T)
    m, _ = E.detectar(a, b)
    return bool(m[huella(p)].any()), f, Lnuevo


def vrp_minimo(E, base13, base15, p, T):
    alerta0, _, _ = alerta(E, base13, base15, p, 0.0, T)
    res = [alerta(E, base13, base15, p, v, T)[0] for v in VRP_GRUESO]
    if not any(res):
        return {"alerta_0": alerta0, "vrp_min": None, "no_monotono": False, "evaluaciones": len(res) + 1}
    j = res.index(True)
    no_mono = not all(res[j:])
    hi = VRP_GRUESO[j]
    lo = VRP_GRUESO[j - 1] if j > 0 else 0.0
    n_ev = len(res) + 1
    for _ in range(N_BISECCION):
        mid = math.sqrt(lo * hi) if lo > 0 else hi / 2
        n_ev += 1
        if alerta(E, base13, base15, p, mid, T)[0]:
            hi = mid
        else:
            lo = mid
    _, f, Lnuevo = alerta(E, base13, base15, p, hi, T)
    bt = float(MV.radiancia_a_temperatura(np.array([Lnuevo]), MV.LAMBDA_M13)[0])
    return {"alerta_0": alerta0, "vrp_min": float(hi), "vrp_fallo": float(lo), "f": float(f), "bt13_pixel": bt,
            "sobre_techo_634K": bt > 634.0, "no_monotono": no_mono, "evaluaciones": n_ev}


def umbrales(d):
    out = {}
    for ps in ("pasada1", "pasada2"):
        dp = d.get(ps) or {}
        out[ps] = {k: (None if dp.get(k) is None else float(dp[k]))
                   for k in ("mu_nti", "sd_nti", "u_nti1", "u_nti2", "sd_eti", "u_eti1", "u_eti2")}
    return out


def correr_serie(E, serie, brazos, origen, ref_brazo):
    """brazos: dict nombre -> (m13g, m15g). Devuelve registros y umbrales por brazo."""
    base_masks, umb = {}, {}
    for nb, (a, b) in brazos.items():
        m, d = E.detectar(a, b)
        base_masks[nb] = m
        umb[nb] = {"n_alertadas": int(m.sum()), **umbrales(d)}
    caja = np.array(E.box, float)
    caja[:, [0, -1]] = np.nan
    caja[[0, -1], :] = np.nan
    vec = np.zeros_like(next(iter(base_masks.values())))
    for m in base_masks.values():
        vec |= binary_dilation(m, structure=np.ones((3, 3), bool))
    regs = []
    for p in puntos(E, origen):
        r0 = {"escena": E.meta["clave"], "serie": serie, "d": p["d"], "az": p["az"],
              "cenit": E.geom["sensor_zenith"], "ref": ref_brazo}
        if "i" not in p:
            regs.append({**r0, "motivo": p["motivo"]})
            continue
        h = huella(p)
        r0.update({"offset_km": p["offset_km"], "dist_real_km": p["dist_real_km"], "n_huella": int(h.sum())})
        if not h.any():
            regs.append({**r0, "motivo": "huella_vacia"})
            continue
        fmax = np.unravel_index(np.argmax(p["w13"]), h.shape)
        r0["zona"] = None if not np.isfinite(caja[fmax]) else int(caja[fmax])
        if np.isnan(caja[h]).any() or any(np.isnan(a[h]).any() for a, _ in brazos.values()):
            regs.append({**r0, "motivo": "borde"})
            continue
        if (vec & h).any():
            regs.append({**r0, "motivo": "solapado"})
            continue
        for T in T_HOT:
            for nb, (a, b) in brazos.items():
                regs.append({**r0, "brazo": nb, "T": T, **vrp_minimo(E, a, b, p, T)})
    return regs, umb


def por_escena(esc):
    t0 = time.time()
    E = C.Escena(esc)
    regs, umb = [], {}
    mask, d = E.detectar(E.m13g, E.m15g)
    # Serie R
    s13, s15, _ = quitar_anomalia(E, E.m13g, E.m15g, mask)
    s13b, s15b, _ = quitar_anomalia(E, E.m13g, E.m15g, mask, k=9)
    org = celda_pico(E, mask)
    r, u = correr_serie(E, "R", {"R-con": (E.m13g, E.m15g), "R-sin": (s13, s15), "R-sin9": (s13b, s15b)}, org, "R-sin")
    regs += r
    umb["R"] = u
    umb["R"]["origen"] = org
    # Control C4 (ruido que duplica sd)
    n13, n15 = ruido(E, E.m13g, E.m15g, d["pasada1"]["sd_nti"])
    r, u = correr_serie(E, "N", {"N-sin": (E.m13g, E.m15g), "N-con": (n13, n15)}, org, "N-sin")
    regs += r
    umb["N"] = u
    # Serie T
    if esc["clave"] != CLAVE_FUENTE:
        parche = parche_fuente()
        crat = (int(round(E.pos[0])), int(round(E.pos[1])))
        brazos = {"T-sin": (E.m13g, E.m15g)}
        for s in ESCALAS_T:
            brazos[f"T-con-{s}"] = aplicar_parche(E.m13g, E.m15g, parche, crat, s)
        r, u = correr_serie(E, "T", brazos, crat, "T-sin")
        regs += r
        umb["T"] = u
    return esc["clave"], regs, umb, time.time() - t0


def main():
    C.utf8()
    escs = C.escenas()
    todos, umbs = [], {}
    with ProcessPoolExecutor(max_workers=5) as ex:
        for clave, regs, umb, seg in ex.map(por_escena, escs):
            print(f"{clave}: {len(regs)} registros en {seg:.0f} s", flush=True)
            todos += regs
            umbs[clave] = umb
    with open(C.AQUI / "resultados.jsonl", "w", encoding="utf-8", newline="") as fh:
        for r in todos:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    (C.AQUI / "umbrales.json").write_text(json.dumps(umbs, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
