# -*- coding: utf-8 -*-
"""P7 (F5b): validación de la regla fija (f5b_lib.REGLA_LRTB) en casos NUEVOS con TIF, incluidos MODIS y un segundo
VIIRS 750, y los 4 de F5 pasados por la misma biblioteca (control de que la biblioteca reproduce p3).

Por qué: p3 derivó la regla con 3 láminas VIIRS 375 y 1 VIIRS 750; no hay MODIS en los 4 de F5, y la grilla MODIS es
de 51 celdas (2,96 px por celda). Si la regla falla en MODIS, las 23 protegidas MODIS de Chillán y las 3 de Láscar
quedan (iv).

Vara por caso, como en i2_tif.py de F5: el máximo del TIF dentro del inner tiene que reproducir la Distancia_km
de la tabla (± max(tolerancia, 1 celda)); si no, el caso no sirve de vara (se informa igual). Control: la posición
sacada del PNG cae a menos de la tolerancia (0,75 / 1,5 / 3 km) del máximo del TIF.
Pregunta 1: si la regla no valiera para MODIS, d_png_tif saldría de más de 1 celda. Pregunta 2: si la lámina bajada
no fuera de la pasada, la etiqueta OCR del panel 1 no coincidiría con la hora del TIF (se imprime).

Bajadas sueltas por raw.githubusercontent.com. Salida: p7_mas_casos_out.json.
"""
import csv, datetime as dt, hashlib, json, os, sys, urllib.request
import numpy as np
import yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import f5b_lib as L

sys.stdout.reconfigure(encoding="utf-8")
H = os.path.dirname(os.path.abspath(__file__))
TMP = r"C:\Users\nmend\vrp-temporales\s175_audit\f5b"
INS = r"C:\Users\nmend\vrp-temporales\s175_audit\insumos"
RAW = "https://raw.githubusercontent.com/MendozaVolcanic/mirova-tif-archive/main/"
V = {v["name"]: v for v in yaml.safe_load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\main\volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
ARCH = {"NevadosDeChillan": "ChillanNevadosde"}   # nombre de F5/volcanoes.yaml -> nombre del archivo
# (vol F5, bucket, dt nuestra pasada) ; dist y our_lat/lon salen de i2_pares.csv de F5
CASOS = [("Lascar", "MODIS", "2026-06-27 01:35"), ("Lascar", "MODIS", "2026-06-24 08:00"), ("Lascar", "MODIS", "2026-06-21 07:45"),
         ("Lascar", "MODIS", "2026-07-30 07:55"), ("Lascar", "MODIS", "2026-06-14 01:20"), ("Lascar", "MODIS", "2026-06-17 01:40"),
         ("Lascar", "MODIS", "2026-07-09 07:40"),
         ("Villarrica", "MODIS", "2026-09-04 07:50"), ("Villarrica", "VIIRS750", "2026-08-18 05:48"), ("PuyehueCordonCaulle", "VIIRS750", "2026-09-18 05:24"),
         ("Lastarria", "VIIRS375", "2026-06-12 05:54"), ("Lastarria", "VIIRS375", "2026-08-09 05:48"),
         ("Lascar", "VIIRS750", "2026-06-21 05:30"), ("Isluga", "VIIRS375", "2026-09-22 05:42")]
P = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
tif_idx = [r for r in csv.DictReader(open(INS + r"\tif_index.csv", encoding="utf-8")) if r["acquisition_utc"]]
png_idx = [r for r in csv.DictReader(open(INS + r"\png_index.csv", encoding="utf-8")) if r["kind"] == "Latest10NTI"]
pares = {(r["vol"], r["b"], r["dt"]): r for r in csv.DictReader(open(os.path.join(H, "..", "f5", "i2_pares.csv"), encoding="utf-8"))}


def bajar(path, sub):
    d = os.path.join(TMP, sub)
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, path.split("/")[-2] + "_" + os.path.basename(path))
    if not os.path.exists(dst):
        urllib.request.urlretrieve(RAW + path, dst)
    return dst, hashlib.md5(open(dst, "rb").read()).hexdigest()


out = []
for vol, b, hora in CASOS:
    r = pares[(vol, b, hora)]
    va = ARCH.get(vol, vol)
    t0 = dt.datetime.strptime(hora, "%Y-%m-%d %H:%M")
    tifs = [x for x in tif_idx if x["volcano"] == va and x["sensor"] == b and abs((P(x["acquisition_utc"]) - t0).total_seconds()) <= 120]
    o = {"vol": vol, "b": b, "dt": hora, "vrp_mirova": r["vrp_mirova"], "dist_tabla": r["dist_mirova"], "fuente_dist": r["fuente_dist"],
         "our_lat": float(r["our_lat"]), "our_lon": float(r["our_lon"])}
    if not tifs:
        o["estado"] = "sin TIF en el índice"
        out.append(o); print(json.dumps(o, ensure_ascii=False)); continue
    tr = sorted(tifs, key=lambda x: x["last_modified_utc"])[0]
    tlm = P(tr["last_modified_utc"])
    pngs = [x for x in png_idx if x["volcano"] == va and x["sensor"] == b and 0 <= (P(x["last_modified_utc"]) - tlm).total_seconds() <= 180]
    if not pngs:
        o["estado"] = "TIF sí, lámina no (ninguna a <=180 s del TIF)"; o["tif"] = tr["tif_path"]
        out.append(o); print(json.dumps(o, ensure_ascii=False)); continue
    pr = sorted(pngs, key=lambda x: x["last_modified_utc"])[0]
    ftif, m1 = bajar(tr["tif_path"], "tif_val")
    fpng, m2 = bajar(pr["png_path"], "png")
    o.update({"tif": tr["tif_path"], "tif_md5_ok": m1 == tr["md5"], "png": pr["png_path"], "png_md5_ok": m2 == pr["md5"],
              "lag_png_tif_s": (P(pr["last_modified_utc"]) - tlm).total_seconds()})
    cab, pan = L.etiquetas(fpng)
    o["ocr_cabecera"] = cab[1]; o["ocr_paneles"] = [x[1] for x in pan]
    # la pasada puede estar en cualquiera de los 10 paneles (van por hora de adquisición, no de proceso; p7 v0 lo mostró
    # en Láscar MODIS 2026-06-27 01:35: panel 2, con el 08:15 en el panel 1)
    kk = [k for k, x in enumerate(pan) if x[1] and abs((dt.datetime.strptime(x[1], "%Y-%m-%d %H:%M:%S") - t0).total_seconds()) <= 120]
    o["panel_de_la_pasada"] = kk[0] if kk else None
    if not kk:
        o["estado"] = "la pasada no está en los 10 paneles de la lámina pareada"
        out.append(o); print(json.dumps(o, ensure_ascii=False)); continue
    g = L.grilla(ftif)
    mc = (V[vol]["mirova_center_lat"], V[vol]["mirova_center_lon"])
    inner = L.mascara_inner(g, mc, V[vol]["inner_radius_km"])
    am = np.where(inner, g["a"], np.nan)
    iy, ix = np.unravel_index(np.nanargmax(am), am.shape)
    lat_t, lon_t = float(g["lats"][iy, ix]), float(g["lons"][iy, ix])
    celda_km = abs(g["transform"].e) * 111.0
    d_mc = L.hav(lat_t, lon_t, *mc)
    o.update({"tif_n": g["n"], "celda_km_aprox": round(celda_km, 3), "tif_max_rc": [int(iy), int(ix)], "tif_max_latlon": [round(lat_t, 5), round(lon_t, 5)],
              "d_tifmax_mirova_center": round(d_mc, 2),
              "georef_reproduce_distancia": (abs(d_mc - float(r["dist_mirova"])) <= max(L.TOL[b], celda_km)) if r["dist_mirova"] else None})
    im = L.abrir_png(fpng)
    bb = L.bbox_marco(im, kk[0])
    o["marco_centros"] = bb
    o["geometria_X0_Y0_W_H"] = [round(x, 2) for x in L.geometria(bb)]
    h = L.pixel_mas_claro(im, bb, g, inner, nan_tif=np.isnan(g["a"]))
    if h is None:
        o["estado"] = "sin píxel claro dentro del inner"
    else:
        d = L.hav(h["lat"], h["lon"], lat_t, lon_t)
        o.update({"png_max_rc": h["rc"], "png_max_latlon": [round(h["lat"], 5), round(h["lon"], 5)], "lum_max": round(h["lum_max"], 1),
                  "lum_p99": round(h["lum_p99_panel"], 1), "mancha_px": h["mancha_px"], "px_por_celda": round(h["px_por_celda"], 3),
                  "d_png_tif_km": round(d, 3), "d_png_tif_celdas": round(float(np.hypot(h["rc"][0] - iy, h["rc"][1] - ix)), 2),
                  "d_png_nuestro_km": round(L.hav(h["lat"], h["lon"], o["our_lat"], o["our_lon"]), 3),
                  "d_tif_nuestro_km": round(L.hav(lat_t, lon_t, o["our_lat"], o["our_lon"]), 3),
                  "tol_km": L.TOL[b], "valida": bool(d <= L.TOL[b])})
    out.append(o)
    print(json.dumps(o, ensure_ascii=False))
json.dump(out, open(os.path.join(H, "p7_mas_casos_out.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
v = [o for o in out if "valida" in o]
print("VALIDA", sum(o["valida"] for o in v), "de", len(v), "| con georref que reproduce la distancia:",
      sum(o["valida"] for o in v if o.get("georef_reproduce_distancia")), "de", sum(1 for o in v if o.get("georef_reproduce_distancia")))
