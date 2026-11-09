# -*- coding: utf-8 -*-
"""lib177: selector de la mancha térmica en la lámina Latest10NTI de MIROVA (copia corregida de f5b_lib.pixel_mas_claro) y
clasificación de coincidencia, un solo código para el observado y para el nulo.

Fenómeno: en una erupción el foco satura la paleta y la lámina lo dibuja como una mancha blanca de varias celdas. El
«sin dato» (fuera de la franja del sensor) también es blanco, pero es enorme (>= 2000 px, o toca el borde del panel).
F5b borraba toda componente blanca >= 20 px, es decir también la mancha (V5B-01). Acá sólo es «sin dato» la componente
blanca que toca el borde del panel o de área >= UMBRAL_SIN_DATO (400 px; el histograma de f5b no tiene componentes
entre 200 y 2000 px, así que cualquier umbral en ese hueco da lo mismo; s02 lo recuenta).

Tres selectores, todos sobre la misma geometría, grilla prestada y recorte de f5b_lib (no se tocan):
  A  = el de F5b tal cual (f5b_lib.pixel_mas_claro, sin dato = componente blanca >= 20 px).
  C1 = lo mínimo: A con la máscara de sin dato corregida; el resto igual (píxel más claro, mancha = componente
       8-vecinos a menos de 10 niveles del máximo, posición = centro de masa de la mancha ajustado a celda).
  C2 = C1 + empates (V5B-02): si el máximo está saturado (lum >= 245) los píxeles saturados separados por un hueco de 1 px
       pertenecen a la misma mancha (dilatación de 1 px para unir) y se guardan TODAS las componentes; la principal es la de
       mayor área (desempate: la primera en orden de barrido). Sin saturación, C2 = C1 exactamente.
Qué es «el píxel»: en una mancha saturada la lámina NO ordena los píxeles (todos 255). Por eso C2 devuelve la mancha (conjunto
de celdas) y su centroide, nunca «el píxel». d_cent = distancia del punto nuestro al centroide de la componente principal;
d_min = distancia a la celda más cercana de cualquiera de las componentes (más blando: «cae sobre o junto a la mancha»).
"""
import math, os, sys
import numpy as np
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "orig"))
sys.dont_write_bytecode = True
import f5b_lib as L

UMBRAL_SIN_DATO = 400
SAT = 245.0   # lum media >= 245 = saturado (el blanco de la paleta; coincide con la definición de «blanco» de f5b: min RGB > 245)


def preparar(im, bb, g):
    X0, Y0, W, Hh = L.geometria(bb)
    pan, px_x, px_y = L.recorte(im, X0, Y0, W, Hh)
    n = g["n"]
    cy, cx = L.celdas_de(px_x, px_y, X0, Y0, W, Hh, n)
    return dict(pan=pan, Lu=pan.astype(float).mean(axis=2), cy=cy, cx=cx, inner_p=g["inner"][np.ix_(cy, cx)],
                blanco=pan.min(axis=2) > 245, px_x=px_x, px_y=px_y, X0=X0, Y0=Y0, W=W, Hh=Hh, n=n)


def componentes_blancas(P):
    lab, nl = ndimage.label(P["blanco"])
    out = []
    for i in range(1, nl + 1):
        m = lab == i
        toca = bool(m[0].any() or m[-1].any() or m[:, 0].any() or m[:, -1].any())
        out.append(dict(area=int(m.sum()), toca=toca, en_inner=bool((m & P["inner_p"]).any()), mask=m))
    return out


def mascara_sin_dato(P, regla="B", umbral=UMBRAL_SIN_DATO):
    """regla 'A' = F5b (area >= 20); 'B' = toca el borde del panel o area >= umbral."""
    sd = np.zeros(P["blanco"].shape, bool)
    for c in componentes_blancas(P):
        if (regla == "A" and c["area"] >= 20) or (regla == "B" and (c["toca"] or c["area"] >= umbral)):
            sd |= c["mask"]
    return ndimage.binary_dilation(sd, iterations=1)


def _celda_de_centro(P, mask):
    pyc, pxc = ndimage.center_of_mass(mask)
    ri = int(np.clip((P["px_y"][0] + pyc + 0.5 - P["Y0"]) / P["Hh"] * P["n"], 0, P["n"] - 1))
    ci = int(np.clip((P["px_x"][0] + pxc + 0.5 - P["X0"]) / P["W"] * P["n"], 0, P["n"] - 1))
    return ri, ci


def seleccionar(P, g, regla_sd="B", empates=True, umbral=UMBRAL_SIN_DATO):
    """Devuelve dict con la mancha (principal y todas las componentes) o None. regla_sd 'A' + empates False = F5b."""
    sd = mascara_sin_dato(P, regla_sd, umbral)
    Lm = np.where(P["inner_p"] & ~sd, P["Lu"], -1.0)
    if Lm.max() < 0:
        return None
    py, px = np.unravel_index(np.argmax(Lm), Lm.shape)
    mx = float(Lm.max())
    cand = Lm >= mx - 10
    saturado = mx >= SAT
    if empates and saturado:
        lab_d, _ = ndimage.label(ndimage.binary_dilation(cand, structure=np.ones((3, 3)), iterations=1), structure=np.ones((3, 3)))
        lab2 = np.where(cand, lab_d, 0)
    else:
        lab2, _ = ndimage.label(cand, structure=np.ones((3, 3)))
        lab2 = np.where(lab2 == lab2[py, px], lab2, 0)
    ids = [i for i in np.unique(lab2) if i > 0]
    comps = []
    for i in ids:
        m = lab2 == i
        ri, ci = _celda_de_centro(P, m)
        yy, xx = np.where(m)
        celdas = sorted(set(zip(P["cy"][yy].tolist(), P["cx"][xx].tolist())))
        comps.append(dict(px=int(m.sum()), rc=[ri, ci], lat=float(g["lats"][ri, ci]), lon=float(g["lons"][ri, ci]),
                          celdas=celdas, contiene_max=bool(m[py, px])))
    # principal: la que contiene el máximo (sin empates) o la de mayor área (con empates y saturado)
    if empates and saturado:
        comps.sort(key=lambda c: (-c["px"]))
    else:
        comps.sort(key=lambda c: (not c["contiene_max"]))
    sin_dato_en_inner = bool((sd & P["inner_p"]).any())
    return dict(lum_max=mx, saturado=bool(saturado), comps=comps, n_comps=len(comps), sin_dato_toca_inner=sin_dato_en_inner,
                lum_p99_panel=float(np.percentile(P["Lu"], 99)), lat=comps[0]["lat"], lon=comps[0]["lon"], rc=comps[0]["rc"], px_principal=comps[0]["px"])


def hav_vec(lat, lon, lats, lons):
    p = np.pi / 180.0
    a = np.sin((lats - lat) * p / 2) ** 2 + np.cos(lat * p) * np.cos(lats * p) * np.sin((lons - lon) * p / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


class Mancha:
    """Mancha ya reducida a lat/lon de sus celdas, para medir contra cualquier punto (nuestro, de otra pasada o desplazado)."""
    def __init__(self, d, g, mc):
        cs = [c for comp in d["comps"] for c in comp["celdas"]]
        self.lats = np.array([g["lats"][r, c] for r, c in cs])
        self.lons = np.array([g["lons"][r, c] for r, c in cs])
        self.lat, self.lon = d["lat"], d["lon"]
        self.d_mc_cells = hav_vec(mc[0], mc[1], self.lats, self.lons)
        self.d_mc_cent = float(L.hav(self.lat, self.lon, *mc))
        self.n_celdas = len(cs)
        self.n_comps = d["n_comps"]
        self.saturado = d["saturado"]

    def d_cent(self, la, lo):
        return float(L.hav(self.lat, self.lon, la, lo))

    def d_min(self, la, lo):
        return float(hav_vec(la, lo, self.lats, self.lons).min())

    def ctrl_cent(self, dist, tolc):
        return abs(self.d_mc_cent - dist) <= tolc

    def ctrl_any(self, dist, tolc):
        return bool((np.abs(self.d_mc_cells - dist) <= tolc).any())


def clase(m, punto, dist, b, celda_km, control="any", metrica="cent", sin_control=False):
    """UNA función para el observado y para el nulo. punto = (lat, lon) de lo que se compara con la mancha (en el observado,
    nuestro final_hotspot; en el nulo, el de otra pasada). Devuelve 'i', 'iii' o 'iv' (control fallido o sin distancia)."""
    tol = L.TOL[b]
    tolc = max(tol, celda_km)
    if not sin_control:
        if dist is None:
            return "iv"
        ok = m.ctrl_any(dist, tolc) if control == "any" else m.ctrl_cent(dist, tolc)
        if not ok:
            return "iv"
    d = m.d_cent(*punto) if metrica == "cent" else m.d_min(*punto)
    return "i" if d <= tol else "iii"
