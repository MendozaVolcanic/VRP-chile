# -*- coding: utf-8 -*-
"""V177 v03. Pregunta: la mascara corregida conserva la mancha y solo la mancha?

Fenomeno: blanco en la lamina es saturacion de la paleta O sin dato. Una mancha de calor tiene halo (vecinos grises claros, porque el NTI baja
gradualmente desde el foco y la lamina dibuja cada celda). Un hueco de sin dato chico tiene borde duro contra fondo oscuro. Si la regla B guarda huecos,
aparecen manchas falsas.
Pre-registro:
 A. Por cada una de las 35 laminas donde A y B difieren: halo = media de L en el anillo de 1 a 3 px alrededor de la componente blanca borrada por A, contra mediana del panel; area;
    relacion con nuestros pixeles alertados (Chillan). Un halo igual a la mediana del panel seria un hueco.
 B. Control: mismas medidas en componentes blancas grandes que SI son sin dato (toca borde o >= 400 px).
 C. Tautologia del control de no-cambio: en las 268 laminas sin componente borrada, cuantos pixeles del inner distinguen la mascara A de la B. Si 0 en todas, 268 de 268 no podia fallar.
 D. Las 4 protegidas de 351: distancia a centroide, a celda mas cercana, a celda mas lejana, y a las celdas que reproducen la Distancia_km de la tabla.
 E. Que selector mueve cada una: A, C1, C2, con control por centroide, any y sin control.
 F. Limite de lo que la mancha puede excluir: fraccion de pasadas con alguna celda de la mancha a mas de la tolerancia de nuestro punto.
Salida: stdout.
"""
import os, sys, pickle, collections
import numpy as np
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from comun import *
from scipy import ndimage as ni

R = pickle.load(open(os.path.join(HERE, "v01_manchas.pkl"), "rb"))
s8 = np.ones((3, 3), bool)
filas = []
sd_grandes = []
inner_dif = collections.Counter()
for o in R:
    g = grilla(o["vol"], o["b"])
    P = panel(o["x"], g)
    comps = blancas(P)
    med = np.median(P["L"])
    sdA, sdB = sin_dato(P, "A"), sin_dato(P, "B")
    bor = [c for c in comps if (c["mask"] & P["inn"]).any() and not c["toca"] and 20 <= c["area"] < 400]
    dif_inner = int(((sdA ^ sdB) & P["inn"]).sum())
    if not bor:
        inner_dif[dif_inner > 0] += 1
    for c in bor:
        an = ni.binary_dilation(c["mask"], structure=s8, iterations=3) & ~ni.binary_dilation(c["mask"], structure=s8, iterations=0 + 1) & ~sdB
        an1 = ni.binary_dilation(c["mask"], structure=s8, iterations=1) & ~c["mask"]
        filas.append(dict(vol=o["vol"], b=o["b"], sensor=o["sensor"], dt=o["dt"], area=c["area"], halo=float(P["L"][an].mean()), halo1=float(P["L"][an1].mean()), med=float(med), p99=float(np.percentile(P["L"], 99)), vrp=o["vrp"]))
    for c in comps:
        if c["toca"] or c["area"] >= 400:
            an = ni.binary_dilation(c["mask"], structure=s8, iterations=3) & ~ni.binary_dilation(c["mask"], structure=s8) & ~sdB
            if an.sum() > 5:
                sd_grandes.append(dict(area=c["area"], halo=float(P["L"][an].mean()), med=float(med), vol=o["vol"], b=o["b"]))

print("A. 35 laminas: componentes blancas 20 a 399 px en el inner")
print(f"   componentes: {len(filas)}; laminas {len({(f['vol'], f['sensor'], f['dt']) for f in filas})}")
for k, f_ in (("Chillan V750", lambda f: f["vol"] == CH and f["b"] == "VIIRS750"), ("Chillan V375", lambda f: f["vol"] == CH and f["b"] == "VIIRS375"), ("Chillan MODIS", lambda f: f["vol"] == CH and f["b"] == "MODIS"), ("Caulle", lambda f: f["vol"] != CH)):
    ss = [f for f in filas if f_(f)]
    print(f"   {k:14s} n={len(ss):2d} area p50 {np.median([f['area'] for f in ss]):.0f} rango {min(f['area'] for f in ss)} a {max(f['area'] for f in ss)}; halo-mediana panel p10 {np.percentile([f['halo'] - f['med'] for f in ss], 10):.1f} p50 {np.median([f['halo'] - f['med'] for f in ss]):.1f}; halo anillo 1 px p50 {np.median([f['halo1'] for f in ss]):.0f}; mediana panel p50 {np.median([f['med'] for f in ss]):.0f}; VRP MIROVA p10 {np.percentile([f['vrp'] for f in ss], 10):.1f} p50 {np.median([f['vrp'] for f in ss]):.1f}")
for f in sorted(filas, key=lambda f: f["halo"] - f["med"])[:6]:
    print("   halo mas bajo:", f["vol"], f["sensor"], f["dt"], "area", f["area"], "halo", round(f["halo"], 1), "mediana panel", round(f["med"], 1), "VRP", f["vrp"])
print("B. Componentes sin dato (toca borde o >= 400 px): n", len(sd_grandes), "halo-mediana panel p10 %.1f p50 %.1f p90 %.1f" % tuple(np.percentile([f["halo"] - f["med"] for f in sd_grandes], [10, 50, 90])))
print("C. Laminas sin componente borrada: pixeles del inner donde A y B difieren >0:", dict(inner_dif))


def cel_mancha(m, pt, g, dist, tolc):
    dm = hav(m["lats"], m["lons"], pt[0], pt[1])
    dc = hav(m["lats"], m["lons"], g["mc"][0], g["mc"][1])
    tab = dm[np.abs(dc - dist) <= tolc] if dist is not None else np.array([])
    tabe = dm[np.abs(dc - dist) <= g["celda"]] if dist is not None else np.array([])
    return dm, dc, tab, tabe


print("\nD/E. Las 4 protegidas de 351")
CUAT = [("VIIRS_NOAA21", "2026-10-18 05:06"), ("VIIRS_NOAA20_750", "2026-10-10 06:54"), ("VIIRS_NOAA20_750", "2026-10-16 06:42"), ("VIIRS_NOAA21_750", "2026-10-29 06:42")]
for sen, d_ in CUAT:
    o = next(x for x in R if x["vol"] == CH and x["sensor"] == sen and x["dt"] == d_)
    g = grilla(CH, o["b"])
    tolc = max(TOL[o["b"]], o["celda"])
    res = {}
    for k in ("A", "C1", "C2"):
        res[k] = (clase(o[k], o["pt"], o["dist"], o["b"], o["celda"], g, "cent"), clase(o[k], o["pt"], o["dist"], o["b"], o["celda"], g, "any"), clase(o[k], o["pt"], o["dist"], o["b"], o["celda"], g, "any", True), round(float(hav(o[k]["la"], o[k]["lo"], *o["pt"])), 2))
    dm, dc, tab, tabe = cel_mancha(o["C2"], o["pt"], g, o["dist"], tolc)
    dmc_pt = float(hav(g["mc"][0], g["mc"][1], *o["pt"]))
    print(f"  {sen} {d_}: tabla Dist {o['dist']} km (tolc {tolc:.2f}); nuestro punto a {dmc_pt:.2f} km del centro MIROVA; celdas {o['C2']['nc']}")
    print(f"     clase (control centroide, any, sin control; d_cent): A {res['A']} | C1 {res['C1']} | C2 {res['C2']}")
    print(f"     d(nuestro, celda): min {dm.min():.2f} max {dm.max():.2f}; d(centroide, centro MIROVA) {float(hav(o['C2']['la'], o['C2']['lo'], g['mc'][0], g['mc'][1])):.2f}; d(celdas, centro MIROVA) {dc.min():.2f} a {dc.max():.2f}")
    print(f"     celdas compatibles con la tabla a +- 1 celda ({len(tabe)}): d a nuestro punto {('%.2f a %.2f' % (tabe.min(), tabe.max())) if len(tabe) else 'ninguna'}; a +- tolc ({len(tab)}): {('%.2f a %.2f' % (tab.min(), tab.max())) if len(tab) else 'ninguna'}")

print("\nF. Lo que la mancha no puede excluir (Chillan, C2): por pasada, distancia de nuestro punto a la celda mas lejana de la mancha y a las celdas que reproducen la tabla a +- 1 celda")
for b in ("VIIRS375", "VIIRS750"):
    ss = [o for o in R if o["vol"] == CH and o["b"] == b]
    tol = TOL[b]
    g = grilla(CH, b)
    dmax = np.array([hav(o["C2"]["lats"], o["C2"]["lons"], *o["pt"]).max() for o in ss])
    ntab, medt, sin_t, cls = 0, [], 0, collections.Counter()
    for o in ss:
        if o["dist"] is None:
            continue
        dm, dc, tab, tabe = cel_mancha(o["C2"], o["pt"], g, o["dist"], 0)
        if len(tabe) == 0:
            sin_t += 1
            continue
        medt.append(float(np.median(tabe)))
        cls["<=tol" if np.median(tabe) <= tol else ">tol"] += 1
    medt = np.array(medt)
    print(f"  {b} n={len(ss)} tol {tol}: dmax p50 {np.median(dmax):.2f} p90 {np.percentile(dmax, 90):.2f} max {dmax.max():.2f}; con alguna celda a mas de tol: {(dmax > tol).sum()} ({(dmax > tol).mean():.2f}); a mas de 1 km: {(dmax > 1).sum()}")
    print(f"     celda que reproduce la tabla a +-1 celda: pasadas sin ninguna {sin_t}; d mediana a nuestro punto p50 {np.median(medt):.2f} p90 {np.percentile(medt, 90):.2f} max {medt.max():.2f}; {dict(cls)}")
    # centroide vs distancia de la tabla
    dcent = np.array([float(hav(o["C2"]["la"], o["C2"]["lo"], g["mc"][0], g["mc"][1])) for o in ss if o["dist"] is not None])
    dist = np.array([o["dist"] for o in ss if o["dist"] is not None])
    print(f"     d(centroide, centro MIROVA) p50 {np.median(dcent):.2f}; Dist tabla p50 {np.median(dist):.2f}; tabla - centroide p50 {np.median(dist - dcent):+.2f} p90 {np.percentile(dist - dcent, 90):+.2f}; correlacion {np.corrcoef(dcent, dist)[0, 1]:+.2f}; n={len(dist)}")
