# -*- coding: utf-8 -*-
"""P8 (F5b): clasificar los aciertos posteriores al 2026-09-22 (alerta de MIROVA pareada a ±120 s con una pasada
nuestra publicada; universo de F5, p5_universo_post.json) con la lámina Latest10NTI como vara de posición.

Por qué: sin TIF, la única huella de dónde marcó MIROVA el foco es la lámina. La regla fija de recorte (f5b_lib) quedó
validada a 1 celda en VIIRS 375 y 750 (p3, p7) y NO en MODIS (p7: el foco no es el píxel más claro del panel y el
máximo del TIF tampoco reproduce la distancia en 4 de 7). Acá se corre igual para MODIS, pero el control de distancia
decide.

Por acierto:
 1. Lámina: la primera del mismo volcán y sensor con last_modified entre +20 min y +40 h de la pasada cuyo OCR de los
    10 paneles contenga la hora de la pasada (±120 s). Hasta 4 láminas por acierto. Cache de OCR por lámina.
 2. Panel: marco por centro de línea, regla fija, grilla prestada del TIF de referencia del volcán y sensor (p6).
 3. Píxel más claro dentro del inner de MIROVA (medido desde mirova_center), fuera del blanco de «sin dato».
 4. Control de identidad del píxel (como F5 i2_tif.py): su distancia a mirova_center tiene que reproducir la
    Distancia_km de la tabla (± max(tolerancia, 1 celda)). Si la distancia viene del OCR (F5 301), el control vale menos
    y se marca.
 5. Clase: (i) si el píxel de MIROVA cae a <= tolerancia de nuestro punto (our_lat/lon de F5, final_hotspot), (iii) si
    cae más lejos, (iv) si no hay lámina, panel, píxel, o el control falla. (ii) no aplica: todos son misma pasada.

Pregunta 1: si publicáramos otro foco, d_png_nuestro saldría grande y la clase (iii) aparecería; el control positivo es
el conjunto de validación (p7, 4 de 4 VIIRS) y un caso sintético: nuestro punto movido 3 km da (iii).
Pregunta 2: si el OCR o el recorte murieran, el número de «sin panel» o de controles fallidos subiría; se cuentan y se
listan por volcán.

Salida: p8_clases.csv, p8_clases.json, p8_ocr_cache.json, p8_resumen.txt (stdout).
"""
import csv, datetime as dt, hashlib, json, os, sys, urllib.request, collections
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
ARCH = {"NevadosDeChillan": "ChillanNevadosde"}
P = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
MAX_LAMINAS = int(os.environ.get("F5B_MAX_LAMINAS", "4"))   # 8 para reintentar los «pasada no hallada» (7 casos)
TOPE_BYTES = 1_200_000_000   # tope propio bajo los 2 GB de la tarea; C: tenía 4,7 GB libres (parada a 3 GB)

# filas con png_path vacío (omitido = nti_cubierto_por_mosaico_guardado) no son archivos: fuera (daban IndexError en bajar)
png_idx = [r for r in csv.DictReader(open(INS + r"\png_index.csv", encoding="utf-8")) if r["kind"] == "Latest10NTI" and r["png_path"]]
png_idx.sort(key=lambda r: r["last_modified_utc"])
post = json.load(open(os.path.join(H, "p5_universo_post.json"), encoding="utf-8"))
refs = json.load(open(os.path.join(H, "p6_tif_referencia_out.json"), encoding="utf-8"))
cache_fn = os.path.join(H, "p8_ocr_cache.json")
cache = json.load(open(cache_fn, encoding="utf-8")) if os.path.exists(cache_fn) else {}
bajado = [0]


def libre_gb(unidad="C:"):
    import shutil
    return shutil.disk_usage(unidad).free / 1e9


def bajar(path):
    d = os.path.join(TMP, "png")
    dst = os.path.join(d, path.split("/")[-2] + "_" + os.path.basename(path))
    if not os.path.exists(dst):
        if libre_gb() < 3.2 or bajado[0] > TOPE_BYTES:
            raise RuntimeError("PARADA por disco: libre %.2f GB, bajado %d bytes" % (libre_gb(), bajado[0]))
        urllib.request.urlretrieve(RAW + path, dst)
        bajado[0] += os.path.getsize(dst)
    return dst


def etiquetas_cache(path):
    if path not in cache:
        fn = bajar(path)
        cab, pan = L.etiquetas(fn)
        cache[path] = {"cabecera": cab[1], "paneles": [x[1] for x in pan], "md5": hashlib.md5(open(fn, "rb").read()).hexdigest()}
        json.dump(cache, open(cache_fn, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    return cache[path]


grillas = {}


def grilla_ref(vol, b):
    k = (vol, b)
    if k not in grillas:
        ref = refs[f"{ARCH.get(vol, vol)}|{b}"]["ref_sep"]
        fn = os.path.join(TMP, "tif_ref", ARCH.get(vol, vol) + "_" + os.path.basename(ref["path"]))
        g = L.grilla(fn)
        mc = (V[vol]["mirova_center_lat"], V[vol]["mirova_center_lon"])
        g["inner"] = L.mascara_inner(g, mc, V[vol]["inner_radius_km"])
        g["mc"] = mc
        g["celda_km"] = abs(g["transform"].e) * 111.0
        g["ref"] = ref["path"]
        grillas[k] = g
    return grillas[k]


def clasificar(r):
    vol, b = r["vol"], r["b"]
    va = ARCH.get(vol, vol)
    t0 = dt.datetime.strptime(r["dt"], "%Y-%m-%d %H:%M")
    o = {k: r[k] for k in ("vol", "b", "sensor", "dt", "fecha_mirova", "vrp_mirova", "protegida", "dist_mirova", "fuente_dist", "our_lat", "our_lon", "clase")}
    o["clase_f5_radio"] = o.pop("clase")
    cands = [x for x in png_idx if x["volcano"] == va and x["sensor"] == b and 1200 <= (P(x["last_modified_utc"]) - t0).total_seconds() <= 40 * 3600]
    o["laminas_candidatas"] = len(cands)
    panel = None
    for x in cands[:MAX_LAMINAS]:
        et = etiquetas_cache(x["png_path"])
        kk = [k for k, s_ in enumerate(et["paneles"]) if s_ and abs((dt.datetime.strptime(s_, "%Y-%m-%d %H:%M:%S") - t0).total_seconds()) <= 120]
        o.setdefault("laminas_vistas", []).append(x["png_path"].split("/")[-1])
        if kk:
            panel = (x, kk[0], et["paneles"][kk[0]])
            break
    if panel is None:
        o.update({"clase": "iv", "motivo_iv": "pasada no hallada en los paneles de hasta %d láminas" % MAX_LAMINAS})
        return o
    x, k, etiqueta = panel
    o.update({"png": x["png_path"], "png_last_modified": x["last_modified_utc"], "panel": k, "etiqueta_panel": etiqueta,
              "lag_lamina_h": round((P(x["last_modified_utc"]) - t0).total_seconds() / 3600, 2)})
    g = grilla_ref(vol, b)
    im = L.abrir_png(bajar(x["png_path"]))
    bb = L.bbox_marco(im, k)
    if bb is None:
        o.update({"clase": "iv", "motivo_iv": "sin marco en el panel"})
        return o
    o["marco_verde"] = bb[4]
    o["geometria"] = [round(v_, 2) for v_ in L.geometria(bb)]
    h = L.pixel_mas_claro(im, bb, g, g["inner"])
    if h is None:
        o.update({"clase": "iv", "motivo_iv": "sin píxel dentro del inner"})
        return o
    d_mc = L.hav(h["lat"], h["lon"], *g["mc"])
    tol_ctrl = max(L.TOL[b], g["celda_km"])
    dist = float(r["dist_mirova"]) if r["dist_mirova"] not in ("", None) else None
    ctrl = (abs(d_mc - dist) <= tol_ctrl) if dist is not None else None
    d_n = L.hav(h["lat"], h["lon"], float(r["our_lat"]), float(r["our_lon"]))
    o.update({"png_lat": round(h["lat"], 5), "png_lon": round(h["lon"], 5), "png_rc": h["rc"], "lum_max": round(h["lum_max"], 1),
              "lum_p99_panel": round(h["lum_p99_panel"], 1), "lum_mediana_panel": round(h["lum_mediana_panel"], 1), "mancha_px": h["mancha_px"],
              "blancos_sin_dato_px": h["blancos_sin_dato_px"], "d_png_mirova_center_km": round(d_mc, 3), "dist_tabla_km": dist,
              "control_distancia": ctrl, "tol_control_km": round(tol_ctrl, 3), "d_png_nuestro_km": round(d_n, 3), "tol_km": L.TOL[b],
              "prominencia": round(h["lum_max"] - h["lum_p99_panel"], 1)})
    if ctrl is None:
        o.update({"clase": "iv", "motivo_iv": "sin distancia de MIROVA para el control"})
    elif not ctrl:
        o.update({"clase": "iv", "motivo_iv": "el píxel más claro no reproduce la distancia de la tabla (%.2f contra %.2f km)" % (d_mc, dist)})
    else:
        o["clase"] = "i" if d_n <= L.TOL[b] else "iii"
        if r["fuente_dist"] == "OCR":
            o["clase"] += "?"   # control con distancia del OCR (F5 301): vale menos
    return o


def main():
    fn_json = os.path.join(H, "p8_clases.json")
    out = json.load(open(fn_json, encoding="utf-8")) if os.path.exists(fn_json) else []
    out = [o for o in out if o.get("vol") != "_CONTROL_"]
    hechos = {(o["vol"], o["b"], o["dt"]) for o in out}
    orden = sorted(post, key=lambda r: (r["vol"] != "NevadosDeChillan", r["vol"], r["b"], r["dt"]))
    for i, r in enumerate(orden):
        if (r["vol"], r["b"], r["dt"]) in hechos:
            continue
        try:
            o = clasificar(r)
        except RuntimeError as e:
            if "PARADA" in str(e):
                print("DETENIDO:", e); break
            o = {k: r[k] for k in ("vol", "b", "sensor", "dt", "vrp_mirova", "protegida", "dist_mirova", "fuente_dist")}
            o.update({"clase": "iv", "motivo_iv": "error: %r" % e})
        except Exception as e:
            o = {k: r[k] for k in ("vol", "b", "sensor", "dt", "vrp_mirova", "protegida", "dist_mirova", "fuente_dist")}
            import traceback
            o.update({"clase": "iv", "motivo_iv": "error: %r | %s" % (e, traceback.format_exc().strip().splitlines()[-3])})
        out.append(o)
        print(i + 1, o["vol"], o["b"], o["dt"], o.get("clase"), o.get("d_png_nuestro_km"), o.get("motivo_iv", ""), flush=True)
        json.dump(out, open(os.path.join(H, "p8_clases.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    # control sintético: el primer acierto clase i con nuestro punto movido 3 km al norte tiene que salir iii
    for o in out:
        if o.get("clase") == "i":
            r = dict(next(r for r in post if (r["vol"], r["b"], r["dt"]) == (o["vol"], o["b"], o["dt"])))
            r["our_lat"] = str(float(r["our_lat"]) + 3 / 111.0)
            c = clasificar(r)
            print("CONTROL SINTÉTICO (punto movido 3 km):", o["vol"], o["b"], o["dt"], "->", c.get("clase"), c.get("d_png_nuestro_km"))
            out.append({"vol": "_CONTROL_", "b": o["b"], "dt": o["dt"], "clase": c.get("clase"), "d_png_nuestro_km": c.get("d_png_nuestro_km"), "motivo_iv": "sintético: punto movido 3 km"})
            break
    cols = ["vol", "b", "sensor", "dt", "fecha_mirova", "vrp_mirova", "protegida", "dist_mirova", "fuente_dist", "our_lat", "our_lon", "clase_f5_radio",
            "clase", "motivo_iv", "png", "panel", "etiqueta_panel", "lag_lamina_h", "marco_verde", "png_lat", "png_lon", "png_rc", "lum_max", "lum_p99_panel",
            "lum_mediana_panel", "prominencia", "mancha_px", "blancos_sin_dato_px", "d_png_mirova_center_km", "dist_tabla_km", "control_distancia",
            "tol_control_km", "d_png_nuestro_km", "tol_km", "laminas_candidatas", "laminas_vistas"]
    with open(os.path.join(H, "p8_clases.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for o in out:
            w.writerow({k: (json.dumps(v_, ensure_ascii=False) if isinstance(v_, (list, dict)) else v_) for k, v_ in o.items()})
    real = [o for o in out if o["vol"] != "_CONTROL_"]
    print("\nRESUMEN por volcán y sensor (n, i, iii, iv, protegidas i/iii/iv):")
    for (vol, b), grp in sorted(collections.OrderedDict((k, [o for o in real if (o["vol"], o["b"]) == k]) for k in sorted({(o["vol"], o["b"]) for o in real})).items()):
        c = collections.Counter(o["clase"].rstrip("?") for o in grp)
        cp = collections.Counter(o["clase"].rstrip("?") for o in grp if o.get("protegida") == "True")
        print("  %-22s %-9s n=%3d  i=%3d iii=%3d iv=%3d | prot i=%3d iii=%3d iv=%3d | con control OCR (?)=%d" % (vol, b, len(grp), c["i"], c["iii"], c["iv"], cp["i"], cp["iii"], cp["iv"], sum(1 for o in grp if o["clase"].endswith("?"))))
    print("motivos iv:", collections.Counter(o.get("motivo_iv", "").split(" (")[0] for o in real if o["clase"] == "iv"))
    print("láminas bajadas en esta corrida: %d, bytes %d; láminas en cache OCR: %d" % (sum(1 for _ in cache), bajado[0], len(cache)))


if __name__ == "__main__":
    main()
