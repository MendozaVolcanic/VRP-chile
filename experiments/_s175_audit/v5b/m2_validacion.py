# -*- coding: utf-8 -*-
"""m2 (V5B): validar la regla de recorte en casos que el auditor nunca miro, con su nulo.

Fenomeno: si la lamina sirve de vara, la mancha caliente del panel cae donde esta el maximo del TIF de la misma pasada.
La regla fija se ajusto y se valido sobre los mismos 4 casos VIIRS (p3 y p7). Aca se toman casos nuevos elegidos por una
regla fija antes de ver resultados: i2_pares.csv de F5, dt < 2026-09-22, alerta de MIROVA con VRP >= 0,5 MW (hay foco
que mirar), TIF con adquisicion a <= 120 s y lamina con last_modified a 0 a 180 s despues del TIF (regla de p7), fuera
de los casos del auditor, muestra aleatoria semilla 175, hasta 25 por sensor.

Metodo A: f5b_lib.pixel_mas_claro (como p7, con mascara NaN del TIF). Metodo B: la misma geometria pero la mascara de
sin dato solo quita componentes blancas que tocan el borde del panel o de area >= 400 px, y el foco es la mancha de
lum >= max-10 que contiene el maximo; distancia al TIF por la celda mas cercana (B_min) y por el centroide (B_cen).

Nulos (dos): N1 misma lamina, otro panel que tenga dato (persistencia del foco: no separa pasadas, si separa el metodo
de una posicion arbitraria); N2 posicion uniforme dentro del inner (azar puro, 2000 sorteos por caso). Tasa de acierto
= fraccion con d <= tolerancia F5 (0,75 / 1,5 / 3 km) y fraccion a <= 1 celda.

Pregunta 1: si la regla no valiera, d A y d B serian del orden del radio del inner y similares a N2.
Pregunta 2: si el TIF o la lamina no fueran de la pasada, el OCR no hallaria la pasada (se cuenta, no se incluye) y la
correlacion panel-TIF seria baja (se reporta corr por caso con log10 del TIF, sin ajustar nada).
Control positivo: los 4 casos del auditor pasan por el mismo codigo y deben dar 0 o 1 celda con A.
Salida: m2_validacion.json y stdout.
"""
import csv, datetime as dt, json, os, random, sys, urllib.request, collections, math
import numpy as np
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__))
F5B = os.path.join(HERE, "..", "f5b")
sys.dont_write_bytecode = True
sys.path.insert(0, F5B)
import f5b_lib as L
import yaml
sys.stdout.reconfigure(encoding="utf-8")
TMP = r"C:\Users\nmend\vrp-temporales\s175_audit\v5b\m2"
os.makedirs(TMP, exist_ok=True)
AUD = r"C:\Users\nmend\vrp-temporales\s175_audit\f5b"
AUD_T = r"C:\Users\nmend\vrp-temporales\s175_audit\f5\tif_descargas"
INS = r"C:\Users\nmend\vrp-temporales\s175_audit\insumos"
RAW = "https://raw.githubusercontent.com/MendozaVolcanic/mirova-tif-archive/main/"
V = {v["name"]: v for v in yaml.safe_load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\main\volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
ARCH = {"NevadosDeChillan": "ChillanNevadosde"}
P = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
tif_idx = [r for r in csv.DictReader(open(INS + r"\tif_index.csv", encoding="utf-8")) if r["acquisition_utc"]]
png_idx = [r for r in csv.DictReader(open(INS + r"\png_index.csv", encoding="utf-8")) if r["kind"] == "Latest10NTI" and r["png_path"]]
pares = list(csv.DictReader(open(os.path.join(HERE, "..", "f5", "i2_pares.csv"), encoding="utf-8")))
AUDITOR = {("Lastarria", "VIIRS375", "2026-06-12 05:54"), ("Lastarria", "VIIRS375", "2026-08-09 05:48"), ("Lascar", "VIIRS750", "2026-06-21 05:30"), ("Isluga", "VIIRS375", "2026-09-22 05:42")}
AUD_MODIS = {("Lascar", "MODIS", h) for h in ("2026-06-27 01:35", "2026-06-24 08:00", "2026-06-21 07:45", "2026-07-30 07:55", "2026-06-14 01:20", "2026-06-17 01:40", "2026-07-09 07:40")}
TOPE = 300_000_000
bajado = [0]


def bajar(path, sub):
    d = os.path.join(TMP, sub)
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, path.split("/")[-2] + "_" + os.path.basename(path))
    if not os.path.exists(dst):
        if bajado[0] > TOPE:
            raise RuntimeError("tope de bytes")
        urllib.request.urlretrieve(RAW + path, dst)
        bajado[0] += os.path.getsize(dst)
    return dst


def buscar(r):
    va = ARCH.get(r["vol"], r["vol"])
    t0 = dt.datetime.strptime(r["dt"], "%Y-%m-%d %H:%M")
    tifs = [x for x in tif_idx if x["volcano"] == va and x["sensor"] == r["b"] and abs((P(x["acquisition_utc"]) - t0).total_seconds()) <= 120]
    if not tifs:
        return None
    tr = sorted(tifs, key=lambda x: x["last_modified_utc"])[0]
    tlm = P(tr["last_modified_utc"])
    pngs = [x for x in png_idx if x["volcano"] == va and x["sensor"] == r["b"] and 0 <= (P(x["last_modified_utc"]) - tlm).total_seconds() <= 180]
    if not pngs:
        return None
    return tr, sorted(pngs, key=lambda x: x["last_modified_utc"])[0], t0


def metodo_B(im, bb, g, inner, nan_tif):
    X0, Y0, W, Hh = L.geometria(bb)
    pan, px_x, px_y = L.recorte(im, X0, Y0, W, Hh)
    Lu = pan.astype(float).mean(axis=2)
    n = g["n"]
    cy, cx = L.celdas_de(px_x, px_y, X0, Y0, W, Hh, n)
    inner_p = inner[np.ix_(cy, cx)]
    bl = pan.min(axis=2) > 245
    lab, nl = ndimage.label(bl)
    sd = np.zeros(bl.shape, bool)
    borr = 0
    for i in range(1, nl + 1):
        m = lab == i
        a = int(m.sum())
        if m[0].any() or m[-1].any() or m[:, 0].any() or m[:, -1].any() or a >= 400:
            sd |= m
        elif a >= 20 and (m & inner_p).any():
            borr += 1
    sd = ndimage.binary_dilation(sd, iterations=1)
    if nan_tif is not None:
        sd |= nan_tif[np.ix_(cy, cx)]
    Lm = np.where(inner_p & ~sd, Lu, -1.0)
    if Lm.max() < 0:
        return None
    py, px = np.unravel_index(np.argmax(Lm), Lm.shape)
    cand = Lm >= Lm.max() - 10
    lab2, _ = ndimage.label(cand, structure=np.ones((3, 3)))
    man = lab2 == lab2[py, px]
    rr = cy[np.where(man)[0]]
    cc = cx[np.where(man)[1]]
    celdas = sorted(set(zip(rr.tolist(), cc.tolist())))
    pyc, pxc = ndimage.center_of_mass(man)
    ri = int(np.clip((px_y[0] + pyc + 0.5 - Y0) / Hh * n, 0, n - 1))
    ci = int(np.clip((px_x[0] + pxc + 0.5 - X0) / W * n, 0, n - 1))
    return dict(celdas=celdas, ri=ri, ci=ci, borr=borr, lum=float(Lm.max()), L=Lu, cy=cy, cx=cx, px_y=px_y, px_x=px_x)


def caso(r, etiqueta):
    b = buscar(r)
    if b is None:
        return None
    tr, pr, t0 = b
    tb = r["b"]
    vol = r["vol"]
    ftif = bajar(tr["tif_path"], "tif")
    fpng = bajar(pr["png_path"], "png")
    cab, pan = L.etiquetas(fpng)
    kk = [k for k, x in enumerate(pan) if x[1] and abs((dt.datetime.strptime(x[1], "%Y-%m-%d %H:%M:%S") - t0).total_seconds()) <= 120]
    o = {"etiqueta": etiqueta, "vol": vol, "b": tb, "dt": r["dt"], "vrp": r["vrp_mirova"], "dist_tabla": r["dist_mirova"], "fuente": r["fuente_dist"], "tif": tr["tif_path"], "png": pr["png_path"], "ocr_ok": bool(kk)}
    if not kk:
        return o
    k = kk[0]
    o["panel"] = k
    g = L.grilla(ftif)
    n = g["n"]
    mc = (V[vol]["mirova_center_lat"], V[vol]["mirova_center_lon"])
    inner = L.mascara_inner(g, mc, V[vol]["inner_radius_km"])
    nan_t = np.isnan(g["a"])
    am = np.where(inner & ~nan_t, g["a"], np.nan)
    iy, ix = np.unravel_index(np.nanargmax(am), am.shape)
    lat_t, lon_t = float(g["lats"][iy, ix]), float(g["lons"][iy, ix])
    tol = L.TOL[tb]
    cel = abs(g["transform"].e) * 111.0
    im = L.abrir_png(fpng)
    bb = L.bbox_marco(im, k)
    if bb is None:
        o["sin_marco"] = True
        return o
    d_mc_t = L.hav(lat_t, lon_t, *mc)
    try:
        dt_ = float(r["dist_mirova"])
        o["tif_reproduce_tabla"] = abs(d_mc_t - dt_) <= max(tol, cel)
    except ValueError:
        o["tif_reproduce_tabla"] = None
    h = L.pixel_mas_claro(im, bb, g, inner, nan_tif=nan_t)
    if h:
        o["d_A_km"] = round(L.hav(h["lat"], h["lon"], lat_t, lon_t), 3)
        o["d_A_celdas"] = round(float(np.hypot(h["rc"][0] - iy, h["rc"][1] - ix)), 2)
        o["lum_A"] = round(h["lum_max"], 1)
    B = metodo_B(im, bb, g, inner, nan_t)
    if B:
        dB = [L.hav(g["lats"][r_, c_], g["lons"][r_, c_], lat_t, lon_t) for r_, c_ in B["celdas"]]
        o["d_B_min_km"] = round(min(dB), 3)
        o["d_B_cen_km"] = round(L.hav(g["lats"][B["ri"], B["ci"]], g["lons"][B["ri"], B["ci"]], lat_t, lon_t), 3)
        o["d_B_cen_celdas"] = round(float(np.hypot(B["ri"] - iy, B["ci"] - ix)), 2)
        o["n_celdas_B"] = len(B["celdas"])
        o["borr"] = B["borr"]
        o["lum_B"] = B["lum"]
        la = np.log10(np.clip(g["a"], 1e-6, None))
        la = np.where(np.isfinite(la), la, np.nanmedian(la))
        v = la[np.ix_(B["cy"], B["cx"])]
        lu = B["L"]
        o["corr_panel_tif"] = round(float(np.corrcoef(v.ravel(), lu.ravel())[0, 1]), 3)
        # sensibilidad a la regla: mover la grilla +-1 celda en fila y columna
        o["corr_shift"] = {f"{dr},{dc}": round(float(np.corrcoef(la[np.ix_(np.clip(B["cy"] + dr, 0, n - 1), np.clip(B["cx"] + dc, 0, n - 1))].ravel(), lu.ravel())[0, 1]), 3)
                           for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))}
    o["tol"] = tol
    o["celda_km"] = round(cel, 3)
    # N2 azar uniforme dentro del inner
    idxs = np.argwhere(inner & ~nan_t)
    rng = np.random.default_rng(175)
    pick = idxs[rng.integers(0, len(idxs), 2000)]
    d2 = np.array([L.hav(g["lats"][a, c], g["lons"][a, c], lat_t, lon_t) for a, c in pick])
    o["N2_tasa_tol"] = round(float((d2 <= tol).mean()), 4)
    o["N2_tasa_1cel"] = round(float((d2 <= cel).mean()), 4)
    # N1 otro panel de la misma lamina con dato (A y B)
    otros = []
    for j in range(10):
        if j == k or not pan[j][1]:
            continue
        bbj = L.bbox_marco(im, j)
        if bbj is None:
            continue
        hj = L.pixel_mas_claro(im, bbj, g, inner, nan_tif=None)
        bj = metodo_B(im, bbj, g, inner, None)
        if hj and bj:
            dj = [L.hav(g["lats"][r_, c_], g["lons"][r_, c_], lat_t, lon_t) for r_, c_ in bj["celdas"]]
            otros.append((round(L.hav(hj["lat"], hj["lon"], lat_t, lon_t), 3), round(L.hav(g["lats"][bj["ri"], bj["ci"]], g["lons"][bj["ri"], bj["ci"]], lat_t, lon_t), 3), round(min(dj), 3)))
    o["N1_otros_paneles"] = otros
    return o


random.seed(175)
cand = collections.defaultdict(list)
for r in pares:
    if r["dt"] >= "2026-09-22" or (r["vol"], r["b"], r["dt"]) in AUDITOR | AUD_MODIS:
        continue
    try:
        v_ = float(r["vrp_mirova"])
    except ValueError:
        continue
    if v_ >= 0.5:
        cand[r["b"]].append(r)
casos = []
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    ls = sorted(cand[b], key=lambda r: (r["vol"], r["dt"]))
    random.shuffle(ls)
    n_ok = 0
    prob = 0
    for r in ls:
        if n_ok >= 25:
            break
        prob += 1
        if buscar(r) is None:
            continue
        casos.append((r, "nuevo"))
        n_ok += 1
    print("candidatos", b, len(ls), "probados", prob, "con TIF y lamina", n_ok, "por volcan", collections.Counter(c[0]["vol"] for c in casos if c[0]["b"] == b))
for r in pares:
    if (r["vol"], r["b"], r["dt"]) in AUDITOR:
        casos.append((r, "auditor_viirs"))
    if (r["vol"], r["b"], r["dt"]) in AUD_MODIS:
        casos.append((r, "auditor_modis"))
out = []
for r, et in casos:
    try:
        o = caso(r, et)
    except Exception as e:
        print("ERROR", r["vol"], r["b"], r["dt"], repr(e), flush=True)
        continue
    if o:
        out.append(o)
    json.dump(out, open(os.path.join(HERE, "m2_validacion.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("bytes bajados", bajado[0])


def tasas(g, campo, tolcampo="tol"):
    g = [o for o in g if campo in o]
    if not g:
        return "n=0"
    return f"n={len(g)} tasa<=tol {sum(o[campo] <= o[tolcampo] for o in g)}/{len(g)}; <=1 celda {sum(o[campo] <= o['celda_km'] + 1e-6 for o in g)}/{len(g)}; p50 {np.median([o[campo] for o in g]):.2f} p90 {np.percentile([o[campo] for o in g], 90):.2f} km"


for et in ("auditor_viirs", "auditor_modis", "nuevo"):
    for b in ("VIIRS375", "VIIRS750", "MODIS"):
        g = [o for o in out if o["etiqueta"] == et and o["b"] == b and o.get("ocr_ok") and "d_A_km" in o]
        if not g:
            continue
        print(f"--- {et} {b}")
        print("  A      :", tasas(g, "d_A_km"))
        print("  B cen  :", tasas(g, "d_B_cen_km"))
        print("  B min  :", tasas(g, "d_B_min_km"))
        print("  N2 azar en inner: tasa<=tol media", round(float(np.mean([o["N2_tasa_tol"] for o in g])), 3), " <=1 celda media", round(float(np.mean([o["N2_tasa_1cel"] for o in g])), 3))
        n1 = [(x[0], x[1], x[2], o["tol"]) for o in g for x in o["N1_otros_paneles"]]
        if n1:
            print("  N1 otros paneles misma lamina (n=%d): A<=tol %.3f, B cen<=tol %.3f, B min<=tol %.3f" % (len(n1), np.mean([x[0] <= x[3] for x in n1]), np.mean([x[1] <= x[3] for x in n1]), np.mean([x[2] <= x[3] for x in n1])))
        print("  corr panel-TIF p50", round(float(np.median([o["corr_panel_tif"] for o in g if "corr_panel_tif" in o])), 3), "; corr <0,5 en", sum(1 for o in g if o.get("corr_panel_tif", 1) < 0.5))
        print("  TIF max reproduce tabla:", sum(1 for o in g if o.get("tif_reproduce_tabla")), "de", len(g), "; A borro una mancha en", sum(1 for o in g if o.get("borr", 0) > 0))
print("OCR no hallo la pasada:", sum(1 for o in out if not o.get("ocr_ok")), "de", len(out))
