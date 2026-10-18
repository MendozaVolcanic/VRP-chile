# -*- coding: utf-8 -*-
"""Paso 4: A61 de las 62 movidas de P4.

(1) Radio (todas): la Distancia_km de MIROVA se mide desde mirova_center y viene cuantizada a celdas del sensor
    (D15). Se compara con la distancia de cada cumulo (C0, K) al mismo punto. Es una COTA: sirve para descartar que
    un cumulo sea el objeto de MIROVA, no para identificarlo (A93, A107).
(2) Imagen (las que tienen GeoTIFF): campo de MIROVA (radiancia MIR, EPSG:4326). Anomalia = valor menos la mediana
    del anillo de 2 a 5 celdas. "Objeto de MIROVA" = celda de mayor anomalia sobre el anillo de radio Distancia_km
    alrededor de mirova_center (la direccion la pone la imagen, el radio lo pone MIROVA). Se mide la distancia de C0
    y de K a ese objeto. Imagen propia (mismo granulo) = sesgo de ganador A109: se dice. Otra pasada de la misma
    noche (45-120 min) = control independiente.
(3) Nulo del instrumento (A110): el mismo procedimiento con un radio falso (Distancia_km + 1,5 km y - 1,5 km
    cuando cabe) debe dar objetos de anomalia menor que el del radio verdadero en la mayoria de las imagenes; si no,
    el anillo no esta identificando nada.
"""
import json, math, sys, statistics, collections
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage
sys.stdout.reconfigure(encoding="utf-8")
import yaml
RAIZ = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile")
Y = {v["name"]: v for v in yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
T = json.load(open('s1_tabla.json', encoding='utf-8'))
EMP = {e['k']: e for e in json.load(open('s2_emparejar.json', encoding='utf-8'))}
CELDA = {"VIIRS375": 0.375, "VIIRS750": 0.75, "MODIS": 1.0}
EMPATE_KM = 0.3


def hav(a, b, c, d):
    R = 6371.0088
    p1, p2 = math.radians(a), math.radians(c)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def rumbo(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c); dl = math.radians(d - b)
    return (math.degrees(math.atan2(math.sin(dl) * math.cos(p2), math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl))) + 360) % 360


def card(b):
    return ["N", "NE", "E", "SE", "S", "SO", "O", "NO"][int((b + 22.5) // 45) % 8]


yy, xx = np.mgrid[-5:6, -5:6]; rr = np.hypot(yy, xx)
ANILLO = (rr >= 2) & (rr <= 5)
_cache = {}


def cargar(path):
    if path in _cache: return _cache[path]
    ds = rasterio.open(path); a = ds.read(1).astype(float)
    if ds.nodata is not None: a[a == ds.nodata] = np.nan
    bg = ndimage.generic_filter(a, np.nanmedian, footprint=ANILLO, mode='nearest')
    an = a - bg
    rows, cols = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    xs, ys = rasterio.transform.xy(ds.transform, rows.ravel(), cols.ravel())
    lon = np.array(xs).reshape(a.shape); lat = np.array(ys).reshape(a.shape)
    cx = (ds.bounds.left + ds.bounds.right) / 2; cy = (ds.bounds.top + ds.bounds.bottom) / 2
    res_km = ds.res[1] * 111.2
    _cache[path] = (ds, a, an, lat, lon, cx, cy, res_km)
    return _cache[path]


def dist_grid(lat, lon, la, lo):
    R = 6371.0088
    p1 = np.radians(lat); p2 = math.radians(la)
    h = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * math.cos(p2) * np.sin(np.radians(lo - lon) / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(h))


def objeto(an, lat, lon, ml, mo, dkm, tol, vl, vo, lim):
    dm = dist_grid(lat, lon, ml, mo); dv = dist_grid(lat, lon, vl, vo)
    m = (np.abs(dm - dkm) <= tol) & (dv <= lim) & np.isfinite(an)
    if not m.any(): return None
    i = np.unravel_index(np.nanargmax(np.where(m, an, -np.inf)), an.shape)
    return i, float(an[i])


def en(an, lat, lon, la, lo):
    d = dist_grid(lat, lon, la, lo); i = np.unravel_index(np.argmin(d), d.shape)
    r0, c0 = i
    w = an[max(r0 - 1, 0):r0 + 2, max(c0 - 1, 0):c0 + 2]
    return float(an[i]), float(np.nanmax(w))


filas = []
nulo = []
for m in T:
    vol, s = m["vol"], m["s"]; y = Y[vol]
    vl, vo, ml, mo = y["vent_lat"], y["vent_lon"], y["mirova_center_lat"], y["mirova_center_lon"]
    cons = [f for f in m["filas_mirova"] if f["source"] == "CONS" and f["dist"] is not None]
    ocr = [f for f in m["filas_mirova"] if f["source"] == "OCR" and f["dist"] is not None]
    fref = (cons or ocr or [None])[0]
    dmir = fref["dist"] if fref else None
    tolr = CELDA[s] * 0.5 + 0.1
    r = {k: m[k] for k in ("w", "k", "vol", "s", "t", "prot_A", "solo_ocr", "decide", "mov_km", "vrp_ref", "plataforma")}
    r["C0"], r["K"] = m["C0"], m["K"]
    r["mir_dist"] = dmir; r["mir_fuente"] = fref["source"] if fref else None
    r["mir_dist_otras"] = [(f["source"], f["dist"]) for f in m["filas_mirova"]]
    r["d_mcenter_vent"] = round(hav(ml, mo, vl, vo), 2)
    if dmir is not None:
        for lado in ("C0", "K"):
            r[lado + "_radio_ok"] = abs(r[lado]["d_mcenter"] - dmir) <= tolr
            r[lado + "_radio_err"] = round(r[lado]["d_mcenter"] - dmir, 2)
    # imagenes
    e = EMP[m["k"]]; imgs = []
    if e["near"] and e["near"]["dentro15"]:
        imgs.append(("propia" if e["near"]["propia"] else "reciclada", e["near"]["tif"], 0))
    pref = {'VIIRS375': 0, 'VIIRS750': 1, 'MODIS': 2}
    ot = sorted([o for o in e["otras"] if o["propia"]], key=lambda o: (pref[o['sensor']], abs(o['dt_min'])))
    if ot: imgs.append(("otra", ot[0]["tif"], ot[0]["dt_min"]))
    r["imagenes"] = []
    lim = max(y["inner_radius_km"], 5) + 3
    for tipo, tif, dtm in imgs:
        p = Path('tif') / tif.replace('data/tif/', '').replace('/', '_')
        if not p.exists(): continue
        ds, a, an, lat, lon, cx, cy, res_km = cargar(str(p))
        img = {"tipo": tipo, "tif": tif, "dt_min": dtm, "crs": str(ds.crs), "res_km": round(res_km, 3),
               "centro_vs_mcenter_km": round(hav(cy, cx, ml, mo), 2)}
        sd = float(np.nanstd(an[dist_grid(lat, lon, vl, vo) <= 15]))
        img["sd_anom"] = sd
        for lado in ("C0", "K"):
            ex, mx = en(an, lat, lon, r[lado]["lat"], r[lado]["lon"])
            img[lado + "_anom"] = round(ex / sd, 2); img[lado + "_anom3"] = round(mx / sd, 2)
        if dmir is not None:
            tol = tolr + res_km * 0.5
            ob = objeto(an, lat, lon, ml, mo, dmir, tol, vl, vo, lim)
            if ob:
                (i, j), val = ob; ola, olo = float(lat[i, j]), float(lon[i, j])
                img["obj"] = {"lat": round(ola, 5), "lon": round(olo, 5), "z": round(val / sd, 2),
                              "d_vent": round(hav(vl, vo, ola, olo), 2), "card": card(rumbo(vl, vo, ola, olo))}
                for lado in ("C0", "K"):
                    img[lado + "_a_obj"] = round(hav(ola, olo, r[lado]["lat"], r[lado]["lon"]), 2)
                # nulo: radios falsos
                zs = []
                for dd in (dmir + 1.5, dmir - 1.5):
                    if dd < 0.4: continue
                    o2 = objeto(an, lat, lon, ml, mo, dd, tol, vl, vo, lim + 1.5)
                    if o2: zs.append(o2[1] / sd)
                if zs: nulo.append((m["k"], tipo, val / sd, max(zs)))
        r["imagenes"].append(img)
    # veredicto por movida: imagen propia si hay, si no la otra; reciclada cuenta como otra pasada
    ver = "sin imagen"; base = None
    orden = sorted(r["imagenes"], key=lambda i: {"propia": 0, "otra": 1, "reciclada": 2}[i["tipo"]])
    for img in orden:
        if "obj" in img:
            base = img; dc, dk = img["C0_a_obj"], img["K_a_obj"]
            ver = "K acerca" if dk < dc - EMPATE_KM else ("K aleja" if dk > dc + EMPATE_KM else "indistinto")
            break
    r["veredicto_imagen"] = ver; r["base_imagen"] = base["tipo"] if base else None
    # consistencia entre imagen propia y otra
    vv = []
    for img in r["imagenes"]:
        if "obj" in img:
            dc, dk = img["C0_a_obj"], img["K_a_obj"]
            vv.append((img["tipo"], "K acerca" if dk < dc - EMPATE_KM else ("K aleja" if dk > dc + EMPATE_KM else "indistinto")))
    r["veredictos_por_imagen"] = vv
    # radio
    if dmir is None: rv = "sin distancia"
    else:
        c, k = r["C0_radio_ok"], r["K_radio_ok"]
        rv = {(True, True): "ambos compatibles", (False, False): "ninguno compatible",
              (True, False): "solo C0 compatible", (False, True): "solo K compatible"}[(c, k)]
    r["veredicto_radio"] = rv
    filas.append(r)

json.dump({"filas": filas, "nulo": nulo}, open('s4_analisis.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ------------------------------------------------ impresion
print("NULO del anillo (z del objeto con radio verdadero vs mejor radio falso +-1,5 km):")
gana = sum(1 for x in nulo if x[2] > x[3]); print("  verdadero > falso en %d de %d imagenes" % (gana, len(nulo)))
for x in nulo: print("   %-40s %-9s z_ver=%.2f z_falso=%.2f" % x)
print()
for r in filas:
    print("%s %-42s A=%d %s | C0 %.2f %-2s mc %.2f | K %.2f %-2s mc %.2f | MIR %s(%s) radio: %s | img: %s [%s] %s" % (
        r["w"], r["k"], r["prot_A"], r["plataforma"], r["C0"]["d_vent"], r["C0"]["card"], r["C0"]["d_mcenter"],
        r["K"]["d_vent"], r["K"]["card"], r["K"]["d_mcenter"], r["mir_dist"], r["mir_fuente"], r["veredicto_radio"],
        r["veredicto_imagen"], r["base_imagen"], r["veredictos_por_imagen"]))
    for img in r["imagenes"]:
        o = img.get("obj")
        print("      %-9s dt=%4s %-55s centro-mc %.2f | obj %s | C0->obj %s z=%s/%s | K->obj %s z=%s/%s" % (
            img["tipo"], img["dt_min"], img["tif"][9:], img["centro_vs_mcenter_km"],
            ("%.2fkm %s z=%.1f" % (o["d_vent"], o["card"], o["z"])) if o else "-", img.get("C0_a_obj"), img["C0_anom"], img["C0_anom3"],
            img.get("K_a_obj"), img["K_anom"], img["K_anom3"]))
print()
agg = collections.Counter((r["vol"], r["s"], r["veredicto_imagen"]) for r in filas)
for x in sorted(agg): print("  %-20s %-8s %-12s %d" % (*x, agg[x]))
print(collections.Counter(r["veredicto_imagen"] for r in filas))
print(collections.Counter(r["veredicto_radio"] for r in filas))
print("protegidas A:")
for r in filas:
    if r["prot_A"]: print("  ", r["k"], r["veredicto_radio"], r["veredicto_imagen"], r["veredictos_por_imagen"], "solo_ocr=", r["solo_ocr"])
