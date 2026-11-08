# -*- coding: utf-8 -*-
"""P9 (F5b): las tres alertas MODIS de Láscar sin TIF (2026-09-25 08:00, 2026-10-08 08:00, 2026-10-26 07:55 UTC).

Qué se mira: (1) la fila de la tabla de MIROVA en la referencia de la base (VRP, Distancia_km, Clasificacion);
(2) si tenemos un record MODIS a ±120 s en data/mirova_equivalent/Lascar.json de la base (árbol
C:\\Users\\nmend\\vrp-temporales\\s175_audit\\f1\\root_base, datos de e75a7d52d) y qué publica (via_codigo_mirova,
final_hotspot, pc.vrp_mw); (3) la lámina MODIS de Láscar que muestra la pasada (OCR de los 10 paneles), si su marco
es verde, y el píxel más claro con la regla fija aunque en MODIS no valide (p7), para dejar el número y su control.

Pregunta 2: si la lámina no mostrara la pasada, el OCR no la encontraría y se diría. Salida: p9_lascar_modis_out.json.
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
P = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
PASADAS = ["2026-09-25 08:00", "2026-10-08 08:00", "2026-10-26 07:55"]

tabla = list(csv.DictReader(open(INS + r"\snapshot_consolidado_base.csv", encoding="utf-8")))
png_idx = sorted([r for r in csv.DictReader(open(INS + r"\png_index.csv", encoding="utf-8")) if r["kind"] == "Latest10NTI" and r["volcano"] == "Lascar" and r["sensor"] == "MODIS"], key=lambda r: r["last_modified_utc"])
recs = json.load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\f1\root_base\data\mirova_equivalent\Lascar.json", encoding="utf-8"))
recs = recs["records"] if isinstance(recs, dict) and "records" in recs else recs


def bajar(path):
    d = os.path.join(TMP, "png_p9")
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, os.path.basename(path))
    if not os.path.exists(dst):
        urllib.request.urlretrieve(RAW + path, dst)
    return dst


def hora_rec(rec):
    for k in ("acq_time_utc", "acquisition_utc", "datetime_utc", "time_utc", "timestamp_utc", "acq_datetime"):
        if k in rec and rec[k]:
            return k, rec[k]
    return None, None


refs = json.load(open(os.path.join(H, "p6_tif_referencia_out.json"), encoding="utf-8"))["Lascar|MODIS"]["ref_sep"]
g = L.grilla(os.path.join(TMP, "tif_ref", "Lascar_" + os.path.basename(refs["path"])))
mc = (V["Lascar"]["mirova_center_lat"], V["Lascar"]["mirova_center_lon"])
inner = L.mascara_inner(g, mc, V["Lascar"]["inner_radius_km"])
out = []
for h in PASADAS:
    t0 = dt.datetime.strptime(h, "%Y-%m-%d %H:%M")
    o = {"pasada": h}
    o["tabla"] = [{k: r[k] for k in ("Fecha_Satelite_UTC", "Sensor", "VRP_MW", "Distancia_km", "Tipo_Registro", "Clasificacion Mirova")}
                  for r in tabla if r["Volcan"].lower().startswith("lascar") and r["Sensor"] == "MODIS" and abs((dt.datetime.strptime(r["Fecha_Satelite_UTC"][:19], "%Y-%m-%d %H:%M:%S") - t0).total_seconds()) <= 120]
    # nuestros records MODIS a ±120 s
    nuestros = []
    for rec in recs:
        if not str(rec.get("sensor", "")).upper().startswith("MODIS"):
            continue
        k, hv = hora_rec(rec)
        if not hv:
            continue
        try:
            t = dt.datetime.strptime(str(hv)[:16].replace("T", " "), "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        if abs((t - t0).total_seconds()) <= 120:
            pc = rec.get("primary_cluster") or {}
            nuestros.append({"sensor": rec.get("sensor"), "hora": hv, "campo_hora": k, "via_codigo_mirova": rec.get("via_codigo_mirova"),
                             "detection": rec.get("detection"), "distance_class": rec.get("distance_class"), "final_hotspot_lat": rec.get("final_hotspot_lat"),
                             "final_hotspot_lon": rec.get("final_hotspot_lon"), "final_hotspot_dist_km": rec.get("final_hotspot_dist_km"),
                             "pc_vrp_mw": pc.get("vrp_mw"), "vrp_mw": rec.get("vrp_mw"), "n_hot": rec.get("n_hot_pixels", rec.get("n_hot")),
                             "is_night": rec.get("is_night"), "claves": sorted(rec.keys())[:60]})
    o["nuestros_records"] = nuestros
    # lámina con la pasada
    cands = [x for x in png_idx if 1200 <= (P(x["last_modified_utc"]) - t0).total_seconds() <= 40 * 3600]
    o["laminas_candidatas"] = len(cands)
    hallado = None
    for x in cands[:5]:
        fn = bajar(x["png_path"])
        cab, pan = L.etiquetas(fn)
        kk = [k for k, s_ in enumerate(pan) if s_[1] and abs((dt.datetime.strptime(s_[1], "%Y-%m-%d %H:%M:%S") - t0).total_seconds()) <= 120]
        o.setdefault("laminas_vistas", []).append({"png": x["png_path"].split("/")[-1], "cabecera": cab[1], "paneles": [s_[1] for s_ in pan]})
        if kk:
            hallado = (fn, x, kk[0], pan[kk[0]][1]); break
    if hallado:
        fn, x, k, et = hallado
        im = L.abrir_png(fn)
        bb = L.bbox_marco(im, k)
        o.update({"png": x["png_path"], "panel": k, "etiqueta": et, "marco_verde": bb[4] if bb else None})
        hp = L.pixel_mas_claro(im, bb, g, inner) if bb else None
        if hp:
            d_mc = L.hav(hp["lat"], hp["lon"], *mc)
            o.update({"png_latlon": [round(hp["lat"], 5), round(hp["lon"], 5)], "d_png_mirova_center_km": round(d_mc, 2), "lum_max": round(hp["lum_max"], 1),
                      "lum_p99_panel": round(hp["lum_p99_panel"], 1), "mancha_px": hp["mancha_px"]})
            if nuestros and nuestros[0].get("final_hotspot_lat") is not None:
                o["d_png_nuestro_km"] = round(L.hav(hp["lat"], hp["lon"], float(nuestros[0]["final_hotspot_lat"]), float(nuestros[0]["final_hotspot_lon"])), 2)
    else:
        o["png"] = None
    out.append(o)
    print(json.dumps(o, ensure_ascii=False, default=str))
json.dump(out, open(os.path.join(H, "p9_lascar_modis_out.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
