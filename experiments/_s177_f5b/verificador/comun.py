# -*- coding: utf-8 -*-
"""Verificador V177: selector escrito desde cero (sin importar lib177 ni f5b_lib). Reutiliza SOLO: geometria del panel
guardada en p8_clases.json, TIF de referencia del volcan y sensor, volcanoes.yaml, chillan_base.json."""
import json, math, os, datetime as dt
import numpy as np
import yaml, rasterio
from rasterio.warp import transform as rtransform
from PIL import Image
from scipy import ndimage as ni

BASE = r"C:\Users\nmend\vrp-temporales"
F = BASE + r"\s177_f5b"
TMP = BASE + r"\s175_audit\f5b"
CH = "NevadosDeChillan"
ARCH = {CH: "ChillanNevadosde"}
TOL = {"VIIRS375": 0.75, "VIIRS750": 1.5, "MODIS": 3.0}
VOL = {v["name"]: v for v in yaml.safe_load(open(BASE + r"\s175_audit\main\volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
REFS = json.load(open(F + r"\orig\p6_tif_referencia_out.json", encoding="utf-8"))
P8 = [x for x in json.load(open(F + r"\orig\p8_clases.json", encoding="utf-8")) if x.get("vol") != "_CONTROL_"]
_g = {}


def hav(lat1, lon1, lat2, lon2):
    r = np.pi / 180
    a = np.sin((lat2 - lat1) * r / 2) ** 2 + np.cos(lat1 * r) * np.cos(lat2 * r) * np.sin((lon2 - lon1) * r / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def grilla(vol, b):
    if (vol, b) in _g:
        return _g[(vol, b)]
    ref = REFS[f"{ARCH.get(vol, vol)}|{b}"]["ref_sep"]
    fn = os.path.join(TMP, "tif_ref", ARCH.get(vol, vol) + "_" + os.path.basename(ref["path"]))
    with rasterio.open(fn) as ds:
        n, m = ds.height, ds.width
        T = ds.transform
        col, row = np.meshgrid(np.arange(m) + 0.5, np.arange(n) + 0.5)
        xs = T.a * col + T.b * row + T.c
        ys = T.d * col + T.e * row + T.f
        if str(ds.crs) != "EPSG:4326":
            lo, la = rtransform(ds.crs, "EPSG:4326", xs.ravel().tolist(), ys.ravel().tolist())
            lons, lats = np.array(lo).reshape(xs.shape), np.array(la).reshape(xs.shape)
        else:
            lons, lats = xs, ys
        e = abs(T.e)
    mc = (VOL[vol]["mirova_center_lat"], VOL[vol]["mirova_center_lon"])
    inner = hav(lats, lons, mc[0], mc[1]) <= VOL[vol]["inner_radius_km"]
    g = dict(n=n, lats=lats, lons=lons, mc=mc, inner=inner, celda=e * 111.0)
    _g[(vol, b)] = g
    return g


def png_path(x):
    return os.path.join(TMP, "png", x["png"].split("/")[-2] + "_" + os.path.basename(x["png"]))


def panel(x, g):
    """Recorte del panel con la geometria guardada [X0, Y0, W, H]. Filas y columnas de celda por pixel."""
    im = np.array(Image.open(png_path(x)).convert("RGB"))
    X0, Y0, W, H = x["geometria"]
    px = np.arange(math.ceil(X0), math.floor(X0 + W))
    py = np.arange(math.ceil(Y0), math.floor(Y0 + H))
    a = im[py[0]:py[-1] + 1, px[0]:px[-1] + 1]
    cx = np.clip(((px + 0.5 - X0) / W * g["n"]).astype(int), 0, g["n"] - 1)
    cy = np.clip(((py + 0.5 - Y0) / H * g["n"]).astype(int), 0, g["n"] - 1)
    return dict(a=a, L=a.astype(float).mean(axis=2), px=px, py=py, cx=cx, cy=cy, X0=X0, Y0=Y0, W=W, H=H, n=g["n"], inn=g["inner"][np.ix_(cy, cx)])


def blancas(P):
    """Componentes blancas (4 vecinos), con area, si toca el borde y mascara."""
    w = P["a"].min(axis=2) > 245
    lab, k = ni.label(w)
    alto, ancho = w.shape
    out = []
    if k:
        for i, sl in enumerate(ni.find_objects(lab), 1):
            m = lab == i
            toca = sl[0].start == 0 or sl[1].start == 0 or sl[0].stop == alto or sl[1].stop == ancho
            out.append(dict(area=int(m.sum()), toca=bool(toca), mask=m))
    return out


def sin_dato(P, regla, U=400):
    sd = np.zeros(P["L"].shape, bool)
    for c in blancas(P):
        if (regla == "A" and c["area"] >= 20) or (regla == "B" and (c["toca"] or c["area"] >= U)):
            sd |= c["mask"]
    return ni.binary_dilation(sd)


def mancha(P, g, regla="B", empates=True, Lover=None):
    """Devuelve dict con componentes (principal primero), o None."""
    L = P["L"] if Lover is None else Lover
    sd = sin_dato(P, regla)
    ok = P["inn"] & ~sd
    if not ok.any():
        return None
    mx = L[ok].max()
    ys, xs = np.where(ok & (L == mx))
    p0 = (ys[0], xs[0])
    c = ok & (L >= mx - 10)
    s8 = np.ones((3, 3), bool)
    sat = mx >= 245
    if empates and sat:
        lab, _ = ni.label(ni.binary_dilation(c, structure=s8), structure=s8)
        lab = lab * c
        ids = [i for i in np.unique(lab) if i]
        comps = [lab == i for i in ids]
        comps.sort(key=lambda m: -int(m.sum()))
    else:
        lab, _ = ni.label(c, structure=s8)
        comps = [lab == lab[p0]]
    out = []
    for m in comps:
        y, x = np.where(m)
        cm_y, cm_x = y.mean(), x.mean()
        r = int(np.clip((P["py"][0] + cm_y + 0.5 - P["Y0"]) / P["H"] * P["n"], 0, P["n"] - 1))
        cc = int(np.clip((P["px"][0] + cm_x + 0.5 - P["X0"]) / P["W"] * P["n"], 0, P["n"] - 1))
        cel = sorted(set(zip(P["cy"][y].tolist(), P["cx"][x].tolist())))
        fr = (P["py"][0] + cm_y + 0.5 - P["Y0"]) / P["H"] * P["n"] - 0.5
        fc = (P["px"][0] + cm_x + 0.5 - P["X0"]) / P["W"] * P["n"] - 0.5
        la_c = float(ni.map_coordinates(g["lats"], [[fr], [fc]], order=1, mode="nearest")[0])
        lo_c = float(ni.map_coordinates(g["lons"], [[fr], [fc]], order=1, mode="nearest")[0])
        out.append(dict(px=int(m.sum()), r=r, c=cc, cel=cel, la=float(g["lats"][r, cc]), lo=float(g["lons"][r, cc]), la_c=la_c, lo_c=lo_c, mask=m))
    return dict(mx=float(mx), sat=bool(sat), comps=out)


def resumen(s, g):
    rr = [c for k in s["comps"] for c in k["cel"]]
    return dict(la=s["comps"][0]["la"], lo=s["comps"][0]["lo"], la_c=s["comps"][0]["la_c"], lo_c=s["comps"][0]["lo_c"],
                lats=np.array([g["lats"][a, b] for a, b in rr]), lons=np.array([g["lons"][a, b] for a, b in rr]),
                nc=len(rr), ncomp=len(s["comps"]), sat=s["sat"], mx=s["mx"], px=s["comps"][0]["px"])


def clase(m, pt, dist, b, celda, g, control="any", sin_control=False):
    tol = TOL[b]
    if not sin_control:
        if dist is None:
            return "iv"
        tolc = max(tol, celda)
        if control == "any":
            ok = (np.abs(hav(m["lats"], m["lons"], g["mc"][0], g["mc"][1]) - dist) <= tolc).any()
        else:
            ok = abs(hav(m["la"], m["lo"], g["mc"][0], g["mc"][1]) - dist) <= tolc
        if not ok:
            return "iv"
    return "i" if hav(m["la"], m["lo"], pt[0], pt[1]) <= tol else "iii"


def fecha(s):
    return dt.datetime.strptime(s, "%Y-%m-%d %H:%M")


def geo_chillan():
    d = json.load(open(BASE + r"\s175_audit\v5b\chillan_base.json", encoding="utf-8"))
    return {(r["sensor"], str(r["datetime_utc"])[:16]): r for r in d["records"]}
