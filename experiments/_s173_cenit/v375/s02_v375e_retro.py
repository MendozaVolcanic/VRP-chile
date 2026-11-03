# -*- coding: utf-8 -*-
"""s02 (S173, auditoría cenit V375 en Chillán): V375-E por pasada en Nevados de Chillán, desde los lotes retrospectivos.

POR QUÉ. La sombra prospectiva de V375-E todavía no escribió ningún record (ver s00): la única salida por pasada de la
vía que existe hoy está en las grillas guardadas de los lotes retrospectivos (S159, S162, S162b y el run FAR), las mismas
que leyó el lector sellado. Ahí está, por pasada, el gránulo ya interpolado a la grilla fija de 375 m de MIROVA.
Sobre esas grillas se corre la función de la vía de pipeline/ de origin/main (mirova_v750_codigo.procesar_grilla con la
caja caja_v375), sin tocar nada, y el record que sale pasa por el predicado del tablero ejecutado con node
(banco_paridad.cargar_nuestros con data= una carpeta temporal mía). Así la magnitud de la vía es la que el tablero
publicaría si la vía fuera producción. NO es una ablación: es la vía entera.

Para cada pasada se guardan además, sin recalcular: el VRP del brazo C13 de brazos.py (la caja de la vía, salida del
probe), los demás brazos de ROI de V375-C (M14, M13, M21, C14, C21, PIX7, SENS, CIRC) cuando existen, y el record K que
corrió el probe sobre el mismo gránulo (otro código, el de la fecha del probe).

P1 (si lo medido estuviera roto, ¿lo vería?): control cruzado, el VRP de la vía re-corrida contra el C13 guardado por el
   probe (otra implementación, brazos.py) debe coincidir salvo las escenas de 1 a 4 píxeles donde el relleno difiere
   (PREREGISTRO_E.md §8.6 b); y el disp de node contra el vrp_mw del record de la vía.
P2 (instrumento muerto): si las grillas no se leyeran, n_via_con_pixeles sería 0 y el control cruzado no tendría pares;
   se imprime cuántas grillas se leyeron y cuántas faltaron, por lote.
Uso: python -B s02_v375e_retro.py <raiz copia origin/main> <s01_k_pasadas.csv> <prefijo salida>
"""
import csv, glob, json, os, shutil, sys
from collections import Counter
from datetime import datetime

import numpy as np

ROOT, KCSV, PRE = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp  # noqa: E402
import yaml  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402

VOL = "NevadosDeChillan"
LOTES = {"S162": r"C:/vrp-trabajo/temporales/s162_v375/run_40116289866",
         "S162b": r"C:/vrp-trabajo/temporales/s162_v375/run_40131572769",
         "S159": r"D:/vrp-trabajo/temporales/s159_portes/run_39712862945",
         "FAR": r"D:/vrp-trabajo/temporales/s167_v375e_far/run_40773794395"}
PLAT = {"VNP": "VIIRS_SNPP", "VJ1": "VIIRS_NOAA20", "VJ2": "VIIRS_NOAA21"}

v = [x for x in yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]
     if x["name"] == VOL][0]
vent_lat, vent_lon = v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])
bp.VOLS = [VOL]
coords = bp._coords_por_volcan()
inner = bp.inner_desde_html()
g = MV.grilla_del_volcan(VOL, paso_m=375.0, clave_roi="roi_v375")
box = MV.caja_v375(g, vent_lat, vent_lon, lado_sensible=13, half_roi1_m=MV.HALF_ROI1_V375_M)
pos = MV.posicion_de(g, vent_lat, vent_lon)

filas, cnt = {}, Counter()
for lote, base in LOTES.items():
    for fn in glob.glob(os.path.join(base, "**", "resultados_VIIRS375*.json"), recursive=True):
        for x in json.load(open(fn, encoding="utf-8")):
            if x.get("volcan") != VOL:
                continue
            cnt[(lote, "entradas")] += 1
            if x.get("estado") != "ok":
                cnt[(lote, "estado_no_ok")] += 1
                continue
            gz = os.path.join(os.path.dirname(fn), f"grilla_{x['id']}.npz")
            if not os.path.exists(gz):
                cnt[(lote, "sin_grilla")] += 1
                continue
            d = np.load(gz)
            mir, tir = np.asarray(d["mir"], float), np.asarray(d["tir"], float)
            sensor = PLAT[x["granule"][:3]]
            rec = MV.procesar_grilla(mir, tir, g, box, x["dayflag"], x["sunglint"], pos, v["inner_radius_km"], sensor,
                                     familia="VIIRS375")
            geom = x.get("geometria_centro") or {}
            rec.update({"datetime_utc": x["hora_utc"], "sensor_zenith_deg": round(geom.get("sensor_zenith"), 2),
                        "granule": x["granule"], "via_codigo_mirova": True})
            port = x.get("port") or {}
            brazos = {b: (port[b] or {}).get("vrp_mw") for b in port}
            krec = (x.get("K") or {}).get("record") or {}
            kpc = krec.get("primary_cluster") or {}
            clave = (sensor, x["hora_utc"])
            cnt[(lote, "corridas")] += 1
            if clave in filas:
                cnt[(lote, "duplicada")] += 1
                filas[clave]["lotes"] += "+" + lote
                continue
            filas[clave] = {"sensor": sensor, "dt": x["hora_utc"], "lotes": lote, "id": x["id"],
                            "z_via": geom.get("sensor_zenith"), "rec": rec,
                            "via_vrp_rec": rec.get("vrp_mw"), "via_npix": rec.get("n_anomalous_pixels"),
                            "via_dc": rec.get("distance_class"),
                            "via_cdist": (rec.get("primary_cluster") or {}).get("centroid_dist_km"),
                            "via_cercano": min([p["dist_km"] for p in rec.get("anomaly_pixels") or []], default=None),
                            "via_tbg": rec.get("t_bg_k"),
                            **{f"br_{b}": brazos.get(b) for b in ("M14", "M13", "M21", "C13", "C14", "C21", "PIX7",
                                                                    "SENS", "CIRC", "fisica", "pixel", "sensible")},
                            "probeK_pc": kpc.get("vrp_mw"), "probeK_f5": krec.get("f5_core_vrp_mw"),
                            "probeK_dc": krec.get("distance_class"), "probeK_z": krec.get("sensor_zenith_deg")}

# predicado del tablero (node) sobre los records de la vía
tmp = os.path.join(os.path.dirname(os.path.abspath(PRE)), "_tmp_via_data")
shutil.rmtree(tmp, ignore_errors=True)
os.makedirs(tmp)
recs = [f["rec"] for f in filas.values()]
json.dump({"records": recs}, open(os.path.join(tmp, VOL + ".json"), "w", encoding="utf-8"))
dts = sorted(f["dt"] for f in filas.values())
ventana = (dts[0][:10], dts[-1][:10])
pub = bp.cargar_nuestros(coords, inner, ventana, data=tmp)
pubmap = {(r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M")): r for r in pub}
nodiurnas = len(pub)

# K de producción (s01) por pasada
K = {(r["sensor"], r["dt"]): r for r in csv.DictReader(open(KCSV, encoding="utf-8")) if r["b"] == "VIIRS375"}

rows = []
for k, f in sorted(filas.items(), key=lambda kv: kv[0][1]):
    p = pubmap.get(k)
    kk = K.get(k) or {}
    r = {x: y for x, y in f.items() if x != "rec"}
    r.update({"via_pub": None if p is None else p["pub"], "via_disp": None if p is None else p["disp"],
              "nocturna_banco": p is not None,
              "K_en_produccion": bool(kk), "K_pub": kk.get("pub"), "K_disp": kk.get("disp"), "K_z": kk.get("z"),
              "K_dc": kk.get("dc"), "K_sha": kk.get("sha"), "K_proc": kk.get("proc"),
              "vrp_M": kk.get("vrp_M"), "vrp_M_cons": kk.get("vrp_M_cons"), "src_M": kk.get("src_M"),
              "dist_M": kk.get("dist_M"), "lab": kk.get("lab")})
    rows.append(r)

with open(PRE + "_pasadas.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

# controles
def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


par_c13 = [(fnum(r["via_vrp_rec"]), fnum(r["br_C13"])) for r in rows if r["br_C13"] is not None and r["via_npix"]]
dif = [abs(a - b) for a, b in par_c13 if a is not None and b is not None]
node_vs_rec = [abs(fnum(r["via_disp"]) - fnum(r["via_vrp_rec"])) for r in rows
               if r["via_pub"] == 1 and r["via_disp"] is not None and r["via_vrp_rec"]]
out = {"ventana_lotes": ventana, "conteo_por_lote": {f"{a}|{b}": c for (a, b), c in sorted(cnt.items())},
       "pasadas_unicas": len(rows), "pasadas_nocturnas_banco": nodiurnas,
       "via_con_pixeles": sum(1 for r in rows if r["via_npix"]),
       "control_via_vs_C13": {"n": len(dif), "dif_max_mw": max(dif) if dif else None,
                              "n_dif_gt_1e-3": sum(1 for x in dif if x > 1e-3)},
       "control_node_vs_record": {"n_pub": len(node_vs_rec), "dif_max_mw": max(node_vs_rec) if node_vs_rec else None},
       "K_en_produccion": sum(1 for r in rows if r["K_en_produccion"]),
       "con_alerta_MIROVA": sum(1 for r in rows if fnum(r["vrp_M"]) and fnum(r["vrp_M"]) > 0),
       "dz_via_vs_K_max": max([abs(fnum(r["z_via"]) - fnum(r["K_z"])) for r in rows
                               if r["K_z"] not in (None, "") and r["z_via"] is not None], default=None)}
json.dump(out, open(PRE + "_resumen.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
print(json.dumps(out, indent=1, ensure_ascii=False, default=str))
