# VX S175: copia literal de i2_extension.py del auditor F5, con DOS cambios: lee i2_pares.csv desde la carpeta f5 y escribe su
# salida en la carpeta vx (para no tocar los archivos del auditor). Nada más cambia.
# -*- coding: utf-8 -*-
"""I2 complemento 2: en los aciertos (iii) por radio, ¿el radio de MIROVA cae dentro de la extensión de NUESTROS píxeles
anómalos (mismo cúmulo, otro píxel) o fuera (otro foco)? Distancias desde mirova_center (origen de MIROVA, A3).
Lee i2_pares.csv y los records de la base (copia privada). Salida: i2_extension_out.json."""
import csv, json, math, os, sys, collections
import yaml
sys.stdout.reconfigure(encoding="utf-8")
H = os.path.dirname(os.path.abspath(__file__))  # VX: salida a vx
F5 = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f5"  # VX: entrada i2_pares.csv del auditor, sin tocarla
ROOT = r"C:\Users\nmend\vrp-temporales\s175_audit\f5\root"
V = {v["name"]: v for v in yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}
TOL = {"VIIRS375": 0.75, "VIIRS750": 1.5, "MODIS": 3.0}
def hav(a, b, c, d):
    p = math.radians
    return 2 * 6371.0 * math.asin(math.sqrt(math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(d - b) / 2) ** 2))
rows = [r for r in csv.DictReader(open(os.path.join(F5, "i2_pares.csv"), encoding="utf-8")) if r["clase"] == "iii"]
vols = {r["vol"] for r in rows}
recs = {}
for v in vols:
    for x in json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", v + ".json"), encoding="utf-8"))["records"]:
        recs[(v, x["sensor"], x["datetime_utc"])] = x
out, cnt = [], collections.Counter()
for r in rows:
    x = recs[(r["vol"], r["sensor"], r["dt"])]
    mc = (V[r["vol"]]["mirova_center_lat"], V[r["vol"]]["mirova_center_lon"])
    px = [p for p in (x.get("anomaly_pixels") or []) if p.get("lat") is not None]
    ds = [hav(p["lat"], p["lon"], *mc) for p in px]
    dm = float(r["dist_mirova"]); tol = TOL[r["b"]]
    if not ds:
        cl = "sin_pixeles"
    else:
        hot = max(px, key=lambda p: p.get("vrp_mw") or 0)
        dh = hav(hot["lat"], hot["lon"], *mc)
        dentro = (min(ds) - tol) <= dm <= (max(ds) + tol)
        cl = "mismo_cumulo_otro_pixel" if dentro else "fuera_de_nuestros_pixeles"
    cnt[(r["vol"], r["b"], cl, r["protegida"] == "True", r["fuente_dist"])] += 1
    out.append({"vol": r["vol"], "sensor": r["sensor"], "dt": r["dt"], "vrp_mirova": r["vrp_mirova"], "protegida": r["protegida"],
                "fuente_dist": r["fuente_dist"], "estrato": r["estrato"], "dist_mirova": dm, "d_centroide_mc": float(r["d_desde_mirova_center"]),
                "n_pix": len(ds), "d_min_pix": round(min(ds), 2) if ds else None, "d_max_pix": round(max(ds), 2) if ds else None,
                "d_pix_caliente": round(dh, 2) if ds else None, "clase_extension": cl})
res = {"conteo": {"|".join(map(str, k)): v for k, v in sorted(cnt.items())}, "casos": out}
json.dump(res, open(os.path.join(H, "i2_extension_out.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in sorted(cnt.items()):
    print(k, v)
for o in out:
    if o["clase_extension"] != "mismo_cumulo_otro_pixel":
        print(o)
